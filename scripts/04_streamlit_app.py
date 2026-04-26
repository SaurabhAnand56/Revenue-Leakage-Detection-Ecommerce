"""
Revenue Leakage Detection & Pricing Optimization System
Streamlit App — Gemini 2.5 Flash (Free) | Flipkart E-Commerce Data
Author: Saurabh Anand
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import requests
import re
import os
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Revenue Leakage Detector",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

[data-testid="collapsedControl"] { display:none; }
section[data-testid="stSidebar"]  { display:none; }

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #0d1117 !important;
    color: #e6edf3;
}

.insight {
    background: #161b22;
    border-left: 4px solid #2ECC71;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 6px 0;
    font-size: 14px;
    color: #cdd9e5;
    line-height: 1.7;
}

.sql-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: monospace;
    font-size: 13px;
    color: #79c0ff;
    margin: 8px 0;
    white-space: pre-wrap;
}

.card-row { display:flex; gap:12px; margin:12px 0; flex-wrap:wrap; }
.card {
    flex: 1; min-width: 130px;
    background: #161b22;
    border-radius: 10px;
    padding: 14px 18px;
    border-left: 4px solid #7F77DD;
    border-top: 1px solid #30363d;
}
.card-val { font-size: 22px; font-weight: 700; color: #e6edf3; }
.card-lbl { font-size: 11px; color: #8b949e; margin-top: 3px; }
.card-risk { border-left-color: #E74C3C !important; }
.card-warn { border-left-color: #F39C12 !important; }
.card-ok   { border-left-color: #2ECC71 !important; }

.author-bar { display:flex; align-items:center; gap:14px; padding:12px 0 6px 0; }
.author-bar img { border-radius:50%; width:52px; height:52px; object-fit:cover; border:2px solid #7F77DD; }
.author-name { font-weight:700; color:#e6edf3; font-size:16px; }
.author-sub  { color:#8b949e; font-size:12px; margin-top:2px; }
.badge {
    display:inline-block; padding:3px 10px; border-radius:14px;
    font-size:11px; font-weight:600; text-decoration:none; margin-right:5px;
}
.badge-gh { background:#21262d; color:#e6edf3; border:1px solid #30363d; }
.badge-li { background:#0A66C2; color:#fff; }

hr { border-color:#21262d !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
PAGES = ["Home", "AI Query Assistant", "Sales Dashboard", "SQL Explorer", "AI Insights"]
if "page"       not in st.session_state: st.session_state.page = "Home"
if "query_hist" not in st.session_state: st.session_state.query_hist = []
if "api_key"    not in st.session_state: st.session_state.api_key = ""
if "prefill_q"  not in st.session_state: st.session_state.prefill_q = ""

# ─────────────────────────────────────────────────────────────
# TOP NAVBAR
# ─────────────────────────────────────────────────────────────
icons = ["🏠", "🤖", "📊", "🔍", "💡"]
nav_cols = st.columns(len(PAGES))
for col, pg_name, ic in zip(nav_cols, PAGES, icons):
    with col:
        if st.button(
            f"{ic} {pg_name}",
            key=f"nav_{pg_name}",
            use_container_width=True,
            type="primary" if st.session_state.page == pg_name else "secondary"
        ):
            st.session_state.page = pg_name
            st.rerun()

st.markdown("<hr style='margin:4px 0 16px 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DATA LOADING — works both locally and on Streamlit Cloud
# ─────────────────────────────────────────────────────────────
GITHUB_CSV = (
    "https://raw.githubusercontent.com/SaurabhAnand56/"
    "Revenue-Leakage-Detection-Ecommerce/main/data/cleaned_data.csv"
)

@st.cache_data(show_spinner="Loading Flipkart dataset...")
def load_df():
    # Try local path first (works when running locally)
    local_paths = [
        "data/cleaned_data.csv",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cleaned_data.csv"),
    ]
    for path in local_paths:
        if os.path.exists(path):
            return pd.read_csv(path)
    # Fallback to GitHub raw URL (works on Streamlit Cloud)
    try:
        return pd.read_csv(GITHUB_CSV)
    except Exception as e:
        st.error(f"Could not load data. Run 01_data_cleaning.py first. Error: {e}")
        st.stop()

@st.cache_resource(show_spinner="Building SQLite database...")
def load_conn(_df):
    """Cache the DB connection separately from the DataFrame."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    _df.to_sql("products", conn, index=False, if_exists="replace")
    return conn

