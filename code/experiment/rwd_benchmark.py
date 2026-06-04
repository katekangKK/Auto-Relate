from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import warnings
from pathlib import Path

import pandas as pd


DEFAULT_NOISE_RATE = 0.1


def clean_colname(col: str) -> str:
    return (
        re.sub(r"[^(a-z)(A-Z)(0-9)._-]", "", col)
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
    )


def parse_tables_arg(value: str | None) -> set[str] | None:
    if not value:
        return None
    tables = {item.strip() for item in value.split(",") if item.strip()}
    return tables or None


def stable_int(seed_material: str) -> int:
    digest = hashlib.md5(seed_material.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def load_table(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    rename_map = {col: clean_colname(col) for col in df.columns}
    cleaned = df.rename(columns=rename_map)
    if cleaned.columns.duplicated().any():
        duplicates = cleaned.columns[cleaned.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate cleaned columns in {csv_path.name}: {duplicates}")
    return cleaned


def find_violations(case_df: pd.DataFrame, left_col: str, right_col: str) -> list[int]:
    violations = []
    for _, grp in case_df.groupby(left_col):
        if len(grp[right_col].unique()) > 1:
            violations.append(grp[grp[right_col] != grp[right_col].mode()[0]])
    if not violations:
        return []
    violation_df = pd.concat(violations)
    return [int(i) for i in violation_df.index.tolist()]


def compute_violation_map(case_df: pd.DataFrame) -> dict[tuple[str, str], list[int]]:
    violation_map: dict[tuple[str, str], list[int]] = {}
    columns = case_df.columns.tolist()
    for left_col in columns:
        for right_col in columns:
            if left_col != right_col:
                violation_map[(left_col, right_col)] = []

        for _, grp in case_df.groupby(left_col, sort=False):
            if grp.shape[0] <= 1:
                continue
            for right_col in columns:
                if right_col == left_col:
                    continue
                if grp[right_col].nunique(dropna=False) <= 1:
                    continue
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    value_counts = grp[right_col].value_counts(dropna=False, sort=False)
                max_count = value_counts.max()
                mode_value = value_counts[value_counts == max_count].index[0]
                mismatched = grp.index[grp[right_col] != mode_value].tolist()
                if mismatched:
                    violation_map[(left_col, right_col)].extend(int(i) for i in mismatched)

    for key in violation_map:
        if violation_map[key]:
            violation_map[key] = sorted(set(violation_map[key]))
    return violation_map


def make_violation_sample(
    case_df: pd.DataFrame,
    left_col: str,
    right_col: str,
    violation_rows: list[int],
    limit: int = 2,
) -> str:
    if not violation_rows:
        return "[]"
    rows = []
    for row_idx in violation_rows[:limit]:
        rows.append(
            (
                str(case_df.at[row_idx, left_col]),
                str(case_df.at[row_idx, right_col]),
                int(row_idx),
            )
        )
    return repr(rows)


def inject_column_noise(
    df: pd.DataFrame,
    noise_rate: float,
    seed: int,
    table_name: str,
) -> pd.DataFrame:
    dirty_df = df.copy()
    row_count = len(dirty_df)
    if row_count == 0 or noise_rate <= 0:
        return dirty_df

    for col in dirty_df.columns:
        noise_count = int(round(row_count * noise_rate))
        if noise_count <= 0:
            continue
        rs = stable_int(f"{seed}|{table_name}|{col}")
        target_rows = dirty_df.sample(n=noise_count, random_state=rs).index.tolist()
        source_rows = dirty_df.sample(n=noise_count, random_state=rs + 1).index.tolist()
        for target_idx, source_idx in zip(target_rows, source_rows):
            dirty_df.at[target_idx, col] = dirty_df.at[source_idx, col]
    return dirty_df


def build_rwd_fd_benchmark(
    source_dir: Path,
    ground_truth_path: Path,
    output_dir: Path,
    noise_rate: float = DEFAULT_NOISE_RATE,
    seed: int = 42,
    selected_tables: set[str] | None = None,
) -> dict[str, object]:
    source_dir = Path(source_dir)
    ground_truth_path = Path(ground_truth_path)
    output_dir = Path(output_dir)
    manifest_path = output_dir.parent / f"{output_dir.name}_manifest.json"

    gt_df = pd.read_csv(ground_truth_path)
    positive_pairs = {
        (str(row["table"]), str(row["lhs"]), str(row["rhs"])) for _, row in gt_df.iterrows()
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    # Remove stale generated case directories so table-filtered smoke runs do not
    # accidentally reuse tables from a previous full build.
    for existing_case_dir in output_dir.iterdir():
        if existing_case_dir.is_dir():
            shutil.rmtree(existing_case_dir)
    manifest_tables = []
    total_candidates = 0
    total_positives = 0
    total_negatives = 0

    for csv_path in sorted(source_dir.glob("*.csv")):
        table_name = csv_path.name
        if selected_tables and table_name not in selected_tables:
            continue

        clean_df = load_table(csv_path)
        dirty_df = inject_column_noise(clean_df, noise_rate=noise_rate, seed=seed, table_name=table_name)
        violation_map = compute_violation_map(clean_df)

        case_dir = output_dir / table_name
        case_dir.mkdir(parents=True, exist_ok=True)
        clean_df.to_csv(case_dir / "clean_data.csv", index=False)
        dirty_df.to_csv(case_dir / "dirty_data_mix_0.1.csv", index=False)

        gt_rows = []
        columns = clean_df.columns.tolist()
        pos_count = 0
        neg_count = 0
        for left_col in columns:
            for right_col in columns:
                if left_col == right_col:
                    continue
                is_positive = (table_name, left_col, right_col) in positive_pairs
                sample_type = "P" if is_positive else "N"
                violation_rows = violation_map[(left_col, right_col)]
                gt_rows.append(
                    {
                        "left_col": left_col,
                        "right_col": right_col,
                        "sample_type": sample_type,
                        "violation_rows": repr(violation_rows),
                        "violation_sample": make_violation_sample(
                            clean_df, left_col, right_col, violation_rows
                        ),
                    }
                )
                if is_positive:
                    pos_count += 1
                else:
                    neg_count += 1

        gt_case_df = pd.DataFrame(gt_rows)
        gt_case_df.to_csv(case_dir / "ground_truth.csv", index=False)

        table_manifest = {
            "table": table_name,
            "rows": int(len(clean_df)),
            "columns": int(len(columns)),
            "candidate_pairs": int(len(gt_rows)),
            "positives": int(pos_count),
            "negatives": int(neg_count),
            "case_dir": str(case_dir),
        }
        manifest_tables.append(table_manifest)
        total_candidates += len(gt_rows)
        total_positives += pos_count
        total_negatives += neg_count

    manifest = {
        "source_dir": str(source_dir),
        "ground_truth_path": str(ground_truth_path),
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "noise_rate": noise_rate,
        "seed": seed,
        "selected_tables": sorted(selected_tables) if selected_tables else None,
        "table_count": len(manifest_tables),
        "candidate_pairs": int(total_candidates),
        "positives": int(total_positives),
        "negatives": int(total_negatives),
        "tables": manifest_tables,
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def add_common_args(parser: argparse.ArgumentParser, project_root: Path) -> None:
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=project_root / "data" / "rwd",
        help="Directory containing official RWD source CSVs.",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=project_root / "data" / "rwd_ground_truth_perfect126.csv",
        help="Positive FD labels to use. Defaults to the Auto-Relate-compatible perfect-126 subset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "data" / "RWD_perfect126_fd",
        help="Output directory for the generated FD-style benchmark.",
    )
    parser.add_argument(
        "--noise-rate",
        type=float,
        default=DEFAULT_NOISE_RATE,
        help="Per-column corruption rate for dirty_data_mix_0.1.csv generation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base seed used for deterministic dirty-data generation.",
    )
    parser.add_argument(
        "--tables",
        type=str,
        default="",
        help="Optional comma-separated table whitelist, e.g. adult.csv,claims.csv.",
    )
