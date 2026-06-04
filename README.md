# Auto-Relate

Auto-Relate is a unified method for discovering reliable functional relationships in tabular data through statistical testing.

This repository provides the public implementation of Auto-Relate, including the source code and scripts required to run the released method on arithmetic relationships, string transformations, and functional dependencies.

## Repository Structure

```text
code/
  auto_relate/            Auto-Relate arithmetic-relation discovery code
  auto_relate_fd_mod/     Functional-dependency relation discovery code
  auto_relate_pbe_mod/    String-transformation discovery code and PBE runtime
  experiment/             Evaluation drivers for the released method
  testdata/               A small smoke-test table
scripts/
  run_auto_relate_ar.py   Run Auto-Relate on arithmetic-relationship data
  run_auto_relate_st.py   Run Auto-Relate on string-transformation data
  run_auto_relate_fd.py   Run Auto-Relate on functional-dependency data
```

## Installation

The code was developed with Python 3.12. The released scripts require Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The string-transformation runner uses the bundled PBE runtime DLLs under `code/auto_relate_pbe_mod/PythonDemo_AutoRelate/dlls`.

## Datasets

We built the first large-scale benchmark suite for functional relationship discovery. The benchmark was collected from 58,679 real-world spreadsheets and relational tables and contains 6,414 real functional relationships covering all three types of functional relationships (FRs): arithmetic relationships, string transformations, and functional dependencies.
This benchmark enables a systematic evaluation of the functional relationship discovery problem and can serve as a useful resource for future research.

The benchmark datasets are available at Google Drive: 
[https://drive.google.com/drive/folders/1wVgqzdhtQzbvYKBWM2kcznM8HJDXuIH2?usp=sharing](https://drive.google.com/drive/folders/1wVgqzdhtQzbvYKBWM2kcznM8HJDXuIH2?usp=sharing)


Place the downloaded folders under the repository root with the following structure:

```text
Auto-Relate/
  data/
    AR/
    ST/
    FD/
```

The default scripts expect the following dataset paths:

```text
data/AR   Arithmetic relationships
data/ST   String transformations
data/FD   Functional dependencies
```

<!-- The released repository does not include baseline outputs, logs, plots, paper result artifacts, or the comparison-method implementations. -->

## Quick Start

<!-- Step 1: Check the Python setup with the bundled smoke test.

```bash
python code/auto_relate/PythonDemo_AutoRelate_math.py
```

This command runs on `code/testdata/test_data_program.csv` and should print discovered aggregate programs such as `sum` and `mean`. -->

### 1. Run Arithmetic Relationship Discovery

```bash
python scripts/run_auto_relate_ar.py
```

The script reads datasets from `data/AR` and writes outputs to `results/ar`.

### 2. Run String Transformation Discovery

```bash
python scripts/run_auto_relate_st.py
```

The script reads datasets from `data/ST` and writes outputs to `results/st`.

### 3. Run Functional Dependency Discovery

```bash
python scripts/run_auto_relate_fd.py
```

The script reads datasets from `data/FD` and writes outputs to `results/fd`.

## Outputs

Each runner creates an `Auto-Relate` subdirectory under its configured result directory.

```text
results/
  ar/
    Auto-Relate/
      clean_data_result.csv
      dirty_data_result.csv
      clean_data_timing_log.csv
      dirty_data_timing_log.csv
    summary.json
  st/
    Auto-Relate/
      clean_data_result.csv
      dirty_data_result.csv
  fd/
    Auto-Relate/
      clean_data_result.csv
      dirty_data_result.csv
```

The generated files contain Auto-Relate's discovery results for the corresponding clean and dirty data settings.

## Configuration

By default, each script runs both the clean and dirty data settings using the standard dataset and result paths described above.

The default configuration can be overridden with environment variables:

```bash
AUTO_RELATE_DATASET_PATH=/path/to/AR \
AUTO_RELATE_DATA_TYPE=all \
AUTO_RELATE_RESULT_DIR=results/ar \
python scripts/run_auto_relate_ar.py
```

The `AUTO_RELATE_DATA_TYPE` variable supports the following values:

```
clean_data    Run only the clean-data setting
dirty_data    Run only the dirty-data setting
all           Run both clean- and dirty-data settings
```

<!-- `AUTO_RELATE_DATA_TYPE` can be set to `clean_data`, `dirty_data`, or `all`. -->
