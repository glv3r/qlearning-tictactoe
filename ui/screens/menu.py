## Screen 01 — the main menu.

import pygame

from ui import anim, theme
from ui.render import backdrop, glow, gradients, icons, shapes, text as T
from ui.screens.base import Screen
from ui.widgets.board import MiniMark
from ui.widgets.button import IconButton
from ui.widgets.card import ModeCard

TITLE_SIZE = 92
GLYPH_SIZE = 54


class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.clock = 0.0
        self.scenery = backdrop.menu()

        self.title = gradients.text('TIC TAC TOE', T.display(TITLE_SIZE), tuple(theme.TITLE))
        self.title_halo = glow.text('TIC TAC TOE', T.display(TITLE_SIZE), theme.EMBER, 26, 0.5)
        self.x_glyph = MiniMark.surface('X', GLYPH_SIZE)
        self.x_halo = MiniMark.halo('X', GLYPH_SIZE, 14)
        self.o_glyph = MiniMark.surface('O', GLYPH_SIZE)
        self.o_halo = MiniMark.halo('O', GLYPH_SIZE, 14)

        # The design centres badge/title/subtitle/cards as one flex column with a 22px gap.
        # That column is 468 tall, so it starts at (700-468)/2 = 116 and these follow from
        # stacking the items down from there.
        self.badge_y = 133
        self.title_y = 217
        self.subtitle_y = 299
        cards_y = 348
        gap = 24
        left = (theme.WIDTH - (theme.MODE_CARD_W * 2 + gap)) // 2

        self.pvp = ModeCard((left, cards_y), 'PLAYER VS PLAYER',
                            'Grab a friend and take turns on one screen.',
                            'users', theme.O_CYAN, on_click=self._start_pvp)
        self.pva = ModeCard((left + theme.MODE_CARD_W + gap, cards_y), 'PLAYER VS AGENT',
                            'Easy, Medium, or flat-out Impossible.',
                            'robot', theme.X_ORANGE, on_click=self._start_pva)

        self.pva = ModeCard((left + theme.MODE_CARD_W + gap, cards_y), 'AGENT VS AGENT',
                                    'To demonstrate how the various agents play against each other',
                                    'robot', theme.X_ORANGE, on_click=self._start_pva)

        self.sound = IconButton((theme.WIDTH - 24 - 24, 24 + 24), self._sound_icon(),
                                on_click=self._toggle_sound)
        self.widgets = [self.pvp, self.pva, self.sound]

    ## ---------- ACTIONS

    def _sound_icon(self):
        return 'speaker-high' if self.app.sound_on else 'speaker-slash'

    def _toggle_sound(self):
        self.app.sound_on = not self.app.sound_on
        self.sound.set_icon(self._sound_icon())

    def _start_pvp(self):
        from ui.screens.name_entry import NameEntryScreen
        self.app.push(NameEntryScreen(self.app))

    def _start_pva(self):
        from ui.screens.difficulty import DifficultyScreen
        self.app.push(DifficultyScreen(self.app))

    ## ---------- LOOP

    def on_enter(self):
        self.sound.set_icon(self._sound_icon())
        for w in self.widgets:
            w.hovered = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.quit()
            return
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        self.clock += dt

    def draw(self, surface):
        surface.blit(self.scenery, (0, 0))

        # ARCADE EDITION pill
        self._draw_badge(surface, self.badge_y)

        # title row: X glyph, wordmark, O glyph
        self._draw_title(surface)

        T.draw(surface, T.label('First to three wins takes the match', T.body(18),
                                theme.TEXT_SOFT), center=(theme.WIDTH // 2, self.subtitle_y))

        for card in (self.pvp, self.pva):
            card.draw(surface, self.clock)
        self.sound.draw(surface)

        # PRESS START, blinking hard on and off
        press = T.tracked('PRESS START', T.body(13, 500), theme.GOLD, 0.3)
        surface.blit(shapes.with_alpha(press, round(255 * anim.step_blink(
            self.clock, theme.BLINK_SLOW))), press.get_rect(center=(theme.WIDTH // 2, 676)))

    def _draw_badge(self, surface, cy):
        font = T.body(13, 600)
        label = T.tracked('ARCADE EDITION', font, theme.GOLD, 0.25)
        star = icons.render('star', 13, theme.GOLD, fill=True)
        gap = 10
        width = label.get_width() + (star.get_width() + gap) * 2 + 40
        height = 33

        pill = shapes.pill((width, height), fill=(*theme.X_ORANGE, 26),
                           border=(*theme.X_ORANGE, 153))
        rect = pill.get_rect(center=(theme.WIDTH // 2, cy))
        surface.blit(pill, rect)

        x = rect.x + 20
        surface.blit(star, star.get_rect(midleft=(x, cy)))
        x += star.get_width() + gap
        surface.blit(label, label.get_rect(midleft=(x, cy)))
        x += label.get_width() + gap
        surface.blit(star, star.get_rect(midleft=(x, cy)))

    def _draw_title(self, surface):
        cy = self.title_y
        gap = 30
        total = self.x_glyph.get_width() + gap + self.title.get_width() + gap + \
            self.o_glyph.get_width()
        x = (theme.WIDTH - total) // 2

        surface.blit(self.x_halo, self.x_halo.get_rect(center=(x + GLYPH_SIZE // 2, cy)))
        surface.blit(self.x_glyph, self.x_glyph.get_rect(center=(x + GLYPH_SIZE // 2, cy)))
        x += self.x_glyph.get_width() + gap

        # the wordmark's glow breathes slowly rather than sitting at a fixed strength
        title_rect = self.title.get_rect(midleft=(x, cy))
        breath = anim.pulse(self.clock, 4.0, 0.45, 1.0)
        pad = glow.glow_offset(26)
        surface.blit(shapes.with_alpha(self.title_halo, round(255 * breath)),
                     (title_rect.x - pad, title_rect.y - pad))
        surface.blit(self.title, title_rect)
        x += self.title.get_width() + gap

        surface.blit(self.o_halo, self.o_halo.get_rect(center=(x + GLYPH_SIZE // 2, cy)))
        surface.blit(self.o_glyph, self.o_glyph.get_rect(center=(x + GLYPH_SIZE // 2, cy)))
