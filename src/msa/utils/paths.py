from pathlib import Path

_FMTS = frozenset(("csv", "parquet"))


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_data_root() -> Path:
    return get_project_root() / "data"


def get_raw_data_path() -> Path:
    return get_data_root() / "raw"


def get_processed_data_path() -> Path:
    return get_data_root() / "processed"


def _artifact(name: str, fmt: str) -> Path:
    if fmt not in _FMTS:
        raise ValueError(f"fmt must be one of {sorted(_FMTS)}")
    return get_processed_data_path() / f"{name}.{fmt}"


def get_joined_dataset(fmt: str = "csv") -> Path:
    """``data/processed/gdelt_ohlcv_join.<fmt>`` (default join, not FinBERT)."""
    return _artifact("gdelt_ohlcv_join", fmt)


def get_gdelt_with_sentiment(fmt: str = "csv") -> Path:
    return _artifact("gdelt_articles_with_sentiment", fmt)


def get_prices_daily_accumulated(fmt: str = "parquet") -> Path:
    """Default ``parquet``; pass ``\"csv\"`` for CSV."""
    return _artifact("prices_daily_accumulated", fmt)


def get_joined_dataset_finbert(fmt: str = "parquet") -> Path:
    """Default ``parquet``; pass ``\"csv\"`` if you only have CSV."""
    return _artifact("gdelt_ohlcv_join_finbert", fmt)


def get_model_selection_outputs_path() -> Path:
    """Directory for model-selection notebook pickles (gitignored)."""
    return get_project_root() / "models" / "model_selection_outputs"
