# Robustness Summary

## Objective

Validate that any observed sentiment–return relationship survives removing or re-weighting dominant
sources. Prior to this analysis, we observed that a small number of domains controlled a
disproportionate share of article volume and carried systematic positive bias, raising the concern
that any signal we observed was an artifact of source concentration rather than genuine
sentiment-price dynamics.

---

## Key Question

**Does the sentiment–return relationship change meaningfully when dominant sources are removed?**

---

## Baseline (Join table)

Before any exclusions, the full 2-year FinBERT-scored dataset shows:

| Metric | Value |
|--------|-------|
| Total MAG7 articles | 89,545 |
| Sentiment present (`\|score\| > 0.05`) | 47.1% |
| Days with any MAG7 sentiment | 102 |
| Days with 5+ MAG7 tickers | 56 |
| Mean tickers/day | 4.73 |
| Overall sentiment–return correlation | ~0.001 |

**Domain concentration is significantly healthier than Sprint 3:**
- Top 5 domains account for 14.6% of articles, down from ~42% in Sprint 3
- Top 10 domains account for 21.4%, down from ~52%
- 1,898 single-article domains out of 5,126 total, a long tail, but less concentrated at the top

**Sentiment bias has shifted:**
- Sprint 3 showed systematic positive bias
- On the 2-year dataset, most domains sit near neutral or slightly negative
- This reflects broader market conditions captured over 2 years vs. the Jan–Feb 2026 AI boom window Sprint 3 used

---

## Cumulative Domain Exclusion

Top domains were dropped cumulatively (top 1, 3, 5, 10) and key metrics recomputed.

| Exclusion | Articles | Days (5+ tickers) | Mean tickers/day | Overall corr |
|-----------|----------|-------------------|------------------|--------------|
| Baseline (all sources) | 12,523 | 56 | 4.73 | 0.0012 |
| Drop top 1 (fool.com) | 11,364 | 55 | 4.76 | 0.0022 |
| Drop top 3 (+ yahoo.com) | 10,997 | 55 | 4.76 | 0.0061 |
| Drop top 5 | 9,025 | 55 | 4.71 | 0.0182 |
| Drop top 10 | 7,144 | 55 | 4.68 | 0.0001 |

**Findings:**
- Dropping the top 10 domains removes 43% of articles yet coverage barely moves (56 → 55 days with 5+ tickers)
- Overall correlation remains near-zero at every exclusion level ranging from 0.0001 to 0.0182
- No threshold produces a meaningful or directionally consistent shift
- Coverage is not being propped up by dominant sources, it is structurally distributed across the dataset

---

## Single Domain Drops (Top 5 Individually)

Each of the top 5 domains was removed one at a time to check if any single source is uniquely
responsible for the signal.

**Findings:**
- No individual domain drop caused a meaningful shift in overall correlation or coverage
- Per-ticker correlations remain noisy and inconsistent regardless of which domain is excluded
- This rules out any single source as a confound

---

## NVDA Isolation

NVDA has historically been over-represented in dominant sources. On the current 2-year dataset:

| Domain | NVDA share |
|--------|------------|
| yahoo.com | 51.2% |
| finance.yahoo.com | 41.9% |
| fool.com | 40.0% |
| marketscreener.com | 35.9% |
| benzinga.com | 13.8% |

NVDA accounts for **23.3% of all MAG7 articles**, the most covered ticker by a significant margin
(next closest: AMZN at 16.1%).

**New finding vs. Sprint 3:** Concentration is more spread across tickers on the 2-year dataset.
`benzinga.com` directs 55% of its coverage to TSLA, more concentrated than any NVDA figure.
`themarketsdaily.com` directs 35% to META. This reflects different market cycles across the 2-year
window rather than a single period of NVDA dominance.

**Isolation results:**

| | Overall corr | Days (5+ tickers) |
|-|-------------|-------------------|
| With NVDA | 0.0012 | 56 |
| Without NVDA | 0.0186 | 53 |

- Correlation remains effectively zero in both configurations
- Coverage drops only marginally (56 → 53 days), NVDA is not propping up cross-sectional coverage
- NVDA concentration is real but is **not a statistical confound** on this dataset

---

## Source Weighting Assessment

Source weighting was originally planned as a follow-up to this analysis under the assumption that
dominant sources were inflating the signal. Based on the results above, **source weighting is not
necessary at this stage** for the following reasons:

- The signal is uniformly near-zero regardless of which sources are included or removed
- No source or combination of sources is artificially inflating the correlation
- Weighting sources would change article contribution ratios but would not resolve a near-zero
  correlation. It would still be near-zero
- Time is better directed toward structural analysis (lag analysis, regime stability) to determine
  whether the relationship exists at a different time horizon or under specific market conditions

---

## Overall Conclusion

> **Source bias is not an explanation for weak signal. The signal is genuinely weak.**

- Domain concentration has improved substantially on the 2-year dataset
- No individual source or ticker is distorting the aggregate sentiment–return relationship
- The near-zero correlation is stable, consistent, and survives every exclusion configuration tested

---

## Next Steps

- Re-direct focus to structural analysis: correlation mapping, lag analysis, and regime stability checks
- Determine whether a meaningful sentiment–return relationship exists at longer time horizons (2–5 day lag)
- Define a concrete modeling target based on structural findings
