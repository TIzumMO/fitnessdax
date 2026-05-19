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
    return f"{value:.1f}%"


# -------------------------
# LOAD DATA
# -------------------------

df = pd.read_csv("output/fitnessdax_final.csv")

numeric_cols = [
    "year",
    "participants",
    "races_entered",
    "median_pace",
    "yearly_return_pct",
    "germany_employees_estimate",
    "participation_rate",
    "participation_rate_pct",
    "fitness_score",
    "fitness_score_100",
    "fitnessdax_rank",
    "culture_score",
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

st.subheader(f"🏆 FitnessDAX Leaderboard ({int(selected_year)})")

st.info(

    "The Fitness Score combines workforce participation and median pace. "

    "Participation is benchmarked against a 5% employee participation target. Companies with less than 10 participants are excluded. "

    "Median pace is benchmarked between 4:30/km and 8:00/km. "

    "The final score is based on 70% employee participation benchmark and 30% median pace benchmark. "

    "The score ranges from 0 to 100."

)


# -------------------------
# METRICS
# -------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Companies",
    len(leaderboard_filtered)
)

col2.metric(
    "Participants",
    f"{int(leaderboard_filtered['participants'].sum()):,}"
    if len(leaderboard_filtered) > 0 else "0"
)

avg_participation = (
    leaderboard_filtered["participation_rate_pct"].mean()
    if "participation_rate_pct" in leaderboard_filtered.columns
    and len(leaderboard_filtered) > 0
    else None
)

col3.metric(
    "Avg Participation Rate",
    f"{avg_participation:.1f}%"
    if pd.notna(avg_participation)
    else "-"
)

median_pace = (
    leaderboard_filtered["median_pace"].mean()
    if len(leaderboard_filtered) > 0
    else None
)

col4.metric(
    "Avg Median Pace",
    pace_to_mmss(median_pace)
)


# -------------------------
# LEADERBOARD
# -------------------------

leaderboard_cols = [
    "fitnessdax_rank",
    "matched_company",
    "fitness_score_100",
    "index",
    "sector",
    "participants",
    "germany_employees_estimate",
    "culture_score",
    "participation_rate_pct",
    "median_pace_formatted",
    "yearly_return_pct",
]

leaderboard_cols = [
    col for col in leaderboard_cols
    if col in leaderboard_filtered.columns
]

leaderboard = leaderboard_filtered[leaderboard_cols].copy()

if "fitness_score_100" in leaderboard.columns:
    leaderboard["fitness_score_100"] = leaderboard["fitness_score_100"].round(1)

if "participation_rate_pct" in leaderboard.columns:
    leaderboard["participation_rate_pct"] = leaderboard["participation_rate_pct"].round(1)

if "yearly_return_pct" in leaderboard.columns:
    leaderboard["yearly_return_pct"] = leaderboard["yearly_return_pct"].round(1)

leaderboard = leaderboard.rename(
    columns={
        "fitnessdax_rank": "Rank",
        "matched_company": "Company",
        "fitness_score_100": "Fitness Score",
        "index": "Index",
        "sector": "Sector",
        "participants": "Participants",
        "germany_employees_estimate": "Employees (DE)",
        "culture_score": "Culture Score",
        "participation_rate_pct": "Participation (%)",
        "median_pace_formatted": "Median Pace",
        "yearly_return_pct": "Stock Return (%)",
    }
)

for col in [
    "Rank",
    "Fitness Score",
    "Participants",
    "Employees (DE)",
    "Culture Score",
    "Participation (%)",
    "Stock Return (%)",
]:
    if col in leaderboard.columns:
        leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce")

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(
            "Rank",
            format="%d"
        ),
        "Fitness Score": st.column_config.NumberColumn(
            "Fitness Score",
            format="%.1f"
        ),
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
            format="%.1f%%"
        ),
        "Stock Return (%)": st.column_config.NumberColumn(
            "Stock Return (%)",
            format="%.1f%%"
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
        "fitness_score_100",
        "yearly_return_pct",
    ]
)

overall_trend_df = (
    trend_df
    .groupby("year", as_index=False)
    .agg(
        avg_fitness_score=("fitness_score_100", "mean"),
        avg_stock_return_pct=("yearly_return_pct", "mean"),
    )
    .sort_values("year")
)

fig_overall = go.Figure()

fig_overall.add_trace(
    go.Scatter(
        x=overall_trend_df["year"],
        y=overall_trend_df["avg_fitness_score"],
        name="Avg Fitness Score",
        mode="lines+markers",
        connectgaps=True,
    )
)

fig_overall.add_trace(
    go.Scatter(
        x=overall_trend_df["year"],
        y=overall_trend_df["avg_stock_return_pct"],
        name="Avg Stock Return (%)",
        mode="lines+markers",
        yaxis="y2",
        connectgaps=True,
    )
)

