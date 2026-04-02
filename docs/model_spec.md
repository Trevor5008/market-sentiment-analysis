# Modeling approach 
*Reference* [metrics.md](metrics.md)

### Objective

Target **architecture** for exploratory work (not a deployed production forecaster):

- **Momentum** is the **primary** signal in the linear return equation.
- **Sentiment** enters **only as a candidate modifier** (interaction), not as a standalone return driver in current results.
- **Out-of-sample (OOS)** checks (walk-forward, honest thresholds) are the **main** gate for whether the “modifier” story generalizes.

### Findings summary (Sprints / hypothesis track)

- **Momentum** is the strongest and most stable **linear** term in the **negative-headline** slice used in `04` / `05`.
- **Sentiment level** (`neg_extreme` alone) shows **little** consistent additive effect on returns once momentum and the interaction are included (see `04`).
- **Extreme negative sentiment** (definition below) does **not** robustly shift returns **by itself**
  - Evidence for **changing the momentum–return slope** is **in-sample** and **definition- and time-sensitive** (`04` robustness / temporal splits; `05` clustering and walk-forward).
- **Interaction** (momentum × extreme):
  - **Conditionally** significant under **HC1** in the pooled sample (`04` / `05`).
  - **Weaker** (e.g. **borderline** at the usual 5% level) when standard errors are **clustered by `price_date`** in `05`
      - Stronger under **ticker** clustering—inference depends on assumed error correlation.
  - **Unstable** over time and across **extreme** definitions in `04` 
      - **OOS** linear **R²** is poor in `05` walk-forward (prefer **median** / **IQR** of fold metrics, not raw mean R² when test-day counts are small).

### Variable definitions (align with `04-hyp..` / `05-hyp..` under `analysis/hypotheses`)

| Symbol | Meaning |
|--------|--------|
| `forward_return_1d` | Next trading day’s **close-to-close** return for the same **ticker**, merged to article rows by `(price_date, ticker)` built with `groupby("ticker") on the daily panel. |
| `momentum_1d` | Prior trading day’s **daily** return (lag-1 `return_1d` within ticker). |
| `neg_extreme` | Binary **1** if article `sentiment_score` ≤ quantile **`Q_BOTTOM`** of scores in the chosen sample **among negative-labeled articles** in `04` / `05` |

Universe and calendar window: **MAG7**, `WINDOW_START` / `WINDOW_END` in `src/msa/utils/vars.py`.

### Specifications

**Baseline** (benchmark for return **level**):

`forward_return_1d ~ momentum_1d`

**Advanced** (modifier spec; same linear predictors as `04` / `05`):

- Features: `momentum_1d`, `neg_extreme`, `momentum_1d * neg_extreme`
- Equation:

`forward_return_1d ~ momentum_1d + neg_extreme + (momentum_1d * neg_extreme)`

**Classification (downside risk):**

- Target: **P(forward_return_1d < 0)** (probability of a **negative** next-day return).
- Same linear predictors (plus constant) via **logistic regression**
    - Interpret with **marginal effects** / probabilities, not only logit coefficients

### Evaluation strategy

**In-sample:**

- **OLS:** coefficients; **HC1** and, where relevant, **cluster-robust** standard errors
- **Logit:** coefficients + **average marginal effects** (e.g. `get_margeff(at="overall")`).

**Out-of-sample (primary validation):**

- **Walk-forward**, **time-ordered** folds, **rolling** (or expanding) training window
    - `neg_extreme` threshold per fold (see `05` and **Time-based validation**)
- **Metrics:** 
    - OOS **R²**, **RMSE**, **Brier** (logit), **directional accuracy**

---

## Modeling Decision

Based on current results:

- Momentum is the only feature with consistent predictive value.
- The sentiment interaction term is NOT sufficiently stable out-of-sample to be included in a production-style forecasting model.

Therefore:

- Baseline model (momentum only) will serve as the primary reference model.
- The interaction model will be treated as an experimental extension and evaluated, but not assumed to improve performance.

Final inclusion of sentiment features depends on:
- Improved OOS performance
- Stability across time periods and definitions