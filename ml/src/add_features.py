# Import libraries
from pathlib import Path
import pandas as pd

# Define strings
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET = PROJECT_ROOT / "ml" / "datasets" / "combined_dataset.csv"

# Read csv file
df = pd.read_csv(DATASET)
print(f"Reading {DATASET}")

# Normalize column
df["source_file"] = df["source_file"].str.lower()

# Add "scheduler" features
df["scheduler"] = df["source_file"].str.extract("(prio|rr)").replace({
    "prio": "PRIORITY",
    "rr": "RR"
})

# Add "resource" features (task type)
df["resource"] = df["source_file"].str.extract(r"\b(cpu|io|mem)\b")[0].str.upper()

print(df[["source_file", "scheduler", "resource"]].head())