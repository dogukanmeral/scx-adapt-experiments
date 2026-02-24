# Importing libraries
from pathlib import Path 
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Add paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRAIN_FILE = Path(__file__).resolve().parent.parent / "datasets" / "train.csv"
VAL_FILE = Path(__file__).resolve().parent.parent / "datasets" / "val.csv"
TEST_FILE = Path(__file__).resolve().parent.parent / "datasets" / "test.csv"

TRAIN_FILE_PREPROCESSED = Path(__file__).resolve().parent.parent / "datasets" / "train_preprocessed.csv"
VAL_FILE_PREPROCESSED = Path(__file__).resolve().parent.parent / "datasets" / "val_preprocessed.csv"
TEST_FILE_PREPROCESSED = Path(__file__).resolve().parent.parent / "datasets" / "test_preprocessed.csv"

# Load data for preprocessing
def load_data(data_path):
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    return df

# Dropping duplicates
def basic_cleaning(df):

    print("Running basic cleaning...")
    
    return df.drop_duplicates()

# time_ms processing
def process_time(df):
    """Convert time_ms to a Unix timestamp (int64 seconds) and sort.

    Previously stored as datetime64, which serialises to an ISO string in CSV
    and is then silently ignored during scaling/feature selection. Storing as
    a plain integer keeps it usable as a numeric feature.
    """
    print("Processing time column...")

    time_dt = pd.to_datetime(df["time_ms"], unit="ms", errors="coerce")
    df = df.copy()
    df["time"] = time_dt.astype("int64") // 10 ** 9  # Unix seconds (int64)
    df = df.sort_values("time")

    return df

# source_file resource extraction / "resource" and "scheduler" creation
def extract_resource(df):

    print("Extracting scheduler + resource...")

    df["source_file"] = df["source_file"].astype(str).str.lower()

    df["scheduler"] = (
        df["source_file"]
        .str.extract("(prio|rr)", expand=False)
        .replace({"prio": "PRIORITY", "rr": "RR"})
    )

    df["resource"] = (
        df["source_file"]
        .str.extract(r"(cpu|io|mem)", expand=False)
        .str.upper()
    )

    return df

# Handle missing values
def handle_missing_values(df):

    print("Handling missing values...")

    df = df.ffill().fillna(0)

    return df

# Categorical Feature encoding
def encode_categorical(df):

    print("Encoding categorical...")

    df = pd.get_dummies(df, columns=["scheduler", "resource"])

    return df

# Drop unused columns
def drop_unused(df):

    print("Dropping unused columns...")

    drop_cols = ["time_ms", "source_file"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    return df

# Scale features
def scale_train_val_test(train_df, val_df, test_df):
    print("Scaling numeric columns (FIT ON TRAIN ONLY)...")

    scaler = StandardScaler()

    numeric_cols = train_df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    # FIT ONLY TRAIN
    scaler.fit(train_df[numeric_cols])

    # TRANSFORM ALL
    train_df[numeric_cols] = scaler.transform(train_df[numeric_cols])
    val_df[numeric_cols] = scaler.transform(val_df[numeric_cols])
    test_df[numeric_cols] = scaler.transform(test_df[numeric_cols])

    return train_df, val_df, test_df

# Preprocess dataFrame
def preprocess_df(df):
    df = basic_cleaning(df)
    df = process_time(df)
    df = extract_resource(df)
    df = handle_missing_values(df)
    df = encode_categorical(df)
    df = drop_unused(df)

    return df

def main():

    # Load
    train = load_data(TRAIN_FILE)
    val = load_data(VAL_FILE)
    test = load_data(TEST_FILE)

    # Preprocess (NO SCALING YET)
    train = preprocess_df(train)
    val = preprocess_df(val)
    test = preprocess_df(test)

    # Align columns (very important for get_dummies)
    val = val.reindex(columns=train.columns, fill_value=0)
    test = test.reindex(columns=train.columns, fill_value=0)

    # Scaling (FIT TRAIN ONLY)
    train, val, test = scale_train_val_test(train, val, test)

    # Save
    train.to_csv(TRAIN_FILE_PREPROCESSED, index=False)
    val.to_csv(VAL_FILE_PREPROCESSED, index=False)
    test.to_csv(TEST_FILE_PREPROCESSED, index=False)

    print("Preprocessing completed successfully!")


if __name__ == "__main__":
    main()