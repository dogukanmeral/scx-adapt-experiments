# Import libraries
from pathlib import Path
import pandas as pd

# Define paths and dataset configurations
OUT_DIR = Path(__file__).resolve().parent.parent / "datasets"

SEED = 42
SPLIT = (0.70, 0.15, 0.15 ) # train, val, test


def split_and_save_all_files():
    """Split combined_dataset.csv into train / val / test CSV files."""
    data = OUT_DIR / "combined_dataset.csv"

    # Read and shuffle
    df = pd.read_csv(data)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Compute split boundaries
    train_size = int(len(df) * SPLIT[0])
    val_size   = int(len(df) * SPLIT[1])

    train_df = df.iloc[:train_size]
    val_df   = df.iloc[train_size : train_size + val_size]
    test_df  = df.iloc[train_size + val_size :]

    print(f"  -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)} rows")

    # Save
    train_path = OUT_DIR / "train.csv"
    val_path   = OUT_DIR / "val.csv"
    test_path  = OUT_DIR / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path,     index=False)
    test_df.to_csv(test_path,   index=False)

    print(f"\nFinal splits saved:")
    print(f"  Train : {len(train_df):>7,} rows  ->  {train_path}")
    print(f"  Val   : {len(val_df):>7,} rows  ->  {val_path}")
    print(f"  Test  : {len(test_df):>7,} rows  ->  {test_path}")

def main():
    """Main function to orchestrate the splitting process."""
    split_and_save_all_files()
    print("\nDataset split complete!")

if __name__ == "__main__":
    main()