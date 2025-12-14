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
    star = tree.star
    star.color = (1.0, 0.84, 0.2)

    body_pixels = [px for px in tree if px is not star]

    # speed is expected to be in a wide range (e.g. 0.1..200).
    s = max(0.001, float(speed))
    # Update cadence: very slow at low end (seconds), extremely fast at high end (milliseconds).
    delay = max(0.001, 1.0 / s)

    # Per-pixel flicker state (independent targets so the body doesn't move uniformly).
    intensities = [random.uniform(0.35, 0.8) for _ in body_pixels]
    targets = [i for i in intensities]
    # Each pixel gets a slightly different responsiveness and target-change rate.
    rates = [random.uniform(0.7, 1.4) for _ in body_pixels]

    # Optional subtle global modulation (helps avoid a chaotic "sparkle" feel).
    # Set to 0.0 if you want *purely* independent pixels.
    GLOBAL_STRENGTH = 0.05
    global_intensity = 0.5
    global_target = 0.5

    while not stop.is_set():
        # Global modulation updates slowly and gently.
        if random.random() < _clamp01(0.02 * (s / 10.0)):
            global_target = random.uniform(0.35, 0.75)
        global_intensity = _lerp(global_intensity, global_target, _clamp01(0.02 * (s / 10.0)))
        global_factor = 1.0 + GLOBAL_STRENGTH * ((global_intensity - 0.5) * 2.0)

        # Apply to all body pixels (everything except the star). Batch the SPI update.
        prev_auto = tree.auto_show
        tree.auto_show = False
        try:
            for i, px in enumerate(body_pixels):
                r_rate = rates[i]

                # Occasionally pick a new random target; higher speed changes targets more often.
                if random.random() < _clamp01(0.05 * (s / 10.0) * r_rate):
                    # Bias towards mid values for gentler motion
                    targets[i] = 0.15 + (random.random() ** 0.7) * 0.85

                # Smooth towards target; faster speeds converge quicker (with per-pixel variance).
                alpha = _clamp01(0.05 * (s / 10.0) * r_rate)
                intensities[i] = _lerp(intensities[i], targets[i], alpha)

                # Flame model:
                # - overall brightness follows intensity (dim ember -> bright flame)
                # - "temperature" shifts with brightness (dimmer is redder, brighter is yellower)
                brightness = _clamp01(intensities[i] * global_factor)
                temp = _clamp01((brightness - 0.15) / 0.85) ** 1.3

                # Base chromaticity endpoints (not yet brightness-scaled)
                ember = (1.0, 0.06, 0.00)   # dim, deep red/orange
                flame = (1.0, 0.95, 0.18)   # bright, warm yellow
                base_r = _lerp(ember[0], flame[0], temp)
                base_g = _lerp(ember[1], flame[1], temp)
                base_b = _lerp(ember[2], flame[2], temp)

                # Slight per-pixel jitter on top of per-pixel state, for shimmer.
                j = 1.0 + random.uniform(-0.06, 0.06) * (0.3 + 0.7 * brightness)
                px.color = (
                    _clamp01(base_r * brightness * j),
                    _clamp01(base_g * brightness * j),
                    _clamp01(base_b * brightness * j),
                )
        finally:
            tree.auto_show = prev_auto
            # Ensure we display the batched update each loop, regardless of prior auto_show.
            tree.show()

        sleep(delay)


