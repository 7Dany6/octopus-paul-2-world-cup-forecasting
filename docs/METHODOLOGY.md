# Methodology

This project uses a layered forecasting approach.

## 1. Football features

The base model uses historical international results to derive features such as:

- team strength;
- Elo-style ratings;
- recent form;
- goals for and against;
- rest days;
- neutral venue flags.

## 2. Scoreline model

A scoreline layer estimates expected home and away goals and converts them into
a score distribution.

This gives:

- most likely scoreline;
- home/draw/away probabilities implied by score probabilities.

## 3. Market-implied probabilities

Pre-match odds are converted into market-implied probabilities and normalized to
remove bookmaker margin.

These probabilities are used as a strong baseline.

## 4. Market-anchored correction

Instead of trying to replace the market, the system applies a small correction
around market probabilities using football features and scoreline signals.

## 5. Live adjustment

Before kickoff, fresh odds snapshots update the model's view.

If the market moves toward the model, the signal is treated as stronger.
If the market moves against the model, the signal is downgraded or marked for
manual review.

Close to kickoff, the model is shrunk partly toward the latest market to account
for late information such as lineups, injuries, weather, and other pre-match
context.
