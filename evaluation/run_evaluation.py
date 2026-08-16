## The two evaluation matchups that actually matter, plus two sanity matchups that give
## the numbers something to be read against.
##
##   Q-agent vs random  -> a win rate. Did the agent learn to punish mistakes?
##   Q-agent vs minimax -> a draw rate. Did the agent reach optimal play? Target is 100%.
##
## The reason we need both is that they measure different things. Beating a bad opponent
## a lot doesn't prove the agent is good, it proves the opponent is bad. Minimax is the
## harder test, and it's the one the report's headline claim rests on.
##
## Run with:  python -m evaluation.run_evaluation

import argparse
import csv

from agents.minimax_agent import MinimaxAgent
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent

from evaluation.compat import enable_minimax_cache
from evaluation.harness import evaluate
from evaluation.paths import MATCHUPS_CSV, Q_TABLE, ensure_dirs

DEFAULT_SEED = 20250816
DEFAULT_GAMES = 1000

CSV_COLUMNS = [
    "matchup", "agent_a", "agent_b", "games", "seed",
    "a_wins", "b_wins", "draws",
    "a_win_rate", "b_win_rate", "draw_rate",
]


def load_q_agent(name="Q-agent"):
    """Load the trained Q-table. Epsilon is 0 because we always want its best known move."""
    agent = QTableAgent(name, epsilon=0)
    agent.load_q_table(str(Q_TABLE))
    return agent


def run_all(games=DEFAULT_GAMES, seed=DEFAULT_SEED):
    enable_minimax_cache()

    matchups = [
        # (label, agent_a, agent_b) - agent_a is the one the rates are reported for
        ("Q-agent vs random", load_q_agent(), RandomAgent("Random")),
        ("Q-agent vs minimax", load_q_agent(), MinimaxAgent("Minimax")),
        ("minimax vs random", MinimaxAgent("Minimax"), RandomAgent("Random")),
        ("random vs random", RandomAgent("Random A"), RandomAgent("Random B")),
    ]

    rows = []
    for label, agent_a, agent_b in matchups:
        # Same seed for every matchup so the numbers are reproducible one by one, rather
        # than only reproducible if you run the whole script start to finish.
        result = evaluate(agent_a, agent_b, games, seed=seed)
        counts = result["counts"]

        rows.append({
            "matchup": label,
            "agent_a": agent_a.agent_name,
            "agent_b": agent_b.agent_name,
            "games": games,
            "seed": seed,
            "a_wins": counts["a_wins"],
            "b_wins": counts["b_wins"],
            "draws": counts["draw"],
            "a_win_rate": result["a_win_rate"],
            "b_win_rate": result["b_win_rate"],
            "draw_rate": result["draw_rate"],
        })

    return rows


def check_ground_truth(rows):
    """Sanity checks on the results. These are bug detectors, not scoring.

    Minimax is the ground truth for the whole project, so if it ever loses, or if the
    Q-agent ever beats it, that's minimax (or the win checker) being broken. The spec is
    blunt about this: a Q-agent win against minimax is a bug signal, not an achievement.
    """
    warnings = []
    by_label = {row["matchup"]: row for row in rows}

    minimax_row = by_label.get("minimax vs random")
    if minimax_row is not None and minimax_row["b_wins"] > 0:
        warnings.append(
            f"BUG SIGNAL: minimax lost {minimax_row['b_wins']} game(s) to random. "
            "Minimax or the win checker is broken, and every number below is meaningless."
        )

    q_vs_minimax = by_label.get("Q-agent vs minimax")
    if q_vs_minimax is not None and q_vs_minimax["a_wins"] > 0:
        warnings.append(
            f"BUG SIGNAL: the Q-agent beat minimax {q_vs_minimax['a_wins']} time(s). "
            "That is not possible against perfect play, so minimax is faulty."
        )

    return warnings


def write_csv(rows):
    ensure_dirs()
    with open(MATCHUPS_CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows, warnings):
    print(f"\n{'matchup':<22}{'games':>7}{'A wins':>9}{'B wins':>9}{'draws':>8}"
          f"{'A win %':>10}{'draw %':>9}")
    print("-" * 74)
    for row in rows:
        print(f"{row['matchup']:<22}{row['games']:>7}{row['a_wins']:>9}{row['b_wins']:>9}"
              f"{row['draws']:>8}{row['a_win_rate']*100:>9.1f}%{row['draw_rate']*100:>8.1f}%")

    by_label = {row["matchup"]: row for row in rows}
    print("\nHeadline results")
    print(f"  win rate vs random   : {by_label['Q-agent vs random']['a_win_rate']*100:.1f}%")
    print(f"  draw rate vs minimax : {by_label['Q-agent vs minimax']['draw_rate']*100:.1f}%  (target 100%)")

    if warnings:
        print()
        for warning in warnings:
            print(f"  !! {warning}")


def main():
    parser = argparse.ArgumentParser(description="Run the evaluation matchups.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES,
                        help=f"games per matchup (spec asks for at least 1000, default {DEFAULT_GAMES})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"random seed, recorded in the results (default {DEFAULT_SEED})")
    args = parser.parse_args()

    rows = run_all(games=args.games, seed=args.seed)
    warnings = check_ground_truth(rows)

    write_csv(rows)
    print_summary(rows, warnings)
    print(f"\nWrote {MATCHUPS_CSV}")


if __name__ == "__main__":
    main()
