import os
import math
import pandas as pd

os.makedirs("output", exist_ok=True)

df = pd.read_csv("data/fitnessdax_matches.csv")
employees_df = pd.read_csv("data/germany_employees.csv")

df = df.drop_duplicates(
    subset=[
        "first_name",
        "last_name",
        "company",
        "time",
        "city",
        "year",
        "matched_company"
    ]
)

MIN_PARTICIPANTS = 10

def top_20_percent_pace(group):
    group = group.sort_values("pace_min_per_km", ascending=True)
    top_n = max(1, math.ceil(len(group) * 0.20))
    return group.head(top_n)["pace_min_per_km"].median()

def pace_to_mmss(pace):
    if pd.isna(pace):
        return "-"
    minutes = int(pace)
    seconds = round((pace - minutes) * 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"

base_metrics = (
    df.groupby(["year", "matched_company", "ticker", "index"])
    .agg(
        participants=("matched_company", "size"),
        races_entered=("competition_id", "nunique"),
        median_pace=("pace_min_per_km", "median"),
        average_pace=("pace_min_per_km", "mean"),
        fastest_pace=("pace_min_per_km", "min"),
        slowest_pace=("pace_min_per_km", "max"),
    )
    .reset_index()
)

top20 = (
    df.groupby(["year", "matched_company", "ticker", "index"])
    .apply(top_20_percent_pace)
    .reset_index(name="top_20_pace")
)

company = base_metrics.merge(
    top20,
    on=["year", "matched_company", "ticker", "index"],
    how="left"
)

# -------------------------
# ADD EMPLOYEE METADATA
# -------------------------

company["ticker"] = company["ticker"].astype(str).str.strip().str.upper()
employees_df["ticker"] = employees_df["ticker"].astype(str).str.strip().str.upper()

company = company.merge(
    employees_df[
        [
            "ticker",
            "sector",
            "cluster",
            "germany_employees_estimate"
        ]
    ],
    on="ticker",
    how="left"
)

company["participation_rate"] = (
    company["participants"] / company["germany_employees_estimate"]
)

company["participation_rate_pct"] = company["participation_rate"] * 100

company = company[company["participants"] >= MIN_PARTICIPANTS].copy()

# -------------------------
# MAIN FITNESSDAX SCORE
# -------------------------
# Absolute benchmark score
# Higher participation = better
# Lower median pace = better

TARGET_PARTICIPATION_RATE = 5.0
BEST_REASONABLE_PACE = 4.5
WORST_REASONABLE_PACE = 8.0

company["participation_score"] = (
    company["participation_rate_pct"] / TARGET_PARTICIPATION_RATE
).clip(0, 1)

company["pace_score"] = (
    (WORST_REASONABLE_PACE - company["median_pace"])
    / (WORST_REASONABLE_PACE - BEST_REASONABLE_PACE)
).clip(0, 1)

company["fitness_score"] = (
    company["participation_score"] * 0.7
    + company["pace_score"] * 0.3
)

company["fitness_score_100"] = company["fitness_score"] * 100

company["fitnessdax_rank"] = (
    company.groupby("year")["fitness_score"]
    .rank(method="first", ascending=False)
    .astype(int)
)

# -------------------------
# SUPPORTING RANKS
# -------------------------

company["participation_rate_rank"] = (
    company.groupby("year")["participation_rate"]
    .rank(method="first", ascending=False)
    .astype(int)
)

company["median_pace_rank"] = (
    company.groupby("year")["median_pace"]
    .rank(method="first", ascending=True)
    .astype(int)
)

company["top_20_pace_rank"] = (
    company.groupby("year")["top_20_pace"]
    .rank(method="first", ascending=True)
    .astype(int)
)

company["participation_multiple"] = (
    company["participants"].apply(lambda x: math.log10(x)) / company["median_pace"]
)

company["participation_multiple_rank"] = (
    company.groupby("year")["participation_multiple"]
    .rank(method="first", ascending=False)
    .astype(int)
)

# -------------------------
# FORMATTING
# -------------------------

company["top_20_pace_formatted"] = company["top_20_pace"].apply(pace_to_mmss)
company["median_pace_formatted"] = company["median_pace"].apply(pace_to_mmss)
company["average_pace_formatted"] = company["average_pace"].apply(pace_to_mmss)
company["fastest_pace_formatted"] = company["fastest_pace"].apply(pace_to_mmss)
company["slowest_pace_formatted"] = company["slowest_pace"].apply(pace_to_mmss)

company["participation_multiple"] = company["participation_multiple"].round(3)
company["participation_rate_pct"] = company["participation_rate_pct"].round(2)
company["fitness_score"] = company["fitness_score"].round(4)
company["fitness_score_100"] = company["fitness_score_100"].round(1)

ranking = company.sort_values(["year", "fitnessdax_rank"], ascending=[True, True])

ranking = ranking[
    [
        "year",
        "fitnessdax_rank",
        "fitness_score",
        "fitness_score_100",
        "matched_company",
        "ticker",
        "index",
        "sector",
        "cluster",
        "participants",
        "germany_employees_estimate",
        "participation_rate",
        "participation_rate_pct",
        "participation_rate_rank",
        "races_entered",
        "top_20_pace",
        "top_20_pace_formatted",
        "top_20_pace_rank",
        "median_pace",
        "median_pace_formatted",
        "median_pace_rank",
        "average_pace_formatted",
        "fastest_pace_formatted",
        "slowest_pace_formatted",
        "participation_multiple",
        "participation_multiple_rank",
    ]
]

ranking.to_csv("output/fitnessdax_ranking_by_year.csv", index=False)

events_overview = (
    df.groupby(["year", "city", "competition_id", "source_url"])
    .size()
    .reset_index(name="matched_runner_count")
    .sort_values(["year", "city"])
)

events_overview.to_csv("output/fitnessdax_events_overview.csv", index=False)

print(ranking.head(30))
print("")
print("Saved ranking to output/fitnessdax_ranking_by_year.csv")
print("Saved event overview to output/fitnessdax_events_overview.csv")