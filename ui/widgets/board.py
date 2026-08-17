## The 3x3 board: the grid, the marks on it, the ghost preview under the cursor, and the
## gold line that strikes through a win.
##
## This is a pure view. It never decides anything about the game — it's handed a board
## tuple to draw and reports which cell a click landed in.

import math

import pygame

from ui import anim, theme
from ui.render import glow, shapes

MARK_COLORS = {'X': theme.X_ORANGE, 'O': theme.O_CYAN}
MARK_GLOW = 12
GHOST_ALPHA = 77        # the design's 30% hover preview


def mark_surface(kind: str) -> pygame.Surface:
    thickness = theme.MARK_X_BAR if kind == 'X' else theme.MARK_O_RING
    return shapes.mark(kind, theme.MARK_SIZE, MARK_COLORS[kind], thickness)


def mark_glow(kind: str) -> pygame.Surface:
    thickness = theme.MARK_X_BAR if kind == 'X' else theme.MARK_O_RING
    return glow.mark(kind, theme.MARK_SIZE, MARK_COLORS[kind], thickness, MARK_GLOW, 0.6)


class BoardView:
    def __init__(self, topleft):
        self.rect = pygame.Rect(topleft[0], topleft[1], theme.BOARD_SIZE, theme.BOARD_SIZE)

        self._frame = shapes.rounded_rect(self.rect.size, theme.BOARD_RADIUS,
                                          fill=(13, 6, 32, 153), border=theme.BORDER)
        self._cell = shapes.rounded_rect((theme.CELL_SIZE, theme.CELL_SIZE),
                                         theme.CELL_RADIUS, fill=theme.CELL,
                                         border=theme.CELL_BORDER)
        # the hovered cell picks up a faint orange wash and a solid orange edge
        self._cell_hover = shapes.rounded_rect(
            (theme.CELL_SIZE, theme.CELL_SIZE), theme.CELL_RADIUS,
            fill=(*theme.X_ORANGE, 20), border=(*theme.X_ORANGE, 153))

        # per-cell entrance animations, keyed by index
        self._pops: dict[int, anim.Timer] = {}
        self._sweep = anim.Timer(theme.WIN_SWEEP, running=False)
        self._sweep.finish()
        self.win_line: tuple | None = None

    ## ---------- GEOMETRY

    def cell_rect(self, index: int) -> pygame.Rect:
        row, col = divmod(index, 3)
        step = theme.CELL_SIZE + theme.BOARD_GAP
        return pygame.Rect(self.rect.x + theme.BOARD_PAD + col * step,
                           self.rect.y + theme.BOARD_PAD + row * step,
                           theme.CELL_SIZE, theme.CELL_SIZE)

    def cell_at(self, pos) -> int | None:
        for i in range(9):
            if self.cell_rect(i).collidepoint(pos):
                return i
        return None

    ## ---------- ANIMATION HOOKS

    def pop(self, index: int) -> None:
        """Start the stamp-in animation for a mark that just landed."""
        self._pops[index] = anim.Timer(theme.MARK_POP)

    def strike(self, line: tuple | None) -> None:
        """Begin sweeping the win line across `line`, or clear it when passed None."""
        self.win_line = line
        if line is None:
            self._sweep.finish()
        else:
            self._sweep.reset()

    def reset(self) -> None:
        self._pops.clear()
        self.strike(None)

    def update(self, dt: float) -> None:
        for timer in self._pops.values():
            timer.update(dt)
        self._sweep.update(dt)

    ## ---------- DRAWING

    def draw(self, surface, board, hover: int | None = None, hover_mark: str = 'X') -> None:
        surface.blit(self._frame, self.rect)

        for i in range(9):
            rect = self.cell_rect(i)
            filled = board[i] != ''
            is_hover = hover == i and not filled

            surface.blit(self._cell_hover if is_hover else self._cell, rect)

            if filled:
                self._draw_mark(surface, board[i], rect, self._pops.get(i))
            elif is_hover:
                ghost = shapes.with_alpha(mark_surface(hover_mark), GHOST_ALPHA)
                surface.blit(ghost, ghost.get_rect(center=rect.center))

        if self.win_line is not None:
            self._draw_win_line(surface)

    def _draw_mark(self, surface, kind, rect, timer) -> None:
        face = mark_surface(kind)
        halo = mark_glow(kind)

        scale = anim.pop_scale(timer.progress) if timer is not None else 1.0
        if scale >= 0.999:
            surface.blit(halo, halo.get_rect(center=rect.center))
            surface.blit(face, face.get_rect(center=rect.center))
            return

        if scale <= 0.01:
            return

        # while it's growing, the glow flashes brighter than it will settle at
        grown, _ = anim.scaled(face, scale)
        flash, _ = anim.scaled(halo, scale)
        surface.blit(flash, flash.get_rect(center=rect.center))
        surface.blit(grown, grown.get_rect(center=rect.center))

    def _draw_win_line(self, surface) -> None:
        first = self.cell_rect(self.win_line[0]).center
        last = self.cell_rect(self.win_line[-1]).center

        # overhang the end cells a little, the way the design's line runs past the marks
        dx, dy = last[0] - first[0], last[1] - first[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        over = theme.CELL_SIZE * 0.34

        start = (first[0] - ux * over, first[1] - uy * over)
        full = length + over * 2

        # sweep: the line draws itself from the first cell towards the last
        travelled = full * anim.ease_out_cubic(self._sweep.progress)
        end = (start[0] + ux * travelled, start[1] + uy * travelled)

        thickness = 20
        pad = 40
        layer = pygame.Surface((self.rect.width + pad * 2, self.rect.height + pad * 2),
                               pygame.SRCALPHA)
        offset = (self.rect.x - pad, self.rect.y - pad)
        local = lambda p: (p[0] - offset[0], p[1] - offset[1])

        pygame.draw.line(layer, theme.GOLD, local(start), local(end), thickness)
        pygame.draw.circle(layer, theme.GOLD, local(start), thickness / 2)
        pygame.draw.circle(layer, theme.GOLD, local(end), thickness / 2)

        halo = glow.from_surface(layer, theme.GOLD, 34, 0.8)
        gpad = glow.glow_offset(34)
        surface.blit(halo, (offset[0] - gpad, offset[1] - gpad))
        surface.blit(layer, offset)


class MiniMark:
    """The small X and O glyphs the design puts on player cards and name fields, at the
    handful of sizes it uses them at."""

    @staticmethod
    def surface(kind: str, size: int, glow_px: int = 0) -> pygame.Surface:
        # the design keeps the bar/ring roughly a quarter of the box at every size
        thickness = max(4, round(size * (16 / 66) if kind == 'X' else size * (15 / 66)))
        return shapes.mark(kind, size, MARK_COLORS[kind], thickness)

    @staticmethod
    def halo(kind: str, size: int, css_blur: int, alpha: float = 0.7) -> pygame.Surface:
        thickness = max(4, round(size * (16 / 66) if kind == 'X' else size * (15 / 66)))
        return glow.mark(kind, size, MARK_COLORS[kind], thickness, css_blur, alpha)
