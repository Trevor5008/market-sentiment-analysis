# Metric Definitions

## Baseline
```python
MIN_TICKERS = 5 (min 5/7 must be present for adequate coverage)
COLUMNS = [price-date]
``` 

## Return Dispersion
1. Primary (standard deviation)
- Choosing std over variance for interperatibility
- This will be sensitive to outliers discussed in `docs/source_bias_findings.md` 
- Variance is accessible by squaring std (ex. ret_cs_var = ret_cs_std ** 2)

2. Secondary (mean absolute deviation)
- Dispersion is measured as the mean of {close (t+1) - open (t+1)} / open (t+1)