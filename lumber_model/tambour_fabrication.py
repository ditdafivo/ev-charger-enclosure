from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Literal

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildSketch,
    CenterArc,
    Compound,
    Cylinder,
    Line,
    Location,
    Locations,
    Part,
    Plane,
    Polygon,
    Rectangle,
    export_step,
    export_stl,
    extrude,
    sweep,
)


MM_PER_INCH = 25.4


def inches(value: float) -> float:
    return value * MM_PER_INCH


Handedness = Literal["left", "right", "common"]


@dataclass(frozen=True)
class TambourFabricationConfig:
    """Millimetre dimensions for the printable tambour components."""

    slat_depth: float = inches(0.5)
    slat_height: float = inches(0.75)
    slat_gap: float = inches(1 / 32)
    curtain_length: float = inches(44)
    bend_radius: float = inches(2.625)
    # Straight distance from the lower endpoint to the rear bend tangency.
    rear_vertical_length: float = inches(38.5)
    top_tangent_length: float = inches(10.375)
    front_vertical_length: float = inches(25.5)
    maximum_segment_length: float = 300.0
    bend_stub_length: float = 20.0
    loading_section_length: float = 100.0
    running_clearance: float = 0.5
    nozzle_width: float = 0.6
    wall_thickness: float = 2.4
    mounting_flange_thickness: float = 4.8
    flange_extension: float = 10.0
    slat_end_engagement: float = 12.0
    mounting_hole_diameter: float = 4.5
    expansion_slot_length: float = 8.0
    joint_expansion_gap: float = 0.6
    collar_clearance: float = 0.25
    collar_pad_depth: float = 1.6
    collar_pad_neck_width: float = 4.0
    collar_pad_head_width: float = 5.5
    collar_pad_height: float = 6.0
    collar_wall_thickness: float = 1.8
    collar_endpoint_inset: float = 3.0
    collar_retention_hole_diameter: float = 3.4
    collar_retention_head_diameter: float = 6.2
    heat_set_insert_diameter: float = 4.6
    heat_set_insert_depth: float = 4.0
    handle_width: float = 300.0
    handle_height: float = inches(0.75) - 1.0
    handle_projection: float = inches(0.625)
    swept_envelope_depth: float = inches(1.5)

    def __post_init__(self) -> None:
        positive_fields = (
            "slat_depth",
            "slat_height",
            "curtain_length",
            "bend_radius",
            "rear_vertical_length",
            "top_tangent_length",
            "front_vertical_length",
            "maximum_segment_length",
            "bend_stub_length",
            "loading_section_length",
            "running_clearance",
            "nozzle_width",
            "wall_thickness",
            "mounting_flange_thickness",
            "flange_extension",
            "slat_end_engagement",
            "mounting_hole_diameter",
            "joint_expansion_gap",
            "collar_clearance",
            "collar_pad_depth",
            "collar_pad_neck_width",
            "collar_pad_head_width",
            "collar_pad_height",
            "collar_wall_thickness",
            "collar_endpoint_inset",
            "collar_retention_hole_diameter",
            "collar_retention_head_diameter",
            "heat_set_insert_diameter",
            "heat_set_insert_depth",
            "handle_width",
            "handle_height",
            "handle_projection",
            "swept_envelope_depth",
        )
        for field_name in positive_fields:
            value = getattr(self, field_name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field_name} must be a finite positive number")
        if self.slat_gap < 0:
            raise ValueError("slat_gap cannot be negative")
        if self.wall_thickness < 4 * self.nozzle_width:
            raise ValueError("wall_thickness must be at least four nozzle widths")
        if self.collar_wall_thickness < 3 * self.nozzle_width:
            raise ValueError(
                "collar_wall_thickness must be at least three nozzle widths"
            )
        if self.collar_pad_head_width <= self.collar_pad_neck_width:
            raise ValueError("collar pad head must be wider than its neck")
        if self.heat_set_insert_depth >= self.mounting_flange_thickness:
            raise ValueError("heat-set insert must remain within the mounting flange")
        if self.handle_width > 350 or self.handle_height > 350:
            raise ValueError("handle must fit the 350 mm printer bed")
        if self.slat_depth + self.handle_projection > self.swept_envelope_depth:
            raise ValueError("slat and handle exceed the swept depth envelope")
        if self.bend_stub_length >= self.top_tangent_length / 2:
            raise ValueError("bend stubs leave no top straight track")
        if self.loading_section_length >= (
            self.rear_vertical_length - self.bend_stub_length
        ):
            raise ValueError("loading section leaves no fixed rear track")

    @property
    def slat_pitch(self) -> float:
        return self.slat_height + self.slat_gap

    @property
    def slat_count(self) -> int:
        return max(1, math.floor(self.curtain_length / self.slat_pitch))

    @property
    def channel_internal_width(self) -> float:
        return self.slat_depth + 2 * self.running_clearance

    @property
    def channel_outer_width(self) -> float:
        return self.channel_internal_width + 2 * self.wall_thickness

    @property
    def centerline_length(self) -> float:
        return (
            self.rear_vertical_length
            + self.top_tangent_length
            + self.front_vertical_length
            + math.pi * self.bend_radius
        )


