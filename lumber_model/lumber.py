from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from lumber_model.constants import ACTUAL_DIMS, AXES, AXIS_INDEX, Axis, LumberType
from lumber_model.coordinates import AbsoluteCoord, Coordinate, resolve_coordinate
from lumber_model.formatting import (
    fmt_float,
    inches_to_fraction_text,
    scad_bool,
    scad_string,
)
from lumber_model.geometry import (
    Vector3,
    inferred_position_axis,
    other_axis,
    replace_axis,
    v_add,
    v_mid,
)


@dataclass(frozen=True)
class Lumber:
    """
    A single piece of lumber.

    Coordinates:
      - start is the minimum [x, y, z] corner.
      - axis is the long axis of the member.
      - length is along axis.

    Default rotated=True orientation:
      X-running 2x4 -> [length, 3.5, 1.5]
      Y-running 2x4 -> [3.5, length, 1.5]
      Z-running 2x4 -> [3.5, 1.5, length]

    rotated=False orientation:
      X-running 2x4 -> [length, 1.5, 3.5]
      Y-running 2x4 -> [1.5, length, 3.5]
      Z-running 2x4 -> [1.5, 3.5, length]
    """

    name: str
    assembly: str
    type: LumberType
    axis: Axis
    start: Coordinate | Vector3
    length: float
    rotated: bool = True

    def __post_init__(self) -> None:
        if self.type not in ACTUAL_DIMS:
            raise ValueError(f"{self.name}: unsupported lumber type {self.type!r}")

        if self.axis not in AXES:
            raise ValueError(f"{self.name}: invalid axis {self.axis!r}")

        if self.length <= 0:
            raise ValueError(f"{self.name}: length must be positive, got {self.length}")

        if isinstance(self.start, AbsoluteCoord):
            object.__setattr__(
                self, "start", resolve_coordinate(f"{self.name}: start", self.start)
            )

        if len(self.start) != 3:
            raise ValueError(f"{self.name}: start must be a 3-tuple")

    @property
    def dims(self) -> tuple[float, float]:
        return ACTUAL_DIMS[self.type]

    @property
    def size(self) -> Vector3:
        narrow, wide = self.dims

        if self.axis == "x":
            return (
                self.length,
                wide if self.rotated else narrow,
                narrow if self.rotated else wide,
            )

        if self.axis == "y":
            return (
                wide if self.rotated else narrow,
                self.length,
                narrow if self.rotated else wide,
            )

        if self.axis == "z":
            return (
                wide if self.rotated else narrow,
                narrow if self.rotated else wide,
                self.length,
            )

        raise ValueError(f"{self.name}: invalid axis {self.axis!r}")

    @property
    def min(self) -> Vector3:
        return self.start

    @property
    def max(self) -> Vector3:
        return v_add(self.start, self.size)

    @property
    def center(self) -> Vector3:
        return v_mid(self.min, self.max)

    def min_on(self, axis: Axis) -> float:
        return self.min[AXIS_INDEX[axis]]

    def max_on(self, axis: Axis) -> float:
        return self.max[AXIS_INDEX[axis]]

    def center_on(self, axis: Axis) -> float:
        return self.center[AXIS_INDEX[axis]]

    def gap_to(self, other: Lumber, axis: Axis) -> float:
        """
        Positive value means there is a clear gap between the two pieces on this axis.
        Negative value means the two pieces overlap on this axis.
        """
        return max(
            other.min_on(axis) - self.max_on(axis),
            self.min_on(axis) - other.max_on(axis),
        )

    def center_distance_to(self, other: Lumber, axis: Axis) -> float:
        return abs(self.center_on(axis) - other.center_on(axis))

    @staticmethod
    def infer_span_axis(support_a: Lumber, support_b: Lumber) -> Axis:
        """
        Infer the axis on which a new member should span between two supports.

        Priority:
          1. Use the axis with the largest positive clear gap.
          2. If supports overlap on all axes, use the largest center distance.
        """
        gaps = {
            axis: support_a.gap_to(support_b, axis)
            for axis in AXES
        }

        positive_gaps = {
            axis: gap
            for axis, gap in gaps.items()
            if gap > 0
        }

        if positive_gaps:
            return max(positive_gaps, key=positive_gaps.get)  # type: ignore[arg-type]

        distances = {
            axis: support_a.center_distance_to(support_b, axis)
            for axis in AXES
        }

        return max(distances, key=distances.get)  # type: ignore[arg-type]

    @classmethod
    def between(
        cls,
        name: str,
        assembly: str,
        type: LumberType,
        support_a: Lumber,
        support_b: Lumber,
        position: float,
        cross_offset: float = 0,
        inset: float = 0,
        rotated: bool = True,
        span_axis: Axis | None = None,
        position_axis: Axis | None = None,
    ) -> Lumber:
        """
        Create a member between the inside faces of two support/reference members.

        Normal use does not require span_axis or position_axis.

        Inference:
          - span_axis is inferred from the two supports.
          - position_axis defaults to Z for X/Y spans.
          - position_axis defaults to X for Z spans.

        Overrides:
          - span_axis and position_axis are optional escape hatches
            for unusual or ambiguous layouts.
        """
        resolved_span_axis = (
            span_axis
            if span_axis is not None
            else cls.infer_span_axis(support_a, support_b)
        )

        resolved_position_axis = (
            position_axis
            if position_axis is not None
            else inferred_position_axis(resolved_span_axis)
        )

        if resolved_span_axis == resolved_position_axis:
            raise ValueError(
                f"{name}: span_axis and position_axis must be different. "
                f"Got {resolved_span_axis!r} for both."
            )

        cross_axis = other_axis(resolved_span_axis, resolved_position_axis)

        narrow, wide = ACTUAL_DIMS[type]

        a_min = support_a.min_on(resolved_span_axis)
        b_min = support_b.min_on(resolved_span_axis)

        if a_min < b_min:
            start_face = support_a.max_on(resolved_span_axis)
            end_face = support_b.min_on(resolved_span_axis)
        else:
            start_face = support_b.max_on(resolved_span_axis)
            end_face = support_a.min_on(resolved_span_axis)

        start_span = start_face + inset
        end_span = end_face - inset
        member_length = end_span - start_span

        if member_length <= 0:
            raise ValueError(
                f"{name}: derived length is {member_length:.4f}. "
                f"Check support positions, span inference, or inset. "
                f"Inferred span_axis={resolved_span_axis!r}."
            )

        if resolved_span_axis == "x":
            member_size = (
                member_length,
                wide if rotated else narrow,
                narrow if rotated else wide,
            )
        elif resolved_span_axis == "y":
            member_size = (
                wide if rotated else narrow,
                member_length,
                narrow if rotated else wide,
            )
        else:
            member_size = (
                wide if rotated else narrow,
                narrow if rotated else wide,
                member_length,
            )

        cross_dim = member_size[AXIS_INDEX[cross_axis]]
        position_dim = member_size[AXIS_INDEX[resolved_position_axis]]

        cross_min = max(
            support_a.min_on(cross_axis),
            support_b.min_on(cross_axis),
        )
        cross_max = min(
            support_a.max_on(cross_axis),
            support_b.max_on(cross_axis),
        )

        if cross_max <= cross_min:
            raise ValueError(
                f"{name}: supports do not overlap on cross_axis={cross_axis!r}. "
                "Cannot derive aligned cross position."
            )

        cross_center = (cross_min + cross_max) / 2

        start = (0.0, 0.0, 0.0)
        start = replace_axis(start, resolved_span_axis, start_span)
        start = replace_axis(
            start,
            cross_axis,
            cross_center + cross_offset - cross_dim / 2,
        )
        start = replace_axis(
            start,
            resolved_position_axis,
            position - position_dim / 2,
        )

        return cls(
            name=name,
            assembly=assembly,
            type=type,
            axis=resolved_span_axis,
            start=start,
            length=member_length,
            rotated=rotated,
        )

    def bom_row(self) -> dict[str, Any]:
        return {
            "assembly": self.assembly,
            "name": self.name,
            "type": self.type,
            "axis": self.axis,
            "length_in": round(self.length, 4),
            "length_display": inches_to_fraction_text(self.length),
            "rotated": self.rotated,
            "start_x": round(self.start[0], 4),
            "start_y": round(self.start[1], 4),
            "start_z": round(self.start[2], 4),
            "size_x": round(self.size[0], 4),
            "size_y": round(self.size[1], 4),
            "size_z": round(self.size[2], 4),
            "start_cut_angle_deg": "",
            "end_cut_angle_deg": "",
        }

    def scad_record(self) -> str:
        sx, sy, sz = self.start

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{scad_string(self.type)}, "
            f"{scad_string(self.axis)}, "
            f"[{fmt_float(sx)}, {fmt_float(sy)}, {fmt_float(sz)}], "
            f"{fmt_float(self.length)}, "
            f"{scad_bool(self.rotated)}"
            "]"
        )


