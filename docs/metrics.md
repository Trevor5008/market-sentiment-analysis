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

---

## Regression, inference & classification (reference)

Terms below appear in hypothesis notebooks (e.g. lag / negative-sentiment risk / momentum interaction analyses). 
*They are **methodology**, not project-specific column names.*

### Ordinary least squares (OLS)

Linear regression that **minimizes the sum of squared residuals** between an outcome $y$ and a linear combination of predictors $X\beta$. Coefficients describe **conditional associations** (holding other included variables fixed), not necessarily causal effects.

### HC1 (heteroskedasticity-consistent) standard errors

**HC** estimators adjust OLS **standard errors** so that inference (t-stats, p-values, confidence intervals) remains **asymptotically valid** when error variance **differs across observations** (heteroskedasticity). 
- **HC1** is one common variant (applies a small-sample rescaling relative to **HC0**). 
*In code (e.g. `statsmodels`), this is often `fit(cov_type="HC1")`.*

HC1 does **not** correct for **correlated errors within groups** (e.g. many articles on the same `price_date` or `ticker`); for that, use **cluster-robust** covariance estimators instead.

### Interaction (moderation)

A **product term** between two predictors (e.g. `momentum_1d * neg_extreme`) allows the **slope** of the outcome on one variable to **depend on** the level of the other. 
- A significant interaction means the relationship is **not additive**; interpret **main effects** at a chosen reference level or use **marginal effects** / simple slopes at specific values.

### Logistic regression (logit)

- Models the **log-odds** of a binary outcome (e.g. next-day return $< 0$) as a linear function of predictors. Coefficients are on the **logit scale**. 
- For interpretability, report **predicted probabilities** or **average marginal effects**.

### ROC-AUC (area under the ROC curve)

Summarizes how well **predicted probabilities** rank **positive vs negative** cases for a binary label. 
- **1** = perfect separation. 
- **0.5** = no better than random. **In-sample** AUC can be optimistic; use holdout or time-based validation for generalization claims.

### Coefficient of determination ($R^2$)

Share of variance in $y$ **explained** by the fitted linear model **in the sample used to fit**. 
- Increases with extra predictors; **does not** imply causal explanation or good out-of-sample performance.

### Permutation test

A **resampling** null: repeatedly **shuffle** one variable (holding others fixed) and recompute a test statistic (e.g. correlation or regression coefficient). 
- The **p-value** is the fraction of permutations where the statistic is at least as extreme as observed.
    - Useful when parametric assumptions are doubtful.

