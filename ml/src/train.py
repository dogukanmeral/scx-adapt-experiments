# Import libraries
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Initialize paths
DATA_PATH = Path(__file__).resolve().parent.parent / "datasets"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

TRAIN_FILE = DATA_PATH / "train_preprocessed.csv"
VAL_FILE = DATA_PATH / "val_preprocessed.csv"
TEST_FILE = DATA_PATH / "test_preprocessed.csv"

MODEL_PRIO_PATH = MODEL_PATH / "model_prio.pkl"
MODEL_RR_PATH = MODEL_PATH / "model_rr.pkl"

# Load data
def load_data():
    train = pd.read_csv(TRAIN_FILE)
    val = pd.read_csv(VAL_FILE)
    test = pd.read_csv(TEST_FILE)
    return train, val, test

# Splitting feature and target variables
def split_features_target(df):
    # TODO For the first iteration, only focused on load_avg_1
    target = "load_avg_1"

    drop_cols = [
        "time",
        "load_avg_1"  # target
    ]

    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df[target]

    return X, y

# Filtering by scheduler
def filter_scheduler(df, scheduler_name):

    col = f"scheduler_{scheduler_name}"

    return df[df[col] == 1].copy()

# Training the model
def train_model(X, y):

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)
    return model

# Simple evaluation
def evaluate(model, X, y, name):

    preds = model.predict(X)

    print(f"\n{name}")
    print("MAE:", mean_absolute_error(y, preds))
    print("R2 :", r2_score(y, preds))

# Main function
def main():

    MODEL_PATH.mkdir(exist_ok=True)

    train, val, test = load_data()

    # Split by scheduler
    train_prio = filter_scheduler(train, "PRIORITY")
    train_rr = filter_scheduler(train, "RR")

    val_prio = filter_scheduler(val, "PRIORITY")
    val_rr = filter_scheduler(val, "RR")

    test_prio = filter_scheduler(test, "PRIORITY")
    test_rr = filter_scheduler(test, "RR")

    # Split X / y
    X_train_prio, y_train_prio = split_features_target(train_prio)
    X_train_rr, y_train_rr = split_features_target(train_rr)

    X_val_prio, y_val_prio = split_features_target(val_prio)
    X_val_rr, y_val_rr = split_features_target(val_rr)

    X_test_prio, y_test_prio = split_features_target(test_prio)
    X_test_rr, y_test_rr = split_features_target(test_rr)

    # Train
    print("\nTraining PRIO model...")
    model_prio = train_model(X_train_prio, y_train_prio)

    print("\nTraining RR model...")
    model_rr = train_model(X_train_rr, y_train_rr)

    # Evaluate
    evaluate(model_prio, X_val_prio, y_val_prio, "PRIO Validation")
    evaluate(model_rr, X_val_rr, y_val_rr, "RR Validation")

    evaluate(model_prio, X_test_prio, y_test_prio, "PRIO Test")
    evaluate(model_rr, X_test_rr, y_test_rr, "RR Test")

    # Save
    joblib.dump(model_prio, MODEL_PRIO_PATH)
    joblib.dump(model_rr, MODEL_RR_PATH)

    print("\nModels saved!")

if __name__ == "__main__":
    main()