# Ingestion Assumptions & Limitations

## Purpose
This document outlines key assumptions and limitations of the data ingestion process.  
The goal is to ensure downstream analysis remains **exploratory**, **non-causal**, and aligned with the intended project scope.

---

## Data Source Assumptions

### Uneven News Coverage
- GDELT does not guarantee equal news coverage across companies, dates, or regions.
- Certain companies may appear more frequently due to external events or media attention.

---

### Public News Only
- The ingestion pipeline captures only publicly available news articles.
- Paywalled, subscription-based, or exclusive sources are excluded.

---

### Duplicate Articles and Stories
- The same news story may be published across multiple outlets.
- Duplicate or near-duplicate articles may remain despite basic deduplication.

---

### News–Price Timing Uncertainty
- Market price movement may occur before, after, or independently of related news coverage.
- The project does not assume a direct cause-and-effect relationship between news coverage and price movement.

---

### Metadata-Level Text
- News content may consist of headlines and snippets rather than full article bodies.
