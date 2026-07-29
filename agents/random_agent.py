import random


from environment.environment import Agent, legal_moves


# Random agent's class implementation
class RandomAgent(Agent):
    def choose_move(self, board) -> int:
        # we get the list of available moves on the board
        legal = legal_moves(board)

        # we pick one of them at random and return it
        return random.choice(legal)


