import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="FitnessDAX",
    layout="wide"
)

# -------------------------
# HELPERS
# -------------------------

def pace_to_mmss(pace):
    if pd.isna(pace):
        return "-"
    minutes = int(pace)
    seconds = round((pace - minutes) * 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"


def format_pct(value):
    if pd.isna(value):
        return "-"
    return f"{value:.2f}%"


# -------------------------
# LOAD DATA
# -------------------------

df = pd.read_csv("output/fitnessdax_final.csv")

numeric_cols = [
    "participants",
    "races_entered",
    "top_20_pace",
    "median_pace",
    "endurance_multiple",
    "yearly_return_pct",
    "germany_employees_estimate",
    "participation_rate",
    "participation_rate_pct",
    "fitnessdax_rank",
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


# -------------------------
# SIDEBAR
# -------------------------

st.sidebar.title("About this project")

st.sidebar.markdown("""
FitnessDAX is a hobby data project exploring whether fit companies also perform well on the stock market.

The project is based on publicly available B2Run race results across Germany and currently includes more than 180,000 runners from almost 50 events over 3 years.

The dataset now also includes estimated German employee numbers, sectors and playful company clusters to make participation comparable across companies.

Most importantly: This is not financial advice 😄
""")

st.sidebar.divider()

st.sidebar.markdown("**Timo Radzik**")
st.sidebar.markdown("💼 [LinkedIn](https://www.linkedin.com/in/timo-radzik/)")

st.sidebar.divider()

st.sidebar.header("Filters")

years = sorted(df["year"].dropna().unique(), reverse=True)

selected_year = st.sidebar.selectbox(
    "Year",
    years
)

available_sectors = sorted(df["sector"].dropna().unique())

selected_sectors = st.sidebar.multiselect(
    "Sector",
    available_sectors,
    default=available_sectors
)

available_clusters = sorted(df["cluster"].dropna().unique())

selected_clusters = st.sidebar.multiselect(
    "Cluster",
    available_clusters,
    default=available_clusters
)


# -------------------------
# TITLE
# -------------------------

st.title("🦡 FitnessDAX")
st.subheader("Germany's fittest publicly traded companies")
st.caption(
    "FitnessDAX is a hobby data experiment based on publicly available B2Run race data. No financial advice!"
)

st.divider()


# -------------------------
# FILTER DATA
# -------------------------

filtered = df[
    (df["year"] == selected_year)
    & (df["sector"].isin(selected_sectors))
    & (df["cluster"].isin(selected_clusters))
].copy()

filtered = filtered.dropna(subset=["fitnessdax_rank"])
filtered = filtered.sort_values("fitnessdax_rank")


# -------------------------
# METRICS
# -------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Companies",
    len(filtered)
)

col2.metric(
    "Total Participants",
    int(filtered["participants"].sum()) if len(filtered) > 0 else 0
)

avg_top20_pace = (
    filtered["top_20_pace"].mean()
    if len(filtered) > 0 else None
)

col3.metric(
    "Average Top 20% Pace",
    pace_to_mmss(avg_top20_pace)
)

avg_participation = (
    filtered["participation_rate_pct"].mean()
    if "participation_rate_pct" in filtered.columns and len(filtered) > 0 else None
)

col4.metric(
    "Avg Participation Rate",
    format_pct(avg_participation)
)

st.divider()


# -------------------------
# LEADERBOARD
# -------------------------

st.subheader("🏆 FitnessDAX Leaderboard")

leaderboard_cols = [
    "fitnessdax_rank",
    "matched_company",
    "ticker",
    "index",
    "sector",
    "cluster",
    "participants",
    "germany_employees_estimate",
    "participation_rate_pct",
    "top_20_pace_formatted",
    "median_pace_formatted",
    "endurance_multiple",
    "yearly_return_pct",
]

leaderboard_cols = [col for col in leaderboard_cols if col in filtered.columns]

leaderboard = filtered[leaderboard_cols].copy()

if "participation_rate_pct" in leaderboard.columns:
    leaderboard["participation_rate_pct"] = leaderboard["participation_rate_pct"].round(2)

if "yearly_return_pct" in leaderboard.columns:
    leaderboard["yearly_return_pct"] = leaderboard["yearly_return_pct"].round(2)

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True
)

