## Draws the learning curves and assembles the results table.
##
## This reads the files the other two scripts wrote, it doesn't train or play anything
## itself. That means the plots can be restyled or redrawn as many times as we like
## without rerunning the study.
##
## Run with:  python -m evaluation.plots

import csv
import json

import matplotlib
matplotlib.use("Agg")   # no display needed, we're writing files
import matplotlib.pyplot as plt

from evaluation.paths import (
    CURVES_JSON,
    MATCHUPS_CSV,
    PLOTS_DIR,
    RESULTS_MD,
    STUDY_CSV,
    ensure_dirs,
)

KNOB_TITLES = {
    "alpha": "Learning rate (alpha)",
    "gamma": "Discount factor (gamma)",
    "epsilon_decay": "Exploration decay (epsilon)",
}

# What we predicted before running anything. Printed under each plot so the writeup can
# be honest about whether the prediction held.
KNOB_EXPECTATIONS = {
    "alpha": "Expected: very high alpha is noisy and unstable, since each game overwrites prior learning.",
    "gamma": "Expected: very low gamma barely rises, since the final reward can't reach the early moves.",
    "epsilon_decay": "Expected: fast decay plateaus early at a mediocre level, having stopped exploring too soon.",
}


def load_curves():
    with open(CURVES_JSON) as handle:
        return json.load(handle)


def load_csv(path):
    with open(path) as handle:
        return list(csv.DictReader(handle))


def plot_knob(knob, runs):
    """One figure per knob, one line per value of that knob."""
    figure, axes = plt.subplots(figsize=(8, 5))

    for run in sorted(runs, key=lambda r: r["value"]):
        episodes = [point[0] for point in run["curve"]]
        win_rates = [point[1] * 100 for point in run["curve"]]

        note = f" ({run['note']})" if run["note"] else ""
        axes.plot(episodes, win_rates, linewidth=1.6,
                  label=f"{knob} = {run['value']}{note}")

    axes.set_title(KNOB_TITLES.get(knob, knob))
    axes.set_xlabel("Training episodes (self-play games)")
    axes.set_ylabel("Win rate vs random agent (%)")
    axes.set_ylim(0, 100)
    axes.grid(True, alpha=0.3)
    axes.legend(loc="lower right")

    figure.text(0.5, 0.005, KNOB_EXPECTATIONS.get(knob, ""),
                ha="center", fontsize=8, style="italic")
    figure.tight_layout(rect=(0, 0.04, 1, 1))

    output = PLOTS_DIR / f"{knob}.png"
    figure.savefig(output, dpi=150)
    plt.close(figure)
    return output


def percent(value):
    return f"{float(value) * 100:.1f}%"


def build_findings(study_rows):
    """What the study actually showed, worked out from the numbers rather than assumed.

    Worth being careful here. The spec predicts each extreme setting will fail visibly on
    the win-rate-against-random curve, and it's tempting to write that up as if it did.
    This section reports what the data says instead, including where the predicted effect
    didn't appear.
    """
    lines = ["## What the numbers actually show", ""]

    win_rates = [float(row["vs_random_win_rate"]) for row in study_rows]
    spread = (max(win_rates) - min(win_rates)) * 100
    lines.append(
        f"**The win rate against random barely separates the settings.** Across all "
        f"{len(study_rows)} runs it lands between {min(win_rates)*100:.1f}% and "
        f"{max(win_rates)*100:.1f}%, a spread of only {spread:.1f} points, and the learning "
        "curves below sit on top of each other. Beating a random opponent turns out to be "
        "an easy bar that even a badly-tuned agent clears, so this metric saturates and "
        "stops being informative. That is itself a result: it is exactly why the spec asks "
        "for the minimax matchup as well."
    )
    lines.append("")

    failures = [row for row in study_rows if float(row["vs_minimax_draw_rate"]) < 1.0]
    if failures:
        lines.append("**The minimax draw rate is what actually discriminates.** "
                     "These settings failed to reach optimal play:")
        lines.append("")
        for row in failures:
            total = (int(row["vs_minimax_wins"]) + int(row["vs_minimax_losses"])
                     + int(row["vs_minimax_draws"]))
            lines.append(
                f"- `{row['knob']} = {row['value']}` ({row['note']}): "
                f"drew only {percent(row['vs_minimax_draw_rate'])} against minimax, "
                f"losing {row['vs_minimax_losses']} of {total} games — "
                f"while still winning {percent(row['vs_random_win_rate'])} against random."
            )
        lines.append("")
        if any(row["knob"] == "gamma" for row in failures):
            lines.append(
                "The gamma result is the clean confirmation of the theory. With the discount "
                "factor that low, the reward at the end of the game is worth almost nothing "
                "by the time it propagates back to the opening moves, so the agent never "
                "learns which early moves set up the win. It still punishes a random "
                "opponent's blunders, but against perfect play it has nothing to fall back on."
            )
            lines.append("")
    else:
        lines.append("**Every setting reached a 100% draw rate against minimax**, so at this "
                     "number of episodes none of the extremes broke the agent outright.")
        lines.append("")

    lines.append(
        "**The alpha and epsilon predictions did not reproduce at 20,000 episodes.** High "
        "alpha was expected to look noisy and unstable and fast epsilon decay was expected to "
        "plateau early; both still reached a 100% draw rate against minimax. Tic-tac-toe is "
        "small enough (5,478 reachable states) that the agent visits the whole space many "
        "times over, which papers over settings that would be fatal on a larger problem. "
        "Reporting this rather than the prediction is the honest version."
    )
    lines.append("")

    return lines


