from __future__ import annotations

from threading import Event
from time import sleep

from colorzero import Color

from rgbxmastree.hardware.tree import RGBXmasTree


def one_by_one(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Cycle through red, green and blue, changing pixel-by-pixel.
    Ported from examples/onebyone.py, but stop-able.
    """
    colors = [Color("red"), Color("green"), Color("blue")]
    delay = max(0.001, 0.02 / max(speed, 0.01))

    while not stop.is_set():
        for c in colors:
            for pixel in tree:
                if stop.is_set():
                    return
                pixel.color = c
                sleep(delay)


