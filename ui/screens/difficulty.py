## Screen 03 — pick the agent you want to play against.

import pygame

from agents.minimax_agent import MinimaxAgent
from agents.qtable_agent import QTableAgent
from agents.random_agent import RandomAgent
from evaluation.paths import Q_TABLE
from ui import theme
from ui.render import backdrop, shapes, text as T
from ui.screens.base import Screen
from ui.widgets.button import GradientButton, IconButton
from ui.widgets.card import DifficultyCard

# The trained Q-table, read once when this module is first imported rather than on every
# click. It's a ~260KB pickle, and the difficulty screen can be visited repeatedly.
_q_table = None


def _build_q_agent(name):
    """The agent we actually trained, playing at a difficulty a human can beat.

    Epsilon is what makes this the middle rung. At epsilon 0 the trained agent plays its
    best known move every time and simply never loses — measured over 400 games it lost 0%
    against both minimax and random, so it would feel identical to IMPOSSIBLE. At 0.1 it
    plays its learned best nine times out of ten and picks at random otherwise, which is
    enough to make it beatable (it loses about 20% against minimax) while still winning
    around 85% against a random opponent.
    """
    global _q_table

    agent = QTableAgent(name, epsilon=0.1)
    if _q_table is None:
        agent.load_q_table(str(Q_TABLE))
        _q_table = agent.q_table
    else:
        agent.q_table = _q_table

    return agent


# The three cards, in the order the design lays them out. Each one builds its own agent, so
# a difficulty that needs setup (loading a Q-table, say) doesn't have to look like the ones
# that don't. Nothing else in this screen is aware of how many there are.
DIFFICULTIES = [
    dict(key='easy', title='EASY', icon='smiley', accent=theme.GREEN, tag='CHILL',
         blurb='Plays random moves. A warm-up round.',
         build=RandomAgent, agent_name='Rookie'),
    dict(key='medium', title='MEDIUM', icon='target', accent=theme.GOLD, tag='FAIR FIGHT',
         blurb='Learned to play by training against itself.',
         build=_build_q_agent, agent_name='Contender'),
    dict(key='impossible', title='IMPOSSIBLE', icon='skull', accent=theme.PINK,
         tag='NEVER LOSES', blurb='Perfect play. It never loses.',
         build=MinimaxAgent, agent_name='Oracle'),
]

PLAYER_NAME = 'You'


class DifficultyScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.clock = 0.0
        self.scenery = backdrop.difficulty()

        # centred flex column, 24px gaps: badge / heading / cards / CTA totals 475, so it
        # starts at (700-475)/2 = 113
        self.badge_y = 130
        self.heading_y = 196
        gap = 20
        total = theme.DIFFICULTY_CARD_W * len(DIFFICULTIES) + gap * (len(DIFFICULTIES) - 1)
        left = (theme.WIDTH - total) // 2
        cards_y = 254

        self.cards = []
        for i, spec in enumerate(DIFFICULTIES):
            x = left + i * (theme.DIFFICULTY_CARD_W + gap)
            card = DifficultyCard((x, cards_y), spec['title'], spec['blurb'], spec['icon'],
                                  spec['accent'], spec['tag'])
            card.on_click = (lambda index=i: self._select(index))
            self.cards.append(card)

        self.selected = 1                       # the design ships with MEDIUM chosen
        self.cards[self.selected].selected = True

        start = pygame.Rect(0, 0, 268, 56)
        start.center = (theme.WIDTH // 2, 560)
        self.start = GradientButton(start, 'START GAME', on_click=self._start,
                                    icon='arrow-right')
        self.back = IconButton((24 + 24, 24 + 24), 'arrow-left', on_click=self.app.pop,
                               color=theme.TEXT_SOFT)

    ## ---------- ACTIONS

    def _select(self, index):
        self.selected = index
        for i, card in enumerate(self.cards):
            card.selected = i == index

    def _start(self):
        from ui.match import MatchController, PlayerSlot
        from ui.screens.game import GameScreen
        spec = DIFFICULTIES[self.selected]
        agent = spec['build'](spec['agent_name'])

        # the human takes X, so they always open the round
        match = MatchController(PlayerSlot(PLAYER_NAME),
                                PlayerSlot(spec['agent_name'], agent))
        self.app.replace(GameScreen(self.app, match))

    ## ---------- LOOP

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.pop()
                return
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = -1 if event.key == pygame.K_LEFT else 1
                self._select((self.selected + step) % len(self.cards))
                return
            if event.key == pygame.K_RETURN:
                self._start()
                return

        for card in self.cards:
            card.handle_event(event)
        self.start.handle_event(event)
        self.back.handle_event(event)

    def update(self, dt):
        self.clock += dt

    def draw(self, surface):
        surface.blit(self.scenery, (0, 0))

        badge = T.tracked('PLAYER VS AGENT', T.body(13, 600), theme.GOLD, 0.25)
        pill = shapes.pill((badge.get_width() + 40, 33), fill=(*theme.X_ORANGE, 26),
                           border=(*theme.X_ORANGE, 153))
        rect = pill.get_rect(center=(theme.WIDTH // 2, self.badge_y))
        surface.blit(pill, rect)
        surface.blit(badge, badge.get_rect(center=rect.center))

        T.draw(surface, T.label('PICK YOUR OPPONENT', T.display(52), theme.TEXT),
               center=(theme.WIDTH // 2, self.heading_y))

        for card in self.cards:
            card.draw(surface, self.clock)
        self.start.draw(surface)
        self.back.draw(surface)
