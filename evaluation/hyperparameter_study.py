## The hyper-parameter study.
##
## We retrain from scratch with different values of alpha, gamma and epsilon decay,
## changing ONE at a time and holding the others at the baseline. During each run we
## measure the win rate against random every N episodes, which gives us a learning curve
## per setting.
##
## What we expect to see, and what it means (this is the bit the writeup explains):
##
##   epsilon decaying too fast -> curve plateaus early at a mediocre level. The agent
##                                stopped exploring before it found the better lines.
##   alpha too high            -> curve is noisy and unstable. Every new game overwrites
##                                what the previous ones taught it.
##   gamma too low             -> curve barely rises. The reward at the end of the game
##                                can't reach back to the early moves that set it up.
##
## Same idea as underfitting and overfitting: extreme settings fail in ways we can predict
## ahead of time and then explain.
##
## Run with:  python -m evaluation.hyperparameter_study

import argparse
import csv
import json

from agents.minimax_agent import MinimaxAgent
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent

from evaluation.compat import enable_minimax_cache
from evaluation.harness import evaluate, train_with_curve
from evaluation.paths import CURVES_JSON, STUDY_CSV, ensure_dirs

DEFAULT_SEED = 20250816
DEFAULT_EPISODES = 20000
DEFAULT_EVAL_EVERY = 500
DEFAULT_EVAL_GAMES = 1000
DEFAULT_FINAL_GAMES = 1000
DEFAULT_CURVE_MINIMAX_GAMES = 500

# The settings the shipped agent was trained with (main.py:87), so the study is anchored
# to the agent we're actually reporting on rather than to an arbitrary starting point.
BASELINE = {
    "alpha": 0.5,
    "gamma": 0.9,
    "epsilon_decay": 0.0001,
    "min_epsilon": 0.05,
}

# One knob at a time, three values each. The middle value of each is the baseline.
SWEEPS = {
    "alpha": [0.05, 0.5, 0.95],
    "gamma": [0.1, 0.9, 0.99],
    "epsilon_decay": [0.001, 0.0001, 0.00002],
}

# Plain-English labels for the extremes, used in the plot legends and the results table.
VALUE_NOTES = {
    ("alpha", 0.05): "very low",
    ("alpha", 0.5): "baseline",
    ("alpha", 0.95): "very high",
    ("gamma", 0.1): "very low",
    ("gamma", 0.9): "baseline",
    ("gamma", 0.99): "very high",
    ("epsilon_decay", 0.001): "fast decay",
    ("epsilon_decay", 0.0001): "baseline",
    ("epsilon_decay", 0.00002): "slow decay",
}

CSV_COLUMNS = [
    "knob", "value", "note", "alpha", "gamma", "epsilon_decay", "min_epsilon",
    "episodes", "seed", "final_epsilon",
    "vs_random_wins", "vs_random_losses", "vs_random_draws", "vs_random_win_rate",
    "vs_minimax_wins", "vs_minimax_losses", "vs_minimax_draws", "vs_minimax_draw_rate",
]


def run_one(knob, value, episodes, eval_every, eval_games, final_games, seed,
            curve_minimax_games=DEFAULT_CURVE_MINIMAX_GAMES):
    """Train one agent from scratch with a single knob changed, and measure it."""
    params = dict(BASELINE)
    params[knob] = value

    # Fresh agent with an empty Q-table, starting fully exploratory.
    agent = QTableAgent(f"{knob}={value}", epsilon=1.0)

    curve = train_with_curve(
        agent=agent,
        episodes=episodes,
        eval_every=eval_every,
        eval_games=eval_games,
        opponent=RandomAgent("Random"),
        alpha=params["alpha"],
        gamma=params["gamma"],
        epsilon_decay=params["epsilon_decay"],
        min_epsilon=params["min_epsilon"],
        # Every run gets the same seed on purpose, so differences between the curves come
        # from the hyper-parameter and not from a different sequence of games.
        seed=seed,
        # The measurement that actually separates the settings. Win rate against random
        # saturates; drawing against perfect play does not.
        optimal_opponent=MinimaxAgent("Minimax"),
        optimal_games=curve_minimax_games,
    )

    # Final scoring of the trained agent on both matchups, so the results table has
    # win/draw/loss for every setting and not just the curve.
    vs_random = evaluate(agent, RandomAgent("Random"), final_games, seed=seed)
    vs_minimax = evaluate(agent, MinimaxAgent("Minimax"), final_games, seed=seed)

    return {
        "knob": knob,
        "value": value,
        "note": VALUE_NOTES.get((knob, value), ""),
        "params": params,
        "episodes": episodes,
        "seed": seed,
        "final_epsilon": agent.epsilon,
        "curve": curve,
        "vs_random": vs_random,
        "vs_minimax": vs_minimax,
    }


