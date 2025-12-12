from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Callable, Protocol

from rgbxmastree.hardware.tree import RGBXmasTree


class ProgramRunner(Protocol):
    def __call__(self, tree: RGBXmasTree, stop: Event, speed: float) -> None: ...


@dataclass(frozen=True)
class ProgramSpec:
    id: str
    name: str
    runner: Callable[[RGBXmasTree, Event, float], None]
    default_speed: float = 1.0


