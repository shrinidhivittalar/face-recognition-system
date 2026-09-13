"""Downloads the LFW verification-pairs parquet files used by scripts/run_evaluation.py.

Not committed to the repository (third-party dataset, ~84MB). Run this once
before scripts/run_evaluation.py if data/raw/ is empty.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

FILES = {
    "lfw_pairs_train.parquet": (
        "https://huggingface.co/datasets/logasja/lfw/resolve/"
        "refs%2Fconvert%2Fparquet/pairs/train/0000.parquet"
    ),
    "lfw_pairs_test.parquet": (
        "https://huggingface.co/datasets/logasja/lfw/resolve/"
        "refs%2Fconvert%2Fparquet/pairs/test/0000.parquet"
    ),
}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in FILES.items():
        dest = RAW_DIR / filename
        if dest.exists():
            print(f"skip (already exists): {filename}")
            continue
        print(f"downloading {filename} ...")
        urllib.request.urlretrieve(url, dest)
        print(f"  saved to {dest}")


if __name__ == "__main__":
    main()
