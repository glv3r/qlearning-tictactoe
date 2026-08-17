## The primitive shapes the design is built out of: rounded panels, the X, the O, pills.
##
## pygame's draw functions don't antialias, and this design is full of large rounded
## corners and 45-degree bars where hard edges would show badly. So everything here is
## drawn at 4x into an oversized surface and then smoothscaled down — cheap supersampling
## that gives us clean edges for free.
##
## All of it is cached: shapes are drawn once per (size, colour, thickness) and reused.

import math
from functools import lru_cache

import pygame

SS = 4      # supersample factor


def _capsule(surface, start, end, thickness, color):
    """A thick line with round caps — CSS `border-radius:999px` on a rotated bar."""
    pygame.draw.line(surface, color, start, end, round(thickness))
    r = thickness / 2
    pygame.draw.circle(surface, color, start, r)
    pygame.draw.circle(surface, color, end, r)


@lru_cache(maxsize=256)
def rounded_mask(size: tuple[int, int], radius: int) -> pygame.Surface:
    """An opaque white rounded rect on transparent — used to clip gradients to a shape."""
    w, h = size
    big = pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)
    pygame.draw.rect(big, (255, 255, 255, 255), (0, 0, w * SS, h * SS),
                     border_radius=radius * SS)
    return pygame.transform.smoothscale(big, size)


@lru_cache(maxsize=512)
def rounded_rect(size: tuple[int, int], radius: int, fill=None,
                 border=None, border_width: int = 1) -> pygame.Surface:
    """A panel: optional translucent fill, optional inset border. Either may be omitted."""
    w, h = size
    big = pygame.Surface((w * SS, h * SS), pygame.SRCALPHA)
    box = (0, 0, w * SS, h * SS)
    r = radius * SS

    if fill is not None:
        pygame.draw.rect(big, fill, box, border_radius=r)
    if border is not None:
        pygame.draw.rect(big, border, box, width=border_width * SS, border_radius=r)

    return pygame.transform.smoothscale(big, size)


@lru_cache(maxsize=128)
def x_mark(size: int, color: tuple, thickness: int) -> pygame.Surface:
    """Two round-capped bars crossing at ±45°, each spanning the full box like the CSS."""
    s = size * SS
    t = thickness * SS
    half = s / 2

    big = pygame.Surface((s, s), pygame.SRCALPHA)
    for degrees in (45, -45):
        rad = math.radians(degrees)
        dx, dy = math.cos(rad) * half, math.sin(rad) * half
        _capsule(big, (half - dx, half - dy), (half + dx, half + dy), t, color)

    return pygame.transform.smoothscale(big, (size, size))


@lru_cache(maxsize=128)
def o_mark(size: int, color: tuple, thickness: int) -> pygame.Surface:
    """A ring. `size` is the outer diameter and the ring grows inward, as border-box does."""
    s = size * SS
    big = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(big, color, (s / 2, s / 2), s / 2, width=thickness * SS)
    return pygame.transform.smoothscale(big, (size, size))


def mark(kind: str, size: int, color: tuple, thickness: int) -> pygame.Surface:
    """Dispatch on 'X' / 'O' so callers can stay agnostic about which player they're drawing."""
    return x_mark(size, color, thickness) if kind == 'X' else o_mark(size, color, thickness)


@lru_cache(maxsize=256)
def pill(size: tuple[int, int], fill=None, border=None, border_width: int = 1) -> pygame.Surface:
    """A fully-rounded capsule — badges, status chips, the turn banner."""
    return rounded_rect(size, min(size) // 2, fill, border, border_width)


@lru_cache(maxsize=128)
def dot(diameter: int, color: tuple) -> pygame.Surface:
    """A filled circle, antialiased — the pulsing status dots and the starfield."""
    d = diameter * SS
    big = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(big, color, (d / 2, d / 2), d / 2)
    return pygame.transform.smoothscale(big, (diameter, diameter))


def with_alpha(surface: pygame.Surface, alpha: int) -> pygame.Surface:
    """A copy of `surface` scaled to `alpha` (0-255). Copies, so cached shapes stay intact."""
    out = surface.copy()
    out.set_alpha(alpha)
    return out
