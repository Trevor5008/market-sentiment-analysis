# MAG7 Dispersion Analysis: Data Flow Tracking

## Overview

This document explains the data filtering pipeline in the MAG7 dispersion hypothesis notebook, tracking data dropoff at each step to diagnose sparsity issues.

## Data Flow Pipeline

### Step-by-Step Breakdown

```
1. Initial Dataset
   - Source: gdelt_ohlcv_join.csv
   - Count: 12,523 rows
   - Description: All articles with joined sentiment and OHLCV data

2. MAG7 Filter
   - Action: Filter to MAG7 tickers only (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)
   - Expected count: ~5,500-7,000 rows
   - Loss: ~5,500-7,000 rows (non-MAG7 companies filtered out)

3. Date Window Filter
   - Action: Filter to 2024-02-23 through 2026-02-23 (2-year window)
   - Expected count: Depends on data distribution
   - Loss: Articles outside the analysis window

4. Sentiment Present Filter
   - Action: Keep only articles where sentiment_present = True
   - Expected count: ~5,286 rows (based on current data)
   - Loss: ~57% of articles (dictionary-based sentiment detection limitation)
   - **KEY BOTTLENECK**: This is the primary source of data sparsity

5. Daily Aggregation (article_date × ticker)
   - Action: Aggregate multiple articles per ticker per day into mean_sentiment
   - Expected count: ~462 pairs
   - Description: One row per (article_date, ticker) combination

6. Daily Coverage Check
   - Action: Count how many tickers appear on each article_date
   - Expected distribution:
     - 1 ticker: X days
     - 2 tickers: Y days
     - 3 tickers: Z days
     - 4 tickers: W days
     - 5+ tickers: V days (target for cross-sectional analysis)

7. Sentiment Dispersion Metrics
   - Action: Calculate cross-sectional variance, breadth, and mean per day
   - Count before filter: All unique article_dates with >=1 ticker
   - Count after >=5 ticker filter: ~50-55 days (based on current data)
   - **KEY BOTTLENECK**: Insufficient days with 5+ ticker coverage

8. Return Calculation
   - Source: Same MAG7 + date window, but NO sentiment_present filter
   - Action: Calculate next_day_ret = (next_close - next_open) / next_open
   - Count: All article-price pairs in MAG7 + date window

9. Return Aggregation
   - Action: Deduplicate to (price_date × ticker) and calculate dispersion
   - Count: More days than sentiment (no sentiment filter applied)

10. Alignment
    - Action: Inner join sentiment_dispersion with return_dispersion via article_date → price_date
    - Final count: Intersection of days with both sentiment and return data
    - Expected: ~40-50 days for analysis

```

## Key Diagnostics Output

The notebook now displays the following diagnostic information at each stage:

### 1. Data Filtering Pipeline (Cell 6)
```
======================================================================
DATA FILTERING PIPELINE
======================================================================

1. Initial dataset: 12,523 rows
2. After MAG7 filter: X,XXX rows (-X,XXX)
3. After date window filter (2024-02-23 to 2026-02-23): X,XXX rows (-X,XXX)
4. After sentiment_present filter: 5,286 rows (-X,XXX)
5. After daily aggregation (article_date × ticker): 462 rows

   Daily ticker coverage distribution:
   {1: XX, 2: XX, 3: XX, 4: XX, 5: XX, 6: XX, 7: XX}

   Days with >=5 tickers: XX / YY total days
   Days with >=4 tickers: XX / YY total days
   Days with >=3 tickers: XX / YY total days

======================================================================
KEY DIAGNOSTICS
======================================================================

Sentiment present statistics (in MAG7 + date window):
  Articles with sentiment: 5,286 / X,XXX (XX.X%)
  Articles without sentiment: X,XXX (XX.X%)

Sentiment score stats (articles with sentiment):
[Statistical summary of sentiment_score]

Date range in filtered data:
  First article: YYYY-MM-DD
  Last article: YYYY-MM-DD
  Unique days: XXX
```

