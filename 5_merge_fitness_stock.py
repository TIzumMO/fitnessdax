import os
import pandas as pd

os.makedirs("output", exist_ok=True)

fitness = pd.read_csv("output/fitnessdax_ranking_by_year.csv")
stocks = pd.read_csv("data/stock_prices.csv")

merged = fitness.merge(
    stocks[
        [
            "year",
            "matched_company",
            "ticker",
            "yearly_return_pct"
        ]
    ],
    on=["year", "matched_company", "ticker"],
    how="outer"
)

merged.to_csv("output/fitnessdax_with_stocks.csv", index=False)

print(merged.head(30))
print("")
print("Saved merged data to output/fitnessdax_with_stocks.csv")