import random

from environment.environment import play_game


def run_matchup(agent_a, agent_b, n, seed=None):
    if seed is not None:
        random.seed(seed)
        
    tally = {a_wins: 0, b_wins: 0, draw: 0}
    
    for game in range(n):
        a_is_x = (game % 2 == 0)
        
        if a_is_x:
            result, history = play_game(agent_a, agent_b)
            mark_a = 'X'
        else:
            result, history = play_game(agent_b, agent_a)
            mark_a = 'O'
            
        if result == 'draw':
            tally.draw += 1
        elif result == mark_a:
            tally.a_wins += 1
        else:
            tally.b_wins += 1
    
    return {
        a_win_rate: tally.a_win / n,
        b_win_rate: tally.b_win / n,
        draw_rate: tally.draw / n,
        counts: tally,
        number_of_games: n
    }