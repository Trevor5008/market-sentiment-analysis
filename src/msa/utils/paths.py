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
    return get_processed_data_path() / "gdelt_ohlcv_join.csv"