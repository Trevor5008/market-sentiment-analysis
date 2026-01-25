#-e so the script stops if any command fails
#-u so the scripts stop if any variable is incorrect or empty
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

venv_python="$PROJECT_ROOT/.venv/Scripts/python.exe"

#echo "RUNNING ingest_demo.py"
# "venv_python" "$PROJECT_ROOT/scripts/ingest_demo.py"

if [ ! -f "$PROJECT_ROOT/data/raw/gdelt_articles.csv" ]; then
  echo "Output at data/raw/gdelt_articles.csv was not created"
  exit 1
fi
if [ ! -f "$PROJECT_ROOT/data/raw/prices_daily.csv" ]; then
  echo "Output at data/raw/prices_daily.csv was not created"
  exit 1
fi

echo "Commencing GDELT process"

echo "RUNNING validate_gdelt.py..."
"$venv_python" "$PROJECT_ROOT/scripts/validate_gdelt.py"
if [ ! -f "$PROJECT_ROOT/docs/validation/gdelt_articles_validation.md" ]; then
  echo "Report at docs/validation/gdelt_articles_validation.md was not created"
  exit 1
fi

echo "RUNNING cleaning_gdelt.py..."
"$venv_python" "$PROJECT_ROOT/scripts/cleaning_gdelt.py"
if [ ! -f "$PROJECT_ROOT/data/processed/gdelt_articles_clean.csv" ]; then
  echo "Output at data/processed/gdelt_articles_clean.csv was not created"
  exit 1
fi

echo "GDELT Complete"




echo "Commencing OHLCV process"

echo "RUNNING ohlcv_validation.py..."
"$venv_python" "$PROJECT_ROOT/scripts/ohlcv_validation.py"
if [ ! -f "$PROJECT_ROOT/docs/validation/ohlcv_validation.md" ]; then
  echo "Report at /docs/validation/ohlcv_validation.md was not created"
  exit 1
fi

echo "RUNNING ohlcv_cleaning.py..."
"$venv_python" "$PROJECT_ROOT/scripts/ohlcv_cleaning.py"
if [ ! -f "$PROJECT_ROOT/data/processed/prices_daily_clean.csv" ]; then
  echo "Output at data/processed/prices_daily_clean.csv was not created"
  exit 1
fi

echo "OHLCV Complete"