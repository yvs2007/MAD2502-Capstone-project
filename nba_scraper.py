"""Scrape NBA scores and odds (2018-19 through 2022-23) from
sportsbookreviewsonline.com and save them to a CSV file.

Each season page holds one big HTML table with two rows per game
(visitor first, home second). This script downloads each season, pairs the
rows into one row per game, cleans the numbers, and writes a CSV.

Usage:
    pip install -r requirements.txt
    python nba_scraper.py
"""

import csv
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.sportsbookreviewsonline.com/scoresoddsarchives/nba-odds-{}"
FIRST_SEASON = 2018  # season starting in fall 2018 (2018-19)
LAST_SEASON = 2022   # season starting in fall 2022 (2022-23)
OUTPUT_FILE = "nba_odds_2018_2023.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PAUSE_SECONDS = 1  # be polite to the server
MIN_TOTAL = 80     # lowest believable half-game total
MAX_TOTAL = 300    # highest believable full-game total
MAX_SPREAD = 40    # biggest believable point spread

TABLE_COLUMNS = ["Date", "Rot", "VH", "Team", "1st", "2nd", "3rd", "4th",
                 "Final", "Open", "Close", "ML", "2H"]


def make_url(season):
    """Build the page URL for a season, e.g. 2018 -> .../nba-odds-2018-19"""
    return BASE_URL.format(f"{season}-{str(season + 1)[-2:]}")


def get_html(url):
    """Download a page and return its HTML text."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def get_rows(html):
    """Pull the odds table out of the HTML as a list of rows of text."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        rows.append(cells)
    return rows


def make_frame(rows):
    """Turn the raw rows into a DataFrame, dropping the header row."""
    header, data = rows[0], rows[1:]
    if header != TABLE_COLUMNS:
        raise ValueError(f"Unexpected table header: {header}")
    return pd.DataFrame(data, columns=TABLE_COLUMNS)


def to_number(series):
    """Convert text to numbers; 'pk' (pick'em) becomes 0, 'NL' etc. become NaN."""
    series = series.replace({"pk": "0", "PK": "0", "Pk": "0"})
    return pd.to_numeric(series, errors="coerce")


def clean_numbers(df):
    """Make every column except VH and Team numeric."""
    for col in df.columns:
        if col not in ("VH", "Team"):
            df[col] = to_number(df[col])
    return df


def add_dates(df, season):
    """Turn the MMDD Date column into real dates.

    Games are in order, so the year goes up by one each time the month
    drops (December -> January).
    """
    month = (df["Date"] // 100).to_numpy()
    day = (df["Date"] % 100).to_numpy()
    new_year = np.insert(np.diff(month) < 0, 0, False)
    year = season + np.cumsum(new_year)
    df["Date"] = pd.to_datetime(
        pd.DataFrame({"year": year, "month": month, "day": day}))
    return df


def split_line(first, second):
    """Split two numbers (one per team) into a spread and a total.

    The bigger number is the game total, the smaller is the spread and
    belongs to the favorite. Returns (spread_for_first, spread_for_second, total).
    Rows with impossible values (typos in the source) become NaN.
    """
    total = np.maximum(first, second)
    spread = np.minimum(first, second)
    first_is_fav = first <= second
    first_spread = np.where(first_is_fav, -spread, spread)
    # Half-time totals are ~100-130, full-game totals ~170-270.
    bad = (total < MIN_TOTAL) | (total > MAX_TOTAL) | (spread > MAX_SPREAD)
    total = np.where(bad, np.nan, total)
    first_spread = np.where(bad, np.nan, first_spread)
    return first_spread, -first_spread, total


def make_games(df):
    """Combine each visitor/home row pair into one game row."""
    away = df.iloc[0::2].reset_index(drop=True)
    home = df.iloc[1::2].reset_index(drop=True)
    # Neutral-site games (London, Mexico City, 2020 bubble) are marked N on
    # both rows; the first team listed is treated as "away", the second as "home".
    neutral = (away["VH"] == "N") & (home["VH"] == "N")
    normal = (away["VH"] == "V") & (home["VH"] == "H")
    if len(away) != len(home) or not (neutral | normal).all():
        raise ValueError("Rows are not in visitor/home pairs")

    open_away, open_home, open_total = split_line(away["Open"], home["Open"])
    close_away, close_home, close_total = split_line(away["Close"], home["Close"])
    half_away, half_home, half_total = split_line(away["2H"], home["2H"])

    games = pd.DataFrame({
        "date": away["Date"],
        "away_team": away["Team"],
        "home_team": home["Team"],
        "neutral_site": neutral,
        "away_q1": away["1st"], "away_q2": away["2nd"],
        "away_q3": away["3rd"], "away_q4": away["4th"],
        "away_final": away["Final"],
        "home_q1": home["1st"], "home_q2": home["2nd"],
        "home_q3": home["3rd"], "home_q4": home["4th"],
        "home_final": home["Final"],
        "open_home_spread": open_home,
        "close_home_spread": close_home,
        "open_total": open_total,
        "close_total": close_total,
        "away_ml": away["ML"],
        "home_ml": home["ML"],
        "second_half_home_spread": half_home,
        "second_half_total": half_total,
    })
    return games


def get_season(season):
    """Download and process one season, returning a DataFrame of games."""
    html = get_html(make_url(season))
    df = make_frame(get_rows(html))
    df = clean_numbers(df)
    df = add_dates(df, season)
    games = make_games(df)
    games.insert(0, "season", f"{season}-{str(season + 1)[-2:]}")
    return games


def get_all():
    """Scrape every season from FIRST_SEASON to LAST_SEASON."""
    frames = []
    for season in range(FIRST_SEASON, LAST_SEASON + 1):
        print(f"Scraping {make_url(season)}")
        frames.append(get_season(season))
        time.sleep(PAUSE_SECONDS)
    return pd.concat(frames, ignore_index=True)


def save_csv(df, filename):
    """Write the DataFrame to a CSV file."""
    df.to_csv(filename, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Saved {len(df)} games to {filename}")


def main():
    games = get_all()
    save_csv(games, OUTPUT_FILE)


if __name__ == "__main__":
    main()
