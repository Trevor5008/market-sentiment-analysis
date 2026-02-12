"""
scripts/ohlcv_cleaning.py

Cleaning pipeline for OHLCV price data.

Philosophy:
- Raw data (data/raw/) is IMMUTABLE - never modified
- Cleaned data (data/processed/) is DERIVED - regenerated from raw

Cleaning Steps (OHLCV):
1. Normalize types (dates and numeric columns)
2. Handle Market Calendar (reindex to NYSE to find missing days)
3. Fix Logical Errors (High must be max, Low must be min)
4. Interpolate missing prices (Linear for prices, 0 for volume)
5. Sort and Save
"""

from __future__ import annotations
import argparse
import os
import pandas as pd
import numpy as np
from pathlib import Path
import pandas_market_calendars as mcal


# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ============================================================
# CONFIG
# ============================================================
REQUIRED_COLS = ["date", "open", "high", "low", "close", "adj_close", "volume", "ticker"]
NUMERIC_COLS = ["open", "high", "low", "close", "adj_close", "volume"]

# ============================================================
# CLEANING FUNCTIONS
# ============================================================

def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def apply_market_calendar(df: pd.DataFrame, exchange: str = "NYSE") -> pd.DataFrame:
    """Ensures every valid trading day is represented in the dataset."""
    df = df.copy()
    tickers = df["ticker"].unique()
    start_date = df["date"].min()
    end_date = df["date"].max()
    
    # Fetch valid trading days
    cal = mcal.get_calendar(exchange)
    schedule = cal.schedule(start_date=start_date, end_date=end_date)
    expected_dates = pd.DatetimeIndex(schedule.index).tz_localize(None)
    
    cleaned_frames = []
    for ticker in tickers:
        tdf = df[df["ticker"] == ticker].set_index("date")
        # Reindexing inserts NaNs for missing market days
        tdf = tdf.reindex(expected_dates)
        tdf["ticker"] = ticker
        cleaned_frames.append(tdf)
    
    return pd.concat(cleaned_frames).reset_index().rename(columns={"index": "date"})

def fix_logical_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Enforces High >= all and Low <= all."""
    df = df.copy()
    # High must be the maximum of the candle components
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    # Low must be the minimum of the candle components
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Interpolates prices and zero-fills volume."""
    df = df.copy()
    price_cols = ["open", "high", "low", "close", "adj_close"]
    
    # Linear interpolation for price gaps
    df[price_cols] = df.groupby("ticker")[price_cols].transform(
        lambda x: x.interpolate(method="linear")
    )
    
    # Volume is 0 if no data existed for that trading day
    df["volume"] = df["volume"].fillna(0)
    return df

def clean_pipeline(df: pd.DataFrame, exchange: str) -> pd.DataFrame:
    print(f"\n{'='*50}")
    print("OHLCV CLEANING PIPELINE")
    print(f"{'='*50}")
    print(f"Input: {len(df):,} rows")

    print(f"\n[1/4] Normalizing data types...")
    df = normalize_types(df)

    print(f"\n[2/4] Aligning with {exchange} calendar...")
    df = apply_market_calendar(df, exchange)

    print("\n[3/4] Enforcing logical price constraints...")
    df = fix_logical_prices(df)

    print("\n[4/4] Interpolating missing values...")
    df = handle_missing_values(df)

    print(f"\n{'='*50}")
    print(f"Output: {len(df):,} rows")
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean OHLCV price data")
    parser.add_argument("--input", 
        default=str(RAW_DIR / "prices_daily.csv"),
        help="Path to raw OHLCV CSV"
    )
    parser.add_argument("--output", 
        default=str(PROCESSED_DIR / "prices_daily_clean.csv"),
        help="Path to save cleaned CSV"
    )
    parser.add_argument("--exchange", default="NYSE", help="Market calendar to use")
    
    args = parser.parse_args()
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    if not Path(args.input).exists():
        print(f"Error: Could not find {args.input}")
        return

    print(f"Loading: {args.input}") 
    df = pd.read_csv(args.input)
    
    df_clean = clean_pipeline(df, args.exchange)
    
    df_clean.to_csv(args.output, index=False)
    print(f"\nSaved: {args.output}")

if __name__ == "__main__":
    main()