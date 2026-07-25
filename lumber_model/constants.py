from __future__ import annotations

from typing import Literal


Axis = Literal["x", "y", "z"]
LumberType = Literal["2x4", "4x4"]


ACTUAL_DIMS: dict[LumberType, tuple[float, float]] = {
    "2x4": (1.5, 3.5),
    "4x4": (3.5, 3.5),
}

AXES: tuple[Axis, Axis, Axis] = ("x", "y", "z")

AXIS_INDEX: dict[Axis, int] = {
    "x": 0,
    "y": 1,
    "z": 2,
}
