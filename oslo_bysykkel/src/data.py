"""Oslo City Bike trip files -> hourly city-wide demand.

We read only 'started_at' to avoid bringing columns with post-trip information
(e.g. end station/duration) into a forecasting problem.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_config(path: str | Path = "config.json") -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_sources(config: dict, root: Path) -> list[tuple[int, int, Path]]:
    data_cfg = config["data"]
    base = root / data_cfg["raw_dir"]
    expected = []
    missing = []
    for year in data_cfg["years"]:
        for month in data_cfg["months"]:
            p = base / str(year) / f"{month:02d}.csv"
            if not p.is_file():
                missing.append(p.relative_to(root).as_posix())
            else:
                expected.append((year, month, p))
    if missing:
        raise FileNotFoundError(
            "Missing required monthly CSV files:\n- " + "\n- ".join(missing)
            + "\nAdd them under data/raw/YYYY/MM.csv or use import_csv.py. "
            + "Preparation will not silently fill absent months with zero demand."
        )
    return expected


def parse_trip_start(series: pd.Series, timezone: str) -> pd.Series:
    # New Oslo trip data uses timestamp strings with +00:00 offsets (UTC).
    # If a file has naive local timestamps, treating them as UTC would be unsafe.
    sample = series.dropna().astype(str)
    if len(sample):
        strings_with_tz = sample.str.contains(r"(?:Z|[+-]\d\d:\d\d)$", regex=True)
        if not bool(strings_with_tz.all()):
            raise ValueError(
                "Timestamp without explicit UTC offset found. Confirm source timezone "
                "and standardise to ISO 8601 offset-aware timestamps before importing."
            )
    try:
        stamp = pd.to_datetime(series, utc=True, errors="coerce", format="mixed")
    except TypeError:  # older Pandas fallback
        stamp = pd.to_datetime(series, utc=True, errors="coerce")
    return stamp.dt.tz_convert(timezone)


def read_month(path: Path, timezone: str, chunksize: int = 150_000) -> tuple[pd.Series, int, int]:
    """Return counts by UTC hour; also raw and invalid-row counts."""
    hourly_counts: dict[pd.Timestamp, int] = {}
    n_rows = 0
    n_invalid = 0
    try:
        iterator = pd.read_csv(path, usecols=["started_at"], chunksize=chunksize)
        for frame in iterator:
            n_rows += len(frame)
            stamps = parse_trip_start(frame["started_at"], timezone)
            n_invalid += int(stamps.isna().sum())
            # Floor *in UTC* to avoid ambiguous fall-back DST hours in October.
            utc_hours = stamps.dt.tz_convert("UTC").dt.floor("h")
            counts = utc_hours.dropna().value_counts()
            for timestamp, n in counts.items():
                hourly_counts[timestamp] = hourly_counts.get(timestamp, 0) + int(n)
    except ValueError as exc:
        raise ValueError(f"Problem reading {path}: {exc}") from exc
    if not n_rows:
        raise ValueError(f"CSV file is empty: {path}")
    if n_invalid:
        raise ValueError(f"{path}: {n_invalid} invalid started_at values; fix input first")
    return pd.Series(hourly_counts, dtype="int64"), n_rows, n_invalid


def build_hourly(config: dict, root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sources = check_sources(config, root)
    timezone = config["data"]["timezone"]
    all_counts: dict[pd.Timestamp, int] = {}
    manifest = []
    for year, month, path in sources:
        counts, n, bad = read_month(path, timezone)
        for utc_ts, count in counts.items():
            all_counts[utc_ts] = all_counts.get(utc_ts, 0) + int(count)
        manifest.append({"year": year, "month": month, "file": path.relative_to(root).as_posix(),
                         "sha256": file_sha256(path), "file_bytes": path.stat().st_size,
                         "rows": n, "invalid_started_at": bad})
        print(f"Loaded {year}-{month:02d}: {n:,} trips")

    # Build hours only for the intended calendar months; no zeros across missing seasons.
    # Source files are partitioned around UTC midnight; the first 1-2 Oslo-local
    # hours of April may be in March.csv, so drop April 1 by default.
    frames = []
    selected_months = sorted(config["data"]["months"])
    if selected_months != list(range(selected_months[0], selected_months[-1] + 1)):
        raise ValueError("Selected months must be consecutive (avoids accidental gaps).")
    for year in config["data"]["years"]:
        first_month = selected_months[0]
        final_month = selected_months[-1]
        start = pd.Timestamp(year=year, month=first_month, day=1, tz=timezone)
        if final_month == 12:
            end = pd.Timestamp(year=year + 1, month=1, day=1, tz=timezone)
        else:
            end = pd.Timestamp(year=year, month=final_month + 1, day=1, tz=timezone)
        if config["data"].get("drop_first_day_of_season", True):
            start += pd.DateOffset(days=1)
        local_hours = pd.date_range(start, end, freq="h", inclusive="left")
        utc_hours = local_hours.tz_convert("UTC")
        counts = [all_counts.get(ts, 0) for ts in utc_hours]
        frames.append(pd.DataFrame({"timestamp_utc": utc_hours, "timestamp_oslo": local_hours,
                                    "demand": np.array(counts, dtype=np.int64)}))
    output = pd.concat(frames, ignore_index=True)
    output["year"] = output["timestamp_oslo"].dt.year
    if output.duplicated("timestamp_utc").any():
        raise ValueError("Repeated hourly timestamps detected")
    return output, pd.DataFrame(manifest)


def load_hourly(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if not {"timestamp_utc", "demand"}.issubset(frame.columns):
        raise ValueError("Prepared data missing timestamp_utc or demand")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["timestamp_oslo"] = frame["timestamp_utc"].dt.tz_convert("Europe/Oslo")
    frame["year"] = frame["timestamp_oslo"].dt.year
    frame["demand"] = pd.to_numeric(frame["demand"], errors="raise").astype(int)
    if frame["timestamp_utc"].duplicated().any() or frame["demand"].lt(0).any():
        raise ValueError("Duplicate timestamps or negative demand found")
    return frame.sort_values("timestamp_utc").reset_index(drop=True)


def split_by_year(df: pd.DataFrame, config: dict) -> dict[str, pd.DataFrame]:
    years = config["split"]
    result = {
        "train": df.loc[df.year == years["train_year"]].copy(),
        "validation": df.loc[df.year == years["validation_year"]].copy(),
        "test": df.loc[df.year == years["test_year"]].copy(),
    }
    if any(part.empty for part in result.values()):
        raise ValueError("Training, validation, and test years must all have data")
    if not (result["train"].timestamp_utc.max() < result["validation"].timestamp_utc.min()
            < result["test"].timestamp_utc.min()):
        raise ValueError("Invalid chronology; future data may leak into training")
    return result


def subset_training_days(df: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    """Nested, seeded complete-day samples, stratified by month.

    Because all sampled days belong to the training year, temporal train/val/test
    separation is maintained. Equal monthly representation reduces seasonal bias.
    """
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    if fraction == 1:
        return df.copy()
    tmp = df.copy()
    tmp["local_date"] = tmp["timestamp_oslo"].dt.date
    tmp["local_month"] = tmp["timestamp_oslo"].dt.month
    rng = np.random.default_rng(seed)
    chosen = []
    for _, block in tmp.groupby("local_month", sort=True):
        days = np.array(sorted(block.local_date.unique()), dtype=object)
        rng.shuffle(days)
        keep = max(1, int(np.ceil(len(days) * fraction)))
        chosen.extend(days[:keep].tolist())
    result = tmp[tmp.local_date.isin(chosen)].drop(columns=["local_date", "local_month"])
    return result.sort_values("timestamp_utc")
