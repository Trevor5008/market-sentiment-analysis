#!/usr/bin/env python3
"""
scripts/dedupe_and_sentiment.py

Deduplicate accumulated GDELT articles and regenerate sentiment scores.

Applies the same deduplication logic as cleaning_gdelt.py:
1. Deduplicate by URL (keep latest by seendate)
2. Deduplicate by normalized headline per ticker (keep latest by seendate)

Then regenerates sentiment scores using add_sentiment.py logic.
"""

import pandas as pd
from pathlib import Path
import sys

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cleaning_gdelt import deduplicate, deduplicate_by_headline
from add_sentiment import add_sentiment_scores

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def main():
    input_file = PROCESSED_DIR / "gdelt_articles_accumulated.csv"
    output_file = PROCESSED_DIR / "gdelt_articles_with_sentiment.csv"
    
    print(f"Loading: {input_file}")
    df = pd.read_csv(input_file, parse_dates=["seendate"])
    print(f"Loaded {len(df):,} rows")
    
    # Deduplicate
    print("\n" + "="*50)
    print("DEDUPLICATION")
    print("="*50)
    
    print("\n[1/2] Removing duplicates by URL...")
    df = deduplicate(df, subset=["url"])
    
    print("\n[2/2] Removing duplicate headlines (same story, different outlets)...")
    df = deduplicate_by_headline(df, title_col="title", date_col="seendate", key_col="ticker")
    
    print(f"\nAfter deduplication: {len(df):,} rows")
    
    # Regenerate sentiment scores
    print("\n" + "="*50)
    print("SENTIMENT SCORING")
    print("="*50)
    df = add_sentiment_scores(df, text_col="title")
    
    # Save
    print(f"\nSaving: {output_file}")
    df.to_csv(output_file, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
