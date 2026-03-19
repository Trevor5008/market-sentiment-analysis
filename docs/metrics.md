# Metric Definitions

## Baseline
```python
MIN_TICKERS = 5 # minimum tickers req'd for dispersion calculation
COLUMNS = [price-date, ticker, next_open, next_close]
``` 
### Correlation
Pairwise Correlation = measures the **strength and direction** of the relationship b/n two variables across time
- -1 = Perfect negative/inverse relationship
- 0 = Neutral (no relationship)
- 1 = Perfect positive/direct relationship

### Rolling Window
Rolling Window = evaluates how a statistical relationship **changes over time**
- Uses overlapping (sliding) window to calculate metrics
    - 5d: day 1-5, day 2-6, day 3-7, etc.
    - 10d: day 1-10, day 2-11, day 3-12, etc.
    - 30d: day 1-30, 2-31, 3-32, etc.

*Pairwise Correlations and Rolling Window used to determine whether signals exhibit consistent relationships w/ market dispersion*


### Return Dispersion
1. Primary (standard deviation)
- Choosing std over variance for interpretability
- This will be sensitive to outliers discussed in `docs/source_bias_findings.md` 
- Variance is accessible by squaring std (ex. ret_cs_var = ret_cs_std ** 2)

2. Secondary (mean absolute deviation or MAD)
- MAD: A **robust dispersion metric** which is less sensitive to extreme ticker movements and reflects *typical* level of dispersion across the group 
- Returns are measured as $r_{i,t} = \frac{\mathrm{close}_{i,t} - \mathrm{open}_{i,t}}{\mathrm{open}_{i,t}}$

- Low dispersion indicates **synchronous movement** and suggests macro-level drivers

### Metric Stability Checks
- Source Exclusion Robustness
- FinBERT (v2) vs dictionary-based scoring (v1)
- Ticker coverage thresholds

### Time Alignment
- Sentiment signals originate from `article_date = t`
- Returns and dispersion are measured on `price_date = t+1` *or next trading day*

### Output Fields
- `price_date, ret_cs_std, ret_cs_mad, ret_mean, n_tickers_returns, coverage_ratio`
    - `coverage_ratio = n_tickers_returns / 7`

