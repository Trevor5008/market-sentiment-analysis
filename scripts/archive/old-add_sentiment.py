#!/usr/bin/env python3
"""
scripts/add_sentiment.py

Add sentiment scores to GDELT articles using a domain-specific word bank approach.

Philosophy:
- Avoid ML/NLP dependencies where possible
- Use financial domain-specific lexicon
- Handle negation and intensity modifiers
- Transparent, tunable scoring

Scoring approach:
- Positive words contribute +1, negative words contribute -1
- Intensity modifiers amplify scores (e.g., "very bullish" = +2, "slightly bearish" = -0.5)
- Negation flips polarity (e.g., "not bullish" = -1)
- Final score normalized to [-1, +1] range based on word count
- Neutral articles (no sentiment words) get score 0

Usage:
    python scripts/add_sentiment.py
    python scripts/add_sentiment.py --input data/processed/gdelt_articles_accumulated.csv --output data/processed/gdelt_articles_with_sentiment.csv
"""

import argparse
import re
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add scripts directory to path so we can import sentiment_lexicon
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from sentiment_lexicon import (
    STRONG_POSITIVE,
    MODERATE_POSITIVE,
    WEAK_POSITIVE,
    WEAK_NEGATIVE,
    MODERATE_NEGATIVE,
    STRONG_NEGATIVE,
    INTENSITY_MODIFIERS,
    NEGATION_WORDS,
)

# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ============================================================
# SENTIMENT SCORING FUNCTIONS
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize text for sentiment analysis."""
    if pd.isna(text):
        return ""
    # Convert to lowercase, preserve word boundaries
    text = str(text).lower()
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def calculate_sentiment_score(text: str) -> tuple[float, int]:
    """
    Calculate sentiment score for a text.

    Returns:
        Tuple of (score, hits) where:
        - score: float in range [-1, +1] (+1 = very positive, 0 = neutral, -1 = very negative)
        - hits: int count of sentiment words found
    """
    if pd.isna(text) or not str(text).strip():
        return 0.0, 0

    normalized = normalize_text(text)

    # Find all sentiment words with their positions
    sentiment_categories = [
        (STRONG_POSITIVE, 2.0),
        (MODERATE_POSITIVE, 1.0),
        (WEAK_POSITIVE, 0.5),
        (WEAK_NEGATIVE, -0.5),
        (MODERATE_NEGATIVE, -1.0),
        (STRONG_NEGATIVE, -2.0),
    ]

    # Collect all sentiment word occurrences with positions
    word_occurrences = []
    for word_list, base_score in sentiment_categories:
        for word in word_list:
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, normalized):
                word_occurrences.append((word, base_score, match.start()))

    if not word_occurrences:
        return 0.0, 0 # score, matches

    # Sort by position (left to right)
    word_occurrences.sort(key=lambda x: x[2])

    total_score = 0.0

    # Process each occurrence with its local context
    for word, base_score, word_pos in word_occurrences:
        score = base_score

        # Extract context: up to 4 words before this word
        text_before = normalized[:word_pos]
        words_before = text_before.split()[-4:]
        context_text = " ".join(words_before).lower()

        # Check for intensity modifier
        intensity_mult = 1.0
        for modifier, multiplier in INTENSITY_MODIFIERS.items():
            if modifier in context_text:
                intensity_mult = multiplier
                break

        # Check for negation (flip polarity)
        is_negated = any(neg_word in context_text for neg_word in NEGATION_WORDS)

        # Apply modifiers
        if is_negated:
            score = -score
        score *= intensity_mult

        total_score += score

    # Normalize to [-1, +1] range
    # Use tanh to smoothly normalize while preserving relative magnitudes
    # Divide by number of occurrences to get average, then apply tanh
    avg_score = total_score / len(word_occurrences)
    normalized_score = np.tanh(avg_score)

    return round(float(normalized_score), 2), int(len(word_occurrences))


def add_sentiment_scores(df: pd.DataFrame, text_col: str = "title") -> pd.DataFrame:
    """
    Add sentiment scores to DataFrame.

    Args:
        df: DataFrame with article data
        text_col: Column name containing text to analyze (default: "title")

    Returns:
        DataFrame with added 'sentiment_score' column
    """
    df = df.copy()

    print(f"\nCalculating sentiment scores from '{text_col}' column...")
    df[['sentiment_score', 'sentiment_hits']] = (df[text_col].apply(lambda x: calculate_sentiment_score(x)).tolist())
    df["sentiment_present"] = df["sentiment_hits"] > 0

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add sentiment scores to GDELT articles using word bank approach"
    )
    parser.add_argument(
        "--input",
        default=str(PROCESSED_DIR / "gdelt_articles_accumulated.csv"),
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        default=str(PROCESSED_DIR / "gdelt_articles_with_sentiment.csv"),
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--text-col",
        default="title",
        help="Column name containing text to analyze (default: 'title')"
    )
    args = parser.parse_args()

    print(f"Loading: {args.input}")
    df = pd.read_csv(args.input, parse_dates=["seendate"])
    print(f"Loaded {len(df):,} rows")

    df_with_sentiment = add_sentiment_scores(df, text_col=args.text_col)

    print(f"\nSaving: {args.output}")
    df_with_sentiment.to_csv(args.output, index=False)
    print("Done!")


if __name__ == "__main__":
    main()
