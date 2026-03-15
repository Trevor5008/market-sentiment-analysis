from __future__ import annotations

import argparse
import html
import json
import os
import re
import random
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

SCRIPT_VERSION = "1.2.0"  # 1.1.0 -> 1.2.0: Added GDELT BigQuery backend (GDELT_SOURCE=bigquery).

# Try to import yfinance and raise an error if it's not installed.
try:
    import yfinance as yf
except ImportError as e:
    # If the import fails, print an error and raise a SystemExit.
    raise SystemExit(
        "Missing dependency: yfinance. Install via `pip install yfinance`.") from e

# Try to import pandas_market_calendars and raise an error if it's not installed.
try:
    import pandas_market_calendars as mcal
except ImportError as e:
    # If the import fails, print an error and raise a SystemExit.
    raise SystemExit(
        "Missing dependency: pandas_market_calendars. Install via `pip install pandas-market-calendars`."
    ) from e

# BigQuery client is optional; required only when GDELT_SOURCE=bigquery.
def _get_bigquery_client():
    """Lazy import of BigQuery client. Raises SystemExit if GDELT_SOURCE=bigquery but client unavailable."""
    try:
        from google.cloud import bigquery
        return bigquery.Client()
    except ImportError as e:
        raise SystemExit(
            "GDELT_SOURCE=bigquery requires google-cloud-bigquery. Install via `pip install google-cloud-bigquery`."
        ) from e

# The MAG7 dict is a dictionary of company names and their tickers.
MAG7: Dict[str, str] = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Meta Platforms": "META",
    "Tesla": "TSLA",
}

# Meta Platforms is the only company that is not in the MAG7 list, included in the query overrides.
COMPANY_QUERY_OVERRIDES = {
    "Meta": '("Meta Platforms" OR Facebook OR META) (stock OR shares OR earnings OR revenue)',
}

# Base URL for GDELT API.
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Get the project root directory during script execution.
def get_project_root() -> Path:
    """Find project root by locating this script and going up one level."""
    script_dir = Path(__file__).parent.resolve()
    # If script is in scripts/, go up one level to project root
    if script_dir.name == "scripts":
        return script_dir.parent
    # Otherwise, assume we're already at project root
    return script_dir

# Configuration class for the data ingestion script.
@dataclass
class Config:
    days_back: int = 7
    max_articles_per_company: int = 500  # dateasc + datedesc passes; after headline dedupe
    page_size: int = 100  # GDELT API max per request
    out_dir: str = "data/raw"
    user_agent: str = "market-sentiment-analysis/data_ingestion (capstone)"

# Ensure the directory exists.
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# (private) Helper for retrieving the git commit hash for usage in the run manifest.
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

# (private) Helper for archiving a dataset if it exists.
def _archive_if_exists(path: Path, archive_dir: Path, date_str: str, dataset_name: str) -> None:
    """If path exists, move it to archive_dir as {dataset_name}_{date_str}.csv."""
    if not path.exists():
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{dataset_name}_{date_str}.csv"
    shutil.move(str(path), str(archive_path))
    print(f"[Archive] Moved {path.name} -> archive/{archive_path.name}")

# Helper for getting the current UTC time.
def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# (private) Helper function for clamping the end date to the last trading day on or before the given date.
def _last_trading_day_on_or_before(dt: datetime, exchange: str = "NYSE") -> datetime:
    """Return the last trading day on or before dt (end of day, UTC)."""
    cal = mcal.get_calendar(exchange)
    start = dt.date() - timedelta(days=30)
    schedule = cal.schedule(start_date=start, end_date=dt.date())
    if schedule.empty:
        return dt
    last_date = pd.Timestamp(schedule.index[-1]).date()
    return datetime.combine(last_date, datetime.min.time(), tzinfo=timezone.utc)

# Helper for formatting a datetime for the GDELT API.
def to_gdelt_dt(dt: datetime) -> str:
    # Format required by GDELT: YYYYMMDDHHMMSS in UTC
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")

# (private) Helper for sanitizing JSON control characters.
def _sanitize_json_control_chars(text: str) -> str:
    """Replace ASCII control chars (0x00-0x1f) with space to fix GDELT's invalid JSON."""
    return "".join(" " if ord(c) < 32 else c for c in text)