def run_study(episodes=DEFAULT_EPISODES, eval_every=DEFAULT_EVAL_EVERY,
              eval_games=DEFAULT_EVAL_GAMES, final_games=DEFAULT_FINAL_GAMES,
              seed=DEFAULT_SEED, curve_minimax_games=DEFAULT_CURVE_MINIMAX_GAMES):
    enable_minimax_cache()
    runs = []

    for knob, values in SWEEPS.items():
        for value in values:
            print(f"  training {knob}={value} ...", flush=True)
            run = run_one(knob, value, episodes, eval_every, eval_games, final_games, seed,
                          curve_minimax_games=curve_minimax_games)
            runs.append(run)
            print(f"    final win rate vs random {run['vs_random']['a_win_rate']*100:5.1f}%"
                  f" | draw rate vs minimax {run['vs_minimax']['draw_rate']*100:5.1f}%")

    return runs


def to_csv_row(run):
    params = run["params"]
    random_counts = run["vs_random"]["counts"]
    minimax_counts = run["vs_minimax"]["counts"]

    return {
        "knob": run["knob"],
        "value": run["value"],
        "note": run["note"],
        "alpha": params["alpha"],
        "gamma": params["gamma"],
        "epsilon_decay": params["epsilon_decay"],
        "min_epsilon": params["min_epsilon"],
        "episodes": run["episodes"],
        "seed": run["seed"],
        "final_epsilon": round(run["final_epsilon"], 6),
        "vs_random_wins": random_counts["a_wins"],
        "vs_random_losses": random_counts["b_wins"],
        "vs_random_draws": random_counts["draw"],
        "vs_random_win_rate": run["vs_random"]["a_win_rate"],
        "vs_minimax_wins": minimax_counts["a_wins"],
        "vs_minimax_losses": minimax_counts["b_wins"],
        "vs_minimax_draws": minimax_counts["draw"],
        "vs_minimax_draw_rate": run["vs_minimax"]["draw_rate"],
    }


def write_outputs(runs):
    ensure_dirs()

    # Raw curves, so the plots can be redrawn without retraining anything.
    with open(CURVES_JSON, "w") as handle:
        json.dump([
            {
                "knob": run["knob"],
                "value": run["value"],
                "note": run["note"],
                "params": run["params"],
                "episodes": run["episodes"],
                "seed": run["seed"],
                "curve": run["curve"],
                "vs_random_win_rate": run["vs_random"]["a_win_rate"],
                "vs_minimax_draw_rate": run["vs_minimax"]["draw_rate"],
            }
            for run in runs
        ], handle, indent=2)

    with open(STUDY_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(to_csv_row(run) for run in runs)


def main():
    parser = argparse.ArgumentParser(description="Run the hyper-parameter study.")
    parser.add_argument("--episodes", type=int, default=DEFAULT_EPISODES,
                        help=f"training episodes per run (default {DEFAULT_EPISODES})")
    parser.add_argument("--eval-every", type=int, default=DEFAULT_EVAL_EVERY,
                        help=f"measure the win rate this often (default {DEFAULT_EVAL_EVERY})")
    parser.add_argument("--eval-games", type=int, default=DEFAULT_EVAL_GAMES,
                        help=f"games per curve point (default {DEFAULT_EVAL_GAMES})")
    parser.add_argument("--final-games", type=int, default=DEFAULT_FINAL_GAMES,
                        help=f"games for the final scoring of each run (default {DEFAULT_FINAL_GAMES})")
    parser.add_argument("--curve-minimax-games", type=int, default=DEFAULT_CURVE_MINIMAX_GAMES,
                        help=f"games per curve point against minimax (default {DEFAULT_CURVE_MINIMAX_GAMES})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"random seed, recorded in the results (default {DEFAULT_SEED})")
    args = parser.parse_args()

    print(f"Running {sum(len(v) for v in SWEEPS.values())} training runs "
          f"at {args.episodes} episodes each, seed {args.seed}\n")

    runs = run_study(
        episodes=args.episodes,
        eval_every=args.eval_every,
        eval_games=args.eval_games,
        final_games=args.final_games,
        seed=args.seed,
        curve_minimax_games=args.curve_minimax_games,
    )

    write_outputs(runs)
    print(f"\nWrote {CURVES_JSON}\nWrote {STUDY_CSV}")


if __name__ == "__main__":
    main()
