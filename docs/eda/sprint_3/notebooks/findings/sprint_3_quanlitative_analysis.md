# Sprint 3: Qualitative Analysis of Sentiment Signal Quality

## Scope & Methods

This analysis covers **3,724 GDELT news articles** spanning **669 unique domains**, collected between **January 6 – February 9, 2026** (~35 calendar days). Seven mega-cap tickers are represented: AAPL, AMZN, GOOGL, META, MSFT, NVDA, and TSLA. All sentiment scores were generated using our custom financial lexicon (Sprint 2). Articles were joined to next-trading-day OHLCV prices via `build_gdelt_ohlcv_join.py`.

### Driving Questions
- Is the aggregate sentiment signal trustworthy, or is it controlled by a small set of sources?
- When extreme sentiment days occur, are they driven by real events or source concentration?
- How does the news-to-price mapping actually behave?

### Source Notebooks
| Notebook | Section |
|----------|---------|
| `source_level_aggregation.ipynb` | Source Problem |
| `source_domain_analysis.ipynb` | Source Problem |
| `Sentiment_Signal_Disagreement_Analysis.ipynb` | Disagreement Structure |
| `price_news_analysis.ipynb` | Price–News Alignment |

### Metric Definitions
- **Net polarity**: positive article count minus negative article count for a given (ticker, day).
- **Magnitude day**: a day with high absolute net polarity, driven primarily by article volume.
- **Directional purity day**: a day where polarity ratio (positive / total non-neutral) is extreme (near 0 or 1), regardless of volume.
- **Dispersion day**: a day with high sentiment spread (large standard deviation across article scores for a ticker).
- **Consensus day**: a rare day when both polarity ratio *and* magnitude intensity co-occur — potential genuine narrative alignment.
- **Signal rate**: 1 − neutral rate; the fraction of articles where the lexicon fires (score ≠ 0).

---

## 1. The Source Problem

**Sources:** `source_level_aggregation.ipynb`, `source_domain_analysis.ipynb`; findings documented in `source_bias_findings.md`

The sentiment signal in our dataset is structurally dominated by a handful of sources:

| Rank | Domain | Articles | Share |
|------|--------|----------|-------|
| 1 | finance.yahoo.com | 680 | 18.3% |
| 2 | markets.financialcontent.com | 323 | 8.7% |
| 3 | fool.com | 317 | 8.5% |
| 4 | webpronews.com | 143 | 3.8% |
| 5 | benzinga.com | 108 | 2.9% |

The **top 5 domains account for 42.2%** of all articles; the **top 10 account for 51.6%**. Meanwhile, **414 of 669 domains contributed only a single article** — a long tail of noise. Only **42 domains have 10+ articles**, making most sources too thin to characterize individually.

This is not just a volume problem — it is a **bias problem**. Investment-oriented sources carry systematically different tone:

| Source Type | Avg Sentiment | % Non-Neutral |
|-------------|---------------|---------------|
| fool.com (investment) | +0.40 | 56.2% |
| finance.yahoo.com | +0.25 | — |
| forbes.com (traditional journalism) | +0.03 | <35% |
| fortune.com | −0.11 | — |
| telecom.economictimes.indiatimes.com | −0.20 | — |

More broadly:
- **Investment/analysis sites**: 55–70% non-neutral (opinionated content)
- **Aggregators**: 47–58% non-neutral
- **Major financial news outlets**: 20–35% non-neutral (fact-focused)

On average, fewer than **~45% of articles carry discernible sentiment at all** — meaning "signal" in our dataset is disproportionately driven by a minority of opinionated articles from promotional outlets.

### Ticker Concentration Within Sources

The source bias compounds at the ticker level. Yahoo Finance directs **~47% of its coverage to NVDA**; Motley Fool directs **~33% to NVDA**. This reflects the Jan–Feb 2026 AI boom and CES announcements, but it means any aggregate sentiment metric is partly just measuring "how much NVDA content did we ingest today."

### High-Volume Days

On high-volume days (top 25% by article count), the **same top 5 domains dominate** (100% overlap with overall top 5). There is no event-driven diversity: busy days don't reflect broader source coverage — they just amplify existing concentration.

### Biases Not Found

- No clickbait sensationalism at scale (high volume ≠ extreme sentiment)
- No event-driven "spike" sources distinct from regular top domains
- No sources meeting all criteria for extreme outlier bias

---

## 2. The Disagreement Structure

**Source:** `Sentiment_Signal_Disagreement_Analysis.ipynb`

Across all seven tickers, **sentiment ranges are comparable** (~1.92 for most tickers; AMZN slightly wider at 1.96) with per-ticker standard deviations between **0.44 (MSFT) and 0.52 (NVDA)**. This means we can use the same thresholds across tickers without needing per-ticker normalization.

Analysis of daily net polarity (positive − negative article counts) revealed that "extreme" sentiment days are **not monolithic**. We identified three structurally different types:

