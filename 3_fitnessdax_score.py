import os
import math
import pandas as pd

os.makedirs("output", exist_ok=True)

df = pd.read_csv("data/fitnessdax_matches.csv")

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

MIN_PARTICIPANTS = 20

def top_20_percent_pace(group):
    group = group.sort_values("pace_min_per_km", ascending=True)
    top_n = max(1, math.ceil(len(group) * 0.20))
    return group.head(top_n)["pace_min_per_km"].median()

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

company = company[company["participants"] >= MIN_PARTICIPANTS].copy()

# Main FitnessDAX rank:
# Lower Top 20% pace = better
company["fitnessdax_rank"] = (
    company.groupby("year")["top_20_pace"]
    .rank(method="first", ascending=True)
    .astype(int)
)

# Broad Fitness Rank:
# Lower median pace = better
company["median_pace_rank"] = (
    company.groupby("year")["median_pace"]
    .rank(method="first", ascending=True)
    .astype(int)
)

# Endurance Multiple:
# More participants = better, faster median pace = better
company["endurance_multiple"] = (
    company["participants"].apply(lambda x: math.log10(x)) / company["median_pace"]
)

company["endurance_multiple_rank"] = (
    company.groupby("year")["endurance_multiple"]
    .rank(method="first", ascending=False)
    .astype(int)
)

def pace_to_mmss(pace):
    minutes = int(pace)
    seconds = round((pace - minutes) * 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"

company["top_20_pace_formatted"] = company["top_20_pace"].apply(pace_to_mmss)
company["median_pace_formatted"] = company["median_pace"].apply(pace_to_mmss)
company["average_pace_formatted"] = company["average_pace"].apply(pace_to_mmss)
company["fastest_pace_formatted"] = company["fastest_pace"].apply(pace_to_mmss)
company["slowest_pace_formatted"] = company["slowest_pace"].apply(pace_to_mmss)

company["endurance_multiple"] = company["endurance_multiple"].round(3)

ranking = company.sort_values(["year", "fitnessdax_rank"], ascending=[True, True])

ranking = ranking[
    [
        "year",
        "fitnessdax_rank",
        "matched_company",
        "ticker",
        "index",
        "participants",
        "races_entered",
        "top_20_pace",
        "top_20_pace_formatted",
        "median_pace",
        "median_pace_formatted",
        "median_pace_rank",
        "average_pace_formatted",
        "fastest_pace_formatted",
        "slowest_pace_formatted",
        "endurance_multiple",
        "endurance_multiple_rank",
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