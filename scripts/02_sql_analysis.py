"""
Revenue Leakage Detection - Step 2: SQL Analysis
Uses SQLite in-memory database on cleaned CSV data.
"""

import pandas as pd
import sqlite3
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned_data.csv')
SQL_OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'sql_results.xlsx')


def load_to_sqlite(csv_path):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(':memory:')
    df.to_sql('products', conn, index=False, if_exists='replace')
    print(f"Loaded {len(df):,} rows into SQLite.")
    return conn, df


def run_query(conn, title, sql):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    return result


def main():
    conn, df = load_to_sqlite(DATA_PATH)
    results = {}

    # ─────────────────────────────────────────────
    # Q1: Over-discounted products (>40% discount)
    # ─────────────────────────────────────────────
    results['high_discount'] = run_query(conn, "Q1: High Discount Products (>40%)", """
        SELECT 
            category,
            sub_category,
            COUNT(*) AS product_count,
            ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
            ROUND(SUM(discount_amount), 0) AS total_discount_given,
            ROUND(SUM(revenue_at_risk), 0) AS revenue_at_risk
        FROM products
        WHERE high_discount_flag = 1
        GROUP BY category, sub_category
        ORDER BY revenue_at_risk DESC
        LIMIT 15
    """)

    # ─────────────────────────────────────────────
    # Q2: Discount Bucket vs Avg Selling Price
    # ─────────────────────────────────────────────
    results['discount_vs_price'] = run_query(conn, "Q2: Discount Bracket vs Avg Selling Price", """
        WITH bucketed AS (
            SELECT *,
                CASE
                    WHEN discount_pct_calc < 20 THEN '0-20%'
                    WHEN discount_pct_calc < 40 THEN '20-40%'
                    WHEN discount_pct_calc < 60 THEN '40-60%'
                    WHEN discount_pct_calc < 80 THEN '60-80%'
                    ELSE '80%+'
                END AS discount_bucket
            FROM products
        )
        SELECT
            discount_bucket,
            COUNT(*) AS product_count,
            ROUND(AVG(actual_price), 0) AS avg_mrp,
            ROUND(AVG(selling_price), 0) AS avg_selling_price,
            ROUND(AVG(discount_amount), 0) AS avg_discount_given,
            ROUND(AVG(average_rating), 2) AS avg_rating
        FROM bucketed
        GROUP BY discount_bucket
        ORDER BY discount_bucket
    """)

    # ─────────────────────────────────────────────
    # Q3: Top leakage categories
    # ─────────────────────────────────────────────
    results['top_leakage'] = run_query(conn, "Q3: Top Revenue Leakage by Category", """
        SELECT
            category,
            COUNT(*) AS total_products,
            ROUND(SUM(revenue_at_risk), 0) AS total_revenue_at_risk,
            ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
            SUM(CASE WHEN high_discount_flag=1 THEN 1 ELSE 0 END) AS over_discounted_count
        FROM products
        GROUP BY category
        ORDER BY total_revenue_at_risk DESC
    """)

    # ─────────────────────────────────────────────
    # Q4: High-risk sellers (avg discount > 50%)
    # ─────────────────────────────────────────────
    results['risky_sellers'] = run_query(conn, "Q4: High-Risk Sellers (Avg Discount > 50%)", """
        SELECT
            seller,
            COUNT(*) AS products_listed,
            ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
            ROUND(SUM(revenue_at_risk), 0) AS total_risk,
            ROUND(AVG(average_rating), 2) AS avg_rating
        FROM products
        GROUP BY seller
        HAVING AVG(discount_pct_calc) > 50
        ORDER BY total_risk DESC
        LIMIT 15
    """)

    # ─────────────────────────────────────────────
    # Q5: Out-of-stock loss by sub_category (CTE)
    # ─────────────────────────────────────────────
    results['oos_loss'] = run_query(conn, "Q5: Out-of-Stock Revenue Loss by Sub-Category (CTE)", """
        WITH oos AS (
            SELECT *
            FROM products
            WHERE out_of_stock = 1
        ),
        oos_summary AS (
            SELECT
                sub_category,
                COUNT(*) AS oos_count,
                ROUND(SUM(selling_price), 0) AS potential_revenue_lost,
                ROUND(AVG(average_rating), 2) AS avg_rating
            FROM oos
            GROUP BY sub_category
        )
        SELECT * FROM oos_summary
        ORDER BY potential_revenue_lost DESC
    """)

    # ─────────────────────────────────────────────
    # Q6: Window function — brand rank by discount within category
    # ─────────────────────────────────────────────
    results['brand_rank'] = run_query(conn, "Q6: Brand Ranking by Discount % Within Category (Window Function)", """
        WITH brand_stats AS (
            SELECT
                category,
                brand,
                COUNT(*) AS products,
                ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
                ROUND(SUM(revenue_at_risk), 0) AS risk
            FROM products
            GROUP BY category, brand
            HAVING COUNT(*) >= 5
        ),
        ranked AS (
            SELECT *,
                RANK() OVER (PARTITION BY category ORDER BY avg_discount DESC) AS rank_in_category
            FROM brand_stats
        )
        SELECT * FROM ranked
        WHERE rank_in_category <= 5
        ORDER BY category, rank_in_category
    """)

    # ─────────────────────────────────────────────
    # Q7: Price tier analysis
    # ─────────────────────────────────────────────
    results['price_tier'] = run_query(conn, "Q7: Revenue Risk by Price Tier", """
        SELECT
            price_tier,
            COUNT(*) AS products,
            ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
            ROUND(SUM(revenue_at_risk), 0) AS total_revenue_at_risk,
            ROUND(AVG(average_rating), 2) AS avg_rating
        FROM products
        WHERE price_tier IS NOT NULL
        GROUP BY price_tier
        ORDER BY total_revenue_at_risk DESC
    """)

    # Save to Excel with multiple sheets
    with pd.ExcelWriter(SQL_OUTPUT, engine='openpyxl') as writer:
        for sheet_name, result_df in results.items():
            result_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    print(f"\nSQL results saved → {SQL_OUTPUT}")

    conn.close()
    return results


if __name__ == '__main__':
    main()
