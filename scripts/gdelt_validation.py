import pandas as pd
import numpy as np
from pathlib import Path
import re
# Load the GDELT articles data
DATA_PATH = Path("../data/raw/gdelt_articles.csv")
df = pd.read_csv(DATA_PATH, parse_dates=["seendate"])
print(f"Loaded {len(df):,} rows from {DATA_PATH}")

RAW_DIR = DATA_PATH.parent                    # ../data/raw
PROCESSED_DIR = DATA_PATH.parent.parent / "processed"  # ../data/processed

# Build output filename from input
output_filename = DATA_PATH.stem + "_clean.csv"  # gdelt_articles_clean.csv
output_path = PROCESSED_DIR / output_filename

original_rows = len(df)
original_cols = len(df.columns)

# Preview first few rows
df.head()

df.shape #how many rows and columns we have 

#check all column names
df.columns

#check if any comand is null, missing or useful
df.info()

df.isnull().sum() #count all the missing values

#check how many percentage of missing values we have based on the whole dataset

(df.isnull().sum()/len(df)) * 100

df_clean = df.drop(columns=['description', 'sourceCountry'])
print(f"Before: {df.shape}")
print(f"After: {df_clean.shape}")


print(f"Duplicate rows: {df_clean.duplicated().sum()}")

print(f"Duplicate URL: {df_clean['url'].duplicated().sum()}")

duplicated_urls = df_clean[df_clean['url'].duplicated(keep=False)]
print(f"\nRows with duplicated urls: {len(duplicated_urls)}")

print(f"One example of duplicated urls:")
example_url = duplicated_urls['url'].iloc[0]
print(df_clean[df_clean['url'] == example_url] [['url', 'company', 'ticker']])

df_clean = df_clean.drop_duplicates(subset=['url', 'company'], keep='first')

print(f"Rows after removing duplicates: {len(df_clean):,}")
print(f"Unique URLs: {df_clean['url'].nunique():,}")

print(f"Earliest article: {df_clean['seendate'].min()}")
print(f"Latest article: {df_clean['seendate'].max()}")

#Calculate the span 
date_range = df_clean['seendate'].max() - df_clean['seendate'].min()
print(f"Date span: {date_range.days} days")

#Check for empty or short title
empty_titles = df_clean['title'].isna().sum()
print(f"Empty titles: {empty_titles}")

short_titles = (df_clean['title'].str.len() < 10).sum()
print(f"Very short titles (<10 chars): {short_titles}")

if short_titles > 0:
    print("\nShort titles found:")
    print(df_clean[df_clean['title'].str.len() < 10]['title'].values)

print("Language in data:")
print(df_clean['language'].value_counts())

#keep only english
df_clean = df_clean[df_clean['language'] == 'English']
print(f"\nRows after filtering to English: {len(df_clean)}")

print("Articles per company:")
print(df_clean['company'].value_counts())

valid_urls = df_clean['url'].str.startswith(('http://', 'https://')).all()
print(f"All URLs valid: {valid_urls}")

invalid = df_clean[~df_clean['url'].str.startswith(('http://', 'https://'))]
print(f"Invalid URLs: {len(invalid)}")

#Top 10 news sources - check for source bias
print("Top 10 domains:")
print(df_clean['domain'].value_counts().head(10))

# How many unique sources?
print(f"\nUnique domains: {df_clean['domain'].nunique()}")

