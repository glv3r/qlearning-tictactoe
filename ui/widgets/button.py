## Buttons, in the four flavours the design uses: a gradient primary, a cyan outline, a
## round icon button, and a bare text link.
##
## They share a base that owns hit-testing and hover, and each one pre-builds its surfaces
## in `_build` so a frame is just a couple of blits.

import pygame

from ui import theme
from ui.render import glow, gradients, icons, shapes, text as T


class Widget:
    """Anything clickable: tracks hover, reports clicks, knows if it's disabled."""

    def __init__(self, rect, on_click=None):
        self.rect = pygame.Rect(rect)
        self.on_click = on_click
        self.hovered = False
        self.enabled = True

    def handle_event(self, event) -> bool:
        """Returns True if this widget consumed the event."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.enabled and self.rect.collidepoint(event.pos)
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and self.enabled and self.rect.collidepoint(event.pos)):
            if self.on_click is not None:
                self.on_click()
            return True
        return False

    def update(self, dt: float) -> None:
        pass


class GradientButton(Widget):
    """The primary call to action — START GAME, REMATCH, RESUME."""

    def __init__(self, rect, label, on_click=None, stops=theme.PRIMARY, icon=None,
                 icon_side='right', font_size=20, tracking=0.08, radius=12,
                 glow_color=theme.EMBER, css_glow=28, icon_size=22):
        super().__init__(rect, on_click)
        self.label = label
        self.stops = tuple(stops)
        self.icon = icon
        self.icon_side = icon_side
        self.font = T.display(font_size)
        self.tracking = tracking
        self.radius = radius
        self.icon_size = icon_size
        self.glow_color = glow_color
        self.css_glow = css_glow
        self._build()

    def _build(self):
        size = self.rect.size
        self.face = gradients.rounded(size, self.stops, self.radius)
        self.halo = glow.rounded(size, self.radius, self.glow_color, self.css_glow, 0.45)
        self.text = T.tracked(self.label, self.font, theme.INK, self.tracking)
        self.icon_surface = (icons.render(self.icon, self.icon_size, theme.INK)
                             if self.icon else None)

    def draw(self, surface):
        alpha = 255 if self.enabled else 102        # the design dims a blocked CTA to 40%
        lift = -2 if (self.hovered and self.enabled) else 0
        rect = self.rect.move(0, lift)

        if self.enabled:
            glow.draw_under(surface, self.halo, rect.topleft, self.css_glow)
        surface.blit(shapes.with_alpha(self.face, alpha), rect)

        # centre the label, plus its icon if there is one, as a single group
        gap = 12
        width = self.text.get_width() + (
            self.icon_surface.get_width() + gap if self.icon_surface else 0)
        x = rect.centerx - width // 2

        if self.icon_surface and self.icon_side == 'left':
            surface.blit(shapes.with_alpha(self.icon_surface, alpha),
                         self.icon_surface.get_rect(midleft=(x, rect.centery)))
            x += self.icon_surface.get_width() + gap

        surface.blit(shapes.with_alpha(self.text, alpha),
                     self.text.get_rect(midleft=(x, rect.centery)))
        x += self.text.get_width() + gap

        if self.icon_surface and self.icon_side == 'right':
            surface.blit(shapes.with_alpha(self.icon_surface, alpha),
                         self.icon_surface.get_rect(midleft=(x, rect.centery)))


class OutlineButton(Widget):
    """Transparent with a coloured border — the secondary action in every dialog."""

    def __init__(self, rect, label, on_click=None, color=theme.O_CYAN, icon=None,
                 font_size=16, tracking=0.06, radius=10, icon_size=18):
        super().__init__(rect, on_click)
        self.color = color
        self.label = label
        self.icon = icon
        self.font = T.display(font_size)
        self.tracking = tracking
        self.radius = radius
        self.icon_size = icon_size
        self._build()

    def _build(self):
        self.face = shapes.rounded_rect(self.rect.size, self.radius, border=self.color)
        self.face_hover = shapes.rounded_rect(self.rect.size, self.radius,
                                              fill=(*self.color, 26), border=self.color)
        self.text = T.tracked(self.label, self.font, self.color, self.tracking)
        self.icon_surface = (icons.render(self.icon, self.icon_size, self.color)
                             if self.icon else None)

    def draw(self, surface):
        surface.blit(self.face_hover if self.hovered else self.face, self.rect)

        gap = 8
        width = self.text.get_width() + (
            self.icon_surface.get_width() + gap if self.icon_surface else 0)
        x = self.rect.centerx - width // 2

        if self.icon_surface:
            surface.blit(self.icon_surface,
                         self.icon_surface.get_rect(midleft=(x, self.rect.centery)))
            x += self.icon_surface.get_width() + gap

        surface.blit(self.text, self.text.get_rect(midleft=(x, self.rect.centery)))


class IconButton(Widget):
    """A round translucent button — sound, pause, and the back arrow."""

    def __init__(self, center, icon, on_click=None, size=theme.ICON_BTN_MENU,
                 color=theme.O_CYAN, icon_size=22):
        rect = pygame.Rect(0, 0, size, size)
        rect.center = center
        super().__init__(rect, on_click)
        self.icon = icon
        self.color = color
        self.icon_size = icon_size
        self._build()

    def _build(self):
        size = self.rect.size
        self.face = shapes.pill(size, fill=(*theme.PANEL, 204), border=theme.BORDER)
        self.face_hover = shapes.pill(size, fill=(*theme.PANEL, 240), border=self.color)

    def set_icon(self, icon: str) -> None:
        """Swap the glyph — the speaker button toggles between two."""
        self.icon = icon

    def draw(self, surface):
        surface.blit(self.face_hover if self.hovered else self.face, self.rect)
        icons.draw(surface, self.icon, self.icon_size, self.color, center=self.rect.center)


class TextButton(Widget):
    """A bare link with no chrome — 'Quit to Menu'."""

    def __init__(self, center, label, on_click=None, color=theme.PINK, icon=None,
                 font_size=15, weight=600, icon_size=17, width=220, height=34):
        rect = pygame.Rect(0, 0, width, height)
        rect.center = center
        super().__init__(rect, on_click)
        self.color = color
        self.icon = icon
        self.icon_size = icon_size
        self.text = T.label(label, T.body(font_size, weight), color)
        self.icon_surface = icons.render(icon, icon_size, color) if icon else None

    def draw(self, surface):
        alpha = 255 if self.hovered else 200
        gap = 8
        width = self.text.get_width() + (
            self.icon_surface.get_width() + gap if self.icon_surface else 0)
        x = self.rect.centerx - width // 2

        if self.icon_surface:
            surface.blit(shapes.with_alpha(self.icon_surface, alpha),
                         self.icon_surface.get_rect(midleft=(x, self.rect.centery)))
            x += self.icon_surface.get_width() + gap

        surface.blit(shapes.with_alpha(self.text, alpha),
                     self.text.get_rect(midleft=(x, self.rect.centery)))
