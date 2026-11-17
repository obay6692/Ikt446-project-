"""Show expected trips in one Oslo-local hour using a saved trained model.

Use checkpoints produced by --phase test. Only use checkpoints from trusted
sources. Does not require actual future outcomes and is not a deployed system.
"""
import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from src.features import build_features
from src.models import load_mlp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hour", required=True, help='Oslo local hour: "2026-09-15 08:00"')
    p.add_argument("--model", choices=["rf", "mlp"], default="rf")
    args = p.parse_args()
    stamp = pd.Timestamp(args.hour)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("Europe/Oslo", ambiguous="raise", nonexistent="raise")
    else:
        stamp = stamp.tz_convert("Europe/Oslo")
    if stamp.minute or stamp.second or stamp.microsecond:
        p.error("Use a whole-hour timestamp (minutes/seconds must be zero)")
    X = build_features(pd.DataFrame({"timestamp_oslo": [stamp]}))
    if args.model == "rf":
        path = Path("outputs/test/random_forest.joblib")
        if not path.exists():
            p.error("RF checkpoint missing: run --phase test first")
        # Warning: never load untrusted .joblib files; pickle can execute code.
        model = joblib.load(path)
        prediction = float(model.predict(X)[0])
    else:
        path = Path("outputs/test/mlp_checkpoint.pt")
        if not path.exists():
            p.error("MLP checkpoint missing: run --phase test first")
        payload, model = load_mlp(path)
        a = X.to_numpy(dtype="float32")
        x_scaled = (a - np.array(payload["scaler_x_mean"], dtype="float32")) / np.array(
            payload["scaler_x_scale"], dtype="float32")
        model.eval()
        with torch.no_grad():
            raw = model(torch.from_numpy(x_scaled)).item()
        prediction = (raw * payload["scaler_y_scale"][0]
                      + payload["scaler_y_mean"][0])
    print(f"Oslo: {stamp} | Model: {args.model} | Predicted trips: {max(0, prediction):.0f}")


if __name__ == "__main__":
    main()
