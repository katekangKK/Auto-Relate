"""Run an isolated evaluation of candidate rejection thresholds."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import warnings

import pandas as pd
from sklearn.metrics import (
    auc, average_precision_score, confusion_matrix, precision_recall_curve,
    precision_score, recall_score, f1_score,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "auto_relate_fd_mod"))
import ht_afd

MODES = ("A_skip", "B_reject_known_negatives", "C_reject_all")
FIELDS = [
    "case_id", "left_col", "right_col", "sample_type", "score", "decision",
    "numeric_pair", "violation_rate", "violation_source", "ht2", "rows_scored",
]


def write_json(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def sample_state(seed: int, split: str, case: str, lhs: str, rhs: str) -> int:
    # Labels are excluded so changing ground truth cannot change predictions.
    material = f"{seed}|{split}|{case}|{lhs}|{rhs}"
    return int(hashlib.md5(material.encode()).hexdigest()[:8], 16)


def detected_violations(frame: pd.DataFrame, lhs: str, rhs: str) -> list[int]:
    """Same majority and sorted-mode tie rule as ht_afd.find_violations."""
    counts = frame.groupby([lhs, rhs], sort=True, dropna=False).size()
    if counts.empty:
        return []
    modes = counts.groupby(level=0, sort=True).idxmax().map(lambda pair: pair[1])
    bad = frame.loc[frame[rhs].ne(frame[lhs].map(modes))]
    return bad.sort_values(lhs, kind="stable").index.tolist()


def fd_score(frame: pd.DataFrame, lhs: str, rhs: str) -> float:
    """The released 1-HT1_FD formula with linear-time frequency counting.

    Preserve first-seen RHS and insertion order, including when a supplied
    clean violation list leaves more than one RHS in an LHS group.
    """
    first: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for left, right in zip(frame[lhs], frame[rhs]):
        if pd.isnull(left) or pd.isnull(right):
            continue
        left, right = str(left), str(right)
        if left not in first:
            first[left], sizes[left] = right, 1
        elif right == first[left]:
            sizes[left] += 1
    n = sum(sizes.values())
    if n == 0:
        return 1.0
    rhs_counts: Counter = Counter()
    for left, size in sizes.items():
        rhs_counts[first[left]] += size
    disruption = 0.0
    for left, size in sizes.items():
        if size > 1:
            disruption += (1 - rhs_counts[first[left]] / n) * size
    return 1 - disruption / n


def score_candidate(
    frame: pd.DataFrame, lhs: str, rhs: str, split: str,
    clean_violations: list[int], seed: int, case: str,
    sample_limit: int, ht2_threshold: float,
) -> tuple[float, str, object, int]:
    if split == "clean":
        frame = frame.drop(clean_violations).reset_index(drop=True)
    else:
        frame = frame.copy()
    if len(frame) > sample_limit:
        frame = frame.sample(
            n=sample_limit, random_state=sample_state(seed, split, case, lhs, rhs)
        ).reset_index(drop=True)
    ht2_value: object = ""
    if split == "dirty":
        violations = detected_violations(frame, lhs, rhs)
        flag, ht2_value = ht_afd.hypothesis_testing2.get_ht2_score(
            frame, frame.columns.tolist(), [lhs, rhs], violations, ht2_threshold
        )
        # Preserve the original rounded >0.5 gate and original HT2 calculation.
        rate = round(len(violations) / len(frame), 4) if len(frame) else 0.0
        if flag is True or rate > 0.5:
            return 1.0, "ht2_reject" if flag is True else "over_half_violations", ht2_value, len(frame)
        frame = frame.drop(violations).reset_index(drop=True)
    return fd_score(frame, lhs, rhs), "scored", ht2_value, len(frame)


def evaluate(frame: pd.DataFrame) -> dict:
    labels = frame.sample_type.eq("P").astype(int)
    scores = frame.score.astype(float)
    precision, recall, _ = precision_recall_curve(labels, -scores)
    # Use a fixed threshold, rather than selecting a threshold using test labels.
    predicted = scores.lt(0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predicted, labels=[0, 1]).ravel()
    return {
        "evaluated": len(frame), "positives": int(labels.sum()),
        "negatives": int(len(frame) - labels.sum()),
        "pr_auc_full": float(auc(recall, precision)),
        "average_precision": float(average_precision_score(labels, -scores)),
        "fixed_threshold": "score < 0.5",
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--split", choices=("clean", "dirty"), required=True)
    parser.add_argument("--violation-threshold", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sample-limit", type=int, default=10000)
    parser.add_argument("--ht2-threshold", type=float, default=0.0001)
    parser.add_argument("--tables", nargs="+")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "decisions.jsonl").exists():
        parser.error("Output already contains decisions; choose a fresh output directory.")
    cases = sorted(p.parent for p in args.dataset.glob("*/ground_truth.csv"))
    if args.tables:
        cases = [p for p in cases if p.name in args.tables]
    if not cases:
        parser.error("No tables selected.")
    config = vars(args).copy()
    config.update(dataset=str(args.dataset.resolve()), output=str(args.output.resolve()))
    config["code_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    config["sampling_key"] = "seed|split|case_id|left_col|right_col (no label)"
    config["violation_source"] = "detected from current full table" if args.mode == MODES[2] else "ground_truth.violation_rows"
    config["diagnostic_only"] = args.mode != MODES[2]
    config["python"] = sys.executable
    write_json(args.output / "config.json", config)
    started = time.time()
    totals: Counter = Counter()
    categories: Counter = Counter()
    selected_keys: set[tuple] = set()
    with (args.output / "results.csv").open("w", newline="") as result_file, \
         (args.output / "decisions.jsonl").open("w") as ledger, \
         (args.output / "failures.jsonl").open("w") as failures:
        writer = csv.DictWriter(result_file, fieldnames=FIELDS)
        writer.writeheader()
        for table_number, case in enumerate(cases, 1):
            filename = "clean_data.csv" if args.split == "clean" else "dirty_data_mix_0.1.csv"
            gt = pd.read_csv(case / "ground_truth.csv", keep_default_na=False)
            inferred = pd.read_csv(case / filename)
            frame = pd.read_csv(case / filename, dtype=str, keep_default_na=False)
            numeric = {c for c in inferred if pd.api.types.is_numeric_dtype(inferred[c])}
            del inferred
            for candidate in gt.to_dict("records"):
                lhs, rhs, label = candidate["left_col"], candidate["right_col"], candidate["sample_type"]
                key = (case.name, lhs, rhs)
                if key in selected_keys:
                    raise ValueError(f"Duplicate candidate: {key}")
                selected_keys.add(key)
                if label not in ("P", "N"):
                    raise ValueError(f"Unknown label: {label!r}")
                totals["input"] += 1
                totals[f"input_{label}"] += 1
                record = dict(case_id=case.name, left_col=lhs, right_col=rhs, sample_type=label)
                try:
                    numeric_pair = lhs in numeric and rhs in numeric
                    if args.mode == MODES[2]:
                        violation_rows = detected_violations(frame, lhs, rhs)
                    else:
                        violation_rows = ast.literal_eval(candidate["violation_rows"])
                    violation_rate = len(violation_rows) / len(frame) if len(frame) else 0.0
                    over_threshold = violation_rate > args.violation_threshold
                    eligible = args.mode == MODES[2] or label == "N"
                    reject = eligible and (numeric_pair or over_threshold)
                    reason = "both" if numeric_pair and over_threshold else "numeric" if numeric_pair else "accuracy"
                    record.update(
                        numeric_pair=numeric_pair, violation_rate=violation_rate,
                        violation_source="detected" if args.mode == MODES[2] else "annotated",
                        ht2="", rows_scored=0,
                    )
                    if reject:
                        categories[f"{reason}_{label}"] += 1
                        if args.mode == MODES[0]:
                            record.update(score=None, decision=f"skip_{reason}")
                            totals["skipped"] += 1
                        else:
                            record.update(score=1.0, decision=f"reject_{reason}")
                            totals["pre_rejected"] += 1
                    else:
                        score, decision, ht2_value, rows = score_candidate(
                            frame, lhs, rhs, args.split, violation_rows, args.seed,
                            case.name, args.sample_limit, args.ht2_threshold,
                        )
                        record.update(score=score, decision=decision, ht2=ht2_value, rows_scored=rows)
                    if record["score"] is not None:
                        writer.writerow(record)
                        totals["evaluated"] += 1
                except Exception as error:
                    record.update(score=None, decision="error", error=repr(error))
                    totals["errors"] += 1
                    failures.write(json.dumps({**record, "traceback": traceback.format_exc()}, ensure_ascii=False) + "\n")
                    failures.flush()
                    print(f"ERROR {key}: {error!r}", flush=True)
                ledger.write(json.dumps(record, ensure_ascii=False) + "\n")
            result_file.flush()
            ledger.flush()
            progress = {
                "status": "running", "mode": args.mode, "split": args.split,
                "tables_done": table_number, "tables_total": len(cases),
                "elapsed_seconds": round(time.time() - started, 2),
                "counts": dict(totals), "filter_counts": dict(categories),
                "last_table": case.name,
            }
            write_json(args.output / "progress.json", progress)
            print(json.dumps(progress, ensure_ascii=False), flush=True)
    result_frame = pd.read_csv(args.output / "results.csv")
    summary = {
        **progress, "status": "complete" if not totals["errors"] else "incomplete",
        "metrics": evaluate(result_frame) if len(result_frame) else {},
    }
    write_json(args.output / "summary.json", summary)
    write_json(args.output / "progress.json", summary)
    print("SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)
    if totals["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if "--output" in sys.argv:
            output = Path(sys.argv[sys.argv.index("--output") + 1])
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "fatal_error.json", {
                "status": "failed", "error": repr(error),
                "traceback": traceback.format_exc(),
            })
        raise
