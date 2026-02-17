import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
# Replace this with your actual file path
FILE_PATH = "data/processed/gdelt_ohlcv_join.csv" 

def analyze_news_impact(file_path):
    print(f"Loading data from {file_path}...")
    
    # 1. Load Data
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(" File not found. Please check the path.")
        return

    # 2. Data Prep
    df['price_date'] = pd.to_datetime(df['price_date'])
    original_count = len(df)
    df = df[df['sentiment_score'] != 0].copy()
    df = df[df['sentiment_score'].abs() > 0.2].copy()
    dropped_count = original_count - len(df)
    print(f"🧹 Filtered Data: Removed {dropped_count} articles with 0 sentiment.")
    print(f"   (Remaining articles: {len(df)})")

    # 3. Aggregation (Critical Step)
    daily_df = df.groupby(['ticker', 'price_date']).agg({
        'sentiment_score': 'mean',         
        'next_open': 'first',               
        'next_close': 'first',
        'title': 'count'
    }).reset_index()
    
    daily_df.rename(columns={'title': 'article_count'}, inplace=True)
    daily_df = daily_df.sort_values(['ticker', 'price_date'])

    # 4. Calculate Overnight Gap
    daily_df['prev_close'] = daily_df.groupby('ticker')['next_close'].shift(1)
    daily_df['gap_pct'] = ((daily_df['next_open'] - daily_df['prev_close']) / daily_df['prev_close']) * 100

    # Drop the first row
    daily_df = daily_df.dropna()

    # 5. filter for days where the Gap was > 1% (Significant)
    big_gaps = daily_df[daily_df['gap_pct'].abs() > 1.0].copy()
    
    # 6. Check Correlation
    # Does high sentiment lead to a positive gap?
    correlation = daily_df['sentiment_score'].corr(daily_df['gap_pct'])


    print(f"\n==================================================")
    print(f" NEWS SENTIMENT vs. PRICE GAPS")
    print(f"==================================================")
    print(f"Total Trading Days Analyzed: {len(daily_df)}")
    print(f"Correlation (Sentiment -> Gap): {correlation:.4f}")
    
    if correlation > 0.1:
        print("    Insight: Positive sentiment predicts positive gaps (Market follows news).")
    elif correlation < -0.1:
        print("    Insight: Negative correlation (Market 'Sells the News').")
    else:
        print("    Insight: No strong link between sentiment and opening price.")

    print(f"\n TOP 5 BIGGEST OVERNIGHT GAPS & SENTIMENT:")
    # Sort by magnitude of the gap
    top_moves = big_gaps.sort_values('gap_pct', key=abs, ascending=False).head(5)
    
    if top_moves.empty:
        print("   No gaps > 1.0% found.")
    else:
        print(f"{'Date':<12} | {'Gap %':<10} | {'Sentiment':<10} | {'Articles'}")
        print("-" * 50)
        for _, row in top_moves.iterrows():
            date_str = row['price_date'].strftime('%Y-%m-%d')
            print(f"{date_str:<12} | {row['gap_pct']:+.2f}%     | {row['sentiment_score']:.2f}       | {row['article_count']}")

if __name__ == "__main__":
    analyze_news_impact(FILE_PATH)