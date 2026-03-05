#!/usr/bin/env python3
"""
scripts/test_finbert_sample.py

Test FinBERT sentiment analysis on a sample of articles before processing the full dataset.

Usage:
    python scripts/test_finbert_sample.py --sample-size 1000
"""

import argparse
import sys
import pandas as pd
from pathlib import Path

from msa.utils.paths import get_project_root, get_processed_data_path

# Add project root to path
PROJECT_ROOT = get_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the FinBERT scorer from the main script
try:
    from add_sentiment_finbert import add_finbert_sentiment
except ImportError:
    print("Error: Could not import add_finbert_sentiment")
    print("Make sure transformers and torch are installed")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Test FinBERT on a sample of articles"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Number of articles to test (default: 1000)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to use (default: auto)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for processing (default: 32)"
    )
    
    args = parser.parse_args()
    
    # Load data
    input_path = get_processed_data_path() / "gdelt_articles_accumulated.csv"
    print(f"Loading articles from: {input_path}")
    df = pd.read_csv(input_path)
    print(f"Total articles available: {len(df):,}\n")
    
    # Take random sample
    print(f"Selecting random sample of {args.sample_size:,} articles...")
    df_sample = df.sample(n=min(args.sample_size, len(df)), random_state=42)
    print(f"Sample size: {len(df_sample):,} articles\n")
    
    # Run FinBERT on sample
    print("="*70)
    print(f"Running FinBERT on {len(df_sample):,} articles (this is a test)")
    print("="*70)
    
    df_sample = add_finbert_sentiment(
        df_sample,
        text_col="title",
        batch_size=args.batch_size,
        device=args.device
    )
    
    # Save sample results
    output_path = get_processed_data_path() / "finbert_sample_test.csv"
    print(f"\nSaving sample results to: {output_path}")
    df_sample.to_csv(output_path, index=False)
    
    # Show comparison with dictionary method
    print("\n" + "="*70)
    print("COMPARISON WITH DICTIONARY METHOD")
    print("="*70)
    
    # Load original sentiment if it exists
    original_path = get_processed_data_path() / "gdelt_articles_with_sentiment.csv"
    if original_path.exists():
        df_orig = pd.read_csv(original_path)
        # Get same articles
        sample_urls = set(df_sample['url'].tolist())
        df_orig_sample = df_orig[df_orig['url'].isin(sample_urls)]
        
        if len(df_orig_sample) > 0:
            print(f"\nDictionary Method (on same {len(df_orig_sample)} articles):")
            print(f"  Sentiment detected: {df_orig_sample['sentiment_present'].sum():,} "
                  f"({100*df_orig_sample['sentiment_present'].mean():.1f}%)")
            
            print(f"\nFinBERT Method:")
            print(f"  Sentiment detected: {df_sample['sentiment_present'].sum():,} "
                  f"({100*df_sample['sentiment_present'].mean():.1f}%)")
            
            improvement = (df_sample['sentiment_present'].mean() - 
                          df_orig_sample['sentiment_present'].mean()) * 100
            print(f"\n  Improvement: +{improvement:.1f} percentage points")
    
    # Show some example comparisons
    print("\n" + "="*70)
    print("EXAMPLE ARTICLES")
    print("="*70)
    
    # Show a few examples
    examples = df_sample.head(5)
    for idx, row in examples.iterrows():
        print(f"\nTitle: {row['title'][:80]}...")
        print(f"  FinBERT Score: {row['sentiment_score']:.3f}")
        print(f"  FinBERT Label: {row['sentiment_label']}")
        print(f"  Confidence: {row['sentiment_confidence']:.3f}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print(f"\nReview the results in: {output_path}")
    print("\nIf satisfied with the quality, run the full processing:")
    print("  python scripts/add_sentiment_finbert.py")
    print("="*70)

if __name__ == "__main__":
    main()
