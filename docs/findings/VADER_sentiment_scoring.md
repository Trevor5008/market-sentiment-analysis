# VADER Sentiment Scoring Analysis
## Assumption:
A general-purpose sentiment model (VADER) will be highly limited in capturing meaningful variation in the tone of financial news headlines across MAG7 companies.
- VADER is applied as a baseline sentiment method, with the expectation that limitations may arise due to its non-financial lexicon.
- EDA is used to asses whether VADER provides sufficient signal for comparing sentiment across companies.

## Finding and Results

**Aggregate Sentiment Behavior:**
- A large portion of headlines recieve an exact neutral sentiment score (compound = 0.0) across all MAG7 tickers.
- As a result, average headline sentiment by company is close to zerom, with very minimal separation between tickers.

### Fraction of neutral headlines by ticker

| Ticker | Neutral headlines (%) |
|--------|------------------------|
| META   | 50.00%                 |
| TSLA   | 46.43%                 |
| MSFT   | 44.57%                 |
| NVDA   | 44.03%                 |
| AAPL   | 42.19%                 |
| GOOGL  | 37.63%                 |
| AMZN   | 37.42%                 |

## Distribution
- The 25th percentile and median sentiment score across all MAG7 tickers are all zero for all MAG7 companies.
- Differences across tickers appear primarily in the upper quartile of the sentiment distribution, reflecting occasional positively scored headlines rather than shifts in central tendency.
- Negative sentiment is present but largely confinsed to the distribution tails.

### Headline sentiment quartiles by ticker (VADER compound)

| Ticker | 25th pct | Median | 75th pct |
|--------|----------|--------|----------|
| AAPL   | 0.0000   | 0.0000 | 0.4019   |
| AMZN   | 0.0000   | 0.0000 | 0.2960   |
| GOOGL  | 0.0000   | 0.0000 | 0.4496   |
| META   | 0.0000   | 0.0000 | 0.2558   |
| MSFT   | 0.0000   | 0.0000 | 0.3291   |
| NVDA   | 0.0000   | 0.0000 | 0.2144   |
| TSLA   | 0.0000   | 0.0000 | 0.2242   |

## Interpretation
- VADER sentiment scores are **heavily zero-inflated** when applied to financial headlines, indicating limited sensitivity in VADERS finance-specific language.
- Central tendency measures (mean, median) provide little discriminatory power across companies.
- Observed differences in sentiment are driven by sparse positive signals rather than consistent sentiment patterns.
- Overall, VADER is **not** a reliable standalone method for capturing headline sentiment in this financial context.

## Potential Follow-up Questions
- Would finance-specific models or non-sentiment-based approaches provide more informative signals?
- Does news volume, rather than sentiment polarity, better explain differences in price behavior?
- Do price movements differ between days with a higher volume of news coverage?
