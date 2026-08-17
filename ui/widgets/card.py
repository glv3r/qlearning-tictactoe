## The four card shapes in the design: a mode card on the menu, a difficulty card, a
## player scoreboard beside the board, and a name-entry card.
##
## They all sit on the same translucent panel with a 1px border, so that part is shared;
## what differs is the contents and which states they respond to.

import pygame

from ui import anim, theme
from ui.render import glow, icons, shapes, text as T
from ui.widgets.board import MARK_COLORS, MiniMark
from ui.widgets.button import Widget


class Panel:
    """The card background: fill, border, and an optional accent glow behind it.

    Both variants are pre-rendered because a card swaps between them on hover or
    selection, and rebuilding a blurred glow mid-frame would be wasteful.
    """

    def __init__(self, size, radius, accent=None, css_glow=26, border_width=2,
                 hover_accent=None):
        self.size = size
        self.radius = radius
        self.idle = shapes.rounded_rect(size, radius, fill=(*theme.PANEL, theme.PANEL_ALPHA),
                                        border=theme.BORDER)
        self.accent = accent
        self.css_glow = css_glow

        if accent is not None:
            # the design darkens and warms the fill behind an active card
            self.active = shapes.rounded_rect(size, radius, fill=(58, 36, 10, 90),
                                              border=accent, border_width=border_width)
            self.halo = glow.rounded(size, radius, accent, css_glow, 0.35)

        # a difficulty card's selection is always gold, so hovering an unselected one has
        # to glow in its own colour or the two states read as the same thing
        self.hover_accent = hover_accent or accent
        self.hover_halo = (glow.rounded(size, radius, self.hover_accent, css_glow, 0.3)
                           if self.hover_accent else None)
        self.hover_face = (shapes.rounded_rect(size, radius,
                                               fill=(*theme.PANEL, theme.PANEL_ALPHA),
                                               border=(*self.hover_accent, 153))
                           if self.hover_accent else self.idle)

    def draw(self, surface, topleft, active=False, hovered=False):
        lift = -theme.HOVER_LIFT if hovered else 0
        pos = (topleft[0], topleft[1] + lift)

        if active and self.accent is not None:
            glow.draw_under(surface, self.halo, pos, self.css_glow)
            surface.blit(self.active, pos)
        elif hovered and self.hover_halo is not None:
            glow.draw_under(surface, self.hover_halo, pos, self.css_glow)
            surface.blit(self.hover_face, pos)
        else:
            surface.blit(self.idle, pos)
        return pos


def _icon_badge(surface, center, diameter, accent, icon, icon_size):
    """The round tinted circle every card leads with."""
    disc = shapes.pill((diameter, diameter), fill=(*accent, 31), border=(*accent, 102))
    surface.blit(disc, disc.get_rect(center=center))
    icons.draw(surface, icon, icon_size, accent, center=center)


