# ============================================================
# BAKERY SALES & MARGIN INTELLIGENCE DASHBOARD
# Streamlit Application
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Bakery Sales & Margin Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #17202a;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff;
    }

    /* Sidebar title */
    .sidebar-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .sidebar-subtitle {
        font-size: 13px;
        color: #b8c2cc !important;
        margin-bottom: 25px;
    }

    /* Main title */
    .dashboard-title {
        font-size: 34px;
        font-weight: 750;
        color: #17202a;
        margin-bottom: 4px;
    }

    .dashboard-subtitle {
        font-size: 16px;
        color: #667085;
        margin-bottom: 25px;
    }

    /* Section titles */
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #17202a;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* KPI cards */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 2px 6px rgba(16, 24, 40, 0.04);
    }

    .kpi-label {
        font-size: 13px;
        color: #667085;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 27px;
        font-weight: 750;
        color: #17202a;
    }

    .kpi-description {
        font-size: 12px;
        color: #98a2b3;
        margin-top: 5px;
    }

    /* Insight cards */
    .insight-card {
        background-color: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(16, 24, 40, 0.04);
    }

    .insight-title {
        font-size: 16px;
        font-weight: 700;
        color: #17202a;
        margin-bottom: 8px;
    }

    .insight-text {
        font-size: 14px;
        color: #475467;
        line-height: 1.6;
    }

    /* Attention cards */
    .attention-card {
        background-color: #ffffff;
        border-left: 4px solid #c0392b;
        border-top: 1px solid #e4e7ec;
        border-right: 1px solid #e4e7ec;
        border-bottom: 1px solid #e4e7ec;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .attention-title {
        font-weight: 700;
        color: #17202a;
        font-size: 15px;
    }

    .attention-text {
        color: #667085;
        font-size: 13px;
        margin-top: 4px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #98a2b3;
        font-size: 12px;
        padding-top: 30px;
        padding-bottom: 10px;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "processed" / "dashboard"


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_dashboard_data():

    product_file = DATA_DIR / "product_dashboard.csv"
    kpi_file = DATA_DIR / "kpi_summary.csv"
    attention_file = DATA_DIR / "products_requiring_attention.csv"
    waste_file = DATA_DIR / "high_waste_products.csv"
    profit_file = DATA_DIR / "top_profit_products.csv"
    status_file = DATA_DIR / "status_summary.csv"

    products = pd.read_csv(product_file)
    kpis = pd.read_csv(kpi_file)
    attention = pd.read_csv(attention_file)
    waste = pd.read_csv(waste_file)
    profit = pd.read_csv(profit_file)
    status = pd.read_csv(status_file)

    return products, kpis, attention, waste, profit, status


# ============================================================
# SAFE NUMBER FUNCTIONS
# ============================================================

def safe_number(value, default=0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except:
        return default


def format_currency(value):
    value = safe_number(value)

    if abs(value) >= 1_000_000:
        return f"₦{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"₦{value / 1_000:.1f}K"

    return f"₦{value:,.0f}"


def format_number(value):
    value = safe_number(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"


def format_percent(value):
    value = safe_number(value)
    return f"{value:.1f}%"


# ============================================================
# LOAD DATA
# ============================================================

try:

    (
        products,
        kpis,
        attention,
        waste,
        profit,
        status
    ) = load_dashboard_data()

except Exception as e:

    st.error(
        "The dashboard data could not be loaded. "
        "Please make sure Stage 6C has been executed successfully."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# DATA CLEANING
# ============================================================

numeric_columns = [
    "units_sold",
    "revenue",
    "unit_cost",
    "cogs",
    "gross_profit",
    "gross_margin_pct",
    "waste_quantity",
    "waste_cost",
    "adjusted_profit",
    "adjusted_margin_pct",
    "waste_pct"
]

for column in numeric_columns:

    if column in products.columns:
        products[column] = pd.to_numeric(
            products[column],
            errors="coerce"
        ).fillna(0)


# Remove test products
if "product_name" in products.columns:

    products = products[
        ~products["product_name"]
        .astype(str)
        .str.contains("TEST", case=False, na=False)
    ].copy()


# Recalculate waste percentage using the project definition
if "waste_cost" in products.columns and "revenue" in products.columns:

    products["waste_pct"] = np.where(
        products["revenue"] > 0,
        products["waste_cost"] / products["revenue"] * 100,
        0
    )


# ============================================================
# EXECUTIVE METRICS
# ============================================================

total_revenue = products["revenue"].sum()

total_profit = products["adjusted_profit"].sum()

total_units = products["units_sold"].sum()

total_waste_cost = products["waste_cost"].sum()

average_margin = (
    products["adjusted_margin_pct"].mean()
    if "adjusted_margin_pct" in products.columns
    else 0
)

average_waste = (
    products["waste_pct"].mean()
    if "waste_pct" in products.columns
    else 0
)

product_count = len(products)

critical_products = products[
    (
        (products["adjusted_margin_pct"] < 5)
        &
        (products["waste_pct"] >= 20)
    )
].copy()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-title">
        Bakery Intelligence
        </div>

        <div class="sidebar-subtitle">
        Sales, profitability and waste analytics
        </div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "Dashboard Sections",
        [
            "Executive Overview",
            "Product Profitability",
            "Waste Intelligence",
            "Management Insights"
        ]
    )

    st.markdown("---")

    st.markdown(
        """
        <div style="font-size:12px;color:#b8c2cc;">
        Data source: Bakery transaction and product cost data
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">Bakery Sales & Margin Intelligence</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'A management dashboard for understanding revenue, profitability, '
    'waste and product-level performance.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# ============================================================

if page == "Executive Overview":

    st.markdown(
        '<div class="section-title">Executive Performance</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">TOTAL REVENUE</div>
                <div class="kpi-value">{format_currency(total_revenue)}</div>
                <div class="kpi-description">Recorded sales revenue</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">ADJUSTED PROFIT</div>
                <div class="kpi-value">{format_currency(total_profit)}</div>
                <div class="kpi-description">After product waste</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">UNITS SOLD</div>
                <div class="kpi-value">{format_number(total_units)}</div>
                <div class="kpi-description">Total units sold</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">WASTE COST</div>
                <div class="kpi-value">{format_currency(total_waste_cost)}</div>
                <div class="kpi-description">Estimated waste impact</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">AVG MARGIN</div>
                <div class="kpi-value">{format_percent(average_margin)}</div>
                <div class="kpi-description">Average adjusted margin</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # Revenue vs Profit
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Revenue and Profit by Product</div>',
        unsafe_allow_html=True
    )

    chart_data = products.sort_values(
        "revenue",
        ascending=False
    ).copy()

    fig = px.bar(
        chart_data,
        x="product_name",
        y=["revenue", "adjusted_profit"],
        barmode="group",
        title="Revenue vs Adjusted Profit",
        labels={
            "value": "Amount",
            "product_name": "Product",
            "variable": "Metric"
        }
    )

    fig.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=60, b=100),
        legend_title_text="",
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    # --------------------------------------------------------
    # Executive Summary
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Executive Summary</div>',
        unsafe_allow_html=True
    )

    top_profit_product = products.loc[
        products["adjusted_profit"].idxmax(),
        "product_name"
    ]

    top_margin_product = products.loc[
        products["adjusted_margin_pct"].idxmax(),
        "product_name"
    ]

    highest_waste_product = products.loc[
        products["waste_pct"].idxmax(),
        "product_name"
    ]

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">Highest Profit Contributor</div>
                <div class="insight-text">
                {top_profit_product} generates the highest adjusted
                profit among the products analysed.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">Strongest Margin</div>
                <div class="insight-text">
                {top_margin_product} has the highest adjusted
                profit margin.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">Highest Waste Rate</div>
                <div class="insight-text">
                {highest_waste_product} has the highest waste
                cost relative to revenue.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# PAGE 2 — PRODUCT PROFITABILITY
# ============================================================

elif page == "Product Profitability":

    st.markdown(
        '<div class="section-title">Product Profitability Analysis</div>',
        unsafe_allow_html=True
    )

    selected_product = st.selectbox(
        "Select a product",
        sorted(products["product_name"].unique())
    )

    product = products[
        products["product_name"] == selected_product
    ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">REVENUE</div>
                <div class="kpi-value">
                {format_currency(product["revenue"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">ADJUSTED PROFIT</div>
                <div class="kpi-value">
                {format_currency(product["adjusted_profit"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">ADJUSTED MARGIN</div>
                <div class="kpi-value">
                {format_percent(product["adjusted_margin_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">WASTE RATE</div>
                <div class="kpi-value">
                {format_percent(product["waste_pct"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="section-title">Profitability Ranking</div>',
        unsafe_allow_html=True
    )

    profitability_table = products[
        [
            "product_name",
            "units_sold",
            "revenue",
            "adjusted_profit",
            "adjusted_margin_pct",
            "waste_cost",
            "waste_pct"
        ]
    ].sort_values(
        "adjusted_profit",
        ascending=False
    ).copy()

    profitability_table.columns = [
        "Product",
        "Units Sold",
        "Revenue",
        "Adjusted Profit",
        "Adjusted Margin %",
        "Waste Cost",
        "Waste %"
    ]

    st.dataframe(
        profitability_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(
                format="₦%,.0f"
            ),
            "Adjusted Profit": st.column_config.NumberColumn(
                format="₦%,.0f"
            ),
            "Waste Cost": st.column_config.NumberColumn(
                format="₦%,.0f"
            ),
            "Adjusted Margin %": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "Waste %": st.column_config.NumberColumn(
                format="%.1f%%"
            )
        }
    )

    # --------------------------------------------------------
    # Margin Chart
    # --------------------------------------------------------

    margin_data = products.sort_values(
        "adjusted_margin_pct",
        ascending=True
    )

    fig = px.bar(
        margin_data,
        x="adjusted_margin_pct",
        y="product_name",
        orientation="h",
        title="Adjusted Profit Margin by Product",
        labels={
            "adjusted_margin_pct": "Adjusted Margin (%)",
            "product_name": "Product"
        }
    )

    fig.update_layout(
        height=650,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# PAGE 3 — WASTE INTELLIGENCE
# ============================================================

elif page == "Waste Intelligence":

    st.markdown(
        '<div class="section-title">Waste Intelligence</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">TOTAL WASTE COST</div>
                <div class="kpi-value">
                {format_currency(total_waste_cost)}
                </div>
                <div class="kpi-description">
                Estimated cost associated with waste
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">AVERAGE WASTE RATE</div>
                <div class="kpi-value">
                {format_percent(average_waste)}
                </div>
                <div class="kpi-description">
                Waste cost relative to revenue
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">HIGH-WASTE PRODUCTS</div>
                <div class="kpi-value">
                {len(products[products["waste_pct"] >= 20])}
                </div>
                <div class="kpi-description">
                Products with waste rate of 20% or higher
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # Waste Cost
    # --------------------------------------------------------

    waste_data = products.sort_values(
        "waste_cost",
        ascending=True
    )

    fig = px.bar(
        waste_data,
        x="waste_cost",
        y="product_name",
        orientation="h",
        title="Waste Cost by Product",
        labels={
            "waste_cost": "Waste Cost",
            "product_name": "Product"
        }
    )

    fig.update_layout(
        height=650,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    # --------------------------------------------------------
    # Waste Rate
    # --------------------------------------------------------

    waste_rate_data = products.sort_values(
        "waste_pct",
        ascending=True
    )

    fig2 = px.bar(
        waste_rate_data,
        x="waste_pct",
        y="product_name",
        orientation="h",
        title="Waste Rate by Product",
        labels={
            "waste_pct": "Waste Rate (%)",
            "product_name": "Product"
        }
    )

    fig2.update_layout(
        height=650,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig2,
        width="stretch"
    )

    # --------------------------------------------------------
    # Waste vs Margin
    # --------------------------------------------------------

    fig3 = px.scatter(
        products,
        x="waste_pct",
        y="adjusted_margin_pct",
        size="revenue",
        hover_name="product_name",
        title="Waste Rate vs Adjusted Margin",
        labels={
            "waste_pct": "Waste Rate (%)",
            "adjusted_margin_pct": "Adjusted Margin (%)",
            "revenue": "Revenue"
        }
    )

    fig3.update_layout(
        height=550,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig3,
        width="stretch"
    )

    # --------------------------------------------------------
    # High Waste Products
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Products Requiring Waste Reduction</div>',
        unsafe_allow_html=True
    )

    high_waste = products[
        products["waste_pct"] >= 20
    ].sort_values(
        "waste_pct",
        ascending=False
    ).copy()

    if len(high_waste) == 0:

        st.success(
            "No products currently exceed the high-waste threshold."
        )

    else:

        high_waste_display = high_waste[
            [
                "product_name",
                "waste_cost",
                "waste_pct",
                "adjusted_margin_pct"
            ]
        ].copy()

        high_waste_display.columns = [
            "Product",
            "Waste Cost",
            "Waste Rate",
            "Adjusted Margin"
        ]

        st.dataframe(
            high_waste_display,
            width="stretch",
            hide_index=True,
            column_config={
                "Waste Cost": st.column_config.NumberColumn(
                    format="₦%,.0f"
                ),
                "Waste Rate": st.column_config.NumberColumn(
                    format="%.1f%%"
                ),
                "Adjusted Margin": st.column_config.NumberColumn(
                    format="%.1f%%"
                )
            }
        )


# ============================================================
# PAGE 4 — MANAGEMENT INSIGHTS
# ============================================================

# ============================================================
# PAGE 4 — MANAGEMENT INSIGHTS
# ============================================================

elif page == "Management Insights":

    st.markdown(
        '<div class="section-title">Management Insights</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Products Requiring Immediate Attention
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Products Requiring Immediate Attention</div>',
        unsafe_allow_html=True
    )

    if len(critical_products) == 0:

        st.success(
            "No products currently meet the critical-risk threshold."
        )

    else:

        for _, row in critical_products.iterrows():

            product_name = str(row["product_name"])
            margin = safe_number(row["adjusted_margin_pct"])
            waste_rate = safe_number(row["waste_pct"])
            waste_cost = safe_number(row["waste_cost"])

            st.markdown(
                f"""
                <div class="attention-card">
                    <div class="attention-title">
                        {product_name}
                    </div>
                    <div class="attention-text">
                        Adjusted margin: {margin:.1f}%
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Waste rate: {waste_rate:.1f}%
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Waste cost: {format_currency(waste_cost)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # Management Recommendations
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Management Recommendations</div>',
        unsafe_allow_html=True
    )

    recommendations = []

    if average_waste >= 20:

        recommendations.append(
            "Prioritize waste reduction because the average product waste rate is elevated."
        )

    else:

        recommendations.append(
            "Maintain current waste controls while monitoring products with above-average waste."
        )

    if average_margin < 15:

        recommendations.append(
            "Review pricing and production costs because overall adjusted margins are relatively low."
        )

    else:

        recommendations.append(
            "Protect current margins by monitoring ingredient costs, discounts and waste."
        )

    if len(critical_products) > 0:

        recommendations.append(
            "Investigate critical products individually before increasing their production volume."
        )

    recommendations.append(
        "Use product-level profitability rather than revenue alone when making production decisions."
    )

    recommendations.append(
        "Use future demand forecasts to align production quantities with expected sales."
    )

    for recommendation in recommendations:

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-text">
                    {recommendation}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # Product Decision Matrix
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Product Decision Matrix</div>',
        unsafe_allow_html=True
    )

    decision_df = products[
        [
            "product_name",
            "revenue",
            "adjusted_profit",
            "adjusted_margin_pct",
            "waste_pct"
        ]
    ].copy()

    def classify_product(row):

        margin = safe_number(row["adjusted_margin_pct"])
        waste_rate = safe_number(row["waste_pct"])

        if margin < 5 and waste_rate >= 20:
            return "Critical"

        elif margin < 10:
            return "Low Margin"

        elif waste_rate >= 20:
            return "High Waste"

        elif margin >= 25:
            return "Strong"

        else:
            return "Moderate"

    decision_df["Business Status"] = decision_df.apply(
        classify_product,
        axis=1
    )

    decision_df = decision_df.sort_values(
        ["Business Status", "adjusted_profit"],
        ascending=[True, False]
    )

    decision_df.columns = [
        "Product",
        "Revenue",
        "Adjusted Profit",
        "Adjusted Margin",
        "Waste Rate",
        "Business Status"
    ]

    st.dataframe(
        decision_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(
                format="₦%,.0f"
            ),
            "Adjusted Profit": st.column_config.NumberColumn(
                format="₦%,.0f"
            ),
            "Adjusted Margin": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "Waste Rate": st.column_config.NumberColumn(
                format="%.1f%%"
            )
        }
    )
# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
    Bakery Sales & Margin Intelligence Dashboard
    <br>
    Built for product profitability, waste management and management decision support
    </div>
    """,
    unsafe_allow_html=True
)