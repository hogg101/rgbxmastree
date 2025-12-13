from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def candles(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Candle-like warm flicker on the body (red/orange/yellow), star stays a steady gold.

    The only tempo control is the supplied `speed` knob from the web UI/controller.
    """
    # Star: constant warm gold (slightly subdued so it reads as "metallic")
    try:
        tree.star.color = (1.0, 0.84, 0.2)
    except Exception:
        # If star is not addressable for some reason, keep going.
        pass

    # speed is expected to be in a wide range (e.g. 0.1..200).
    s = max(0.001, float(speed))
    # Update cadence: very slow at low end (seconds), extremely fast at high end (milliseconds).
    delay = max(0.001, 1.0 / s)

    # Flicker state: low-pass filtered random target intensity.
    intensity = 0.6
    target = 0.6

    while not stop.is_set():
        # Occasionally pick a new random target; higher speeds change target more often.
        if random.random() < _clamp01(0.05 * (s / 10.0)):
            target = random.uniform(0.35, 1.0)

        # Smooth towards target; faster speeds converge quicker.
        alpha = _clamp01(0.08 * (s / 10.0))
        intensity = _lerp(intensity, target, alpha)

        # Warm palette: blend between deep red and bright yellow by intensity.
        # intensity≈0.35 -> red/orange, intensity≈1.0 -> yellow.
        t = _clamp01((intensity - 0.35) / (1.0 - 0.35))
        r = 1.0
        g = _lerp(0.10, 0.90, t)
        b = _lerp(0.02, 0.10, t)

        try:
            tree.body.color = (r, g, b)
        except Exception:
            pass

        sleep(delay)


