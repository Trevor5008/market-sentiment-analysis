from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

REQUIRED_COLS = [
    "seendate", "url", "title", "description", "language", "domain",
    "sourceCountry", "socialimage", "company", "ticker"
]

def load_gdelt(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["seendate"])
    return df

def validate_schema(df: pd.DataFrame) -> dict:
    cols = set(df.columns)
    missing = [c for c in REQUIRED_COLS if c not in cols]
    extra = [c for c in df.columns if c not in REQUIRED_COLS]
    return {"missing_required": missing, "extra_columns": extra}

def summarize(df: pd.DataFrame) -> dict:
    out = {}
    out["rows"] = int(len(df))
    out["cols"] = int(len(df.columns))

    out["date_min"] = str(df["seendate"].min()) if "seendate" in df else None
    out["date_max"] = str(df["seendate"].max()) if "seendate" in df else None

    # Missingness for required cols that exist
    missingness = {}
    for c in REQUIRED_COLS:
        if c in df.columns:
            missingness[c] = float(df[c].isna().mean())
    out["missingness_pct"] = {k: round(v * 100, 2) for k, v in missingness.items()}

    # Duplicates
    if "url" in df.columns:
        out["duplicate_url_count"] = int(df["url"].duplicated().sum())
        out["unique_url_count"] = int(df["url"].nunique())

    # Coverage
    if "ticker" in df.columns:
        out["articles_per_ticker"] = df["ticker"].value_counts().to_dict()

    # Language distribution
    if "language" in df.columns:
        out["language_counts"] = df["language"].value_counts().head(10).to_dict()

    # Domain concentration
    if "domain" in df.columns:
        out["top_domains"] = df["domain"].value_counts().head(10).to_dict()
        out["unique_domains"] = int(df["domain"].nunique())

    return out

def to_markdown_report(input_path: Path, schema: dict, stats: dict) -> str:
    lines = []
    lines.append("# GDELT Articles Validation Report")
    lines.append("")
    lines.append(f"**Input:** `{input_path.as_posix()}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Rows: **{stats.get('rows')}**")
    lines.append(f"- Columns: **{stats.get('cols')}**")
    lines.append(f"- Date range: **{stats.get('date_min')} → {stats.get('date_max')}**")
    lines.append("")
    lines.append("## Schema")
    lines.append(f"- Missing required columns: `{schema['missing_required']}`")
    lines.append(f"- Extra columns: `{schema['extra_columns']}`")
    lines.append("")
    lines.append("## Missingness (percent)")
    for k, v in stats.get("missingness_pct", {}).items():
        lines.append(f"- {k}: {v}%")
    lines.append("")
    lines.append("## Coverage")
    apt = stats.get("articles_per_ticker", {})
    if apt:
        lines.append("### Articles per ticker")
        for t, n in apt.items():
            lines.append(f"- {t}: {n}")
    lines.append("")
    lines.append("## Sources")
    td = stats.get("top_domains", {})
    if td:
        lines.append("### Top domains")
        for d, n in td.items():
            lines.append(f"- {d}: {n}")
        lines.append(f"- Unique domains: {stats.get('unique_domains')}")
    lines.append("")
    lines.append("## Notes / Caveats")
    lines.append("- GDELT coverage varies by company and time.")
    lines.append("- Syndication can create duplicate URLs or near-duplicates.")
    lines.append("- Non-English articles may appear depending on query.")
    lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/gdelt_articles.csv")
    parser.add_argument("--out", default="docs/validation/gdelt_articles_validation.md")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    df = load_gdelt(input_path)

    schema = validate_schema(df)
    stats = summarize(df)

    report = to_markdown_report(input_path, schema, stats)
    out_path.write_text(report, encoding="utf-8")

    print(f"[OK] Loaded {len(df):,} rows")
    print(f"[OK] Wrote report -> {out_path}")

    # Hard fail only if missing required columns or zero rows
    if len(df) == 0 or len(schema["missing_required"]) > 0:
        raise SystemExit(2)

if __name__ == "__main__":
    main()

