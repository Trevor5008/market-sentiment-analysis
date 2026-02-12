#!/usr/bin/env bash
#
# run_pipeline.sh — Full data pipeline: validate → clean → accumulate → sentiment.
#
# Optional: RUN_INGEST=1 runs data_ingestion.py first (fetch raw GDELT + OHLCV, archive, manifest).
#
# Pipeline steps:
#   1. GDELT: validate_gdelt → cleaning_gdelt → accumulate (url dedupe) → add_sentiment → dedupe_and_sentiment
#      Outputs: gdelt_articles_clean.csv, gdelt_articles_accumulated.csv, gdelt_articles_with_sentiment.csv
#   2. OHLCV: ohlcv_validation → ohlcv_cleaning → accumulate (date,ticker dedupe)
#      Outputs: prices_daily_clean.csv, prices_daily_accumulated.csv
#
# Not run by this script: build_gdelt_ohlcv_join.py (news day t → prices day t+1).
# Run separately when needed: python scripts/build_gdelt_ohlcv_join.py
#
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

# When RUN_INGEST=1, data_ingestion.py runs and writes a run manifest to
# data/raw/snapshots/run_manifest_YYYY-MM-DD.json
RUN_INGEST="${RUN_INGEST:-0}" # REQUIRED for accumulation component (dependency)
if [[ "$RUN_INGEST" == "1" ]]; then
  echo "RUNNING data_ingestion.py..."
  python "$PROJECT_ROOT/scripts/data_ingestion.py"
  # Verify a run manifest was created (ingestion names it by end_dt, not today)
  MANIFEST_DIR="$PROJECT_ROOT/data/raw/snapshots"
  LATEST_MANIFEST=$(ls -t "$MANIFEST_DIR"/run_manifest_*.json 2>/dev/null | head -1)
  if [[ -n "$LATEST_MANIFEST" && -f "$LATEST_MANIFEST" ]]; then
    echo "[OK] Run manifest: $LATEST_MANIFEST"
  else
    echo "ERROR: No run manifest found in $MANIFEST_DIR"
    exit 1
  fi
else
  echo "Skipping ingestion (set RUN_INGEST=1 to enable). No run manifest is produced when ingestion is skipped."
  echo "  → Raw data will not be refreshed; output date range will not extend past the last ingestion run."
  MANIFEST_DIR="$PROJECT_ROOT/data/raw/snapshots"
  if [[ -d "$MANIFEST_DIR" ]]; then
    LATEST_MANIFEST=$(ls -t "$MANIFEST_DIR"/run_manifest_*.json 2>/dev/null | head -1)
    if [[ -n "$LATEST_MANIFEST" && -f "$LATEST_MANIFEST" ]]; then
      echo "  → Last ingestion (from manifest): $(python -c "import json; print(json.load(open('$LATEST_MANIFEST')).get('timestamp', 'unknown')[:10])" 2>/dev/null || echo "unknown")"
    fi
  fi
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

# ---- GDELT: validate → clean → accumulate → sentiment ----
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

echo "Accumulating GDELT..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/accumulate.py" \
  --new "$PROJECT_ROOT/data/processed/gdelt_articles_clean.csv" \
  --dest "$PROJECT_ROOT/data/processed/gdelt_articles_accumulated.csv" \
  --manifest "$PROJECT_ROOT/data/processed/gdelt_manifest.json" \
  --key "url" \
  --sort "seendate,ticker"

# Sentiment (word-bank) then dedupe + regenerate sentiment → gdelt_articles_with_sentiment.csv
echo "RUNNING add_sentiment.py..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/add_sentiment.py" \
  --input "$PROJECT_ROOT/data/processed/gdelt_articles_accumulated.csv" \
  --output "$PROJECT_ROOT/data/processed/gdelt_articles_with_sentiment.csv"

echo "RUNNING dedupe_and_sentiment.py..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/dedupe_and_sentiment.py"

if [[ ! -f "$PROJECT_ROOT/data/processed/gdelt_articles_with_sentiment.csv" ]]; then
  echo "ERROR: data/processed/gdelt_articles_with_sentiment.csv was not created"
  exit 1
fi

echo "GDELT complete (accumulated + sentiment)."

# ---- OHLCV: validate → clean → accumulate ----
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
echo "Accumulating OHLCV..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/accumulate.py" \
  --new "$PROJECT_ROOT/data/processed/prices_daily_clean.csv" \
  --dest "$PROJECT_ROOT/data/processed/prices_daily_accumulated.csv" \
  --manifest "$PROJECT_ROOT/data/processed/ohlcv_manifest.json" \
  --key "date,ticker" \
  --sort "date,ticker"


echo
echo "============================================================"
echo "PIPELINE COMPLETE ✅"
echo "============================================================"
echo "Outputs: gdelt_articles_with_sentiment.csv, prices_daily_accumulated.csv"
echo "To build the price–news join (news t → prices t+1), run:"
echo "  python scripts/build_gdelt_ohlcv_join.py"
echo "============================================================"
