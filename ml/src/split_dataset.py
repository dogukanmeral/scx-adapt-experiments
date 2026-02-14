from pathlib import Path
import shutil
import random
import pandas as pd

IN_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"
OUT_DIR = Path(__file__).resolve().parent.parent / "datasets"

SEED = 42
SPLIT = (0.70, 0.15, 0.15 ) # train, val, test

def reset_data_folders():

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    OUT_DIR.mkdir(parents=True, exist_ok=True)