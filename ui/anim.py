## Easing curves, one-shot timers, and the looping oscillations the design's CSS
## animations describe.
##
## Screens keep a running clock in seconds and feed it to `step_blink` / `pulse` for
## anything that loops forever, and use a `Timer` for anything that plays once.

import math


def clamp01(t: float) -> float:
    return 0.0 if t < 0.0 else 1.0 if t > 1.0 else t


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


## ---------- EASING

def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - clamp01(t)) ** 3


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    """Overshoots past 1 and settles back — dialogs popping in."""
    t = clamp01(t) - 1.0
    return t * t * ((overshoot + 1.0) * t + overshoot) + 1.0


def pop_scale(t: float) -> float:
    """The design's mark entrance: scale 0 -> 1.1 -> 1.

    Grows past full size in the first 70% of the animation, then eases back down. Reads as
    a mark being stamped onto the board rather than fading in.
    """
    t = clamp01(t)
    if t < 0.7:
        return 1.1 * ease_out_cubic(t / 0.7)
    return lerp(1.1, 1.0, ease_out_cubic((t - 0.7) / 0.3))


## ---------- LOOPS

def step_blink(clock: float, period: float, on: float = 1.0, off: float = 0.2) -> float:
    """CSS `step-end` blink — hard on for half the period, hard off for the other half.
    PRESS START and the text caret both use this."""
    return on if (clock % period) < period / 2 else off


def pulse(clock: float, period: float, lo: float = 0.25, hi: float = 1.0) -> float:
    """A smooth oscillation between two values — the status dots' `pulseDot`."""
    phase = (clock % period) / period
    return lerp(lo, hi, (math.cos(2 * math.pi * phase) + 1.0) / 2.0)


## ---------- ONE-SHOTS

class Timer:
    """Runs once from 0 to `duration`, then stays finished until reset."""

    def __init__(self, duration: float, running: bool = True):
        self.duration = duration
        self.elapsed = duration if not running else 0.0

    def update(self, dt: float) -> None:
        if self.elapsed < self.duration:
            self.elapsed = min(self.elapsed + dt, self.duration)

    def reset(self) -> None:
        self.elapsed = 0.0

    def finish(self) -> None:
        self.elapsed = self.duration

    @property
    def progress(self) -> float:
        return 1.0 if self.duration <= 0 else clamp01(self.elapsed / self.duration)

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration


def scaled(surface, scale: float):
    """A copy of `surface` scaled about its own centre. Returns (surface, offset) where
    offset shifts the blit so the centre stays put."""
    import pygame
    w, h = surface.get_size()
    sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
    out = pygame.transform.smoothscale(surface, (sw, sh))
    return out, ((w - sw) // 2, (h - sh) // 2)
