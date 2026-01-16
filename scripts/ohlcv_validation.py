#!/usr/bin/env python3
"""
scripts/ohlcv_validation.py

Validates daily OHLCV CSV formatted like:

date,open,high,low,close,adj_close,volume,ticker

Checks (per ticker):
1) Missing values (NaNs) in required columns
2) Logical price constraints:
   - high >= max(open, close)
   - low  <= min(open, close)
   - high >= low
   - volume >= 0
   - open/close within [low, high] (sanity)
3) Outlier detection (robust MAD z-scores):
   - log returns outliers
   - log volume outliers

Output:
- Always writes a summary CSV to: data/raw/ohlcv_issues.csv
  (one row per ticker, with counts of each issue)

Default input:
- data/raw/prices_daily.csv

Run:
  python scripts/ohlcv_validation.py
or
  python scripts/ohlcv_validation.py --input data/raw/prices_daily.csv

Notes:
- This produces a summary, not row-level detailed dumps.
- If you want row-level outputs later, you can add separate exports.
"""

from __future__ import annotations

import argparse
import os
from typing import Dict, Any

import numpy as np
import pandas as pd


REQUIRED_COLS = ["date", "open", "high", "low", "close", "volume", "ticker"]
NUMERIC_COLS = ["open", "high", "low", "close", "volume"]


def mad_zscore(x: pd.Series) -> pd.Series:
    """Robust z-score using MAD (median absolute deviation)."""
    x = x.astype(float)
    med = np.nanmedian(x.values)
    mad = np.nanmedian(np.abs(x.values - med))
    if mad == 0 or np.isnan(mad):
        return pd.Series(np.nan, index=x.index)
    return (x - med) / (1.4826 * mad)


