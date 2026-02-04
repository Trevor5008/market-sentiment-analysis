# Weekend effect analysis

## Purpose
This document records the working assumption, context, and **findings** for the weekend-effect analysis (Friday vs Monday price behavior) in this project. The assumption is a hypothesis to be tested or validated with the MAG7 data; the results below come from `docs/eda/sprint_2/notebooks/weekend_effect_analysis.ipynb`.

---

## Weekend effect (Friday / Monday)

**Assumption:** The "weekend effect" (prices tending to rise on Friday and drop on Monday) still applies to the **MAG7 subset** of tickers we are investigating (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA).

- The broader literature often finds a small negative Monday return or positive Friday return in equity indices; the effect may vary by market, period, and cap segment.
- We treat MAG7 large-cap tech as a subset where this pattern may still hold, and use EDA (e.g. Friday vs Monday returns in `weekend_effect_analysis.ipynb`) to check whether it is visible in our sample.
- With limited history, results can be noisy; absence of a clear effect in our sample does not refute the assumption for MAG7 in general, only for the observed window.

---

## Findings and results

### Aggregate by weekday (close-to-close return)

Close-to-close return includes overnight/weekend; Monday’s return is Fri close → Mon close.

| Weekday | Mean return (close-to-close) | Count |
|---------|------------------------------|-------|
| Mon     | 0.3083%                      | 28    |
| Tue     | -0.7980%                     | 42    |
| Wed     | -0.1726%                     | 35    |
| Thu     | 0.5005%                      | 28    |
| Fri     | 0.0780%                      | 35    |

- **Friday** mean return (close-to-close): **0.0780%**
- **Monday** mean return (close-to-close): **0.3083%**
- **Difference (Fri − Mon): −0.2302%**

In this sample, Monday’s mean return is *higher* than Friday’s on average, so the classic “weekend effect” (lower Monday return) is **not** visible in the aggregate MAG7 close-to-close returns for the observed window.

### Same-day return (open → close)

Within-session move only (no overnight/weekend).

| Weekday | Mean same-day return | Count |
|---------|----------------------|-------|
| Mon     | 0.3629%              | 28    |
| Tue     | -0.6067%             | 42    |
| Wed     | -0.2311%             | 35    |
| Thu     | -0.1848%             | 28    |
| Fri     | -0.1617%             | 35    |

- **Friday** mean same-day return: **−0.1617%**
- **Monday** mean same-day return: **+0.3629%**

Same-day returns also do **not** support “Friday rise, Monday drop”: on average Fridays are slightly negative and Mondays positive in this sample.

### By ticker (Friday vs Monday, close-to-close)

| Ticker | Friday | Monday | Fri − Mon |
|--------|--------|--------|-----------|
| AAPL   | -0.18% | 1.50%  | -1.67%    |
| AMZN   | 0.00%  | 0.94%  | -0.93%    |
| GOOGL  | -0.01% | 1.19%  | -1.20%    |
| META   | -0.34% | 0.06%  | -0.40%    |
| MSFT   | 0.26%  | -0.28% | 0.54%     |
| NVDA   | 0.31%  | -0.97% | 1.28%     |
| TSLA   | 0.51%  | -0.27% | 0.78%     |

- **AAPL, AMZN, GOOGL, META:** Monday mean return &gt; Friday (negative Fri − Mon); no weekend effect in this direction.
- **MSFT, NVDA, TSLA:** Friday mean return &gt; Monday (positive Fri − Mon); consistent with “Friday stronger than Monday” for these three tickers only.

### Interpretation

- **Aggregate:** For the observed MAG7 window, mean Monday close-to-close return is *higher* than Friday’s; the classic weekend effect (Friday up, Monday down) is not present in the aggregate.
- **Same-day:** Fridays are slightly negative and Mondays positive on average; again opposite to the assumed pattern.
- **By ticker:** Mixed. Three names (MSFT, NVDA, TSLA) show Friday &gt; Monday; four (AAPL, AMZN, GOOGL, META) show Monday &gt; Friday.
- **Caveat:** Short history and small counts per weekday; results are suggestive only. Re-run the notebook after new ingestions to refresh these numbers.

### Follow-up Questions:
- "Is aggregated weekend news sentiment positively correlated with Monday close-close returns across MAG7?"
- "Does high headline volume + mild positive sentiment matter more than low volume w/ bullish (strong) positivity?"

#### Next Steps
- Explicitly set start date for gdelt data ingestion (currently cutting off at 1/27 due to 200 articles cap)
- Price data is not yet capable of mapping directly to news coverage due to the different ranges

Once resolved...
- Lexicon-based sentiment (VADER, TextBlob, AFINN?) -> Polarity score
- % positive headlines (over the weekend)
- Net sentiment
