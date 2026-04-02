# Metric Definitions

Short guide for the team: **baseline** dispersion/correlation terms, **regression & inference** (hypothesis notebooks), and **time-based validation** / **OOS** metrics (e.g. `05-hyp-sentiment-modifier.ipynb`).

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

### Cluster-robust standard errors

**Clustering** allows correlation of the regression error **within a group** (e.g. all articles on the same calendar `price_date`, or all rows for the same `ticker`). Standard errors are adjusted so that **inference is asymptotically valid** when errors are independent **across clusters** but not necessarily within them.

- One-way clustering: a single grouping column (e.g. date *or* ticker).
- **Two-way** clustering (e.g. date **and** ticker) is stricter and often implemented in specialized packages when software supports it.

Contrast with **HC1**: HC1 addresses **heteroskedasticity** (unequal variance) but still treats observations as independent unless you add clustering.

---

## Time-based validation & forecast metrics (reference)

Terms below support **`05-hyp-sentiment-modifier.ipynb`** (walk-forward with rolling training windows) and related notebooks. They describe **how** we evaluate predictions over time, not project-specific column names.

### In-sample vs out-of-sample (OOS)

- **In-sample:** The model is **fit and evaluated on the same rows** (or the same time period). Metrics can look **too good** because the model has already “seen” those outcomes.
- **Out-of-sample (OOS):** The model is **fit only on past data** and evaluated on **future (or held-out) rows** that were **not** used in estimation. This better reflects **forward** use but is still **not** the same as live trading (no fills, costs, etc.).

### Walk-forward validation

A **time-ordered** procedure: move forward through the calendar **one test step at a time** (e.g. one `price_date`), each time **re-fitting** the model on **training history** and scoring **only the next period(s)**. This mimics **sequence**: at each step you only use information available **before** the test date.

- Avoids random train/test splits that **shuffle** time and leak **future** information into training.

### Rolling vs expanding training window

Both are common **training sets** in walk-forward work:

| Style | Training data before test day $t$ | Typical use |
|--------|-------------------------------------|-------------|
| **Expanding** | **All** history strictly before $t$ | Maximum data; early periods have small train sets; later periods weight the **distant** past equally with the recent past. |
| **Rolling** (sliding) | Only the **last $W$** distinct time periods (e.g. last $W$ trading days) before $t$ | Emphasizes a **recent** regime; drops old data; $W$ must be chosen explicitly. |

In **`05`**, `USE_EXPANDING_WINDOW` switches between these ideas. The choice affects **non-stationarity**: relationships that drift over time may favor a **rolling** window.

### “Honest” threshold / avoiding leakage (example: `neg_extreme`)

If a rule uses a **cutoff** derived from the data (e.g. bottom 10% of `sentiment_score` **among negative articles**), recomputing that cutoff using **both train and test** rows from the **same fold** leaks information from the **future** into training.

An **honest** walk-forward fold:

1. Compute the quantile (or rule) **only on the training slice** for that step.
2. Apply the **same numeric threshold** to **test** rows.

That keeps the evaluation order aligned with **real-time**: you only know today’s distribution of scores **after** seeing the past, not the future.

### OOS $R_2$ (out-of-sample coefficient of determination)

For a test vector $y$ and predictions $\hat{y}$, OOS $R^2$ compares the model’s MSE to the MSE of predicting the **training-sample mean** $\bar{y}_{\text{train}}$ on the test set (common sklearn definition):

- Values **$\le 0$** mean the model’s errors are **no better** (or worse) than a trivial constant predictor from train—**common** in noisy financial returns at short horizons.
- **Do not** interpret OOS $R^2$ like in-sample $R^2$; negative values are informative, not “bugs.”

### RMSE (root mean squared error)

$\text{RMSE} = \sqrt{\frac{1}{n}\sum_i (y_i - \hat{y}_i)^2}$ in the **evaluation** set (here, OOS). Same units as $y$ (e.g. daily returns). **Lower** is better; use to **compare models**, not as an absolute “good/bad” without a baseline.

### Brier score

For **binary** outcomes $y_i \in \{0,1\}$ and predicted probabilities $\hat{p}_i = P(y_i=1 \mid X_i)$:

$$\text{Brier} = \frac{1}{n}\sum_i (y_i - \hat{p}_i)^2.$$

- **0** = perfect calibration and sharpness; **0.25** is a naive baseline for a **marginal rate of 50%** (always predict 0.5). **Lower** is better.
- Penalizes both **wrong** class calls and **overconfident** probabilities.

Used in **`05`** for **logit** predictions of **down day** (`forward return < 0`) on the **OOS** slice.

### Sign accuracy (directional hit rate)

Share of test observations where **sign**$(\hat{y})$ matches **sign**$(y)$, often **restricted** to rows where $y \neq 0$ (returns of exactly zero make “direction” ambiguous).

- **0.5** ≈ coin-flip on balanced up/down tests; **not** sufficient alone (a tiny positive return vs tiny negative matters economically).
- Useful **diagnostic** alongside RMSE / Brier.

### Calibration (probability forecasts)

A model is **well calibrated** if, among all days where we predict “about $p$” chance of a down day, the **long-run frequency** of down days is **near $p$**.

- A simple check: plot or correlate **predicted** mean probability of the event vs **realized** event rate over groups (e.g. per walk-forward test day in **`05`**), or use **reliability** curves for finer bins.
- **ROC-AUC** ranks well; **Brier** and calibration address **absolute** probability levels.

### Average marginal effects (logit)

The **average marginal effect** summarizes how a **small change** in a predictor (or a discrete jump, e.g. 0→1) changes the **predicted probability** of the event, **averaged** over the estimation sample. Complements raw logit coefficients, which are on the **log-odds** scale. (Example: `get_margeff(at="overall")` in `statsmodels`.)

