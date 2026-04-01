# DataFrame Filter Audit

## What this is

`msa.audit` is a simple tool to help you keep track of what happens to your dataframes when you filter them.

It’s mainly useful in notebooks where dataframes from old cells are used to create new dataframs. This get messy and non-linear.

This helps you track:

* what dataframe you started with
* what step you applied
* how many rows you had before and after
* what the new dataframe is called

**It basically keeps a record of your filtering steps so you don’t lose track of your data.**

---

## Import

```python
from msa import audit
```

You don’t need to import anything from deep inside the package.

---

## How it works (simple)

Every filtering step has 2 parts:

1. `audit.pre(...)`  before you filter
2. `filtering method`
3. `audit.post(...)`  after you filter

Think of it like: 

“I’m about to do something” -> do it -> “here’s what happened”

---

## Functions

### `audit.pre(df_name, df, step)`

Call this **right before** you filter.

**What you pass:**

* `df_name`: name of the current dataframe
* `df`: the dataframe itself
* `step`: what you’re about to do

**Example:**

```python
audit.pre("df_raw", df_raw, "drop missing headlines")
```

---

### `audit.post(df_name, df)`

Call this **right after** your filtering step.

**What you pass:**

* `df_name`: name of the new dataframe
* `df`: the filtered dataframe

**Example:**

```python
audit.post("df_headlines", df_headlines)
```

---

### `audit.export(file_name)`

Saves everything to a CSV:

```
data/audits/{file_name}_row_audit.csv
```

**Example:**

```python
audit.export("gdelt_cleaning")
```

---

### `audit.reset()`

Clears everything so you can start fresh.

**Example:**

```python
audit.reset()
```

---

## Example

```python
from msa import audit

audit.reset()

audit.pre("df_raw", df_raw, "Apple ticker filter")
df_aapl = df_raw[df_raw["ticker"] == "Apple"].copy()
audit.post("df_aapl", df_aapl)

audit.pre("df_aapl", df_aapl, "groupby domain")
source_counts = df_aapl.groupby("domain").size().sort_values(ascending=False)

audit.post("source_counts", source_counts)

audit.export("gdelt_filter_steps")
```