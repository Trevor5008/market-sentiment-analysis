import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Market Sentiment Analysis", layout="wide")

st.title("Market Sentiment Analysis Dashboard")
st.write("Starter UI for exploring project outputs.")

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "analysis" / "structural" / "correlation_summary.csv"

uploaded_file = st.file_uploader("Upload a CSV or Parquet file", type=["csv", "parquet"])

df = None

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_parquet(uploaded_file)
    st.success(f"Loaded uploaded file with {len(df):,} rows")

elif DEFAULT_CSV.exists():
    df = pd.read_csv(DEFAULT_CSV)
    st.success(f"Loaded default file: {DEFAULT_CSV.name} ({len(df):,} rows)")

else:
    st.warning("No file uploaded and no default project file found.")
    st.stop()

st.subheader("Columns")
st.write(list(df.columns))

st.subheader("Preview")
st.dataframe(df.head(20), use_container_width=True)

st.subheader("Basic Info")
col1, col2, col3 = st.columns(3)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", df.shape[1])
col3.metric("Date Range Available", "Yes" if "price_date" in df.columns else "No")