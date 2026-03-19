from pathlib import Path

__cwd = Path(__file__)
PROJECT_ROOT = __cwd.resolve().parents[4]
GDELT_W_SENT = PROJECT_ROOT / "data" / "processed" / "gdelt_articles_with_sentiment.csv"
GDELT_WO_SENT = PROJECT_ROOT / "data" / "processed" / "gdelt_articles_clean.csv"
PRICES = PROJECT_ROOT / "data" / "processed" / "prices_daily_clean.csv"
GDELT_OHLCV = PROJECT_ROOT / "data" / "processed" / "gdelt_ohlcv_join.csv"