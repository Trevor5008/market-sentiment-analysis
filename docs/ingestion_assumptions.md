# Ingestion Assumptions & Limitations

## Purpose
This document outlines key assumptions and limitations of the data ingestion process.  
The goal is to ensure downstream analysis remains **exploratory**, **non-causal**, and aligned with the intended project scope.

---

## Data Source Assumptions

### News and Price Alignment
- Downstream news–price analysis assumes temporal alignment: same date window for news and prices, with news coverage preceding price moves where causality is considered.
- **Current limitation:** GDELT article dates are skewed to the recent end of the requested window (sort=datedesc + 200-article cap per company in `data_ingestion.py`), so effective news coverage often starts later (e.g. ~1/27) while price data extends to the first trading day in the window (e.g. 12/29). Analyses that map news to price by date therefore have a shorter overlapping range. See `docs/gdelt_vs_prices_date_range_origin.md` for the origin and resolution options.

### Uneven News Coverage
- GDELT does not guarantee equal news coverage across companies, dates, or regions.
- Certain companies may appear more frequently due to external events or media attention.

### Daily Aggregation Assumption
- News articles and price data are aggregated at the **daily** level.
- Intraday timing (e.g., article publish time vs. market open/close) is not modeled.
- This aggregation simplifies alignment but may obscure short-term effects.

### Public News Only
- The ingestion pipeline captures only publicly available news articles.
- Paywalled, subscription-based, or exclusive sources are excluded.

### Duplicate Articles and Stories
- The same news story may be published across multiple outlets.
- Duplicate or near-duplicate articles may remain despite basic deduplication.

### News–Price Timing Uncertainty
- Market price movement may occur before, after, or independently of related news coverage.
- The project does not assume a direct cause-and-effect relationship between news coverage and price movement.

### Query and Keyword Bias
- News articles are retrieved based on predefined queries and company identifiers.
- The choice of query terms may bias which articles are included or excluded.
- Articles that reference a company indirectly or without explicit identifiers may be missed.

### Metadata-Level Text
- News content may consist of headlines and snippets rather than full article bodies.
