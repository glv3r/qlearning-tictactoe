## The modal shell shared by the pause and game-over overlays: a wash over the live board,
## then a panel that pops in on top of it.
##
## The panel scales during its entrance but its contents don't — they fade in over the tail
## of the pop instead. That keeps buttons in plain screen coordinates, so hit-testing needs
## no transform, and at a 0.9-to-1.0 scale over 0.22s the difference isn't visible anyway.

import pygame

from ui import anim, theme
from ui.render import glow, shapes


class Dialog:
    def __init__(self, width, height, accent=None, css_glow=44, radius=theme.RADIUS_MD):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (theme.WIDTH // 2, theme.HEIGHT // 2)
        self.accent = accent

        self.panel = shapes.rounded_rect(
            self.rect.size, radius, fill=theme.PANEL, border=accent or theme.BORDER)
        self.halo = (glow.rounded(self.rect.size, radius, accent, css_glow, 0.3)
                     if accent else None)
        self.css_glow = css_glow

        self.fade = anim.Timer(theme.BACKDROP_FADE)
        self.pop = anim.Timer(theme.DIALOG_POP)

        self._wash = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        self._wash.fill(theme.OVERLAY)

    def replay(self) -> None:
        """Restart the entrance animation."""
        self.fade.reset()
        self.pop.reset()

    def update(self, dt: float) -> None:
        self.fade.update(dt)
        # the panel doesn't start moving until the wash is most of the way in
        if self.fade.progress > 0.5:
            self.pop.update(dt)

    @property
    def content_alpha(self) -> int:
        """Contents fade in over the last 40% of the pop."""
        return round(255 * anim.clamp01((self.pop.progress - 0.6) / 0.4))

    def draw(self, surface) -> None:
        surface.blit(shapes.with_alpha(self._wash, round(255 * self.fade.progress)), (0, 0))

        # anything decorative goes on after the wash but before the panel, so it can't
        # cover the dialog's own text and buttons
        self.draw_behind(surface)

        if self.pop.elapsed <= 0:
            return

        scale = anim.lerp(0.9, 1.0, anim.ease_out_back(self.pop.progress))
        alpha = round(255 * anim.clamp01(self.pop.progress * 2))

        if self.halo is not None:
            halo, _ = anim.scaled(self.halo, scale)
            surface.blit(shapes.with_alpha(halo, alpha),
                         halo.get_rect(center=self.rect.center))

        panel, _ = anim.scaled(self.panel, scale)
        surface.blit(shapes.with_alpha(panel, alpha), panel.get_rect(center=self.rect.center))

        if self.content_alpha:
            self.draw_contents(surface, self.content_alpha)

    def draw_contents(self, surface: pygame.Surface, alpha: int) -> None:
        """Override to paint the dialog's body, in screen coordinates."""

    def draw_behind(self, surface: pygame.Surface) -> None:
        """Override to paint between the wash and the panel — confetti, mostly."""
