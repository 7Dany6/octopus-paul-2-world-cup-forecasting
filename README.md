# Octopus Paul 2.0 — World Cup Forecasting System

A personal side project for forecasting World Cup matches with public football data,
external APIs, market-implied probabilities, scoreline modelling, and live
pre-match adjustment.

The project was built as an engineering and modelling experiment, not as betting
advice.

## Highlights

- Built an end-to-end football forecasting workflow.
- Combined historical international results, team strength, recent form, rest days,
  expected goals, scoreline probabilities, and market-implied probabilities.
- Added a market-anchored correction layer.
- Added a live adjustment layer for late pre-match context such as odds movement,
  lineups, injuries, weather, and rest days.
- Kept predictions timestamped before kickoff.
- Opening-match example: Mexico vs South Africa, predicted score 2:0.

## Important disclaimer

This repository is for forecasting research and portfolio demonstration only.

It is not forecasting or betting advice, financial advice, or a claim of predictive superiority.
Football is noisy, exact-score forecasting is especially noisy, and one correct
scoreline is not statistical proof.

This is a personal side project built with public football data and external APIs.
It is not affiliated with any employer.

## Repository structure

```text
.
├── notebooks/
│   ├── 00_README_run_order.ipynb
│   ├── 01_build_training_features_from_public_results.ipynb
│   ├── 02_the_odds_api_historical_odds_fetch.ipynb
│   ├── 03_join_market_train_and_backtest.ipynb
│   ├── 04_current_wc2026_odds_ledger.ipynb
│   ├── 07_walkforward_model_vs_market_backtest.ipynb
│   ├── 08_edge_selector_grid_search.ipynb
│   ├── 09_robust_edge_validation.ipynb
│   ├── 10_outcome_score_model_with_market_features.ipynb
│   ├── 11_market_anchored_correction_and_edge_selector.ipynb
│   ├── 12_current_wc2026_paper_picks.ipynb
│   ├── 13_data_source_audit_and_api_probe.ipynb
│   ├── 14_budgeted_historical_odds_expansion_v2.ipynb
│   └── 15_live_adjustment_engine.ipynb
├── data/examples/
├── assets/
├── docs/
├── requirements.txt
├── .env.example
└── .gitignore
```

## High-level pipeline

1. Build historical training features from public international results.
2. Fetch or load historical odds snapshots from an external odds API.
3. Join football features with market-implied probabilities.
4. Run walk-forward validation.
5. Train outcome and scoreline models.
6. Add market-anchored correction.
7. Generate current-match predictions.
8. Update live probabilities as pre-match information changes.

## Data sources

The project is designed around:

- Public international football results.
- Public or external API fixtures.
- External odds APIs for market-implied probabilities.
- Optional enrichment sources for lineups, injuries, weather, and other context.

Raw paid API data is intentionally not redistributed in this repository.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then add your own API keys to `.env` if you want to run the odds/API notebooks.

## Environment variables

```text
ODDS_API_KEY=
API_FOOTBALL_KEY=
FOOTBALL_DATA_ORG_TOKEN=
SPORTMONKS_TOKEN=
```

## Suggested run order

For a minimal public-data run:

```text
01 -> 03 -> 07 -> 10 -> 11 -> 12
```

For odds-backed validation:

```text
01 -> 02 -> 03 -> 07 -> 08 -> 09 -> 10 -> 11 -> 12
```

For live tournament monitoring:

```text
04 -> 15
```

Re-run `12` only when the base model or strategy parameters change.

## Example outputs

Example outputs are stored in `data/examples/`:

- `opening_match_prediction.csv`
- `world_cup_predictions_sample.csv`
- `friendly_model_evaluation_sample.csv`
- `friendly_model_evaluation_summary.csv`

These are small example files for demonstration. They are not a replacement for
a full, timestamped evaluation ledger.

## Portfolio framing

This project is mainly about:

- data collection and cleaning;
- feature engineering;
- scoreline modelling;
- probability calibration;
- walk-forward validation;
- live monitoring;
- auditability.

The interesting question is not whether the model can guess one score.

The interesting question is whether a forecasting system can remain calibrated
over a full tournament.
