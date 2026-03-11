from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]

def get_data_root() -> Path:
    return get_project_root() / "data"

def get_raw_data_path() -> Path:
    return get_data_root() / "raw"

def get_processed_data_path() -> Path:
    return get_data_root() / "processed"

def get_joined_dataset(fmt: str = "csv") -> Path:
    """Path to news–price join. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "gdelt_ohlcv_join"
    return Path(f"{base}.{fmt}")

def get_gdelt_with_sentiment(fmt: str = "csv") -> Path:
    """Path to GDELT articles with sentiment. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "gdelt_articles_with_sentiment"
    return Path(f"{base}.{fmt}")

def get_prices_daily_accumulated(fmt: str = "csv") -> Path:
    """Path to accumulated daily prices. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "prices_daily_accumulated"
    return Path(f"{base}.{fmt}")