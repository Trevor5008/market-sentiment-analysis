# Market Sentiment Analysis

## Overview
This capstone project explores the relationship between public sentiment and
short-term market reactions for leading Nasdaq technology companies (often
referred to as the “Magnificent Seven”).

The project is **exploratory in nature** and focuses on identifying patterns,
correlations, and limitations in sentiment-based analysis rather than attempting
to predict future stock prices.

## Table of Contents
- [Project Goals](#project-goals)
- [Scope & Non-Goals](#scope--non-goals)
- [Repository Structure](#repository-structure)
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

- `scripts/` # runnable scripts (data ingestion, utilities)
- `src/` # reusable python modules
- `notebooks/` # exploratory analysis and experimentation
- `data/`
    `raw/` # immutable raw data (not committed/tracked)
    `processed/` # derived datasets (not committed/tracked)
    `validation/` # location for cleaned + validated data
- `docs/` # design notes, assumptions, sprint artifacts

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

