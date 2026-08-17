## Linear gradients, which the design uses for the sky, the retro sun, every primary
## button and the big title text.
##
## The trick throughout is to build a 1px-wide (or 1px-tall) ramp and let
## `pygame.transform.scale` stretch it across the other axis — that's an exact pixel
## repeat, so it's both faster and sharper than filling row by row.
##
## Stops are `[(position 0..1, colour), ...]` and must be sorted. See ui.theme.

from functools import lru_cache

import pygame

from ui.render import shapes


def _ramp(n: int, stops: tuple) -> list[tuple[int, int, int]]:
    """Sample `n` colours along the stop list."""
    if n <= 1:
        return [stops[0][1]]

    out = []
    for i in range(n):
        t = i / (n - 1)

        # find the pair of stops this sample falls between
        lo = stops[0]
        hi = stops[-1]
        for a, b in zip(stops, stops[1:]):
            if a[0] <= t <= b[0]:
                lo, hi = a, b
                break
        else:
            # outside the stop range entirely — clamp to whichever end we're past
            lo = hi = stops[0] if t < stops[0][0] else stops[-1]

        span = hi[0] - lo[0]
        f = 0.0 if span == 0 else (t - lo[0]) / span
        out.append(tuple(round(c1 + (c2 - c1) * f) for c1, c2 in zip(lo[1], hi[1])))

    return out


@lru_cache(maxsize=128)
def _vertical(w: int, h: int, stops: tuple) -> pygame.Surface:
    strip = pygame.Surface((1, h))
    for y, color in enumerate(_ramp(h, stops)):
        strip.set_at((0, y), color)
    return pygame.transform.scale(strip, (w, h))


@lru_cache(maxsize=128)
def _horizontal(w: int, h: int, stops: tuple) -> pygame.Surface:
    strip = pygame.Surface((w, 1))
    for x, color in enumerate(_ramp(w, stops)):
        strip.set_at((x, 0), color)
    return pygame.transform.scale(strip, (w, h))


def vertical(size: tuple[int, int], stops) -> pygame.Surface:
    """Top-to-bottom gradient, opaque. The sky, the sun, gradient text fills."""
    return _vertical(size[0], size[1], tuple(stops))


def horizontal(size: tuple[int, int], stops) -> pygame.Surface:
    """Left-to-right gradient, opaque. Primary buttons and the turn banner."""
    return _horizontal(size[0], size[1], tuple(stops))


@lru_cache(maxsize=256)
def text(string: str, font: pygame.font.Font, stops: tuple) -> pygame.Surface:
    """Gradient-filled text — the CSS `background-clip:text` on the title and win headline.

    Render the glyphs in white, then multiply a gradient over them. White multiplied by
    the gradient *is* the gradient, and the multiply carries the glyphs' antialiased alpha
    through untouched, so the letterforms act as their own mask.
    """
    glyphs = font.render(string, True, (255, 255, 255)).convert_alpha()
    fill = vertical(glyphs.get_size(), stops).convert_alpha()
    glyphs.blit(fill, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return glyphs


@lru_cache(maxsize=256)
def rounded(size: tuple[int, int], stops: tuple, radius: int,
            direction: str = 'horizontal') -> pygame.Surface:
    """A gradient clipped to a rounded rect — every primary button in the design."""
    build = horizontal if direction == 'horizontal' else vertical
    out = build(size, stops).convert_alpha()
    out.blit(shapes.rounded_mask(size, radius), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def pill(size: tuple[int, int], stops, direction: str = 'horizontal') -> pygame.Surface:
    """A gradient capsule — the turn banner and the START GAME button's rounder cousins."""
    return rounded(size, tuple(stops), min(size) // 2, direction)