fig_overall.update_layout(
    title="All Companies Combined: Fitness Score and Stock Performance",
    xaxis=dict(title="Year"),
    yaxis=dict(
        title="Avg Fitness Score",
        side="left",
    ),
    yaxis2=dict(
        title="Avg Stock Return (%)",
        overlaying="y",
        side="right",
    ),
    hovermode="x unified",
)

st.plotly_chart(
    fig_overall,
    use_container_width=True
)

st.caption(
    "FitnessDAX Score combines participation rate and median pace. Stock return is shown as the yearly return percentage."
)

st.divider()


# -------------------------
# ANIMATED FITNESS VS STOCK
# -------------------------

st.subheader("💸 Fitness Score vs Stock Performance Over Time")

animated_df = df.copy()

animated_df = animated_df.dropna(
    subset=[
        "fitness_score_100",
        "yearly_return_pct",
        "participants",
        "year",
    ]
)

if animated_df.empty:
    st.warning("Not enough data available for the animated chart.")
else:
    fig_animated = px.scatter(
        animated_df,
        x="fitness_score_100",
        y="yearly_return_pct",
        animation_frame="year",
        animation_group="matched_company",
        hover_name="matched_company",
        size="participants",
        color="sector",
        size_max=60,
        range_x=[
            0,
            animated_df["fitness_score_100"].max() * 1.1
        ],
        range_y=[
            animated_df["yearly_return_pct"].min() * 1.1,
            animated_df["yearly_return_pct"].max() * 1.1
        ],
        labels={
            "fitness_score_100": "Fitness Score",
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
        "Each bubble represents a company. Bubble size reflects participant count. The animation shows how companies move through Fitness Score and stock performance space over time."
    )

st.divider()


# -------------------------
# POSSIBLE LEADING INDICATORS
# -------------------------

st.subheader("🔮 Possible Leading Indicators")

st.markdown("""
The chart above compares fitness and stock performance in the same year.

But a more interesting question is whether company running culture could act as a **leading indicator**:

> Does stronger participation today show up in stock performance one year later?

This section compares current-year FitnessDAX metrics with **next-year stock returns**.  
This is exploratory and definitely not financial advice.
""")

prediction_df = df.copy()

prediction_df = prediction_df.sort_values(
    ["matched_company", "year"]
)

prediction_df["next_year_stock_return_pct"] = (
    prediction_df
    .groupby("matched_company")["yearly_return_pct"]
    .shift(-1)
)

prediction_df["fitness_score_change"] = (
    prediction_df
    .groupby("matched_company")["fitness_score_100"]
    .diff()
)

prediction_df["participation_rate_change_pct"] = (
    prediction_df
    .groupby("matched_company")["participation_rate_pct"]
    .diff()
)

lead_required_cols = [
    "next_year_stock_return_pct",
    "fitness_score_100",
    "participation_rate_pct",
    "participants",
    "races_entered",
    "median_pace",
]

if "culture_score" in prediction_df.columns:
    lead_required_cols.append("culture_score")

lead_df = prediction_df.dropna(
    subset=lead_required_cols
).copy()

if lead_df.empty:
    st.warning(
        "Not enough data available yet to calculate next-year leading indicator charts."
    )
else:
    # -------------------------
    # CORRELATION OVERVIEW
    # -------------------------

    indicator_map = {
        "Fitness Score": "fitness_score_100",
        "Participation Rate": "participation_rate_pct",
        "Participants": "participants",
        "Races Entered": "races_entered",
        "Median Pace": "median_pace",
    }

    if "culture_score" in lead_df.columns:
        indicator_map["Culture Score"] = "culture_score"

    correlation_rows = []

    for label, col in indicator_map.items():
        if col in lead_df.columns:
            corr = lead_df[col].corr(
                lead_df["next_year_stock_return_pct"]
            )

            correlation_rows.append(
                {
                    "Indicator": label,
                    "Correlation with Next-Year Stock Return": corr,
                }
            )

    correlation_df = pd.DataFrame(correlation_rows)

    if not correlation_df.empty:
        correlation_df["Correlation with Next-Year Stock Return"] = (
            correlation_df["Correlation with Next-Year Stock Return"].round(2)
        )

        st.dataframe(
            correlation_df.sort_values(
                "Correlation with Next-Year Stock Return",
                ascending=False
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Correlation with Next-Year Stock Return": st.column_config.NumberColumn(
                    "Correlation with Next-Year Stock Return",
                    format="%.2f"
                ),
            }
        )

    st.caption(
        "Positive values mean that higher current-year values are associated with higher stock returns in the following year. The dataset is small, so this should be read as exploration, not prediction."
    )

    st.divider()

    # -------------------------
    #  CULTURE SCORE VS NEXT-YEAR STOCK RETURN
    # -------------------------

    if "culture_score" in lead_df.columns:
        st.subheader("🏃 Culture Score vs Next-Year Stock Return")

        st.markdown("""
    The **Culture Score** combines company running scale and median pace:

    ```text
    Culture Score = log10(participants) / median pace

    It rewards companies that mobilize many runners, while preventing very large companies from dominating purely by size.

    Use the year filter below to select the stock return year.
    For example: selecting 2025 compares the 2024 Culture Score with the 2025 stock return.
    """)

    # Create explicit stock return year
    lead_df["stock_return_year"] = lead_df["year"] + 1

    available_return_years = sorted(
        lead_df["stock_return_year"].dropna().unique(),
        reverse=True
    )

    selected_return_year = st.selectbox(
        "Select stock return year",
        available_return_years,
        index=0,
        key="culture_score_return_year"
    )

    culture_score_chart_df = lead_df[
        lead_df["stock_return_year"] == selected_return_year
    ].copy()

    st.caption(
        f"Showing Culture Score from {int(selected_return_year) - 1} "
        f"against stock return in {int(selected_return_year)}."
    )

    fig_culture_score_lead = px.scatter(
        culture_score_chart_df,
        x="culture_score",
        y="next_year_stock_return_pct",
        hover_name="matched_company",
        color="sector",
        size="participants",
        labels={
            "culture_score": f"Culture Score ({int(selected_return_year) - 1})",
            "next_year_stock_return_pct": f"Stock Return ({int(selected_return_year)})",
            "sector": "Sector",
            "participants": "Participants",
        },
    )

    fig_culture_score_lead.add_hline(
        y=0,
        line_dash="dash",
        annotation_text="0% stock return",
        annotation_position="bottom right"
    )

    st.plotly_chart(
        fig_culture_score_lead,
        use_container_width=True
    )

    st.caption(
        "Each point compares a company's previous-year Culture Score with its stock return in the selected year."
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
        y=company_df["fitness_score_100"],
        name="Fitness Score",
        mode="lines+markers",
        connectgaps=True,
    )
)

