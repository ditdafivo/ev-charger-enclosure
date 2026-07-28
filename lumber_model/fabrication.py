from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from lumber_model.formatting import fmt_float, inches_to_fraction_text, scad_string


Point2 = tuple[float, float]


def clip_polygon_to_box(
    polygon: tuple[Point2, ...],
    *,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> tuple[Point2, ...]:
    """Clip a convex XY polygon to an axis-aligned box."""

    points = list(polygon)
    boundaries = (
        (0, min_x, True),
        (0, max_x, False),
        (1, min_y, True),
        (1, max_y, False),
    )
    for axis, boundary, keep_greater in boundaries:
        if not points:
            break
        clipped: list[Point2] = []
        for start, end in zip(points, points[1:] + points[:1]):
            start_inside = (
                start[axis] >= boundary if keep_greater else start[axis] <= boundary
            )
            end_inside = (
                end[axis] >= boundary if keep_greater else end[axis] <= boundary
            )
            if start_inside:
                clipped.append(start)
            if start_inside != end_inside:
                fraction = (boundary - start[axis]) / (end[axis] - start[axis])
                intersection = (
                    start[0] + fraction * (end[0] - start[0]),
                    start[1] + fraction * (end[1] - start[1]),
                )
                clipped.append(intersection)
        points = clipped
    return tuple(points)


@dataclass(frozen=True)
class PurchasedItem:
    name: str
    assembly: str
    description: str
    qty: int

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError(f"{self.name}: quantity must be positive")

    def bom_row(self) -> dict[str, Any]:
        return {
            "category": "hardware",
            "assembly": self.assembly,
            "name": self.name,
            "type": self.description,
            "qty": self.qty,
            "axis": "",
            "length_in": "",
            "length_display": "",
            "rotated": "",
            "start_x": "",
            "start_y": "",
            "start_z": "",
            "size_x": "",
            "size_y": "",
            "size_z": "",
            "start_cut_angle_deg": "",
            "end_cut_angle_deg": "",
            "total_linear_ft": "",
            "stock_length_ft": "",
            "stock_board_qty": "",
        }


@dataclass(frozen=True)
class RoutedSeat:
    """A diagonal, flat-bottomed routed volume removed from one lumber member."""

    name: str
    member: str
    polygon: tuple[Point2, ...]
    depth: float
    top_z: float

    def __post_init__(self) -> None:
        if self.depth <= 0:
            raise ValueError(f"{self.name}: depth must be positive")
        if len(self.polygon) < 3:
            raise ValueError(f"{self.name}: routed seat polygon needs three points")
        if math.isclose(self.area, 0):
            raise ValueError(f"{self.name}: routed seat polygon must have area")

    @property
    def area(self) -> float:
        return abs(
            sum(
                start[0] * end[1] - end[0] * start[1]
                for start, end in zip(
                    self.polygon,
                    self.polygon[1:] + self.polygon[:1],
                )
            )
        ) / 2

    @property
    def min_x(self) -> float:
        return min(point[0] for point in self.polygon)

    @property
    def max_x(self) -> float:
        return max(point[0] for point in self.polygon)

    @property
    def min_y(self) -> float:
        return min(point[1] for point in self.polygon)

    @property
    def max_y(self) -> float:
        return max(point[1] for point in self.polygon)

    def fabrication_row(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "member": self.member,
            "operation": "route clipped diagonal footprint",
            "depth_in": round(self.depth, 4),
            "depth_display": inches_to_fraction_text(self.depth),
            "area_sq_in": round(self.area, 4),
            "top_z": round(self.top_z, 4),
            "min_x": round(self.min_x, 4),
            "max_x": round(self.max_x, 4),
            "min_y": round(self.min_y, 4),
            "max_y": round(self.max_y, 4),
            "polygon_xy": "; ".join(
                f"{point[0]:.4f} {point[1]:.4f}" for point in self.polygon
            ),
        }

    def scad_record(self) -> str:
        return (
            "["
            f"{scad_string(self.name)}, {scad_string(self.member)}, "
            "["
            + ", ".join(
                f"[{fmt_float(point[0])}, {fmt_float(point[1])}]"
                for point in self.polygon
            )
            + "], "
            f"{fmt_float(self.depth)}, {fmt_float(self.top_z)}"
            "]"
        )
