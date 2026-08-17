## Neon glow — the single effect the whole design leans on. In CSS it's `box-shadow`,
## `drop-shadow` and `text-shadow`; here it's a tinted silhouette of the shape, gaussian
## blurred, blitted underneath the real thing.
##
## Glows are expensive to build and never change, so everything is cached. Build them at
## screen construction, not in the draw loop.

from functools import lru_cache

import pygame

from ui.render import shapes


def _css_to_radius(css_px: int) -> int:
    """CSS blur length -> pygame kernel radius. A CSS blur of N spreads about N/2 either
    side of the edge, which is what the kernel radius means here."""
    return max(1, round(css_px / 2))


def tint(surface: pygame.Surface, color: tuple) -> pygame.Surface:
    """Recolour a shape to a flat colour, keeping its alpha exactly.

    Two passes, because there's no single blend that does this: BLEND_RGB_MAX with white
    flattens the colour channels while leaving alpha alone, then BLEND_RGBA_MULT stamps
    the target colour in. Doing it in one multiply would tint by whatever colour the
    source already was.
    """
    out = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    out.blit(surface, (0, 0))
    out.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
    out.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def from_surface(surface: pygame.Surface, color: tuple, css_blur: int,
                 alpha: float = 1.0) -> pygame.Surface:
    """Glow shaped like `surface`, returned on its own padded canvas.

    The result is larger than the input by `pad` on every side — blit it at
    `(x - pad, y - pad)` to line it up with the shape it belongs to. Use `glow_offset`
    to get that padding.
    """
    radius = _css_to_radius(css_blur)
    pad = radius * 3
    w, h = surface.get_size()

    canvas = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    canvas.blit(tint(surface, color), (pad, pad))
    canvas = pygame.transform.gaussian_blur(canvas, radius)

    if alpha < 1.0:
        canvas.fill((255, 255, 255, round(255 * alpha)), special_flags=pygame.BLEND_RGBA_MULT)
    return canvas


def glow_offset(css_blur: int) -> int:
    """How far a `from_surface` glow overhangs its shape, on each side."""
    return _css_to_radius(css_blur) * 3


@lru_cache(maxsize=256)
def rounded(size: tuple[int, int], radius: int, color: tuple, css_blur: int,
            alpha: float = 1.0, spread: int = 0) -> pygame.Surface:
    """`box-shadow: 0 0 <css_blur>px <spread>px <color>` around a rounded rect."""
    w, h = size
    grown = (w + spread * 2, h + spread * 2)
    shape = shapes.rounded_rect(grown, radius + spread, fill=(*color, 255))
    return from_surface(shape, color, css_blur, alpha)


@lru_cache(maxsize=128)
def circle(diameter: int, color: tuple, css_blur: int, alpha: float = 1.0) -> pygame.Surface:
    """Glow around a filled circle — the retro sun, the pulsing status dots."""
    return from_surface(shapes.dot(diameter, (*color, 255)), color, css_blur, alpha)


@lru_cache(maxsize=256)
def mark(kind: str, size: int, color: tuple, thickness: int, css_blur: int,
         alpha: float = 1.0) -> pygame.Surface:
    """`drop-shadow` around an X or an O."""
    return from_surface(shapes.mark(kind, size, color, thickness), color, css_blur, alpha)


@lru_cache(maxsize=256)
def text(string: str, font: pygame.font.Font, color: tuple, css_blur: int,
         alpha: float = 1.0) -> pygame.Surface:
    """`text-shadow` behind a headline."""
    return from_surface(font.render(string, True, (255, 255, 255)), color, css_blur, alpha)


def draw_under(surface: pygame.Surface, glow_surface: pygame.Surface,
               shape_topleft: tuple[int, int], css_blur: int) -> None:
    """Blit a `from_surface` glow so it sits centred behind its shape."""
    pad = glow_offset(css_blur)
    surface.blit(glow_surface, (shape_topleft[0] - pad, shape_topleft[1] - pad))
