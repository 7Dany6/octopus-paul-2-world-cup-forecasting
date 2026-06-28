# 19 Methodology: post-group-stage Poisson recalibration

The group stage is complete, so the bracket is fixed. The modelling problem is now to estimate knockout-stage match probabilities.

Version 19 differs from version 18 because it restores a scoreline-based Poisson model.

## Team recalibration

Each team receives post-group attack and defense ratings.

The model starts with pre-group Poisson lambdas from the existing match-prediction pipeline. It then updates those priors with observed group-stage goals for and goals against.

The update is deliberately shrunk toward the prior, because three group matches are informative but noisy.

## Knockout match model

For each knockout match:

1. Estimate team A and team B lambdas from post-group attack and defense ratings.
2. Apply a moderate Elo multiplier using post-group Elo.
3. Simulate 90-minute scorelines with independent Poisson distributions.
4. If the match is tied after 90 minutes, simulate lower-scoring extra time.
5. If still tied, resolve penalties with a probability shrunk toward 50/50 from Elo.

## Bracket model

The Round of 32 is fixed from exact group-stage results and FIFA Annex C. The model then runs 100,000 knockout simulations over the fixed bracket.

## Caveats

- Group-stage form is based on only three matches, so it must be shrunk toward priors.
- The model does not include injuries, suspensions, tactical changes, rest days, or live market updates.
- The single projected bracket is one coherent path, not a guaranteed exact forecast.
