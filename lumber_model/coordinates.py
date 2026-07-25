from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from lumber_model.geometry import Vector3, v_add


class CoordinateResolver(Protocol):
    def resolve_coordinate_reference(self, name: str) -> Vector3: ...


@dataclass(frozen=True)
class AbsoluteCoord:
    """
    A model-space coordinate.

    Use this when a point is intentionally anchored to the global model axes.
    """

    x: float
    y: float
    z: float

    def resolve(self, resolver: CoordinateResolver | None = None) -> Vector3:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class RelativeCoord:
    """
    A coordinate offset from a named reference.

    ``reference`` is resolved by the collection or model context consuming the
    coordinate. The offset is applied in model-space axes.
    """

    reference: str
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def resolve(self, resolver: CoordinateResolver | None = None) -> Vector3:
        if resolver is None:
            raise ValueError(
                f"Relative coordinate {self!r} requires a coordinate resolver"
            )

        return v_add(
            resolver.resolve_coordinate_reference(self.reference),
            (self.x, self.y, self.z),
        )


Coordinate = AbsoluteCoord | RelativeCoord


def resolve_coordinate(
    name: str,
    coordinate: Coordinate,
    resolver: CoordinateResolver | None = None,
) -> Vector3:
    if not isinstance(coordinate, (AbsoluteCoord, RelativeCoord)):
        raise TypeError(f"{name} must be an AbsoluteCoord or RelativeCoord")

    return coordinate.resolve(resolver)
