"""
Revenue Leakage Detection - Step 1: Data Cleaning & Feature Engineering
Dataset: Flipkart E-Commerce Product Listings
"""

import pandas as pd
import numpy as np
import re
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'flipkart_products.xlsx')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_data.csv')


def load_data(path):
    df = pd.read_excel(path)
    print(f"Raw data shape: {df.shape}")
    return df


def clean_price(val):
    """Strip commas, convert to float."""
    if pd.isna(val):
        return np.nan
    return float(str(val).replace(',', '').strip())


def extract_discount_pct(val):
    """Extract numeric discount percentage from strings like '69% off'."""
    if pd.isna(val):
        return np.nan
    match = re.search(r'(\d+)\s*%', str(val))
    return float(match.group(1)) if match else np.nan


def clean_data(df):
    # ── Column rename: 'discount' column actually contains description text due to CSV shift
    # Real discount % is in the 'description' column, actual description is in 'discount' col
    df = df.rename(columns={
        'description': 'discount_text',
        'discount': 'product_description'
    })

    # ── Price cleaning
    df['actual_price'] = df['actual_price'].apply(clean_price)
    df['selling_price'] = df['selling_price'].apply(clean_price)

    # ── Extract discount %
    df['discount_pct'] = df['discount_text'].apply(extract_discount_pct)

    # ── Remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['pid'])
    print(f"Duplicates removed: {before - len(df)}")

    # ── Drop rows with missing prices
    df = df.dropna(subset=['actual_price', 'selling_price'])
    print(f"After price null drop: {df.shape}")

    # ── Fix out_of_stock type
    df['out_of_stock'] = df['out_of_stock'].astype(bool)

    # ── Derived columns
    df['discount_amount']   = df['actual_price'] - df['selling_price']
    df['discount_pct_calc'] = ((df['discount_amount'] / df['actual_price']) * 100).round(2)
    df['revenue_at_risk']   = np.where(df['discount_pct_calc'] > 40, df['discount_amount'], 0)
    df['price_tier'] = pd.cut(
        df['selling_price'],
        bins=[0, 500, 1500, 5000, np.inf],
        labels=['Budget (<500)', 'Mid (500-1500)', 'Premium (1500-5000)', 'Luxury (5000+)']
    )
    df['high_discount_flag'] = df['discount_pct_calc'] > 40
    df['out_of_stock_loss']  = np.where(df['out_of_stock'], df['selling_price'], 0)

    # ── Clean category strings
    df['category']    = df['category'].str.strip()
    df['sub_category'] = df['sub_category'].str.strip()
    df['brand']       = df['brand'].str.strip().str.title()

    return df


def summarize(df):
    print("\n====== DATA SUMMARY ======")
    print(f"Total products       : {len(df):,}")
    print(f"Unique categories    : {df['category'].nunique()}")
    print(f"Unique sub-categories: {df['sub_category'].nunique()}")
    print(f"Unique brands        : {df['brand'].nunique()}")
    print(f"Out-of-stock items   : {df['out_of_stock'].sum():,}")
    print(f"High-discount items  : {df['high_discount_flag'].sum():,} (>40%)")
    print(f"Avg discount %       : {df['discount_pct_calc'].mean():.1f}%")
    print(f"Total revenue at risk: ₹{df['revenue_at_risk'].sum():,.0f}")
    print(f"\nPrice tier distribution:\n{df['price_tier'].value_counts()}")


def main():
    df = load_data(DATA_PATH)
    df = clean_data(df)
    summarize(df)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nCleaned data saved → {OUTPUT_PATH}")
    return df


if __name__ == '__main__':
    main()
