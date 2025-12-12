from __future__ import annotations

from threading import Event
from time import sleep

from colorzero import Color

from rgbxmastree.hardware.tree import RGBXmasTree


def rgb_cycle(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Cycle through red, green and blue, changing all pixels together.
    Ported from examples/rgb.py, but stop-able.
    """
    colors = [Color("red"), Color("green"), Color("blue")]
    delay = max(0.01, 1.0 / max(speed, 0.01))

    while not stop.is_set():
        for c in colors:
            if stop.is_set():
                return
            tree.color = c
            sleep(delay)