def summarize_ticker_issues(
    tdf: pd.DataFrame,
    freq: str = "B",
    return_z_thresh: float = 8.0,
    volume_z_thresh: float = 8.0,
    gap_days_threshold: int = 3,
) -> Dict[str, Any]:
    """
    Produce a single summary row (dict) for one ticker.
    """
    tdf = tdf.copy()

    # Parse date
    tdf["date"] = pd.to_datetime(tdf["date"], errors="coerce")

    # Coerce numeric columns
    for c in NUMERIC_COLS:
        tdf[c] = pd.to_numeric(tdf[c], errors="coerce")

    tdf = tdf.sort_values("date")

    # ---- Missing values checks ----
    missing_date = int(tdf["date"].isna().sum())
    missing_open = int(tdf["open"].isna().sum())
    missing_high = int(tdf["high"].isna().sum())
    missing_low = int(tdf["low"].isna().sum())
    missing_close = int(tdf["close"].isna().sum())
    missing_volume = int(tdf["volume"].isna().sum())

    # ---- Logical constraints ----
    # Guard against all-NaN slices
    max_oc = tdf[["open", "close"]].max(axis=1)
    min_oc = tdf[["open", "close"]].min(axis=1)

    high_lt_max_open_close = int((tdf["high"] < max_oc).sum(skipna=True))
    low_gt_min_open_close = int((tdf["low"] > min_oc).sum(skipna=True))
    high_lt_low = int((tdf["high"] < tdf["low"]).sum(skipna=True))
    negative_volume = int((tdf["volume"] < 0).sum(skipna=True))
    open_outside_low_high = int(((tdf["open"] < tdf["low"]) | (tdf["open"] > tdf["high"])).sum(skipna=True))
    close_outside_low_high = int(((tdf["close"] < tdf["low"]) | (tdf["close"] > tdf["high"])).sum(skipna=True))

    # ---- Time integrity (missing business days + large gaps) ----
    # duplicates by date within ticker
    duplicate_date_rows = int(tdf["date"].duplicated(keep=False).sum())

    observed = pd.DatetimeIndex(tdf["date"].dropna().unique())
    if len(observed) == 0:
        # No valid dates; cannot compute time checks or outliers
        missing_days_count = 0
        gap_count = 0
        return_outliers_count = 0
        volume_outliers_count = 0
        start_date = None
        end_date = None
    else:
        start_date = pd.Timestamp(observed.min()).date()
        end_date = pd.Timestamp(observed.max()).date()

        expected = pd.date_range(start=observed.min(), end=observed.max(), freq=freq)
        missing_days_count = int(len(expected.difference(observed)))

        uniq_dates = pd.DatetimeIndex(sorted(observed))
        deltas = pd.Series(uniq_dates).diff()
        gap_count = int((deltas > pd.Timedelta(days=gap_days_threshold)).sum(skipna=True))

        # ---- Outliers ----
        # Log returns outliers
        # Use close; if close has NaNs, diff will also NaN
        log_ret = np.log(tdf["close"]).diff()
        ret_z = mad_zscore(log_ret)
        return_outliers_count = int((ret_z.abs() >= return_z_thresh).sum(skipna=True))

        # Log volume outliers (log1p handles 0)
        log_vol = np.log1p(tdf["volume"])
        vol_z = mad_zscore(log_vol)
        volume_outliers_count = int((vol_z.abs() >= volume_z_thresh).sum(skipna=True))

    rows = int(len(tdf))

    # Total issue count for sorting / quick severity
    total_missing = missing_date + missing_open + missing_high + missing_low + missing_close + missing_volume
    total_logical = (
        high_lt_max_open_close
        + low_gt_min_open_close
        + high_lt_low
        + negative_volume
        + open_outside_low_high
        + close_outside_low_high
    )

    total_issues = (
        total_missing
        + total_logical
        + duplicate_date_rows
        + missing_days_count
        + gap_count
        + return_outliers_count
        + volume_outliers_count
    )

    return {
        "ticker": str(tdf["ticker"].iloc[0]) if "ticker" in tdf.columns and rows > 0 else None,
        "rows": rows,
        "start_date": start_date,
        "end_date": end_date,
        # Missing values
        "missing_date": missing_date,
        "missing_open": missing_open,
        "missing_high": missing_high,
        "missing_low": missing_low,
        "missing_close": missing_close,
        "missing_volume": missing_volume,
        "missing_total": total_missing,
        # Logical constraints
        "high_lt_max_open_close": high_lt_max_open_close,
        "low_gt_min_open_close": low_gt_min_open_close,
        "high_lt_low": high_lt_low,
        "negative_volume": negative_volume,
        "open_outside_low_high": open_outside_low_high,
        "close_outside_low_high": close_outside_low_high,
        "logical_total": total_logical,
        # Time integrity
        "duplicate_date_rows": duplicate_date_rows,
        "missing_days_count": missing_days_count,
        "gap_count": gap_count,
        # Outliers
        "return_outliers_count": return_outliers_count,
        "volume_outliers_count": volume_outliers_count,
        # Overall
        "total_issue_count": int(total_issues),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        default=os.path.join("data", "raw", "prices_daily.csv"),
        help="Input CSV path (default: data/raw/prices_daily.csv)",
    )
    ap.add_argument(
        "--output",
        default=os.path.join("data", "raw", "ohlcv_issues.csv"),
        help="Output CSV path (default: data/raw/ohlcv_issues.csv)",
    )
    ap.add_argument(
        "--freq",
        default="B",
        help="Expected frequency for missing date checks (default: B for business days).",
    )
    ap.add_argument(
        "--return_z",
        type=float,
        default=8.0,
        help="MAD z-score threshold for return outliers (default: 8.0).",
    )
    ap.add_argument(
        "--volume_z",
        type=float,
        default=8.0,
        help="MAD z-score threshold for volume outliers (default: 8.0).",
    )
    ap.add_argument(
        "--gap_days",
        type=int,
        default=3,
        help="Gap threshold in days for flagging gaps (default: 3).",
    )
    args = ap.parse_args()

    in_path = args.input
    out_path = args.output

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Input CSV not found: {in_path}")

    # Ensure output dir exists
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(in_path)

    # Validate expected columns
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")

    # Normalize types early
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    summary_rows = []
    for ticker, tdf in df.groupby("ticker"):
        summary_rows.append(
            summarize_ticker_issues(
                tdf,
                freq=args.freq,
                return_z_thresh=args.return_z,
                volume_z_thresh=args.volume_z,
                gap_days_threshold=args.gap_days,
            )
        )

    summary_df = pd.DataFrame(summary_rows)

    # Always write CSV even if empty (e.g., no rows)
    if summary_df.empty:
        # Create an empty file with headers for consistency
        summary_df = pd.DataFrame(
            columns=[
                "ticker",
                "rows",
                "start_date",
                "end_date",
                "missing_date",
                "missing_open",
                "missing_high",
                "missing_low",
                "missing_close",
                "missing_volume",
                "missing_total",
                "high_lt_max_open_close",
                "low_gt_min_open_close",
                "high_lt_low",
                "negative_volume",
                "open_outside_low_high",
                "close_outside_low_high",
                "logical_total",
                "duplicate_date_rows",
                "missing_days_count",
                "gap_count",
                "return_outliers_count",
                "volume_outliers_count",
                "total_issue_count",
            ]
        )

    # Sort by total issues (most problematic first)
    if "total_issue_count" in summary_df.columns:
        summary_df = summary_df.sort_values("total_issue_count", ascending=False)

    summary_df.to_csv(out_path, index=False)

    print(f"Wrote OHLCV issues summary: {out_path}")
    print(summary_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
