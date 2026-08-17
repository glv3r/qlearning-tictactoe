## Screen 02 — who's playing, for a player-vs-player match.

import pygame

from ui import theme
from ui.render import backdrop, shapes, text as T
from ui.screens.base import Screen
from ui.widgets.button import GradientButton, IconButton
from ui.widgets.card import NameCard
from ui.widgets.text_input import TextInput

DEFAULT_NAMES = ('Ama', 'Kofi')


class NameEntryScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.clock = 0.0
        self.scenery = backdrop.name_entry()

        # centred flex column, 24px gaps: badge / heading / cards / CTA totals 403, so it
        # starts at (700-403)/2 = 149
        self.badge_y = 165
        self.heading_y = 232
        gap = 24
        left = (theme.WIDTH - (theme.NAME_CARD_W * 2 + gap)) // 2
        cards_y = 290

        pad = 24
        self.p1_field = TextInput((left + pad, 0), theme.NAME_CARD_W - pad * 2,
                                  placeholder=DEFAULT_NAMES[0])
        self.p2_field = TextInput((0, 0), theme.NAME_CARD_W - pad * 2,
                                  placeholder=DEFAULT_NAMES[1])
        self.p1_field.focused = True

        self.p1_card = NameCard((left, cards_y), 'X', 'Player 1', self.p1_field)
        self.p2_card = NameCard((left + theme.NAME_CARD_W + gap, cards_y), 'O', 'Player 2',
                                self.p2_field)

        start = pygame.Rect(0, 0, 268, 56)
        start.center = (theme.WIDTH // 2, 524)
        self.start = GradientButton(start, 'START GAME', on_click=self._start,
                                    icon='arrow-right')

        self.back = IconButton((24 + 24, 24 + 24), 'arrow-left', on_click=self.app.pop,
                               color=theme.TEXT_SOFT)
        self.fields = [self.p1_field, self.p2_field]

        # events are handled before update() each frame, so the gate has to be correct
        # from construction — otherwise a click on the very first frame gets through
        # while both fields are still empty
        self._refresh_cta()

    ## ---------- ACTIONS

    def _names(self):
        return (self.p1_field.value.strip() or DEFAULT_NAMES[0],
                self.p2_field.value.strip() or DEFAULT_NAMES[1])

    def _focus(self, field):
        for f in self.fields:
            f.focused = f is field

    def _cycle_focus(self):
        i = next((n for n, f in enumerate(self.fields) if f.focused), 0)
        self._focus(self.fields[(i + 1) % len(self.fields)])

    def _refresh_cta(self):
        # the design dims the CTA until both names are filled in
        self.start.enabled = self.p1_field.filled and self.p2_field.filled

    def _start(self):
        from ui.match import MatchController, PlayerSlot
        from ui.screens.game import GameScreen
        p1, p2 = self._names()
        match = MatchController(PlayerSlot(p1), PlayerSlot(p2))
        self.app.replace(GameScreen(self.app, match))

    ## ---------- LOOP

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.pop()
                return
            if event.key == pygame.K_TAB:
                self._cycle_focus()
                return
            if event.key == pygame.K_RETURN and self.start.enabled:
                self._start()
                return

        for field in self.fields:
            if field.handle_event(event):
                self._focus(field)

        self._refresh_cta()
        self.start.handle_event(event)
        self.back.handle_event(event)

    def update(self, dt):
        self.clock += dt
        for field in self.fields:
            field.update(dt)
        self._refresh_cta()

    def draw(self, surface):
        surface.blit(self.scenery, (0, 0))

        badge = T.tracked('PLAYER VS PLAYER', T.body(13, 600), theme.O_CYAN, 0.25)
        pill = shapes.pill((badge.get_width() + 40, 33), fill=(*theme.O_CYAN, 20),
                           border=(*theme.O_CYAN, 128))
        rect = pill.get_rect(center=(theme.WIDTH // 2, self.badge_y))
        surface.blit(pill, rect)
        surface.blit(badge, badge.get_rect(center=rect.center))

        T.draw(surface, T.label("WHO'S PLAYING?", T.display(52), theme.TEXT),
               center=(theme.WIDTH // 2, self.heading_y))

        self.p1_card.draw(surface, self.clock)
        self.p2_card.draw(surface, self.clock)
        self.start.draw(surface)
        self.back.draw(surface)
