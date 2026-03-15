#!/usr/bin/env bash
# Wrapper for fill_missing_dates.py. Ensures conda env is active.
set -euo pipefail

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "ERROR: Activate conda env first, e.g.: conda activate advds"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
python scripts/fill_missing_dates.py "$@"
