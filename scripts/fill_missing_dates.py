#!/usr/bin/env python3
"""
Fill missing date gaps by running chunked GDELT ingestion.

Computes gaps between desired date range and observed article dates,
then runs data_ingestion + accumulate for each chunk. FinBERT and
build_join run once at the end (not per chunk) to save time.

Usage:
    # Dry run (show gaps and chunks, no ingestion)
    python scripts/fill_missing_dates.py --dry-run

    # Fill gaps (chunk size 14 days, runs ingestion for each chunk)
    python scripts/fill_missing_dates.py

    # Custom chunk size
    python scripts/fill_missing_dates.py --chunk-days 7

    # Use join table for observed dates (default); fallback is accumulated
    python scripts/fill_missing_dates.py --source join

Requires: data/processed/gdelt_ohlcv_join.csv or gdelt_articles_accumulated.csv
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from msa.utils.paths import get_processed_data_path
from msa.utils.vars import WINDOW_END, WINDOW_START


def get_observed_dates(source: str) -> set:
    """Return set of normalized dates that have article data."""
    processed = get_processed_data_path()
    if source == "join":
        path = processed / "gdelt_ohlcv_join.csv"
    else:
        path = processed / "gdelt_articles_accumulated.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Source not found. Run pipeline first.\n  Expected: {path}"
        )

    df = pd.read_csv(path)
    if "article_date" in df.columns:
        df["article_date"] = pd.to_datetime(df["article_date"])
        dates = df["article_date"].dt.normalize().dt.date
    else:
        df["seendate"] = pd.to_datetime(df["seendate"])
        dates = df["seendate"].dt.normalize().dt.date
    return set(dates.unique())


def get_gap_ranges(
    observed: set,
    start: str,
    end: str,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Return list of (start, end) for contiguous gap ranges."""
    full = pd.date_range(start=start, end=end, freq="D")
    missing = [d for d in full if d.normalize().date() not in observed]
    if not missing:
        return []

    gaps = []
    gap_start = missing[0]
    prev = missing[0]
    for d in missing[1:]:
        if (d - prev).days > 1:
            gaps.append((gap_start, prev))
            gap_start = d
        prev = d
    gaps.append((gap_start, prev))
    return gaps


