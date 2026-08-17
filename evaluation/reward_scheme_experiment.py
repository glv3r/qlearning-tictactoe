## The reward-design experiment: change one number in the reward scheme and nothing else,
## then measure what it does to the policy.
##
## Two agents are trained from the same seed with identical hyper-parameters. The only
## difference is the terminal reward for a draw: 0 in the baseline, 5 in the modified run.
## The intuition is that rewarding draws more should produce more draws. It doesn't.
##
## Run with:  python -m evaluation.reward_scheme_experiment

from evaluation.compat import enable_minimax_cache
from evaluation.harness import evaluate
from environment.q_training import train

from agents.minimax_agent import MinimaxAgent
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent

# Same settings that produced q_table_trained, so the baseline column of the table in the
# report is directly comparable to the headline results.
HYPERPARAMS = dict(episodes=10000, alpha=0.5, gamma=0.9,
                   epsilon_decay=0.0001, min_epsilon=0.05)
TRAIN_SEED = 6
EVAL_SEED = 20250816
GAMES = 1000

SCHEMES = {
    'baseline (draw = 0)': {'win': 1, 'loss': -1, 'draw': 0},
    'modified (draw = 5)': {'win': 1, 'loss': -1, 'draw': 5},
}


def main():
    # Minimax is a pure function of (board, player), so memoising it changes no result.
    # Without it the two 1000-game minimax matchups below take roughly 20 minutes.
    enable_minimax_cache()

    for label, scheme in SCHEMES.items():
        agent = QTableAgent(label, epsilon=1)
        train(agent, reward_scheme=scheme, seed=TRAIN_SEED, **HYPERPARAMS)

        # Counted before any evaluation. choose_move creates table entries lazily, so
        # evaluating an agent can grow its table and inflate this number.
        states = len(agent.q_table)

        vs_random = evaluate(agent, RandomAgent('rand'), GAMES, seed=EVAL_SEED)
        vs_minimax = evaluate(agent, MinimaxAgent('perfect'), GAMES, seed=EVAL_SEED)

        r, m = vs_random['counts'], vs_minimax['counts']
        print(f"\n{label}   scheme={scheme}")
        print(f"  states learned      {states}")
        print(f"  vs random   W/L/D   {r['a_wins']}/{r['b_wins']}/{r['draw']}"
              f"   win rate {vs_random['a_win_rate']:.1%}")
        print(f"  vs minimax  W/L/D   {m['a_wins']}/{m['b_wins']}/{m['draw']}"
              f"   draw rate {vs_minimax['draw_rate']:.1%}")


if __name__ == '__main__':
    main()
