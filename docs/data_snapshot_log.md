# Data Snapshot Log

## What is tracked in `main`
This repo tracks **only** the latest “canonical snapshot” files:

- `data/raw/gdelt_articles.csv`
- `data/raw/prices_daily.csv`
- (optional) `data/processed/gdelt_articles_clean.csv`

All other generated files are **local artifacts** and must not be committed.

---

## Latest Snapshot
**Updated:** YYYY-MM-DD  
**Updated by:** @<name>

### GDELT (gdelt_articles.csv)
- Date range: YYYY-MM-DD → YYYY-MM-DD
- Rows: N
- Notes: (missing days? duplicates? filtering?)

### Prices (prices_daily.csv)
- Date range: YYYY-MM-DD → YYYY-MM-DD
- Tickers: N
- Notes: (missing days? holidays handled?)

### Processing (optional)
- `gdelt_articles_clean.csv` regenerated: YYYY-MM-DD
- Script: `python scripts/cleaning_gdelt.py --input ... --output ...`

