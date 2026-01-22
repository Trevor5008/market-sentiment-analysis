# GDELT Articles Validation Report

**Input:** `data/raw/gdelt_articles.csv`

## Summary
- Rows: **1400**
- Columns: **11**
- Date range: **2026-01-13 15:45:00+00:00 → 2026-01-14 02:00:00+00:00**

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
- socialimage: 22.86%
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
- markets.financialcontent.com: 128
- finance.yahoo.com: 116
- fool.com: 68
- finance.sina.com.cn: 60
- 163.com: 60
- webpronews.com: 40
- yicai.com: 36
- benzinga.com: 36
- finance.ifeng.com: 32
- finance.eastmoney.com: 28
- Unique domains: 140

## Notes / Caveats
- GDELT coverage varies by company and time.
- Syndication can create duplicate URLs or near-duplicates.
- Non-English articles may appear depending on query.
