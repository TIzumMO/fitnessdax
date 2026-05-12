import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="FitnessDAX",
    layout="wide"
)

st.title("🦡 FitnessDAX")
st.subheader("Germany's fittest publicly traded companies")
st.caption(
    "FitnessDAX is a hobby data experiment based on publicly available B2Run race data. No financial advice!"
)

st.divider()

df = pd.read_csv("output/fitnessdax_with_stocks.csv")

def pace_to_mmss(pace):
    if pd.isna(pace):
        return "-"
    minutes = int(pace)
    seconds = round((pace - minutes) * 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"

# -------------------------
# YEAR SELECTION
# -------------------------

years = sorted(df["year"].dropna().unique(), reverse=True)

selected_year = st.selectbox(
    "Select Year",
    years
)

filtered = df[
    df["year"] == selected_year
].copy()

filtered = filtered.dropna(subset=["fitnessdax_rank"])
filtered = filtered.sort_values("fitnessdax_rank")

# -------------------------
# METRICS
# -------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Companies",
    len(filtered)
)

col2.metric(
    "Total Participants",
    int(filtered["participants"].sum())
)

avg_top20_pace = (
    filtered["top_20_pace"].mean()
    if len(filtered) > 0 else None
)

col3.metric(
    "Average Top 20% Pace",
    pace_to_mmss(avg_top20_pace)
)

st.divider()

# -------------------------
# LEADERBOARD
# -------------------------

st.subheader("🏆 FitnessDAX Leaderboard")

st.dataframe(
    filtered[
        [
            "fitnessdax_rank",
            "matched_company",
            "ticker",
            "yearly_return_pct",
            "index",
            "participants",
            "races_entered",
            "top_20_pace_formatted",
            "median_pace_formatted",
            "endurance_multiple",
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.divider()

# -------------------------
# PACE VS PARTICIPATION
# -------------------------

st.subheader("📈 Top 20% Pace vs Participation")

fig = px.scatter(
    filtered,
    x="participants",
    y="top_20_pace",
    hover_name="matched_company",
    size="races_entered",
    color="index",
    labels={
        "participants": "Participants",
        "top_20_pace": "Top 20% Pace (min/km)",
        "index": "Index",
    },
)

fig.update_yaxes(autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------
# FITNESS VS STOCK
# -------------------------

st.subheader("💸 Fitness vs Stock Performance")

stock_filtered = filtered.dropna(
    subset=["yearly_return_pct", "top_20_pace"]
)

fig_stock = px.scatter(
    stock_filtered,
    x="top_20_pace",
    y="yearly_return_pct",
    hover_name="matched_company",
    color="index",
    size="participants",
    labels={
        "top_20_pace": "Top 20% Pace (min/km)",
        "yearly_return_pct": "Stock Return (%)",
        "index": "Index",
    },
)

fig_stock.update_xaxes(autorange="reversed")

st.plotly_chart(fig_stock, use_container_width=True)

st.divider()

# -------------------------
# COMPANY TRENDS
# -------------------------

st.subheader("📊 Company Trends")

companies = sorted(
    df["matched_company"].dropna().unique()
)

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

company_df["yearly_return_pct"] = pd.to_numeric(
    company_df["yearly_return_pct"],
    errors="coerce"
)

company_df["top_20_pace"] = pd.to_numeric(
    company_df["top_20_pace"],
    errors="coerce"
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

fig_company.update_layout(
    title=f"{selected_company}: Stock Performance vs Top 20% Pace",
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

st.dataframe(
    company_df[
        [
            "year",
            "matched_company",
            "ticker",
            "top_20_pace",
            "top_20_pace_formatted",
            "median_pace",
            "median_pace_formatted",
            "yearly_return_pct",
            "participants",
            "races_entered",
            "endurance_multiple",
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Lower pace means faster runners. Pace axes are reversed so that better fitness appears higher."
)