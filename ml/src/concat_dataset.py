# Import libraries
from pathlib import Path
import pandas as pd

# Define strings
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPPER_DATASETS = PROJECT_ROOT / "datasets"
ML_DATASETS = PROJECT_ROOT / "ml" / "datasets"

OUTPUT_FILE = ML_DATASETS / "combined_dataset.csv"

# Create datasets folder in ml/datasets if missing
ML_DATASETS.mkdir(parents=True, exist_ok=True)
print("Created datasets folder.")

# Read every csv from datasets and create dataFrames
csv_files = list(UPPER_DATASETS.glob("*.csv"))

if not csv_files:
    raise ValueError(f"No csv files in {UPPER_DATASETS}")

# Add every csv file as a dataFrame into a list
dfs = []

for file in csv_files:
    print(f"Reading: {file.name}")
    df = pd.read_csv(file)

    # Keep source file name info
    df["source_file"] = file.name

    dfs.append(df)
    
# Concatenate
combined_df = pd.concat(dfs, ignore_index=True)
print(f"Combined shape: {combined_df.shape}")

combined_df.to_csv(OUTPUT_FILE, index=False)