from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _candle_rgb(brightness: float, *, white_bias: float = 0.0) -> tuple[float, float, float]:
    """
    Map a 0..1 brightness to a candle-like warm colour.

    Many RGB LEDs skew green in the "yellow" region. This palette intentionally
    keeps green lower (and slightly compresses it) so the hot end reads as amber.
    """
    b = _clamp01(brightness)
    # "Temperature" rises with brightness; shaped so most values sit in orange/amber.
    t = _clamp01((b - 0.10) / 0.90) ** 1.35

    # Piecewise palette: ember -> orange -> amber -> warm-white-ish
    if t < 0.45:
        tt = t / 0.45
        r = _lerp(1.0, 1.0, tt)
        g = _lerp(0.02, 0.22, tt)
        bb = _lerp(0.00, 0.01, tt)
    elif t < 0.80:
        tt = (t - 0.45) / 0.35
        r = _lerp(1.0, 1.0, tt)
        g = _lerp(0.22, 0.55, tt)
        bb = _lerp(0.01, 0.05, tt)
    else:
        tt = (t - 0.80) / 0.20
        r = _lerp(1.0, 1.0, tt)
        g = _lerp(0.55, 0.72, tt)
        bb = _lerp(0.05, 0.12, tt)

    # Optional push towards a slightly whiter "gold" (useful for the star).
    wb = _clamp01(white_bias)
    if wb > 0.0:
        r = _lerp(r, 1.0, wb)
        g = _lerp(g, 0.90, wb)
        bb = _lerp(bb, 0.20, wb)

    # LED correction: tame green a bit (minimal effect when g is already low).
    g *= 0.82
    g = g**1.10

    return (_clamp01(r), _clamp01(g), _clamp01(bb))


def candles(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Candle-like warm flicker on the body (red/orange/amber), star flickers too.

    The only tempo control is the supplied `speed` knob from the web UI/controller.
    """
    star = tree.star
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

    # Star flicker state (independent of the body).
    star_intensity = random.uniform(0.55, 0.90)
    star_target = star_intensity
    star_rate = random.uniform(0.8, 1.2)

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
            # --- star ---
            if random.random() < _clamp01(0.04 * (s / 10.0) * star_rate):
                star_target = 0.35 + (random.random() ** 0.65) * 0.65
            star_alpha = _clamp01(0.04 * (s / 10.0) * star_rate)
            star_intensity = _lerp(star_intensity, star_target, star_alpha)

            star_brightness = _clamp01(star_intensity * (1.0 + 0.02 * ((global_intensity - 0.5) * 2.0)))
            sr, sg, sb = _candle_rgb(star_brightness, white_bias=0.18)
            sj = 1.0 + random.uniform(-0.04, 0.04) * (0.25 + 0.75 * star_brightness)
            star.color = (_clamp01(sr * sj), _clamp01(sg * sj), _clamp01(sb * sj))

            for i, px in enumerate(body_pixels):
                r_rate = rates[i]

                # Occasionally pick a new random target; higher speed changes targets more often.
                if random.random() < _clamp01(0.05 * (s / 10.0) * r_rate):
                    # Bias towards mid values for gentler motion
                    targets[i] = 0.15 + (random.random() ** 0.7) * 0.85

                # Smooth towards target; faster speeds converge quicker (with per-pixel variance).
                alpha = _clamp01(0.05 * (s / 10.0) * r_rate)
                intensities[i] = _lerp(intensities[i], targets[i], alpha)

                brightness = _clamp01(intensities[i] * global_factor)
                base_r, base_g, base_b = _candle_rgb(brightness)

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


