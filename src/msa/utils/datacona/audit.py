import pandas as pd
from pathlib import Path
from msa import path_list as pl
import pandas as pd


_audit_log = []
_pre_set = False


def pre(df_name:str, df:pd.DataFrame, step:str):
    # Record the dataframe state before a filtering step.
    
    global _pre_set

    _audit_log.append({
        "previous df": df_name,
        "step": step,
        "rows_before": len(df)
    })

    _pre_set = True 


def post(df_name:str, df:pd.DataFrame):
    # Complete the latest audit record with the row count after filtering.

    global _pre_set


    if not _pre_set:
        raise ValueError("\"post\" function used before \"pre\" function.")
    
    if not _audit_log:
        raise ValueError("\"post\" function used before \"pre\" function.")

    _audit_log[-1]["df"] = [df_name]
    _audit_log[-1]["rows_after"] = [len(df)]

    if _audit_log.count(_audit_log[-1]) > 1:
        _audit_log.remove(_audit_log[-1])
        raise ValueError("Duplicated step")
    
    
    _pre_set = False


def export(file_name: str):
    if not _audit_log:
        raise ValueError("No filtering steps auditted.")
    return pd.DataFrame(_audit_log).to_csv(pl.PROJECT_ROOT/"data"/"audits"/f"{file_name}_row_audit.csv", index=False)

def reset():
    _audit_log.clear()
    print("Audit cleared.")