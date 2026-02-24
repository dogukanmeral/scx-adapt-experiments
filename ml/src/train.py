# Import libraries
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor

from evaluate import evaluate

# Paths
DATA_PATH = Path(__file__).resolve().parent.parent / "datasets"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

TRAIN_FILE = DATA_PATH / "train_preprocessed.csv"
VAL_FILE   = DATA_PATH / "val_preprocessed.csv"
TEST_FILE  = DATA_PATH / "test_preprocessed.csv"

MODEL_FILE = MODEL_PATH / "model.pkl"

# Target column to predict. Change here to switch prediction objectives.
# TODO Check TARGET variable for necessary changes after real-time execution in kernel.
TARGET = "load_avg_1"

# Columns that are never used as features (metadata / other targets).
DROP_COLS = ["time", TARGET]

# Data loading
def load_data():
    train = pd.read_csv(TRAIN_FILE)
    val   = pd.read_csv(VAL_FILE)
    test  = pd.read_csv(TEST_FILE)
    return train, val, test

# Feature / target split
def split_features_target(df):
    """Return (X, y) dropping metadata columns and the target column."""
    X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    y = df[TARGET]
    return X, y

# Model training
def train_model(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def main():
    MODEL_PATH.mkdir(exist_ok=True)

    train, val, test = load_data()

    X_train, y_train = split_features_target(train)
    X_val,   y_val   = split_features_target(val)
    X_test,  y_test  = split_features_target(test)

    print("Training model...")
    model = train_model(X_train, y_train)

    evaluate(model, X_val,  y_val,  label="Validation")
    evaluate(model, X_test, y_test, label="Test")

    joblib.dump(model, MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()