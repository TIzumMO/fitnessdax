import pandas as pd
import yfinance as yf
from datetime import datetime

# Load companies
ranking = pd.read_csv("output/fitnessdax_ranking_by_year.csv")

companies = (
    ranking[["matched_company", "ticker"]]
    .drop_duplicates()
    .dropna()
)

YEARS = [2023, 2024, 2025]

results = []

for _, row in companies.iterrows():
    company = row["matched_company"]
    ticker = row["ticker"]

    print(f"Loading {company} ({ticker})")

    try:
        stock = yf.Ticker(ticker)

        hist = stock.history(
            start="2022-12-01",
            end="2025-12-31",
            auto_adjust=True
        )

        if hist.empty:
            print(f"No data for {ticker}")
            continue

        hist = hist.reset_index()

        hist["year"] = hist["Date"].dt.year

        for year in YEARS:
            year_data = hist[hist["year"] == year]

            if len(year_data) == 0:
                continue

            start_price = year_data.iloc[0]["Close"]
            end_price = year_data.iloc[-1]["Close"]

            yearly_return = (
                (end_price - start_price) / start_price
            ) * 100

            results.append({
                "year": year,
                "matched_company": company,
                "ticker": ticker,
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "yearly_return_pct": round(yearly_return, 2),
            })

    except Exception as e:
        print(f"Error for {ticker}: {e}")

stock_df = pd.DataFrame(results)

stock_df.to_csv("data/stock_prices.csv", index=False)

print("")
print("Saved stock prices to data/stock_prices.csv")