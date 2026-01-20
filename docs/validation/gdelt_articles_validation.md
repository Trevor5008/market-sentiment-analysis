# GDELT Articles Validation Report

**Input:** `data/raw/gdelt_articles.csv`

## Summary
- Rows: **1400**
- Columns: **11**
- Date range: **2026-01-13 03:45:00+00:00 → 2026-01-13 15:00:00+00:00**

## Schema
- Missing required columns: `[]`
- Extra columns: `['query']`

## Missingness (percent)
- seendate: 0.0%
- url: 0.0%
- title: 0.0%
- description: 100.0%
- language: 0.0%
- domain: 0.0%
- sourceCountry: 100.0%
- socialimage: 16.57%
- company: 0.0%
- ticker: 0.0%

## Coverage
### Articles per ticker
- AAPL: 200
- MSFT: 200
- NVDA: 200
- GOOGL: 200
- AMZN: 200
- META: 200
- TSLA: 200

## Sources
### Top domains
- finance.yahoo.com: 100
- forbes.com: 60
- zerohedge.com: 48
- insidermonkey.com: 36
- abcnews.go.com: 32
- webpronews.com: 32
- cnbc.com: 28
- afghanistansun.com: 24
- cincinnatisun.com: 24
- thailandnews.net: 24
- Unique domains: 155

## Notes / Caveats
- GDELT coverage varies by company and time.
- Syndication can create duplicate URLs or near-duplicates.
- Non-English articles may appear depending on query.
