from __future__ import annotations

import argparse
import json
import os
import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_EXPERIMENT_PATH = PROJECT_ROOT / "code" / "experiment"

sys.path.append(str(CODE_EXPERIMENT_PATH))

import measure_and_save_result
import rwd_benchmark


def count_rows(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    with csv_path.open("r", encoding="utf-8") as f:
        return max(sum(1 for _ in f) - 1, 0)


def should_reuse_manifest(
    manifest: dict[str, object],
    selected_tables: set[str] | None,
    source_dir: Path,
    ground_truth_path: Path,
    noise_rate: float,
    seed: int,
) -> bool:
    manifest_tables = manifest.get("selected_tables")
    if manifest_tables is None:
        manifest_table_set = None
    else:
        manifest_table_set = set(manifest_tables)

    return (
        manifest.get("source_dir") == str(source_dir)
        and manifest.get("ground_truth_path") == str(ground_truth_path)
        and float(manifest.get("noise_rate", -1)) == float(noise_rate)
        and int(manifest.get("seed", -1)) == int(seed)
        and manifest_table_set == selected_tables
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the RWD perfect-126 benchmark and run Auto-Relate with the existing FD pipeline."
    )
    rwd_benchmark.add_common_args(parser, PROJECT_ROOT)
    parser.add_argument(
        "--data-type",
        choices=["clean_data", "dirty_data", "all"],
        default="all",
        help="Which split to run through the existing FD pipeline.",
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "rwd",
        help="Directory where Auto-Relate result CSVs will be written.",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Only materialize the benchmark directory without running Auto-Relate.",
    )
    args = parser.parse_args()

    selected_tables = rwd_benchmark.parse_tables_arg(args.tables)
    expected_manifest = args.output_dir.parent / f"{args.output_dir.name}_manifest.json"
    if expected_manifest.exists() and args.output_dir.exists():
        with expected_manifest.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        reuse_manifest = should_reuse_manifest(
            manifest,
            selected_tables,
            args.source_dir,
            args.ground_truth,
            args.noise_rate,
            args.seed,
        )
    else:
        reuse_manifest = False

    if not reuse_manifest:
        manifest = rwd_benchmark.build_rwd_fd_benchmark(
            source_dir=args.source_dir,
            ground_truth_path=args.ground_truth,
            output_dir=args.output_dir,
            noise_rate=args.noise_rate,
            seed=args.seed,
            selected_tables=selected_tables,
        )

    summary = {
        "benchmark_manifest": manifest,
        "data_type": args.data_type,
        "result_dir": str(args.result_dir),
        "prepare_only": args.prepare_only,
    }

    args.result_dir.mkdir(parents=True, exist_ok=True)

    if not args.prepare_only:
        methods = ["Auto-Relate"]
        measure_and_save_result.run(
            str(args.output_dir),
            args.data_type,
            "FD",
            methods,
            str(args.result_dir),
        )
        method_dir = args.result_dir / "Auto-Relate"
        summary["result_rows"] = {
            "clean_data_result.csv": count_rows(method_dir / "clean_data_result.csv"),
            "dirty_data_result.csv": count_rows(method_dir / "dirty_data_result.csv"),
        }

    with (args.result_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
