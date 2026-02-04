from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests

SCRIPT_VERSION = "1.0.0"

try:
    import yfinance as yf
except ImportError as e:
    raise SystemExit(
        "Missing dependency: yfinance. Install via `pip install yfinance`.") from e

# --- Configurable constants ---
MAG7: Dict[str, str] = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Meta Platforms": "META",
    "Tesla": "TSLA",
}

COMPANY_QUERY_OVERRIDES = {
    "Meta": '("Meta Platforms" OR Facebook OR META) (stock OR shares OR' +
        'earnings OR revenue)'
}

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def get_project_root() -> Path:
    """Find project root by locating this script and going up one level."""
    script_dir = Path(__file__).parent.resolve()
    # If script is in scripts/, go up one level to project root
    if script_dir.name == "scripts":
        return script_dir.parent
    # Otherwise, assume we're already at project root
    return script_dir


@dataclass
class Config:
    days_back: int = 30
    max_articles_per_company: int = 2000  # Per company: dateasc + datedesc passes; after headline dedupe in cleaning, unique stories span window
    page_size: int = 250  # GDELT API max per request
    out_dir: str = "data/raw"
    user_agent: str = "market-sentiment-analysis/data_ingestion (capstone)"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_git_short_hash(project_root: Path) -> str:
    """Return short git commit hash, or 'unknown' if not in a repo or git unavailable."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def archive_if_exists(path: Path, archive_dir: Path, date_str: str, dataset_name: str) -> None:
    """If path exists, move it to archive_dir as {dataset_name}_{date_str}.csv."""
    if not path.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{dataset_name}_{date_str}.csv"
    shutil.move(str(path), str(archive_path))
    print(f"[Archive] Moved {path.name} -> archive/{archive_path.name}")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_gdelt_dt(dt: datetime) -> str:
    # Format required by GDELT: YYYYMMDDHHMMSS in UTC
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def request_with_backoff(
    url: str,
    params: Dict[str, str],
    headers: Dict[str, str],
    max_retries: int = 6,
    timeout: int = 30,
) -> requests.Response:
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params,
                                headers=headers, timeout=timeout)

            # Handle rate limiting explicitly
            if resp.status_code == 429:
                sleep_s = (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_s)
                continue

            resp.raise_for_status()
            return resp
        except Exception as e:
            last_err = e
            sleep_s = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_s)

    raise RuntimeError(
        f"Request failed after {max_retries} retries. Last error: {last_err}"
    )


def fetch_gdelt_articles(
    query: str,
    start_dt: datetime,
    end_dt: datetime,
    page_size: int,
    max_articles: int,
    headers: Dict[str, str],
    sort_order: str = "datedesc",
) -> pd.DataFrame:
    """Fetch GDELT articles in the given window. sort_order 'dateasc' = oldest first, 'datedesc' = newest first."""
    start_str = to_gdelt_dt(start_dt)
    end_str = to_gdelt_dt(end_dt)

    rows: List[Dict[str, Any]] = []
    start_record = 1  # GDELT uses 1-indexed startrecord
    sort_param = "dateasc" if sort_order == "dateasc" else "datedesc"

    while len(rows) < max_articles:
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "startdatetime": start_str,
            "enddatetime": end_str,
            "maxrecords": str(page_size),
            "startrecord": str(start_record),
            "sort": sort_param,
        }

        resp = request_with_backoff(
            GDELT_DOC_URL, params=params, headers=headers)
        ct = resp.headers.get("content-type", "")
        if "json" not in ct.lower():
            print(
                f"[GDELT] Non-JSON response status={resp.status_code} " +
                    "content-type={ct} query={query}")
            print(resp.text[:300])
            break
        try:
            data = resp.json()
            if "error" in data:
                print("[GDELT] API error: " +
                    f"{data.get('error')} | query={query}")
                break
        except ValueError as e:
            print(f"Warning: Failed to parse JSON response: {e}")
            break

        articles = data.get("articles") or []
        if not isinstance(articles, list):
            print("[GDELT] Unexpected payload shape" +
                f"(no articles list). Keys: {list(data.keys())}")
            break
        if not articles:
            break

        for a in articles:
            rows.append(
                {
                    "query": query,
                    "seendate": a.get("seendate"),
                    "url": a.get("url"),
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "language": a.get("language"),
                    "domain": a.get("domain"),
                    "sourceCountry": a.get("sourceCountry"),
                    "socialimage": a.get("socialimage"),
                }
            )

        # Early stop: datedesc => stop when we have articles back to start_dt; dateasc => stop when we reach end_dt
        if rows:
            try:
                parsed = [pd.Timestamp(r["seendate"], tz="UTC") for r in rows if r.get("seendate")]
                if parsed:
                    if sort_param == "datedesc" and min(parsed) <= start_dt:
                        break
                    if sort_param == "dateasc" and max(parsed) >= end_dt:
                        break
            except (TypeError, ValueError):
                pass

        start_record += page_size
        time.sleep(0.2)  # polite pacing

    df = pd.DataFrame(rows)

    if not df.empty and "seendate" in df.columns:
        df["seendate"] = pd.to_datetime(
            df["seendate"], errors="coerce", utc=True)

    return df


def fetch_prices_daily(tickers: List[str]
                       , start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    # yfinance end date is exclusive; add one day to include end date
    start_str = start_dt.date().isoformat()
    end_str = (end_dt.date() + timedelta(days=1)).isoformat()

    try:
        raw = yf.download(
            tickers=tickers,
            start=start_str,
            end=end_str,
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception as e:
        print(f"Warning: Failed to download prices: {e}")
        return pd.DataFrame()

    if raw.empty:
        return pd.DataFrame()

    # Normalize to long format
    rows = []
    if isinstance(raw.columns, pd.MultiIndex):
        level_0_values = raw.columns.get_level_values(0).unique()
        for t in tickers:
            if t not in level_0_values:
                continue
            sub = raw[t].copy()
            sub["ticker"] = t
            sub = sub.reset_index().rename(columns={"Date": "date"})
            rows.append(sub)
        out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    else:
        out = raw.reset_index().rename(columns={"Date": "date"})
        out["ticker"] = tickers[0] if tickers else None

    if not out.empty:
        out.columns = [c.lower().replace(" ", "_") for c in out.columns]
    return out


def main() -> None:
    cfg = Config()
    project_root = get_project_root()
    out_dir = (project_root / cfg.out_dir).resolve()
    ensure_dir(str(out_dir))
    archive_dir = out_dir / "archive"
    snapshots_dir = out_dir / "snapshots"

    end_dt = utc_now()
    start_dt = end_dt - timedelta(days=cfg.days_back)
    date_str = end_dt.strftime("%Y-%m-%d")

    print(f"[Ingestion] Requested date range: {start_dt.date().isoformat()} to {end_dt.date().isoformat()} (UTC)")
    headers = {"User-Agent": cfg.user_agent}

    # --- Fetch news ---
    # Two-phase fetch: dateasc pulls from start_dt (match OHLCV range); datedesc pulls newest; merge and dedupe by URL
    per_pass = max(1, cfg.max_articles_per_company // 2)
    article_frames = []
    for company, ticker in MAG7.items():
        base_query = f"""
        ("{company}" OR {ticker}) (stock OR shares OR earnings OR revenue)
        """
        query = COMPANY_QUERY_OVERRIDES.get(company, base_query)
        print(f"[GDELT] Fetching articles for {company} ({ticker}) [oldest then newest] ...")

        df_old = fetch_gdelt_articles(
            query=query,
            start_dt=start_dt,
            end_dt=end_dt,
            page_size=cfg.page_size,
            max_articles=per_pass,
            headers=headers,
            sort_order="dateasc",
        )
        df_new = fetch_gdelt_articles(
            query=query,
            start_dt=start_dt,
            end_dt=end_dt,
            page_size=cfg.page_size,
            max_articles=per_pass,
            headers=headers,
            sort_order="datedesc",
        )
        df = pd.concat([df_old, df_new], ignore_index=True)
        if not df.empty and "url" in df.columns:
            df = df.drop_duplicates(subset=["url"], keep="last").reset_index(drop=True)
        df["company"] = company
        df["ticker"] = ticker
        article_frames.append(df)

    articles_df = pd.concat(
        article_frames, ignore_index=True) if article_frames else pd.DataFrame()
    articles_path = out_dir / "gdelt_articles.csv"
    archive_if_exists(articles_path, archive_dir, date_str, "gdelt_articles")
    articles_df.to_csv(articles_path, index=False)
    print(f"[OK] Wrote {len(articles_df):,} rows -> {articles_path}")

    # --- Fetch prices ---
    tickers = list(MAG7.values())
    print(f"[Prices] Fetching daily OHLCV for {len(tickers)} tickers ...")
    prices_df = fetch_prices_daily(
        tickers=tickers, start_dt=start_dt, end_dt=end_dt)

    prices_path = out_dir / "prices_daily.csv"
    archive_if_exists(prices_path, archive_dir, date_str, "prices_daily")
    prices_df.to_csv(prices_path, index=False)
    print(f"[OK] Wrote {len(prices_df):,} rows -> {prices_path}")

    # --- Run manifest ---
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = snapshots_dir / f"run_manifest_{date_str}.json"
    manifest = {
        "timestamp": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_range": {
            "start_date": start_dt.date().isoformat(),
            "end_date": end_dt.date().isoformat(),
        },
        "tickers_covered": tickers,
        "row_counts": {
            "gdelt_articles": int(len(articles_df)),
            "prices_daily": int(len(prices_df)),
        },
        "script_version": SCRIPT_VERSION,
        "git_commit": get_git_short_hash(project_root),
        "notes": "",
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Wrote run manifest -> {manifest_path}")

    # --- Demo-friendly summary ---
    if not articles_df.empty and "ticker" in articles_df.columns:
        print("\nArticle counts by ticker:")
        count_col = "url" if "url" in articles_df.columns else articles_df.columns[0]
        print(articles_df.groupby("ticker")[
              count_col].count().sort_values(ascending=False).to_string())

    if not prices_df.empty and "ticker" in prices_df.columns and "date" in prices_df.columns:
        print("\nPrice rows by ticker:")
        print(prices_df.groupby("ticker")["date"].count(
        ).sort_values(ascending=False).to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
