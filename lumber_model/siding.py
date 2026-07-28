from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Any

from lumber_model.formatting import fmt_float, inches_to_fraction_text, scad_string
from lumber_model.geometry import Vector3


SidingColor = tuple[float, float, float, float]
DEFAULT_DECKING_COLOR: SidingColor = (0.17, 0.18, 0.19, 1.0)
DEFAULT_ANGLE_COLOR: SidingColor = (0.03, 0.03, 0.03, 1.0)


def _format_vector(values: tuple[float, ...]) -> str:
    return "[" + ", ".join(fmt_float(value) for value in values) + "]"


def _course_widths(span: float, board_width: float, gap: float) -> tuple[float, ...]:
    count = math.ceil((span + gap) / (board_width + gap))
    final_width = span - (count - 1) * (board_width + gap)
    if final_width <= 0:
        raise ValueError(
            "Siding span leaves no room for the final board after applying gaps"
        )
    return (board_width,) * (count - 1) + (final_width,)


def minimum_stock_board_count(
    cut_lengths: tuple[float, ...],
    stock_length: float,
) -> int:
    """Return the exact minimum number of stock boards needed for the cuts."""
    if stock_length <= 0:
        raise ValueError("Siding stock length must be positive")
    if any(length <= 0 for length in cut_lengths):
        raise ValueError("Siding cut lengths must be positive")
    if not cut_lengths:
        return 0

    cuts = tuple(sorted(cut_lengths, reverse=True))
    if cuts[0] > stock_length + 1e-9:
        raise ValueError(
            f"Siding cut length {cuts[0]} exceeds stock length {stock_length}"
        )

    lower_bound = math.ceil(sum(cuts) / stock_length - 1e-12)

    # First-fit decreasing provides a small, deterministic upper bound.
    remaining: list[float] = []
    for cut in cuts:
        for index, capacity in enumerate(remaining):
            if capacity + 1e-9 >= cut:
                remaining[index] -= cut
                break
        else:
            remaining.append(stock_length - cut)
    upper_bound = len(remaining)

    for board_count in range(lower_bound, upper_bound + 1):
        initial = tuple(stock_length for _ in range(board_count))

        @lru_cache(maxsize=None)
        def can_pack(index: int, capacities: tuple[float, ...]) -> bool:
            if index == len(cuts):
                return True

            cut = cuts[index]
            tried: set[float] = set()
            for bin_index, capacity in enumerate(capacities):
                rounded_capacity = round(capacity, 7)
                if rounded_capacity in tried or capacity + 1e-9 < cut:
                    continue
                tried.add(rounded_capacity)

                updated = list(capacities)
                updated[bin_index] = round(capacity - cut, 7)
                next_capacities = tuple(sorted(updated, reverse=True))
                if can_pack(index + 1, next_capacities):
                    return True

            return False

        if can_pack(0, initial):
            return board_count

    return upper_bound


@dataclass(frozen=True)
class SidingPart:
    name: str
    material: str
    start: Vector3
    size: Vector3
    color: SidingColor
    cut_length: float | None = None

    def scad_record(self) -> str:
        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.material)}, "
            f"{_format_vector(self.start)}, "
            f"{_format_vector(self.size)}, "
            f"{_format_vector(self.color)}"
            "]"
        )


@dataclass(frozen=True)
class FrontSidingOpening:
    name: str
    min_x: float
    max_x: float
    bottom_z: float
    top_z: float

    def __post_init__(self) -> None:
        if self.max_x <= self.min_x or self.top_z <= self.bottom_z:
            raise ValueError(f"{self.name}: siding opening must have positive area")


@dataclass(frozen=True)
class RightSidingOpening:
    name: str
    min_y: float
    max_y: float
    bottom_z: float
    top_z: float

    def __post_init__(self) -> None:
        if self.max_y <= self.min_y or self.top_z <= self.bottom_z:
            raise ValueError(f"{self.name}: siding opening must have positive area")


