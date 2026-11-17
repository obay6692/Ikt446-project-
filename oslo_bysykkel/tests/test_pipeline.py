"""Lightweight reproducibility checks. These are NOT empirical results."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.data import build_hourly, parse_trip_start, split_by_year, subset_training_days
from src.evaluate import metrics
from src.features import build_features, FEATURE_NAMES
from src.models import fit_rf, fit_mlp, predict_rf, predict_mlp


class TestOsloData(unittest.TestCase):
    def test_utc_to_oslo_hour(self):
        strings = pd.Series(["2026-09-30 22:00:11.663000+00:00",
                             "2026-09-30 23:00:02+00:00"])
        local = parse_trip_start(strings, "Europe/Oslo")
        self.assertEqual(local.dt.day.tolist(), [1, 1])
        self.assertEqual(local.dt.hour.tolist(), [0, 1])
        self.assertEqual(local.dt.month.tolist(), [10, 10])

    def test_offset_required(self):
        with self.assertRaises(ValueError):
            parse_trip_start(pd.Series(["2026-10-01 08:00:00"]), "Europe/Oslo")

    def test_hourly_aggregation_and_zero_filling(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base = root / "data/raw/2024"
            base.mkdir(parents=True)
            for month in [4, 5]:
                pd.DataFrame({"started_at": [
                    f"2024-{month:02d}-02T06:15:00+00:00",
                    f"2024-{month:02d}-02T06:45:00+00:00"]}).to_csv(base / f"{month:02d}.csv", index=False)
            cfg = {"data": {"raw_dir": "data/raw", "years": [2024], "months": [4, 5],
                            "timezone": "Europe/Oslo", "drop_first_day_of_season": True}}
            hourly, manifest = build_hourly(cfg, root)
            sel = hourly[hourly.timestamp_oslo.dt.strftime("%Y-%m-%d %H") == "2024-04-02 08"]
            self.assertEqual(sel.demand.iloc[0], 2)
            self.assertTrue((hourly.demand == 0).any())
            self.assertEqual(len(manifest), 2)

    def test_features_and_models_on_small_fake_data(self):
        # Illustrative synthetic hourly observations, used ONLY for testing software.
        index = pd.date_range("2024-04-02", periods=24 * 8, freq="h", tz="Europe/Oslo")
        df = pd.DataFrame({"timestamp_oslo": index, "demand": (index.hour * 2 + 5).astype(int)})
        X = build_features(df)
        self.assertEqual(X.columns.tolist(), FEATURE_NAMES)
        n = 24 * 6
        y = df.demand.to_numpy()
        rf = fit_rf(X.iloc[:n], y[:n], {"n_estimators": 10, "min_samples_leaf": 2}, 42)
        self.assertTrue(np.isfinite(predict_rf(rf, X.iloc[n:])).all())
        art = fit_mlp(X.iloc[:n], y[:n], X.iloc[n:], y[n:],
                      {"hidden_sizes": [8], "learning_rate": 0.01,
                       "batch_size": 32, "max_epochs": 4, "patience": 2,
                       "weight_decay": 0.0}, 42)
        self.assertTrue(np.isfinite(predict_mlp(art, X.iloc[n:])).all())
        self.assertGreaterEqual(metrics(y[n:], predict_rf(rf, X.iloc[n:]))["rmse"], 0)

    def test_nested_day_selection(self):
        idx = pd.date_range("2024-04-02", periods=24 * 20, freq="h", tz="Europe/Oslo")
        df = pd.DataFrame({"timestamp_oslo": idx, "timestamp_utc": idx.tz_convert("UTC")})
        small = subset_training_days(df, 0.25, 42)
        large = subset_training_days(df, 0.5, 42)
        self.assertTrue(set(small.timestamp_utc).issubset(set(large.timestamp_utc)))


if __name__ == "__main__":
    unittest.main()
