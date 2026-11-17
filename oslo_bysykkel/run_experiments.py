"""IKT466: comparison + training-size investigation, fixed chronological partitions.

Run --phase validation first. Test should be run only after checking your fixed
config and hypotheses; do NOT tune on the held-out test results.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import time

import numpy as np
import pandas as pd
import sklearn
import torch

from src.data import load_config, load_hourly, split_by_year, subset_training_days
from src.evaluate import metrics, save_predictions, draw_example, draw_learning_curve
from src.features import build_features, FEATURE_NAMES
from src.models import fit_rf, predict_rf, fit_mlp, predict_mlp, save_rf, save_mlp


def main():
    parser = argparse.ArgumentParser(description="Train RF/MLP on 2023-2024 and validate 2025 / test 2026")
    parser.add_argument("--phase", choices=["validation", "test"], required=True,
                        help="Use validation for model design; test only for frozen final comparisons")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cfg = load_config(root / args.config)
    path = root / cfg["data"]["prepared_path"]
    if not path.exists():
        parser.error("Prepared dataset missing; add all CSV files and run python prepare_data.py")
    parts = split_by_year(load_hourly(path), cfg)
    target_name = "validation" if args.phase == "validation" else "test"
    comparison = parts[target_name]
    X_target = build_features(comparison)
    X_val = build_features(parts["validation"])
    y_val = parts["validation"].demand.to_numpy()
    seed = int(cfg["experiments"]["seed"])
    out = root / "outputs" / args.phase
    out.mkdir(parents=True, exist_ok=True)
    rows = []

    for frac in cfg["experiments"]["training_fractions"]:
        selected = subset_training_days(parts["train"], frac, seed)
        X_train = build_features(selected)
        y_train = selected.demand.to_numpy()
        fraction_label = f"{int(round(frac * 100))}pct"
        print(f"\nTraining subset: {fraction_label} ({len(selected)} hourly examples)")
        for model_type in ["RandomForest", "MLP"]:
            start = time.perf_counter()
            if model_type == "RandomForest":
                model = fit_rf(X_train, y_train, cfg["experiments"]["random_forest"], seed)
                predictions = predict_rf(model, X_target)
                best_epoch = None
                if frac == 1.0:
                    save_rf(model, out / "random_forest.joblib")
            else:
                artifact = fit_mlp(X_train, y_train, X_val, y_val,
                                   cfg["experiments"]["mlp"], seed)
                predictions = predict_mlp(artifact, X_target)
                best_epoch = artifact["best_epoch"]
                if frac == 1.0:
                    save_mlp(artifact, out / "mlp_checkpoint.pt")
                    pd.DataFrame(artifact["history"]).to_csv(out / "mlp_learning_curve.csv", index=False)
                    draw_learning_curve(artifact["history"], out / "mlp_learning_curve.png")
            duration = time.perf_counter() - start
            row = {"phase": args.phase, "model": model_type, "training_fraction": frac,
                   "n_train_hours": len(selected), "best_epoch": best_epoch,
                   "training_seconds": round(duration, 3), **metrics(comparison.demand, predictions)}
            rows.append(row)
            print(f"{model_type}: MAE {row['mae']:.2f}, RMSE {row['rmse']:.2f}, R2 {row['r2']:.3f}")
            # For all fractions, preserve raw predictions for error analysis/reproduction.
            save_predictions(comparison, predictions,
                             out / f"predictions_{model_type.lower()}_{fraction_label}.csv")
            if frac == 1.0:
                draw_example(comparison, predictions, out / f"plot_{model_type.lower()}.png")

    pd.DataFrame(rows).to_csv(out / "metrics.csv", index=False)
    metadata = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "phase": args.phase,
        "seed": seed, "config": cfg,
        "features": FEATURE_NAMES,
        "python": platform.python_version(),
        "pandas": pd.__version__, "sklearn": sklearn.__version__,
        "torch": torch.__version__, "numpy": np.__version__,
        "data_file": str(path.relative_to(root)),
        "train_hours": len(parts["train"]), "validation_hours": len(parts["validation"]),
        "test_hours": len(parts["test"])
    }
    with (out / "run_metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved measurements, figures, models and run metadata to: {out}")
    if args.phase == "validation":
        print("IMPORTANT: choose/freeze all settings before running --phase test.")
    else:
        print("TEST COMPLETED. Do not tune parameters based on these test scores.")


if __name__ == "__main__":
    main()
