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
st.dataframe(df.head(20), height=600, width=1200)

st.subheader("Model Selection Summary")

st.markdown("""
### Key findings
- Strongest standalone signal: **mom_1d** (1-day momentum)
- Raw sentiment alone was **not significant**
- Sentiment × momentum interaction was significant
- Composite signal achieved **rho ≈ +0.097 to +0.098**
- Q5–Q1 spread was approximately **0.6%–0.8% per day**
""")

# TODO: Add a table of the signal discovery table -> current hardcoded values
signal_df = pd.DataFrame([
    {"Signal": "mom_1d", "Spearman rho": 0.167, "p_value": 0.0000, "Significant": "Yes"},
    {"Signal": "volume_z", "Spearman rho": 0.057, "p_value": 0.0386, "Significant": "Yes"},
    {"Signal": "mom_5d", "Spearman rho": 0.063, "p_value": 0.0094, "Significant": "Yes"},
    {"Signal": "sent_x_mom", "Spearman rho": -0.056, "p_value": 0.0210, "Significant": "Yes"},
    {"Signal": "mean_sent", "Spearman rho": -0.026, "p_value": 0.2778, "Significant": "No"},
])

st.write("Signal discovery")
st.dataframe(signal_df, height=600, width=1200)

# TODO: Add a table of the leaderboard table -> current hardcoded values
leaderboard_df = pd.DataFrame([
    {"Target": "beat_market", "Model": "Tuned LightGBM (held-out)", "AUC": 0.6075, "Accuracy": 0.6013},
    {"Target": "beat_market", "Model": "Ensemble XGB+LGBM (held-out)", "AUC": 0.6070, "Accuracy": 0.5981},
    {"Target": "beat_market", "Model": "Tuned XGBoost (held-out)", "AUC": 0.6068, "Accuracy": 0.5498},
    {"Target": "beat_market", "Model": "Walk-forward XGBoost", "AUC": 0.5858, "Accuracy": 0.5536},
    {"Target": "direction", "Model": "LogReg_L2 (top)", "AUC": 0.5543, "Accuracy": 0.5321},
])

st.write("Top model results")
st.dataframe(leaderboard_df, height=600, width=1200)

# TODO: Add a table of the top models for each target -> current hardcoded values
st.markdown("""
### Interpretation
- **Momentum is the primary signal**
- **beat_market** is more predictable than raw direction
- Tree models outperformed logistic regression
- Held-out AUC around **0.60–0.61** is solid for liquid large-cap stocks
- Walk-forward performance is lower, but is a more honest estimate
""")

st.subheader("Basic Info")
col1, col2, col3 = st.columns(3)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", df.shape[1])
col3.metric("Date Range Available", "Yes" if "price_date" in df.columns else "No")