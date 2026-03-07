import pandas as pd
from pathlib import Path
audit_log = []

def collect(df, step):
    audit_log.append({
        "step": step,
        "rows": len(df)
    })

def export(file_name: str):
    return pd.DataFrame(audit_log).to_csv(f"{file_name}_row_audit.csv")

def reset():
    audit_log.clear()