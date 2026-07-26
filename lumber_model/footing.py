from __future__ import annotations

from dataclasses import dataclass

from lumber_model.coordinates import Coordinate, CoordinateResolver, resolve_coordinate
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3


DEFAULT_GRAVEL_COLOR = (0.46, 0.43, 0.37, 0.45)


@dataclass(frozen=True)
class ResolvedFooting:
    name: str
    center: Vector3
    diameter: float
    bottom_z: float
    top_z: float
    color: tuple[float, float, float, float]

    def scad_record(self) -> str:
        def vector(values: tuple[float, ...]) -> str:
            return "[" + ", ".join(fmt_float(value) for value in values) + "]"

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{vector(self.center)}, "
            f"{fmt_float(self.diameter)}, "
            f"{fmt_float(self.bottom_z)}, "
            f"{fmt_float(self.top_z)}, "
            f"{vector(self.color)}"
            "]"
        )


@dataclass(frozen=True)
class Footing:
    """A vertical cylindrical footing centered at a model coordinate."""

    name: str
    center: Coordinate
    diameter: float
    bottom_z: float
    top_z: float
    color: tuple[float, float, float, float] = DEFAULT_GRAVEL_COLOR

    def __post_init__(self) -> None:
        if self.diameter <= 0:
            raise ValueError(f"{self.name}: diameter must be positive")
        if self.top_z <= self.bottom_z:
            raise ValueError(f"{self.name}: top_z must be greater than bottom_z")
        if len(self.color) != 4:
            raise ValueError(f"{self.name}: color must be an RGBA tuple")

    def resolved(self, resolver: CoordinateResolver) -> ResolvedFooting:
        center = resolve_coordinate(f"{self.name}: center", self.center, resolver)
        return ResolvedFooting(
            name=self.name,
            center=(center[0], center[1], (self.bottom_z + self.top_z) / 2),
            diameter=self.diameter,
            bottom_z=self.bottom_z,
            top_z=self.top_z,
            color=self.color,
        )
