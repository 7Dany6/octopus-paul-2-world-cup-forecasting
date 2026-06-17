# 17e Methodology: Exact Annex C Modal-Order Projection

## What changed

Earlier versions produced a single projected bracket from expected group tables.
That can create unintuitive results when two teams are separated by a very small
expected-points difference.

Version 17e-fixed instead builds the public single bracket from the most frequent
complete group order in each group across the Monte Carlo simulation.

## Pipeline

1. Load group-stage match predictions.
2. Fix completed matches using actual results.
3. Simulate the remaining group-stage matches.
4. Rank every group from 1st to 4th.
5. Count the full group order for each group.
6. Select the most frequent full group order per group.
7. Take the top two teams from each group.
8. Rank all third-placed teams and take the best eight.
9. Use exact FIFA Annex C lookup for third-place placement.
10. Build the official Round of 32 bracket.
11. Simulate knockout winners through the final.

## Validation

- Annex C rows loaded: 495
- Annex C validation: passed
- Single bracket validation: passed
- Third-place combination: `BCDEFIJL`
- Annex C row exists: True
- Unique Round-of-32 teams: 32

## Group C sanity check

The most frequent full Group C order is now:

|   group_rank | team     |   points |   goals_for |   goals_against |   goal_difference |
|-------------:|:---------|---------:|------------:|----------------:|------------------:|
|            1 | Brazil   | 6.73246  |     6.69177 |         2.18301 |           4.50876 |
|            2 | Morocco  | 5.40204  |     4.9553  |         2.50386 |           2.45144 |
|            3 | Scotland | 3.61627  |     2.47561 |         4.29052 |          -1.81491 |
|            4 | Haiti    | 0.397636 |     1.21125 |         6.35654 |          -5.14529 |

This fixes the earlier expected-points issue where Scotland could be placed
above Morocco because of a tiny expected-points margin. In the modal-order
projection, Morocco is second and Scotland is third.

## Projected bracket

| match_id   | stage        | team_a        | team_b               | projected_winner   |
|:-----------|:-------------|:--------------|:---------------------|:-------------------|
| M73        | round_of_32  | South Korea   | Canada               | South Korea        |
| M74        | round_of_32  | Germany       | Turkey               | Germany            |
| M75        | round_of_32  | Netherlands   | Morocco              | Morocco            |
| M76        | round_of_32  | Brazil        | Japan                | Brazil             |
| M77        | round_of_32  | France        | Sweden               | France             |
| M78        | round_of_32  | Ecuador       | Norway               | Ecuador            |
| M79        | round_of_32  | Mexico        | Scotland             | Mexico             |
| M80        | round_of_32  | England       | Senegal              | England            |
| M81        | round_of_32  | United States | Bosnia & Herzegovina | United States      |
| M82        | round_of_32  | Belgium       | Côte d'Ivoire        | Belgium            |
| M83        | round_of_32  | Colombia      | Croatia              | Colombia           |
| M84        | round_of_32  | Spain         | Austria              | Spain              |
| M85        | round_of_32  | Switzerland   | Algeria              | Switzerland        |
| M86        | round_of_32  | Argentina     | Uruguay              | Argentina          |
| M87        | round_of_32  | Portugal      | Ghana                | Portugal           |
| M88        | round_of_32  | Australia     | Egypt                | Australia          |
| M89        | round_of_16  | Germany       | France               | France             |
| M90        | round_of_16  | South Korea   | Morocco              | Morocco            |
| M91        | round_of_16  | Brazil        | Ecuador              | Brazil             |
| M92        | round_of_16  | Mexico        | England              | England            |
| M93        | round_of_16  | Colombia      | Spain                | Spain              |
| M94        | round_of_16  | United States | Belgium              | Belgium            |
| M95        | round_of_16  | Argentina     | Australia            | Argentina          |
| M96        | round_of_16  | Switzerland   | Portugal             | Portugal           |
| M97        | quarterfinal | France        | Morocco              | France             |
| M98        | quarterfinal | Spain         | Belgium              | Spain              |
| M99        | quarterfinal | Brazil        | England              | Brazil             |
| M100       | quarterfinal | Argentina     | Portugal             | Argentina          |
| M101       | semifinal    | France        | Spain                | Spain              |
| M102       | semifinal    | Brazil        | Argentina            | Argentina          |
| M104       | final        | Spain         | Argentina            | Argentina          |

## Caveats

This is a probabilistic simulation, not a deterministic forecast. The single
bracket is one coherent projected path built from modal group orders and model
knockout probabilities. Tournament-stage probabilities remain the more robust
summary of model uncertainty.
