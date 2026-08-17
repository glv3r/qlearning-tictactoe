## Screens 04, 05 and 06 — the board in play, plus the pause and result dialogs that sit
## on top of it.
##
## The overlays live here rather than in their own modules because they're not separate
## destinations: they're states of a match that's still on screen underneath, and both need
## to reach into the same MatchController.

import random

import pygame

from ui import anim, theme
from ui.match import Phase
from ui.render import backdrop, glow, gradients, icons, shapes, text as T
from ui.screens.base import Overlay, Screen
from ui.widgets.board import BoardView, MiniMark
from ui.widgets.button import GradientButton, IconButton, OutlineButton, TextButton
from ui.widgets.card import PlayerCard
from ui.widgets.dialog import Dialog

BANNER_CY = 56
BOARD_TOP = 108
FOOTER_Y = 565
RESULT_DELAY = 0.55         # let the win line finish sweeping before the dialog covers it
DRAW_DELAY = 0.35           # a draw has no line to sweep, so it needs less of a beat

LINE_NAMES = {
    (0, 1, 2): 'Three in a row across the top',
    (3, 4, 5): 'Three in a row across the middle',
    (6, 7, 8): 'Three in a row across the bottom',
    (0, 3, 6): 'Three in a row down the left',
    (1, 4, 7): 'Three in a row down the middle',
    (2, 5, 8): 'Three in a row down the right',
    (0, 4, 8): 'Three in a row on the diagonal',
    (2, 4, 6): 'Three in a row on the diagonal',
}


