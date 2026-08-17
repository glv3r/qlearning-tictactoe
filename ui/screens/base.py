## The contract every screen implements, and the overlay variant used for the pause and
## win dialogs.

from abc import ABC, abstractmethod

import pygame


class Screen(ABC):
    """One full-window view. The app keeps a stack of these and drives the top one."""

    def __init__(self, app):
        self.app = app

    def on_enter(self) -> None:
        """Called each time this screen becomes the active one, including on the way back
        from a screen pushed on top of it."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """One SDL event. Only the top of the stack receives these."""

    def update(self, dt: float) -> None:
        """Advance animations. `dt` is seconds since the last frame."""

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Paint the whole window. Screens are expected to cover every pixel."""


class Overlay(Screen):
    """A screen drawn on top of the one below it — the pause and game-over dialogs.

    The app still draws the screen underneath first, so overlays paint only their backdrop
    wash and their dialog.
    """

    transparent = True
