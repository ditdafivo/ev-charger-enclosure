from __future__ import annotations

from dataclasses import dataclass
import math

from lumber_model.coordinates import Coordinate, CoordinateResolver, resolve_coordinate
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )


def _length(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _unit(v: Vector3) -> Vector3:
    length = _length(v)

    if length == 0:
        raise ValueError("Cannot normalize zero-length vector")

    return (v[0] / length, v[1] / length, v[2] / length)


@dataclass(frozen=True)
class ResolvedGroundPlane:
    name: str
    origin: Vector3
    point_a: Vector3
    point_b: Vector3
    center: Vector3
    radius: float
    color: tuple[float, float, float, float]
    thickness: float

    @property
    def normal(self) -> Vector3:
        normal = _unit(
            _cross(
                _sub(self.point_a, self.origin),
                _sub(self.point_b, self.origin),
            )
        )

        if normal[2] < 0:
            return (-normal[0], -normal[1], -normal[2])

        return normal

    def z_at(self, x: float, y: float) -> float:
        normal = self.normal
        if abs(normal[2]) < 1e-9:
            raise ValueError("Cannot calculate elevation on a vertical ground plane")
        return self.origin[2] - (
            normal[0] * (x - self.origin[0])
            + normal[1] * (y - self.origin[1])
        ) / normal[2]

    def scad_record(self) -> str:
        def vector(values: tuple[float, ...]) -> str:
            return "[" + ", ".join(fmt_float(value) for value in values) + "]"

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{vector(self.center)}, "
            f"{vector(self.normal)}, "
            f"{fmt_float(self.radius)}, "
            f"{vector(self.color)}, "
            f"{fmt_float(self.thickness)}"
            "]"
        )


@dataclass(frozen=True)
class GroundPlane:
    """
    A circular visual representation of the ground plane.

    The plane is fixed to z=0 at the named origin reference's x/y position,
    normally ``post_fl``. Two additional model coordinates define the
    tilt. The rendered circle is centered at ``center``.
    """

    name: str
    point_a: Coordinate
    point_b: Coordinate
    center: Coordinate
    radius: float
    origin_reference: str = "post_fl"
    color: tuple[float, float, float, float] = (0.24, 0.42, 0.24, 0.35)
    thickness: float = 0.05

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"{self.name}: radius must be positive")

        if self.thickness <= 0:
            raise ValueError(f"{self.name}: thickness must be positive")

        if len(self.color) != 4:
            raise ValueError(f"{self.name}: color must be an RGBA tuple")

    def resolved(self, resolver: CoordinateResolver) -> ResolvedGroundPlane:
        reference = resolver.resolve_coordinate_reference(self.origin_reference)
        origin = (reference[0], reference[1], 0.0)
        point_a = resolve_coordinate(f"{self.name}: point_a", self.point_a, resolver)
        point_b = resolve_coordinate(f"{self.name}: point_b", self.point_b, resolver)
        center = resolve_coordinate(f"{self.name}: center", self.center, resolver)

        try:
            resolved = ResolvedGroundPlane(
                name=self.name,
                origin=origin,
                point_a=point_a,
                point_b=point_b,
                center=center,
                radius=self.radius,
                color=self.color,
                thickness=self.thickness,
            )
            resolved.normal
        except ValueError as exc:
            raise ValueError(
                f"{self.name}: ground plane points must not be coincident or collinear"
            ) from exc

        return resolved
