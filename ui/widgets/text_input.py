## A single-line text field. Only the name-entry screen uses it.
##
## Focus is owned by the screen, not the field — it decides which one Tab moves to and
## which one a click lands in — so this just reports whether it was clicked and renders
## itself accordingly.

import pygame

from ui import anim, theme
from ui.render import glow, shapes, text as T

CARET_W = 2
CARET_H = 24
PAD_X = 14


class TextInput:
    def __init__(self, topleft, width, value='', placeholder='', max_length=12):
        self.rect = pygame.Rect(topleft[0], topleft[1], width, theme.INPUT_H)
        self.value = value
        self.placeholder = placeholder
        self.max_length = max_length
        self.focused = False
        self.clock = 0.0

        self.font = T.body(17)
        self._idle = shapes.rounded_rect(self.rect.size, theme.RADIUS_XS,
                                         fill=theme.INPUT_BG, border=theme.BORDER)
        self._active = shapes.rounded_rect(self.rect.size, theme.RADIUS_XS,
                                           fill=theme.INPUT_BG, border=theme.O_CYAN)
        # the design's focus ring is a 4px spread plus a soft 18px bloom
        self._ring = glow.rounded(self.rect.size, theme.RADIUS_XS, theme.O_CYAN, 18,
                                  0.25, spread=4)

    @property
    def filled(self) -> bool:
        return bool(self.value.strip())

    def handle_event(self, event) -> bool:
        """Returns True if this field wants focus (it was clicked)."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)

        if not self.focused or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(self.value) < self.max_length:
                self.value += event.unicode

        return False

    def update(self, dt: float) -> None:
        self.clock += dt

    def draw(self, surface):
        if self.focused:
            glow.draw_under(surface, self._ring, self.rect.topleft, 18)
            surface.blit(self._active, self.rect)
        else:
            surface.blit(self._idle, self.rect)

        x = self.rect.x + PAD_X
        if self.value:
            label = T.label(self.value, self.font, theme.TEXT)
        else:
            label = T.label(self.placeholder, self.font, theme.TEXT_DIM)
        surface.blit(label, label.get_rect(midleft=(x, self.rect.centery)))

        if self.focused:
            caret_x = x + (label.get_width() + 3 if self.value else 0)
            alpha = anim.step_blink(self.clock, theme.BLINK_CARET, 255, 0)
            if alpha:
                caret = pygame.Surface((CARET_W, CARET_H), pygame.SRCALPHA)
                caret.fill(theme.O_CYAN)
                surface.blit(caret, caret.get_rect(
                    midleft=(caret_x, self.rect.centery)))