st.divider()


# -------------------------
# PARTICIPATION RATE VS PACE
# -------------------------

st.subheader("📈 Top 20% Pace vs Participation Rate")

scatter_filtered = filtered.dropna(
    subset=["participation_rate_pct", "top_20_pace"]
)

fig = px.scatter(
    scatter_filtered,
    x="participation_rate_pct",
    y="top_20_pace",
    hover_name="matched_company",
    size="participants",
    color="sector",
    labels={
        "participation_rate_pct": "Participation Rate (% of German employees)",
        "top_20_pace": "Top 20% Pace (min/km)",
        "sector": "Sector",
    },
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------
# OVERALL YEARLY TRENDS
# -------------------------

st.subheader("📊 Overall FitnessDAX Trends")

trend_df = (
    df[
        (df["sector"].isin(selected_sectors))
        & (df["cluster"].isin(selected_clusters))
    ]
    .copy()
)

trend_df = trend_df.dropna(
    subset=[
        "year",
        "participation_rate_pct",
        "median_pace",
        "yearly_return_pct",
    ]
)

overall_trend_df = (
    trend_df
    .groupby("year", as_index=False)
    .agg(
        avg_participation_rate_pct=("participation_rate_pct", "mean"),
        avg_median_pace=("median_pace", "mean"),
        avg_stock_return_pct=("yearly_return_pct", "mean"),
    )
    .sort_values("year")
)

fig_overall = go.Figure()

fig_overall.add_trace(
    go.Scatter(
        x=overall_trend_df["year"],
        y=overall_trend_df["avg_stock_return_pct"],
        name="Avg Stock Return (%)",
        mode="lines+markers",
        connectgaps=True,
    )
)

fig_overall.add_trace(
    go.Scatter(
        x=overall_trend_df["year"],
        y=overall_trend_df["avg_median_pace"],
        name="Avg Median Pace (min/km)",
        mode="lines+markers",
        yaxis="y2",
        connectgaps=True,
    )
)

fig_overall.add_trace(
    go.Scatter(
        x=overall_trend_df["year"],
        y=overall_trend_df["avg_participation_rate_pct"],
        name="Avg Participation Rate (%)",
        mode="lines+markers",
        yaxis="y3",
        connectgaps=True,
    )
)

fig_overall.update_layout(
    title="All Companies Combined: Stock Performance, Median Pace and Participation Rate",
    xaxis=dict(title="Year"),
    yaxis=dict(
        title="Avg Stock Return (%)",
        side="left",
    ),
    yaxis2=dict(
        title="Avg Median Pace (min/km)",
        overlaying="y",
        side="right",
        autorange="reversed",
    ),
    yaxis3=dict(
        title="Avg Participation Rate (%)",
        overlaying="y",
        side="right",
        position=0.95,
        anchor="free",
    ),
    hovermode="x unified",
)

st.plotly_chart(
    fig_overall,
    use_container_width=True
)

st.caption(
    "This chart combines all selected companies and shows average values per year. Lower median pace means faster runners."
)

st.divider()

# -------------------------
# CLUSTER OVERVIEW
# -------------------------

st.subheader("🧩 Cluster Overview")

cluster_df = (
    filtered
    .groupby("cluster", as_index=False)
    .agg(
        companies=("matched_company", "nunique"),
        participants=("participants", "sum"),
        avg_participation_rate_pct=("participation_rate_pct", "mean"),
        avg_top_20_pace=("top_20_pace", "mean"),
        avg_stock_return_pct=("yearly_return_pct", "mean"),
    )
)

cluster_df["avg_participation_rate_pct"] = cluster_df["avg_participation_rate_pct"].round(2)
cluster_df["avg_stock_return_pct"] = cluster_df["avg_stock_return_pct"].round(2)
cluster_df["avg_top_20_pace_formatted"] = cluster_df["avg_top_20_pace"].apply(pace_to_mmss)

st.dataframe(
    cluster_df[
        [
            "cluster",
            "companies",
            "participants",
            "avg_participation_rate_pct",
            "avg_top_20_pace_formatted",
            "avg_stock_return_pct",
        ]
    ].sort_values("avg_participation_rate_pct", ascending=False),
    use_container_width=True,
    hide_index=True
)

st.divider()


# -------------------------
# FITNESS VS STOCK
# -------------------------

st.subheader("💸 Fitness vs Stock Performance")

stock_filtered = filtered.dropna(
    subset=["yearly_return_pct", "participation_rate_pct"]
)

fig_stock = px.scatter(
    stock_filtered,
    x="participation_rate_pct",
    y="yearly_return_pct",
    hover_name="matched_company",
    color="sector",
    size="participants",
    labels={
        "participation_rate_pct": "Participation Rate (% of German employees)",
        "yearly_return_pct": "Stock Return (%)",
        "sector": "Sector",
    },
)

st.plotly_chart(fig_stock, use_container_width=True)

st.divider()


# -------------------------
# COMPANY TRENDS
# -------------------------

st.subheader("📊 Company Trends")

companies = sorted(df["matched_company"].dropna().unique())

selected_company = st.selectbox(
    "Select company",
    companies
)

company_df = (
    df[df["matched_company"] == selected_company]
    .copy()
    .sort_values("year")
)

company_df = company_df.drop_duplicates(
    subset=["year"]
)

fig_company = go.Figure()

fig_company.add_trace(
    go.Scatter(
        x=company_df["year"],
        y=company_df["yearly_return_pct"],
        name="Stock Return (%)",
        mode="lines+markers",
        connectgaps=True,
    )
)

fig_company.add_trace(
    go.Scatter(
        x=company_df["year"],
        y=company_df["top_20_pace"],
        name="Top 20% Pace (min/km)",
        mode="lines+markers",
        yaxis="y2",
        connectgaps=True,
    )
)

fig_company.add_trace(
    go.Scatter(
        x=company_df["year"],
        y=company_df["participation_rate_pct"],
        name="Participation Rate (%)",
        mode="lines+markers",
        yaxis="y3",
        connectgaps=True,
    )
)

fig_company.update_layout(
    title=f"{selected_company}: Stock Performance, Pace and Participation",
    xaxis=dict(title="Year"),
    yaxis=dict(
        title="Stock Return (%)",
        side="left",
    ),
    yaxis2=dict(
        title="Top 20% Pace (min/km)",
        overlaying="y",
        side="right",
        autorange="reversed",
    ),
    yaxis3=dict(
        title="Participation Rate (%)",
        overlaying="y",
        side="right",
        position=0.95,
        anchor="free",
    ),
    hovermode="x unified",
)

st.plotly_chart(
    fig_company,
    use_container_width=True
)


# -------------------------
# COMPANY TABLE
# -------------------------

st.subheader("Selected company data")

company_cols = [
    "year",
    "matched_company",
    "ticker",
    "index",
    "sector",
    "cluster",
    "participants",
    "germany_employees_estimate",
    "participation_rate_pct",
    "top_20_pace",
    "top_20_pace_formatted",
    "median_pace",
    "median_pace_formatted",
    "yearly_return_pct",
    "races_entered",
    "endurance_multiple",
]

company_cols = [col for col in company_cols if col in company_df.columns]

company_table = company_df[company_cols].copy()

if "participation_rate_pct" in company_table.columns:
    company_table["participation_rate_pct"] = company_table["participation_rate_pct"].round(2)

if "yearly_return_pct" in company_table.columns:
    company_table["yearly_return_pct"] = company_table["yearly_return_pct"].round(2)

st.dataframe(
    company_table,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Lower pace means faster runners. Pace axes are reversed so that better fitness appears higher. German employee numbers are estimates and used for normalization."
)