"""Prepare per-hour Oslo bike-trip counts and provenance manifest."""
import argparse
import json
from pathlib import Path
from src.data import build_hourly, load_config


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="config.json")
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    cfg = load_config(root / args.config)
    hourly, manifest = build_hourly(cfg, root)
    target = root / cfg["data"]["prepared_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    hourly.to_csv(target, index=False)
    manifest.to_csv(target.parent / "source_manifest.csv", index=False)
    selection = {"years": cfg["data"]["years"], "months": cfg["data"]["months"],
                 "timezone": cfg["data"]["timezone"], "first_day_excluded": cfg["data"]["drop_first_day_of_season"],
                 "train_year": cfg["split"]["train_year"],
                 "validation_year": cfg["split"]["validation_year"],
                 "test_year": cfg["split"]["test_year"],
                 "hours_per_year": {str(y): int((hourly.year == y).sum()) for y in cfg["data"]["years"]}}
    with (target.parent / "split_definition.json").open("w", encoding="utf-8") as f:
        json.dump(selection, f, ensure_ascii=False, indent=2)
    print(f"\nPrepared {len(hourly):,} hourly rows -> {target}")
    print("Trip totals (selected local hours):", hourly.groupby("year").demand.sum().to_dict())
    print("Source manifest and split definitions saved in data/processed/")


if __name__ == "__main__":
    main()
