## Match state for the UI.
##
## environment.play_game runs a whole game inside a `while True`, pulling a move from each
## agent in turn. That works for batch testing but can't be driven from an event loop —
## a human player's move arrives as a mouse click several frames later, not as a return
## value. So this steps the same game one move at a time instead, and everything it does
## to the board goes through the environment's existing pure functions.
##
## It also tracks what a single game doesn't: rounds, running scores, and the first-to-three
## match the design is built around.

from dataclasses import dataclass, field
from enum import Enum

from environment.environment import (Agent, apply_move, check_winner, current_player,
                                     legal_moves, new_board, winning_line)
from environment.models import History
from ui import theme


class Phase(Enum):
    AWAITING_HUMAN = 'awaiting_human'   # waiting on a click
    AGENT_THINKING = 'agent_thinking'   # counting down, then the agent commits
    ROUND_OVER = 'round_over'           # this board is finished, match continues
    MATCH_OVER = 'match_over'           # someone reached WINS_NEEDED


@dataclass
class PlayerSlot:
    """One side of the match. An agent of None means a human is sitting there."""
    name: str
    agent: Agent | None = None

    @property
    def is_human(self) -> bool:
        return self.agent is None


@dataclass
class MatchController:
    x: PlayerSlot
    o: PlayerSlot
    wins_needed: int = theme.WINS_NEEDED

    board: tuple = field(default_factory=new_board)
    history: list[History] = field(default_factory=list)
    round_no: int = 1
    wins: dict = field(default_factory=lambda: {'X': 0, 'O': 0})
    draws: int = 0

    result: str | None = None           # 'X' / 'O' / 'draw' once the round ends
    win_line: tuple | None = None       # the three cells to strike through
    last_move: int | None = None        # cell the most recent mark landed on

    phase: Phase = Phase.AWAITING_HUMAN
    think_elapsed: float = 0.0

    # called with (index, mark) whenever a mark lands, so the screen can animate it
    on_move = None

    def __post_init__(self):
        self._begin_round()

    ## ---------- WHOSE TURN

    @property
    def mark(self) -> str:
        """Whose turn it is. X always opens — that's baked into current_player."""
        return current_player(self.board)

    def slot(self, mark: str) -> PlayerSlot:
        return self.x if mark == 'X' else self.o

    @property
    def current(self) -> PlayerSlot:
        return self.slot(self.mark)

    @property
    def in_play(self) -> bool:
        return self.phase in (Phase.AWAITING_HUMAN, Phase.AGENT_THINKING)

    ## ---------- DRIVING THE GAME

    def update(self, dt: float) -> None:
        """Tick the agent's thinking delay. Call once a frame while the board is live."""
        if self.phase is not Phase.AGENT_THINKING:
            return

        self.think_elapsed += dt
        if self.think_elapsed >= theme.AGENT_THINK:
            mark = self.mark
            self._commit(self.current.agent.choose_move(self.board, mark), mark)

    def play(self, index: int) -> bool:
        """A human clicking a cell. Returns False if that wasn't a legal thing to do."""
        if self.phase is not Phase.AWAITING_HUMAN or index not in legal_moves(self.board):
            return False

        self._commit(index, self.mark)
        return True

    def _commit(self, index: int, mark: str) -> None:
        # record the board *before* the move, matching how play_game builds its history
        self.history.append(History(mark=mark, board=self.board, action=index))
        self.board = apply_move(self.board, index, mark)
        self.last_move = index

        if self.on_move is not None:
            self.on_move(index, mark)

        result = check_winner(self.board)
        if result is None:
            self._await_turn()
            return

        self._finish_round(result)

    def _finish_round(self, result: str) -> None:
        self.result = result
        self.win_line = winning_line(self.board)

        if result == 'draw':
            self.draws += 1
        else:
            self.wins[result] += 1

        self.phase = Phase.MATCH_OVER if self.match_winner else Phase.ROUND_OVER

    ## ---------- ROUNDS

    def _await_turn(self) -> None:
        self.think_elapsed = 0.0
        self.phase = Phase.AWAITING_HUMAN if self.current.is_human else Phase.AGENT_THINKING

    def _begin_round(self) -> None:
        self.board = new_board()
        self.history = []
        self.result = None
        self.win_line = None
        self.last_move = None
        self._await_turn()

    def next_round(self) -> None:
        """Move on after a finished round. No-op once the match is decided."""
        if self.phase is not Phase.ROUND_OVER:
            return
        self.round_no += 1
        self._begin_round()

    def restart_round(self) -> None:
        """Throw away the current board without scoring it — the pause menu's option."""
        self._begin_round()

    def rematch(self) -> None:
        """Reset scores and start the match over."""
        self.round_no = 1
        self.wins = {'X': 0, 'O': 0}
        self.draws = 0
        self._begin_round()

    ## ---------- RESULTS

    @property
    def match_winner(self) -> str | None:
        """The mark that has taken the match, or None if it's still open."""
        for mark in ('X', 'O'):
            if self.wins[mark] >= self.wins_needed:
                return mark
        return None
