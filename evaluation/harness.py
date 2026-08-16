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
                     alpha, gamma, epsilon_decay, min_epsilon, seed=None):
    """Train in chunks, measuring win rate against opponent after each chunk.

    Returns a list of (episodes_trained, win_rate) points, which is what the learning
    curve plots are drawn from. The whole run sits inside stable_rng so that training and
    measurement share one continuous random stream seeded exactly once (see compat.py for
    why that needs a workaround).
    """
    curve = []

    with stable_rng(seed):
        for completed in range(0, episodes, eval_every):
            chunk = min(eval_every, episodes - completed)

            train(agent, chunk, alpha, gamma, epsilon_decay, min_epsilon)

            result = evaluate(agent, opponent, eval_games)
            curve.append((completed + chunk, result['a_win_rate']))

    return curve
