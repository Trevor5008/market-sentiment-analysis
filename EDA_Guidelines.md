## Purpose
Provide guardrails for exploratory data analysis (EDA) during current sprint

### Structure
```bash
docs/
└── eda/
    └── sprint_2/
        ├── notebooks/
        │   ├── article_coverage.ipynb
        │   ├── price_distribution.ipynb
        │   └── exploratory_notes.ipynb
        ├── scripts/
        │   ├── article_coverage.py
        │   └── price_distribution.py
        ├── article_coverage.md
        ├── price_distribution.md
        └── notes.md
```

### Scope of EDA
- Understand distributions, coverage and basic relationships
- Identify obvious anomalies or gaps
- Build intuition for future modeling and feature engineering
- Validate that cleaned + accumulated data is **usable**

### Out of Scope
- Finalize hypotheses or modeling decisions
- Modify ingestion, validation or accumulation logic 
- Introduce new pipelines/schemas

### Allowable
- Load processed/cleaned datasets (only)
- Compute summary statistics (mean, median, counts, coverage)
- Data Issues should be documented, not fixed directly
- Create visualizations:
    - Histograms
    - Bar charts
    - Line plots
    - Box / Violin plots
- Explore:
    - Article counts over time
    - Price distributions
    - Missingness patterns
    - Basic correlations

### Not Allowed
- Modification of existing raw, processed or accumulated data files
- Writing outputs back to `data/processed` or `data/raw`

### Decision Authority

- EDA findings are **informational only**
- No architectural, pipeline, or schema changes are made based on EDA alone
- Any proposed changes must be:
  - Documented
  - Discussed in a team meeting
  - Approved before implementation

### Rule of Thumb

If your EDA changes shared data, code, or structure — stop and ask.

### Expected Outputs (Examples)

- 1–2 plots with brief captions
- Short markdown notes summarizing observations
- Screenshots pasted into `docs/eda/`

