import random
from environment.environment import play_game


reward_scheme = {'win': 1, 'loss': -1, 'draw': 0}

def train(agent, episodes, alpha, gamma, epsilon_decay, min_epsilon):
    random.seed(6)
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