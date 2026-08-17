## Font loading and text rendering.
##
## Fonts are loaded once and cached by (family, size), and rendered labels are cached by
## (text, font, colour) — the UI redraws every frame at 60fps, so nothing here should be
## rebuilding a surface on a frame that didn't change.
##
## Surfaces handed back by these functions are shared cache entries. Blit them; never
## mutate them in place.

from functools import lru_cache

import pygame

from ui import theme


@lru_cache(maxsize=None)
def _load(name: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(theme.FONT_DIR / f'{name}.ttf', size)


def display(size: int) -> pygame.font.Font:
    """Righteous — the arcade display face. Titles, buttons, scores."""
    return _load(theme.DISPLAY, size)


def body(size: int, weight: int = 400) -> pygame.font.Font:
    """Rubik at one of the four vendored weights (400/500/600/700)."""
    return _load(theme.BODY[weight], size)


def icon_font(size: int, fill: bool = False) -> pygame.font.Font:
    """Phosphor. Render a codepoint from ui.render.icons through this."""
    return _load(theme.ICON_FILL if fill else theme.ICON, size)


@lru_cache(maxsize=1024)
def label(text: str, font: pygame.font.Font, color: tuple) -> pygame.Surface:
    """A single run of text, antialiased."""
    return font.render(text, True, color)


@lru_cache(maxsize=512)
def tracked(text: str, font: pygame.font.Font, color: tuple, em: float) -> pygame.Surface:
    """Text with letter-spacing, which pygame has no native support for.

    `em` is the CSS value: .25em on a 13px font means each glyph gets 3.25px of extra
    advance after it. The design leans on this heavily for its uppercase pill labels, so
    without it those read noticeably tighter than the mockup.
    """
    if not text:
        return pygame.Surface((0, 0), pygame.SRCALPHA)

    extra = em * font.get_height()
    glyphs = [font.render(ch, True, color) for ch in text]
    advances = [font.size(ch)[0] for ch in text]

    # the trailing glyph gets no extra advance, otherwise the run looks off-centre
    width = sum(advances) + extra * (len(text) - 1)
    out = pygame.Surface((round(width), font.get_height()), pygame.SRCALPHA)

    x = 0.0
    for glyph, advance in zip(glyphs, advances):
        out.blit(glyph, (round(x), 0))
        x += advance + extra

    return out


@lru_cache(maxsize=256)
def wrap(string: str, font: pygame.font.Font, max_width: int) -> tuple[str, ...]:
    """Greedy word wrap — the card descriptions run to two or three lines."""
    lines, current = [], ''
    for word in string.split():
        candidate = f'{current} {word}'.strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return tuple(lines)


def draw_wrapped(surface: pygame.Surface, string: str, font: pygame.font.Font, color: tuple,
                 topleft: tuple, max_width: int, line_height: int | None = None,
                 center: bool = False) -> int:
    """Draw wrapped text from `topleft`, returning the height it consumed."""
    step = line_height or font.get_height() + 4
    lines = wrap(string, font, max_width)
    for i, line in enumerate(lines):
        run = label(line, font, color)
        x = topleft[0] + (max_width - run.get_width()) // 2 if center else topleft[0]
        surface.blit(run, (x, topleft[1] + i * step))
    return len(lines) * step


def draw(surface: pygame.Surface, text_surface: pygame.Surface, center=None, topleft=None,
         midleft=None, midtop=None) -> pygame.Rect:
    """Blit a rendered run by whichever anchor is convenient, and return where it landed."""
    rect = text_surface.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    elif midleft is not None:
        rect.midleft = midleft
    elif midtop is not None:
        rect.midtop = midtop
    surface.blit(text_surface, rect)
    return rect
