# Data Snapshot Log

## What is tracked in `main`
This repo tracks **only** the latest “canonical snapshot” files:

- `data/raw/gdelt_articles.csv`
- `data/raw/prices_daily.csv`
- (optional) `data/processed/gdelt_articles_clean.csv`

All other generated files are **local artifacts** and must not be committed.

---

## Latest Snapshot
**Updated:** 2026-01-26  
**Updated by:** @trevor

### GDELT (gdelt_articles.csv)
- Date range: 2026-01-24 → 2026-01-25
- Rows: 1,400
- Notes: 200 articles per ticker (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA). Description and sourceCountry columns are 100% missing (expected). Some duplicate URLs may exist due to syndication.

### Prices (prices_daily.csv)
- Date range: 2025-12-26 → 2026-01-23
- Tickers: 7 (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA)
- Notes: 133 rows total. No missing trading days (NYSE calendar). No logical price errors or outliers detected.

### Processing
- `gdelt_articles_clean.csv` regenerated: 2026-01-26
- Script: `python scripts/cleaning_gdelt.py`