fig_company.add_trace(
    go.Scatter(
        x=company_df["year"],
        y=company_df["yearly_return_pct"],
        name="Stock Return (%)",
        mode="lines+markers",
        yaxis="y2",
        connectgaps=True,
    )
)

fig_company.add_trace(
    go.Scatter(
        x=company_df["year"],
        y=company_df["culture_score"],
        name="Culture Score",
        mode="lines+markers",
        yaxis="y3",
        connectgaps=True,
    )
)

fig_company.update_layout(
    title=f"{selected_company}: Fitness Score, Culture Score and Stock Performance",
    xaxis=dict(
        title="Year"
    ),
    yaxis=dict(
        title="Fitness Score",
        side="left",
    ),
    yaxis2=dict(
        title="Stock Return (%)",
        overlaying="y",
        side="right",
    ),
    yaxis3=dict(
        title="Culture Score",
        overlaying="y",
        side="right",
        anchor="free",
        position=0.95,
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
    "fitness_score_100",
    "participants",
    "germany_employees_estimate",
    "participation_rate_pct",
    "median_pace_formatted",
    "yearly_return_pct",
    "races_entered",
    "culture_score",
]

company_cols = [
    col for col in company_cols
    if col in company_df.columns
]

company_table = company_df[company_cols].copy()

if "fitness_score_100" in company_table.columns:
    company_table["fitness_score_100"] = company_table["fitness_score_100"].round(1)

if "participation_rate_pct" in company_table.columns:
    company_table["participation_rate_pct"] = company_table["participation_rate_pct"].round(1)

if "yearly_return_pct" in company_table.columns:
    company_table["yearly_return_pct"] = company_table["yearly_return_pct"].round(1)

if "culture_score" in company_table.columns:
    company_table["culture_score"] = company_table["culture_score"].round(3)

company_table = company_table.rename(
    columns={
        "year": "Year",
        "matched_company": "Company",
        "ticker": "Ticker",
        "index": "Index",
        "sector": "Sector",
        "fitness_score_100": "Fitness Score",
        "participants": "Participants",
        "germany_employees_estimate": "Employees (DE)",
        "participation_rate_pct": "Participation (%)",
        "median_pace_formatted": "Median Pace",
        "yearly_return_pct": "Stock Return (%)",
        "races_entered": "Races Entered",
        "culture_score": "Culture Score",
    }
)

for col in [
    "Year",
    "Fitness Score",
    "Participants",
    "Employees (DE)",
    "Participation (%)",
    "Stock Return (%)",
    "Races Entered",
    "Culture Score",
]:
    if col in company_table.columns:
        company_table[col] = pd.to_numeric(company_table[col], errors="coerce")

st.dataframe(
    company_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Year": st.column_config.NumberColumn(
            "Year",
            format="%d"
        ),
        "Fitness Score": st.column_config.NumberColumn(
            "Fitness Score",
            format="%.1f"
        ),
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
            format="%.1f%%"
        ),
        "Stock Return (%)": st.column_config.NumberColumn(
            "Stock Return (%)",
            format="%.1f%%"
        ),
        "Races Entered": st.column_config.NumberColumn(
            "Races Entered",
            format="%d"
        ),
        "Culture Score": st.column_config.NumberColumn(
            "Culture Score",
            format="%.3f"
        ),
    }
)
