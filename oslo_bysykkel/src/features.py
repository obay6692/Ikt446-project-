"""Calendar-only predictors known before the forecast hour.

No demand lags, weather observations, trip duration or station arrival details:
those may be unavailable at inference time and could create leakage.
"""
import numpy as np
import pandas as pd

FEATURE_NAMES = [
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
    "month_sin", "month_cos", "dayofyear_sin", "dayofyear_cos",
    "is_weekend", "rush_hour", "is_summer"
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    local = df["timestamp_oslo"]
    hour = local.dt.hour
    weekday = local.dt.dayofweek
    month = local.dt.month
    dayofyear = local.dt.dayofyear
    is_weekend = weekday >= 5
    columns = {
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "weekday_sin": np.sin(2 * np.pi * weekday / 7),
        "weekday_cos": np.cos(2 * np.pi * weekday / 7),
        "month_sin": np.sin(2 * np.pi * (month - 1) / 12),
        "month_cos": np.cos(2 * np.pi * (month - 1) / 12),
        "dayofyear_sin": np.sin(2 * np.pi * (dayofyear - 1) / 366),
        "dayofyear_cos": np.cos(2 * np.pi * (dayofyear - 1) / 366),
        "is_weekend": is_weekend.astype(int),
        "rush_hour": ((~is_weekend) & (hour.isin([7, 8, 9, 15, 16, 17]))).astype(int),
        "is_summer": month.isin([6, 7, 8]).astype(int),
    }
    return pd.DataFrame(columns, index=df.index)[FEATURE_NAMES].astype("float32")
