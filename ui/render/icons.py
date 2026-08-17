## Phosphor icons, rendered as font glyphs.
##
## The codepoints below were extracted from @phosphor-icons/web@2.1.2's stylesheets — the
## same version the design references. `ph-robot` in the design is REGULAR['robot'] here;
## anything the design writes as `ph-fill ph-x` lives in FILL.
##
## They're written as \u escapes rather than literal characters on purpose: these live in
## the Unicode private use area and render as tofu in most editors and diffs, which makes
## a literal table impossible to proofread.

from functools import lru_cache

import pygame

from ui.render import text as text_render

REGULAR = {
    'robot': '',
    'users': '',
    'smiley': '',
    'target': '',
    'skull': '',
    'pause': '',
    'pause-circle': '',
    'play': '',
    'house': '',
    'arrow-right': '',
    'arrow-left': '',
    'arrows-clockwise': '',
    'arrow-counter-clockwise': '',
    'sign-out': '',
    'speaker-high': '',
    'speaker-slash': '',
    'handshake': '',
    'star': '',
}

FILL = {
    'trophy': '',
    'check-circle': '',
    # the design writes the ARCADE EDITION flourish as a literal ★, but Rubik has no
    # U+2605 glyph and renders it as tofu. Phosphor's filled star stands in.
    'star': '',
}


@lru_cache(maxsize=256)
def render(name: str, size: int, color: tuple, fill: bool = False) -> pygame.Surface:
    """One icon at one size and colour. Cached — call it freely from a draw loop."""
    table = FILL if fill else REGULAR
    if name not in table:
        raise KeyError(f'unknown Phosphor icon {name!r} '
                       f'({"fill" if fill else "regular"} set)')
    return text_render.label(table[name], text_render.icon_font(size, fill), color)


def draw(surface: pygame.Surface, name: str, size: int, color: tuple,
         center=None, topleft=None, midleft=None, fill: bool = False) -> pygame.Rect:
    """Render and place an icon in one call."""
    return text_render.draw(surface, render(name, size, color, fill),
                            center=center, topleft=topleft, midleft=midleft)
