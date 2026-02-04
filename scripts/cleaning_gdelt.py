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
3. Deduplicate by normalized headline per ticker (same story, different outlets → one row; keep latest by seendate)
4. Filter to English only
5. Filter to relevant articles (financial keywords)
6. Handle missing values

Usage:
    python scripts/cleaning_data.py
    python scripts/cleaning_data.py --input data/raw/gdelt_articles.csv

"""
import argparse #for command line arguments
import os
import re
import pandas as pd
import numpy as np
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
    'stock', 'share', 'shares', 'trading', 'trader', 'nasdaq', 'nyse', 
    's&p', 'dow', 'index', 'etf', 'fund', 'hedge',

    # Financial Metrics
    'earnings', 'revenue', 'profit', 'loss', 'margin', 'eps', 
    'guidance', 'forecast', 'outlook', 'quarter', 'quarterly',
    'annual', 'fiscal', 'billion', 'million', 'trillion',

    # Market Movement
    'bull', 'bear', 'rally', 'surge', 'soar', 'jump', 'climb',
    'drop', 'fall', 'crash', 'plunge', 'sink', 'tumble', 'volatile',
    'gain', 'rise', 'decline', 'dip',

    # Valuation
    'valuation', 'market cap', 'price target', 'rating', 'upgrade',
    'downgrade', 'buy', 'sell', 'hold', 'overweight', 'underweight',

    # Business Operations  
    'ceo', 'cfo', 'executive', 'board', 'investor', 'shareholder',
    'dividend', 'buyback', 'acquisition', 'merger', 'deal', 'partnership',
    'investment', 'ipo', 'stake',

    # Supply Chain & Operations
    'supplier', 'supply chain', 'manufacture', 'production', 'factory',
    'chip', 'semiconductor', 'shortage',

    # Tech-Specific
    'ai', 'artificial intelligence', 'cloud', 'software', 'hardware',
    'iphone', 'android', 'windows', 'azure', 'aws', 'gpu', 'data center',

    # MAG7 Company Names
    'apple', 'microsoft', 'google', 'alphabet', 'amazon', 'meta', 
    'facebook', 'tesla', 'nvidia', 'aapl', 'msft', 'googl', 'amzn', 
    'tsla', 'nvda',

    # Competition & Industry
    'competitor', 'rival', 'industry', 'sector', 'antitrust', 'regulation',
    'ces', 'conference', 'keynote', 'announcement', 'launch', 'unveil',
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
def deduplicate(df: pd.DataFrame, subset: list[str], date_col: str = "seendate") -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.sort_values(date_col)
    df = df.drop_duplicates(subset=subset, keep="last")
    removed = before - len(df)
    print(f"  Removed {removed:,} duplicates (by {subset})")
    return df


def normalize_title(title: str) -> str:
    """Lowercase, strip, collapse whitespace for headline dedupe."""
    if pd.isna(title):
        return ""
    return " ".join(str(title).lower().strip().split())


def deduplicate_by_headline(df: pd.DataFrame, title_col: str = "title", date_col: str = "seendate", key_col: str = "ticker") -> pd.DataFrame:
    """Keep one article per distinct (normalized headline, ticker); same story from different outlets → one row (keep latest by seendate)."""
    df = df.copy()
    before = len(df)
    if title_col not in df.columns or key_col not in df.columns:
        return df
    df["_norm_title"] = df[title_col].apply(normalize_title)
    df = df.sort_values(date_col)
    df = df.drop_duplicates(subset=["_norm_title", key_col], keep="last")
    df = df.drop(columns=["_norm_title"])
    removed = before - len(df)
    print(f"  Removed {removed:,} duplicate headlines (same story, different outlets)")
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

def clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n{'='*50}")
    print("GDELT CLEANING PIPELINE")
    print(f"{'='*50}")
    print(f"Input: {len(df):,} rows")

    print("\n[1/6] Dropping unused columns...")
    df = drop_columns(df, gdelt_drop_cols)

    print("\n[2/6] Removing duplicates by URL...")
    df = deduplicate(df, subset=gdelt_dedupe_cols)

    print("\n[3/6] Removing duplicate headlines (same story, different outlets)...")
    df = deduplicate_by_headline(df, title_col="title", date_col="seendate", key_col="ticker")

    print("\n[4/6] Filtering to English...")
    df = filter_lang(df)

    print("\n[5/6] Filtering to relevant articles...")
    df = filter_relevance(df)

    print("\n[6/6] Dropping missing required fields...")
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
    df_clean = clean_pipeline(df)
    df_clean.to_csv(args.output, index=False)
    print(f"\nSaved: {args.output}")

if __name__ == "__main__":
    main()