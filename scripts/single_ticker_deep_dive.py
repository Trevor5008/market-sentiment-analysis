import pandas as pd
import yfinance as yf  
from pathlib import Path

# --- CONFIGURATION ---
TARGET_TICKER = "NVDA" 
HISTORY_YEARS = 2      # 1 year gives ~252 data points

def analyze_ticker_robust(ticker):
    print(f" Fetching {HISTORY_YEARS} year(s) of data for {ticker} to ensure statistical significance...")
    
    # 1. Fetch fresh long term data directly
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period=f"{HISTORY_YEARS}y")
    
    if df.empty:
        print(f" Error: Could not fetch data for {ticker}")
        return

    # Clean up (yfinance uses capitalized columns change to lowercase)
    df.reset_index(inplace=True)
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure date is datetime
    # remove timezone for simplicity
    df['date'] = df['date'].dt.tz_localize(None)
    df = df.sort_values('date')

    # INSIGHT 1: Calendar Effect
    df['day_name'] = df['date'].dt.day_name()
    df['daily_return'] = df['close'].pct_change() * 100
    
    day_stats = df.groupby('day_name')['daily_return'].mean().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    )

    # INSIGHT 2: Overnight Gaps
    df['prev_close'] = df['close'].shift(1)
    df['gap_pct'] = ((df['open'] - df['prev_close']) / df['prev_close']) * 100
    avg_gap = df['gap_pct'].abs().mean()

    # INSIGHT 3: Volume Impact
    # Using a rolling average for volume
    df['vol_ma'] = df['volume'].rolling(20).mean()
    
    # High volume is > 1.5x the recent average
    high_vol_days = df[df['volume'] > 1.5 * df['vol_ma']]
    
    # Win rate: Did it close higher than it opened? (Green candle)
    # or did it close higher than yesterday? (Price gain)
    # Let's use Price Gain (daily_return > 0)
    if len(high_vol_days) > 0:
        high_vol_win_rate = (high_vol_days['daily_return'] > 0).mean() * 100
        count_high_vol = len(high_vol_days)
    else:
        high_vol_win_rate = 0
        count_high_vol = 0

    # INSIGHT 4: Momentum Memory
    df['prev_return'] = df['daily_return'].shift(1)
    
    # Filter for days where previous day was UP
    prev_up = df[df['prev_return'] > 0]
    if len(prev_up) > 0:
        # How many of those days were ALSO up?
        consecutive_up = prev_up[prev_up['daily_return'] > 0]
        continuation_prob = (len(consecutive_up) / len(prev_up)) * 100
    else:
        continuation_prob = 0

    # REPORTING 
    print(f"==================================================")
    print(f" ANALYSIS FOR: {ticker} ({len(df)} days analyzed)")
    print(f"==================================================")
    
    print(f"\n1. THE CALENDAR EFFECT (Avg Return)")
    for day, ret in day_stats.items():
        if pd.isna(ret): ret = 0.0
        bar = "🟩" if ret > 0 else "🟥"
        print(f"   - {day:<10}: {bar} {ret:+.2f}%")

    print(f"\n2. OVERNIGHT GAPS")
    print(f"   - Avg Gap Size: {avg_gap:.2f}%")
    if avg_gap > 1.5:
        print("   - Insight: Highly sensitive to overnight news.")
    else:
        print("   - Insight: Relatively stable opens.")

    print(f"\n3. VOLUME IMPACT (Sample size: {count_high_vol} days)")
    print(f"   - When volume surges, price closes GREEN {high_vol_win_rate:.1f}% of the time.")
    if high_vol_win_rate > 55:
        print("   - Insight: Big volume indicates BUYING pressure.")
    elif high_vol_win_rate < 45:
        print("   - Insight: Big volume indicates SELLING pressure.")
    else:
        print("   - Insight: Volume spikes are neutral/indecisive.")

    print(f"\n4. MOMENTUM MEMORY")
    print(f"   - Probability of a 'Green Day' following another 'Green Day': {continuation_prob:.1f}%")
    if continuation_prob > 55:
        print("   - Conclusion: TRENDING BEHAVIOR DETECTED.")
    elif continuation_prob < 45:
        print("   - Conclusion: MEAN REVERTING BEHAVIOR DETECTED.")
    else:
        print("   - Conclusion: RANDOM WALK (No memory).")
    print(f"==================================================")

# Run it
if __name__ == "__main__":
    analyze_ticker_robust(TARGET_TICKER)