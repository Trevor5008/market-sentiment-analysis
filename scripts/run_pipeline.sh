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
# When RUN_INGEST=1, data_ingestion.py runs and writes a run manifest to
# data/raw/snapshots/run_manifest_YYYY-MM-DD.json
RUN_INGEST="${RUN_INGEST:-0}"
if [[ "$RUN_INGEST" == "1" ]]; then
  echo "RUNNING data_ingestion.py..."
  python "$PROJECT_ROOT/scripts/data_ingestion.py"
  # Verify run manifest was created (same date logic as data_ingestion.py)
  MANIFEST_DIR="$PROJECT_ROOT/data/raw/snapshots"
  TODAY_UTC=$(python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%d'))")
  MANIFEST_FILE="$MANIFEST_DIR/run_manifest_${TODAY_UTC}.json"
  if [[ -f "$MANIFEST_FILE" ]]; then
    echo "[OK] Run manifest: $MANIFEST_FILE"
  else
    echo "ERROR: Run manifest was not created at $MANIFEST_FILE"
    exit 1
  fi
else
  echo "Skipping ingestion (set RUN_INGEST=1 to enable). No run manifest is produced when ingestion is skipped."
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
echo "Accumulating GDELT..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/accumulate.py" \
  --new "$PROJECT_ROOT/data/processed/gdelt_articles_clean.csv" \
  --dest "$PROJECT_ROOT/data/processed/gdelt_articles_accumulated.csv" \
  --manifest "$PROJECT_ROOT/data/processed/gdelt_manifest.json" \
  --key "url"

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
echo "Accumulating OHLCV..."
"$PYTHON_BIN" "$PROJECT_ROOT/scripts/accumulate.py" \
  --new "$PROJECT_ROOT/data/processed/prices_daily_clean.csv" \
  --dest "$PROJECT_ROOT/data/processed/prices_daily_accumulated.csv" \
  --manifest "$PROJECT_ROOT/data/processed/ohlcv_manifest.json" \
  --key "date,ticker"


echo
echo "============================================================"
echo "PIPELINE COMPLETE ✅"
echo "============================================================"
