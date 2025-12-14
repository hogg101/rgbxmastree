from __future__ import annotations

from rgbxmastree.programs.base import ProgramSpec
from rgbxmastree.programs.candles import candles
from rgbxmastree.programs.hue_cycle import hue_cycle
from rgbxmastree.programs.navi import navi
from rgbxmastree.programs.one_by_one import one_by_one
from rgbxmastree.programs.random_sparkles import random_sparkles
from rgbxmastree.programs.rainbow_snake import rainbow_snake
from rgbxmastree.programs.rgb_cycle import rgb_cycle
from rgbxmastree.programs.snowfall import snowfall


PROGRAMS: dict[str, ProgramSpec] = {
    "candles": ProgramSpec(
        id="candles",
        name="Candles",
        runner=candles,
        default_speed=1.0,
    ),
    "navi": ProgramSpec(
        id="navi",
        name="Navi",
        runner=navi,
        default_speed=1.0,
    ),
    "rgb_cycle": ProgramSpec(
        id="rgb_cycle",
        name="Legacy: RGB Cycle",
        runner=rgb_cycle,
        default_speed=1.0,
    ),
    "one_by_one": ProgramSpec(
        id="one_by_one",
        name="Legacy: One by One",
        runner=one_by_one,
        default_speed=1.0,
    ),
    "hue_cycle": ProgramSpec(
        id="hue_cycle",
        name="Legacy: Hue Cycle",
        runner=hue_cycle,
        default_speed=1.0,
    ),
    "random_sparkles": ProgramSpec(
        id="random_sparkles",
        name="Legacy: Random Sparkles",
        runner=random_sparkles,
        default_speed=1.0,
    ),
    "rainbow_snake": ProgramSpec(
        id="rainbow_snake",
        name="Rainbow Snake",
        runner=rainbow_snake,
        default_speed=1.0,
    ),
    "snowfall": ProgramSpec(
        id="snowfall",
        name="Snowfall",
        runner=snowfall,
        default_speed=1.0,
    ),
}


