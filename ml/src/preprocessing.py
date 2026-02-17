# Importing libraries
from pathlib import Path 
import pandas as pd
import numpy as np

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
    # TODO Possible Error drop_duplicates ain't highlighted
    print("Running basic cleaning...")

    df = df.drop_duplicates()

    return df

# Time processing
