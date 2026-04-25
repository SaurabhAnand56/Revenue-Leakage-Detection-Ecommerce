# 📉 Revenue Leakage Detection & Pricing Optimization System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-E97627?style=for-the-badge&logo=tableau&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)
![Seaborn](https://img.shields.io/badge/Seaborn-4C72B0?style=for-the-badge&logo=python&logoColor=white)

**Identify where an e-commerce platform loses revenue due to pricing inefficiencies, excessive discounts, and out-of-stock situations — powered by Gemini 2.5 Flash AI**

[![Live App](https://img.shields.io/badge/🚀_Live_Streamlit_App-FF4B4B?style=for-the-badge)](https://your-streamlit-app-link-here.streamlit.app)
[![Tableau Dashboard](https://img.shields.io/badge/📊_Tableau_Dashboard-E97627?style=for-the-badge)](https://public.tableau.com/app/profile/saurabhanand56/viz/RevenueLeakageDetection-FlipkartPricingAnalysis/E-CommerceDashboard)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/saurabhanand56)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SaurabhAnand56)

</div>

---

## 📌 Problem Statement

> *"Identify where the business is losing revenue due to pricing inefficiencies, discounts, and cost structures — and recommend corrective actions."*

Most e-commerce platforms bleed revenue silently through:
- Excessive discount policies that erode margins
- Out-of-stock products causing missed sales opportunities
- No visibility into which sellers, categories, or price tiers are highest risk

This project detects all of the above and surfaces actionable insights through SQL, Python, AI, and interactive dashboards.

---

## 📊 Key Findings

| Metric | Value |
|--------|-------|
| 📦 Total Products Analyzed | **27,303** |
| 💸 Total Revenue at Risk | **₹18.2 Million** |
| ⚠️ Over-Discounted Products (>40%) | **20,532 (75.2%)** |
| 📉 Avg Platform Discount | **50.5%** |
| 🚫 OOS Revenue Loss | **₹1.54 Million** |
| 🏷️ Highest Risk Sub-Category | **Topwear (₹9.4M at risk)** |
| 🏪 Highest Risk Seller | **RetailNet (₹1.01M at risk)** |
| ⭐ Avg Product Rating | **3.63 / 5** |

---

## 🗂️ Project Structure

```
revenue-leakage-detection/
│
├── 📁 data/
│   ├── flipkart_products.xlsx          # Raw dataset (27,303 products)
│   └── cleaned_data.csv                # Processed data (generated on run)
│
├── 📁 notebooks/
│   └── Revenue_Leakage_Analysis.ipynb  # Full analysis notebook
│
├── 📁 scripts/
│   ├── 01_data_cleaning.py             # Data cleaning + feature engineering
│   ├── 02_sql_analysis.py              # 7 SQL queries (CTEs + window functions)
│   ├── 03_eda_analysis.py              # 6 EDA charts
│   ├── 04_streamlit_app.py             # Streamlit + Gemini AI web app
│   └── 05_generate_notebook.py         # Notebook generator
│
├── 📁 outputs/
│   └── charts/                         # 6 generated PNG charts
│       ├── chart1_discount_distribution.png
│       ├── chart2_revenue_at_risk_category.png
│       ├── chart3_discount_vs_rating.png
│       ├── chart4_discount_heatmap.png
│       ├── chart5_top_risky_sellers.png
│       └── chart6_oos_impact.png
│
├── 📁 dashboard/
│   └── POWERBI_INSTRUCTIONS.md         # Power BI step-by-step guide
│
├── requirements.txt                    # Python dependencies
├── LICENSE                             # MIT License
└── README.md                           # You are here
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite (CTEs, Window Functions, JOINs) |
| **Visualization** | Matplotlib, Seaborn |
| **Web App** | Streamlit |
| **AI Layer** | Google Gemini 2.5 Flash API |
| **BI Dashboard** | Tableau Public |
| **Notebook** | Jupyter Notebook |
| **Version Control** | Git / GitHub |

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10 or higher
- pip package manager
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### Step 1 — Clone the repository

```bash
git clone https://github.com/SaurabhAnand56/revenue-leakage-detection.git
cd revenue-leakage-detection
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Run the data pipeline (in order)

```bash
# Clean raw data + create derived columns
python scripts/01_data_cleaning.py

# Run 7 SQL analysis queries
python scripts/02_sql_analysis.py

# Generate 6 EDA charts
python scripts/03_eda_analysis.py
```

### Step 4 — Launch the Streamlit app

```bash
streamlit run scripts/04_streamlit_app.py
```

The app opens at `http://localhost:8501` in your browser.

> **Note:** Enter your free Gemini API key in the sidebar of the app to enable AI features.

### Step 5 — Open the Jupyter Notebook (optional)

```bash
jupyter notebook notebooks/Revenue_Leakage_Analysis.ipynb
```

---

## 🤖 Streamlit App Features

The app has **5 pages** accessible via the top navigation bar:

| Page | Description |
|------|-------------|
| 🏠 **Home** | Project overview, KPI cards, quick-start tiles |
| 🤖 **AI Query Assistant** | Ask business questions in plain English → Gemini generates SQL → runs it → explains results |
| 📊 **Sales Dashboard** | 6 interactive charts with category, price tier, and discount filters |
| 🔍 **SQL Explorer** | Write custom SQL with 6 preset revenue-leakage queries |
| 💡 **AI Insights** | Full AI-generated business intelligence report |

---

## 🗄️ SQL Analysis Highlights

7 advanced queries including:

```sql
-- Top leakage sub-categories (CTE + aggregation)
WITH risk AS (
    SELECT sub_category,
           COUNT(*) AS products,
           ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
           ROUND(SUM(revenue_at_risk), 0) AS total_risk
    FROM products
    WHERE high_discount_flag = 1
    GROUP BY sub_category
)
SELECT * FROM risk ORDER BY total_risk DESC;

-- Brand ranking by discount within category (Window Function)
WITH brand_stats AS (
    SELECT category, brand,
           ROUND(AVG(discount_pct_calc), 1) AS avg_disc,
           ROUND(SUM(revenue_at_risk), 0) AS risk
    FROM products GROUP BY category, brand HAVING COUNT(*) >= 5
)
SELECT *, RANK() OVER (PARTITION BY category ORDER BY avg_disc DESC) AS rank
FROM brand_stats WHERE rank <= 5
ORDER BY category, rank;
```

---

## 📈 EDA Charts Generated

| Chart | Insight |
|-------|---------|
| Discount % Distribution | 75% of products exceed the 40% risk threshold |
| Revenue at Risk by Sub-Category | Topwear contributes ₹9.4M alone |
| Discount % vs Rating | High discounts don't improve ratings |
| Discount Heatmap | Budget tier most over-discounted across all sub-categories |
| Top Risky Sellers | RetailNet accounts for ₹1.01M in risk |
| Out-of-Stock Impact | 1,577 OOS products = ₹1.54M missed revenue |

---

## 📊 Tableau Public Dashboard

**Live Dashboard →** [Revenue Leakage Detection — Flipkart Pricing Analysis](https://public.tableau.com/app/profile/saurabhanand56/viz/RevenueLeakageDetection-FlipkartPricingAnalysis/E-CommerceDashboard)

5-panel interactive dashboard featuring:
- 🟢 KPI Cards (Revenue at Risk, Avg Discount, OOS Loss, Avg Rating)
- 📊 Revenue at Risk by Sub-Category (sorted bar chart)
- 🌡️ Discount Heatmap (Price Tier × Sub-Category)
- 🏪 Top Risky Sellers (gradient bar chart)
- 🔵 Discount % vs Rating (bubble scatter plot with 40% reference line)

---

## 💡 Business Recommendations

| Priority | Finding | Recommendation |
|----------|---------|----------------|
| 🔴 Critical | 75.2% products discounted >40% | Cap seller discounts at 40% platform-wide |
| 🔴 Critical | Topwear: ₹9.4M at risk | Category-specific max discount tiers |
| 🟠 High | 1,577 OOS products = ₹1.54M lost | Enforce seller SLA for inventory restocking |
| 🟠 High | High discounts don't improve ratings | Use dynamic pricing instead of blanket discounts |
| 🟡 Medium | Budget tier most over-discounted | Floor price = 60% of MRP across all categories |
| 🟡 Medium | RetailNet avg discount >60% | Require seller profitability score before listing |

---

## 👨‍💻 Author

**Saurabh Anand**
Data Analyst | Python • SQL • AI • Power BI • Tableau

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/saurabhanand56)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/SaurabhAnand56)
[![Email](https://img.shields.io/badge/Email-saurabhcimage@gmail.com-D14836?style=flat&logo=gmail&logoColor=white)](mailto:saurabhcimage@gmail.com)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
⭐ If you found this project helpful, please consider giving it a star!
</div>