#Some articles might not actually be about the company's stock/business:
financial_keywords = [
    # Stock & Trading
    'stock', 'share', 'shares', 'trading', 'trader', 'nasdaq', 'nyse', 
    's&p', 'dow', 'index', 'etf', 'fund', 'hedge',
    
    # Financial Metrics
    'earnings', 'revenue', 'profit', 'loss', 'margin', 'eps', 
    'guidance', 'forecast', 'outlook', 'quarter', 'quarterly',
    'annual', 'fiscal', 'billion', 'million', 'trillion',
    
    # Market Movement
    'bull', 'bear', 'rally', 'surge', 'soar', 'jump', 'climb',
    'drop', 'fall', 'crash', 'plunge', 'sink', 'tumble', 'volatile',
    'gain', 'rise', 'decline', 'dip',
    
    # Valuation
    'valuation', 'market cap', 'price target', 'rating', 'upgrade',
    'downgrade', 'buy', 'sell', 'hold', 'overweight', 'underweight',
    
    # Business Operations  
    'ceo', 'cfo', 'executive', 'board', 'investor', 'shareholder',
    'dividend', 'buyback', 'acquisition', 'merger', 'deal', 'partnership',
    'investment', 'ipo', 'stake',
    
    # Supply Chain & Operations
    'supplier', 'supply chain', 'manufacture', 'production', 'factory',
    'chip', 'semiconductor', 'shortage',
    
    # Tech-Specific
    'ai', 'artificial intelligence', 'cloud', 'software', 'hardware',
    'iphone', 'android', 'windows', 'azure', 'aws', 'gpu', 'data center',
    
    # MAG7 Company Names (catches articles about them)
    'apple', 'microsoft', 'google', 'alphabet', 'amazon', 'meta', 
    'facebook', 'tesla', 'nvidia', 'aapl', 'msft', 'googl', 'amzn', 
    'tsla', 'nvda',
    
    # Competition & Industry
    'competitor', 'rival', 'industry', 'sector', 'antitrust', 'regulation',
    'ces', 'tech trends', 'conference', 'keynote', 'announcement', 'launch', 'unveil'
]
def has_financial_keyword(title):
    title_lower = title.lower()
    for kw in financial_keywords:
        # Use word boundary \b to match whole words only
        if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
            return True
    return False
df_clean['is_relevant'] = df_clean['title'].apply(has_financial_keyword)

print(f"Articles with financial keywords: {df_clean['is_relevant'].sum()}")
print(f"Potential irrelevant: {(~df_clean['is_relevant']).sum()}")

# Preview potentially irrelevant articles
print("\nPotentially irrelevant titles:")
print(df_clean[~df_clean['is_relevant']]['title'].head(10).values)

#keep only relevant data 
df_clean = df_clean[df_clean['is_relevant'] ==  True]
print(f"Clean rows after relevance filter: {len(df_clean)}")

# Debug: Test the function directly
test_titles = [
    "20 Canadian albums we cant wait to hear in 2026",
    "Apple stock rises 5%",
    "How Hermès keeps its clutches on its own handbags"
]

for title in test_titles:
    result = has_financial_keyword(title)
    print(f"{result} <- '{title[:50]}'")

df_clean = df_clean[df_clean['is_relevant']==True]
df_clean = df_clean.drop(columns=['is_relevant', 'query' ])

df_clean.head(10)

from difflib import SequenceMatcher #comparing sequence

def similar(a,b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

#Find titles that >80% similar
titles = df_clean['title'].tolist()
near_dupes=[]
for i, t1 in enumerate(titles):
    for j, t2 in enumerate(titles[i+1:], i+1):
        if similar(t1, t2) > 0.8:
            near_dupes.append((t1,t2,similar(t1,t2)))

print(f"Found {len(near_dupes)} near duplicate pairs")
for t1, t2, score in near_dupes[:5]:
    print(f"\n{score:.0%} similar:")
    print(f"  1: {t1[:60]}...")
    print(f"  2: {t2[:60]}...")

# Check one of the duplicate titles
dupe_title = "Apple Is Losing Its Grip on the World Tech Supply Chain"
print(df_clean[df_clean['title'] == dupe_title][['title', 'company', 'ticker']])

# Save
df_clean.to_csv(output_path, index=False)
print(f"Saved {len(df_clean)} rows to {output_path}")

# All cleaning in one cell (near the end of notebook)
df_clean = df.copy()
df_clean = df_clean.drop(columns=['description', 'sourceCountry'])
df_clean = df_clean.drop_duplicates(subset=['url', 'company'], keep='first')
df_clean = df_clean[df_clean['language'] == 'English']
df_clean = df_clean[df_clean['title'].apply(has_financial_keyword)]
df_clean = df_clean.drop(columns=['query'])

print(f"Final clean data: {len(df_clean)} rows")

# Save immediately after
df_clean.to_csv(output_path, index=False)
print(f"Saved to {output_path}")
