#!/usr/bin/env python3
from __future__ import annotations
"""

scripts/cleaning_data.py

Cleaning pipeline for GDELT articles and OHLCV price data.

Philosophy:
- Raw data (data/raw/) is IMMUTABLE - never modified
- Cleaned data (data/processed/) is DERIVED - regenerated from raw

Cleaning Steps (GDELT):
1. Drop columns with 100% missing (description, sourceCountry, query)
2. Deduplicate by URL (keep latest by seendate)
3. Filter to English only
4. Filter to relevant articles (financial keywords)
5. Handle missing values

Usage:
    python scripts/cleaning_data.py
    python scripts/cleaning_data.py --input data/raw/gdelt_articles.csv

"""
import argparse #for command line arguments
import os
import re
import pandas as pd
import numpy as np
from this import d

from pathlib import Path

# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ============================================================
# GDELT CONFIG
# ============================================================

gdelt_drop_cols = ["description", "sourceCountry","query"]
gdelt_dedupe_cols = ["url"]
gdelt_required_cols = ["url", "title", "seendate", "ticker", "company"]

FINANCIAL_KEYWORDS = [
    # Stock & Trading
    'stock', 'share', 'shares', 'trading', 'nasdaq', 'nyse',
    # Financial Metrics
    'earnings', 'revenue', 'profit', 'loss', 'eps', 'guidance',
    # Market Movement
    'rally', 'surge', 'drop', 'crash', 'plunge', 'gain', 'decline',
    # Business
    'ceo', 'dividend', 'acquisition', 'merger', 'ipo',
    # Tech keywords
    'ai', 'artificial intelligence', 'cloud', 'semiconductor', 'chip',
    # MAG7 names (your tickers)
    'apple', 'microsoft', 'google', 'alphabet', 'amazon', 
    'meta', 'tesla', 'nvidia',
]
# ============================================================
# CLEANING FUNCTIONS
# ============================================================
def drop_columns(df:pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    existing = [c for c in cols if c in df.columns]
    if existing:
        df = df.drop(columns=existing)
        print(f" dropped columns: {existing}")
    return df
def duplicate(df: pd.DataFrame, subset: list[str], date_col: str="seendate") -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    df = df.sort_values(date_col)
    df = df.drop_duplicates(subset=subset, keep="last")
    removed = removed = before - len(df)
    print(f"Removed {removed:,} duplicates (by{subset})")

    return df
def filter_lang(df: pd.DataFrame, lang: str = "English") -> pd.DataFrame:
    df = df.copy()
    if "language" not in df.columns:
        print("Warning: cannot find language columns")
        return df
    before = len(df)
    df = df[df["language"] ==  lang]
    removed = before - len(df)

    print(f"  Removed {removed:,} non-{lang} articles")
    return df


def has_financial_keywords(title: str) -> bool:
    if pd.isna(title):
        return False
    
    title_lower = str(title).lower()
    # Check each keyword
    for kw in FINANCIAL_KEYWORDS:
        # \b means "word boundary" - matches whole words only
        # "stock" matches "stock" but not "stockings"
        if re.search(r'\b' + re.escape(kw) +  r'\b', title_lower):
            return True
    return False

def filter_relevance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df["_is_relevant"] = df["title"].apply(has_financial_keywords)
    df = df[df["_is_relevant"] == True]
    df = df.drop(columns=["_is_relevant"])
    removed = before - len(df)
    print(f"  Removed {removed:,} irrelevant articles")
    return df

def drop_missing_required(df: pd.DataFrame, required: list[str]) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.dropna(subset=required)
    
    removed = before - len(df)

    if removed > 0:
        print(f"  Removed {removed:,} rows with missing required values")
    
    return df

def clean_pipline(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n{'='*50}")
    print("GDELT CLEANING PIPELINE")
    print(f"{'='*50}")
    print(f"Input: {len(df):,} rows")

    print("\n[1/5] Dropping unused columns...")
    df = drop_columns(df, gdelt_drop_cols)

    print("\n[2/5] Removing duplicates...")
    df = duplicate(df, subset=gdelt_dedupe_cols)

    print("\n[3/5] Filtering to English...")
    df = filter_lang(df)
    
    # Step 4
    print("\n[4/5] Filtering to relevant articles...")
    df = filter_relevance(df)
    
    # Step 5
    print("\n[5/5] Dropping missing required fields...")
    df = drop_missing_required(df, gdelt_required_cols)
    
    print(f"\n{'='*50}")
    print(f"Output: {len(df):,} rows")
    return df.reset_index(drop=True)

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean GDELT data")
    parser.add_argument("--input", 
    default=str(RAW_DIR/"gdelt_articles.csv"),
    help="Path to raw GDELT csv"\
)
    parser.add_argument("--output", 
    default=str(PROCESSED_DIR/"gdelt_articles_clean.csv"),
    help="Path to save cleaned csv"
)
    args = parser.parse_args()
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    print(f"Loading: {args.input}") 
    df = pd.read_csv(args.input, parse_dates=["seendate"])
    df_clean = clean_pipline(df)
    df_clean.to_csv(args.output, index=False)
    print(f"\nSaved: {args.output}")

if __name__ == "__main__":
    main()