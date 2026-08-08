from collections import Counter

from agents.minimax_agent import MinimaxAgent
from environment.environment import Agent, apply_move, check_winner, legal_moves, new_board, play_game, replay
from agents.random_agent import RandomAgent


# batch testing for n games between two agents

# declaring minimax and random agents
baidoo = MinimaxAgent('Baidoo')
tetteh = MinimaxAgent('Tetteh')

glover = RandomAgent('Glover')
akosua = RandomAgent('Akosua')



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

if __name__ == '__main__':
    # print('minimax vs random:', run_matchup(baidoo, glover, 1000, expect_no_loss_for=baidoo))
    # print('minimax vs minimax:', run_matchup(tetteh, baidoo, 50,  expect_no_loss_for=None))
    # print('random vs random:', run_matchup(glover, akosua, 5000))
    r, h = play_game(glover, baidoo)
    replay(h, r)