def _status_pill(surface, topleft, label, accent, clock, dot=True):
    """A small capsule with a pulsing dot — 'CHILL', 'NEVER LOSES'."""
    font = T.body(11, 700)
    text = T.tracked(label, font, accent, 0.12)
    pad_x, dot_d, gap = 12, 7, 8
    width = pad_x * 2 + text.get_width() + (dot_d + gap if dot else 0)
    height = 27

    face = shapes.pill((width, height), fill=(*accent, 26), border=(*accent, 115))
    surface.blit(face, topleft)

    x = topleft[0] + pad_x
    cy = topleft[1] + height // 2
    if dot:
        disc = shapes.dot(dot_d, accent)
        surface.blit(shapes.with_alpha(disc, round(255 * anim.pulse(clock, theme.PULSE_DOT))),
                     disc.get_rect(center=(x + dot_d // 2, cy)))
        x += dot_d + gap
    surface.blit(text, text.get_rect(midleft=(x, cy)))
    return pygame.Rect(topleft, (width, height))


class ModeCard(Widget):
    """Main menu: PLAYER VS PLAYER, PLAYER VS AGENT & AGENT VS AGENT"""

    HEIGHT = 236

    def __init__(self, topleft, title, blurb, icon, accent, on_click=None):
        super().__init__((topleft[0], topleft[1], theme.MODE_CARD_W, self.HEIGHT), on_click)
        self.title, self.blurb, self.icon, self.accent = title, blurb, icon, accent
        self.panel = Panel(self.rect.size, theme.RADIUS_LG, accent, css_glow=26, border_width=1)

    def draw(self, surface, clock=0.0):
        x, y = self.panel.draw(surface, self.rect.topleft, hovered=self.hovered)
        pad = 26
        inner = self.rect.width - pad * 2

        _icon_badge(surface, (x + pad + 29, y + pad + 29), 58, self.accent, self.icon, 28)

        cursor = y + pad + 58 + 12
        surface.blit(T.label(self.title, T.display(23), theme.TEXT), (x + pad, cursor))
        cursor += 34

        cursor += T.draw_wrapped(surface, self.blurb, T.body(15), theme.TEXT_MUTED,
                                 (x + pad, cursor), inner) + 8

        play = T.tracked('PLAY', T.body(15, 700), self.accent, 0.12)
        surface.blit(play, (x + pad, cursor))
        icons.draw(surface, 'arrow-right', 18, self.accent,
                   midleft=(x + pad + play.get_width() + 8, cursor + play.get_height() // 2))


class DifficultyCard(Widget):
    """Agent difficulty: EASY / MEDIUM / IMPOSSIBLE, one of which is selected."""

    HEIGHT = 240

    def __init__(self, topleft, title, blurb, icon, accent, tag, on_click=None):
        super().__init__((topleft[0], topleft[1], theme.DIFFICULTY_CARD_W, self.HEIGHT),
                         on_click)
        self.title, self.blurb, self.icon = title, blurb, icon
        self.accent, self.tag = accent, tag
        self.selected = False
        # selection is always gold, whatever the difficulty's own accent is; hover uses
        # the card's colour so the two states stay distinguishable
        self.panel = Panel(self.rect.size, theme.RADIUS_MD, theme.GOLD, css_glow=26,
                           hover_accent=accent)

    def draw(self, surface, clock=0.0):
        x, y = self.panel.draw(surface, self.rect.topleft,
                               active=self.selected, hovered=self.hovered and not self.selected)
        pad = 24
        inner = self.rect.width - pad * 2

        _icon_badge(surface, (x + pad + 28, y + pad + 28), 56, self.accent, self.icon, 28)

        cursor = y + pad + 56 + 12
        surface.blit(T.label(self.title, T.display(24), theme.TEXT), (x + pad, cursor))
        cursor += 36

        body_color = theme.TEXT_SOFT if self.selected else theme.TEXT_MUTED
        T.draw_wrapped(surface, self.blurb, T.body(14), body_color, (x + pad, cursor), inner)
        cursor += 54

        _status_pill(surface, (x + pad, cursor), self.tag, self.accent, clock)

        if self.selected:
            icons.draw(surface, 'check-circle', 26, theme.GOLD,
                       center=(x + self.rect.width - 14 - 13, y + 14 + 13), fill=True)


class PlayerCard:
    """The scoreboard beside the board. Highlights whoever is to move."""

    HEIGHT = 224

    def __init__(self, topleft, mark):
        self.rect = pygame.Rect(topleft[0], topleft[1], theme.PLAYER_CARD_W, self.HEIGHT)
        self.mark = mark
        accent = MARK_COLORS[mark]
        self.accent = accent
        self.panel = Panel(self.rect.size, theme.RADIUS_MD, accent, css_glow=26)
        self.glyph = MiniMark.surface(mark, 36)
        self.halo = MiniMark.halo(mark, 36, 10)

    def draw(self, surface, name, wins, active, label):
        # the panel goes straight onto the screen so its glow isn't clipped, but the
        # contents go through a layer we can fade as a whole — the design drops the
        # waiting player's card back to 70%
        x, y = self.panel.draw(surface, self.rect.topleft, active=active)
        layer = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        cx = self.rect.width // 2
        cursor = 22

        if active:
            layer.blit(self.halo, self.halo.get_rect(center=(cx, cursor + 18)))
        layer.blit(self.glyph, self.glyph.get_rect(center=(cx, cursor + 18)))
        cursor += 46

        T.draw(layer, T.label(name, T.body(19, 700), theme.TEXT), midtop=(cx, cursor))
        cursor += 32

        # status chip: filled in the player's colour when it's their turn
        chip_font = T.body(11, 700)
        chip_text = T.tracked(label, chip_font, theme.INK if active else theme.TEXT_MUTED, 0.1)
        chip = shapes.pill((chip_text.get_width() + 24, 25),
                           fill=self.accent if active else theme.BORDER)
        chip_rect = chip.get_rect(midtop=(cx, cursor))
        layer.blit(chip, chip_rect)
        layer.blit(chip_text, chip_text.get_rect(center=chip_rect.center))
        cursor += 25 + 16

        T.draw(layer, T.tracked('WINS', T.body(11, 600), theme.TEXT_MUTED, 0.2),
               midtop=(cx, cursor))
        cursor += 22

        score = T.label(str(wins), T.display(42), theme.GOLD)
        if active:
            halo = glow.text(str(wins), T.display(42), theme.GOLD, 16, 0.5)
            pad = glow.glow_offset(16)
            rect = score.get_rect(midtop=(cx, cursor))
            layer.blit(halo, (rect.x - pad, rect.y - pad))
        T.draw(layer, score, midtop=(cx, cursor))

        surface.blit(layer if active else shapes.with_alpha(layer, 179), (x, y))


class NameCard:
    """Name entry: a header row, a NAME label, and the text field itself."""

    HEIGHT = 168

    def __init__(self, topleft, mark, heading, field):
        self.rect = pygame.Rect(topleft[0], topleft[1], theme.NAME_CARD_W, self.HEIGHT)
        self.mark = mark
        self.heading = heading
        self.field = field
        self.accent = MARK_COLORS[mark]
        self.panel = Panel(self.rect.size, theme.RADIUS_MD)
        self.glyph = MiniMark.surface(mark, 26)
        self.halo = MiniMark.halo(mark, 26, 8)

    def draw(self, surface, clock=0.0):
        x, y = self.panel.draw(surface, self.rect.topleft)
        pad = 24
        row_y = y + pad + 13

        surface.blit(self.halo, self.halo.get_rect(center=(x + pad + 13, row_y)))
        surface.blit(self.glyph, self.glyph.get_rect(center=(x + pad + 13, row_y)))

        T.draw(surface, T.label(self.heading, T.body(17, 600), theme.TEXT),
               midleft=(x + pad + 38, row_y))

        # 'PLAYS X' / 'PLAYS O', pinned to the right edge of the row
        badge_text = T.tracked(f'PLAYS {self.mark}', T.body(11, 700),
                               theme.GOLD if self.mark == 'X' else theme.O_CYAN, 0.1)
        badge = shapes.rounded_rect((badge_text.get_width() + 20, 24), 8,
                                    fill=(*self.accent, 33), border=(*self.accent, 128))
        badge_rect = badge.get_rect(midright=(x + self.rect.width - pad, row_y))
        surface.blit(badge, badge_rect)
        surface.blit(badge_text, badge_text.get_rect(center=badge_rect.center))

        T.draw(surface, T.tracked('NAME', T.body(13, 500), theme.TEXT_MUTED, 0.08),
               midleft=(x + pad, row_y + 40))

        self.field.rect.topleft = (x + pad, row_y + 56)
        self.field.draw(surface)
