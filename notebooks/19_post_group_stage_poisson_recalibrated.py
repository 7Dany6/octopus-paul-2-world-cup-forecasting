# 19 post-group-stage Poisson-recalibrated forecast
# This script is generated from the verified notebook run.
# It expects to be run from anywhere inside the repository.

from pathlib import Path
import json
import math
import zipfile
from collections import defaultdict, Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def find_repo_root(start=None):
    start = Path.cwd() if start is None else Path(start)
    start = start.resolve()
    required = Path("data/examples/19_post_group_stage_poisson_recalibrated/group_stage_results_full.csv")
    for candidate in [start] + list(start.parents):
        if (candidate / required).exists():
            return candidate
    checked = "\n".join(str(candidate / required) for candidate in [start] + list(start.parents))
    raise FileNotFoundError("Could not find repository root. Checked:\n" + checked)


REPO_ROOT = find_repo_root()
INPUT_DIR = REPO_ROOT / "data/examples/19_post_group_stage_poisson_recalibrated"
OUTPUT_DIR = REPO_ROOT / "data/processed/19_post_group_stage_poisson_recalibrated"
FIGURE_DIR = REPO_ROOT / "assets/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

results_df = pd.read_csv(INPUT_DIR / "group_stage_results_full.csv")
annex = pd.read_csv(INPUT_DIR / "official_annex_c_2026.csv")
pre_group_priors = pd.read_csv(INPUT_DIR / "pre_group_match_priors_minimal.csv")

GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Switzerland", "Canada", "Bosnia & Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Australia", "Paraguay", "Turkey"],
    "E": ["Germany", "Côte d'Ivoire", "Ecuador", "Curaçao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Uruguay", "Saudi Arabia"],
    "I": ["France", "Norway", "Senegal", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Colombia", "Portugal", "DR Congo", "Uzbekistan"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

TEAM_TO_GROUP = {team: group for group, group_teams in GROUPS.items() for team in group_teams}
teams = sorted(TEAM_TO_GROUP)

# Official order after the group stage. This is treated as an official input.
OFFICIAL_GROUP_ORDER = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Switzerland", "Canada", "Bosnia & Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Australia", "Paraguay", "Turkey"],
    "E": ["Germany", "Côte d'Ivoire", "Ecuador", "Curaçao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Uruguay", "Saudi Arabia"],
    "I": ["France", "Norway", "Senegal", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Colombia", "Portugal", "DR Congo", "Uzbekistan"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

OFFICIAL_RANK = {
    team: i + 1
    for group, order in OFFICIAL_GROUP_ORDER.items()
    for i, team in enumerate(order)
}

R32_FIXED = {
    "M73": ("2A", "2B"), "M74": ("1E", "3ABCDF"),
    "M75": ("1F", "2C"), "M76": ("1C", "2F"),
    "M77": ("1I", "3CDFGH"), "M78": ("2E", "2I"),
    "M79": ("1A", "3CEFHI"), "M80": ("1L", "3EHIJK"),
    "M81": ("1D", "3BEFIJ"), "M82": ("1G", "3AEHIJ"),
    "M83": ("2K", "2L"), "M84": ("1H", "2J"),
    "M85": ("1B", "3EFGIJ"), "M86": ("1J", "2H"),
    "M87": ("1K", "3DEIJL"), "M88": ("2D", "2G"),
}
R16_PAIRS = [("M89", "M74", "M77"), ("M90", "M73", "M75"), ("M91", "M76", "M78"), ("M92", "M79", "M80"), ("M93", "M83", "M84"), ("M94", "M81", "M82"), ("M95", "M86", "M88"), ("M96", "M85", "M87")]
QF_PAIRS = [("M97", "M89", "M90"), ("M98", "M93", "M94"), ("M99", "M91", "M92"), ("M100", "M95", "M96")]
SF_PAIRS = [("M101", "M97", "M98"), ("M102", "M99", "M100")]
FINAL_PAIR = ("M104", "M101", "M102")


def expected_score(ra, rb):
    return 1.0 / (1.0 + 10 ** (-(ra - rb) / 400.0))


def margin_multiplier(goal_diff, elo_diff):
    margin = max(abs(goal_diff), 1)
    return np.log(margin + 1.0) * (2.2 / (0.001 * abs(elo_diff) + 2.2))


def build_team_priors(priors):
    rows = []
    for _, row in priors.iterrows():
        rows.append({"team": row["home_team"], "for_lambda": row["lambda_home"], "against_lambda": row["lambda_away"], "elo": row["elo_home_pre"]})
        rows.append({"team": row["away_team"], "for_lambda": row["lambda_away"], "against_lambda": row["lambda_home"], "elo": row["elo_away_pre"]})
    long = pd.DataFrame(rows)
    return long.groupby("team").agg(
        prior_lambda_for=("for_lambda", "mean"),
        prior_lambda_against=("against_lambda", "mean"),
        prior_elo=("elo", "mean"),
        prior_matches=("for_lambda", "size"),
    ).reset_index()


def compute_standings(results):
    stats = {team: {"team": team, "group": TEAM_TO_GROUP[team], "played": 0, "goals_for": 0, "goals_against": 0, "goal_difference": 0, "points": 0} for team in teams}
    for _, row in results.iterrows():
        home, away = row["home_team"], row["away_team"]
        hg, ag = int(row["home_goals"]), int(row["away_goals"])
        for team, gf, ga in [(home, hg, ag), (away, ag, hg)]:
            stats[team]["played"] += 1
            stats[team]["goals_for"] += gf
            stats[team]["goals_against"] += ga
            stats[team]["goal_difference"] += gf - ga
            if gf > ga:
                stats[team]["points"] += 3
            elif gf == ga:
                stats[team]["points"] += 1
    df = pd.DataFrame(stats.values())
    df["official_group_rank"] = df["team"].map(OFFICIAL_RANK).astype(int)
    return df.sort_values(["group", "official_group_rank"]).reset_index(drop=True)


team_priors = build_team_priors(pre_group_priors)
standings = compute_standings(results_df)
thirds = standings[standings["official_group_rank"] == 3].copy()
thirds_ranked = thirds.sort_values(["points", "goal_difference", "goals_for"], ascending=[False, False, False]).reset_index(drop=True)
thirds_ranked["third_place_rank"] = np.arange(1, len(thirds_ranked) + 1)
best_thirds = thirds_ranked.head(8).copy()
third_combo_key = "".join(sorted(best_thirds["group"]))
annex_row = annex[annex["combo_key"] == third_combo_key].iloc[0]

lookup = {f"{int(row['official_group_rank'])}{row['group']}": row["team"] for _, row in standings.iterrows()}


def team_for_slot(slot, match_id):
    if not slot.startswith("3"):
        return lookup[slot]
    return lookup[annex_row[R32_FIXED[match_id][0]]]


r32 = pd.DataFrame([
    {"match_id": match_id, "stage": "round_of_32", "slot_a": left_slot, "slot_b": right_slot, "team_a": team_for_slot(left_slot, match_id), "team_b": team_for_slot(right_slot, match_id)}
    for match_id, (left_slot, right_slot) in R32_FIXED.items()
])

GLOBAL_AVG_LAMBDA = float(pd.concat([pre_group_priors["lambda_home"], pre_group_priors["lambda_away"]]).mean())

elo = dict(zip(team_priors["team"], team_priors["prior_elo"]))
for team in teams:
    elo.setdefault(team, 1500.0)

starting_elo = elo.copy()
for _, row in results_df.sort_values("date").iterrows():
    home, away = row["home_team"], row["away_team"]
    hg, ag = int(row["home_goals"]), int(row["away_goals"])
    actual_home = 1.0 if hg > ag else 0.5 if hg == ag else 0.0
    expected_home = expected_score(elo[home], elo[away])
    delta = 32.0 * margin_multiplier(hg - ag, elo[home] - elo[away]) * (actual_home - expected_home)
    elo[home] += delta
    elo[away] -= delta

PRIOR_MATCH_WEIGHT = 6.0

recal = (
    pd.DataFrame({"team": teams})
    .merge(team_priors, on="team", how="left")
    .merge(standings[["team", "group", "played", "goals_for", "goals_against", "goal_difference", "points", "official_group_rank"]], on="team", how="left")
)
recal["group"] = recal["group"].fillna(recal["team"].map(TEAM_TO_GROUP))
recal["prior_lambda_for"] = recal["prior_lambda_for"].fillna(GLOBAL_AVG_LAMBDA)
recal["prior_lambda_against"] = recal["prior_lambda_against"].fillna(GLOBAL_AVG_LAMBDA)
recal["prior_elo"] = recal["prior_elo"].fillna(1500.0)
recal["played"] = recal["played"].fillna(0)
recal["goals_for"] = recal["goals_for"].fillna(0)
recal["goals_against"] = recal["goals_against"].fillna(0)
recal["actual_goals_for_per_match"] = recal["goals_for"] / recal["played"].replace(0, np.nan)
recal["actual_goals_against_per_match"] = recal["goals_against"] / recal["played"].replace(0, np.nan)
recal["post_group_lambda_for"] = (PRIOR_MATCH_WEIGHT * recal["prior_lambda_for"] + recal["goals_for"]) / (PRIOR_MATCH_WEIGHT + recal["played"])
recal["post_group_lambda_against"] = (PRIOR_MATCH_WEIGHT * recal["prior_lambda_against"] + recal["goals_against"]) / (PRIOR_MATCH_WEIGHT + recal["played"])
recal["post_group_elo"] = recal["team"].map(elo)
recal["elo_change"] = recal["post_group_elo"] - recal["prior_elo"]
recal["attack_rating"] = recal["post_group_lambda_for"] / GLOBAL_AVG_LAMBDA
recal["defense_concede_rating"] = recal["post_group_lambda_against"] / GLOBAL_AVG_LAMBDA

team_row = recal.set_index("team").to_dict(orient="index")


def matchup_lambdas(team_a, team_b):
    a, b = team_row[team_a], team_row[team_b]
    elo_diff = a["post_group_elo"] - b["post_group_elo"]
    lam_a = GLOBAL_AVG_LAMBDA * a["attack_rating"] * b["defense_concede_rating"] * np.exp(elo_diff / 900.0)
    lam_b = GLOBAL_AVG_LAMBDA * b["attack_rating"] * a["defense_concede_rating"] * np.exp(-elo_diff / 900.0)
    return float(np.clip(lam_a, 0.20, 4.20)), float(np.clip(lam_b, 0.20, 4.20))


def poisson_pmf(lam, max_goals=10):
    probs = np.array([np.exp(-lam) * (lam ** k) / math.factorial(k) for k in range(max_goals + 1)])
    probs[-1] += max(0.0, 1.0 - probs.sum())
    return probs


_match_cache = {}


def match_win_probability(team_a, team_b, max_goals=10):
    key = (team_a, team_b)
    if key in _match_cache:
        return _match_cache[key]
    lam_a, lam_b = matchup_lambdas(team_a, team_b)
    pa, pb = poisson_pmf(lam_a, max_goals), poisson_pmf(lam_b, max_goals)
    p_a_90 = p_b_90 = p_draw_90 = 0.0
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            p = pa[ga] * pb[gb]
            if ga > gb:
                p_a_90 += p
            elif gb > ga:
                p_b_90 += p
            else:
                p_draw_90 += p
    et_factor = (30.0 / 90.0) * 0.70
    ea, eb = poisson_pmf(lam_a * et_factor, 5), poisson_pmf(lam_b * et_factor, 5)
    p_a_et = p_b_et = p_draw_et = 0.0
    for ga in range(6):
        for gb in range(6):
            p = ea[ga] * eb[gb]
            if ga > gb:
                p_a_et += p
            elif gb > ga:
                p_b_et += p
            else:
                p_draw_et += p
    penalty_p_a = expected_score(team_row[team_a]["post_group_elo"], team_row[team_b]["post_group_elo"])
    penalty_p_a = 0.5 + 0.35 * (penalty_p_a - 0.5)
    p_a_total = float(np.clip(p_a_90 + p_draw_90 * (p_a_et + p_draw_et * penalty_p_a), 0.0, 1.0))
    out = {"lambda_team_a": lam_a, "lambda_team_b": lam_b, "p_team_a_90": p_a_90, "p_draw_90": p_draw_90, "p_team_b_90": p_b_90, "p_team_a_advance": p_a_total, "p_team_b_advance": 1.0 - p_a_total}
    _match_cache[key] = out
    return out


def play_bracket(rng=None, deterministic=False):
    winners, participants = {}, {}
    for _, row in r32.iterrows():
        match_id, a, b = row["match_id"], row["team_a"], row["team_b"]
        participants[match_id] = (a, b)
        p = match_win_probability(a, b)["p_team_a_advance"]
        winners[match_id] = a if (p >= 0.5 if deterministic else rng.random() < p) else b
    for pairs in [R16_PAIRS, QF_PAIRS, SF_PAIRS, [FINAL_PAIR]]:
        for match_id, prev_a, prev_b in pairs:
            a, b = winners[prev_a], winners[prev_b]
            participants[match_id] = (a, b)
            p = match_win_probability(a, b)["p_team_a_advance"]
            winners[match_id] = a if (p >= 0.5 if deterministic else rng.random() < p) else b
    return participants, winners, winners["M104"]


N_SIM = 100_000
rng = np.random.default_rng(42)
stage_counts = {team: defaultdict(int) for team in teams}
qualified_teams = set(r32[["team_a", "team_b"]].values.ravel())

for _ in range(N_SIM):
    participants, winners, champion = play_bracket(rng=rng, deterministic=False)
    for team in qualified_teams:
        stage_counts[team]["round_of_32"] += 1
    for mid in r32["match_id"]:
        stage_counts[winners[mid]]["round_of_16"] += 1
    for mid, _, _ in R16_PAIRS:
        stage_counts[winners[mid]]["quarterfinal"] += 1
    for mid, _, _ in QF_PAIRS:
        stage_counts[winners[mid]]["semifinal"] += 1
    for mid, _, _ in SF_PAIRS:
        stage_counts[winners[mid]]["final"] += 1
    stage_counts[champion]["champion"] += 1

knockout_probs = pd.DataFrame([
    {"team": team, "group": TEAM_TO_GROUP[team], "post_group_elo": team_row[team]["post_group_elo"], "post_group_lambda_for": team_row[team]["post_group_lambda_for"], "post_group_lambda_against": team_row[team]["post_group_lambda_against"], "round_of_32_probability": stage_counts[team]["round_of_32"] / N_SIM, "round_of_16_probability": stage_counts[team]["round_of_16"] / N_SIM, "quarterfinal_probability": stage_counts[team]["quarterfinal"] / N_SIM, "semifinal_probability": stage_counts[team]["semifinal"] / N_SIM, "final_probability": stage_counts[team]["final"] / N_SIM, "champion_probability": stage_counts[team]["champion"] / N_SIM}
    for team in sorted(qualified_teams)
]).sort_values("champion_probability", ascending=False).reset_index(drop=True)

det_participants, det_winners, det_champion = play_bracket(deterministic=True)


def stage_for_match(mid):
    if mid in set(r32["match_id"]):
        return "round_of_32"
    if any(mid == x[0] for x in R16_PAIRS):
        return "round_of_16"
    if any(mid == x[0] for x in QF_PAIRS):
        return "quarterfinal"
    if any(mid == x[0] for x in SF_PAIRS):
        return "semifinal"
    return "final"


single_bracket = pd.DataFrame([
    {"match_id": mid, "stage": stage_for_match(mid), "team_a": a, "team_b": b, **match_win_probability(a, b), "projected_winner": det_winners[mid]}
    for mid, (a, b) in sorted(det_participants.items(), key=lambda item: int(item[0].replace("M", "")))
])

r32_match_model = pd.DataFrame([
    {"match_id": row["match_id"], "stage": "round_of_32", "team_a": row["team_a"], "team_b": row["team_b"], **match_win_probability(row["team_a"], row["team_b"])}
    for _, row in r32.iterrows()
])

summary = {
    "stage": "post_group_stage_poisson_recalibrated",
    "group_stage_complete": True,
    "group_stage_results_loaded": int(len(results_df)),
    "qualified_teams": int(len(qualified_teams)),
    "annex_c_rows": int(len(annex)),
    "third_combo_key": third_combo_key,
    "annex_c_option": int(annex_row["option"]),
    "round_of_32_unique_teams": int(len(qualified_teams)),
    "n_simulations": N_SIM,
    "model": "post_group_attack_defense_poisson_plus_extra_time_penalties",
    "top_champion_by_probability": knockout_probs.iloc[0]["team"],
    "top_champion_probability": float(knockout_probs.iloc[0]["champion_probability"]),
    "projected_champion_single_bracket": det_champion,
    "global_average_lambda": GLOBAL_AVG_LAMBDA,
    "prior_match_weight": PRIOR_MATCH_WEIGHT,
}

results_df.to_csv(OUTPUT_DIR / "group_stage_results_full.csv", index=False)
standings.to_csv(OUTPUT_DIR / "final_group_standings.csv", index=False)
thirds_ranked.to_csv(OUTPUT_DIR / "third_place_ranking.csv", index=False)
r32.to_csv(OUTPUT_DIR / "official_round_of_32_bracket.csv", index=False)
annex.to_csv(OUTPUT_DIR / "official_annex_c_2026.csv", index=False)
pd.DataFrame([annex_row]).to_csv(OUTPUT_DIR / "actual_annex_c_row.csv", index=False)
pre_group_priors.to_csv(OUTPUT_DIR / "pre_group_match_priors_minimal.csv", index=False)
recal.to_csv(OUTPUT_DIR / "post_group_poisson_team_ratings.csv", index=False)
r32_match_model.to_csv(OUTPUT_DIR / "round_of_32_poisson_match_model.csv", index=False)
knockout_probs.to_csv(OUTPUT_DIR / "knockout_stage_probabilities_poisson.csv", index=False)
single_bracket.to_csv(OUTPUT_DIR / "single_projected_knockout_bracket_poisson.csv", index=False)
(OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

top = knockout_probs.head(12)
plt.figure(figsize=(10, 7))
plt.barh(top["team"][::-1], top["champion_probability"][::-1])
plt.xlabel("Champion probability")
plt.title("Post-group-stage champion probabilities - Poisson recalibrated")
plt.tight_layout()
plt.savefig(FIGURE_DIR / "19_poisson_champion_probabilities.png", dpi=180)
plt.close()

report_zip = OUTPUT_DIR.parent / "19_post_group_stage_poisson_recalibrated_report_bundle.zip"
with zipfile.ZipFile(report_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in OUTPUT_DIR.rglob("*"):
        if path.is_file():
            zf.write(path, arcname=path.relative_to(OUTPUT_DIR))

print(json.dumps(summary, indent=2))
print("Created:", report_zip)
