from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, _tree

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_DATASETS = PROJECT_ROOT / "ml" / "datasets"
RAW_DATASETS = PROJECT_ROOT / "datasets"
SAMPLE_PROFILES = PROJECT_ROOT / "sample-profiles"
OUTPUT_PROFILE = SAMPLE_PROFILES / "generated_tester.yaml"
COMBINED_FILE = ML_DATASETS / "combined_dataset.csv"

SCHEDULER_PATHS = {
    "simple": "/etc/scx-adapt/schedulers/simple.bpf.c.o",
    "flatcg": "/etc/scx-adapt/schedulers/flatcg.bpf.c.o",
    "prio": "/etc/scx-adapt/schedulers/prio.bpf.c.o",
    "rr": "/etc/scx-adapt/schedulers/rr.bpf.c.o",
}

FEATURE_DROP = ["time_ms", "source_file"]


def combine_datasets():
    """Combine all root telemetry CSVs into a single dataset for training."""
    ML_DATASETS.mkdir(parents=True, exist_ok=True)
    if COMBINED_FILE.exists():
        print(f"Using existing combined dataset: {COMBINED_FILE}")
        return

    csv_files = sorted(RAW_DATASETS.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DATASETS}")

    frames = []
    for csv_file in csv_files:
        print(f"Reading {csv_file.name}")
        df = pd.read_csv(csv_file)
        df["source_file"] = csv_file.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined dataset shape: {combined.shape}")
    combined.to_csv(COMBINED_FILE, index=False)
    print(f"Saved combined dataset to {COMBINED_FILE}")


def infer_scheduler_and_resource(df: pd.DataFrame) -> pd.DataFrame:
    source = df["source_file"].astype(str).str.lower()
    df = df.copy()
    df["scheduler"] = source.str.extract(r"^(flatcg|prio|rr|simple)-", expand=False).fillna("unknown")
    df["resource"] = source.str.extract(r"-(cpu|io|mem)\.csv$", expand=False).fillna("unknown")
    return df


def prepare_features(df: pd.DataFrame):
    df = infer_scheduler_and_resource(df)
    df = df.drop(columns=[c for c in FEATURE_DROP if c in df.columns])

    # Keep the scheduler label separate and encode resource as dummy variables
    X = pd.get_dummies(df.drop(columns=["scheduler"]), columns=["resource"], drop_first=False)
    y = df["scheduler"].astype(str)

    return X, y


def train_model(X: pd.DataFrame, y: pd.Series):
    model = DecisionTreeClassifier(
        max_depth=4,
        min_samples_leaf=50,
        random_state=42,
    )
    model.fit(X, y)
    return model


def extract_leaf_rules(tree, feature_names, class_names):
    tree_ = tree.tree_

    def recurse(node, conditions):
        if tree_.feature[node] == _tree.TREE_UNDEFINED:
            class_id = np.argmax(tree_.value[node][0])
            scheduler = class_names[class_id]
            return [{
                "scheduler": scheduler,
                "conditions": conditions.copy(),
                "samples": int(tree_.n_node_samples[node]),
            }]

        name = feature_names[tree_.feature[node]]
        threshold = float(tree_.threshold[node])

        left_conditions = conditions + [{
            "feature": name,
            "operator": "<=",
            "threshold": threshold,
        }]
        right_conditions = conditions + [{
            "feature": name,
            "operator": ">",
            "threshold": threshold,
        }]

        left_rules = recurse(tree_.children_left[node], left_conditions)
        right_rules = recurse(tree_.children_right[node], right_conditions)
        return left_rules + right_rules

    return recurse(0, [])


def normalize_rules(rules):
    best_rules = {}
    for rule in rules:
        scheduler = rule["scheduler"]
        current = best_rules.get(scheduler)
        if current is None or rule["samples"] > current["samples"]:
            best_rules[scheduler] = rule
    return list(best_rules.values())


def build_yaml_content(rules):
    selected = sorted(rules, key=lambda x: (-x["samples"], x["scheduler"]))
    lines = ["interval: 1000", "schedulers:"]

    for priority, rule in enumerate(selected, start=1):
        scheduler_name = rule["scheduler"]
        path = SCHEDULER_PATHS.get(scheduler_name, f"/etc/scx-adapt/schedulers/{scheduler_name}.bpf.c.o")
        lines.append(f"  - path: \"{path}\"")
        lines.append(f"    priority: {priority}")
        lines.append("    criterias:")

        if not rule["conditions"]:
            lines.append("      []")
            continue

        for cond in rule["conditions"]:
            key = "less_than" if cond["operator"] == "<=" else "more_than"
            value = round(float(cond["threshold"]), 6)
            if float(value).is_integer():
                value = int(value)
            lines.append("      - value_name: " + cond["feature"])
            lines.append(f"        {key}: {value}")

    return "\n".join(lines) + "\n"


def save_yaml(content: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Generated YAML profile at {path}")


def main():
    combine_datasets()
    df = pd.read_csv(COMBINED_FILE)
    df = infer_scheduler_and_resource(df)

    print("Scheduler distribution:")
    print(df["scheduler"].value_counts())

    X, y = prepare_features(df)
    model = train_model(X, y)

    rules = extract_leaf_rules(model, X.columns.tolist(), model.classes_.tolist())
    rules = normalize_rules(rules)

    print("Extracted scheduler rules from tree:")
    for rule in rules:
        print(f"  - {rule['scheduler']} ({rule['samples']} samples)")

    yaml_text = build_yaml_content(rules)
    save_yaml(yaml_text, OUTPUT_PROFILE)


if __name__ == "__main__":
    main()
