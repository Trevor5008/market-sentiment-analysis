import pandas as pd
from pathlib import Path
from msa import path_list as pl
import pandas as pd


__audit_log = []
__pre_set = False


def pre(df_name:str, df:pd.DataFrame, step:str):
    # Record the dataframe state before a filtering step.
    
    global __pre_set

    __audit_log.append({
        "previous df": df_name,
        "step": step,
        "rows_before": len(df)
    })

    __pre_set = True 


def post(df_name:str, df:pd.DataFrame):
    # Complete the latest audit record with the row count after filtering.

    global __pre_set


    if not __pre_set:
        raise ValueError("\"post\" function used before \"pre\" function.")
    
    if not __audit_log:
        raise ValueError("\"post\" function used before \"pre\" function.")

    __audit_log[-1]["df"] = [df_name]
    __audit_log[-1]["rows_after"] = [len(df)]

    if __audit_log.count(__audit_log[-1]) > 1:
        __audit_log.remove(__audit_log[-1])
        raise ValueError("Duplicated step")
    
    
    __pre_set = False


def export(file_name: str):
    
    if not __audit_log:
        raise ValueError("No filtering steps auditted.")
    return pd.DataFrame(__audit_log).to_csv(pl.PROJECT_ROOT/"data"/"audits"/f"{file_name}_row_audit.csv", index=False)

def reset():
    __audit_log.clear()
    print("Audit cleared.")