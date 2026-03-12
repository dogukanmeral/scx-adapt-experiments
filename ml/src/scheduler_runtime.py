def choose_scheduler(model, base_features):

    # Copy features
    rr_features = base_features.copy()
    prio_features = base_features.copy()

    # Set scheduler flags
    rr_features["scheduler_RR"] = 1
    rr_features["scheduler_PRIORITY"] = 0

    prio_features["scheduler_RR"] = 0
    prio_features["scheduler_PRIORITY"] = 1

    # Predict loads
    load_rr = model.predict([rr_features])[0]
    load_prio = model.predict([prio_features])[0]

    # Choose scheduler that gives lower load
    if load_rr < load_prio:
        return "RR"
    else:
        return "PRIO"