FrontRectangle = tuple[float, float, float, float]
RightRectangle = tuple[float, float, float, float]


def _subtract_front_opening(
    rectangle: FrontRectangle,
    opening: FrontSidingOpening,
) -> tuple[FrontRectangle, ...]:
    min_x, max_x, bottom_z, top_z = rectangle
    overlap_min_x = max(min_x, opening.min_x)
    overlap_max_x = min(max_x, opening.max_x)
    overlap_bottom_z = max(bottom_z, opening.bottom_z)
    overlap_top_z = min(top_z, opening.top_z)

    if overlap_max_x <= overlap_min_x or overlap_top_z <= overlap_bottom_z:
        return (rectangle,)

    pieces: list[FrontRectangle] = []
    if min_x < overlap_min_x:
        pieces.append((min_x, overlap_min_x, bottom_z, top_z))
    if overlap_max_x < max_x:
        pieces.append((overlap_max_x, max_x, bottom_z, top_z))
    if bottom_z < overlap_bottom_z:
        pieces.append(
            (overlap_min_x, overlap_max_x, bottom_z, overlap_bottom_z)
        )
    if overlap_top_z < top_z:
        pieces.append((overlap_min_x, overlap_max_x, overlap_top_z, top_z))

    return tuple(pieces)


def _subtract_right_opening(
    rectangle: RightRectangle,
    opening: RightSidingOpening,
) -> tuple[RightRectangle, ...]:
    min_y, max_y, bottom_z, top_z = rectangle
    overlap_min_y = max(min_y, opening.min_y)
    overlap_max_y = min(max_y, opening.max_y)
    overlap_bottom_z = max(bottom_z, opening.bottom_z)
    overlap_top_z = min(top_z, opening.top_z)

    if overlap_max_y <= overlap_min_y or overlap_top_z <= overlap_bottom_z:
        return (rectangle,)

    pieces: list[RightRectangle] = []
    if min_y < overlap_min_y:
        pieces.append((min_y, overlap_min_y, bottom_z, top_z))
    if overlap_max_y < max_y:
        pieces.append((overlap_max_y, max_y, bottom_z, top_z))
    if bottom_z < overlap_bottom_z:
        pieces.append(
            (overlap_min_y, overlap_max_y, bottom_z, overlap_bottom_z)
        )
    if overlap_top_z < top_z:
        pieces.append((overlap_min_y, overlap_max_y, overlap_top_z, top_z))

    return tuple(pieces)


