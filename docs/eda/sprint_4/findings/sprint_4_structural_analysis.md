# Sprint 4: FinBERT Re-scoring, Structural Hypothesis Testing & Momentum Signal Analysis

## Scope & Methods

This sprint covers three interconnected workstreams:

1. **FinBERT v2 Re-scoring** — replace the Sprint 2/3 custom lexicon scores with ProsusAI/finbert sentiment labels across the full dataset.
2. **Structural Hypothesis Testing** — test four a-priori sentiment-return hypotheses (H1–H4) on the joined dataset.
3. **Momentum Signal Engineering** — build and evaluate ticker-level momentum features as an alternative to sentiment.

All analysis is performed on **1,168 clean ticker-day records** (after joining GDELT articles to OHLCV prices) plus re-scored article-level data covering **12,523 articles**.

### Source Notebooks

| Notebook | Workstream |
|----------|------------|
| `analysis/structural/re_score_finbert_v2.ipynb` | FinBERT v2 re-scoring |
| `analysis/structural/correlation_mapping.ipynb` | Correlation mapping (v1 scores) |
| `analysis/structural/correlation_mapping_finbert.ipynb` | Correlation mapping (FinBERT v2 scores) |
| `analysis/structural/hypothesis_testing_report.ipynb` | Structural hypothesis tests (H1–H4) |
| `analysis/correlation_mapping_2.ipynb` | Extended correlation analysis |

### Data Artifacts

| File | Description |
|------|-------------|
| `data/processed/gdelt_ohlcv_join_finbert.parquet` | Full join dataset re-scored with FinBERT v2 |
| `.gitignore` | Updated to track the finbert parquet snapshot |

---

## 1. FinBERT v2 Re-scoring

**Source:** `analysis/structural/re_score_finbert_v2.ipynb`

The Sprint 2/3 custom lexicon produced ~66% zero-scored articles (high sparsity), which limited signal quality in all downstream analyses. In Sprint 4 we replaced those scores with **ProsusAI/finbert** (a BERT model fine-tuned on financial text), which assigns a three-class label (positive / negative / neutral) and a continuous confidence score to every article.

### Re-scoring Results

- **12,523 articles** re-scored
- Output saved to `data/processed/gdelt_ohlcv_join_finbert.parquet`
- Sparsity (neutral rate) remains a structural pain point even with FinBERT — the model classifies a significant fraction of articles as neutral, which limits effective article-level signal

### Correlation with Returns

After re-scoring, Spearman correlation between FinBERT-derived sentiment aggregates and next-day returns was computed across tickers and lag windows. The relationship remains **weak and unstable**:

- Correlations are low in magnitude across all aggregation methods (mean, median, net polarity)
- No consistent lag (same-day, 1-day, 2-day) showed a stable positive pattern
- Results are consistent with the Sprint 3 finding that sentiment alone does not reliably predict short-term price movement

### Key Takeaway on Sparsity

Sparsity in the lexicon-scored data was confirmed as a major pain point. Switching to FinBERT improves label coverage but does not resolve the fundamental weakness of news sentiment as a return predictor. Domain concentration (a small set of sources accounting for most articles) continues to inflate noise.

---

## 2. Structural Hypothesis Tests (H1–H4)

**Source:** `analysis/structural/hypothesis_testing_report.ipynb`

Four pre-registered hypotheses were tested using Spearman rank correlation and permutation-based p-values on the ticker-day level dataset (N = 1,168 after cleaning).

| Hypothesis | Description | Result |
|------------|-------------|--------|
| **H1** | Daily net sentiment predicts next-day return | ❌ Rejected (p > 0.05) |
| **H2** | Sentiment dispersion predicts next-day volatility | ❌ Rejected (p > 0.05) |
| **H3** | High-volume sentiment days have stronger return signal | ❌ Rejected (p > 0.05) |
| **H4** | FinBERT v2 sentiment improves over lexicon-based signal | ❌ Rejected (p > 0.05) |

All four sentiment-based hypotheses were rejected. This is a strong null result: **sentiment derived from GDELT news (whether lexicon or FinBERT-based) does not produce a statistically reliable short-term return signal** in this dataset and time window.

### Domain Concentration Update

The 2-year window analysis shows domain concentration improved from **42% (top 5 sources)** in Sprint 3 to **14.6%** in the broader dataset — suggesting the Sprint 3 concentration was partly driven by the narrow Jan–Feb 2026 window. However, even with lower concentration the sentiment signal remains insignificant.

---

## 3. Momentum Signal Engineering

**Source:** `analysis/correlation_mapping_2.ipynb`, `a18964c` commit

Given the null result on sentiment hypotheses, Sprint 4 pivots to **price-based momentum features** as the primary candidate signal. Four features were engineered at the ticker-day level:

| Feature | Description |
|---------|-------------|
| `mom_1d` | 1-day lagged return (price momentum) |
| `volume_z` | Volume z-score relative to ticker's rolling mean |
| `peer_mom_1d` | Equal-weighted mean of other 6 MAG-7 tickers' 1-day return |
| `vol_price_interaction` | `volume_z × mom_1d` interaction term |

### Signal Evaluation (Spearman ρ, N = 1,168)

| Signal | ρ | p-value | Significant |
|--------|---|---------|-------------|
| **mom_1d** | +0.169 | < 0.0001 | ✅ Yes |
| **volume_z** | +0.057 | 0.0181 | ✅ Yes |
| **peer_mom_1d** | −0.034 | — | ❌ No |
| **vol_price_interaction** | +0.029 | — | ❌ No |

**`mom_1d` is the dominant signal.** The 1-day price momentum predicts next-day return with a statistically significant positive correlation. `volume_z` is also significant but weak. Cross-asset peer momentum and the volume-price interaction add no incremental predictive value.

### Volume Regime Robustness

The momentum signal was tested for robustness across volume regimes:

```
High volume days (volume_z > 0.5):
  n = 364
  mom_1d ρ = +0.189,  p < 0.001  ✓

Low volume days (volume_z < -0.5):
  n = 504
  mom_1d ρ = +0.165,  p < 0.001  ✓

→ Momentum signal is robust across both regimes
→ Volume filtering provides no advantage
→ Same model applies to all days
```

---

## 4. .gitignore & Data Tracking Changes

- `data/processed/gdelt_ohlcv_join_finbert.parquet` is now tracked in `.gitignore` as a canonical snapshot (mirrors the existing `data/raw/` tracking policy)
- All other generated files remain untracked local artifacts

---

## 5. Limitations

1. **Short time window**: The ticker-day dataset covers a limited period. The momentum signal may be period-specific.
2. **MAG-7 only**: Results apply to 7 highly liquid mega-cap stocks. Generalization to smaller-cap or less liquid tickers is not tested.
3. **No causal claims**: Spearman correlations establish association, not causation.
4. **Sentiment null may be data-limited**: The GDELT data limitations (free-web bias, high neutral rate, source concentration) may be suppressing a real sentiment signal rather than confirming its absence.

---

## 6. Sprint 5 Decisions

| Decision | Rationale |
|----------|-----------|
| **Use `mom_1d` + `volume_z` as primary features** | Only signals with statistically significant correlations |
| **Build logistic regression classifier** | Predict next-day return direction (up/down); binary target simplifies the problem |
| **Do not include sentiment features in Sprint 5 model** | All four sentiment hypotheses rejected; no evidence of incremental value |
| **Evaluate peer momentum in a larger dataset** | `peer_mom_1d` was non-significant here but theoretically motivated; defer to Sprint 6 |