df   = load_df()
conn = load_conn(df)

# ─────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────
SCHEMA = """
Table: products
Columns:
  pid                TEXT  -- product unique ID
  title              TEXT  -- product title
  brand              TEXT  -- brand name
  category           TEXT  -- e.g. Clothing and Accessories, Footwear
  sub_category       TEXT  -- e.g. Topwear, Bottomwear, Footwear
  actual_price       REAL  -- original MRP in INR
  selling_price      REAL  -- discounted selling price in INR
  discount_pct_calc  REAL  -- calculated discount % = (actual-selling)/actual*100
  discount_amount    REAL  -- actual_price - selling_price
  revenue_at_risk    REAL  -- discount_amount where discount>40%, else 0
  high_discount_flag BOOL  -- TRUE if discount_pct_calc > 40%
  price_tier         TEXT  -- Budget / Mid / Premium / Luxury
  out_of_stock       BOOL  -- TRUE if product is out of stock
  average_rating     REAL  -- product rating out of 5
  seller             TEXT  -- seller name
"""

# ─────────────────────────────────────────────────────────────
# TILE QUESTIONS
# ─────────────────────────────────────────────────────────────
TILE_QUESTIONS = [
    ("📉", "Where is the most revenue being lost?"),
    ("🏷️", "Which sellers give the highest discounts?"),
    ("📦", "Which sub-categories are most over-discounted?"),
    ("⭐", "Do high discounts actually improve ratings?"),
    ("💰", "Which price tier has the most revenue at risk?"),
    ("🚫", "Which OOS products are causing the most loss?"),
    ("🏆", "Which brands have the lowest average discount?"),
    ("📊", "Show discount bucket breakdown with avg price"),
    ("🔴", "Which products have more than 70% discount?"),
    ("📈", "Which category contributes most to total risk?"),
]

