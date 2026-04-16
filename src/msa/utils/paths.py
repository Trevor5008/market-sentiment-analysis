from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_data_root() -> Path:
    return get_project_root() / "data"


def get_raw_data_path() -> Path:
    return get_data_root() / "raw"


def get_processed_data_path() -> Path:
    return get_data_root() / "processed"


def get_joined_dataset() -> Path:
    """Path to news–price join. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "gdelt_ohlcv_join"
    return base


def get_gdelt_with_sentiment() -> Path:
    """Path to GDELT articles with sentiment. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "gdelt_articles_with_sentiment"
    return base


def get_prices_daily_accumulated() -> Path:
    """Path to accumulated daily prices. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "prices_daily_accumulated"
    return base


def get_joined_dataset_finbert() -> Path:
    """Path to news+price join with FinBERT scores. fmt: 'csv' or 'parquet'."""
    base = get_processed_data_path() / "gdelt_ohlcv_join_finbert"
    return base


def get_model_selection_outputs_path() -> Path:
    """Directory for model-selection notebook pickles (gitignored)."""
    return get_project_root() / "models" / "model_selection_outputs"