@dataclass(frozen=True)
class CompositeSiding:
    name: str
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    frame_top_z: float
    bottom_z: float
    rear_opening_min_x: float
    rear_opening_max_x: float
    rear_opening_top_z: float
    roof_support_z: float | None = None
    board_width: float = 5.5
    board_thickness: float = 1.0
    gap: float = 3 / 16
    stock_length: float = 16 * 12
    angle_leg_width: float = 1.25
    angle_thickness: float = 0.125
    decking_color: SidingColor = DEFAULT_DECKING_COLOR
    angle_color: SidingColor = DEFAULT_ANGLE_COLOR
    assembly: str = "siding"
    front_openings: tuple[FrontSidingOpening, ...] = ()
    right_openings: tuple[RightSidingOpening, ...] = ()

    def __post_init__(self) -> None:
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError(f"{self.name}: siding envelope must have positive area")
        if self.frame_top_z <= self.bottom_z:
            raise ValueError(f"{self.name}: frame top must be above siding bottom")
        if self.roof_support_z is None:
            object.__setattr__(self, "roof_support_z", self.frame_top_z)
        elif self.roof_support_z < self.frame_top_z:
            raise ValueError(
                f"{self.name}: roof support must not be below the frame top"
            )
        for field_name in (
            "board_width",
            "board_thickness",
            "stock_length",
            "angle_leg_width",
            "angle_thickness",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{self.name}: {field_name} must be positive")
        if self.gap < 0:
            raise ValueError(f"{self.name}: gap must not be negative")
        if not (
            self.min_x
            < self.rear_opening_min_x
            < self.rear_opening_max_x
            < self.max_x
        ):
            raise ValueError(
                f"{self.name}: rear opening must lie strictly inside the envelope"
            )
        for opening in self.front_openings:
            if not isinstance(opening, FrontSidingOpening):
                raise TypeError(
                    f"{self.name}: front_openings must contain FrontSidingOpening"
                )
            if not (
                self.min_x <= opening.min_x
                < opening.max_x <= self.max_x
                and self.bottom_z <= opening.bottom_z
                < opening.top_z <= self.finished_top_z
            ):
                raise ValueError(
                    f"{self.name}: front opening {opening.name!r} must lie within "
                    "the front wall"
                )
        for index, opening in enumerate(self.front_openings):
            for other in self.front_openings[index + 1 :]:
                overlaps_x = max(opening.min_x, other.min_x) < min(
                    opening.max_x,
                    other.max_x,
                )
                overlaps_z = max(opening.bottom_z, other.bottom_z) < min(
                    opening.top_z,
                    other.top_z,
                )
                if overlaps_x and overlaps_z:
                    raise ValueError(
                        f"{self.name}: front openings {opening.name!r} and "
                        f"{other.name!r} overlap"
                    )
        for opening in self.right_openings:
            if not isinstance(opening, RightSidingOpening):
                raise TypeError(
                    f"{self.name}: right_openings must contain RightSidingOpening"
                )
            if not (
                self.min_y <= opening.min_y
                < opening.max_y <= self.max_y
                and self.bottom_z <= opening.bottom_z
                < opening.top_z <= self.finished_top_z
            ):
                raise ValueError(
                    f"{self.name}: right opening {opening.name!r} must lie within "
                    "the right wall"
                )
        for index, opening in enumerate(self.right_openings):
            for other in self.right_openings[index + 1 :]:
                overlaps_y = max(opening.min_y, other.min_y) < min(
                    opening.max_y,
                    other.max_y,
                )
                overlaps_z = max(opening.bottom_z, other.bottom_z) < min(
                    opening.top_z,
                    other.top_z,
                )
                if overlaps_y and overlaps_z:
                    raise ValueError(
                        f"{self.name}: right openings {opening.name!r} and "
                        f"{other.name!r} overlap"
                    )
        if len(self.decking_color) != 4 or len(self.angle_color) != 4:
            raise ValueError(f"{self.name}: siding colors must be RGBA 4-tuples")

        # Resolve geometry during validation so impossible final courses fail early.
        _course_widths(self.max_y - self.min_y, self.board_width, self.gap)
        wall_courses = _course_widths(
            self.finished_top_z - self.bottom_z,
            self.board_width,
            self.gap,
        )
        top_course_bottom = self.finished_top_z - wall_courses[0]
        if not top_course_bottom < self.rear_opening_top_z < self.finished_top_z:
            raise ValueError(
                f"{self.name}: rear opening top must fall within the top wall course"
            )

    @property
    def finished_top_z(self) -> float:
        return self.frame_top_z + self.board_thickness

    @property
    def roof_finished_top_z(self) -> float:
        assert self.roof_support_z is not None
        return self.roof_support_z + self.board_thickness

    def _board_parts(self) -> tuple[SidingPart, ...]:
        parts: list[SidingPart] = []
        frame_width = self.max_x - self.min_x
        frame_depth = self.max_y - self.min_y
        exterior_depth = frame_depth + 2 * self.board_thickness

        top_widths = _course_widths(frame_depth, self.board_width, self.gap)
        y = self.min_y
        for index, width in enumerate(top_widths, start=1):
            parts.append(
                SidingPart(
                    name=f"{self.name}_top_{index}",
                    material="composite_decking",
                    start=(self.min_x, y, self.roof_support_z),
                    size=(frame_width, width, self.board_thickness),
                    color=self.decking_color,
                    cut_length=frame_width,
                )
            )
            y += width + self.gap

        course_widths = _course_widths(
            self.finished_top_z - self.bottom_z,
            self.board_width,
            self.gap,
        )
        course_top = self.finished_top_z
        for index, height in enumerate(course_widths, start=1):
            z = course_top - height
            course_top = z - self.gap

            front_rectangles: tuple[FrontRectangle, ...] = (
                (self.min_x, self.max_x, z, z + height),
            )
            for opening in self.front_openings:
                front_rectangles = tuple(
                    piece
                    for rectangle in front_rectangles
                    for piece in _subtract_front_opening(rectangle, opening)
                )

            front_parts = []
            for piece_index, rectangle in enumerate(front_rectangles, start=1):
                min_x, max_x, bottom_z, top_z = rectangle
                part_suffix = (
                    str(index)
                    if len(front_rectangles) == 1
                    else f"{index}_{piece_index}"
                )
                front_parts.append(
                    SidingPart(
                        name=f"{self.name}_front_{part_suffix}",
                        material="composite_decking",
                        start=(
                            min_x,
                            self.min_y - self.board_thickness,
                            bottom_z,
                        ),
                        size=(
                            max_x - min_x,
                            self.board_thickness,
                            top_z - bottom_z,
                        ),
                        color=self.decking_color,
                        cut_length=frame_width if piece_index == 1 else None,
                    )
                )

            right_rectangles: tuple[RightRectangle, ...] = (
                (
                    self.min_y - self.board_thickness,
                    self.max_y + self.board_thickness,
                    z,
                    z + height,
                ),
            )
            for opening in self.right_openings:
                right_rectangles = tuple(
                    piece
                    for rectangle in right_rectangles
                    for piece in _subtract_right_opening(rectangle, opening)
                )

            right_parts = []
            for piece_index, rectangle in enumerate(right_rectangles, start=1):
                min_y, max_y, bottom_z, top_z = rectangle
                part_suffix = (
                    str(index)
                    if len(right_rectangles) == 1
                    else f"{index}_{piece_index}"
                )
                right_parts.append(
                    SidingPart(
                        name=f"{self.name}_right_{part_suffix}",
                        material="composite_decking",
                        start=(self.max_x, min_y, bottom_z),
                        size=(
                            self.board_thickness,
                            max_y - min_y,
                            top_z - bottom_z,
                        ),
                        color=self.decking_color,
                        cut_length=exterior_depth if piece_index == 1 else None,
                    )
                )

            course_parts = front_parts + [
                SidingPart(
                    name=f"{self.name}_left_{index}",
                    material="composite_decking",
                    start=(
                        self.min_x - self.board_thickness,
                        self.min_y - self.board_thickness,
                        z,
                    ),
                    size=(self.board_thickness, exterior_depth, height),
                    color=self.decking_color,
                    cut_length=exterior_depth,
                ),
            ] + right_parts

            if index == 1:
                # One full-length rear board with a rectangular tambour opening
                # is rendered as three boxes. Only the first carries its cut
                # length so the BOM counts the physical board once.
                course_parts.extend(
                    (
                        SidingPart(
                            name=f"{self.name}_rear_top_left",
                            material="composite_decking",
                            start=(self.min_x, self.max_y, z),
                            size=(
                                self.rear_opening_min_x - self.min_x,
                                self.board_thickness,
                                height,
                            ),
                            color=self.decking_color,
                            cut_length=frame_width,
                        ),
                        SidingPart(
                            name=f"{self.name}_rear_top_header",
                            material="composite_decking",
                            start=(
                                self.rear_opening_min_x,
                                self.max_y,
                                self.rear_opening_top_z,
                            ),
                            size=(
                                self.rear_opening_max_x
                                - self.rear_opening_min_x,
                                self.board_thickness,
                                self.finished_top_z - self.rear_opening_top_z,
                            ),
                            color=self.decking_color,
                        ),
                        SidingPart(
                            name=f"{self.name}_rear_top_right",
                            material="composite_decking",
                            start=(self.rear_opening_max_x, self.max_y, z),
                            size=(
                                self.max_x - self.rear_opening_max_x,
                                self.board_thickness,
                                height,
                            ),
                            color=self.decking_color,
                        ),
                    )
                )
            else:
                course_parts.extend(
                    (
                        SidingPart(
                            name=f"{self.name}_rear_left_{index}",
                            material="composite_decking",
                            start=(self.min_x, self.max_y, z),
                            size=(
                                self.rear_opening_min_x - self.min_x,
                                self.board_thickness,
                                height,
                            ),
                            color=self.decking_color,
                            cut_length=self.rear_opening_min_x - self.min_x,
                        ),
                        SidingPart(
                            name=f"{self.name}_rear_right_{index}",
                            material="composite_decking",
                            start=(self.rear_opening_max_x, self.max_y, z),
                            size=(
                                self.max_x - self.rear_opening_max_x,
                                self.board_thickness,
                                height,
                            ),
                            color=self.decking_color,
                            cut_length=self.max_x - self.rear_opening_max_x,
                        ),
                    )
                )

            parts.extend(course_parts)

        return tuple(parts)

    def _angle_parts(self) -> tuple[SidingPart, ...]:
        t = self.angle_thickness
        leg = self.angle_leg_width
        height = self.finished_top_z - self.bottom_z
        bottom = self.bottom_z
        outer_left = self.min_x - self.board_thickness
        outer_right = self.max_x + self.board_thickness
        outer_front = self.min_y - self.board_thickness
        outer_rear = self.max_y + self.board_thickness
        parts: list[SidingPart] = []

        def add_angle(
            name: str,
            plate_a_start: Vector3,
            plate_a_size: Vector3,
            plate_b_start: Vector3,
            plate_b_size: Vector3,
        ) -> None:
            parts.extend(
                (
                    SidingPart(
                        f"{self.name}_{name}_a",
                        "black_aluminum_angle",
                        plate_a_start,
                        plate_a_size,
                        self.angle_color,
                    ),
                    SidingPart(
                        f"{self.name}_{name}_b",
                        "black_aluminum_angle",
                        plate_b_start,
                        plate_b_size,
                        self.angle_color,
                    ),
                )
            )

        add_angle(
            "angle_front_left",
            (outer_left, outer_front - t, bottom),
            (leg, t, height),
            (outer_left - t, outer_front, bottom),
            (t, leg, height),
        )
        add_angle(
            "angle_front_right",
            (outer_right - leg, outer_front - t, bottom),
            (leg, t, height),
            (outer_right, outer_front, bottom),
            (t, leg, height),
        )
        add_angle(
            "angle_rear_left",
            (outer_left, outer_rear, bottom),
            (leg, t, height),
            (outer_left - t, outer_rear - leg, bottom),
            (t, leg, height),
        )
        add_angle(
            "angle_rear_right",
            (outer_right - leg, outer_rear, bottom),
            (leg, t, height),
            (outer_right, outer_rear - leg, bottom),
            (t, leg, height),
        )
        add_angle(
            "angle_tambour_left",
            (self.rear_opening_min_x - leg, outer_rear, bottom),
            (leg, t, height),
            (self.rear_opening_min_x, outer_rear - leg, bottom),
            (t, leg, height),
        )
        add_angle(
            "angle_tambour_right",
            (self.rear_opening_max_x, outer_rear, bottom),
            (leg, t, height),
            (self.rear_opening_max_x - t, outer_rear - leg, bottom),
            (t, leg, height),
        )
        opening_width = self.rear_opening_max_x - self.rear_opening_min_x
        parts.extend(
            (
                SidingPart(
                    f"{self.name}_angle_tambour_header_face",
                    "black_aluminum_angle",
                    (
                        self.rear_opening_min_x,
                        outer_rear,
                        self.rear_opening_top_z,
                    ),
                    (opening_width, t, leg),
                    self.angle_color,
                ),
                SidingPart(
                    f"{self.name}_angle_tambour_header_bottom",
                    "black_aluminum_angle",
                    (
                        self.rear_opening_min_x,
                        outer_rear - leg,
                        self.rear_opening_top_z - t,
                    ),
                    (opening_width, leg, t),
                    self.angle_color,
                ),
            )
        )
        return tuple(parts)

    @property
    def board_parts(self) -> tuple[SidingPart, ...]:
        return self._board_parts()

    @property
    def angle_parts(self) -> tuple[SidingPart, ...]:
        return self._angle_parts()

    @property
    def parts(self) -> tuple[SidingPart, ...]:
        return self.board_parts + self.angle_parts

    @property
    def cut_lengths(self) -> tuple[float, ...]:
        return tuple(
            part.cut_length
            for part in self.board_parts
            if part.cut_length is not None
        )

    def bom_rows(self) -> list[dict[str, Any]]:
        total_inches = sum(self.cut_lengths)
        angle_length = self.finished_top_z - self.bottom_z
        opening_angle_length = self.rear_opening_max_x - self.rear_opening_min_x
        return [
            {
                "category": "siding",
                "assembly": self.assembly,
                "name": f"{self.name}_composite_decking",
                "type": (
                    "composite decking "
                    f"{fmt_float(self.board_width)} x "
                    f"{fmt_float(self.board_thickness)} in"
                ),
                "qty": len(self.cut_lengths),
                "axis": "",
                "length_in": round(total_inches, 4),
                "length_display": inches_to_fraction_text(total_inches),
                "rotated": "",
                "start_x": "",
                "start_y": "",
                "start_z": "",
                "size_x": "",
                "size_y": "",
                "size_z": "",
                "start_cut_angle_deg": "",
                "end_cut_angle_deg": "",
                "total_linear_ft": round(total_inches / 12, 4),
                "stock_length_ft": round(self.stock_length / 12, 4),
                "stock_board_qty": minimum_stock_board_count(
                    self.cut_lengths, self.stock_length
                ),
            },
            {
                "category": "siding",
                "assembly": self.assembly,
                "name": f"{self.name}_corner_angles",
                "type": "1-1/4 in black aluminum angle",
                "qty": 6,
                "axis": "z",
                "length_in": round(angle_length, 4),
                "length_display": inches_to_fraction_text(angle_length),
                "rotated": "",
                "start_x": "",
                "start_y": "",
                "start_z": round(self.bottom_z, 4),
                "size_x": "",
                "size_y": "",
                "size_z": round(angle_length, 4),
                "start_cut_angle_deg": "",
                "end_cut_angle_deg": "",
                "total_linear_ft": round(6 * angle_length / 12, 4),
                "stock_length_ft": "",
                "stock_board_qty": "",
            },
            {
                "category": "siding",
                "assembly": self.assembly,
                "name": f"{self.name}_rear_opening_angle",
                "type": "1-1/4 in black aluminum angle",
                "qty": 1,
                "axis": "x",
                "length_in": round(opening_angle_length, 4),
                "length_display": inches_to_fraction_text(opening_angle_length),
                "rotated": "",
                "start_x": round(self.rear_opening_min_x, 4),
                "start_y": "",
                "start_z": round(self.rear_opening_top_z, 4),
                "size_x": round(opening_angle_length, 4),
                "size_y": "",
                "size_z": "",
                "start_cut_angle_deg": "",
                "end_cut_angle_deg": "",
                "total_linear_ft": round(opening_angle_length / 12, 4),
                "stock_length_ft": "",
                "stock_board_qty": "",
            },
        ]
