import random
from environment.environment import play_game


# The reward scheme we actually train with. It's a default rather than a fixed rule so
# that a different scheme can be passed in, which is what the ethics experiment needs:
# training with {'win': 1, 'loss': 0, 'draw': 0} gives the agent no reason to avoid
# losing, and it never learns to block.
DEFAULT_REWARD_SCHEME = {'win': 1, 'loss': -1, 'draw': 0}


def train(agent, episodes, alpha, gamma, epsilon_decay, min_epsilon,
          seed=None, reward_scheme=DEFAULT_REWARD_SCHEME):
    # Seeding is the caller's decision. This used to be a hardcoded random.seed(6) here,
    # which meant that anything calling train() more than once (like measuring a learning
    # curve in chunks) silently restarted the same random stream on every call and kept
    # replaying the same games. Pass a seed to make a run reproducible; pass None to keep
    # whatever stream the caller already set up.
    if seed is not None:
        random.seed(seed)

    for ep in range(episodes):
        result, history = play_game(agent, agent)

        for mark in ['X', 'O']:
            hist = []

            for i in history:
                if mark == i.mark:
                    hist.append(i)

            reversed_hist = list(reversed(hist))
            for index, move in enumerate(reversed_hist):
                state = move.board
                action = move.action
                if index == 0:
                    reward_value = reward(result, mark, reward_scheme)
                    next_state = None
                else:
                    reward_value = 0
                    next_state = reversed_hist[index - 1].board

                agent.update(
                    state,
                    action,
                    reward_value,
                    next_state,
                    alpha,
                    gamma
                )


        agent.epsilon = agent.epsilon - epsilon_decay
        agent.epsilon = max(agent.epsilon, min_epsilon)
            



            



def reward(result, perspective_mark, reward_scheme):
    if result == 'draw':
        return reward_scheme['draw']

    elif result == perspective_mark:
        return reward_scheme['win']

    else:
        return reward_scheme['loss']