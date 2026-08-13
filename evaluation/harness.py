import random

from environment.environment import play_game
from environment.q_training import train


def run_matchup(agent_a, agent_b, n, seed=None):
    if seed is not None:
        random.seed(seed)
        
    tally = {"a_wins": 0, "b_wins": 0, "draw": 0}
    
    for game in range(n):
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
        "a_win_rate": tally.a_win / n,
        "b_win_rate": tally.b_win / n,
        "draw_rate": tally.draw / n,
        "counts": tally,
        "number_of_games": n
    }
    
def evaluate(agent, opponent, n_games):
    saved_epsilon =  agent.epsilon
    agent_epsilon = 0
    
    
    try:
        result = run_matchup(agent, opponent, n_games)
    finally:
        agent.epsilon = saved_epsilon
        
    
    return result['a_win_rate']


def train_with_curve(agent, episodes, eval_every, eval_games, opponent, alpha, gamma, epsilon):
    curve = []
    
    for epi in range(0, episodes, eval_every):
        train(agent, eval_every, alpha, gamma, epsilon)
        rate = evaluate(agent, opponent, eval_games)
        curve.append((epi + eval_every, rate))
    return curve
    