@dataclass(frozen=True)
class TambourPart:
    name: str
    role: str
    handedness: Handedness
    shape: Part
    quantity: int = 1

    @property
    def size(self) -> tuple[float, float, float]:
        box = self.shape.bounding_box()
        return (box.size.X, box.size.Y, box.size.Z)

    def fits_bed(self, bed_size: float = 350.0) -> bool:
        return all(dimension <= bed_size for dimension in self.size)


def split_segment_lengths(length: float, maximum: float) -> tuple[float, ...]:
    if length <= 0 or maximum <= 0:
        raise ValueError("segment lengths must be positive")
    count = math.ceil(length / maximum)
    segment = length / count
    return tuple(segment for _ in range(count))


def _track_section(
    config: TambourFabricationConfig,
    plane: Plane,
) -> object:
    outer = config.channel_outer_width
    extension = config.flange_extension
    with BuildSketch(plane) as section:
        with Locations((-extension, 0)):
            Rectangle(
                outer + 2 * extension,
                config.mounting_flange_thickness,
                align=(Align.MIN, Align.MIN),
            )
        Rectangle(
            config.wall_thickness,
            config.slat_end_engagement,
            align=(Align.MIN, Align.MIN),
        )
        with Locations((outer - config.wall_thickness, 0)):
            Rectangle(
                config.wall_thickness,
                config.slat_end_engagement,
                align=(Align.MIN, Align.MIN),
            )
    return section.sketch


