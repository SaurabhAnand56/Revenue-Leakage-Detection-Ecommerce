"""
Revenue Leakage Detection - Step 3: Exploratory Data Analysis
Generates 6 publication-ready charts saved to outputs/charts/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

DATA_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_data.csv')
CHART_DIR  = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

PALETTE = {
    'danger' : '#E63946',
    'warning': '#F4A261',
    'ok'     : '#2A9D8F',
    'neutral': '#457B9D',
    'bg'     : '#1A1A2E',
    'panel'  : '#16213E',
    'text'   : '#E0E0E0',
}

def set_style():
    plt.rcParams.update({
        'figure.facecolor' : PALETTE['bg'],
        'axes.facecolor'   : PALETTE['panel'],
        'axes.edgecolor'   : '#444',
        'axes.labelcolor'  : PALETTE['text'],
        'xtick.color'      : PALETTE['text'],
        'ytick.color'      : PALETTE['text'],
        'text.color'       : PALETTE['text'],
        'grid.color'       : '#2a2a4a',
        'grid.linestyle'   : '--',
        'grid.alpha'       : 0.5,
        'font.family'      : 'DejaVu Sans',
        'figure.dpi'       : 150,
    })

set_style()


def chart1_discount_distribution(df):
    """Distribution of discount percentages with risk zones."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axvspan(40, 100, alpha=0.15, color=PALETTE['danger'], label='High-Risk Zone (>40%)')
    ax.axvspan(0, 40,  alpha=0.08, color=PALETTE['ok'],     label='Safe Zone (<40%)')
    
    ax.hist(df['discount_pct_calc'].dropna(), bins=60, color=PALETTE['neutral'],
            edgecolor='#0d0d1e', linewidth=0.4)
    ax.axvline(df['discount_pct_calc'].mean(), color=PALETTE['warning'],
               linewidth=2, linestyle='--', label=f"Mean: {df['discount_pct_calc'].mean():.1f}%")
    
    ax.set_title('Discount % Distribution Across All Products', fontsize=14, pad=12)
    ax.set_xlabel('Discount Percentage (%)')
    ax.set_ylabel('Number of Products')
    ax.legend(framealpha=0.2)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart1_discount_distribution.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def chart2_revenue_at_risk_by_category(df):
    """Revenue at risk by sub-category — horizontal bar."""
    grp = df.groupby('sub_category')['revenue_at_risk'].sum().sort_values(ascending=True)
    grp = grp[grp > 0].tail(12)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [PALETTE['danger'] if v > grp.quantile(0.75) else PALETTE['warning']
              if v > grp.quantile(0.5) else PALETTE['neutral'] for v in grp.values]
    
    bars = ax.barh(grp.index, grp.values / 1e6, color=colors, edgecolor='none', height=0.65)
    for bar, val in zip(bars, grp.values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                f'₹{val/1e6:.1f}M', va='center', fontsize=9, color=PALETTE['text'])
    
    ax.set_title('Revenue at Risk by Sub-Category\n(Products with >40% Discount)', fontsize=14, pad=12)
    ax.set_xlabel('Revenue at Risk (₹ Millions)')
    ax.grid(axis='x', alpha=0.4)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart2_revenue_at_risk_category.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def chart3_discount_vs_rating(df):
    """Scatter: Discount % vs Rating with density."""
    sample = df.sample(min(3000, len(df)), random_state=42)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(sample['discount_pct_calc'], sample['average_rating'],
                    c=sample['selling_price'], cmap='plasma',
                    alpha=0.4, s=15, linewidths=0)
    
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Selling Price (₹)', color=PALETTE['text'])
    cbar.ax.yaxis.set_tick_params(color=PALETTE['text'])
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=PALETTE['text'])
    
    ax.axvline(40, color=PALETTE['danger'], linewidth=1.5,
               linestyle='--', label='40% Risk Threshold')
    
    # Regression line
    z = np.polyfit(sample['discount_pct_calc'].dropna(),
                   sample.loc[sample['discount_pct_calc'].notna(), 'average_rating'], 1)
    xp = np.linspace(0, 90, 100)
    ax.plot(xp, np.poly1d(z)(xp), color=PALETTE['ok'], linewidth=2, label='Trend')
    
    ax.set_title('Discount % vs Product Rating\n(colored by Selling Price)', fontsize=14, pad=12)
    ax.set_xlabel('Discount Percentage (%)')
    ax.set_ylabel('Average Rating (out of 5)')
    ax.legend(framealpha=0.2)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart3_discount_vs_rating.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def chart4_price_tier_heatmap(df):
    """Heatmap: price tier vs sub-category — avg discount."""
    top_subs = df['sub_category'].value_counts().head(8).index
    sub_df = df[df['sub_category'].isin(top_subs)]
    
    pivot = sub_df.pivot_table(
        values='discount_pct_calc',
        index='price_tier',
        columns='sub_category',
        aggfunc='mean'
    ).round(1)
    
    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn_r',
                linewidths=0.5, linecolor='#0d0d1e',
                ax=ax, cbar_kws={'label': 'Avg Discount %'})
    
    ax.set_title('Average Discount % — Price Tier × Sub-Category', fontsize=14, pad=12)
    ax.set_xlabel('')
    ax.set_ylabel('Price Tier')
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart4_discount_heatmap.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def chart5_top_risky_sellers(df):
    """Top 10 sellers by revenue at risk."""
    grp = (df.groupby('seller')['revenue_at_risk'].sum()
             .sort_values(ascending=False).head(10))
    
    fig, ax = plt.subplots(figsize=(12, 5))
    bars = ax.bar(range(len(grp)), grp.values / 1000,
                  color=[PALETTE['danger'] if i < 3 else PALETTE['warning']
                         if i < 6 else PALETTE['neutral'] for i in range(len(grp))],
                  edgecolor='none', width=0.6)
    
    ax.set_xticks(range(len(grp)))
    ax.set_xticklabels(grp.index, rotation=35, ha='right', fontsize=9)
    for bar, val in zip(bars, grp.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'₹{val/1000:.0f}K', ha='center', fontsize=8)
    
    ax.set_title('Top 10 Sellers by Revenue at Risk (₹K)', fontsize=14, pad=12)
    ax.set_ylabel('Revenue at Risk (₹ Thousands)')
    ax.grid(axis='y', alpha=0.4)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart5_top_risky_sellers.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def chart6_oos_impact(df):
    """Out-of-stock items vs in-stock: rating and price comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    oos_labels = ['In Stock', 'Out of Stock']
    
    # Rating comparison
    ratings = [df[df['out_of_stock']==False]['average_rating'].mean(),
               df[df['out_of_stock']==True]['average_rating'].mean()]
    axes[0].bar(oos_labels, ratings,
                color=[PALETTE['ok'], PALETTE['danger']], width=0.4)
    for i, v in enumerate(ratings):
        axes[0].text(i, v + 0.01, f'{v:.2f}', ha='center', fontsize=11)
    axes[0].set_title('Avg Rating: In-Stock vs Out-of-Stock')
    axes[0].set_ylabel('Average Rating')
    axes[0].set_ylim(0, 5)
    
    # Price comparison
    prices = [df[df['out_of_stock']==False]['selling_price'].median(),
              df[df['out_of_stock']==True]['selling_price'].median()]
    axes[1].bar(oos_labels, prices,
                color=[PALETTE['ok'], PALETTE['danger']], width=0.4)
    for i, v in enumerate(prices):
        axes[1].text(i, v + 5, f'₹{v:.0f}', ha='center', fontsize=11)
    axes[1].set_title('Median Selling Price: In-Stock vs Out-of-Stock')
    axes[1].set_ylabel('Median Selling Price (₹)')
    
    fig.suptitle('Out-of-Stock Impact Analysis', fontsize=14, y=1.01)
    plt.tight_layout()
    path = os.path.join(CHART_DIR, 'chart6_oos_impact.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path}")


def print_key_insights(df):
    print("\n" + "="*60)
    print("  KEY BUSINESS INSIGHTS")
    print("="*60)
    total_risk = df['revenue_at_risk'].sum()
    pct_over_discount = (df['high_discount_flag'].sum() / len(df)) * 100
    top_cat = df.groupby('sub_category')['revenue_at_risk'].sum().idxmax()
    top_seller = df.groupby('seller')['revenue_at_risk'].sum().idxmax()
    oos_loss = df[df['out_of_stock']==True]['selling_price'].sum()
    
    print(f"1. Total revenue at risk (>40% discount): ₹{total_risk:,.0f}")
    print(f"2. {pct_over_discount:.1f}% of all products are over-discounted (>40%)")
    print(f"3. Highest-risk sub-category         : {top_cat}")
    print(f"4. Highest-risk seller               : {top_seller}")
    print(f"5. Potential OOS revenue loss        : ₹{oos_loss:,.0f}")
    print(f"6. Average discount across platform  : {df['discount_pct_calc'].mean():.1f}%")
    print("="*60)


def main():
    df = pd.read_csv(DATA_PATH)
    
    print("Generating EDA charts...")
    chart1_discount_distribution(df)
    chart2_revenue_at_risk_by_category(df)
    chart3_discount_vs_rating(df)
    chart4_price_tier_heatmap(df)
    chart5_top_risky_sellers(df)
    chart6_oos_impact(df)
    print_key_insights(df)
    print(f"\nAll charts saved to: {CHART_DIR}")


if __name__ == '__main__':
    main()
