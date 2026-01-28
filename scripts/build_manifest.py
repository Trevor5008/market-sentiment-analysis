from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd


# -- Config --
SNAPSHOT_DIR = "data/raw/snapshots"
SCRIPT_VERSION = "1.0.0"

RAW_FILES = {
    "gdelt_articles": "data/raw/gdelt_articles.csv",
    "prices_daily": "data/raw/prices_daily.csv",
}

# -- Helpers --
def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_timestamp() -> str:
    # Used for timestamp field in manifest
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_date_yyyy_mm_dd() -> str:
    # Used for run_manifest_YYYY-MM-DD.json
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_git_commit_short(root: Path) -> str:
    # Gets git commit hash for the current HEAD
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def load_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    return pd.read_csv(path)


def safe_row_count(df: Optional[pd.DataFrame]) -> int:
    # Return number of rows in df, or 0 if df is None
    if df is None:
        return 0
    return int(len(df))


def get_unique_tickers_from_df(df: Optional[pd.DataFrame]) -> list[str]:
    # Extract tickers from a dataframe if it has a 'ticker' column.
    # Returns an empty list if df is missing or ticker column doesn't exist.

    if df is None or df.empty:
        return []
    if "ticker" not in df.columns:
        return []

    values = df["ticker"].dropna().astype(str).str.strip().unique().tolist()
    # remove empty strings if any
    return [v for v in values if v != ""]


def build_manifest(notes: str = "") -> dict:
    root = get_repo_root()

    # Load raw datasets
    loaded = {}
    for dataset_name, rel_path in RAW_FILES.items():
        abs_path = root / rel_path
        loaded[dataset_name] = load_csv_if_exists(abs_path)

    # Row counts per dataset
    row_counts = {}
    for dataset_name, df in loaded.items():
        row_counts[dataset_name] = safe_row_count(df)

    # Unique tickers across all datasets
    ticker_set = set()
    for df in loaded.values():
        for t in get_unique_tickers_from_df(df):
            ticker_set.add(t)

    tickers_covered = sorted(list(ticker_set))

    # Required metadata
    manifest = {
        "timestamp": utc_timestamp(),
        "tickers_covered": tickers_covered,
        "row_counts": row_counts,
        "script_version": SCRIPT_VERSION,
        "git_commit": get_git_commit_short(root),
        "notes": notes,
    }

    return manifest


def write_manifest_file(manifest: dict) -> Path:
    root = get_repo_root()

    filename = f"run_manifest_{utc_date_yyyy_mm_dd()}.json"

    out_dir = root / SNAPSHOT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / filename
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return out_path


def main() -> None:
    notes = ""

    manifest = build_manifest(notes=notes)
    out_path = write_manifest_file(manifest)

    root = get_repo_root()
    print(f"[OK] Wrote run manifest -> {out_path.relative_to(root)}")


if __name__ == "__main__":
    main()
