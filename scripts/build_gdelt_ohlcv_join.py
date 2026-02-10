#!/usr/bin/env python3
"""
scripts/build_gdelt_ohlcv_join.py

Build a join table linking GDELT articles to OHLCV prices for team analysis.

Working assumption: news on day t is aligned to prices on day t+1 (next trading day).
- Article on Monday → Tuesday's prices
- Article on Friday, Saturday, or Sunday → Monday's prices (weekends skipped)
Uses NYSE market calendar so holidays are respected.

Output: one row per (article, ticker) with article fields plus next-day price fields.
"""

from __future__ import annotations

import argparse
import pandas as pd
import numpy as np
from pathlib import Path

try:
    import pandas_market_calendars as mcal
except ImportError:
    raise ImportError("pandas_market_calendars is required. Install with: pip install pandas_market_calendars")

# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Default inputs
DEFAULT_GDELT = PROCESSED_DIR / "gdelt_articles_with_sentiment.csv"
DEFAULT_OHLCV = PROCESSED_DIR / "prices_daily_accumulated.csv"
DEFAULT_OUTPUT = PROCESSED_DIR / "gdelt_ohlcv_join.csv"


def get_trading_days(start: pd.Timestamp, end: pd.Timestamp, exchange: str = "NYSE") -> pd.DatetimeIndex:
    """Return sorted DatetimeIndex of trading days in [start, end] (inclusive)."""
    cal = mcal.get_calendar(exchange)
    schedule = cal.schedule(start_date=start, end_date=end)
    return pd.DatetimeIndex(schedule.index).tz_localize(None).normalize()


def next_trading_day_series(dates: pd.Series, trading_days: pd.DatetimeIndex) -> pd.Series:
    """
    For each date in `dates`, return the next trading day (strictly after that date).
    Weekend/holiday safe: Fri/Sat/Sun all map to Monday (next trading day).
    """
    t = np.sort(trading_days.unique())
    norm = pd.to_datetime(dates).dt.normalize()

    # searchsorted(t, d, side='right') = index of first trading day > d
    indices = np.searchsorted(t, norm.values, side="right")
    no_next = indices >= len(t)
    result = pd.Series(t[indices], index=dates.index)
    result = result.where(~no_next, pd.NaT)
    result = result.where(norm.notna(), pd.NaT)  # keep NaT where input was NaT
    return result


def build_join(
    gdelt_path: Path | str,
    ohlcv_path: Path | str,
    output_path: Path | str,
    exchange: str = "NYSE",
) -> pd.DataFrame:
    """
    Build join table: GDELT rows with next-trading-day OHLCV columns per ticker.

    - gdelt must have: seendate, ticker (and optionally sentiment_score, etc.)
    - ohlcv must have: date, ticker, open, high, low, close, (adj_close), volume
    - Each article row gets price_date = next trading day after article date (by NYSE).
    """
    gdelt_path = Path(gdelt_path)
    ohlcv_path = Path(ohlcv_path)
    output_path = Path(output_path)

    # Load
    gdelt = pd.read_csv(gdelt_path, parse_dates=["seendate"])
    ohlcv = pd.read_csv(ohlcv_path, parse_dates=["date"])

    # Article date (date only, no time)
    gdelt["article_date"] = pd.to_datetime(gdelt["seendate"]).dt.tz_localize(None).dt.normalize()

    # Trading day range: from min article date to max ohlcv date (add buffer for "next" day)
    art_min = gdelt["article_date"].min()
    art_max = gdelt["article_date"].max()
    ohlcv_min = ohlcv["date"].min()
    ohlcv_max = ohlcv["date"].max()
    range_start = min(art_min, ohlcv_min) - pd.Timedelta(days=1)
    range_end = max(art_max, ohlcv_max) + pd.Timedelta(days=1)
    trading_days = get_trading_days(range_start, range_end, exchange)

    # Map each article_date -> next trading day
    gdelt["price_date"] = next_trading_day_series(gdelt["article_date"], trading_days)

    # Drop rows with no next trading day (e.g. article after last price date)
    before_join = len(gdelt)
    gdelt = gdelt.dropna(subset=["price_date"])
    gdelt["price_date"] = pd.to_datetime(gdelt["price_date"]).dt.normalize()
    dropped = before_join - len(gdelt)
    if dropped:
        print(f"  Dropped {dropped} article rows with no next trading day in range.")

    # OHLCV columns to attach (avoid name clashes)
    price_cols = ["open", "high", "low", "close", "adj_close", "volume"]
    price_cols = [c for c in price_cols if c in ohlcv.columns]
    ohlcv_sub = ohlcv[["date", "ticker"] + price_cols].copy()
    ohlcv_sub = ohlcv_sub.rename(columns={c: f"next_{c}" for c in price_cols})
    ohlcv_sub = ohlcv_sub.rename(columns={"date": "price_date"})
    ohlcv_sub["price_date"] = pd.to_datetime(ohlcv_sub["price_date"]).dt.normalize()

    # Join on (price_date, ticker)
    join_df = gdelt.merge(
        ohlcv_sub,
        on=["price_date", "ticker"],
        how="inner",
    )

    # Sort for readability
    sort_cols = [c for c in ["article_date", "ticker", "seendate"] if c in join_df.columns]
    if sort_cols:
        join_df = join_df.sort_values(sort_cols).reset_index(drop=True)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    join_df.to_csv(output_path, index=False)
    print(f"  Join table: {len(join_df):,} rows -> {output_path}")

    return join_df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build GDELT–OHLCV join table (news day t -> prices day t+1, NYSE calendar)"
    )
    parser.add_argument(
        "--gdelt",
        default=str(DEFAULT_GDELT),
        help="Path to GDELT CSV (with seendate, ticker)",
    )
    parser.add_argument(
        "--ohlcv",
        default=str(DEFAULT_OHLCV),
        help="Path to OHLCV CSV (date, ticker, OHLCV columns)",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to output join CSV",
    )
    parser.add_argument(
        "--exchange",
        default="NYSE",
        help="Exchange for trading calendar (default: NYSE)",
    )
    args = parser.parse_args()

    print("Building GDELT–OHLCV join table (article date t -> price date t+1, next trading day)")
    build_join(args.gdelt, args.ohlcv, args.output, exchange=args.exchange)
    print("Done.")


if __name__ == "__main__":
    main()
