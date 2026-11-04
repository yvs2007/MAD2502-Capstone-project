# MAD2502-Capstone-project
This is a collaborative project that is done for the MAD2502 class @ UF

## Update 2 analysis

Install dependencies and run the saved dataset analysis:

```bash
python -m pip install -r requirements.txt
python nba_analysis.py
```

The script works from any directory and writes CSV checkpoints and actual
console output to `results/`. It leaves the source CSV unchanged.

Spread error is home points minus away points plus the closing home spread.
Total error is combined points minus the closing total. Mean error measures
direction; mean absolute error measures average distance from the prediction.
Both summaries use games with complete scores and both closing lines.
Missing lines are excluded, not replaced with zero. Pushes remain zero errors.

The saved dataset has 5,613 games and 23 columns, spanning October 16, 2018
through January 16, 2023. It excludes 2017-18 and has only part of 2022-23.
Five games lack closing lines, leaving 5,608 for this checkpoint.
Neutral-site games remain included; this is not a home-court bias test.
Scores have not yet been independently checked against nba_api.

## Data collection

```bash
python nba_scraper.py
```

This command downloads the configured seasons and overwrites the source CSV.
The scraper uses SportsbookReviewsOnline season pages, for example:
https://www.sportsbookreviewsonline.com/scoresoddsarchives/nba-odds-2018-19

Source tables have two team rows per game. The scraper pairs visitor/home
rows; neutral-site pairs keep source ordering. Numeric text is converted to
numbers, pick'em becomes zero, and unparseable values become missing.
Dates advance a year when the chronological month decreases.
The larger line value is treated as the total and the smaller as the
favorite's spread. Totals outside 80–300 or spreads above 40 become missing.
These are screening rules, not proof of a source typo.

## Style checks

```bash
python -m pip install pycodestyle
python -m pycodestyle nba_analysis.py nba_scraper.py
```

Python follows PEP 8 with lines of at most 79 characters. Comments and
docstrings contain at most four words. Detailed methodology stays here.
