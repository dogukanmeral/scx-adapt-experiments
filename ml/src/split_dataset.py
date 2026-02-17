from pathlib import Path
import shutil
import random
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "datasets"

SEED = 42
SPLIT = (0.70, 0.15, 0.15 ) # train, val, test

def split_and_save_all_files():
    """Split csv into train/val/test sets with equal distribution."""
    data = OUT_DIR / "combined_dataset.csv"

    # Lists to accumulate each split
    train_rows = []
    val_rows = []
    test_rows = []

    # Random seed for reproducability
    random.seed(SEED)

    # Read the data
    df = pd.read_csv(data)

    # Shuffle the rows
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    # Initialize train/val/test sizes
    train_size = int(len(df) * SPLIT[0])
    val_size = int(len(df) * SPLIT[1])

    # Split rows
    train_df = df.iloc[:train_size]
    val_df = df.iloc[train_size:train_size + val_size]
    test_df = df.iloc[train_size + val_size:]

    train_rows.append(train_df)
    val_rows.append(val_df)
    test_rows.append(test_df)

    print(f"  -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)} rows")

    # Combine all splits
    train_combined = pd.concat(train_rows, ignore_index=True)
    val_combined = pd.concat(val_rows, ignore_index=True)
    test_combined = pd.concat(test_rows, ignore_index=True)
    
    # Save to CSV files
    train_path = OUT_DIR / "train.csv"
    val_path = OUT_DIR / "val.csv"
    test_path = OUT_DIR / "test.csv"
    
    train_combined.to_csv(train_path, index=False)
    val_combined.to_csv(val_path, index=False)
    test_combined.to_csv(test_path, index=False)
    
    print(f"\nFinal splits:")
    print(f"Train set: {len(train_combined)} rows -> {train_path}")
    print(f"Val set:   {len(val_combined)} rows -> {val_path}")
    print(f"Test set:  {len(test_combined)} rows -> {test_path}")

def main():
    """Main function to orchestrate the splitting process."""
    split_and_save_all_files()
    print("\nDataset split complete!")

if __name__ == "__main__":
    main()
        