### 2. Sentiment Dispersion Filtering (Cell 7)
```
======================================================================
SENTIMENT DISPERSION FILTERING
======================================================================

6. Before coverage filter: XX days
   Coverage distribution: {1: X, 2: X, 3: X, 4: X, 5: X, 6: X, 7: X}

7. After >=5 ticker filter: XX days (-XX)
   XX.X% of days retained
```

### 3. Return Dispersion Calculation (Cell 12)
```
======================================================================
RETURN DISPERSION CALCULATION
======================================================================

8. Rows for return calculation (MAG7 + date window, no sentiment filter): X,XXX
9. Unique (price_date × ticker) pairs: X,XXX

10. Before coverage filter: XXX trading days
    Coverage distribution: {1: X, 2: X, ..., 7: X}

11. After >=5 ticker filter: XXX trading days (-XX)
    XX.X% of trading days retained
```

### 4. Sentiment-Return Alignment (Cell 13)
```
======================================================================
SENTIMENT-RETURN ALIGNMENT
======================================================================

12. Sentiment days available: XX
13. Return days available: XXX
14. Unique article_date → price_date mappings: XXX

15. Final aligned dataset: XX days
    XX.X% of sentiment days successfully aligned with returns

======================================================================
COMPLETE DATA FLOW SUMMARY
======================================================================

Initial dataset:                12,523 rows
  ↓ MAG7 filter
  ↓ Date window filter
  ↓ sentiment_present filter
Filtered articles:              5,286 rows
  ↓ Daily aggregation (article_date × ticker)
Daily sentiment pairs:          462 pairs
  ↓ Cross-sectional metrics per day
Daily sentiment metrics:        XX days
  ↓ >=5 ticker coverage filter
Sentiment dispersion (final):   XX days (XX.X%)
  ↓ Align with returns
Final analysis dataset:         XX days (XX.X%)
```

## Key Findings

### Primary Bottleneck: sentiment_present Filter (Step 4)
- **Impact**: Removes ~57% of articles
- **Root Cause**: Dictionary-based sentiment method only detects sentiment in 43% of articles
- **Solution**: Implement FinBERT transformer model to increase coverage to 85-95%

### Secondary Bottleneck: >=5 Ticker Coverage Requirement (Step 7)
- **Impact**: Reduces daily observations from ~90-100 days to ~50-55 days
- **Root Cause**: Sparse article distribution across MAG7 tickers on any given day
- **Context**: This is necessary for statistical validity of cross-sectional metrics
- **Alternative Approaches**:
  - Lower threshold to >=4 or >=3 tickers (reduces validity)
  - Use rolling windows (3-day, 5-day) to smooth coverage
  - Impute missing tickers with forward-fill or neutral sentiment

### Data Retention Rates
Based on current dictionary-based sentiment:
- Step 1→4: ~42% retention (primarily due to sentiment_present filter)
- Step 4→7: ~10-12% retention (daily aggregation + coverage filter)
- Overall: ~4-5% of initial articles contribute to final analysis

## Next Steps

### Immediate: FinBERT Integration
1. Run `scripts/test_finbert_sample.py` to validate quality on 1,000 articles
2. If satisfactory, run `scripts/add_sentiment_finbert.py` on full dataset
3. Rebuild joined dataset with `scripts/build_gdelt_ohlcv_join.py`
4. Re-run this notebook to see improved coverage

### Expected Impact of FinBERT
- Step 4 sentiment coverage: 43% → 85-95%
- Step 5 daily sentiment pairs: 462 → ~1,000-1,100
- Step 7 days with >=5 tickers: ~55 → ~120-150
- Final analysis dataset: ~50 → ~100-120 days

This would more than double the statistical power of the analysis while maintaining the >=5 ticker coverage requirement.

## Monitoring and Validation

After implementing changes, monitor:
1. Article retention rate at each step
2. Daily ticker coverage distribution
3. Sentiment score distribution (ensure FinBERT scores are reasonable)
4. Final dataset size and date range coverage
5. Statistical validity of cross-sectional metrics

---

**Last Updated**: 2026-02-24
**Notebook**: `mag7_dispersion_hyp.ipynb`
**Author**: Data Pipeline Analysis
