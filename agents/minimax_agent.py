from environment.environment import Agent, apply_move, check_winner, current_player, legal_moves


class MinimaxAgent(Agent):
    def choose_move(self, board, mark) -> int:
        # initialising as a very small number so the first iteration passes, although you
        # can give it -2 and it'll still work because we're always returning either -1, 0 or 1
        # for a move
        best_score = float('-inf')
        best_move = None
        legal = legal_moves(board)   # return all legal moves for iterating

        for m in legal:
            score = minimax(apply_move(board=board, index=m, mark=mark), mark)
            if score > best_score:
                best_score, best_move = score, m

        return best_move


def minimax(board, player: str):
  
    # base case to check for a result at the particular board's state
    r = check_winner(board=board)

    if r == player:
        return 1
    elif r == 'draw':
        return 0
    elif r is not None:
        return -1

    # recursive case for when the game is ongoing still (no result at all)
    turn = current_player(board)

    if turn == player:
        best = float('-inf')
        for m in legal_moves(board):
            score = minimax(apply_move(board, m, turn), player)
            best = max(best, score)

        return best

    else:
        best = float('inf')
        for m in legal_moves(board):
            score = minimax(apply_move(board, m, turn), player)
            best = min(best, score)

        return best