def _vertical_cylinder(
    x: float,
    y: float,
    diameter: float,
    height: float,
    z: float = -0.5,
) -> Part:
    return Location((x, y, z)) * Cylinder(
        diameter / 2,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def _slot_cutter(
    x: float,
    y: float,
    config: TambourFabricationConfig,
) -> Part:
    diameter = config.mounting_hole_diameter
    length = config.expansion_slot_length
    height = config.mounting_flange_thickness + 1
    cutter = _vertical_cylinder(x, y - (length - diameter) / 2, diameter, height)
    cutter += _vertical_cylinder(x, y + (length - diameter) / 2, diameter, height)
    cutter += Location((x, y, -0.5)) * Box(
        diameter,
        length - diameter,
        height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return cutter


def _dovetail_prism(
    base: tuple[float, float],
    outward: tuple[float, float],
    tangent: tuple[float, float],
    depth: float,
    neck_width: float,
    head_width: float,
    height: float,
    z: float,
) -> Part:
    """Create a wall-mounted dovetail rail that is constant along Z."""

    def point(distance: float, tangent_offset: float) -> tuple[float, float]:
        return (
            base[0] + outward[0] * distance + tangent[0] * tangent_offset,
            base[1] + outward[1] * distance + tangent[1] * tangent_offset,
        )

    with BuildSketch(Plane.XY) as profile:
        Polygon(
            point(0, -neck_width / 2),
            point(0, neck_width / 2),
            point(depth, head_width / 2),
            point(depth, -head_width / 2),
            align=(Align.NONE, Align.NONE),
        )
    return Location((0, 0, z)) * extrude(profile.sketch, amount=height)


def _add_joint_endpoint(
    result: Part,
    config: TambourFabricationConfig,
    tangent: tuple[float, float],
    wall_exteriors: tuple[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[tuple[float, float], tuple[float, float]],
    ],
) -> Part:
    """Add two exterior dovetails and insert pockets at a track endpoint."""

    for pad_base, outward in wall_exteriors:
        embedded_base = (
            pad_base[0] - outward[0] * 0.1,
            pad_base[1] - outward[1] * 0.1,
        )
        result += _dovetail_prism(
            embedded_base,
            outward,
            tangent,
            config.collar_pad_depth + 0.1,
            config.collar_pad_neck_width,
            config.collar_pad_head_width,
            config.collar_pad_height,
            config.mounting_flange_thickness,
        )
        insert_center = (
            pad_base[0] + outward[0] * 5.0,
            pad_base[1] + outward[1] * 5.0,
        )
        result -= _vertical_cylinder(
            insert_center[0],
            insert_center[1],
            config.heat_set_insert_diameter,
            config.heat_set_insert_depth + 0.1,
            z=config.mounting_flange_thickness - config.heat_set_insert_depth,
        )
    return result


def _section_plane(origin: tuple[float, float, float]) -> Plane:
    # Local section X follows the right-hand in-plane normal; local Y opens
    # toward the slat span. The path tangent is the plane normal.
    return Plane(origin=origin, x_dir=(-1, 0, 0), z_dir=(0, 1, 0))


def make_straight_track(
    length: float,
    config: TambourFabricationConfig,
) -> Part:
    if length <= 0 or length > config.maximum_segment_length:
        raise ValueError("straight track length is outside the printable range")
    start = (0.0, 0.0, 0.0)
    with BuildLine() as path:
        Line(start, (0, length, 0))
    result = sweep(
        _track_section(config, _section_plane(start)),
        path.line,
    )

    outer = config.channel_outer_width
    screw_x = (
        config.flange_extension / 2,
        -(outer + config.flange_extension / 2),
    )
    for x in screw_x:
        result -= _vertical_cylinder(
            x,
            length / 2,
            config.mounting_hole_diameter,
            config.mounting_flange_thickness + 1,
        )
        for y in (12.0, length - 12.0):
            result -= _slot_cutter(x, y, config)

    inset = config.collar_endpoint_inset
    for y in (inset, length - inset):
        result = _add_joint_endpoint(
            result,
            config,
            tangent=(0, 1),
            wall_exteriors=(
                ((0, y), (1, 0)),
                ((-outer, y), (-1, 0)),
            ),
        )
    return result


def make_bend_track(config: TambourFabricationConfig) -> Part:
    radius = config.bend_radius
    stub = config.bend_stub_length
    start = (0.0, -stub, 0.0)
    with BuildLine() as path:
        Line(start, (0, 0, 0))
        CenterArc((radius, 0, 0), radius, 180, -90)
        Line((radius, radius, 0), (radius + stub, radius, 0))
    result = sweep(
        _track_section(config, _section_plane(start)),
        path.line,
    )
    outer = config.channel_outer_width
    flange_offsets = (-config.flange_extension / 2, outer + config.flange_extension / 2)
    # The path turns clockwise. At the incoming stub local section X maps to
    # global -X; at the outgoing stub it maps to global +Y.
    for offset in flange_offsets:
        incoming_x = -offset
        outgoing_y = radius + offset
        result -= _vertical_cylinder(
            incoming_x,
            -stub / 2,
            config.mounting_hole_diameter,
            config.mounting_flange_thickness + 1,
        )
        result -= _vertical_cylinder(
            radius + stub / 2,
            outgoing_y,
            config.mounting_hole_diameter,
            config.mounting_flange_thickness + 1,
        )
    inset = config.collar_endpoint_inset
    result = _add_joint_endpoint(
        result,
        config,
        tangent=(0, 1),
        wall_exteriors=(
            ((0, -stub + inset), (1, 0)),
            ((-outer, -stub + inset), (-1, 0)),
        ),
    )
    result = _add_joint_endpoint(
        result,
        config,
        tangent=(1, 0),
        wall_exteriors=(
            ((radius + stub - inset, radius), (0, -1)),
            ((radius + stub - inset, radius + outer), (0, 1)),
        ),
    )
    return result


def make_joint_collar(config: TambourFabricationConfig) -> Part:
    """Create one external dovetail shoe; install two at every joint."""

    clearance = config.collar_clearance
    gap = config.joint_expansion_gap
    inset = config.collar_endpoint_inset
    wall = config.collar_wall_thickness
    pad_depth = config.collar_pad_depth
    pad_centers = (-(gap / 2 + inset), gap / 2 + inset)
    collar_length = (
        2 * (gap / 2 + inset)
        + config.collar_pad_head_width
        + 2 * wall
    )
    collar_depth = pad_depth + wall
    result = Location((collar_depth / 2, 0, 0)) * Box(
        collar_depth,
        collar_length,
        config.collar_pad_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # A foot rests on the mounting flange. Its recessed M3 screw retains the
    # shoe on one segment without placing hardware in the running channel.
    foot_depth = 7.0
    foot_thickness = 3.0
    retained_y = pad_centers[0]
    result += Location((foot_depth / 2, retained_y, 0)) * Box(
        foot_depth,
        config.collar_pad_head_width + 2 * wall,
        foot_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    for center_y in pad_centers:
        cavity = _dovetail_prism(
            (-0.1, center_y),
            (1, 0),
            (0, 1),
            pad_depth + clearance + 0.1,
            config.collar_pad_neck_width + 2 * clearance,
            config.collar_pad_head_width + 2 * clearance,
            config.collar_pad_height + 1,
            -0.5,
        )
        result -= cavity
    result -= _vertical_cylinder(
        5.0,
        retained_y,
        config.collar_retention_hole_diameter,
        foot_thickness + 1,
    )
    result -= _vertical_cylinder(
        5.0,
        retained_y,
        config.collar_retention_head_diameter,
        1.3,
        z=foot_thickness - 1.2,
    )
    return result


def make_joint_preview(config: TambourFabricationConfig) -> Compound:
    """Return two test stubs and both collars in their installed positions."""

    stub_length = 40.0
    gap = config.joint_expansion_gap
    seam_y = stub_length + gap / 2
    first = make_straight_track(stub_length, config)
    second = Location((0, stub_length + gap, 0)) * make_straight_track(
        stub_length, config
    )
    collar = make_joint_collar(config)
    first_collar = Location(
        (0, seam_y, config.mounting_flange_thickness)
    ) * collar
    second_collar = Location(
        (-config.channel_outer_width, seam_y, config.mounting_flange_thickness)
    ) * collar.mirror(Plane.YZ)
    return Compound([first, second, first_collar, second_collar])


def make_end_stop(config: TambourFabricationConfig) -> Part:
    internal = config.channel_internal_width
    insertion = 12.0
    result = Box(
        internal - 0.4,
        insertion,
        config.slat_end_engagement - config.mounting_flange_thickness,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    result += Location((0, 0, 0)) * Box(
        internal + 2 * config.wall_thickness,
        3.0,
        config.slat_end_engagement,
        align=(Align.CENTER, Align.MAX, Align.MIN),
    )
    # The open-bottom notch lets water and grit pass the lower endpoint while
    # leaving the upper bridge intact to stop the curtain.
    result -= Location((0, insertion / 2, 0)) * Box(
        4.0,
        insertion + 6.0,
        4.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return result


def make_handle(config: TambourFabricationConfig) -> Part:
    base_thickness = 3.0
    ledge_depth = config.handle_projection - base_thickness
    ledge_height = 6.0
    result = Box(
        config.handle_width,
        config.handle_height,
        base_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    result += Location((0, -config.handle_height / 2 + ledge_height / 2, 0)) * Box(
        config.handle_width,
        ledge_height,
        config.handle_projection,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for x in range(-120, 121, 40):
        result += Location((x, -config.handle_height / 2 + ledge_height, 0)) * Box(
            2.4,
            config.handle_height - ledge_height,
            ledge_depth,
            align=(Align.CENTER, Align.MIN, Align.MIN),
        )
        result -= _vertical_cylinder(x, 3.0, 4.5, base_thickness + 1)
        result -= _vertical_cylinder(x, 3.0, 8.5, 2.1, z=base_thickness - 2.0)
    return result


def make_clearance_coupon(
    clearance: float,
    config: TambourFabricationConfig,
) -> Part:
    coupon_config = TambourFabricationConfig(
        **{**config.__dict__, "running_clearance": clearance}
    )
    return make_straight_track(40.0, coupon_config)


def _handed(shape: Part, handedness: Handedness) -> Part:
    if handedness == "right":
        # Mirror the installed hand, then rotate it back onto its mounting
        # flange so both exports arrive in a support-free print orientation.
        return shape.mirror(Plane.XY).rotate(Axis.X, 180)
    return shape


def tambour_parts(
    config: TambourFabricationConfig = TambourFabricationConfig(),
) -> tuple[TambourPart, ...]:
    rear_straight = (
        config.rear_vertical_length
        - config.bend_stub_length
        - config.loading_section_length
    )
    top_straight = config.top_tangent_length - 2 * config.bend_stub_length
    front_straight = config.front_vertical_length - config.bend_stub_length
    runs = {
        "rear": split_segment_lengths(rear_straight, config.maximum_segment_length),
        "top": split_segment_lengths(top_straight, config.maximum_segment_length),
        "front": split_segment_lengths(front_straight, config.maximum_segment_length),
    }
    parts: list[TambourPart] = []
    for handedness in ("left", "right"):
        for run_name, lengths in runs.items():
            for index, length in enumerate(lengths, start=1):
                shape = _handed(make_straight_track(length, config), handedness)
                parts.append(
                    TambourPart(
                        f"{handedness}_{run_name}_straight_{index:02d}",
                        "track",
                        handedness,
                        shape,
                    )
                )
        bend = make_bend_track(config)
        for bend_name in ("rear", "front"):
            parts.append(
                TambourPart(
                    f"{handedness}_{bend_name}_bend",
                    "track",
                    handedness,
                    _handed(bend, handedness),
                )
            )
        parts.append(
            TambourPart(
                f"{handedness}_loading_section",
                "loading_section",
                handedness,
                _handed(
                    make_straight_track(config.loading_section_length, config),
                    handedness,
                ),
            )
        )
        parts.append(
            TambourPart(
                f"{handedness}_end_stop",
                "stop",
                handedness,
                _handed(make_end_stop(config), handedness),
            )
        )

    pieces_per_side = 1 + sum(len(lengths) for lengths in runs.values()) + 2
    joint_collar_quantity = 2 * 2 * (pieces_per_side - 1)
    parts.extend(
        (
            TambourPart(
                "joint_collar",
                "joiner",
                "common",
                make_joint_collar(config),
                quantity=joint_collar_quantity,
            ),
            TambourPart(
                "joint_test_track",
                "coupon",
                "common",
                make_straight_track(40.0, config),
                quantity=2,
            ),
            TambourPart(
                "pull_handle",
                "handle",
                "common",
                make_handle(config),
                quantity=2,
            ),
        )
    )
    for clearance in (0.3, 0.5, 0.7):
        parts.append(
            TambourPart(
                f"clearance_coupon_{clearance:.1f}mm",
                "coupon",
                "common",
                make_clearance_coupon(clearance, config),
            )
        )
    return tuple(parts)


def generate_tambour_fabrication(
    output_dir: Path,
    config: TambourFabricationConfig = TambourFabricationConfig(),
    part_name: str | None = None,
) -> tuple[Path, ...]:
    selected = [
        part
        for part in tambour_parts(config)
        if part_name is None or part.name == part_name
    ]
    if part_name is not None and not selected:
        raise KeyError(f"unknown tambour fabrication part: {part_name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for part in selected:
        if not part.shape.is_valid:
            raise ValueError(f"{part.name} is not a valid solid")
        if not part.fits_bed():
            raise ValueError(f"{part.name} does not fit a 350 mm print bed")
        step_path = output_dir / f"{part.name}.step"
        stl_path = output_dir / f"{part.name}.stl"
        export_step(part.shape, step_path)
        export_stl(part.shape, stl_path, tolerance=0.05, angular_tolerance=0.1)
        written.extend((step_path, stl_path))
    if part_name is None:
        manifest_rows = [
            {
                "name": part.name,
                "role": part.role,
                "handedness": part.handedness,
                "quantity": part.quantity,
                "size_x_mm": round(part.size[0], 3),
                "size_y_mm": round(part.size[1], 3),
                "size_z_mm": round(part.size[2], 3),
            }
            for part in selected
        ]
        csv_path = output_dir / "manifest.csv"
        json_path = output_dir / "manifest.json"
        with csv_path.open("w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=manifest_rows[0].keys())
            writer.writeheader()
            writer.writerows(manifest_rows)
        json_path.write_text(json.dumps(manifest_rows, indent=2) + "\n")
        preview_path = output_dir / "joint_fit_preview.step"
        export_step(make_joint_preview(config), preview_path)
        written.extend((csv_path, json_path, preview_path))
    return tuple(written)
