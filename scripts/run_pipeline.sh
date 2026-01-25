#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---- Require conda env to be active (since you're using conda) ----
if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "ERROR: No conda environment active."
  echo "Activate your env first, e.g.:"
  echo "  conda activate <env-name>"
  exit 1
fi

PYTHON_BIN="$(command -v python)"

echo "============================================================"
echo "Using python: $PYTHON_BIN"
python -V
echo "Conda prefix: $CONDA_PREFIX"
echo "Project root: $PROJECT_ROOT"
echo "============================================================"

# ---- Preflight dependency checks (fail fast) ----
echo "Preflight: checking required Python packages..."
python - <<'EOF'
import sys
required = ["pandas", "numpy", "pandas_market_calendars"]
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except Exception:
        missing.append(pkg)

if missing:
    print("Missing packages:", ", ".join(missing))
    print("\nFix (conda-forge recommended):")
    print("  conda install -c conda-forge " + " ".join(missing))
    print("\nOr via pip:")
    print("  pip install " + " ".join(missing))
    sys.exit(1)

print("OK: dependencies available.")
EOF

# ---- Optional: Ingestion step (enable if desired) ----
RUN_INGEST="${RUN_INGEST:-0}"
if [[ "$RUN_INGEST" == "1" ]]; then
  echo "RUNNING ingest_demo.py..."
  python "$PROJECT_ROOT/scripts/ingest_demo.py"
else
  echo "Skipping ingestion (set RUN_INGEST=1 to enable)."
fi

# ---- Verify raw outputs exist ----
if [[ ! -f "$PROJECT_ROOT/data/raw/gdelt_articles.csv" ]]; then
  echo "ERROR: data/raw/gdelt_articles.csv was not found"
  exit 1
fi
if [[ ! -f "$PROJECT_ROOT/data/raw/prices_daily.csv" ]]; then
  echo "ERROR: data/raw/prices_daily.csv was not found"
  exit 1
fi

# ---- GDELT validate + clean ----
echo
echo "==================== GDELT PIPELINE ===================="
echo "RUNNING validate_gdelt.py..."
python "$PROJECT_ROOT/scripts/validate_gdelt.py"

if [[ ! -f "$PROJECT_ROOT/docs/validation/gdelt_articles_validation.md" ]]; then
  echo "ERROR: docs/validation/gdelt_articles_validation.md was not created"
  exit 1
fi

echo "RUNNING cleaning_gdelt.py..."
python "$PROJECT_ROOT/scripts/cleaning_gdelt.py"

if [[ ! -f "$PROJECT_ROOT/data/processed/gdelt_articles_clean.csv" ]]; then
  echo "ERROR: data/processed/gdelt_articles_clean.csv was not created"
  exit 1
fi

echo "GDELT complete."

# ---- OHLCV validate + clean ----
echo
echo "==================== OHLCV PIPELINE ===================="
echo "RUNNING ohlcv_validation.py..."
python "$PROJECT_ROOT/scripts/ohlcv_validation.py"

if [[ ! -f "$PROJECT_ROOT/docs/validation/ohlcv_validation.md" ]]; then
  echo "ERROR: docs/validation/ohlcv_validation.md was not created"
  exit 1
fi

echo "RUNNING ohlcv_cleaning.py..."
python "$PROJECT_ROOT/scripts/ohlcv_cleaning.py"

if [[ ! -f "$PROJECT_ROOT/data/processed/prices_daily_clean.csv" ]]; then
  echo "ERROR: data/processed/prices_daily_clean.csv was not created"
  exit 1
fi

echo "OHLCV complete."

echo
echo "============================================================"
echo "PIPELINE COMPLETE ✅"
echo "============================================================"