# ─────────────────────────────────────────────────────────────
# GEMINI 2.5 FLASH API  (confirmed free tier)
# ─────────────────────────────────────────────────────────────
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def call_gemini(prompt: str, api_key: str) -> dict:
    """Call Gemini 2.5 Flash — free tier, no credit card needed."""
    url  = f"{GEMINI_URL}?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600,
        },
    }
    try:
        r = requests.post(url, json=body, timeout=30)
        if r.status_code == 200:
            data = r.json()
            # Safe extraction with fallback
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"success": True, "text": text}
            except (KeyError, IndexError):
                return {"success": False, "error": f"Unexpected response format: {str(data)[:200]}"}
        else:
            try:
                err_msg = r.json().get("error", {}).get("message", r.text[:300])
            except Exception:
                err_msg = r.text[:300]
            return {"success": False, "error": f"HTTP {r.status_code}: {err_msg}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Try again."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def text_to_sql(question: str, api_key: str) -> dict:
    """Convert plain English question to SQLite SQL."""
    prompt = f"""You are an expert SQL analyst. Convert the user's question into a SQLite SQL query.

Database schema:
{SCHEMA}

Rules:
- SQLite-compatible syntax only
- Use ROUND(value, 2) for all monetary and percentage values
- Limit results to 20 rows maximum unless asked otherwise
- Return ONLY the raw SQL query — no explanation, no markdown, no backticks, no comments

User question: {question}

SQL query:"""

    result = call_gemini(prompt, api_key)
    if not result["success"]:
        return result

    sql = result["text"]
    # Strip any accidental markdown fences
    sql = re.sub(r"```sql|```", "", sql).strip()
    # Remove comment lines
    lines = [l for l in sql.splitlines() if l.strip() and not l.strip().startswith("--")]
    return {"success": True, "sql": "\n".join(lines).strip()}


def generate_insight(question: str, result_df: pd.DataFrame, api_key: str) -> str:
    """Generate plain English business insight from query results."""
    if result_df is None or result_df.empty:
        return "No data returned from query."

    preview = result_df.head(10).to_string(index=False)
    prompt = f"""You are a senior business analyst reviewing e-commerce pricing data.

The user asked: "{question}"

Query results:
{preview}

Write 2-3 sentences of plain English business insight.
- Mention specific numbers from the data
- Make it actionable — what should the business do?
- No bullet points, no markdown, no headers
- Sound like a human analyst, not a template"""

    result = call_gemini(prompt, api_key)
    if result["success"]:
        return result["text"]
    return f"Could not generate insight: {result['error']}"


def run_sql(query: str) -> dict:
    """Run SQL safely and return DataFrame or error."""
    try:
        result = pd.read_sql_query(query, conn)
        return {"success": True, "df": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def style_ax(ax):
    """Apply dark theme to matplotlib axes."""
    ax.set_facecolor("#161b22")
    ax.figure.patch.set_facecolor("#0d1117")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color("#30363d")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.label.set_color("#8b949e")
    ax.yaxis.label.set_color("#8b949e")
    ax.title.set_color("#e6edf3")


def auto_chart(df_result: pd.DataFrame, question: str = ""):
    """Automatically pick and render the best chart for results."""
    if df_result is None or df_result.empty or len(df_result.columns) < 2:
        return
    num_cols = df_result.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df_result.select_dtypes(exclude=[np.number]).columns.tolist()
    if not num_cols:
        return

    y_col = num_cols[0]
    x_col = cat_cols[0] if cat_cols else df_result.columns[0]

    fig, ax = plt.subplots(figsize=(9, 4))

    if any(w in question.lower() for w in ["trend", "month", "year", "over time", "growth"]):
        ax.plot(range(len(df_result)), df_result[y_col],
                marker="o", lw=2.5, color="#7F77DD", ms=5)
        ax.fill_between(range(len(df_result)), df_result[y_col],
                        alpha=0.15, color="#7F77DD")
        step = max(1, len(df_result) // 8)
        ax.set_xticks(range(0, len(df_result), step))
        ax.set_xticklabels(
            df_result[x_col].astype(str).iloc[::step],
            rotation=45, ha="right", fontsize=8
        )
    elif len(df_result) <= 15:
        colors = ["#E74C3C" if i < 3 else "#7F77DD" for i in range(len(df_result))]
        ax.barh(df_result[x_col].astype(str), df_result[y_col],
                color=colors, edgecolor="none")
        for i, v in enumerate(df_result[y_col]):
            ax.text(v * 1.01, i, f"{v:,.1f}", va="center",
                    fontsize=9, color="#cdd9e5")
    else:
        ax.bar(df_result[x_col].astype(str), df_result[y_col],
               color="#7F77DD", edgecolor="none", alpha=0.85)
        plt.xticks(rotation=45, ha="right", fontsize=8)

    if question:
        ax.set_title(question[:65], fontsize=11, fontweight="bold", pad=10)

    style_ax(ax)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ═════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═════════════════════════════════════════════════════════════
pg = st.session_state.page

# ─────────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────────
if pg == "Home":

    st.markdown("""
    <div class="author-bar">
        <img src="https://github.com/SaurabhAnand56.png"/>
        <div>
            <div class="author-name">Saurabh Anand</div>
            <div class="author-sub">Data Analyst &nbsp;|&nbsp; Python &bull; SQL &bull; AI &bull; Power BI</div>
            <a class="badge badge-gh" href="https://github.com/SaurabhAnand56" target="_blank">GitHub</a>
            <a class="badge badge-li" href="https://www.linkedin.com/in/saurabhanand56" target="_blank">LinkedIn</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.title("📉 Revenue Leakage Detection & Pricing Optimization")
    st.markdown(
        "Identify where a Flipkart e-commerce platform loses revenue due to "
        "**excessive discounts, out-of-stock situations, and pricing inefficiencies** "
        "— powered by **Gemini 2.5 Flash AI**. Built on **27,303 real Flipkart product listings**."
    )

    # ── KPI Cards ────────────────────────────────────────────
    total_risk    = df["revenue_at_risk"].sum()
    avg_disc      = df["discount_pct_calc"].mean()
    over_disc_pct = df["high_discount_flag"].mean() * 100
    oos_loss      = df[df["out_of_stock"] == True]["selling_price"].sum()
    avg_rating    = df["average_rating"].mean()
    total_prods   = len(df)

    st.markdown(f"""
    <div class="card-row">
      <div class="card card-risk">
        <div class="card-val">₹{total_risk/1e6:.1f}M</div>
        <div class="card-lbl">Revenue at Risk</div>
      </div>
      <div class="card card-warn">
        <div class="card-val">{over_disc_pct:.1f}%</div>
        <div class="card-lbl">Over-Discounted Products</div>
      </div>
      <div class="card card-warn">
        <div class="card-val">{avg_disc:.1f}%</div>
        <div class="card-lbl">Avg Platform Discount</div>
      </div>
      <div class="card card-risk">
        <div class="card-val">₹{oos_loss/1e6:.2f}M</div>
        <div class="card-lbl">OOS Revenue Loss</div>
      </div>
      <div class="card card-ok">
        <div class="card-val">{avg_rating:.2f} ⭐</div>
        <div class="card-lbl">Avg Product Rating</div>
      </div>
      <div class="card">
        <div class="card-val">{total_prods:,}</div>
        <div class="card-lbl">Products Analysed</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── What this app does ───────────────────────────────────
    st.markdown("### What this app does")
    st.markdown('<div class="insight">🤖 <b>AI Query Assistant</b> — Ask any business question, Gemini 2.5 Flash generates SQL + chart + plain English insight</div>', unsafe_allow_html=True)
    st.markdown('<div class="insight">📊 <b>Sales Dashboard</b> — 6 interactive charts: discount distribution, revenue at risk, OOS loss, seller risk, price tier breakdown</div>', unsafe_allow_html=True)
    st.markdown('<div class="insight">🔍 <b>SQL Explorer</b> — Write custom SQL with 6 preset queries using CTEs, window functions, and CASE bucketing</div>', unsafe_allow_html=True)
    st.markdown('<div class="insight">💡 <b>AI Insights</b> — Full auto-generated business intelligence report across 5 key pricing dimensions</div>', unsafe_allow_html=True)

    # ── Tile question buttons ────────────────────────────────
    st.markdown("### Try asking the AI")
    row1 = st.columns(5)
    row2 = st.columns(5)
    for i, (icon, q) in enumerate(TILE_QUESTIONS):
        col = row1[i] if i < 5 else row2[i - 5]
        with col:
            if st.button(f"{icon}  {q}", key=f"home_tile_{i}", use_container_width=True):
                st.session_state.page      = "AI Query Assistant"
                st.session_state.prefill_q = q
                st.rerun()

    st.markdown("### Database schema")
    st.code(SCHEMA.strip(), language="sql")


# ─────────────────────────────────────────────────────────────
# AI QUERY ASSISTANT
# ─────────────────────────────────────────────────────────────
elif pg == "AI Query Assistant":
    st.title("🤖 AI Query Assistant")
    st.markdown(
        "Ask any business question in plain English. "
        "**Gemini 2.5 Flash** generates SQL, runs it on the database, "
        "and explains the result."
    )

    # API key
    with st.expander(
        "⚙️ Enter your Gemini API Key (free)",
        expanded=(st.session_state.api_key == "")
    ):
        st.markdown("""
**How to get a free Gemini API key (takes 2 minutes):**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key** → Create API key
3. Copy and paste below — completely free, no credit card needed
        """)
        api_input = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="AIza..."
        )
        if api_input:
            st.session_state.api_key = api_input
            st.success("API key saved for this session.")

    st.markdown("---")

    # Get prefilled question from home tile click
    default_q = st.session_state.get("prefill_q", "")
    st.session_state.prefill_q = ""  # reset after reading

    c1, c2 = st.columns([4, 1])
    with c1:
        question = st.text_input(
            "Ask a business question:",
            value=default_q,
            placeholder="e.g. Which seller has the highest revenue at risk?"
        )
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("Ask AI →", use_container_width=True, type="primary")

    # Tile quick questions
    st.markdown("**Quick questions:**")
    tr1 = st.columns(5)
    tr2 = st.columns(5)
    for i, (icon, q) in enumerate(TILE_QUESTIONS):
        col = tr1[i] if i < 5 else tr2[i - 5]
        with col:
            if st.button(f"{icon} {q}", key=f"aq_tile_{i}", use_container_width=True):
                question = q
                run_btn  = True

    st.markdown("---")

    if run_btn and question.strip():
        if not st.session_state.api_key:
            st.warning("Please enter your Gemini API key above — free at aistudio.google.com")
            st.stop()

        # Step 1: Generate SQL
        with st.spinner("🧠 Generating SQL..."):
            sql_result = text_to_sql(question, st.session_state.api_key)

        if not sql_result["success"]:
            st.error(f"AI Error: {sql_result['error']}")
            st.info("Check your API key is correct, or try rephrasing the question.")
        else:
            sql_query = sql_result["sql"]
            st.markdown("#### Generated SQL")
            st.markdown(f'<div class="sql-box">{sql_query}</div>', unsafe_allow_html=True)

            # Step 2: Run SQL
            with st.spinner("Running query on database..."):
                db_result = run_sql(sql_query)

            if not db_result["success"]:
                st.error(f"SQL Error: {db_result['error']}")
                st.info("Try rephrasing your question. Sometimes the AI generates slightly wrong column names.")
            else:
                result_df = db_result["df"]
                st.success(f"Query returned {len(result_df)} rows")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### Results")
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                with c2:
                    st.markdown("#### Chart")
                    auto_chart(result_df, question)

                # Step 3: Generate insight
                with st.spinner("Generating business insight..."):
                    insight = generate_insight(question, result_df, st.session_state.api_key)

                st.markdown("#### AI Business Insight")
                st.markdown(f'<div class="insight">💡 {insight}</div>', unsafe_allow_html=True)

                # Save to history
                st.session_state.query_hist.append({
                    "question": question,
                    "sql":      sql_query,
                    "rows":     len(result_df),
                    "insight":  insight,
                })

    # Query history
    if st.session_state.query_hist:
        st.markdown("---")
        st.markdown("#### Query History")
        for h in reversed(st.session_state.query_hist[-5:]):
            with st.expander(f"Q: {h['question'][:60]}"):
                st.code(h["sql"], language="sql")
                st.caption(f"Returned {h['rows']} rows")
                st.markdown(f'<div class="insight">💡 {h["insight"]}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SALES DASHBOARD
# ─────────────────────────────────────────────────────────────
elif pg == "Sales Dashboard":
    st.title("📊 Revenue Leakage Dashboard")
    st.markdown("Interactive charts from the Flipkart pricing database. Use filters to explore.")

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        all_cats = df["category"].unique().tolist()
        sel_cat  = st.multiselect("Category", all_cats, default=all_cats)
    with fc2:
        all_tiers = [t for t in ["Budget (<500)", "Mid (500-1500)", "Premium (1500-5000)", "Luxury (5000+)"]
                     if t in df["price_tier"].unique()]
        sel_tier  = st.multiselect("Price Tier", all_tiers, default=all_tiers)
    with fc3:
        disc_max = st.slider("Max Discount % shown", 10, 100, 100)

    df_f = df[
        df["category"].isin(sel_cat) &
        df["price_tier"].isin(sel_tier) &
        (df["discount_pct_calc"] <= disc_max)
    ].copy()

    st.caption(f"Showing {len(df_f):,} of {len(df):,} products")
    st.markdown("---")

    # Row 1
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Revenue at Risk by Sub-Category")
        grp = df_f.groupby("sub_category")["revenue_at_risk"].sum().sort_values(ascending=True).tail(10)
        fig, ax = plt.subplots(figsize=(7, 4))
        colors  = ["#E74C3C" if v > grp.quantile(0.7) else
                   "#F39C12" if v > grp.quantile(0.4) else "#7F77DD"
                   for v in grp.values]
        ax.barh(grp.index, grp.values / 1e3, color=colors, edgecolor="none")
        ax.set_xlabel("₹ Thousands")
        for i, v in enumerate(grp.values):
            ax.text(v / 1e3 * 1.01, i, f"₹{v/1e3:.0f}K",
                    va="center", fontsize=8, color="#cdd9e5")
        style_ax(ax)
        plt.tight_layout()
        st.pyplot(fig); plt.close()

    with c2:
        st.markdown("#### Discount % Distribution")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.axvspan(40, 100, alpha=0.12, color="#E74C3C", label="High-Risk Zone (>40%)")
        ax.axvspan(0,  40,  alpha=0.06, color="#2ECC71", label="Safe Zone (<40%)")
        ax.hist(df_f["discount_pct_calc"].dropna(), bins=50,
                color="#7F77DD", edgecolor="none", alpha=0.85)
        ax.axvline(40, color="#E74C3C", lw=1.5, ls="--")
        ax.axvline(df_f["discount_pct_calc"].mean(), color="#F39C12", lw=1.5, ls="--",
                   label=f"Mean {df_f['discount_pct_calc'].mean():.1f}%")
        ax.set_xlabel("Discount %")
        ax.legend(framealpha=0.1, labelcolor="#cdd9e5", fontsize=8)
        style_ax(ax); plt.tight_layout()
        st.pyplot(fig); plt.close()

    # Row 2
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Discount % vs Rating")
        sample = df_f.sample(min(2000, len(df_f)), random_state=42)
        fig, ax = plt.subplots(figsize=(7, 4))
        sc = ax.scatter(
            sample["discount_pct_calc"], sample["average_rating"],
            c=sample["selling_price"], cmap="plasma", alpha=0.4, s=12
        )
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label("Selling Price (₹)", color="#8b949e")
        cbar.ax.yaxis.set_tick_params(color="#8b949e")
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#8b949e")
        ax.axvline(40, color="#E74C3C", lw=1.2, ls="--", alpha=0.8)
        ax.set_xlabel("Discount %"); ax.set_ylabel("Rating")
        style_ax(ax); plt.tight_layout()
        st.pyplot(fig); plt.close()
        st.info("Finding: Higher discounts do NOT improve ratings — the trend line is flat.")

    with c4:
        st.markdown("#### Top 10 High-Risk Sellers")
        sel_grp = (df_f.groupby("seller")["revenue_at_risk"]
                   .sum().sort_values(ascending=False).head(10))
        fig, ax = plt.subplots(figsize=(7, 4))
        colors2 = ["#E74C3C" if i < 3 else "#F39C12" if i < 6 else "#7F77DD"
                   for i in range(len(sel_grp))]
        ax.barh(sel_grp.index[::-1], sel_grp.values[::-1] / 1e3,
                color=colors2[::-1], edgecolor="none")
        ax.set_xlabel("Revenue at Risk (₹K)")
        style_ax(ax); plt.tight_layout()
        st.pyplot(fig); plt.close()

    # Row 3
    c5, c6 = st.columns(2)
    with c5:
        st.markdown("#### Price Tier Breakdown")
        tier_df = df_f["price_tier"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 4))
        wedges, texts, autotexts = ax.pie(
            tier_df.values, labels=tier_df.index, autopct="%1.1f%%",
            colors=["#7F77DD", "#2ECC71", "#F39C12", "#E74C3C"],
            startangle=90, wedgeprops=dict(edgecolor="#0d1117", linewidth=2)
        )
        for t in texts:     t.set_color("#cdd9e5"); t.set_fontsize(10)
        for t in autotexts: t.set_fontsize(9); t.set_fontweight("bold")
        ax.figure.patch.set_facecolor("#0d1117")
        plt.tight_layout()
        st.pyplot(fig); plt.close()

    with c6:
        st.markdown("#### Out-of-Stock Revenue Loss by Sub-Category")
        oos_df = (df_f[df_f["out_of_stock"] == True]
                  .groupby("sub_category")["selling_price"]
                  .sum().sort_values(ascending=True).tail(8))
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(oos_df.index, oos_df.values / 1e3,
                color="#E74C3C", edgecolor="none", alpha=0.8)
        ax.set_xlabel("Revenue Lost (₹K)")
        style_ax(ax); plt.tight_layout()
        st.pyplot(fig); plt.close()
        st.info("Restock high-rating OOS items first — they represent immediate recoverable revenue.")


# ─────────────────────────────────────────────────────────────
# SQL EXPLORER
# ─────────────────────────────────────────────────────────────
elif pg == "SQL Explorer":
    st.title("🔍 SQL Explorer")
    st.markdown("Write and run custom SQL on the 27,303-row Flipkart pricing database.")

    with st.expander("View full schema"):
        st.code(SCHEMA.strip(), language="sql")

    PRESET_QUERIES = {
        "Select a preset query...": "",
        "Revenue at risk by sub-category": """SELECT sub_category,
  COUNT(*) AS products,
  ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
  ROUND(SUM(revenue_at_risk), 0) AS total_revenue_at_risk
FROM products
WHERE high_discount_flag = 1
GROUP BY sub_category
ORDER BY total_revenue_at_risk DESC
LIMIT 15;""",
        "Discount bucket analysis (CTE)": """WITH bucketed AS (
  SELECT *,
    CASE
      WHEN discount_pct_calc < 20 THEN '0-20%'
      WHEN discount_pct_calc < 40 THEN '20-40%'
      WHEN discount_pct_calc < 60 THEN '40-60%'
      WHEN discount_pct_calc < 80 THEN '60-80%'
      ELSE '80%+'
    END AS bucket
  FROM products
)
SELECT bucket,
  COUNT(*) AS products,
  ROUND(AVG(selling_price), 0) AS avg_price,
  ROUND(AVG(average_rating), 2) AS avg_rating,
  ROUND(SUM(revenue_at_risk), 0) AS total_risk
FROM bucketed
GROUP BY bucket
ORDER BY bucket;""",
        "High-risk sellers — window function": """WITH seller_stats AS (
  SELECT seller,
    COUNT(*) AS products,
    ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
    ROUND(SUM(revenue_at_risk), 0) AS total_risk,
    ROUND(AVG(average_rating), 2) AS avg_rating
  FROM products
  GROUP BY seller
  HAVING COUNT(*) >= 10
)
SELECT *,
  RANK() OVER (ORDER BY total_risk DESC) AS risk_rank
FROM seller_stats
ORDER BY total_risk DESC
LIMIT 15;""",
        "OOS loss by sub-category (CTE)": """WITH oos AS (
  SELECT * FROM products WHERE out_of_stock = 1
)
SELECT sub_category,
  COUNT(*) AS oos_count,
  ROUND(SUM(selling_price), 0) AS potential_revenue_lost,
  ROUND(AVG(average_rating), 2) AS avg_rating
FROM oos
GROUP BY sub_category
ORDER BY potential_revenue_lost DESC;""",
        "Brand rank by discount within category": """WITH brand_stats AS (
  SELECT category, brand,
    COUNT(*) AS products,
    ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
    ROUND(SUM(revenue_at_risk), 0) AS risk
  FROM products
  GROUP BY category, brand
  HAVING COUNT(*) >= 5
),
ranked AS (
  SELECT *,
    RANK() OVER (PARTITION BY category ORDER BY avg_discount DESC) AS rank_in_cat
  FROM brand_stats
)
SELECT * FROM ranked
WHERE rank_in_cat <= 5
ORDER BY category, rank_in_cat;""",
        "Price tier risk summary": """SELECT price_tier,
  COUNT(*) AS products,
  ROUND(AVG(discount_pct_calc), 1) AS avg_discount_pct,
  ROUND(SUM(revenue_at_risk), 0) AS total_revenue_at_risk,
  ROUND(AVG(average_rating), 2) AS avg_rating
FROM products
WHERE price_tier IS NOT NULL
GROUP BY price_tier
ORDER BY total_revenue_at_risk DESC;""",
    }

    preset = st.selectbox("Choose a preset query:", list(PRESET_QUERIES.keys()))
    default_sql = PRESET_QUERIES.get(preset) or \
        "SELECT category, COUNT(*) products,\n  ROUND(SUM(revenue_at_risk),0) total_risk\nFROM products\nGROUP BY category\nORDER BY total_risk DESC;"

    user_sql = st.text_area("SQL Query:", value=default_sql, height=180)

    if st.button("Run Query ▶", type="primary"):
        if user_sql.strip():
            result = run_sql(user_sql)
            if result["success"]:
                res_df = result["df"]
                st.success(f"Returned {len(res_df)} rows, {len(res_df.columns)} columns")
                st.dataframe(res_df, use_container_width=True, hide_index=True)
                auto_chart(res_df, preset if preset != "Select a preset query..." else "")
                st.download_button(
                    "Download CSV",
                    res_df.to_csv(index=False),
                    "query_result.csv",
                    "text/csv"
                )
            else:
                st.error(f"SQL Error: {result['error']}")
                st.info("Check column names against the schema above.")


# ─────────────────────────────────────────────────────────────
# AI INSIGHTS
# ─────────────────────────────────────────────────────────────
elif pg == "AI Insights":
    st.title("💡 AI Business Insights")
    st.markdown("Auto-generated pricing intelligence report powered by **Gemini 2.5 Flash**.")

    # API key
    with st.expander(
        "⚙️ Gemini API Key",
        expanded=(st.session_state.api_key == "")
    ):
        st.markdown("Get your free key at [aistudio.google.com](https://aistudio.google.com)")
        api_input = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="AIza..."
        )
        if api_input:
            st.session_state.api_key = api_input
            st.success("API key saved.")

    st.markdown("---")

    # Pre-defined insight queries
    INSIGHT_QUERIES = {
        "Revenue at Risk by Category": """
            SELECT category,
              ROUND(SUM(revenue_at_risk), 0) AS total_risk,
              ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
              COUNT(*) AS products
            FROM products
            GROUP BY category
            ORDER BY total_risk DESC""",

        "Discount Impact on Product Ratings": """
            SELECT
              CASE
                WHEN discount_pct_calc < 20 THEN 'Low (<20%)'
                WHEN discount_pct_calc < 40 THEN 'Medium (20-40%)'
                WHEN discount_pct_calc < 60 THEN 'High (40-60%)'
                ELSE 'Very High (>60%)'
              END AS discount_band,
              ROUND(AVG(average_rating), 2) AS avg_rating,
              COUNT(*) AS products,
              ROUND(SUM(revenue_at_risk), 0) AS total_risk
            FROM products
            GROUP BY discount_band
            ORDER BY avg_rating DESC""",

        "Top High-Risk Sellers": """
            SELECT seller,
              ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
              ROUND(SUM(revenue_at_risk), 0) AS total_risk,
              COUNT(*) AS products_listed,
              ROUND(AVG(average_rating), 2) AS avg_rating
            FROM products
            GROUP BY seller
            HAVING COUNT(*) >= 20
            ORDER BY total_risk DESC
            LIMIT 10""",

        "Price Tier Performance": """
            SELECT price_tier,
              COUNT(*) AS products,
              ROUND(SUM(revenue_at_risk), 0) AS total_risk,
              ROUND(AVG(discount_pct_calc), 1) AS avg_discount,
              ROUND(AVG(average_rating), 2) AS avg_rating
            FROM products
            WHERE price_tier IS NOT NULL
            GROUP BY price_tier
            ORDER BY total_risk DESC""",

        "Out-of-Stock Revenue Loss": """
            SELECT sub_category,
              COUNT(*) AS oos_items,
              ROUND(SUM(selling_price), 0) AS revenue_lost,
              ROUND(AVG(average_rating), 2) AS avg_rating
            FROM products
            WHERE out_of_stock = 1
            GROUP BY sub_category
            ORDER BY revenue_lost DESC
            LIMIT 10""",
    }

    # Pre-run all queries
    results_cache = {}
    for title, q in INSIGHT_QUERIES.items():
        r = run_sql(q)
        if r["success"] and not r["df"].empty:
            results_cache[title] = r["df"]

    generate_btn = st.button(
        "Generate Full AI Report",
        type="primary",
        use_container_width=True
    )

    if generate_btn:
        if not st.session_state.api_key:
            st.warning("Please enter your Gemini API key above — free at aistudio.google.com")
        else:
            st.markdown("### AI-Generated Pricing Intelligence Report")
            st.markdown("---")

            for title, res_df in results_cache.items():
                st.markdown(f"#### {title}")

                c1, c2 = st.columns(2)
                with c1:
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
                with c2:
                    auto_chart(res_df, title)

                with st.spinner(f"Analysing {title}..."):
                    insight = generate_insight(title, res_df, st.session_state.api_key)

                st.markdown(f'<div class="insight">💡 {insight}</div>', unsafe_allow_html=True)
                st.markdown("---")

            st.success("Full AI report generated successfully!")

    else:
        # Show charts without AI insight while waiting
        st.info("Enter your Gemini API key above and click **Generate Full AI Report** to add AI insights to each section.")
        for title, res_df in results_cache.items():
            st.markdown(f"#### {title}")
            c1, c2 = st.columns(2)
            with c1:
                st.dataframe(res_df, use_container_width=True, hide_index=True)
            with c2:
                auto_chart(res_df, title)
            st.markdown("---")


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#8b949e; font-size:12px; padding:8px 0'>
    Built by <b style='color:#e6edf3'>Saurabh Anand</b> &nbsp;|&nbsp;
    <a href='https://github.com/SaurabhAnand56' target='_blank' style='color:#8b949e'>GitHub</a>
    &nbsp;|&nbsp;
    <a href='https://www.linkedin.com/in/saurabhanand56' target='_blank' style='color:#8b949e'>LinkedIn</a>
    &nbsp;|&nbsp;
    AI: Gemini 2.5 Flash (Free) &nbsp;|&nbsp;
    Database: SQLite &nbsp;|&nbsp;
    Dataset: 27,303 Flipkart products
</div>
""", unsafe_allow_html=True)
