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
│   ├── raw/                     # Immutable raw data (append-only)
│        └── archive/            # Date-stamped snapshots (gitignored)             
│   └── processed/               # Deterministically cleaned outputs
├── scripts/
│   ├── ingest_demo.py           # Data ingestion (GDELT articles + OHLCV prices)
│   ├── validate_gdelt.py        # GDELT data validation
│   ├── cleaning_gdelt.py        # GDELT data cleaning
│   ├── ohlcv_validation.py      # OHLCV price data validation
│   ├── ohlcv_cleaning.py        # OHLCV price data cleaning
│   └── run_pipeline.sh          # Full pipeline automation script           
├── notebooks/
│   └── exploratory/
├── docs/
│   ├── validation/
│   ├── ingestion_assumptions.md
│   └── data_snapshot_log.md
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
### Raw Snapshot Naming Convention

To avoid accidental data accumulation and maintain clarity:

**Canonical files** (tracked in git):
- `data/raw/gdelt_articles.csv`
- `data/raw/prices_daily.csv`

**Archived snapshots** (local only, not committed):
- Location: `data/raw/archive/`
- Format: `{dataset}_{YYYY-MM-DD}.csv`
- Examples:
  - `data/raw/archive/gdelt_articles_2026-01-26.csv`
  - `data/raw/archive/prices_daily_2026-01-26.csv`

**Rules:**
1. Only canonical files are committed to `main`
2. Before overwriting a canonical file, move the current version to `archive/` with a date suffix
3. Archive folder is gitignored to prevent accidental commits
4. See `docs/data_snapshot_log.md` for snapshot metadata tracking
## Getting Started

### Environment Setup

**This project requires Anaconda/Conda** - Python 3.11 is recommended.

**Note:** This project is configured for conda environments. Using virtual environments (venv) may cause conflicts with package management and path resolution.

```bash
# Create and activate a conda environment
conda create -n advds python=3.11
conda activate advds

# Install dependencies using pip (pip works fine in conda environments)
pip install -r requirements.txt
```

**Note:** Using `pip` within a conda environment is the recommended approach for this project. Conda environments include pip, and it's safe to use pip to install packages that aren't available via conda.

**Alternative: Hybrid conda-forge + pip approach**
If you prefer to use conda-forge for packages that are available there:
```bash
# Install core packages via conda-forge
conda install -c conda-forge pandas numpy pandas_market_calendars yfinance requests
# Then install remaining packages via pip
pip install -r requirements.txt
```

### Running Scripts

All scripts use project-root-relative paths and can be run from any directory.

**Note for Linux/macOS users:** The pipeline script (`run_pipeline.sh`) needs to be executable. If you encounter a "Permission denied" error, run:
```bash
chmod +x scripts/run_pipeline.sh
```

#### Individual Scripts
```bash
# Ingest data (GDELT articles + OHLCV prices)
python scripts/ingest_demo.py

# Validate GDELT data
python scripts/validate_gdelt.py

# Clean GDELT data
python scripts/cleaning_gdelt.py

# Validate OHLCV price data
python scripts/ohlcv_validation.py

# Clean OHLCV price data
python scripts/ohlcv_cleaning.py
```

#### Full Pipeline (Recommended)
Run the complete validation and cleaning pipeline:

**Linux/macOS:**
```bash
# Make the script executable (first time only)
chmod +x scripts/run_pipeline.sh

# Ensure conda environment is activated
conda activate advds

# Run the pipeline
./scripts/run_pipeline.sh

# Or run with bash explicitly
bash scripts/run_pipeline.sh

# To include data ingestion in the pipeline:
RUN_INGEST=1 ./scripts/run_pipeline.sh
```

**Windows:**
```bash
# Ensure conda environment is activated
conda activate advds

# Using Git Bash or WSL
bash scripts/run_pipeline.sh

# Using WSL (Windows Subsystem for Linux)
# First, make executable:
chmod +x scripts/run_pipeline.sh
# Then run:
./scripts/run_pipeline.sh

# To include data ingestion:
RUN_INGEST=1 bash scripts/run_pipeline.sh
```

**Important:** The pipeline script requires an active conda environment. It will check for `CONDA_PREFIX` and exit with an error if no conda environment is active. The script also validates that required Python packages are installed.

The pipeline script:
- Validates dependencies are installed
- Runs validation scripts (generates reports in `docs/validation/`)
- Runs cleaning scripts (generates cleaned data in `data/processed/`)
- Verifies all outputs are created successfully

## Validation Scripts

Each dataset has a dedicated validation script following a shared structure:
- **`validate_gdelt.py`** - Validates GDELT article data
- **`ohlcv_validation.py`** - Validates OHLCV price data

Validation scripts:
- Audit data quality and coverage
- **Do not mutate** datasets
- Generate markdown reports in `docs/validation/`
- Can be run from any directory (paths are project-root-relative)

## Workflow
This project follows an **Agile sprint-based workflow**:
- Work is tracked using GitHub Issues and Projects
- Each sprint includes planning, daily scrums, review and retrospective
- Tickets define **scope**, **ownership**, and **definitions of done**

## Contributing
Collaboration guidelines and workflow expectations are documented in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Notes
- **This project requires Anaconda/Conda** - virtual environments (venv) are not supported due to package management conflicts
- Generated data artifacts are intentionally excluded from version control
- All results should be reproducible from committed code
- Assumptions and limitations are documented throughout the project
- Scripts use project-root-relative paths and work correctly regardless of current working directory
- The project uses `pandas_market_calendars` for market calendar validation

---

