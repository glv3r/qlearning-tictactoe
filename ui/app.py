## The window, the clock, and the screen stack.
##
## Screens are a stack rather than a single value so the pause and win dialogs can sit on
## top of a live game board without the board having to know about them — the app draws
## every screen from the bottom up, but only the top one receives events.

import pygame

from ui import theme


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(theme.CAPTION)
        self.surface = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self._stack: list = []

        # global preferences the screens share. The design puts a speaker toggle on both
        # the menu and the board, and they're the same switch.
        self.sound_on = True

    ## ---------- SCREEN STACK

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def push(self, screen) -> None:
        """Put a screen on top. Used for overlays and for forward navigation."""
        self._stack.append(screen)
        screen.on_enter()

    def pop(self) -> None:
        """Drop the top screen and hand control back to the one beneath."""
        if len(self._stack) > 1:
            self._stack.pop()
            self.current.on_enter()

    def replace(self, screen) -> None:
        """Swap the top screen out — forward navigation that shouldn't be re-enterable."""
        if self._stack:
            self._stack.pop()
        self.push(screen)

    def reset_to(self, screen) -> None:
        """Clear the stack entirely. Quitting a match back to the main menu."""
        self._stack.clear()
        self.push(screen)

    def quit(self) -> None:
        self.running = False

    ## ---------- MAIN LOOP

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(theme.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current is not None:
                    self.current.handle_event(event)

            if self.current is not None:
                self.current.update(dt)
            self._draw()

            pygame.display.flip()

        pygame.quit()

    def _draw(self) -> None:
        # find the lowest screen that paints every pixel, and draw up from there
        start = 0
        for i in range(len(self._stack) - 1, -1, -1):
            if not getattr(self._stack[i], 'transparent', False):
                start = i
                break

        for screen in self._stack[start:]:
            screen.draw(self.surface)
