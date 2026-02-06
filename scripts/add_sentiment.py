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
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ============================================================
# SENTIMENT LEXICON
# ============================================================

# Strong positive sentiment words (score: +2)
STRONG_POSITIVE = [
    'surge', 'soar', 'rally', 'rocket', 'skyrocket', 'explode', 'breakthrough',
    'record high', 'record high', 'all-time high', 'peak', 'milestone',
    'outperform', 'outperforming', 'beat', 'beats', 'beating', 'exceed',
    'upside', 'bullish', 'bull market', 'bull run',
    'momentum', 'strength', 'strong', 'robust', 'solid', 'impressive',
    'upgrade', 'upgraded', 'buy rating', 'strong buy', 'outperform rating',
    'breakout', 'break out', 'gains', 'win', 'wins', 'victory', 'success',
]

# Moderate positive sentiment words (score: +1)
MODERATE_POSITIVE = [
    'rise', 'rises', 'rising', 'gain', 'gains', 'gaining', 'climb', 'climbs',
    'climbing', 'jump', 'jumps', 'jumping', 'increase', 'increases', 'increasing',
    'up', 'upside', 'growth', 'growing', 'expand', 'expands', 'expansion',
    'positive', 'optimistic', 'optimism', 'confidence', 'confident',
    'improve', 'improves', 'improving', 'improvement', 'better', 'best',
    'profit', 'profits', 'profitable', 'profitability', 'earnings beat',
    'revenue growth', 'margin expansion', 'guidance raise', 'guidance raised',
    'momentum', 'trending up', 'uptrend', 'support', 'resistance break',
]

# Weak positive sentiment words (score: +0.5)
WEAK_POSITIVE = [
    'stable', 'stability', 'steady', 'steadily', 'maintain', 'maintains',
    'hold', 'holds', 'holding', 'neutral', 'neutral rating', 'hold rating',
    'modest', 'modestly', 'slight', 'slightly', 'gradual', 'gradually',
]

# Weak negative sentiment words (score: -0.5)
WEAK_NEGATIVE = [
    'concern', 'concerns', 'concerned', 'caution', 'cautious', 'uncertainty',
    'uncertain', 'volatile', 'volatility', 'fluctuation', 'fluctuations',
    'modest decline', 'slight dip', 'slight drop',
]

# Moderate negative sentiment words (score: -1)
MODERATE_NEGATIVE = [
    'fall', 'falls', 'falling', 'drop', 'drops', 'dropping', 'decline', 'declines',
    'declining', 'decrease', 'decreases', 'decreasing', 'down', 'downside',
    'loss', 'losses', 'losing', 'negative', 'pessimistic', 'pessimism',
    'worry', 'worries', 'worried', 'fear', 'fears', 'fearful',
    'dip', 'dips', 'dipped', 'slip', 'slips', 'slipping', 'slide', 'slides',
    'tumble', 'tumbles', 'tumbling', 'sink', 'sinks', 'sinking',
    'earnings miss', 'revenue decline', 'margin compression', 'guidance cut',
    'guidance lowered', 'downgrade', 'downgraded', 'sell rating', 'underperform',
    'resistance', 'support break', 'breakdown', 'break down',
]

# Strong negative sentiment words (score: -2)
STRONG_NEGATIVE = [
    'crash', 'crashes', 'crashing', 'plunge', 'plunges', 'plunging',
    'collapse', 'collapses', 'collapsing', 'collapse', 'crisis', 'crises',
    'bearish', 'bear market', 'bear run', 'correction', 'corrections',
    'selloff', 'sell-off', 'sell off', 'rout', 'routs', 'panic', 'panics',
    'disappoint', 'disappoints', 'disappointing', 'disappointment',
    'failure', 'failures', 'fails', 'failed', 'failing',
    'worst', 'worst-performing', 'underperform', 'underperforming',
    'breakdown', 'break down', 'support break', 'resistance break down',
]

# Intensity modifiers (multiply base score)
INTENSITY_MODIFIERS = {
    'very': 1.5,
    'extremely': 2.0,
    'highly': 1.5,
    'significantly': 1.5,
    'substantially': 1.5,
    'dramatically': 2.0,
    'slightly': 0.5,
    'somewhat': 0.75,
    'moderately': 0.75,
    'marginally': 0.5,
}

# Negation words (flip polarity)
NEGATION_WORDS = [
    'not', 'no', 'never', 'none', 'nothing', 'nobody', 'nowhere',
    'neither', 'nor', "n't", "don't", "doesn't", "didn't", "won't",
    "can't", "couldn't", "shouldn't", "wouldn't", "isn't", "aren't",
    "wasn't", "weren't", "hasn't", "haven't", "hadn't",
]

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


def calculate_sentiment_score(text: str) -> float:
    """
    Calculate sentiment score for a text.
    
    Returns:
        Score in range [-1, +1], where:
        - +1 = very positive
        - 0 = neutral
        - -1 = very negative
    """
    if pd.isna(text) or not str(text).strip():
        return 0.0
    
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
        return 0.0
    
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
    avg_score = total_score / max(len(word_occurrences), 1)
    normalized_score = np.tanh(avg_score)
    
    return float(normalized_score)


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
    df['sentiment_score'] = df[text_col].apply(calculate_sentiment_score)
    
    # Summary statistics
    positive_count = (df['sentiment_score'] > 0).sum()
    negative_count = (df['sentiment_score'] < 0).sum()
    neutral_count = (df['sentiment_score'] == 0).sum()
    
    print(f"\nSentiment Score Summary:")
    print(f"  Positive (>0): {positive_count:,} ({100*positive_count/len(df):.1f}%)")
    print(f"  Neutral (=0): {neutral_count:,} ({100*neutral_count/len(df):.1f}%)")
    print(f"  Negative (<0): {negative_count:,} ({100*negative_count/len(df):.1f}%)")
    print(f"\n  Mean score: {df['sentiment_score'].mean():.3f}")
    print(f"  Std dev: {df['sentiment_score'].std():.3f}")
    print(f"  Min: {df['sentiment_score'].min():.3f}")
    print(f"  Max: {df['sentiment_score'].max():.3f}")
    
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
