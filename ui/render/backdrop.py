## The synthwave scenery every screen sits on: gradient sky, scattered stars, a striped
## retro sun, and a grid receding to the horizon.
##
## None of it moves, so each screen's backdrop is composited once into a single surface at
## construction and then blitted as one operation per frame.
##
## The design builds its grid with `perspective(320px) rotateX(58deg)` on a flat CSS grid.
## We don't emulate that matrix — we just draw the perspective directly, which is both
## less code and easier to reason about: verticals fan out from a vanishing point, and
## horizontals bunch up as they approach it.

from dataclasses import dataclass

import pygame

from ui import theme
from ui.render import glow, gradients, shapes


@dataclass(frozen=True)
class Star:
    x: int
    y: int
    size: int
    color: tuple
    opacity: float


@dataclass(frozen=True)
class Sun:
    diameter: int = 260
    center: tuple = (theme.WIDTH // 2, 420)
    opacity: float = 0.55
    css_glow: int = 90
    stripe_gap: int = 12       # transparent run, per the repeating-linear-gradient
    stripe_height: int = 5     # the bar itself
    stripe_from: float = 0.45  # stripes start 45% down, covering the lower 55%


def _draw_stars(surface: pygame.Surface, stars) -> None:
    for star in stars:
        dot = shapes.dot(star.size, star.color)
        surface.blit(shapes.with_alpha(dot, round(255 * star.opacity)), (star.x, star.y))


def _draw_sun(surface: pygame.Surface, sun: Sun) -> None:
    d = sun.diameter
    disc = pygame.Surface((d, d), pygame.SRCALPHA)

    # a vertical gradient clipped to a circle
    disc.blit(shapes.dot(d, (255, 255, 255, 255)), (0, 0))
    disc.blit(gradients.vertical((d, d), theme.SUN).convert_alpha(), (0, 0),
              special_flags=pygame.BLEND_RGBA_MULT)

    # punch horizontal slots through the lower part, so the sky shows between the bars
    start = int(d * sun.stripe_from)
    period = sun.stripe_gap + sun.stripe_height
    for y in range(start + sun.stripe_gap, d, period):
        pygame.draw.rect(disc, (0, 0, 0, 0), (0, y, d, sun.stripe_height))

    disc = shapes.with_alpha(disc, round(255 * sun.opacity))
    rect = disc.get_rect(center=sun.center)

    halo = glow.circle(d, theme.EMBER, sun.css_glow, 0.45)
    surface.blit(halo, halo.get_rect(center=sun.center))
    surface.blit(disc, rect)


def _draw_grid(surface: pygame.Surface, height: int, alpha: float,
               spacing: int = 64, line_width: int = 2) -> None:
    """Verticals converging on a vanishing point, horizontals compressed towards it."""
    w = surface.get_width()
    top = surface.get_height() - height
    vp = (w / 2, top)
    color = (*theme.O_CYAN, round(255 * alpha))

    ss = 2      # supersample, so the fanned diagonals don't stair-step
    layer = pygame.Surface((w * ss, height * ss), pygame.SRCALPHA)
    lw = line_width * ss

    # verticals: evenly spaced where they meet the bottom edge, all aimed at the vanishing
    # point. They start well outside the frame so the fan reaches the screen corners.
    bottom_y = height * ss
    for i in range(-8, 9):
        x = (w / 2 + i * spacing * 3.0) * ss
        pygame.draw.line(layer, color, (vp[0] * ss, 0), (x, bottom_y), lw)

    # horizontals: a ground plane's row at depth d lands at y = height/d with the horizon
    # at y=0, so rows crowd towards the horizon and spread out towards the viewer. Stop
    # once consecutive rows are within a few pixels, where they'd just read as a smear.
    i = 1
    while True:
        y = height / i
        if y - height / (i + 1) < 8:
            break
        pygame.draw.line(layer, color, (0, y * ss), (w * ss, y * ss), lw)
        i += 1

    surface.blit(pygame.transform.smoothscale(layer, (w, height)), (0, top))


def _draw_horizon_line(surface: pygame.Surface, y: int) -> None:
    w = surface.get_width()
    halo = glow.rounded((w, 3), 2, theme.O_CYAN, 24, 0.55, spread=4)
    surface.blit(halo, halo.get_rect(center=(w // 2, y + 1)))
    strip = pygame.Surface((w, 3), pygame.SRCALPHA)
    strip.fill((*theme.O_CYAN, 128))
    surface.blit(strip, (0, y))


def build(stops=theme.SKY, stars=(), sun: Sun | None = None,
          grid_height: int = 0, grid_alpha: float = 0.16,
          horizon_line_y: int | None = None) -> pygame.Surface:
    """Composite one screen's scenery into a single opaque surface."""
    size = (theme.WIDTH, theme.HEIGHT)
    surface = gradients.vertical(size, stops).copy()

    _draw_stars(surface, stars)
    if sun is not None:
        _draw_sun(surface, sun)
    if grid_height:
        _draw_grid(surface, grid_height, grid_alpha)
    if horizon_line_y is not None:
        _draw_horizon_line(surface, horizon_line_y)

    return surface


## ---------- PER-SCREEN SCENERY
## Star positions are taken straight from the design. Where it anchors a star with
## `right: N`, the x here is 900 - N - size.

MENU_STARS = (
    Star(120, 44, 3, theme.TEXT, 0.8),
    Star(310, 92, 2, theme.O_CYAN, 0.7),
    Star(697, 60, 3, theme.GOLD, 0.8),
    Star(808, 150, 2, theme.TEXT, 0.5),
    Star(70, 170, 2, theme.TEXT, 0.6),
    Star(470, 30, 2, theme.X_ORANGE, 0.7),
)

NAME_STARS = (
    Star(150, 60, 2, theme.TEXT, 0.7),
    Star(717, 110, 3, theme.O_CYAN, 0.7),
    Star(548, 40, 2, theme.GOLD, 0.6),
)

DIFFICULTY_STARS = (
    Star(200, 70, 2, theme.TEXT, 0.7),
    Star(747, 120, 3, theme.X_ORANGE, 0.7),
    Star(478, 45, 2, theme.O_CYAN, 0.6),
)

GAME_STARS = (
    Star(100, 50, 2, theme.TEXT, 0.6),
    Star(778, 100, 2, theme.O_CYAN, 0.6),
)


def menu() -> pygame.Surface:
    return build(theme.SKY, MENU_STARS, Sun(), grid_height=230, grid_alpha=0.22,
                 horizon_line_y=475)


def name_entry() -> pygame.Surface:
    return build(theme.SKY_LOW, NAME_STARS, grid_height=170, grid_alpha=0.16)


def difficulty() -> pygame.Surface:
    return build(theme.SKY_LOW, DIFFICULTY_STARS, grid_height=170, grid_alpha=0.16)


def game() -> pygame.Surface:
    return build(theme.SKY_LOW, GAME_STARS, grid_height=130, grid_alpha=0.12)
