import os
import sys
import json
import time
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_EXPERIMENT_PATH = os.path.join(PROJECT_ROOT, "code", "experiment")
AUTO_RELATE_PATH = os.path.join(PROJECT_ROOT, "code", "auto_relate")

sys.path.append(CODE_EXPERIMENT_PATH)
sys.path.append(AUTO_RELATE_PATH)

import measure_and_save_result
import optimization_flags
import optimization_stats


def count_rows(csv_path):
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, "r", encoding="utf-8") as f:
        return max(sum(1 for _ in f) - 1, 0)


def percentile(sorted_values, percent):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * (percent / 100)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def timing_summary(csv_path):
    runtimes = []
    if not os.path.exists(csv_path):
        return {
            "path": csv_path,
            "count": 0,
            "p50_seconds": None,
            "p90_seconds": None,
            "p95_seconds": None,
            "avg_seconds": None,
        }
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            value = row.get("verification_runtime_seconds", "")
            if value == "":
                continue
            runtimes.append(float(value))
    runtimes.sort()
    return {
        "path": csv_path,
        "count": len(runtimes),
        "p50_seconds": round(percentile(runtimes, 50), 6) if runtimes else None,
        "p90_seconds": round(percentile(runtimes, 90), 6) if runtimes else None,
        "p95_seconds": round(percentile(runtimes, 95), 6) if runtimes else None,
        "avg_seconds": round(sum(runtimes) / len(runtimes), 6) if runtimes else None,
    }


def main():
    methods = ["Auto-Relate"]
    dataset_path = os.environ.get(
        "AUTO_RELATE_DATASET_PATH",
        os.path.join(PROJECT_ROOT, "data", "AR"),
    )
    data_type = os.environ.get("AUTO_RELATE_DATA_TYPE", "all")
    result_save_folder_path = os.environ.get(
        "AUTO_RELATE_RESULT_DIR",
        os.path.join(PROJECT_ROOT, "results", "ar"),
    )
    optimization_stats.reset()
    start = time.perf_counter()
    measure_and_save_result.run(dataset_path, data_type, "AR", methods, result_save_folder_path)
    runtime_seconds = time.perf_counter() - start

    method_dir = os.path.join(result_save_folder_path, "Auto-Relate")
    clean_rows = count_rows(os.path.join(method_dir, "clean_data_result.csv"))
    dirty_rows = count_rows(os.path.join(method_dir, "dirty_data_result.csv"))
    total_rows = clean_rows + dirty_rows
    clean_timing_summary = timing_summary(os.path.join(method_dir, "clean_data_timing_log.csv"))
    dirty_timing_summary = timing_summary(os.path.join(method_dir, "dirty_data_timing_log.csv"))
    stats = optimization_stats.snapshot()
    perturbation_test_candidates = (
        stats.get("ht_single_perturb_calls", 0.0)
        + stats.get("ht_bound_sample_skip_calls", 0.0)
    )
    sampling_loop_skipped_candidates = (
        stats.get("ht_single_perturb_calls", 0.0)
        + stats.get("groupby_early_rejects", 0.0)
    )
    sampling_loop_candidates = stats.get("multicol_sample_calls", 0.0)
    binomial_effective_candidates = (
        stats.get("binomial_early_stop_accept", 0.0)
        + stats.get("binomial_early_stop_reject", 0.0)
    )
    summary = {
        "variant": os.environ.get("AUTO_RELATE_VARIANT_NAME", "default"),
        "task": "AR",
        "data_type": data_type,
        "result_dir": result_save_folder_path,
        "runtime_seconds": round(runtime_seconds, 4),
        "result_rows": {
            "clean_data_result.csv": clean_rows,
            "dirty_data_result.csv": dirty_rows,
            "total": total_rows,
        },
        "throughput_rows_per_second": round(total_rows / runtime_seconds, 4) if runtime_seconds > 0 else None,
        "per_candidate_timing": {
            "clean_data": clean_timing_summary,
            "dirty_data": dirty_timing_summary,
        },
        "flags": {
            "disable_groupby_bound": optimization_flags.disable_groupby_bound(),
            "disable_closed_form": optimization_flags.disable_closed_form(),
            "disable_binomial_bound": optimization_flags.disable_binomial_bound(),
        },
        "optimization_stats": stats,
        "paper_style_metrics": {
            "perturbation_test_candidates": int(perturbation_test_candidates),
            "sampling_loop_skipped_candidates": int(sampling_loop_skipped_candidates),
            "sampling_loop_skipped_rate": round(
                sampling_loop_skipped_candidates / perturbation_test_candidates, 4
            )
            if perturbation_test_candidates
            else None,
            "sampling_loop_candidates": int(sampling_loop_candidates),
            "binomial_effective_candidates": int(binomial_effective_candidates),
            "binomial_effective_rate": round(
                binomial_effective_candidates / sampling_loop_candidates, 4
            )
            if sampling_loop_candidates
            else None,
            "closed_form_candidate_level_counter_available": False,
            "closed_form_paper_rate_note": (
                "Not directly recoverable from the current public release: "
                "the paper describes an applicability/effective rate for the "
                "closed-form speed-up, but the released implementation does "
                "not expose an equivalent staged candidate-level counter. "
                "The closest legacy hook is formula_analyze.isolatable(...), "
                "which is not wired into the released perturbation-test path."
            ),
        },
    }
    with open(os.path.join(result_save_folder_path, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
