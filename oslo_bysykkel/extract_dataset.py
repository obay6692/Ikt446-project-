"""Extract the bundled Oslo Bysykkel dataset zip into data/raw/YYYY/MM.csv.

The zip (in the repository root) contains "oslo sykel dataset/YYYY/MM.csv".
The top-level folder is stripped so files land where prepare_data.py expects them.
"""
import argparse
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_ZIP = ROOT.parent / "oslo sykel dataset.zip"
MEMBER = re.compile(r"(?:^|/)(\d{4})/(\d{2})\.csv$")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    p.add_argument("--out", type=Path, default=ROOT / "data" / "raw")
    p.add_argument("--overwrite", action="store_true", help="Replace existing CSVs")
    args = p.parse_args()

    if not args.zip.is_file():
        p.error(f"zip not found: {args.zip} (is Git LFS pulled? run 'git lfs pull')")

    extracted = skipped = 0
    with zipfile.ZipFile(args.zip) as zf:
        for info in zf.infolist():
            m = MEMBER.search(info.filename)
            if info.is_dir() or not m:
                continue
            year, month = m.groups()
            target = args.out / year / f"{month}.csv"
            if target.exists() and not args.overwrite:
                skipped += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            extracted += 1
            print(f"{info.filename} -> {target.relative_to(ROOT).as_posix()}")
    print(f"\nExtracted {extracted} file(s), skipped {skipped} existing (use --overwrite to replace).")


if __name__ == "__main__":
    main()
