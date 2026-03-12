#!/usr/bin/env python3
"""Export key processed datasets to Parquet for team sharing.

Converts:
  - gdelt_articles_with_sentiment.csv
  - prices_daily_accumulated.csv
  - gdelt_ohlcv_join.csv

Writes Parquet versions to data/processed/. Use for shared storage or version control.
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT_ROOT / "data" / "processed"

SHARED_DATASETS = [
    "gdelt_articles_with_sentiment.csv",
    "prices_daily_accumulated.csv",
    "gdelt_ohlcv_join.csv",
]

DATE_COLS = {
    "gdelt_articles_with_sentiment.csv": ["seendate", "date"],
    "prices_daily_accumulated.csv": ["date"],
    "gdelt_ohlcv_join.csv": ["seendate", "date", "article_date", "price_date"],
}


def main() -> None:
    print("Exporting shared datasets to Parquet...")
    for name in SHARED_DATASETS:
        csv_path = PROCESSED / name
        parquet_path = csv_path.with_suffix(".parquet")
        if not csv_path.exists():
            print(f"  SKIP {name} (not found)")
            continue
        df = pd.read_csv(csv_path)
        date_cols = DATE_COLS.get(name, [])
        existing = [c for c in date_cols if c in df.columns]
        if existing:
            df[existing] = df[existing].apply(pd.to_datetime, errors="coerce")
        df.to_parquet(parquet_path, index=False)
        size_csv = csv_path.stat().st_size / 1024
        size_pq = parquet_path.stat().st_size / 1024
        print(f"  {name} -> {parquet_path.name} ({size_csv:.0f}KB -> {size_pq:.0f}KB)")
    print("Done.")


if __name__ == "__main__":
    main()
