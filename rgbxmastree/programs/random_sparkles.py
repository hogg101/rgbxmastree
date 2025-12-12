from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def _random_color():
    return (random.random(), random.random(), random.random())


def random_sparkles(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Randomly sparkle all the pixels.
    Ported from examples/randomsparkles.py, but stop-able.
    """
    delay = max(0.001, 0.03 / max(speed, 0.01))

    while not stop.is_set():
        pixel = random.choice(list(tree))
        pixel.color = _random_color()
        sleep(delay)


