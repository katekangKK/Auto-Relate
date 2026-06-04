import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_EXPERIMENT_PATH = os.path.join(PROJECT_ROOT, "code", "experiment")

sys.path.append(CODE_EXPERIMENT_PATH)

import measure_and_save_result


def main():
    methods = ["Auto-Relate"]
    dataset_path = os.environ.get(
        "AUTO_RELATE_DATASET_PATH",
        os.path.join(PROJECT_ROOT, "data", "FD"),
    )
    data_type = os.environ.get("AUTO_RELATE_DATA_TYPE", "all")
    result_save_folder_path = os.environ.get(
        "AUTO_RELATE_RESULT_DIR",
        os.path.join(PROJECT_ROOT, "results", "fd"),
    )
    measure_and_save_result.run(dataset_path, data_type, "FD", methods, result_save_folder_path)


if __name__ == "__main__":
    main()
