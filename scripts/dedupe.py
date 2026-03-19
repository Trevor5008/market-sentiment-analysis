#!/usr/bin/env python3
"""
scripts/dedupe.py

Dedupe GDELT articles by URL and headline.
"""
import pandas as pd
from cleaning_gdelt import deduplicate, deduplicate_by_headline
from msa.utils.paths import get_processed_data_path

DATA_PATH = get_processed_data_path() / "gdelt_articles_accumulated.csv"


def main():
    df = pd.read_csv(DATA_PATH, parse_dates=["seendate"])
    output_file = get_processed_data_path() / "gdelt_articles_deduped.csv"
    df = deduplicate(df, subset=["url"])
    df = deduplicate_by_headline(df, title_col="title", date_col="seendate", key_col="ticker")
    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()