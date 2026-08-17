from environment.q_training import train
from evaluation.harness import evaluate


from environment.environment import play_game
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent
from agents.minimax_agent import MinimaxAgent

HYPERPARAMS = dict(episodes=10000, alpha=0.5, gamma=0.9, epsilon_decay=0.0001, min_epsilon=0.05)
SEED = 6


def reward(result, perspective_mark, scheme):
    if result == 'draw':
        return scheme['draw']
    return scheme['win'] if result == perspective_mark else scheme['loss']


def main():
    baseline_scheme = {'win': 1, 'loss': -1, 'draw': 0}
    bad_scheme = {'win': 1, 'loss': -1, 'draw': 5}

    baseline_agent = QTableAgent("baseline", epsilon=1)
    train(baseline_agent, reward_scheme=baseline_scheme, **HYPERPARAMS)

    bad_agent = QTableAgent("bad_reward", epsilon=1)
    train(bad_agent, reward_scheme=bad_scheme, **HYPERPARAMS)

    random_opp = RandomAgent("rand")
    minimax_opp = MinimaxAgent("perfect")  # unpruned -- this step is slow, see README

    print("States learned - baseline:  ", len(baseline_agent.q_table))
    print("States learned - bad reward:", len(bad_agent.q_table))
    print()
    print("BASELINE   vs Random  (1000 games):", evaluate(baseline_agent, random_opp, 1000))
    print("BAD REWARD vs Random  (1000 games):", evaluate(bad_agent, random_opp, 1000))
    print("BASELINE   vs Minimax ( 1000 games):", evaluate(baseline_agent, minimax_opp, 1000))
    print("BAD REWARD vs Minimax ( 1000 games):", evaluate(bad_agent, minimax_opp, 1000))


if __name__ == '__main__':
    main()
