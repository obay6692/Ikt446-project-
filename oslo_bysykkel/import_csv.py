"""Import one downloaded official Oslo Bysykkel monthly CSV into canonical layout."""
import argparse
from pathlib import Path
import shutil
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Copy a monthly Oslo trip CSV into data/raw/YYYY/MM.csv")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.month <= 12:
        parser.error("month must be between 1 and 12")
    if not args.file.exists():
        parser.error(f"file not found: {args.file}")
    columns = pd.read_csv(args.file, nrows=1).columns
    if "started_at" not in columns:
        parser.error(f"Missing started_at column; got {columns.tolist()}")
    target = Path("data/raw") / str(args.year) / f"{args.month:02d}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        parser.error(f"Refusing to overwrite existing {target}; remove it first if intended")
    shutil.copy2(args.file, target)
    print(f"Copied: {args.file} -> {target}")


if __name__ == "__main__":
    main()
