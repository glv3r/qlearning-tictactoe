from typing import Counter

from environment.environment import apply_move, check_winner, legal_moves, new_board, play_game
from agents.random_agent import RandomAgent


# batch testing for 5000 games between two random agents


baidoo = RandomAgent('Baidoo')
glover = RandomAgent('Glover')
counter = Counter()

for game in range(5000):
    
    r, h = play_game(baidoo, glover)
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
    counter[r] += 1


print(counter) 