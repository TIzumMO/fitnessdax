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
    "median_pace",
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

Happy to cooperate on further analysis.

Most importantly: This is not financial advice 😄
""")

st.sidebar.divider()

st.sidebar.markdown("**Timo Radzik**")
st.sidebar.markdown("💼 [LinkedIn](https://www.linkedin.com/in/timo-radzik/)")


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
# LEADERBOARD FILTERS
# -------------------------

with st.expander("Filter leaderboard", expanded=False):
    years = sorted(df["year"].dropna().unique(), reverse=True)

    selected_year = st.selectbox(
        "Year",
        years
    )

    available_sectors = sorted(df["sector"].dropna().unique())

    selected_sectors_leaderboard = st.multiselect(
        "Sector",
        available_sectors,
        default=available_sectors
    )

leaderboard_filtered = df[
    (df["year"] == selected_year)
    & (df["sector"].isin(selected_sectors_leaderboard))
].copy()

leaderboard_filtered = leaderboard_filtered.dropna(subset=["fitnessdax_rank"])
leaderboard_filtered = leaderboard_filtered.sort_values("fitnessdax_rank")

st.subheader(f"🏆 FitnessDAX Leaderboard ({selected_year})")

# -------------------------
# METRICS
# -------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Companies",
    len(leaderboard_filtered)
)

col2.metric(
    "Total Participants",
    int(leaderboard_filtered["participants"].sum()) if len(leaderboard_filtered) > 0 else 0
)

median_pace = (
    leaderboard_filtered["median_pace"].mean()
    if len(leaderboard_filtered) > 0 else None
)

col3.metric(
    "Median Pace",
    pace_to_mmss(median_pace)
)

avg_participation = (
    leaderboard_filtered["participation_rate_pct"].mean()
    if "participation_rate_pct" in leaderboard_filtered.columns and len(leaderboard_filtered) > 0 else None
)

col4.metric(
    "Avg Participation Rate",
    format_pct(avg_participation)
)

# -------------------------
# LEADERBOARD
# -------------------------

leaderboard_cols = [
    "fitnessdax_rank",
    "matched_company",
    "index",
    "sector",
    "participants",
    "germany_employees_estimate",
    "participation_rate_pct",
    "median_pace_formatted",
    "yearly_return_pct",
]

leaderboard_cols = [col for col in leaderboard_cols if col in leaderboard_filtered.columns]

leaderboard = leaderboard_filtered[leaderboard_cols].copy()

if "participation_rate_pct" in leaderboard.columns:
    leaderboard["participation_rate_pct"] = leaderboard["participation_rate_pct"].round(2)

if "yearly_return_pct" in leaderboard.columns:
    leaderboard["yearly_return_pct"] = leaderboard["yearly_return_pct"].round(2)

leaderboard = leaderboard.rename(
    columns={
        "fitnessdax_rank": "Rank",
        "matched_company": "Company",
        "index": "Index",
        "sector": "Sector",
        "participants": "Participants",
        "germany_employees_estimate": "Employees (DE)",
        "participation_rate_pct": "Participation (%)",
        "median_pace_formatted": "Median Pace",
        "yearly_return_pct": "Stock Return (%)",
    }
)

for col in ["Participants", "Employees (DE)", "Participation (%)", "Stock Return (%)"]:
    if col in leaderboard.columns:
        leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce")

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Participants": st.column_config.NumberColumn(
            "Participants",
            format="%d"
        ),
        "Employees (DE)": st.column_config.NumberColumn(
            "Employees (DE)",
            format="%d"
        ),
        "Participation (%)": st.column_config.NumberColumn(
            "Participation (%)",
            format="%.2f%%"
        ),
        "Stock Return (%)": st.column_config.NumberColumn(
            "Stock Return (%)",
            format="%.2f%%"
        ),
    }
)

st.divider()

# -------------------------
# OVERALL YEARLY TRENDS
# -------------------------

st.subheader("📊 Overall FitnessDAX Trends")

trend_df = df.copy()

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
# ANIMATED FITNESS VS STOCK
# -------------------------

st.subheader("💸 Participation vs Stock Performance Over Time")

animated_df = df.copy()

animated_df = animated_df.dropna(
    subset=[
        "participation_rate_pct",
        "yearly_return_pct",
        "participants",
        "year",
    ]
)

fig_animated = px.scatter(
    animated_df,
    x="participation_rate_pct",
    y="yearly_return_pct",
    animation_frame="year",
    animation_group="matched_company",
    hover_name="matched_company",
    size="participants",
    color="sector",
    size_max=60,
    range_x=[
        0,
        animated_df["participation_rate_pct"].max() * 1.1
    ],
    range_y=[
        animated_df["yearly_return_pct"].min() * 1.1,
        animated_df["yearly_return_pct"].max() * 1.1
    ],
    labels={
        "participation_rate_pct": "Participation Rate (%)",
        "yearly_return_pct": "Stock Return (%)",
        "participants": "Participants",
        "sector": "Sector",
    },
)

fig_animated.update_layout(
    height=700
)

st.plotly_chart(
    fig_animated,
    use_container_width=True
)

st.caption(
    "Each bubble represents a company. Bubble size reflects participant count. The animation shows how companies move through participation and stock performance space over time."
)

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
        y=company_df["median_pace"],
        name="Median Pace (min/km)",
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
        title="Median Pace (min/km)",
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
    "participants",
    "germany_employees_estimate",
    "participation_rate_pct",
    "median_pace_formatted",
    "yearly_return_pct",
    "races_entered",
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