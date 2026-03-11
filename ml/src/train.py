# Import libraries
from pathlib import Path
import pandas as pd
import joblib
import json

from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor, export_text

from evaluate import evaluate

# Paths
DATA_PATH = Path(__file__).resolve().parent.parent / "datasets"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

TRAIN_FILE = DATA_PATH / "train_preprocessed.csv"
VAL_FILE   = DATA_PATH / "val_preprocessed.csv"
TEST_FILE  = DATA_PATH / "test_preprocessed.csv"

MODEL_FILE = MODEL_PATH / "model.pkl"
TREE_FILE  = MODEL_PATH / "scheduler_tree.json"

# Target column to predict
TARGET = "load_avg_1"

# Columns never used as features
DROP_COLS = ["time", TARGET]

# Data loading
def load_data():
    train = pd.read_csv(TRAIN_FILE)
    val   = pd.read_csv(VAL_FILE)
    test  = pd.read_csv(TEST_FILE)
    return train, val, test

# Feature / target split
def split_features_target(df):
    X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    y = df[TARGET]
    return X, y

# Random Forest training (smaller + faster)
def train_model(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=50,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model

# Train surrogate decision tree to approximate RF
def train_surrogate_tree(rf_model, X_train):
    rf_predictions = rf_model.predict(X_train)

    surrogate = DecisionTreeRegressor(
        max_depth=5,
        min_samples_leaf=20,
        random_state=42
    )

    surrogate.fit(X_train, rf_predictions)
    return surrogate

# Export decision tree to JSON
def export_tree_to_json(tree, feature_names, output_file):
    tree_ = tree.tree_

    tree_dict = {
        "feature_names": feature_names,
        "children_left": tree_.children_left.tolist(),
        "children_right": tree_.children_right.tolist(),
        "feature": tree_.feature.tolist(),
        "threshold": tree_.threshold.tolist(),
        "value": tree_.value.flatten().tolist()
    }

    with open(output_file, "w") as f:
        json.dump(tree_dict, f, indent=4)

def main():
    MODEL_PATH.mkdir(exist_ok=True)

    train, val, test = load_data()

    X_train, y_train = split_features_target(train)
    X_val,   y_val   = split_features_target(val)
    X_test,  y_test  = split_features_target(test)

    print("Training Random Forest model...")
    model = train_model(X_train, y_train)

    evaluate(model, X_val,  y_val,  label="Validation")
    evaluate(model, X_test, y_test, label="Test")

    print("\nTraining surrogate decision tree...")
    surrogate_tree = train_surrogate_tree(model, X_train)

    print("\nExporting surrogate tree...")
    export_tree_to_json(
        surrogate_tree,
        X_train.columns.tolist(),
        TREE_FILE
    )

    print("\nSurrogate scheduler rules:\n")
    rules = export_text(surrogate_tree, feature_names=list(X_train.columns))
    print(rules)

    joblib.dump(model, MODEL_FILE)
    print(f"\nRandom Forest model saved to {MODEL_FILE}")
    print(f"Surrogate tree exported to {TREE_FILE}")

if __name__ == "__main__":
    main()