def chunk_gap(
    gap_start: pd.Timestamp,
    gap_end: pd.Timestamp,
    chunk_days: int,
) -> list[tuple[str, str]]:
    """Split a gap into (start_str, end_str) chunks."""
    chunks = []
    curr = gap_start
    while curr <= gap_end:
        end = min(curr + timedelta(days=chunk_days - 1), gap_end)
        chunks.append((curr.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        curr = end + timedelta(days=1)
    return chunks


def run_cmd(cmd: list[str], env: dict | None = None, cwd: Path = PROJECT_ROOT) -> bool:
    """Run command; return True if success."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(cmd, cwd=cwd, env=full_env)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill missing GDELT date gaps via chunked ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Show gaps/chunks only, no ingestion")
    parser.add_argument("--chunk-days", type=int, default=14, help="Days per ingestion chunk (default: 14)")
    parser.add_argument("--source", choices=["join", "accumulated"], default="join", help="Source for observed dates")
    parser.add_argument("--delay-between-chunks", type=int, default=30, help="Seconds to wait between chunks (default: 30, helps avoid GDELT rate limits)")
    parser.add_argument("--gdelt-source", choices=["rest", "bigquery"], default=None, help="GDELT data source (default: rest). Use bigquery when REST API is blocked.")
    args = parser.parse_args()

    print("=" * 60)
    print("FILL MISSING DATES")
    print("=" * 60)

    # Resolve source: prefer join if it exists, else use accumulated
    join_path = get_processed_data_path() / "gdelt_ohlcv_join.csv"
    if args.source == "join" and not join_path.exists():
        print("Join table not found; using gdelt_articles_accumulated.csv")
        args.source = "accumulated"

    observed = get_observed_dates(args.source)
    full_range = pd.date_range(start=WINDOW_START, end=WINDOW_END, freq="D")
    missing_count = len([d for d in full_range if d.normalize().date() not in observed])

    print(f"Desired range: {WINDOW_START} to {WINDOW_END}")
    print(f"Days with data: {len(observed)}")
    print(f"Missing days: {missing_count}")
    print()

    if missing_count == 0:
        print("No gaps to fill.")
        return 0

    gaps = get_gap_ranges(observed, WINDOW_START, WINDOW_END)
    all_chunks = []
    for g_start, g_end in gaps:
        for s, e in chunk_gap(g_start, g_end, args.chunk_days):
            all_chunks.append((s, e))

    print(f"Gap ranges: {len(gaps)}")
    print(f"Total chunks ({args.chunk_days}-day): {len(all_chunks)}")
    print()
    for i, (s, e) in enumerate(all_chunks[:10]):
        print(f"  Chunk {i+1}: {s} to {e}")
    if len(all_chunks) > 10:
        print(f"  ... and {len(all_chunks) - 10} more")
    print()

    if args.dry_run:
        print("[DRY RUN] No ingestion performed.")
        return 0

    # Run ingestion + accumulate for each chunk (skip full pipeline to avoid FinBERT per chunk)
    py = sys.executable
    processed = get_processed_data_path()
    raw = PROJECT_ROOT / "data" / "raw"

    for i, (start_str, end_str) in enumerate(all_chunks):
        print(f"\n--- Chunk {i+1}/{len(all_chunks)}: {start_str} to {end_str} ---")
        env = {
            "FIXED_START_DATE": start_str,
            "FIXED_END_DATE": end_str,
            "RUN_INGEST": "1",
        }
        if args.gdelt_source:
            env["GDELT_SOURCE"] = args.gdelt_source

        # data_ingestion uses Config; we can't easily override max_articles without code change.
        # Run data_ingestion
        if not run_cmd([py, str(PROJECT_ROOT / "scripts" / "data_ingestion.py")], env=env):
            print(f"WARNING: Ingestion failed for {start_str} to {end_str}")
            continue

        if not (raw / "gdelt_articles.csv").exists():
            print("No gdelt_articles.csv produced; skipping accumulate")
            continue

        # validate_gdelt, cleaning_gdelt
        if not run_cmd([py, str(PROJECT_ROOT / "scripts" / "validate_gdelt.py")]):
            print("validate_gdelt failed")
        if not run_cmd([py, str(PROJECT_ROOT / "scripts" / "cleaning_gdelt.py")]):
            print("cleaning_gdelt failed")
            continue

        # GDELT accumulate
        run_cmd(
            [py, str(PROJECT_ROOT / "scripts" / "accumulate.py"),
             "--new", str(processed / "gdelt_articles_clean.csv"),
             "--dest", str(processed / "gdelt_articles_accumulated.csv"),
             "--manifest", str(processed / "gdelt_manifest.json"),
             "--key", "url",
             "--sort", "seendate,ticker"],
        )

        # OHLCV validate, clean, accumulate
        if (raw / "prices_daily.csv").exists():
            run_cmd([py, str(PROJECT_ROOT / "scripts" / "ohlcv_validation.py")])
            run_cmd([py, str(PROJECT_ROOT / "scripts" / "ohlcv_cleaning.py")])
            if (processed / "prices_daily_clean.csv").exists():
                run_cmd(
                    [py, str(PROJECT_ROOT / "scripts" / "accumulate.py"),
                     "--new", str(processed / "prices_daily_clean.csv"),
                     "--dest", str(processed / "prices_daily_accumulated.csv"),
                     "--manifest", str(processed / "ohlcv_manifest.json"),
                     "--key", "date,ticker",
                     "--sort", "date,ticker"],
                )

        # Pause between chunks to avoid GDELT rate limits
        if i < len(all_chunks) - 1 and args.delay_between_chunks > 0:
            print(f"\n[Fill] Waiting {args.delay_between_chunks}s before next chunk...")
            time.sleep(args.delay_between_chunks)

    # Final: dedupe, sentiment, build_join
    print("\n" + "=" * 60)
    print("Running dedupe, FinBERT, build_join (once)...")
    print("=" * 60)

    run_cmd([py, str(PROJECT_ROOT / "scripts" / "dedupe.py")])
    run_cmd([py, str(PROJECT_ROOT / "scripts" / "add_sentiment_v2.py"),
             "--input", str(processed / "gdelt_articles_deduped.csv"),
             "--output", str(processed / "gdelt_articles_with_sentiment.csv")])
    run_cmd([py, str(PROJECT_ROOT / "scripts" / "build_gdelt_ohlcv_join.py")])

    print("\nDone. Run export_shared_datasets.py if needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
