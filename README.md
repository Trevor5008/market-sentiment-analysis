# Market Sentiment Analysis

## Overview
This capstone project explores the relationship between public sentiment and
short-term market reactions for leading Nasdaq technology companies (often
referred to as the “Magnificent Seven”).

The project is **exploratory in nature** and focuses on identifying patterns,
correlations, and limitations in sentiment-based analysis rather than attempting
to predict future stock prices.

This repository is structured to support:
- deterministic data ingestion
- explicit data validation and cleaning steps
- repeatable exploratory analysis
- team-based development with clear process boundaries

## Table of Contents
- [Project Goals](#project-goals)
- [Scope & Non-Goals](#scope--non-goals)
- [Repository Structure](#repository-structure)
- [Data Lifecycle](#data-lifecycle)
- [Getting Started](#getting-started)
- [Workflow](#workflow)
- [Contributing](#contributing)
- [Notes](#notes)

---

## Project Goals
- Build reproducible data ingestion pipelines
- Collect and preprocess public sentiment data from news and/or social sources
- Align sentiment signals with short-term market behavior
- Analyze patterns and limitations across companies and time windows
- Practice Agile workflows in a team-based data science project

---

## Scope & Non-Goals
**In scope**
- Exploratory sentiment analysis
- Publicly available data sources
- Daily-level aggregation and comparison
- Transparent assumptions and limitations

**Out of scope**
- Price prediction or trading strategies
- Real-time systems or production deployment
- Claims of causality or financial advice

---

## Repository Structure
```text
├── data/
│   ├── raw/                    # Immutable raw data (append-only)
│   └── processed/              # Deterministically cleaned outputs
├── scripts/
│   ├── validate_gdelt.py
│   ├── ohlcv_validation.py
│   └── cleaning_gdelt.py
│    └── ingest_demo.py           
├── notebooks/
│   └── exploratory/
├── docs/
│   ├── validation/
│   ├── assumptions.md
│   ├── sprint_minutes/
│   └── retrospectives/
├── README.md
└── CONTRIBUTING.md
```
## Data Lifecycle
1. Raw Data (Immutable)
- Stored under `data/raw`
- Treated as **append-only**
- Never manually edited
- May be re-fetched, but prior snapshots are preserved
2. Validation (Non-Mutating)
- Validation scripts:
    - **Inspect** raw data
    - **Report** gaps, duplicates, anomalies
    - **Do not** modify raw files
- Outputs:
    - console summaries
    - optional markdown/csv reports under `docs/validation/`
3. Cleaning (Deterministic Mutation)
- Cleaning scripts:
    - operate only on **validated raw data**
    - apply deterministic transformations:
        - deduplication
        - language filtering
        - relevance filtering
        - column pruning
        - missing value handling
    - write outputs to `data/processed/`
- *Cleaned data may be overwritten, as it can always be regenerated from raw inputs*
- *Cleaning logic is implemented in standalone scripts under `scripts/clean_*.py` and does not perform ingestion or validation.*
4. Analysis (Exploratory Only)
  - Conducted in notebooks under `notebooks/`
  - Uses cleaned datasets only
  - Focuses on visualization and pattern exploration
  - No modeling or inference claims at this stage
 
### Accumulation Strategy
- Each ingestion run pulls data "up to today"
- Raw outputs are date-stamped
- Cleaned datasets are regenerated as needed
- *Incremental append and automation will be revisited **after validation and cleaning logic is finalized***
---

## Getting Started
1. Create and activate a Python virtual environment

### Environment Setup
It is recommended to use a Python virtual environment to isolate dependencies

**Python 3.10+ is recommended**

```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

2. Install dependencies from `requirements.txt`

```bash
pip install -r requirements.txt
```

**If pip is missing from venv, run the following...

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

3. Run ingestion scripts under `scripts/` to reproduce datasets

Example:
```bash
python scripts/ingest_demo.py
```

## Validation Scripts

Each dataset has a dedicated script following a shared structure
Validation scripts audit data quality and coverage only - they do not mutate
datasets

Outputs written to `docs/validation`

## Workflow
This project follows an **Agile sprint-based workflow**:
- Work is tracked using GitHub Issues and Projects
- Each sprint includes planning, daily scrums, review and retrospective
- Tickets define **scope**, **ownership**, and **definitions of done**

## Contributing
Collaboration guidelines and workflow expectations are documented in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Notes
- Generated data artifacts are intentionally excluded from version control
- All results should be reproducible from committed code
- Assumptions and limitations are documented throughout the project

---

