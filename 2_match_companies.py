import pandas as pd

# -----------------------------
# Load files
# -----------------------------

results = pd.read_csv("data/b2run_results_structured.csv")

listed = pd.read_csv("listed_companies.csv", sep=",", engine="python")
aliases = pd.read_csv("company_aliases.csv", sep=",", engine="python")

# Emergency fix: if pandas reads the whole CSV as one column
if list(listed.columns) == ["company_name,ticker,index"]:
    listed = pd.read_csv("listed_companies.csv", header=None, names=["raw"])
    listed = listed["raw"].str.split(",", expand=True)
    listed.columns = ["company_name", "ticker", "index"]
    listed = listed.iloc[1:].reset_index(drop=True)

if list(aliases.columns) == ["alias,matched_company"]:
    aliases = pd.read_csv("company_aliases.csv", header=None, names=["raw"])
    aliases = aliases["raw"].str.split(",", expand=True)
    aliases.columns = ["alias", "matched_company"]
    aliases = aliases.iloc[1:].reset_index(drop=True)

# -----------------------------
# Normalize helper
# -----------------------------

def normalize(text):
    text = str(text).lower()

    replacements = [
        " ag ",
        " se ",
        " gmbh ",
        " holding ",
        " group ",
        " deutschland ",
        "&",
        "-",
        ".",
        ","
    ]

    text = f" {text} "

    for r in replacements:
        text = text.replace(r, " ")

    text = " ".join(text.split())

    return text

# -----------------------------
# Normalize all tables
# -----------------------------

results["company_normalized"] = results["company"].apply(normalize)

listed["company_normalized"] = listed["company_name"].apply(normalize)

aliases["alias_normalized"] = aliases["alias"].apply(normalize)
aliases["matched_company_normalized"] = aliases["matched_company"].apply(normalize)

# -----------------------------
# Step 1: Alias matching
# -----------------------------

alias_matches = []

for _, alias_row in aliases.iterrows():

    alias_norm = alias_row["alias_normalized"]
    canonical_norm = alias_row["matched_company_normalized"]

    # Find canonical company row
    canonical_company = listed[
        listed["company_normalized"] == canonical_norm
    ]

    if canonical_company.empty:
        continue

    canonical_company = canonical_company.iloc[0]

    matched_rows = results[
        results["company_normalized"] == alias_norm
    ]

    if len(matched_rows) > 0:

        matched_rows = matched_rows.copy()

        matched_rows["matched_company"] = canonical_company["company_name"]
        matched_rows["ticker"] = canonical_company["ticker"]
        matched_rows["index"] = canonical_company["index"]

        alias_matches.append(matched_rows)

# Combine alias matches
alias_df = (
    pd.concat(alias_matches, ignore_index=True)
    if alias_matches else pd.DataFrame()
)

# -----------------------------
# Step 2: Direct/fuzzy matching
# -----------------------------

remaining_results = results.copy()

if not alias_df.empty:

    matched_companies = set(
        alias_df["company"]
    )

    remaining_results = remaining_results[
        ~remaining_results["company"].isin(matched_companies)
    ]

direct_matches = []

for _, company in listed.iterrows():

    company_norm = company["company_normalized"]

    matched_rows = remaining_results[
        remaining_results["company_normalized"].str.contains(company_norm, na=False)
    ]

    if len(matched_rows) > 0:

        matched_rows = matched_rows.copy()

        matched_rows["matched_company"] = company["company_name"]
        matched_rows["ticker"] = company["ticker"]
        matched_rows["index"] = company["index"]

        direct_matches.append(matched_rows)

direct_df = (
    pd.concat(direct_matches, ignore_index=True)
    if direct_matches else pd.DataFrame()
)

# -----------------------------
# Combine all matches
# -----------------------------

matched_df = pd.concat(
    [alias_df, direct_df],
    ignore_index=True
)

# -----------------------------
# Remove duplicates
# -----------------------------

matched_df = matched_df.drop_duplicates(
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

# -----------------------------
# Create unmatched companies list
# -----------------------------

matched_original_companies = set(matched_df["company"].dropna().unique())

unmatched_df = results[
    ~results["company"].isin(matched_original_companies)
].copy()

unmatched_companies = (
    unmatched_df[["company", "company_normalized"]]
    .drop_duplicates()
    .sort_values("company")
)

unmatched_companies.to_csv("data/unmatched_companies.csv", index=False)

# -----------------------------
# Save
# -----------------------------

matched_df.to_csv("data/fitnessdax_matches.csv", index=False)

print("")
print(f"Alias matches: {len(alias_df)}")
print(f"Direct matches: {len(direct_df)}")
print(f"Total matched runner entries: {len(matched_df)}")
print(f"Unmatched companies: {len(unmatched_companies)}")
print("")
print("Saved to data/fitnessdax_matches.csv")
print("Saved to data/unmatched_companies.csv")