import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import nbformat as nbf
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
FILE_PATH = Path("data/processed/prices_daily_clean.csv")
NB_PATH = Path("docs/eda/sprint_2/ohlcv_eda_summary.ipynb")
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# DATA ANALYSIS
# ============================================================
df = pd.read_csv(FILE_PATH)

# 1. Pivot and Calculate Log Returns
pivot_df = df.pivot(index='date', columns='ticker', values='close')
log_returns = np.log(pivot_df / pivot_df.shift(1)).dropna()

# 2. Cumulative Returns
cum_returns = (1 + log_returns).cumprod()

# ============================================================
# NOTEBOOK GENERATION
# ============================================================
nb = nbf.v4.new_notebook()

# Define Markdown Summary based on your latest charts
summary_md = """# OHLCV Sprint 2 EDA Summary

## Core Insights

### 1. Performance Leaders and Laggards
- **Top Performer:** **AMZN** led the group, ending with a multiplier near **1.10** (~10% gain).
- **Underperformer:** **TSLA** showed significant weakness, dropping over 5% during the period.
- **Divergence:** AAPL and TSLA trended downward while AMZN and GOOGL moved upward, showing a split in Tech sector performance.

### 2. Risk and Volatility
- **High Risk:** **TSLA** and **NVDA** exhibit the highest standard deviation of returns (volatility).
- **Stable Assets:** **AAPL** and **MSFT** remain the least volatile, acting as stabilizing "blue-chip" anchors.

### 3. Correlation Dynamics
- **Hedge Potential:** **AAPL and AMZN** have a significant negative correlation (**-0.42**), making them excellent pairs for diversification.
- **Sector Links:** **GOOGL and NVDA** show the strongest positive link (**0.68**).
"""

# Define the Code Cell to reproduce the charts
code_content = f"""import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Load and process
df = pd.read_csv('{FILE_PATH.as_posix()}')
pivot_df = df.pivot(index='date', columns='ticker', values='close')
log_returns = np.log(pivot_df / pivot_df.shift(1)).dropna()
cum_returns = (1 + log_returns).cumprod()

# Plotting
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
plt.subplots_adjust(hspace=0.4)

sns.heatmap(log_returns.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=axes[0,0])
axes[0,0].set_title('Ticker Correlation Matrix (Log Returns)')

cum_returns.plot(ax=axes[0,1])
axes[0,1].set_title('Cumulative Returns (Growth of $1)')
axes[0,1].set_ylabel('Multiplier')

log_returns.std().sort_values().plot(kind='barh', ax=axes[1,1], color='skyblue')
axes[1,1].set_title('Standard Deviation of Returns (Volatility/Risk)')

plt.show()"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(summary_md),
    nbf.v4.new_code_cell(code_content)
]

with open(NB_PATH, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

# ============================================================
# LOCAL VISUALIZATION (Original Script Logic)
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
plt.subplots_adjust(hspace=0.4)

sns.heatmap(log_returns.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=axes[0,0])
axes[0,0].set_title('Ticker Correlation Matrix (Log Returns)')

cum_returns.plot(ax=axes[0,1])
axes[0,1].set_title('Cumulative Returns (Growth of $1)')
axes[0,1].set_ylabel('Multiplier')

log_returns.std().sort_values().plot(kind='barh', ax=axes[1,1], color='skyblue')
axes[1,1].set_title('Standard Deviation of Returns (Volatility/Risk)')

print(f"[OK] Generated summary notebook at: {NB_PATH}")
plt.show()