# (private) Helper for parsing GDELT JSON.
def _parse_gdelt_json(text: str) -> Any:
    """Parse GDELT JSON, with fallback for 'Invalid control character' errors."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if "control character" in str(e).lower():
            print("[GDELT] Invalid control character in response; sanitizing and retrying parse...")
            return json.loads(_sanitize_json_control_chars(text))
        raise

# (private) Helper for checking if a response looks like HTML/non-JSON.
def _response_looks_non_json(text: str) -> bool:
    """True if response body clearly looks like HTML or non-JSON. Skip parse, use backoff retry."""
    if not text or not text.strip():
        return True
    t = text.strip().lower()
    # Check HTML/error indicators first (GDELT error body can start with {Content-type: text/html...)
    if (
        "content-type: text/html" in t[:800]
        or "unknown error occurred" in t[:1000]
        or "try your query again" in t[:1000]
        or "<!doctype" in t[:1000]
        or "<html" in t[:500]
    ):
        return True
    if t.startswith("<"):
        return True
    # Valid JSON starts with { or [
    if t.startswith("{") or t.startswith("["):
        return False
    return True

# (private) Helper for retrying failed GDELT ticker requests.
def _request_with_backoff(
    url: str,
    params: Dict[str, str],
    headers: Dict[str, str],
    max_retries: int = 3,
    timeout: int = 20,
) -> requests.Response:
    if max_retries is None:
        try:
            max_retries = int(os.environ.get("GDELT_MAX_RETRIES", "12"))
        except ValueError:
            max_retries = 12
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)

            # Handle rate limiting (429) - GDELT is very sensitive; use longer backoff
            if resp.status_code == 429:
                print(f"[GDELT] Rate limited (429); retrying in {2 ** attempt}s...")
                sleep_s = (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_s)
                last_err = RuntimeError(f"Server error {resp.status_code}")
                continue
           

            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout as e:
            last_err = e
            sleep_s = min(60, 5 * (2 ** attempt))
            print(f"[GDELT] Timeout. Waiting {sleep_s:.0f}s before retry...")
            time.sleep(sleep_s)
        except Exception as e:
            print(f"Response failed with error: {e}. Attempt {attempt + 1} of {max_retries}.")
            last_err = e
            sleep_s = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(sleep_s)

    hint = ""
    if "429" in str(last_err) or (hasattr(last_err, "response") and getattr(last_err.response, "status_code", None) == 429):
        hint = " Use --skip-gdelt to refresh prices only, or try GDELT_MAX_RETRIES=2 for quicker exit."
    raise RuntimeError(
        f"GDELT request failed after {max_retries} retries. Last error: {last_err}.{hint}"
    )

# (private) Helper function for fetching GDELT articles
def _fetch_gdelt_articles(
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

    # Create a list to store the rows.
    rows: List[Dict[str, Any]] = []
    # The start record is the 1-indexed start record.
    start_record = 1  # GDELT uses 1-indexed startrecord
    sort_param = "dateasc" if sort_order == "dateasc" else "datedesc"

    # While the number of rows is less than the maximum number of articles.
    while len(rows) < max_articles:
        # Create the parameters for the GDELT API request.
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

        resp = _request_with_backoff(
            GDELT_DOC_URL, params=params, headers=headers)
        ct = resp.headers.get("content-type", "")
        if "json" not in ct.lower():
            print(f"[GDELT] Non-JSON response status={resp.status_code} content-type={ct} query={query[:60]}...")
            print(resp.text[:300])
            break

        # Explicit check: skip parse if body is HTML/non-JSON; avoid unproductive parse + immediate retry
        text = resp.text or ""
        if _response_looks_non_json(text):
            print("[GDELT] Response is HTML/non-JSON; skipping parse, using backoff retry...")
            is_transient = True
            data = None
        else:
            try:
                data = _parse_gdelt_json(text)
                if "error" in data:
                    print(f"[GDELT] API error: {data.get('error')} | query={query[:60]}...")
                    break
                is_transient = False
            except ValueError as e:
                text_lower = text.lower()
                snippet = text_lower[:400].replace("\n", " ")
                print(f"[GDELT] Failed to parse JSON: {e}. Response snippet: {snippet}")
                # GDELT returns HTML with "try again in a few minutes" on transient errors
                is_transient = (
                    "unknown error occurred" in text_lower
                    or "try your query again" in text_lower
                    or "content-type: text/html" in text_lower
                )
                data = None

        # Retry parsing if the initial parse failed (no data returned).
        if data is None:
            max_parse_retries = 3 if is_transient else 1
            parse_retry_delay = 120 if is_transient else 1  # seconds
            # Retry up to max_parse_retries times (3 by default).
            for parse_attempt in range(max_parse_retries):
                if parse_attempt > 0 or is_transient:
                    # Print the retry attempt number and the total number of retries.
                    msg = f"[GDELT] Retry {parse_attempt + 1}/{max_parse_retries}"
                    if is_transient:
                        msg += f" (waiting {parse_retry_delay}s for GDELT recovery)..."
                    else:
                        msg += f" (waiting {parse_retry_delay}s)..."
                    print(msg)
                    time.sleep(parse_retry_delay)
                # Retry the request with backoff.
                resp = _request_with_backoff(
                    GDELT_DOC_URL, params=params, headers=headers)
                ct = resp.headers.get("content-type", "")
                if "json" not in ct.lower():
                    print(f"[GDELT] Retry returned non-JSON (content-type={ct}); skipping rest of this pass.")
                    break

                # Handle HTML/non-JSON responses
                if _response_looks_non_json(resp.text or ""):
                    print(f"[GDELT] Retry returned HTML/non-JSON again; retry {parse_attempt + 1}/{max_parse_retries}.")
                    continue
                try:
                    data = _parse_gdelt_json(resp.text or "")
                    break
                except (ValueError, json.JSONDecodeError):
                    if parse_attempt < max_parse_retries - 1:
                        continue
                    print("[GDELT] Retries exhausted; skipping rest of this pass.")
                    break

            if data is None:
                break
            if "error" in data:
                print(f"[GDELT] API error on retry: {data.get('error')}")
                break

        # Get the articles from the data.
        articles = data.get("articles") or []
        # If the articles are not a list, print an error and break.
        if not isinstance(articles, list):
            print(f"[GDELT] Unexpected payload shape (no articles list). Keys: {list(data.keys())}")
            break
        # If the articles are an empty list, print an error and break.
        if not articles:
            break

        # Append the articles to the rows list.
        for a in articles:
            # Append the article to the rows list.
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
                    # Stop if we have enough articles back to start_dt (datedesc) or forward to end_dt (dateasc).
                    if sort_param == "datedesc" and min(parsed) <= start_dt:
                        break
                    if sort_param == "dateasc" and max(parsed) >= end_dt:
                        break
                    # Otherwise, continue fetching more articles.
                    continue
            except (TypeError, ValueError):
                pass

        start_record += page_size
        time.sleep(1.0)  # polite pacing - GDELT rate limits are strict

    df = pd.DataFrame(rows)

    if not df.empty and "seendate" in df.columns:
        df["seendate"] = pd.to_datetime(
            df["seendate"], errors="coerce", utc=True)

    return df


# ---- GDELT BigQuery backend ----
GDELT_BQ_TABLE = "gdelt-bq.gdeltv2.gkg_partitioned"
# Organization search terms per company (for V2Organizations LIKE). Meta needs extra aliases.
_COMPANY_ORG_TERMS: Dict[str, List[str]] = {
    "Apple": ["Apple", "AAPL"],
    "Microsoft": ["Microsoft", "MSFT"],
    "NVIDIA": ["NVIDIA", "NVDA"],
    "Alphabet": ["Alphabet", "Google", "GOOGL", "GOOG"],
    "Amazon": ["Amazon", "AMZN"],
    "Meta Platforms": ["Meta Platforms", "Meta", "Facebook", "META", "FB"],
    "Tesla": ["Tesla", "TSLA"],
}


def _parse_page_title_from_extras(extras: Optional[str]) -> str:
    """Extract and unescape <<PAGE_TITLE>>...<</PAGE_TITLE>> from GKG Extras. Returns empty string if not found."""
    if not extras or not isinstance(extras, str):
        return ""
    m = re.search(r"<<PAGE_TITLE>>(.*?)<<\/PAGE_TITLE>>", extras, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    try:
        return html.unescape(m.group(1).strip())
    except Exception:
        return m.group(1).strip() or ""


def _fetch_gdelt_bigquery(
    company: str,
    ticker: str,
    start_dt: datetime,
    end_dt: datetime,
    max_articles: int,
) -> pd.DataFrame:
    """
    Fetch GDELT articles from BigQuery GKG for one company. Uses V2Organizations
    for filtering. Returns DataFrame with url, seendate, title, domain, company, ticker.
    """
    client = _get_bigquery_client()
    terms = _COMPANY_ORG_TERMS.get(company, [company, ticker])
    # Build OR conditions: V2Organizations LIKE '%Apple%' OR V2Organizations LIKE '%AAPL%'
    like_conditions = " OR ".join(
        f"LOWER(COALESCE(V2Organizations,'')) LIKE LOWER('%{t.replace(chr(39), chr(39)+chr(39))}%')"
        for t in terms
    )
    start_pt = start_dt.date().isoformat()
    end_pt = end_dt.date().isoformat()
    start_ts = start_dt.strftime("%Y%m%d%H%M%S")
    end_ts = end_dt.strftime("%Y%m%d%H%M%S")

    # Use _PARTITIONTIME for cost-efficient scans. Extras column may be Extras or empty.
    query = f"""
    SELECT
        DocumentIdentifier AS url,
        DATE AS date_raw,
        SourceCommonName AS domain,
        COALESCE(Extras, '') AS extras
    FROM `{GDELT_BQ_TABLE}`
    WHERE _PARTITIONTIME >= TIMESTAMP("{start_pt}")
      AND _PARTITIONTIME <= TIMESTAMP("{end_pt}")
      AND DATE >= {start_ts}
      AND DATE <= {end_ts}
      AND ({like_conditions})
    ORDER BY DATE
    LIMIT {max_articles}
    """
    try:
        df = client.query(query).result().to_dataframe(create_bqstorage_client=False)
    except Exception as e:
        if "Unrecognized name: Extras" in str(e) or "Extras" in str(e):
            # Fallback: table may use different column name or lack Extras
            query_no_extras = f"""
            SELECT
                DocumentIdentifier AS url,
                DATE AS date_raw,
                SourceCommonName AS domain
            FROM `{GDELT_BQ_TABLE}`
            WHERE _PARTITIONTIME >= TIMESTAMP("{start_pt}")
              AND _PARTITIONTIME <= TIMESTAMP("{end_pt}")
              AND DATE >= {start_ts}
              AND DATE <= {end_ts}
              AND ({like_conditions})
            ORDER BY DATE
            LIMIT {max_articles}
            """
            df = client.query(query_no_extras).result().to_dataframe(create_bqstorage_client=False)
            df["extras"] = ""
        else:
            raise

    if df.empty:
        df = pd.DataFrame(columns=["url", "seendate", "title", "domain", "company", "ticker"])
        return df

    df["seendate"] = pd.to_datetime(df["date_raw"].astype(str), format="%Y%m%d%H%M%S", errors="coerce")
    df["title"] = df.get("extras", pd.Series(dtype=object)).apply(_parse_page_title_from_extras)
    # Fallback title for FinBERT when PAGE_TITLE not in Extras
    missing_title = df["title"].fillna("").eq("")
    if missing_title.any():
        df.loc[missing_title, "title"] = df.loc[missing_title, "url"].astype(str).str[:120]
    df["company"] = company
    df["ticker"] = ticker
    for col in ["description", "language", "sourceCountry", "socialimage"]:
        if col not in df.columns:
            df[col] = ""
    if "domain" not in df.columns:
        df["domain"] = ""
    df = df[["url", "seendate", "title", "description", "language", "domain", "sourceCountry", "socialimage", "company", "ticker"]]
    return df


# Helper function for fetching daily prices from yfinance.
def fetch_prices_daily(
    tickers: List[str],
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame:
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
    # If the request fails, print a warning and return an empty DataFrame.
    except Exception as e:
        print(f"Warning: Failed to download prices: {e}")
        return pd.DataFrame()

    # If the raw data is empty, return an empty DataFrame.
    if raw.empty:
        return pd.DataFrame()

    # Normalize to long format
    rows = []
    if isinstance(raw.columns, pd.MultiIndex):
        level_0_values = raw.columns.get_level_values(0).unique()
        # For each ticker, if the ticker is not in the raw data, continue.
        for t in tickers:
            if t not in level_0_values:
                continue
            # Copy the raw data for the ticker and add the ticker column.
            sub = raw[t].copy()
            sub["ticker"] = t
            # Reset the index and rename the date column.
            sub = sub.reset_index().rename(columns={"Date": "date"})
            # Append the sub DataFrame to the rows list.
            rows.append(sub)
        # Concatenate the rows list into a single DataFrame.
        out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    # If the raw data is not a MultiIndex, reset the index and rename the date column.
    else:
        out = raw.reset_index().rename(columns={"Date": "date"})
        # Add the ticker column.
        out["ticker"] = tickers[0] if tickers else None

    # If the output DataFrame is not empty, lowercase the column names.
    if not out.empty:
        out.columns = [c.lower().replace(" ", "_") for c in out.columns]
    # Return the output DataFrame.
    return out

# (private) Helper for applying the DAYS_BACK environment variable to the config.
def _apply_days_back_env(cfg: Config) -> None:
    """Apply DAYS_BACK env var override to cfg if set."""
    days_back_env = os.environ.get("DAYS_BACK")
    if days_back_env:
        try:
            cfg.days_back = int(days_back_env)
            if cfg.days_back <= 0:
                raise ValueError
        except ValueError:
            raise SystemExit("Invalid DAYS_BACK value. Use a positive integer, e.g. DAYS_BACK=30.")

def _get_date_range(cfg: Config) -> tuple[datetime, datetime]:
    """Get the date range from env vars and config. End date must be resolved first for DAYS_BACK fallback."""
    fixed_end = os.environ.get("FIXED_END_DATE")
    fixed_start = os.environ.get("FIXED_START_DATE")
    # Resolve end_dt first (needed when deriving start_dt from DAYS_BACK)
    if fixed_end:
        end_dt = datetime.strptime(fixed_end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        end_dt = utc_now()
    if fixed_start:
        start_dt = datetime.strptime(fixed_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start_dt = end_dt - timedelta(days=cfg.days_back)
    return start_dt, end_dt

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest GDELT articles and OHLCV prices.")
    parser.add_argument(
        "--skip-gdelt",
        action="store_true",
        help="Skip GDELT fetch; keep existing gdelt_articles.csv and refresh prices only. Requires data/raw/gdelt_articles.csv to exist.",
    )
    return parser.parse_args()


# Main function for the data ingestion script.
def main() -> None:
    args = _parse_args()
    cfg = Config()
    project_root = get_project_root()
    out_dir = (project_root / cfg.out_dir).resolve()
    ensure_dir(str(out_dir))

    # Create the archive directory.
    archive_dir = out_dir / "archive"
    snapshots_dir = out_dir / "snapshots"

    # Apply the DAYS_BACK environment variable to the config.
    _apply_days_back_env(cfg)

    # Get the date range from the config.
    start_dt, end_dt = _get_date_range(cfg)
    date_str = end_dt.strftime("%Y-%m-%d")

    # Clamp the end date to the last trading day so weekend/holiday runs don't fetch articles we can't join.
    gdelt_end_dt = _last_trading_day_on_or_before(end_dt)
    clamped = gdelt_end_dt.date() < end_dt.date()
    print(f"[Ingestion] script_version={SCRIPT_VERSION} gdelt_end_clamped={clamped}")

    # If the end date was clamped, print the clamped date and the requested date.
    if clamped:
        print(f"[Ingestion] GDELT end clamped to last trading day {gdelt_end_dt.date().isoformat()} (requested {end_dt.date().isoformat()})")
    # Print the requested date range.
    print(f"[Ingestion] Requested date range: {start_dt.date().isoformat()} to {end_dt.date().isoformat()} (UTC)")
    articles_path = out_dir / "gdelt_articles.csv"

    if args.skip_gdelt:
        if not articles_path.exists():
            raise SystemExit(
                f"ERROR: --skip-gdelt requires existing {articles_path}. Run without --skip-gdelt first to fetch GDELT data."
            )
        print(f"[Ingestion] Skipping GDELT (--skip-gdelt); using existing {articles_path.name}")
        articles_df = pd.read_csv(articles_path)
    else:
        use_bigquery = os.environ.get("GDELT_SOURCE", "").lower() == "bigquery"

        if use_bigquery:
            print("[GDELT] Using BigQuery backend (GDELT_SOURCE=bigquery)")
            article_frames = []
            for company, ticker in MAG7.items():
                print(f"[GDELT] Fetching articles for {company} ({ticker}) from BigQuery ...")
                df = _fetch_gdelt_bigquery(
                    company=company,
                    ticker=ticker,
                    start_dt=start_dt,
                    end_dt=gdelt_end_dt,
                    max_articles=cfg.max_articles_per_company,
                )
                if not df.empty and "url" in df.columns:
                    df = df.drop_duplicates(subset=["url"], keep="last").reset_index(drop=True)
                article_frames.append(df)
            articles_df = pd.concat(article_frames, ignore_index=True) if article_frames else pd.DataFrame()
        else:
            # REST API backend
            headers = {"User-Agent": cfg.user_agent}
            per_pass = max(1, cfg.max_articles_per_company // 2)
            article_frames = []
            for company, ticker in MAG7.items():
                base_query = f"""
        ("{company}" OR {ticker}) (stock OR shares OR earnings OR revenue)
        """
                query = COMPANY_QUERY_OVERRIDES.get(company, base_query)
                print(f"[GDELT] Fetching articles for {company} ({ticker}) [oldest then newest] ...")

                df_old = _fetch_gdelt_articles(
                    query=query,
                    start_dt=start_dt,
                    end_dt=gdelt_end_dt,
                    page_size=cfg.page_size,
                    max_articles=per_pass,
                    headers=headers,
                    sort_order="dateasc",
                )
                df_new = _fetch_gdelt_articles(
                    query=query,
                    start_dt=start_dt,
                    end_dt=gdelt_end_dt,
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
                time.sleep(3)

            articles_df = pd.concat(article_frames, ignore_index=True) if article_frames else pd.DataFrame()

    # If the DataFrame is not empty and the seendate column exists, print the minimum and maximum seendate dates.
    if not articles_df.empty and "seendate" in articles_df.columns:
        art_min = articles_df["seendate"].min()
        art_max = articles_df["seendate"].max()
        print(f"[Ingestion] GDELT article date range in output: {pd.Timestamp(art_min).date()} to {pd.Timestamp(art_max).date()}")

    # Archive and write articles only when we fetched new GDELT data.
    if not args.skip_gdelt:
        _archive_if_exists(articles_path, archive_dir, date_str, "gdelt_articles")
        articles_df.to_csv(articles_path, index=False)
        print(f"[OK] Wrote {len(articles_df):,} rows -> {articles_path}")
    else:
        print(f"[OK] Kept existing {articles_path.name} ({len(articles_df):,} rows)")

    # Fetch daily prices from yfinance.
    # Get the tickers from the MAG7 dict.
    tickers = list(MAG7.values())
    # Print the number of tickers being fetched.
    print(f"[Prices] Fetching daily OHLCV for {len(tickers)} tickers ...")
    prices_df = fetch_prices_daily(tickers=tickers, start_dt=start_dt, end_dt=end_dt)
    # Create the full path for the prices DataFrame.
    prices_path = out_dir / "prices_daily.csv"
    # Archive the prices DataFrame if it exists.
    _archive_if_exists(prices_path, archive_dir, date_str, "prices_daily")
    # Write the prices DataFrame to the prices path.
    prices_df.to_csv(prices_path, index=False)
    print(f"[OK] Wrote {len(prices_df):,} rows -> {prices_path}")

    # Create the snapshots directory if it doesn't exist.
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    # Create the full path for the manifest.
    manifest_path = snapshots_dir / f"run_manifest_{date_str}.json"
    # Create the manifest dictionary.
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
        "gdelt_skipped": args.skip_gdelt,
        "gdelt_source": os.environ.get("GDELT_SOURCE", "rest"),
        "notes": "GDELT skipped (--skip-gdelt)" if args.skip_gdelt else (
            "GDELT from BigQuery" if os.environ.get("GDELT_SOURCE", "").lower() == "bigquery" else ""
        ),
    }
    # Write the manifest to the manifest path.
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Wrote run manifest -> {manifest_path}")

    # Print the article counts by ticker.
    if not articles_df.empty and "ticker" in articles_df.columns:
        print("\nArticle counts by ticker:")
        count_col = "url" if "url" in articles_df.columns else articles_df.columns[0]
        print(articles_df.groupby("ticker")[count_col].count().sort_values(ascending=False).to_string())

    if not prices_df.empty and "ticker" in prices_df.columns and "date" in prices_df.columns:
        print("\nPrice rows by ticker:")
        print(prices_df.groupby("ticker")["date"].count().sort_values(ascending=False).to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