class GameScreen(Screen):
    def __init__(self, app, match):
        super().__init__(app)
        self.match = match
        self.clock = 0.0
        self.scenery = backdrop.game()

        board_x = (theme.WIDTH - theme.BOARD_SIZE) // 2
        self.board = BoardView((board_x, BOARD_TOP))
        self.match.on_move = self._on_move

        card_y = BOARD_TOP + (theme.BOARD_SIZE - PlayerCard.HEIGHT) // 2
        self.card_x = PlayerCard((board_x - theme.BOARD_ROW_GAP - theme.PLAYER_CARD_W,
                                  card_y), 'X')
        self.card_o = PlayerCard((board_x + theme.BOARD_SIZE + theme.BOARD_ROW_GAP,
                                  card_y), 'O')

        self.sound = IconButton((804, 42), self._sound_icon(), on_click=self._toggle_sound,
                                size=theme.ICON_BTN_GAME, icon_size=20)
        self.pause = IconButton((858, 42), 'pause', on_click=self._open_pause,
                                size=theme.ICON_BTN_GAME, color=theme.TEXT_SOFT, icon_size=20)

        self.hover: int | None = None
        self._result_wait = anim.Timer(RESULT_DELAY, running=False)
        self._result_started = False
        self._result_shown = False

    ## ---------- ACTIONS

    def _sound_icon(self):
        return 'speaker-high' if self.app.sound_on else 'speaker-slash'

    def _toggle_sound(self):
        self.app.sound_on = not self.app.sound_on
        self.sound.set_icon(self._sound_icon())

    def _on_move(self, index, mark):
        self.board.pop(index)

    def _open_pause(self):
        if self.match.in_play:
            self.app.push(PauseOverlay(self.app, self))

    def to_menu(self):
        from ui.screens.menu import MenuScreen
        self.app.reset_to(MenuScreen(self.app))

    def begin_round(self):
        """Start the next board after a result has been acknowledged."""
        if self.match.phase is Phase.MATCH_OVER:
            self.match.rematch()
        else:
            self.match.next_round()
        self._reset_round_visuals()

    def restart_round(self):
        self.match.restart_round()
        self._reset_round_visuals()

    def _reset_round_visuals(self):
        self.board.reset()
        self._result_wait = anim.Timer(RESULT_DELAY, running=False)
        self._result_started = False
        self._result_shown = False
        self.hover = None

    ## ---------- LOOP

    def on_enter(self):
        self.hover = None
        for w in (self.sound, self.pause):
            w.hovered = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._open_pause()
            return

        if event.type == pygame.MOUSEMOTION:
            self.hover = (self.board.cell_at(event.pos)
                          if self.match.phase is Phase.AWAITING_HUMAN else None)

        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.match.phase is Phase.AWAITING_HUMAN):
            cell = self.board.cell_at(event.pos)
            if cell is not None and self.match.play(cell):
                self.hover = None

        self.sound.handle_event(event)
        self.pause.handle_event(event)

    def update(self, dt):
        self.clock += dt
        self.board.update(dt)
        self.match.update(dt)

        if self.match.in_play:
            return

        # The round has ended. Strike the win line, hold long enough for the sweep to
        # play, and only then let the dialog cover the board.
        if not self._result_started:
            self._result_started = True
            self.board.strike(self.match.win_line)      # None on a draw, which clears it
            self._result_wait = anim.Timer(
                RESULT_DELAY if self.match.win_line else DRAW_DELAY)

        self._result_wait.update(dt)
        if self._result_wait.done and not self._result_shown:
            self._result_shown = True
            self.app.push(ResultOverlay(self.app, self))

    def draw(self, surface):
        surface.blit(self.scenery, (0, 0))
        self._draw_banner(surface)

        ghost_mark = self.match.mark if self.match.phase is Phase.AWAITING_HUMAN else 'X'
        self.board.draw(surface, self.match.board, self.hover, ghost_mark)

        turn = self.match.mark if self.match.in_play else None
        self.card_x.draw(surface, self.match.x.name, self.match.wins['X'],
                         turn == 'X', self._chip_label('X'))
        self.card_o.draw(surface, self.match.o.name, self.match.wins['O'],
                         turn == 'O', self._chip_label('O'))

        self.sound.draw(surface)
        self.pause.draw(surface)
        self._draw_footer(surface)

    def _chip_label(self, mark):
        if not self.match.in_play or self.match.mark != mark:
            return 'WAITING'
        slot = self.match.slot(mark)
        if slot.is_human:
            return 'YOUR TURN'
        return 'THINKING' if self.match.phase is Phase.AGENT_THINKING else 'ITS TURN'

    def _draw_banner(self, surface):
        mark = self.match.mark if self.match.in_play else 'X'
        stops = theme.PRIMARY if mark == 'X' else theme.ELECTRIC
        ink = theme.INK if mark == 'X' else theme.INK_DEEP

        name = self.match.slot(mark).name
        label = T.tracked(f"{name}'s Turn".upper(), T.display(26), ink, 0.05)

        glyph = MiniMark.surface(mark, 22)
        glyph = glow.tint(glyph, ink)       # the banner draws the mark in its own ink

        gap, pad_x, height = 14, 36, 52
        dot_d = 10
        width = pad_x * 2 + glyph.get_width() + gap + label.get_width() + gap + dot_d

        face = gradients.pill((width, height), stops)
        rect = face.get_rect(center=(theme.WIDTH // 2, BANNER_CY))
        halo = glow.rounded((width, height), height // 2,
                            theme.EMBER if mark == 'X' else theme.O_CYAN, 30, 0.5)
        surface.blit(halo, halo.get_rect(center=rect.center))
        surface.blit(face, rect)

        x = rect.x + pad_x
        surface.blit(glyph, glyph.get_rect(midleft=(x, rect.centery)))
        x += glyph.get_width() + gap
        surface.blit(label, label.get_rect(midleft=(x, rect.centery)))
        x += label.get_width() + gap

        dot = shapes.dot(dot_d, ink)
        surface.blit(shapes.with_alpha(dot, round(255 * anim.pulse(
            self.clock, theme.PULSE_TURN))), dot.get_rect(midleft=(x, rect.centery)))

    def _draw_footer(self, surface):
        font = T.body(15)
        parts = [f'ROUND {self.match.round_no}',
                 f'FIRST TO {self.match.wins_needed} WINS',
                 f'DRAWS {self.match.draws}']
        pieces = [T.label(p, font, theme.TEXT_DIM) for p in parts]
        sep = T.label('·', font, theme.BORDER)

        gap = 14
        width = sum(p.get_width() for p in pieces) + (sep.get_width() + gap * 2) * (len(pieces) - 1)
        x = (theme.WIDTH - width) // 2

        for i, piece in enumerate(pieces):
            surface.blit(piece, piece.get_rect(midleft=(x, FOOTER_Y)))
            x += piece.get_width()
            if i < len(pieces) - 1:
                x += gap
                surface.blit(sep, sep.get_rect(midleft=(x, FOOTER_Y)))
                x += sep.get_width() + gap


## ---------- OVERLAYS

class PauseOverlay(Overlay):
    """Screen 06. The board stays visible and locked underneath."""

    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.dialog = Dialog(theme.DIALOG_PAUSE_W, 400)

        cx = self.dialog.rect.centerx
        inner = theme.DIALOG_PAUSE_W - theme.DIALOG_PAD * 2
        y = self.dialog.rect.y + 236

        self.resume = GradientButton(pygame.Rect(cx - inner // 2, y, inner, 48), 'RESUME',
                                     on_click=self._resume, icon='play', icon_side='left',
                                     font_size=17, radius=10, css_glow=22, icon_size=18)
        self.restart = OutlineButton(pygame.Rect(cx - inner // 2, y + 58, inner, 48),
                                     'RESTART ROUND', on_click=self._restart,
                                     icon='arrow-counter-clockwise', font_size=17)
        self.quit = TextButton((cx, y + 132), 'Quit to Menu', on_click=self.game.to_menu,
                               icon='sign-out')
        self.widgets = [self.resume, self.restart, self.quit]

    def _resume(self):
        self.app.pop()

    def _restart(self):
        self.game.restart_round()
        self.app.pop()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        self.dialog.update(dt)

    def draw(self, surface):
        self.dialog.draw_contents = self._contents
        self.dialog.draw(surface)

    def _contents(self, surface, alpha):
        rect = self.dialog.rect
        icons.draw(surface, 'pause-circle', 58, theme.O_CYAN, center=(rect.centerx, rect.y + 66))
        T.draw(surface, T.label('GAME PAUSED', T.display(34), theme.TEXT),
               center=(rect.centerx, rect.y + 124))
        T.draw_wrapped(surface, 'The board is locked. Pick up where you left off.',
                       T.body(15), theme.TEXT_MUTED,
                       (rect.x + 46, rect.y + 152), rect.width - 92, center=True)
        for w in self.widgets:
            w.draw(surface)


class ResultOverlay(Overlay):
    """Screen 05. Shown after every round; the buttons change once the match is decided."""

    CONFETTI = 90

    def __init__(self, app, game):
        super().__init__(app)
        self.game = game
        self.match = game.match
        self.decided = self.match.phase is Phase.MATCH_OVER
        self.result = self.match.result

        self.dialog = Dialog(theme.DIALOG_WIN_W, 356, accent=theme.O_CYAN)

        rect = self.dialog.rect
        cx = rect.centerx
        y = rect.y + 264
        btn_w, btn_gap = 164, 12

        primary_label = 'REMATCH' if self.decided else 'NEXT ROUND'
        self.primary = GradientButton(
            pygame.Rect(cx - btn_w - btn_gap // 2, y, btn_w, 48), primary_label,
            on_click=self._advance, icon='arrows-clockwise', icon_side='left',
            font_size=16, radius=10, css_glow=22, icon_size=18)
        self.menu = OutlineButton(pygame.Rect(cx + btn_gap // 2, y, btn_w, 48), 'MAIN MENU',
                                  on_click=self.game.to_menu, icon='house', font_size=16)
        self.widgets = [self.primary, self.menu]

        self.confetti = self._make_confetti() if self.result != 'draw' else []
        self._title_cache = self._build_title()

    ## ---------- CONTENT

    def _build_title(self):
        if self.result == 'draw':
            label = "IT'S A DRAW!"
        else:
            label = f'{self.match.slot(self.result).name} Wins!'.upper()
        return gradients.text(label, T.display(40), tuple(theme.TITLE))

    def _subtitle(self):
        if self.result == 'draw':
            return 'Every square taken, nobody ahead'
        return LINE_NAMES.get(tuple(self.match.win_line), 'Three in a row')

    def _score_line(self):
        return (f"{self.match.x.name}  {self.match.wins['X']} · "
                f"{self.match.wins['O']}  {self.match.o.name}")

    def _make_confetti(self):
        rect = self.dialog.rect
        pieces = []
        for _ in range(self.CONFETTI):
            pieces.append(dict(
                x=random.uniform(rect.x, rect.right),
                y=random.uniform(rect.y - 40, rect.centery),
                vx=random.uniform(-70, 70),
                vy=random.uniform(-40, 90),
                spin=random.uniform(-6, 6),
                angle=random.uniform(0, 360),
                size=random.randint(5, 10),
                color=random.choice([theme.X_ORANGE, theme.O_CYAN, theme.GOLD]),
            ))
        return pieces

    ## ---------- LOOP

    def _advance(self):
        self.app.pop()
        self.game.begin_round()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._advance()
            return
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        self.dialog.update(dt)
        for p in self.confetti:
            p['vy'] += 180 * dt          # gravity
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['angle'] += p['spin']

    def draw(self, surface):
        self.dialog.draw_contents = self._contents
        self.dialog.draw_behind = self._draw_confetti
        self.dialog.draw(surface)

    def _contents(self, surface, alpha):
        rect = self.dialog.rect

        icon = 'trophy' if self.result != 'draw' else 'handshake'
        icons.draw(surface, icon, 62, theme.GOLD, center=(rect.centerx, rect.y + 68),
                   fill=self.result != 'draw')

        T.draw(surface, self._title_cache, center=(rect.centerx, rect.y + 136))
        T.draw(surface, T.label(self._subtitle(), T.body(15), theme.TEXT_SOFT),
               center=(rect.centerx, rect.y + 176))

        score = T.tracked(self._score_line(), T.display(19), theme.TEXT, 0.05)
        pill = shapes.pill((score.get_width() + 44, 42), fill=theme.INPUT_BG,
                           border=theme.BORDER)
        pill_rect = pill.get_rect(center=(rect.centerx, rect.y + 216))
        surface.blit(pill, pill_rect)
        surface.blit(score, score.get_rect(center=pill_rect.center))

        for w in self.widgets:
            w.draw(surface)

    def _draw_confetti(self, surface):
        for p in self.confetti:
            if p['y'] > theme.HEIGHT + 20:
                continue
            chip = pygame.Surface((p['size'], p['size'] // 2 + 1), pygame.SRCALPHA)
            chip.fill(p['color'])
            spun = pygame.transform.rotate(chip, p['angle'])
            surface.blit(spun, spun.get_rect(center=(p['x'], p['y'])))
