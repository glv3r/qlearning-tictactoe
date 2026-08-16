from collections import Counter

from agents.minimax_agent import MinimaxAgent
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent
from environment.environment import (
    Agent,
    apply_move,
    check_winner,
    legal_moves,
    new_board,
    play_game,
    replay,
)
from environment.q_training import train

# batch testing for n games between two agents

# declaring minimax and random agents
baidoo = MinimaxAgent('Baidoo')
tetteh = MinimaxAgent('Tetteh')

glover = RandomAgent('Glover')
akosua = RandomAgent('Akosua')

q1 = QTableAgent("Q1", epsilon=1)



def run_matchup(agent_a: Agent, agent_b: Agent, n: int, expect_no_loss_for=None):
    counter = Counter()

    for game in range(n):
    
        # alternating who starts first between minimax and
        # the random agent
        if game % 2 == 0:
             mark_a = 'X'
             r, h = play_game(agent_a, agent_b)
        else:
             mark_a = 'O'
             r, h = play_game(agent_b, agent_a) 
        
        assert r in {'X', 'O', 'draw'} # the result must be one of the three 

        # we're basically saying here that the length of our history list
        # should between 5 and 9, the reason being that it takes 3 moves from
        # X, and 2 from O (or vice versa), at the very least, to get a win
        assert 5 <= len(h) <= 9 
        # Replay the history using an empty board to see if the final board matches our result
        board = new_board() 
        for e in h:
             # state matches
             assert board == e.board
             # move is legal
             assert e.action in legal_moves(board)
             board = apply_move(board, e.action, e.mark) 

        # includes last move    
        assert check_winner(board=board) == r 

        if r == 'draw':
             outcome = 'draw'
        elif r == mark_a:
             outcome = agent_a.agent_name
        else:
             outcome = agent_b.agent_name
       

        if expect_no_loss_for is not None:
            loser = agent_b.agent_name if expect_no_loss_for is agent_a else agent_a.agent_name
            assert outcome != loser, f"{expect_no_loss_for.agent_name} lost as {mark_a}: {h}"
        
        counter[outcome] += 1
    
    
    return counter 

def verify():
    """Prove the environment and minimax are correct. This is the ground truth check.

    Every result in the project is measured against minimax, so if minimax can be beaten,
    or the win checker is wrong, then nothing downstream means anything. run_matchup
    asserts its way through each game: the replayed history has to match the board, every
    move has to have been legal, the final board has to agree with the reported result,
    and minimax must never lose.
    """
    print('minimax vs random:', run_matchup(baidoo, glover, 1000, expect_no_loss_for=baidoo))
    print('minimax vs minimax:', run_matchup(tetteh, baidoo, 50, expect_no_loss_for=None))
    print('random vs random:', run_matchup(glover, akosua, 5000))
    print('\nMinimax never lost. Environment and minimax verified.')


def retrain(output='q_table_trained'):
    """Retrain the Q-agent from scratch and overwrite the saved Q-table.

    Deliberately not the default action. q_table_trained is the artifact every evaluation
    number is computed from, so running this file shouldn't quietly replace it. seed=6
    reproduces the committed table exactly.
    """
    print(f'Training 10000 self-play games, will overwrite {output} ...')
    train(agent=q1, episodes=10000, alpha=0.5, gamma=0.9, epsilon_decay=0.0001,
          min_epsilon=0.05, seed=6)
    q1.save_q_table(output)
    print(f'Wrote {output}')


if __name__ == '__main__':
    import sys

    if '--retrain' in sys.argv:
        retrain()
    elif '--replay' in sys.argv:
        r, h = play_game(baidoo, glover)
        replay(h, r)
    else:
        verify()