@dataclass(frozen=True)
class AngledLumber:
    """
    A horizontal lumber member modeled from a centerline start/end.

    The member is rendered with its long axis along the centerline, its wide face
    horizontal in XY, and its narrow dimension vertical. This is intended for
    flat diagonal bracing in the top-rail plane.
    """

    name: str
    assembly: str
    type: LumberType
    start: Vector3
    end: Vector3
    rotated: bool = True

    def __post_init__(self) -> None:
        if self.type not in ACTUAL_DIMS:
            raise ValueError(f"{self.name}: unsupported lumber type {self.type!r}")

        if len(self.start) != 3:
            raise ValueError(f"{self.name}: start must be a 3-tuple")

        if len(self.end) != 3:
            raise ValueError(f"{self.name}: end must be a 3-tuple")

        if self.length <= 0:
            raise ValueError(f"{self.name}: length must be positive, got {self.length}")

        if not math.isclose(self.start[2], self.end[2]):
            raise ValueError(
                f"{self.name}: angled lumber must be horizontal; "
                f"got start z={self.start[2]} and end z={self.end[2]}"
            )

    @property
    def dims(self) -> tuple[float, float]:
        return ACTUAL_DIMS[self.type]

    @property
    def width(self) -> float:
        narrow, wide = self.dims
        return wide if self.rotated else narrow

    @property
    def thickness(self) -> float:
        narrow, wide = self.dims
        return narrow if self.rotated else wide

    @property
    def length(self) -> float:
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @property
    def angle_deg(self) -> float:
        return math.degrees(
            math.atan2(self.end[1] - self.start[1], self.end[0] - self.start[0])
        )

    @property
    def cut_angle_deg(self) -> float:
        angle = abs(self.angle_deg) % 180
        if angle > 90:
            angle = 180 - angle
        return angle

    @property
    def min(self) -> Vector3:
        half_width = self.width / 2
        half_thickness = self.thickness / 2
        return (
            min(self.start[0], self.end[0]) - half_width,
            min(self.start[1], self.end[1]) - half_width,
            self.start[2] - half_thickness,
        )

    @property
    def max(self) -> Vector3:
        half_width = self.width / 2
        half_thickness = self.thickness / 2
        return (
            max(self.start[0], self.end[0]) + half_width,
            max(self.start[1], self.end[1]) + half_width,
            self.start[2] + half_thickness,
        )

    @property
    def size(self) -> Vector3:
        return (
            self.max[0] - self.min[0],
            self.max[1] - self.min[1],
            self.max[2] - self.min[2],
        )

    @property
    def center(self) -> Vector3:
        return v_mid(self.start, self.end)

    def bom_row(self) -> dict[str, Any]:
        return {
            "assembly": self.assembly,
            "name": self.name,
            "type": self.type,
            "axis": "angled",
            "length_in": round(self.length, 4),
            "length_display": inches_to_fraction_text(self.length),
            "rotated": self.rotated,
            "start_x": round(self.start[0], 4),
            "start_y": round(self.start[1], 4),
            "start_z": round(self.start[2] - self.thickness / 2, 4),
            "size_x": round(self.size[0], 4),
            "size_y": round(self.size[1], 4),
            "size_z": round(self.size[2], 4),
            "start_cut_angle_deg": round(self.cut_angle_deg, 2),
            "end_cut_angle_deg": round(self.cut_angle_deg, 2),
        }

    def scad_record(self) -> str:
        sx, sy, sz = self.start
        ex, ey, ez = self.end

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{scad_string(self.type)}, "
            f"{scad_string('angled')}, "
            f"[{fmt_float(sx)}, {fmt_float(sy)}, {fmt_float(sz)}], "
            f"{fmt_float(self.length)}, "
            f"{scad_bool(self.rotated)}, "
            f"[{fmt_float(ex)}, {fmt_float(ey)}, {fmt_float(ez)}], "
            f"{fmt_float(self.width)}, "
            f"{fmt_float(self.thickness)}, "
            f"{fmt_float(self.angle_deg)}"
            "]"
        )


LumberPiece = Lumber | AngledLumber
