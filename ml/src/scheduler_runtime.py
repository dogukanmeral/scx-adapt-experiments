import json
from pathlib import Path

MODEL_FILE = Path(__file__).resolve().parent.parent / "models" / "scheduler_tree.json"

with open(MODEL_FILE) as f:
    model = json.load(f)


def predict_tree(model, features):
    node = 0

    while model["feature"][node] != -2:
        feature_index = model["feature"][node]
        threshold = model["threshold"][node]

        if features[feature_index] <= threshold:
            node = model["children_left"][node]
        else:
            node = model["children_right"][node]

    return model["value"][node]


def choose_scheduler(predicted_load):

    if predicted_load < -0.404:
        # Percentile decided by lighter-load, switch to RR if load is lighter.
        return "RR"

    else:
        return "PRIO"

# Runtime decision function
def decide_scheduler(features):

    predicted_load = predict_tree(model, features)

    scheduler = choose_scheduler(predicted_load)

    return scheduler