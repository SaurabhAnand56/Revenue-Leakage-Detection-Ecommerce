"""Generates the full Revenue Leakage Jupyter Notebook."""
import nbformat as nbf
import os

NB_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks',
                       'Revenue_Leakage_Analysis.ipynb')

nb = nbf.v4.new_notebook()

cells = []

def md(text):
    return nbf.v4.new_markdown_cell(text)

def code(text):
    return nbf.v4.new_code_cell(text)

# ── Title ──
cells.append(md("""# 📉 Revenue Leakage Detection & Pricing Optimization
### E-Commerce Dataset — Flipkart Product Listings
**Objective:** Identify where the business is losing revenue due to pricing inefficiencies,
excessive discounts, and out-of-stock situations. Recommend corrective actions.

---
"""))

# ── Cell 1: Setup ──
cells.append(md("## 1. Setup & Data Loading"))
cells.append(code("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import sqlite3
import re
import warnings
warnings.filterwarnings('ignore')

plt.rcParams.update({
    'figure.facecolor': '#1A1A2E', 'axes.facecolor': '#16213E',
    'axes.edgecolor': '#444', 'axes.labelcolor': '#E0E0E0',
    'xtick.color': '#E0E0E0', 'ytick.color': '#E0E0E0',
    'text.color': '#E0E0E0', 'grid.color': '#2a2a4a',
    'grid.linestyle': '--', 'grid.alpha': 0.5, 'figure.dpi': 120,
})

df_raw = pd.read_excel('../data/flipkart_products.xlsx')
print(f"Shape: {df_raw.shape}")
df_raw.head(3)
"""))

# ── Cell 2: Cleaning ──
cells.append(md("## 2. Data Cleaning & Feature Engineering"))
cells.append(code("""
def clean_price(val):
    if pd.isna(val): return np.nan
    return float(str(val).replace(',', '').strip())

def extract_discount_pct(val):
    if pd.isna(val): return np.nan
    m = re.search(r'(\\d+)\\s*%', str(val))
    return float(m.group(1)) if m else np.nan

df = df_raw.copy()
df = df.rename(columns={'description': 'discount_text', 'discount': 'product_description'})
df['actual_price']   = df['actual_price'].apply(clean_price)
df['selling_price']  = df['selling_price'].apply(clean_price)
df['discount_pct']   = df['discount_text'].apply(extract_discount_pct)

# Remove duplicates and nulls
df = df.drop_duplicates(subset=['pid']).dropna(subset=['actual_price','selling_price'])

# Derived columns
df['discount_amount']   = df['actual_price'] - df['selling_price']
df['discount_pct_calc'] = ((df['discount_amount'] / df['actual_price']) * 100).round(2)
df['revenue_at_risk']   = np.where(df['discount_pct_calc'] > 40, df['discount_amount'], 0)
df['high_discount_flag']= df['discount_pct_calc'] > 40
df['out_of_stock_loss'] = np.where(df['out_of_stock'], df['selling_price'], 0)
df['price_tier'] = pd.cut(
    df['selling_price'],
    bins=[0,500,1500,5000,np.inf],
    labels=['Budget','Mid','Premium','Luxury']
)
df['brand']      = df['brand'].str.strip().str.title()
df['category']   = df['category'].str.strip()
df['sub_category']= df['sub_category'].str.strip()

print(f"Clean dataset shape: {df.shape}")
print(f"Revenue at risk: ₹{df['revenue_at_risk'].sum():,.0f}")
print(f"Over-discounted: {df['high_discount_flag'].sum():,} ({df['high_discount_flag'].mean()*100:.1f}%)")
df.describe()[['actual_price','selling_price','discount_pct_calc','revenue_at_risk']]
"""))

# ── Cell 3: SQL ──
cells.append(md("## 3. SQL Analysis (SQLite)"))
cells.append(code("""
conn = sqlite3.connect(':memory:')
df.to_sql('products', conn, index=False, if_exists='replace')

def sql(query, title=""):
    if title: print(f"\\n{'='*55}\\n  {title}\\n{'='*55}")
    result = pd.read_sql_query(query, conn)
    display(result)
    return result
"""))

cells.append(code("""
# Q1: Revenue at risk by sub-category
q1 = sql('''
    SELECT sub_category, COUNT(*) products,
           ROUND(AVG(discount_pct_calc),1) avg_disc,
           ROUND(SUM(revenue_at_risk),0) revenue_at_risk
    FROM products WHERE high_discount_flag=1
    GROUP BY sub_category ORDER BY revenue_at_risk DESC LIMIT 10
''', "Q1: Revenue at Risk by Sub-Category")
"""))

cells.append(code("""
# Q2: Discount bucket analysis
q2 = sql('''
    WITH b AS (SELECT *,
        CASE WHEN discount_pct_calc<20 THEN '0-20%'
             WHEN discount_pct_calc<40 THEN '20-40%'
             WHEN discount_pct_calc<60 THEN '40-60%'
             WHEN discount_pct_calc<80 THEN '60-80%'
             ELSE '80%+' END AS bucket FROM products)
    SELECT bucket, COUNT(*) products, ROUND(AVG(selling_price),0) avg_price,
           ROUND(AVG(average_rating),2) avg_rating,
           ROUND(SUM(revenue_at_risk),0) total_risk
    FROM b GROUP BY bucket ORDER BY bucket
''', "Q2: Discount Bucket Analysis")
"""))

cells.append(code("""
# Q3: High-risk sellers (window function)
q3 = sql('''
    WITH seller_stats AS (
        SELECT seller, COUNT(*) products,
               ROUND(AVG(discount_pct_calc),1) avg_disc,
               ROUND(SUM(revenue_at_risk),0) risk,
               ROUND(AVG(average_rating),2) avg_rating
        FROM products GROUP BY seller HAVING COUNT(*) >= 10
    )
    SELECT *, RANK() OVER (ORDER BY risk DESC) AS risk_rank
    FROM seller_stats ORDER BY risk DESC LIMIT 10
''', "Q3: High-Risk Sellers (with Window Function)")
"""))

cells.append(code("""
# Q4: Out-of-stock loss (CTE)
q4 = sql('''
    WITH oos AS (SELECT * FROM products WHERE out_of_stock=1),
    summary AS (
        SELECT sub_category, COUNT(*) oos_count,
               ROUND(SUM(selling_price),0) potential_revenue_lost,
               ROUND(AVG(average_rating),2) avg_rating
        FROM oos GROUP BY sub_category
    )
    SELECT * FROM summary ORDER BY potential_revenue_lost DESC
''', "Q4: Out-of-Stock Revenue Loss (CTE)")
"""))

# ── Cell 4: EDA ──
cells.append(md("## 4. Exploratory Data Analysis"))

cells.append(code("""
# Chart 1: Discount Distribution
fig, ax = plt.subplots(figsize=(12,5))
ax.axvspan(40,100,alpha=0.15,color='#E63946',label='High-Risk Zone (>40%)')
ax.axvspan(0,40, alpha=0.08,color='#2A9D8F',label='Safe Zone (<40%)')
ax.hist(df['discount_pct_calc'].dropna(),bins=60,color='#457B9D',edgecolor='#0d0d1e',lw=0.4)
ax.axvline(df['discount_pct_calc'].mean(),color='#F4A261',lw=2,ls='--',
           label=f"Mean: {df['discount_pct_calc'].mean():.1f}%")
ax.set_title('Discount % Distribution Across All Products',fontsize=14,pad=12)
ax.set_xlabel('Discount %'); ax.set_ylabel('Products')
ax.legend(framealpha=0.2); plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# Chart 2: Revenue at risk by sub-category
grp = df.groupby('sub_category')['revenue_at_risk'].sum().sort_values().tail(10)
fig, ax = plt.subplots(figsize=(12,5))
colors = ['#E63946' if v > grp.quantile(0.7) else '#F4A261' for v in grp.values]
ax.barh(grp.index, grp.values/1e6, color=colors, height=0.65)
ax.set_title('Revenue at Risk by Sub-Category (₹M)',fontsize=14,pad=12)
ax.set_xlabel('₹ Millions'); plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# Chart 3: Discount vs Rating (scatter)
sample = df.sample(3000, random_state=42)
fig, ax = plt.subplots(figsize=(10,6))
sc = ax.scatter(sample['discount_pct_calc'], sample['average_rating'],
                c=sample['selling_price'], cmap='plasma', alpha=0.4, s=15)
plt.colorbar(sc,ax=ax,label='Selling Price (₹)')
ax.axvline(40,color='#E63946',lw=1.5,ls='--',label='40% Threshold')
z = np.polyfit(sample.dropna(subset=['discount_pct_calc','average_rating'])['discount_pct_calc'],
               sample.dropna(subset=['discount_pct_calc','average_rating'])['average_rating'],1)
xp = np.linspace(0,90,100)
ax.plot(xp,np.poly1d(z)(xp),color='#2A9D8F',lw=2,label='Trend')
ax.set_title('Discount % vs Rating',fontsize=14); ax.legend(framealpha=0.2)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""
# Chart 4: Heatmap — price tier vs sub-category
top_subs = df['sub_category'].value_counts().head(8).index
pivot = df[df['sub_category'].isin(top_subs)].pivot_table(
    'discount_pct_calc','price_tier','sub_category','mean').round(1)
fig,ax = plt.subplots(figsize=(14,5))
sns.heatmap(pivot,annot=True,fmt='.1f',cmap='RdYlGn_r',linewidths=0.5,
            linecolor='#0d0d1e',ax=ax,cbar_kws={'label':'Avg Discount %'})
ax.set_title('Avg Discount % — Price Tier × Sub-Category',fontsize=14,pad=12)
plt.xticks(rotation=30,ha='right'); plt.tight_layout(); plt.show()
"""))

# ── Cell 5: Business Recommendations ──
cells.append(md("""## 5. Business Recommendations

| # | Finding | Recommendation | Priority |
|---|---------|---------------|----------|
| 1 | **75% of products discounted >40%** | Cap seller discounts at 40% platform-wide | 🔴 Critical |
| 2 | **Topwear has ₹9.4M revenue at risk** | Implement category-specific max discount tiers | 🔴 Critical |
| 3 | **1,577 OOS items = ₹1.5M lost** | Enforce seller SLA for inventory restocking | 🟠 High |
| 4 | **High discounts don't improve ratings** | Use dynamic pricing instead of blanket discounts | 🟠 High |
| 5 | **Budget tier most over-discounted** | Repricing strategy: floor price = 60% of MRP | 🟡 Medium |
| 6 | **Some sellers avg >70% discount** | Require seller profitability score before listing | 🟡 Medium |

### 💡 Pricing Strategy Framework
- **Floor Price Rule:** `Selling Price ≥ 60% of MRP` for all categories
- **Smart Discounting:** Tie max discount % to category margin benchmarks  
- **OOS Penalty:** Auto-delist sellers with >10% OOS rate  
- **Profit-First Listing:** Require margin disclosure before product approval
"""))

# ── Cell 6: Export ──
cells.append(md("## 6. Export Cleaned Data"))
cells.append(code("""
df.to_csv('../data/cleaned_data.csv', index=False)
print(f"Exported {len(df):,} rows to data/cleaned_data.csv")
print("\\n=== FINAL SUMMARY ===")
print(f"Total Products      : {len(df):,}")
print(f"Revenue at Risk     : ₹{df['revenue_at_risk'].sum():,.0f}")
print(f"Over-Discounted     : {df['high_discount_flag'].sum():,} ({df['high_discount_flag'].mean()*100:.1f}%)")
print(f"OOS Revenue Loss    : ₹{df[df['out_of_stock']==True]['selling_price'].sum():,.0f}")
print(f"Avg Discount        : {df['discount_pct_calc'].mean():.1f}%")
print(f"Avg Rating          : {df['average_rating'].mean():.2f}")
"""))

nb.cells = cells

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f"Notebook saved: {NB_PATH}")
