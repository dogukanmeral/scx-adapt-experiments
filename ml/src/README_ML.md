ML scripts in `ml/src` implement the data preparation, training, and evaluation flow for scheduler telemetry.

# Pipeline overview

1. `concat_dataset.py`
   - Input: CSV files in the repository root `datasets/` folder.
   - Output: `ml/datasets/combined_dataset.csv`.
   - Action: reads every CSV in root `datasets/`, adds a `source_file` column, and concatenates them.

2. `split_dataset.py`
   - Input: `ml/datasets/combined_dataset.csv`.
   - Output: `ml/datasets/train.csv`, `ml/datasets/val.csv`, `ml/datasets/test.csv`.
   - Action: shuffles the combined dataset with `random_state=42` and splits it into 70% train, 15% validation, and 15% test.

3. `preprocessing.py`
   - Input: `ml/datasets/train.csv`, `ml/datasets/val.csv`, `ml/datasets/test.csv`.
   - Output: `ml/datasets/train_preprocessed.csv`, `ml/datasets/val_preprocessed.csv`, `ml/datasets/test_preprocessed.csv`.
   - Action:
     - deduplicates rows
     - converts `time_ms` into Unix seconds in a new `time` column
     - extracts `scheduler` and `resource` labels from `source_file`
     - fills missing values with forward fill and zero
     - one-hot encodes `scheduler` and `resource`
     - drops `time_ms` and `source_file`
     - scales numeric columns with `StandardScaler` fitted only on the train split

# Training

4. `train.py`
   - Input: `ml/datasets/train_preprocessed.csv`, `ml/datasets/val_preprocessed.csv`, `ml/datasets/test_preprocessed.csv`.
   - Output:
     - `models/model.pkl`
     - `models/scheduler_tree.json`
   - Target: `load_avg_1`
   - Features: all preprocessed columns except `time` and `load_avg_1`
   - Random Forest parameters:
     - `n_estimators=50`
     - `max_depth=10`
     - `min_samples_leaf=5`
     - `random_state=42`
     - `n_jobs=-1`
   - Surrogate decision tree parameters:
     - `max_depth=5`
     - `min_samples_leaf=20`
   - Action: trains the regressor on the training data, evaluates on validation/test data, saves the RF model, and exports a surrogate tree.

# Evaluation

5. `evaluate.py`
   - Input: `models/model.pkl`, `ml/datasets/val_preprocessed.csv`, `ml/datasets/test_preprocessed.csv`.
   - Output: printed MAE and R² values, plus validation prediction statistics.
   - Metrics reported:
     - mean absolute error (MAE)
     - coefficient of determination (R²)
   - Additional validation output:
     - min, mean, max predicted load
     - 25th, 50th, 75th, and 90th percentiles

# Rule/Profile generation

6. `generate_profile.py`
   - Input: raw `datasets/*.csv` files or existing `ml/datasets/combined_dataset.csv`.
   - Output: `sample-profiles/generated_tester.yaml`.
   - Action: trains a `DecisionTreeClassifier` to infer scheduler selection rules from raw telemetry.
   - Classifier parameters:
     - `max_depth=4`
     - `min_samples_leaf=50`
     - `random_state=42`
   - It extracts scheduler/resource labels from file names and emits YAML rules for scheduler selection.

# Model export and runtime helpers

7. `pkl_converter.py`
   - Input: `models/model.pkl`
   - Output: `models/rf_model.h`
   - Action: converts the trained Random Forest into static C data structures and prediction code.

8. `scheduler_runtime.py`
   - Input: `models/scheduler_tree.json`
   - Output: runtime scheduler decision based on predicted load.
   - Action: loads the surrogate JSON tree and maps predicted load into either `RR` or `PRIO`.

# Typical execution order

```bash
cd ml/src
python concat_dataset.py
python split_dataset.py
python preprocessing.py
python train.py
python evaluate.py
```

Optional additional generation:

```bash
python generate_profile.py
python pkl_converter.py
```

# Notes

- The primary ML target is `load_avg_1`.
- The preprocessing pipeline keeps scheduler/resource metadata and converts it into numeric features.
- The training outputs are saved under `models/`.
