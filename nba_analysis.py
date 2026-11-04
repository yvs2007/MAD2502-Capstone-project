"""Analyze closing line errors."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "nba_odds_2018_2023.csv"
OUTPUT_DIR = ROOT / "results"
REQUIRED_COLUMNS = [
    "home_final",
    "away_final",
    "close_home_spread",
    "close_total",
]


def calculate_errors(data):
    """Calculate complete game errors."""
    games = data.dropna(subset=REQUIRED_COLUMNS).copy()
    games["spread_error"] = (
        games["home_final"] - games["away_final"]
        + games["close_home_spread"]
    )
    games["total_error"] = (
        games["home_final"] + games["away_final"] - games["close_total"]
    )
    return games


def summarize_errors(games):
    """Summarize error measurements."""
    rows = []
    for column, label in [
        ("spread_error", "Closing spread"),
        ("total_error", "Closing total"),
    ]:
        error = games[column]
        rows.append({
            "prediction": label,
            "games": error.count(),
            "mean_error": error.mean(),
            "mean_absolute_error": error.abs().mean(),
        })
    return pd.DataFrame(rows)


def main():
    """Run the analysis checkpoint."""
    data = pd.read_csv(DATA_FILE)
    games = calculate_errors(data)
    if games.empty:
        raise ValueError("No complete games available.")
    summary = summarize_errors(games)
    excluded = data.loc[data[REQUIRED_COLUMNS].isna().any(axis=1)]

    OUTPUT_DIR.mkdir(exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "error_summary.csv", index=False)
    excluded.to_csv(OUTPUT_DIR / "excluded_games.csv", index=False)
    data.head().to_csv(OUTPUT_DIR / "first_five.csv", index=False)
    data.tail().to_csv(OUTPUT_DIR / "last_five.csv", index=False)
    coverage = data.groupby("season")["date"].agg(["count", "min", "max"])
    coverage.to_csv(OUTPUT_DIR / "season_coverage.csv")

    lines = [
        f"Games loaded: {len(data)}",
        f"Columns loaded: {len(data.columns)}",
        f"Games analyzed: {len(games)}",
        f"Games excluded: {len(excluded)}",
    ]
    for row in summary.itertuples(index=False):
        lines.extend([
            "",
            row.prediction,
            f"Mean error: {row.mean_error:.3f}",
            f"Mean absolute error: {row.mean_absolute_error:.3f}",
        ])
    output = "\n".join(lines) + "\n"
    print(output, end="")
    (OUTPUT_DIR / "checkpoint_output.txt").write_text(output)


if __name__ == "__main__":
    main()
