# Source Bias & Domain Quality Analysis

## Overview

This document investigates **source bias and domain quality** in our GDELT news dataset to identify patterns that could distort our sentiment signals. 


## Domain Concentration

### Key Metrics
- **Top 5 domains** account for ~42% of all articles
- **Top 10 domains** account for ~52% of all articles
- Majority of domains contribute only 1 article (long tail of noise)

### Dominant Sources
1. **finance.yahoo.com** — ~18% 
2. **markets.financialcontent.com** — ~9% 
3. **fool.com** — ~8% 
4. **webpronews.com** — ~4%
5. **benzinga.com** — ~3% 

### Findings
- **Single-source dependency risk**: Yahoo Finance alone provides nearly 1 in 5 articles
- **Long tail inefficiency**: Hundreds of domains contribute minimal signal

**Implication:** Our sentiment signal is controlled by a small set of sources. Domain-based filtering or weighting is necessary.

---

## Sentiment Bias by Source/Domain

### Grouped Sentiment Scores (10+ articles)

**Most Positive Domains:**
| Domain | Avg Sentiment |
|--------|--------------|
| fool.com | +0.40 |
| proactiveinvestors.com | +0.27 |
| morningstar.com | +0.25 |
| markets.financialcontent.com | +0.25 |
| finance.yahoo.com | +0.25 |

**Most Negative Domains:**
| Domain | Avg Sentiment |
|--------|--------------|
| telecom.economictimes.indiatimes.com | -0.20 |
| finanznachrichten.de | -0.16 |
| businesstimes.com.sg | -0.14 |
| fortune.com | -0.11 |

**Near-Neutral Sources (Traditional Journalism):**
- forbes.com: +0.03
- timesofindia.indiatimes.com: +0.04
- moneycontrol.com: +0.04

### Findings
- **Traditional journalism is neutral**: Forbes, Fortune, major outlets show balanced coverage
- **Volume ≠ Bias**: Low correlation between article count and sentiment extremity

**Implication:** Positive dataset bias stems from investment/promotional sources.

---

## % Non-Neutral Sentiment per Source

### Distribution
- **Investment/Analysis sites**: 55–70% non-neutral (opinionated content)
- **Aggregators**: 47–58% non-neutral (mix of republished opinions)
- **Major Financial News**: 20–35% non-neutral (fact-focused reporting)

### Findings
- **~45% baseline**: On average, less than half of articles carry discernible sentiment
- **Investment sources most opinionated**: Motley Fool, Benzinga show 56%+ non-neutral
- **Major news outlets prioritize facts**: CNBC, Forbes <35% non-neutral

**Implication:** "Signal" in our dataset is driven by a minority of opinionated articles from promotional sources.

---

## High-Volume Days Analysis

### Definition
- **Threshold**: 75th percentile of daily article counts
- Identifies the busiest ~25% of news days in the dataset

### Which Domains Dominate?

**Top domains on high-volume days (by %):**
1. finance.yahoo.com — ~15%
2. markets.financialcontent.com — ~11%
3. fool.com — ~7%
4. webpronews.com — ~4%
5. benzinga.com — ~3%

**Overlap with overall top 5:** 5/5 (100%)

### Findings
- **Same sources dominate both regular and busy days**: No evidence of niche sources "spiking" during breaking news
- **Structural concentration**: The 42% top-5 dominance is persistent, not event-driven
- **No event-driven diversity**: High article counts don't reflect broader coverage — just the same aggregators republishing more

**Implication:** High-volume days don't provide additional signal diversity; they amplify existing source concentration.

---

## Domain × Ticker Analysis

### Ticker-Specific Concentration
- **finance.yahoo.com**: ~47% of coverage focuses on NVDA
- **fool.com**: ~33% of coverage focuses on NVDA
- Most domains show relatively balanced ticker distribution

### Findings
- **NVDA is over-represented**: Reflects Jan–Feb 2026 AI boom and CES announcements
- **Single-ticker focus sources exist**: Some domains heavily favor specific companies

**Implication:** NVDA sentiment may be over-weighted; ticker-specific filtering may be needed.

---

## Observed Bias Tendencies

### Systematic Biases Identified

**Ticker-Specific Concentration (NVDA Favoritism)**
- **Who**: Yahoo Finance (47% NVDA), Motley Fool (33% NVDA)
- **Mechanism**: NVDA was hottest stock in Jan–Feb 2026
- **Impact**: NVDA sentiment over-represented vs. AMZN/TSLA

### Biases NOT Found
- **No clickbait sensationalism at scale**: High volume ≠ extreme sentiment
- **No event-driven "spike" sources**: Same domains dominate regular and busy days
- **No extreme outliers**: No sources meet all criteria for "extreme" bias

---

## Limitations

1. **Time window**: Analysis covers ~35 days (Jan 6 – Feb 9, 2026); patterns may be period-specific
2. **GDELT sampling**: Paywalled sources (WSJ, Bloomberg) underrepresented; free aggregators overrepresented
3. **Sentiment lexicon**: Word-bank approach may miss contextual nuance
