## The experiment harness. Takes two agents, plays them against each other N times, and
## records wins/losses/draws. Everything else in evaluation/ is built on top of this.

import random
from contextlib import contextmanager

from environment.environment import play_game
from environment.q_training import train

from evaluation.compat import stable_rng


@contextmanager
def greedy(agent):
    """Turn exploration off for the duration of an evaluation, then put it back.

    When we're measuring an agent we want its best known move every single time, not a
    move it picked to explore with. Agents that don't have an epsilon at all (minimax,
    random) just pass straight through untouched.
    """
    if not hasattr(agent, 'epsilon'):
        yield agent
        return

    saved_epsilon = agent.epsilon
    agent.epsilon = 0
    try:
        yield agent
    finally:
        agent.epsilon = saved_epsilon


def run_matchup(agent_a, agent_b, n, seed=None):
    """Play agent_a against agent_b n times and tally the outcomes from a's point of view."""
    if seed is not None:
        random.seed(seed)

    tally = {"a_wins": 0, "b_wins": 0, "draw": 0}

    for game in range(n):
        # Alternating who starts. Half the games a is X, half the games a is O, otherwise
        # the first-move advantage alone decides the numbers and they tell us nothing.
        a_is_x = (game % 2 == 0)

        if a_is_x:
            result, history = play_game(agent_a, agent_b)
            mark_a = 'X'
        else:
            result, history = play_game(agent_b, agent_a)
            mark_a = 'O'

        if result == 'draw':
            tally['draw'] += 1
        elif result == mark_a:
            tally['a_wins'] += 1
        else:
            tally['b_wins'] += 1

    return {
        "a_win_rate": tally['a_wins'] / n,
        "b_win_rate": tally['b_wins'] / n,
        "draw_rate": tally['draw'] / n,
        "counts": tally,
        "number_of_games": n,
    }


def evaluate(agent, opponent, n_games, seed=None):
    """Measure agent against opponent with exploration switched off on both sides.

    Returns the whole result dict rather than a single number, because the two matchups
    we care about read different fields off it: the random matchup wants the win rate,
    the minimax matchup wants the draw rate.
    """
    with greedy(agent), greedy(opponent):
        return run_matchup(agent, opponent, n_games, seed=seed)


def train_with_curve(agent, episodes, eval_every, eval_games, opponent,
                     alpha, gamma, epsilon_decay, min_epsilon, seed=None,
                     optimal_opponent=None, optimal_games=None):
    """Train in chunks, measuring the agent after each chunk.

    Returns a list of points, which is what the learning curve plots are drawn from.
    Each point has the episodes trained so far and the win rate against `opponent`.

    If `optimal_opponent` is given (in practice, minimax) each point also gets a draw
    rate against it. That second measurement is the one that actually tells settings
    apart: beating a random opponent is an easy bar that even a badly tuned agent clears,
    so the win rate saturates around 90% and every curve ends up on top of every other.
    Drawing against perfect play is pass/fail on never making a losing mistake, so it
    stays sensitive all the way to convergence.

    The whole run sits inside stable_rng so training and measurement share one continuous
    random stream seeded exactly once (see compat.py for why that needs a workaround).
    """
    curve = []

    with stable_rng(seed):
        for completed in range(0, episodes, eval_every):
            chunk = min(eval_every, episodes - completed)

            train(agent, chunk, alpha, gamma, epsilon_decay, min_epsilon)

            point = {
                "episodes": completed + chunk,
                "win_rate": evaluate(agent, opponent, eval_games)['a_win_rate'],
            }

            if optimal_opponent is not None:
                # Snapshot the RNG, take the measurement, then put the stream back exactly
                # where it was. Measuring consumes random numbers, and without this the
                # extra probe would shift every training game that follows it, changing
                # results that were already published. This way the numbers this study
                # produced before the probe existed still reproduce exactly.
                snapshot = random.getstate()
                point["draw_rate"] = evaluate(
                    agent, optimal_opponent, optimal_games or eval_games
                )['draw_rate']
                random.setstate(snapshot)

            curve.append(point)

    return curve
