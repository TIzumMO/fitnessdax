import pandas as pd

# Load full runners
all_results = pd.read_csv("data/b2run_results_structured.csv")

# Load matched runners
matched = pd.read_csv("data/fitnessdax_matches.csv")

# Normalize
def normalize(text):
    text = str(text).lower().strip()
    return " ".join(text.split())

all_results["company_norm"] = all_results["company"].apply(normalize)
matched["company_norm"] = matched["company"].apply(normalize)

matched_set = set(matched["company_norm"])

# Find unmatched companies
unmatched = (
    all_results[
        ~all_results["company_norm"].isin(matched_set)
    ]
    .groupby("company")
    .size()
    .reset_index(name="runner_count")
    .sort_values("runner_count", ascending=False)
)

# Save
unmatched.to_csv("output/unmatched_companies.csv", index=False)

print(unmatched.head(100))
print("")
print("Saved to output/unmatched_companies.csv")