1. **Magnitude days** — high absolute net polarity driven by raw article volume. *Example:* NVDA on Jan 11 had 44 positive articles, 0 negative (net polarity = 44), and GOOGL on Feb 9 had 68 positive, 7 negative (net polarity = 61). These look extreme but are largely a function of how many articles were published.

2. **Directional purity days** — strong bias regardless of volume, measured by polarity ratio. *Example:* AAPL on Feb 3 had 13 positive articles and 0 negative — perfect purity (ratio = 1.0), but on low volume.

3. **Dispersion days** — high sentiment spread/disagreement within a single ticker-day. *Example:* META on Feb 6 had 57 positive but also 19 negative articles — the highest negative count for any ticker-day — indicating genuine disagreement rather than one-sided coverage.

These types **rarely overlap**. A day with strong directional purity is not necessarily a day with high volume. The one exception is rare **"consensus days"** when ratio and intensity co-occur, which may represent genuine market narrative alignment.

The correlation between log(volume) and log(net polarity) is often **>0.9**, confirming that magnitude is volume-driven. Conversely, higher volume tends to produce **lower directional purity** — more articles means more dissent.

### Key Limitation

Isolated daily outliers are interesting but **do not establish persistent narrative shifts**. A single day of 68 positive articles for NVDA (Feb 9) does not tell us whether positive sentiment was sustained across the surrounding days. Single days are structurally insufficient for inference.

---

## 3. The Price–News Alignment

**Source:** `price_news_analysis.ipynb`

### Join Logic

News published on day *t* is mapped to prices on the **next NYSE trading day** (*t*+1). Weekend and holiday articles roll forward to Monday. This design captures the "news published → market reacts next open" hypothesis.

### Join Validation

- The join was designed so that price_date is strictly after `article_date`; validation is pending re-execution of the notebook.
- Each `(price_date, ticker)` pair has exactly **one set of `next_*` values** — no conflicting prices.
- Cross-check against source OHLCV (`prices_daily_accumulated.csv`): **all join prices match** the original price data.
- Calendar-day gaps are as expected: 1 day for weekday articles, 2–3 days for Friday/weekend articles.

### Coverage

Not all trading days have matched news. The alternative join (trading-day-indexed left join) shows that many `(trading_date, ticker)` pairs have **zero matched articles** — particularly on low-activity tickers and mid-week days outside major news cycles.

### Weekly Aggregation

Mean and median sentiment were computed per ticker per week (using Monday-only filtering, weeks numbered from Jan 12, 2026). **Week 2 is missing** due to the MLK holiday on Jan 19.

The weekly pivot tables show ticker-level sentiment trends, but at this stage the relationship between weekly sentiment and next-week returns remains **exploratory with no confirmed signal**. The planned analyses — sentiment vs. price direction, volatility, sentiment buckets, news volume effects, and disagreement-return relationships — are **not yet complete**.

---

## 4. Limitations

1. **Narrow time window**: ~35 calendar days (Jan 6 – Feb 9, 2026). Patterns may be period-specific and cannot be assumed to generalize.
2. **GDELT sampling bias**: Paywalled sources (WSJ, Bloomberg, FT) are underrepresented; free aggregators are overrepresented. Our "market sentiment" is really "free-web sentiment."
3. **Lexicon coverage**: The custom financial lexicon (Sprint 2) is better than VADER but still produces **~66% zero-scored articles** (`sentiment_score = 0`). Volume-based signals (article counts, net polarity) may carry more information than polarity scores.
4. **No causality claims**: The news→price join captures temporal ordering, not causal mechanism. Correlation (if found) does not imply sentiment *causes* price movement.
5. **Single-ticker generalization risk**: NVDA results are contaminated by over-representation in Yahoo Finance (47%) and Fool (33%). Cross-ticker comparisons involving NVDA should be interpreted cautiously.

---

## 5. Sprint 4 Decisions

Based on these findings, the following changes will be implemented in Sprint 4:

| Decision | Rationale |
|----------|-----------|
| **Use median aggregation** as the primary sentiment metric (not mean) | Mean is distorted by source concentration and zero-inflated scores |
| **Implement source weighting** (inverse-frequency or credibility-based) | Top 5 sources control 42% of volume and carry systematic positive bias |
| **Switch to weekly rolling windows** for all downstream analysis | Daily outliers are too noisy; single days don't establish narrative shifts |
| **Flag/separate NVDA** in all cross-ticker comparisons | Over-representation (47% of Yahoo, 33% of Fool) contaminates aggregate results |
| **Run source-exclusion robustness checks** before claiming any price–sentiment relationship | No signal can be trusted until we verify it survives removal of top sources |
| **Complete the planned price-direction and volatility analyses** | Weekly sentiment vs. returns, sentiment buckets, and disagreement-return tests are still pending |

# Flag: 
| `source_domain_analysis.ipynb` loaded **3,724 rows** but `Sentiment_Signal_Disagreement_Analysis.ipynb` loaded only **1,309 rows** - both from `gdelt_ohclv_join.csv`. Probably run from different times, or one applies a filter. 