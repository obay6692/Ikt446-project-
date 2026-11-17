"""Metrics and figures for hourly demand regression."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def metrics(y_true, y_pred) -> dict:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "r2": float(r2_score(y, p)),
        "n_samples": len(y),
    }


def save_predictions(df: pd.DataFrame, prediction: np.ndarray, path: Path) -> None:
    result = df[["timestamp_utc", "timestamp_oslo", "demand"]].copy()
    result["predicted"] = np.asarray(prediction)
    result["absolute_error"] = abs(result.demand - result.predicted)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(path, index=False)


def draw_example(df: pd.DataFrame, prediction: np.ndarray, out: Path) -> None:
    """Plot the first 7 days from the test year, no manual cherry-picking."""
    sample = min(7 * 24, len(df))
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(df.timestamp_oslo.iloc[:sample], df.demand.iloc[:sample], label="Actual", linewidth=1.7)
    ax.plot(df.timestamp_oslo.iloc[:sample], np.asarray(prediction)[:sample],
            label="Predicted", linewidth=1.3)
    ax.set(xlabel="Local Oslo time", ylabel="Trips started per hour",
           title="First seven days of held-out period")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)


def draw_learning_curve(history: list[dict], out: Path) -> None:
    if not history:
        return
    frame = pd.DataFrame(history)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(frame.epoch, frame.train_loss, label="Training MSE (scaled target)")
    ax.plot(frame.epoch, frame.val_loss, label="Validation MSE (scaled target)")
    ax.set(xlabel="Epoch", ylabel="Loss", title="MLP training")
    ax.legend()
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