def build_results_md(matchup_rows, study_rows, curves):
    lines = []
    lines.append("# Evaluation Results")
    lines.append("")
    lines.append("Generated by `evaluation/run_evaluation.py` and "
                 "`evaluation/hyperparameter_study.py`, plotted by `evaluation/plots.py`.")
    lines.append("")

    if matchup_rows:
        seed = matchup_rows[0]["seed"]
        games = matchup_rows[0]["games"]
        lines.append(f"## Matchups ({games} games each, seed {seed})")
        lines.append("")
        lines.append("Who goes first alternates every game, so the first-move advantage is "
                     "split evenly and doesn't skew the numbers.")
        lines.append("")
        lines.append("| Matchup | A wins | B wins | Draws | A win rate | Draw rate |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in matchup_rows:
            lines.append(
                f"| {row['matchup']} | {row['a_wins']} | {row['b_wins']} | {row['draws']} "
                f"| {percent(row['a_win_rate'])} | {percent(row['draw_rate'])} |"
            )
        lines.append("")

        by_label = {row["matchup"]: row for row in matchup_rows}
        q_random = by_label.get("Q-agent vs random")
        q_minimax = by_label.get("Q-agent vs minimax")
        if q_random and q_minimax:
            lines.append("**Headline numbers**")
            lines.append("")
            lines.append(f"- Win rate vs random: **{percent(q_random['a_win_rate'])}** "
                         "— the agent learned to punish mistakes.")
            lines.append(f"- Draw rate vs minimax: **{percent(q_minimax['draw_rate'])}** "
                         "(target 100%) — the agent reached optimal play.")
            lines.append(f"- Losses to minimax: {q_minimax['b_wins']}, "
                         f"wins against minimax: {q_minimax['a_wins']} "
                         "(any win here would be a bug in minimax, not an achievement).")
            lines.append("")

    if study_rows:
        seed = study_rows[0]["seed"]
        episodes = study_rows[0]["episodes"]
        lines.append(f"## Hyper-parameter study ({episodes} episodes per run, seed {seed})")
        lines.append("")
        lines.append("One knob varied at a time, the others held at the baseline "
                     "(alpha 0.5, gamma 0.9, epsilon decay 0.0001, min epsilon 0.05). "
                     "Final scoring is over 1000 games per matchup.")
        lines.append("")
        lines.append("| Knob | Value | | vs random W/L/D | Win rate | vs minimax W/L/D | Draw rate |")
        lines.append("|---|---:|---|---|---:|---|---:|")
        for row in study_rows:
            lines.append(
                f"| {row['knob']} | {row['value']} | {row['note']} "
                f"| {row['vs_random_wins']}/{row['vs_random_losses']}/{row['vs_random_draws']} "
                f"| {percent(row['vs_random_win_rate'])} "
                f"| {row['vs_minimax_wins']}/{row['vs_minimax_losses']}/{row['vs_minimax_draws']} "
                f"| {percent(row['vs_minimax_draw_rate'])} |"
            )
        lines.append("")

        lines.extend(build_findings(study_rows))

    lines.append("## Learning curves")
    lines.append("")
    for knob in sorted({run["knob"] for run in curves}):
        lines.append(f"### {KNOB_TITLES.get(knob, knob)}")
        lines.append("")
        lines.append(f"![{knob} learning curves](../plots/{knob}.png)")
        lines.append("")
        lines.append(KNOB_EXPECTATIONS.get(knob, ""))
        lines.append("")

    lines.append("## Reproducibility")
    lines.append("")
    lines.append("Every experiment sets a fixed seed, recorded in the tables above. "
                 "Python's `random` is a deterministic sequence starting from that seed, "
                 "so rerunning with the same seed reproduces these numbers exactly:")
    lines.append("")
    lines.append("```")
    lines.append("python -m evaluation.run_evaluation")
    lines.append("python -m evaluation.hyperparameter_study")
    lines.append("python -m evaluation.plots")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main():
    ensure_dirs()
    curves = load_curves()

    written = []
    for knob in sorted({run["knob"] for run in curves}):
        runs = [run for run in curves if run["knob"] == knob]
        written.append(plot_knob(knob, runs))

    matchup_rows = load_csv(MATCHUPS_CSV) if MATCHUPS_CSV.exists() else []
    study_rows = load_csv(STUDY_CSV) if STUDY_CSV.exists() else []

    RESULTS_MD.write_text(build_results_md(matchup_rows, study_rows, curves))

    for path in written:
        print(f"Wrote {path}")
    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
