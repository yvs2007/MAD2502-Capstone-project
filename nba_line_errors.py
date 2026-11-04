import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 10)

# 1. Load the data
df = pd.read_csv("nba_odds_2018_2023.csv", parse_dates=["date"])
print("Shape (rows, columns):", df.shape)

# 2. First and last 5 rows
cols = ["season", "date", "away_team", "home_team", "away_final", "home_final",
        "close_home_spread", "close_total"]
print("\nFirst 5 rows:")
print(df[cols].head())
print("\nLast 5 rows:")
print(df[cols].tail())

# 3. Missing values and games per season
missing = df.isna().sum()
print("\nColumns with missing values:")
print(missing[missing > 0])
print("\nGames per season:")
print(df["season"].value_counts().sort_index())

# 4. Errors (negative home spread means home is favored)
df["spread_error"] = df["home_final"] - df["away_final"] + df["close_home_spread"]
df["total_error"] = df["home_final"] + df["away_final"] - df["close_total"]
valid = df.dropna(subset=["spread_error", "total_error"])
print("\nValid games used:", len(valid))

# 5. Results table
summary = pd.DataFrame({
    "mean_error": [valid["spread_error"].mean(), valid["total_error"].mean()],
    "MAE": [valid["spread_error"].abs().mean(), valid["total_error"].abs().mean()],
}, index=["Closing spread", "Closing total"]).round(3)
print("\nResults:")
print(summary)

# 6. Chart: MAE by season
mae = valid.groupby("season")[["spread_error", "total_error"]].agg(
    lambda s: s.abs().mean())
mae.plot(kind="bar")
plt.title("Mean Absolute Error of Closing Lines by Season")
plt.xlabel("Season")
plt.ylabel("Mean absolute error (points)")
plt.legend(["Spread", "Total"])
plt.tight_layout()
plt.savefig("mae_by_season.png", dpi=150)
plt.show()