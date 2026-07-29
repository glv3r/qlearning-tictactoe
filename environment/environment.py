## The environment for which everyone's play relies on. The functions here are used/called
## everywhere else, cause nothing can be tested without a working game.


from abc import ABC, abstractmethod
from environment.models import History

## ---------- CONSTANTS
EMPTY = ''

# Paths we go by in checking for a win
LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8), # horizontal
    (0, 3, 6), (1, 4, 7), (2, 5, 8), # vertical
    (0, 4, 8), (2, 4, 6) # diagonal
]

## ----------- AGENT GENERAL ABSTRACT CLASS

# An agent ABC (abstract base class) with a choose_move method which would
# be implemented differently for q-learning, minimax, and the random agent
from abc import ABC, abstractmethod


class Agent(ABC):

    def __init__(self, agent_name):
        self.agent_name = agent_name    # every random agent can be assigned a name. Cute touch

    @abstractmethod
    def choose_move(self, board) -> int:
        pass





## ------------ METHODS
# A function that returns a new board with 9 empty positions
def new_board() -> tuple[str, ...]:
    return ("",) * 9


# A function that returns a list of all legal moves on the board
def legal_moves(board: tuple[str, ...]):
    return [i for i, val in enumerate(board) if val == EMPTY]   # returning the indexes of those positions


# A function that returns the player whose turn it currently is
def current_player(board: tuple[str, ...]):
    # initialize number of times both X and O have appeared
    x_occurrence = 0
    o_occurrence = 0

    # loop through and count them
    for i in board:
        if i == "X":
            x_occurrence += 1
        elif i == "O":
            o_occurrence += 1

    # return X if it's less than O, else it's O's turn
    return 'X' if x_occurrence <= o_occurrence else 'O'


# A function that applies a move to the current state of the board
def apply_move(board: tuple[str, ...], index: int, mark: str) -> tuple:
    # convert board to a list so we can place the mark on the specific index of play
    l = list(board)
    l[index] = mark

    # return the new state as a tuple again
    return tuple(l)


# A function that checks all 8 lines that could give a win (LINES) and returns a winner if any
def check_winner(board: tuple[str, ...]) -> str | None:

    # we loop through all lines and check whether the position of all 3 indexes have equal X or O.
    # if that's the case then we just return the value there as the winner
    for (x, y, z) in LINES:
        if board[x] != EMPTY and (board[x] == board[y] == board[z]):
            return board[x]

    if EMPTY not in board:
        return 'draw'

    # this means the game is still going on
    return None




# One of the most important functions. Starts a game between two agents
def play_game(agent_x: Agent, agent_o: Agent):
    # we create a new board at the start of the game
    board = new_board()

    # assign the agents an X and O (this will be interchanged between both agents later on when playing a set number of games)
    agents = { 'X': agent_x, 'O': agent_o }
    history: list[History] = [] # empty list to keep state before the agent's move is applied

    while True:
        # retrieve the current plater to play
        mark = current_player(board)

        # the agent with the current turn chooses a move from the available legal ones
        action = agents[mark].choose_move(board)

        # important here that we record the state of the board, with the move the agent intends to make
        # before actually applying it next
        history.append(History(mark=mark, board=board, action=action))

        # apply the move here
        board = apply_move(board, action, mark)

        # after each move is applied we check whether we have a winner
        res = check_winner(board)

        # we stated earlier that none meant that the game is still going on
        if res is not None:
            return res, history

