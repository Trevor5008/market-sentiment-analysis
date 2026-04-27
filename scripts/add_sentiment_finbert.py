#!/usr/bin/env python3
"""
scripts/add_sentiment_finbert.py

Add sentiment scores to GDELT articles using FinBERT (transformer-based model).

FinBERT is a BERT model fine-tuned on financial news for sentiment analysis.
It provides:
- Better context understanding than dictionary methods
- Domain-specific financial sentiment (trained on financial news)
- Probability scores for positive/negative/neutral classes

Performance considerations:
- GPU: ~1000 articles/minute (with batch processing)
- CPU: ~50-100 articles/minute (with batch processing)
- For 12,000 articles: ~2-3 minutes on GPU, ~2-3 hours on CPU

Usage:
    # With GPU (recommended)
    python scripts/add_sentiment_finbert.py

    # With CPU (slower)
    python scripts/add_sentiment_finbert.py --device cpu

    # Custom batch size (larger = faster but more memory)
    python scripts/add_sentiment_finbert.py --batch-size 64
"""

import argparse
import sys
import pandas as pd
import numpy as np
from msa.utils.paths import get_processed_data_path
from tqdm import tqdm
import torch
from pathlib import Path

# Check if transformers is installed
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch.nn.functional as F
except ImportError:
    print("=" * 70)
    print("ERROR: Required libraries not installed")
    print("=" * 70)
    print("\nYou need to install transformers and pytorch.")
    print("\nFor conda/miniconda environments, run:")
    print("  conda install -c conda-forge transformers")
    print("  conda install pytorch -c pytorch")
    print("\nOr using pip in your conda environment:")
    print("  pip install transformers torch")
    print("\nNote: pytorch with GPU support requires specific installation.")
    print("Visit: https://pytorch.org/get-started/locally/")
    print("=" * 70)
    sys.exit(1)


# ============================================================
# PATHS
# ============================================================

DEFAULT_INPUT = get_processed_data_path() / "gdelt_articles_accumulated.csv"
DEFAULT_OUTPUT = get_processed_data_path() / "gdelt_articles_with_sentiment.csv"

# ============================================================
# FINBERT SENTIMENT SCORING
# ============================================================

class FinBERTSentimentScorer:
    """
    Wrapper for FinBERT sentiment analysis with batch processing.
    
    The model outputs 3 probabilities: [positive, negative, neutral]
    We convert to a continuous score in [-1, +1] range:
    - score = P(positive) - P(negative)
    - confidence = max(P(positive), P(negative), P(neutral))
    """
    
    def __init__(self, device="auto", model_name="ProsusAI/finbert"):
        """
        Initialize FinBERT model.
        
        Args:
            device: "auto", "cuda", or "cpu"
            model_name: HuggingFace model identifier
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Loading FinBERT model on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        # Labels: [positive, negative, neutral]
        self.labels = ['positive', 'negative', 'neutral']
        print("Model loaded successfully")
    
    def predict_batch(self, texts, batch_size=32, max_length=512):
        """
        Predict sentiment for a batch of texts.
        
        Args:
            texts: List of text strings
            batch_size: Number of texts to process at once
            max_length: Maximum token length (FinBERT trained on 512)
            
        Returns:
            scores: Array of sentiment scores in [-1, +1]
            confidences: Array of confidence scores in [0, 1]
            labels: Array of predicted labels ('positive', 'negative', 'neutral')
        """
        scores = []
        confidences = []
        predicted_labels = []
        
        # Process in batches
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = F.softmax(outputs.logits, dim=1)
            
            # Convert to CPU numpy
            probs = probs.cpu().numpy()
            
            # For each prediction in batch
            for prob in probs:
                # prob = [P(positive), P(negative), P(neutral)]
                p_pos, p_neg, p_neu = prob
                
                # Sentiment score: positive - negative (range: [-1, +1])
                score = float(p_pos - p_neg)
                
                # Confidence: highest probability
                confidence = float(max(p_pos, p_neg, p_neu))
                
                # Predicted label
                label_idx = np.argmax(prob)
                label = self.labels[label_idx]
                
                scores.append(score)
                confidences.append(confidence)
                predicted_labels.append(label)
        
        return np.array(scores), np.array(confidences), np.array(predicted_labels)

# ============================================================
# MAIN PROCESSING
# ============================================================

def add_finbert_sentiment(df, text_col='title', batch_size=32, device="auto"):
    """
    Add FinBERT sentiment scores to dataframe.
    
    Args:
        df: DataFrame with articles
        text_col: Column containing text to analyze
        batch_size: Batch size for processing
        device: "auto", "cuda", or "cpu"
        
    Returns:
        DataFrame with added columns:
        - sentiment_score: continuous score in [-1, +1]
        - sentiment_confidence: model confidence in [0, 1]
        - sentiment_label: 'positive', 'negative', or 'neutral'
    """
    print(f"\n{'='*60}")
    print(f"Adding FinBERT sentiment to {len(df):,} articles")
    print(f"Text column: '{text_col}'")
    print(f"Batch size: {batch_size}")
    print(f"{'='*60}\n")
    
    # Initialize model
    scorer = FinBERTSentimentScorer(device=device)
    
    # Get texts (handle missing values)
    texts = df[text_col].fillna("").astype(str).tolist()
    
    # Predict
    scores, confidences, labels = scorer.predict_batch(
        texts, 
        batch_size=batch_size
    )
    
    # Add to dataframe
    df = df.copy()
    df['sentiment_score'] = scores
    df['sentiment_confidence'] = confidences
    df['sentiment_label'] = labels
    
    # Statistics
    print(f"\n{'='*60}")
    print("Sentiment Statistics:")
    print(f"{'='*60}")
    print(f"Mean score: {scores.mean():.3f}")
    print(f"Std score: {scores.std():.3f}")
    print(f"Mean confidence: {confidences.mean():.3f}")
    print(f"\nLabel distribution:")
    print(df['sentiment_label'].value_counts())
    print(f"{'='*60}\n")
    
    return df

def main():
    parser = argparse.ArgumentParser(
        description="Add FinBERT sentiment scores to GDELT articles"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input CSV file (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--text-col",
        type=str,
        default="title",
        help="Column containing text to analyze (default: title)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for processing (default: 32, increase for GPU)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to use (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Load data
    print(f"Loading articles from: {args.input}")
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df):,} articles\n")
    
    # Validate text column
    if args.text_col not in df.columns:
        print(f"Error: Column '{args.text_col}' not found")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    # Add sentiment
    df = add_finbert_sentiment(
        df,
        text_col=args.text_col,
        batch_size=args.batch_size,
        device=args.device
    )
    
    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving to: {args.output}")
    df.to_csv(args.output, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
