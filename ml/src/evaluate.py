# Import libraries
from pathlib import Path
import pandas as pd
import joblib

from sklearn.metrics import mean_absolute_error, r2_score

# Define paths and configs
DATA_PATH  = Path(__file__).resolve().parent.parent / "datasets"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

VAL_FILE  = DATA_PATH / "val_preprocessed.csv"
TEST_FILE = DATA_PATH / "test_preprocessed.csv"

MODEL_FILE = MODEL_PATH / "model.pkl"

TARGET    = "load_avg_1"
DROP_COLS = ["time", TARGET]


# Compute MAE and R²
def evaluate(model, X, y, label: str = "") -> dict:
    """Print and return MAE + R² for *model* on (X, y)."""
    preds = model.predict(X)
    mae   = mean_absolute_error(y, preds)
    r2    = r2_score(y, preds)

    header = f"── {label} ──" if label else "── Evaluation ──"
    print(f"\n{header}")
    print(f"  MAE : {mae:.6f}")
    print(f"  R²  : {r2:.6f}")

    return {"mae": mae, "r2": r2}

def _load_split(path: Path):
    df = pd.read_csv(path)
    X  = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    y  = df[TARGET]
    return X, y


def main():
    print(f"Loading model from {MODEL_FILE}")
    model = joblib.load(MODEL_FILE)

    X_val,  y_val  = _load_split(VAL_FILE)
    X_test, y_test = _load_split(TEST_FILE)

    evaluate(model, X_val,  y_val,  label="Validation")
    evaluate(model, X_test, y_test, label="Test")


if __name__ == "__main__":
    main()