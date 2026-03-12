#!/usr/bin/env python3
"""
scripts/add_sentiment_v2.py

Add FinBERT sentiment scores to deduped GDELT articles.
Pipeline step: runs after dedupe, produces gdelt_articles_with_sentiment.csv.
"""
import argparse
import sys
from pathlib import Path
from msa.utils.paths import get_processed_data_path

DEFAULT_INPUT = get_processed_data_path() / "gdelt_articles_deduped.csv"
DEFAULT_OUTPUT = get_processed_data_path() / "gdelt_articles_with_sentiment.csv"


def main():
    parser = argparse.ArgumentParser(
        description="Add FinBERT sentiment scores to GDELT articles"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input CSV (deduped articles, default: {DEFAULT_INPUT.name})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV (default: {DEFAULT_OUTPUT.name})",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device for FinBERT (default: auto)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        print("Run dedupe.py first, or pass --input path/to/deduped.csv")
        sys.exit(1)

    import pandas as pd
    from add_sentiment_finbert import add_finbert_sentiment

    df = pd.read_csv(args.input, parse_dates=["seendate"])
    print(f"Loaded {len(df):,} articles from {args.input.name}")

    df = add_finbert_sentiment(
        df,
        text_col="title",
        batch_size=args.batch_size,
        device=args.device,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()