from __future__ import annotations

from threading import Event
from time import sleep

from colorzero import Color, Hue

from rgbxmastree.hardware.tree import RGBXmasTree


def hue_cycle(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Cycle through hues forever.
    Ported from examples/huecycle.py, but stop-able.
    """
    tree.color = Color("red")
    delay = max(0.005, 0.02 / max(speed, 0.01))
    step = max(1, int(3 * max(speed, 0.01)))

    while not stop.is_set():
        tree.color += Hue(deg=step)
        sleep(delay)


