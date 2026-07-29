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
    # use player to declare who's opponent and who's minimax (player)
    opp = 'O' if player == 'X' else 'X'

    # base case to check for a result at the particular board's state
    r = check_winner(board=board)

    # match r:
    #     case player if player == r:
    #         return 1

    #     case 'draw':
    #         return 0

    #     case opp if opp == r:
    #         return -1

    if r == player:
        return 1
    elif r == 'draw':
        return 0
    elif r is not None:
        return -1

    # recursive case for when the game is ongoing still (no result at all)
    if current_player(board) == player:
        best = float('-inf')
        for m in legal_moves(board):
            score = minimax(apply_move(board, m, current_player(board)))
            best = max(best, score)

        return best

    else:
        best = float('inf')
        for m in legal_moves(board):
            score = minimax(apply_move(board, m, current_player(board)))
            best = min(best, score)

        return best

