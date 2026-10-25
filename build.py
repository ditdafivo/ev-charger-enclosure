from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Sequence

from lumber_model import (
    CARLON_E980DFN_HUB_DEPTH,
    CARLON_E980DFN_OUTLET_BOX,
    CARLON_E989NNJ_JUNCTION_BOX,
    CARLON_E943E_MALE_TERMINAL_ADAPTER,
    CARLON_E987N_JUNCTION_BOX,
    CARLON_UA7AEB_BELL_END_45_ELBOW,
    EV_CHARGER_BODY,
    EV_CHARGER_PLUG,
    MOD_LIGHTING_BROOK_16,
    INTERMATIC_WP5100BL_IN_USE_COVER,
    ONE_INCH_CABLE_GLAND,
    WIFI_ACCESS_POINT,
    AbsoluteCoord,
    BoxFillCalculation,
    CableCollection,
    ComponentCollection,
    ComponentAnchor,
    ComponentType,
    CompositeSiding,
    ConduitBend,
    ConduitCollection,
    CONDUIT_OD_BY_TRADE_SIZE,
    Footing,
    GroundSurface,
    FrontSidingBore,
    LumberCollection,
    Model,
    PurchasedItem,
    RelativeCoord,
    RoutedSeat,
    RightSidingOpening,
    TambourBend,
    TambourCollection,
    TambourFabricationConfig,
    TambourInstalledDetails,
    generate_tambour_fabrication,
    cubic_bezier_conduit_points,
    cubic_bezier_points,
    clip_polygon_to_box,
    ev_charger_cable_points,
    parse_build_steps,
    rounded_cable_points,
    split_segment_lengths,
)
from lumber_model.components import (
    MALE_TERMINAL_ADAPTERS, SEALING_WASHERS, FITTING_LOCKNUTS,
    MALE_FITTING_WALL_OFFSET,
)
from lumber_model.gusset import (
    GUSSET_FASTENER_COUNT,
    GUSSET_MATERIAL,
    GUSSET_SCREW_HEAD_HEIGHT_IN,
    GUSSET_SIZE_IN,
    GUSSET_THICKNESS_IN,
    pan_head_cylinder_primitives,
)
from lumber_model.gusset_dxf import generate_gusset_dxf
from lumber_model.us135 import US135Siding, US135_THICKNESS, ROOF_STRIP_THICKNESS

DEFAULT_WIDTH = 24
DEFAULT_DEPTH = 19.375
DEFAULT_HEIGHT = 49.625
# Vertical ground-to-level-post-top survey at each post's OUTSIDE corner.
POST_GROUND_TO_TOP = {
    "post_br": 47.0,
    "post_bl": 48.5,
    "post_fl": 49.625,
    "post_fr": 49.25,
}
BUILD_STEPS_PATH = Path(__file__).with_name("BUILD_STEPS.md")
BUILD_STEPS = parse_build_steps(BUILD_STEPS_PATH)
DEFERRED_OBJECT_NAMES = (
    "rail_ltam",
    "rail_rtam",
    "rail_ltam_upper",
    "rail_rtam_upper",
    "left_tambour_upper_backing",
    "right_tambour_upper_backing",
    "left_tambour_vertical_backing",
    "right_tambour_vertical_backing",
    "left_tambour_bend_backer",
    "right_tambour_bend_backer",
    "tambour_ceiling_panel",
    "enclosure_tambour_track",
    "enclosure_tambour_door",
)
PLAYGROUND_MODEL_URL = "https://ditdafivo.github.io/ev-charger-enclosure/"
PLAYGROUND_DEPLOY_BRANCH = "pages-source"
PLAYGROUND_DEPLOY_PATH = "pages/model.scad"
PLAYGROUND_REMOTE = "origin"
LOCAL_MESH_PATH = "../assets/components/ev_charger_plug/ev_charger_plug.stl"
PLAYGROUND_MESH_PATH = "ev_charger_plug.stl"
LOCAL_CHARGER_BODY_MESH_PATH = (
    "../assets/components/wallbox_pulsar_plus/wallbox_pulsar_plus_body.stl"
)
PLAYGROUND_CHARGER_BODY_MESH_PATH = "wallbox_pulsar_plus_body.stl"
PLAYGROUND_MESH_PATHS = {
    LOCAL_MESH_PATH: PLAYGROUND_MESH_PATH,
    LOCAL_CHARGER_BODY_MESH_PATH: PLAYGROUND_CHARGER_BODY_MESH_PATH,
}


@dataclass(frozen=True)
class EnclosureBuild:
    """A complete enclosure model and the geometry used to construct it."""

    width: float
    depth: float
    height: float
    members: LumberCollection
    components: ComponentCollection
    conduits: ConduitCollection
    cables: CableCollection
    grounds: list[GroundSurface]
    footings: list[Footing]
    tambours: TambourCollection
    siding: CompositeSiding
    routed_seats: tuple[RoutedSeat, ...]
    model: Model
    anchors: dict[str, Any]

    def __getattr__(self, name: str) -> Any:
        try:
            return self.anchors[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def _finite_positive_dimension(value: float, name: str) -> float:
    dimension = float(value)
    if not math.isfinite(dimension) or dimension <= 0:
        raise ValueError(f"{name} must be a finite positive number, got {value!r}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return dimension


def build_enclosure(
    width: float = DEFAULT_WIDTH,
    depth: float = DEFAULT_DEPTH,
    height: float = DEFAULT_HEIGHT,
) -> EnclosureBuild:
    """Build an enclosure for the requested post centerline spacing, in inches."""

    width = _finite_positive_dimension(width, "width")
    depth = _finite_positive_dimension(depth, "depth")
    height = _finite_positive_dimension(height, "height")
    # The installed brace fits between the posts, flush with their level tops.
    FRAME_DIMS=AbsoluteCoord(width, depth, height)
    BURIED_FRAME_Z=32
    FULL_POST_LEN=BURIED_FRAME_Z+height
    SIDING_BOTTOM_Z=0.75
    SIDING_STOCK_LENGTH_FT=8
    # Boards seat directly on the open lumber framing.
    SIDING_BOARD_THICKNESS=US135_THICKNESS
    TAMBOUR_DOOR_COLOR=(0.10, 0.12, 0.14, 1.0)

    HEIGHT_2x4=1.5
    HALF_HEIGHT_2x4=HEIGHT_2x4/2
    HEIGHT_1X_BOARD=0.75
    HALF_HEIGHT_1X_BOARD=HEIGHT_1X_BOARD/2
    WIDTH_4x4=3.5

    members = LumberCollection()

    for name, x, y in (
        ("post_fl", 0, 0),
        ("post_fr", FRAME_DIMS.x, 0),
        ("post_bl", 0, FRAME_DIMS.y),
        ("post_br", FRAME_DIMS.x, FRAME_DIMS.y),
    ):
        members.add(
            name,
            assembly="posts",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(x, y, -BURIED_FRAME_Z),
            length=FULL_POST_LEN,
        )

    def _member_relative_coord(
        reference: str,
        x: float,
        y: float,
        z: float,
    ) -> RelativeCoord:
        member = members[reference]
        return RelativeCoord(
            reference,
            x-member.start[0],
            y-member.start[1],
            z-member.start[2],
        )


    for name,support_a,support_b,lumber_type in [
        ("brace_fl_fr","post_fl","post_fr", "2x4"),
        ("brace_fl_bl","post_fl","post_bl", "4x4"),
        ("brace_bl_br","post_bl","post_br", "2x4"),
        ("brace_fr_br","post_fr","post_br", "4x4"),
    ]:
        members.between(
            name,
            assembly="frame",
            type=lumber_type,
            support_a=support_a,
            support_b=support_b,
            position=(
                FRAME_DIMS.z-WIDTH_4x4/2
                if lumber_type == "4x4"
                else FRAME_DIMS.z-HALF_HEIGHT_2x4
            ),
        )

    members.diagonal_between(
        "brace_bl_fr",
        assembly="frame",
        type="1x6",
        support_a="post_bl",
        support_b="post_fr",
        position=FRAME_DIMS.z-HALF_HEIGHT_1X_BOARD,
        fit_between_support_faces="y",
    )

    diagonal = members["brace_bl_fr"]
    diagonal_unit = (
        (diagonal.end[0]-diagonal.start[0])/diagonal.length,
        (diagonal.end[1]-diagonal.start[1])/diagonal.length,
    )
    diagonal_normal = (-diagonal_unit[1], diagonal_unit[0])
    diagonal_footprint = diagonal.footprint
    if diagonal_footprint is None:
        raise ValueError("brace_bl_fr: expected a profiled diagonal footprint")
    routed_seats = tuple(
        RoutedSeat(
            name=f"route_{member_name}_for_brace_bl_fr",
            member=member_name,
            polygon=clip_polygon_to_box(
                diagonal_footprint,
                min_x=members[member_name].min_on("x"),
                max_x=members[member_name].max_on("x"),
                min_y=members[member_name].min_on("y"),
                max_y=members[member_name].max_on("y"),
            ),
            depth=diagonal.thickness,
            top_z=FRAME_DIMS.z,
        )
        for member_name in (
            "brace_fl_bl",
            "brace_fr_br",
        )
    )

    # Increasing the default frame depth by one inch moves depth-centered
    # supports rearward by one-half inch. Add the remaining one-half inch here
    # so the center-rail assembly moves exactly one inch in world Y.
    CENTER_RAIL_DEPTH_CORRECTION=0.5
    CENTER_RAIL_OFFSET=-3+CENTER_RAIL_DEPTH_CORRECTION
    # Keep the top guide/support assembly below the perimeter braces.  The
    # swept envelope is asymmetric about the groove centerline: the handle is
    # proud of the outward slat face, while webbing and its fastener heads are
    # on the inward face.
    TAMBOUR_MAX_ENVELOPE_DEPTH=1.5
    TAMBOUR_SLAT_DEPTH=0.5
    TAMBOUR_SLAT_HEIGHT=0.75
    TAMBOUR_SLAT_GAP=1/32
    TAMBOUR_SLAT_PITCH=TAMBOUR_SLAT_HEIGHT+TAMBOUR_SLAT_GAP
    TAMBOUR_FABRICATION=TambourFabricationConfig()
    MM_PER_INCH=25.4
    TAMBOUR_TRACK_FOOTPRINT_WIDTH=(
        TAMBOUR_FABRICATION.channel_internal_width
        +2*TAMBOUR_FABRICATION.wall_thickness
        +2*TAMBOUR_FABRICATION.flange_extension
    )/MM_PER_INCH
    TAMBOUR_TRACK_SUPPORT_EDGE_MARGIN=(
        TAMBOUR_FABRICATION.minimum_backing_width/MM_PER_INCH-TAMBOUR_TRACK_FOOTPRINT_WIDTH
    )/2
    if TAMBOUR_TRACK_SUPPORT_EDGE_MARGIN < 1/16:
        raise ValueError("tambour track leaves less than 1/16 inch support margin")
    TAMBOUR_OUTWARD_ENVELOPE_DEPTH=(
        TAMBOUR_SLAT_DEPTH/2
        +TAMBOUR_FABRICATION.handle_projection/MM_PER_INCH
    )
    TAMBOUR_INWARD_ENVELOPE_DEPTH=(
        TAMBOUR_SLAT_DEPTH/2
        +TAMBOUR_FABRICATION.inward_hardware_projection/MM_PER_INCH
    )
    if (
        TAMBOUR_OUTWARD_ENVELOPE_DEPTH+TAMBOUR_INWARD_ENVELOPE_DEPTH
        > TAMBOUR_MAX_ENVELOPE_DEPTH
    ):
        raise ValueError("tambour hardware exceeds the 1.5-inch swept envelope")
    TAMBOUR_BRACE_CLEARANCE=0.25
    TAMBOUR_TOP_OFFSET=(
        HEIGHT_2x4+TAMBOUR_BRACE_CLEARANCE+TAMBOUR_OUTWARD_ENVELOPE_DEPTH
    )
    TAMBOUR_TOP_Z=FRAME_DIMS.z-TAMBOUR_TOP_OFFSET
    TAMBOUR_TRACK_BACK_Y=members["post_bl"].max_on("y")-0.875
    TAMBOUR_BACK_BOTTOM_Z=3
    TAMBOUR_FRONT_BOTTOM_Z=16
    TAMBOUR_BEND_RADIUS=TAMBOUR_FABRICATION.bend_radius/MM_PER_INCH

    # Retain the established tambour clearance datum after removing the old
    # light backers. New hardware must fit forward of this reserved plane.
    FRONT_STREET_LIGHT_BOX_FACE_Y=-SIDING_BOARD_THICKNESS
    FRONT_ELECTRICAL_CLEARANCE_REAR_Y=3.8
    TAMBOUR_PLACEMENT_INCREMENT=1/8
    TAMBOUR_MINIMUM_TRACK_FRONT_Y=(
        FRONT_ELECTRICAL_CLEARANCE_REAR_Y
        +TAMBOUR_OUTWARD_ENVELOPE_DEPTH
        +TAMBOUR_BRACE_CLEARANCE
    )
    TAMBOUR_TRACK_FRONT_Y=(
        math.ceil(
            TAMBOUR_MINIMUM_TRACK_FRONT_Y/TAMBOUR_PLACEMENT_INCREMENT-1e-9
        )
        *TAMBOUR_PLACEMENT_INCREMENT
    )
    TAMBOUR_FRONT_Y=TAMBOUR_TRACK_FRONT_Y
    TAMBOUR_VERTICAL_SUPPORT_CENTER_Y=TAMBOUR_TRACK_FRONT_Y
    # Track points are the center of the running groove.  The detailed slats
    # must share that datum rather than riding on one of the groove walls.
    TAMBOUR_SLAT_TRACK_OFFSET=0
    TAMBOUR_TRACK_TOP_Z=TAMBOUR_TOP_Z
    TAMBOUR_FRONT_HEADER_TOP_Z=TAMBOUR_TOP_Z-2
    TAMBOUR_FRONT_HEADER_CENTER_Z=(
        TAMBOUR_FRONT_HEADER_TOP_Z-HEIGHT_2x4/2
    )
    TAMBOUR_FRONT_HEADER_CENTER_Y=(
        members["brace_fl_bl"].center_on("y")+CENTER_RAIL_OFFSET
    )
    RAIL_UPPER_CENTER_Z=13
    # The original right lower rail was centered at z=7. Lower both side rails
    # and their front cross rail by one inch to create the junction-box seat.
    RAIL_LOWER_CENTER_Z=6
    for name,support_a,support_b,position,cross_offset,position_axis,rotated in [
        (
            "rail_rbl",
            "post_fr",
            "post_br",
            RAIL_LOWER_CENTER_Z,
            0,
            None,
            True,
        ),
        (
            "rail_lbu",
            "post_fl",
            "post_bl",
            RAIL_UPPER_CENTER_Z,
            0,
            None,
            True,
        ),
        (
            "rail_rbu",
            "post_fr",
            "post_br",
            RAIL_UPPER_CENTER_Z,
            0,
            None,
            True,
        ),
        (
            "rail_lbl",
            "post_fl",
            "post_bl",
            RAIL_LOWER_CENTER_Z,
            0,
            None,
            True,
        ),
        (
            "rail_fbu",
            "rail_lbu",
            "rail_rbu",
            RAIL_UPPER_CENTER_Z,
            CENTER_RAIL_OFFSET,
            None,
            True,
        ),
    ]:
        members.between(
            name,
            assembly="frame",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=position,
            cross_offset=cross_offset,
            position_axis=position_axis,
            rotated=rotated,
        )

    members.between(
        "rail_fbl",
        assembly="frame",
        type="2x4",
        support_a="rail_lbl",
        support_b="rail_rbl",
        position=RAIL_LOWER_CENTER_Z,
        cross_offset=CENTER_RAIL_OFFSET,
        rotated=True,
    )

    for name,support_a,support_b,position,position_axis in [
        (
            "rail_lt",
            "post_fl",
            "post_bl",
            TAMBOUR_FRONT_HEADER_CENTER_Z,
            None,
        ),
        (
            "rail_rt",
            "post_fr",
            "post_br",
            TAMBOUR_FRONT_HEADER_CENTER_Z,
            None,
        ),
    ]:
        members.between(
            name,
            assembly="frame",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=position,
            position_axis=position_axis,
            rotated=True,
        )

    tambour_support_overlap_center_y=(
        max(
            members["brace_fl_bl"].min_on("y"),
            members["rail_lbu"].min_on("y"),
        )
        +min(
            members["brace_fl_bl"].max_on("y"),
            members["rail_lbu"].max_on("y"),
        )
    )/2
    tambour_support_cross_offset=(
        TAMBOUR_VERTICAL_SUPPORT_CENTER_Y-tambour_support_overlap_center_y
    )
    for name,support_a,support_b,position in (
        (
            "rail_ltam",
            "rail_lt",
            "rail_lbu",
            members["post_fl"].center_on("x"),
        ),
        (
            "rail_rtam",
            "rail_rt",
            "rail_rbu",
            members["post_fr"].center_on("x"),
        ),
    ):
        members.between(
            name,
            assembly="tambour_supports",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=position,
            cross_offset=tambour_support_cross_offset,
            rotated=True,
        )

    # Future guide supports stop at the permanent side rails. Keep those
    # load-carrying rails intact and use separate blocks above them.
    for name, lower, upper, post in (
        ("rail_ltam_upper", "rail_lt", "brace_fl_bl", "post_fl"),
        ("rail_rtam_upper", "rail_rt", "brace_fr_br", "post_fr"),
    ):
        members.between(
            name,
            assembly="tambour_supports",
            type="2x4",
            support_a=lower,
            support_b=upper,
            position=members[post].center_on("x"),
            cross_offset=tambour_support_cross_offset,
            rotated=True,
        )

    header_support_overlap_center_y=(
        max(members["rail_lt"].min_on("y"), members["rail_rt"].min_on("y"))
        +min(members["rail_lt"].max_on("y"), members["rail_rt"].max_on("y"))
    )/2
    members.between(
        "rail_ft",
        assembly="frame",
        type="2x4",
        support_a="rail_lt",
        support_b="rail_rt",
        position=TAMBOUR_FRONT_HEADER_CENTER_Z,
        cross_offset=(
            TAMBOUR_FRONT_HEADER_CENTER_Y-header_support_overlap_center_y
        ),
        rotated=True,
    )
    members.between(
        "front_center_rail",
        assembly="frame",
        type="2x4",
        support_a="rail_fbu",
        support_b="rail_ft",
        position=(WIDTH_4x4+FRAME_DIMS.x)/2,
        rotated=False,
    )
    members.between(
        "right_center_rail",
        assembly="frame",
        type="2x4",
        support_a="rail_rbu",
        support_b="rail_rt",
        position=(WIDTH_4x4+FRAME_DIMS.y)/2+CENTER_RAIL_DEPTH_CORRECTION,
        position_axis="y",
        rotated=True,
    )

    BACK_RIGHT_OUTLET_REAR_OFFSET=1.5
    BACK_RIGHT_OUTLET_CENTER_Y=(
        members["post_br"].min_on("y") - BACK_RIGHT_OUTLET_REAR_OFFSET
    )
    BACK_RIGHT_OUTLET_CENTER_Z=18
    BACK_RIGHT_OUTLET_FACE_PROJECTION=0.25
    BACK_RIGHT_OUTLET_MOUNT_SPACING=5.24
    BACK_RIGHT_OUTLET_FACE_X=(
        FRAME_DIMS.x
        + WIDTH_4x4
        + SIDING_BOARD_THICKNESS
        + BACK_RIGHT_OUTLET_FACE_PROJECTION
    )
    BACK_RIGHT_OUTLET_BACK_X=(
        BACK_RIGHT_OUTLET_FACE_X - CARLON_E980DFN_OUTLET_BOX.size[2]
    )
    BACK_RIGHT_OUTLET_BACKER_CROSS_OFFSET=(
        BACK_RIGHT_OUTLET_BACK_X
        - (FRAME_DIMS.x + WIDTH_4x4 / 2)
        - HEIGHT_2x4 / 2
    )

    for name,position in [
        (
            "back_right_outlet_backer_lower",
            BACK_RIGHT_OUTLET_CENTER_Z - BACK_RIGHT_OUTLET_MOUNT_SPACING / 2,
        ),
        (
            "back_right_outlet_backer_upper",
            BACK_RIGHT_OUTLET_CENTER_Z + BACK_RIGHT_OUTLET_MOUNT_SPACING / 2,
        ),
    ]:
        members.between(
            name,
            assembly="electrical_backing",
            type="2x4",
            support_a="right_center_rail",
            support_b="post_br",
            position=position,
            cross_offset=BACK_RIGHT_OUTLET_BACKER_CROSS_OFFSET,
            rotated=False,
        )

    BACK_RIGHT_OUTLET_CONDUIT_ENTRY=_member_relative_coord(
        "post_br",
        BACK_RIGHT_OUTLET_BACK_X + CARLON_E980DFN_HUB_DEPTH,
        BACK_RIGHT_OUTLET_CENTER_Y,
        BACK_RIGHT_OUTLET_CENTER_Z - CARLON_E980DFN_OUTLET_BOX.size[0] / 2,
    )
    BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT=(
        BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(members)
    )
    BACK_RIGHT_OUTLET_SIDING_OPENING=RightSidingOpening(
        "back_right_outlet",
        min_y=BACK_RIGHT_OUTLET_CENTER_Y-CARLON_E980DFN_OUTLET_BOX.size[1]/2,
        max_y=BACK_RIGHT_OUTLET_CENTER_Y+CARLON_E980DFN_OUTLET_BOX.size[1]/2,
        bottom_z=BACK_RIGHT_OUTLET_CENTER_Z-CARLON_E980DFN_OUTLET_BOX.size[0]/2,
        top_z=BACK_RIGHT_OUTLET_CENTER_Z+CARLON_E980DFN_OUTLET_BOX.size[0]/2,
    )

    FRONT_STREET_LIGHT_CENTER_X=(FRAME_DIMS.x + WIDTH_4x4) / 2
    FRONT_STREET_LIGHT_CENTER_Z=members["brace_fl_fr"].min_on("z")+0.5
    FRONT_STREET_LIGHT_CABLE_Z=members["brace_fl_fr"].min_on("z")-0.375
    FRONT_STREET_LIGHT_SIDING_BORE=FrontSidingBore(
        "front_street_light", FRONT_STREET_LIGHT_CENTER_X,
        FRONT_STREET_LIGHT_CABLE_Z, 0.5,
    )
    # Retain the former conduit corridor up the inside of the front-right post.
    FRONT_LIGHT_ROUTE_X=members["post_fr"].min_on("x")-0.8
    FRONT_LIGHT_ROUTE_Y=2.35
    FRONT_ADDRESS_CENTER_Z=FRONT_STREET_LIGHT_CENTER_Z-1.2-3-2.5
    members.add(
        "front_address_number_support", assembly="electrical_backing",
        type="5/4x6", axis="x", rotated=False,
        start=AbsoluteCoord(members["post_fl"].max_on("x"), 0, FRONT_ADDRESS_CENTER_Z-2.75),
        length=members["post_fr"].min_on("x")-members["post_fl"].max_on("x"),
    )

    grounds = [
        GroundSurface(
            "ground",
            corners=tuple(
                AbsoluteCoord(x, y, POST_GROUND_TO_TOP["post_fl"]-POST_GROUND_TO_TOP[name])
                for name, x, y in (
                    ("post_fl", 0, 0),
                    ("post_fr", width+WIDTH_4x4, 0),
                    ("post_br", width+WIDTH_4x4, depth+WIDTH_4x4),
                    ("post_bl", 0, depth+WIDTH_4x4),
                )
            ),
            center=AbsoluteCoord((width+WIDTH_4x4)/2, (depth+WIDTH_4x4)/2, 0),
            radius=48,
        )
    ]

    FOOTING_DIAMETER=10
    FOOTING_BOTTOM_Z=-36
    footings = [
        Footing(
            f"footing_{post_name.removeprefix('post_')}",
            center=RelativeCoord(
                post_name,
                WIDTH_4x4/2,
                WIDTH_4x4/2,
                0,
            ),
            diameter=FOOTING_DIAMETER,
            bottom_z=FOOTING_BOTTOM_Z,
            top_z=grounds[0].resolved(members).z_at(
                members[post_name].center_on("x"),
                members[post_name].center_on("y"),
            ),
        )
        for post_name in ("post_fl", "post_fr", "post_bl", "post_br")
    ]

    POWER_JUNCTION_RIGHT_SHIFT=0
    POWER_JUNCTION_X=(
        members["front_center_rail"].center_on("x")
        + 1.25
        + POWER_JUNCTION_RIGHT_SHIFT
    )
    POWER_JUNCTION_Y_SHIFT=0
    POWER_JUNCTION_PORT_Y=(
        members["front_center_rail"].min_on("y")
        - 1
        + POWER_JUNCTION_Y_SHIFT
    )
    # Keep the box at its previous elevation while translating it in X and Y.
    # Preserve the original ground reference so the requested X translation
    # does not also change the box or its outlet elevations on sloping grade.
    POWER_JUNCTION_GROUND_REFERENCE_X=(
        members["front_center_rail"].center_on("x")+4.25
    )
    POWER_JUNCTION_GROUND_REFERENCE_Y=(
        POWER_JUNCTION_PORT_Y-POWER_JUNCTION_Y_SHIFT
    )
    POWER_JUNCTION_GROUND_Z=grounds[0].resolved(members).z_at(
        POWER_JUNCTION_GROUND_REFERENCE_X,
        POWER_JUNCTION_GROUND_REFERENCE_Y,
    )
    POWER_JUNCTION_BOTTOM_Z=POWER_JUNCTION_GROUND_Z+6
    POWER_JUNCTION_TOP_Z=(
        POWER_JUNCTION_BOTTOM_Z + CARLON_E987N_JUNCTION_BOX.size[0]
    )
    POWER_JUNCTION_CENTER_Z=(POWER_JUNCTION_BOTTOM_Z+POWER_JUNCTION_TOP_Z)/2
    POWER_JUNCTION_CENTER_Y=(
        members["front_center_rail"].min_on("y")
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
        + POWER_JUNCTION_Y_SHIFT
    )
    POWER_JUNCTION_RIGHT_X=(
        POWER_JUNCTION_X + CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    POWER_JUNCTION_LIGHT_PORT_Y=(POWER_JUNCTION_PORT_Y-2)
    POWER_JUNCTION_LIGHT_PORT_Z=POWER_JUNCTION_CENTER_Z
    POWER_UF_CABLE_DIAMETER=0.45  # Schematic circular envelope for flat UF-B.
    # Preserve the former conduit centerline and connector clearance at the box.
    POWER_OUTLET_HORIZONTAL_RUN_Z=(
        members["rail_rbl"].max_on("z")
        + CONDUIT_OD_BY_TRADE_SIZE["1/2"]/2
    )
    POWER_JUNCTION_OUTLET_PORT_Z=POWER_OUTLET_HORIZONTAL_RUN_Z

    POWER_JUNCTION_BOX_FILL=BoxFillCalculation(
        marked_volume=49,
        conductor_groups=((12, 5), (14, 2)),
        equipment_grounding_awgs=(12, 12, 14),
    )
    POWER_JUNCTION_BOX_FILL.validate()

    LOW_VOLTAGE_RISER_X=14
    # Keep the default installed riser at y=6.25 while preserving the same
    # bottom-entry setback when the enclosure depth is parameterized.
    LOW_VOLTAGE_RISER_Y=members["rail_fbu"].min_on("y")-0.9375
    LOW_VOLTAGE_GROUND_Z=grounds[0].resolved(members).z_at(
        LOW_VOLTAGE_RISER_X,
        LOW_VOLTAGE_RISER_Y,
    )
    LOW_VOLTAGE_ELBOW_RADIUS=4.5
    LOW_VOLTAGE_ELBOW_SOCKET_DEPTH=1.5
    LOW_VOLTAGE_ELBOW_ANGLE=math.radians(45)
    LOW_VOLTAGE_ELBOW_SIN=math.sin(LOW_VOLTAGE_ELBOW_ANGLE)
    LOW_VOLTAGE_ELBOW_COS=math.cos(LOW_VOLTAGE_ELBOW_ANGLE)
    LOW_VOLTAGE_ELBOW_SPIGOT_LENGTH=1.0
    # The paired elbows end on a vertical axis offset toward negative X.
    LOW_VOLTAGE_ELBOW_OUTLET_X=(
        LOW_VOLTAGE_RISER_X
        - 2*LOW_VOLTAGE_ELBOW_RADIUS*(1-LOW_VOLTAGE_ELBOW_COS)
        - LOW_VOLTAGE_ELBOW_SPIGOT_LENGTH*LOW_VOLTAGE_ELBOW_SIN
    )
    LOW_VOLTAGE_ELBOW_OUTLET_Z=(
        LOW_VOLTAGE_GROUND_Z+LOW_VOLTAGE_ELBOW_SOCKET_DEPTH
        + 2*LOW_VOLTAGE_ELBOW_RADIUS*LOW_VOLTAGE_ELBOW_SIN
        + LOW_VOLTAGE_ELBOW_SPIGOT_LENGTH*(1+LOW_VOLTAGE_ELBOW_COS)
    )
    LOW_VOLTAGE_BOX_CENTER_X=LOW_VOLTAGE_ELBOW_OUTLET_X
    LOW_VOLTAGE_BOX_CENTER_Y=(
        members["rail_fbu"].min_on("y")
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    LOW_VOLTAGE_BOX_BOTTOM_Z=(
        LOW_VOLTAGE_ELBOW_OUTLET_Z
        + CARLON_E943E_MALE_TERMINAL_ADAPTER.size[0]
    )
    LOW_VOLTAGE_BOX_CENTER_Z=(
        LOW_VOLTAGE_BOX_BOTTOM_Z+CARLON_E987N_JUNCTION_BOX.size[0]/2
    )
    LOW_VOLTAGE_BOX_FRONT_SETBACK=(
        LOW_VOLTAGE_BOX_CENTER_Y
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
        - members["post_fr"].min_on("y")
    )
    LOW_VOLTAGE_PORT_EDGE_CLEARANCE=0.75
    # The elbow outlet fixes the bottom entry behind the box center. The three
    # smaller cable-gland openings remain on the front row.
    LOW_VOLTAGE_INPUT_X=LOW_VOLTAGE_BOX_CENTER_X
    LOW_VOLTAGE_INPUT_Y=LOW_VOLTAGE_RISER_Y
    LOW_VOLTAGE_CONDUIT_RADIUS=CONDUIT_OD_BY_TRADE_SIZE["3/4"]/2
    LOW_VOLTAGE_FOOTING_CLEARANCE_RADIUS=(
        FOOTING_DIAMETER/2+LOW_VOLTAGE_CONDUIT_RADIUS
    )
    LOW_VOLTAGE_GLAND_Y=(
        LOW_VOLTAGE_BOX_CENTER_Y
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
        + LOW_VOLTAGE_PORT_EDGE_CLEARANCE
    )
    LOW_VOLTAGE_GLAND_SPACING=1.2
    LOW_VOLTAGE_GLAND_XS=tuple(
        LOW_VOLTAGE_BOX_CENTER_X + index*LOW_VOLTAGE_GLAND_SPACING
        for index in (-1, 0, 1)
    )
    LOW_VOLTAGE_CABLE_DIAMETER=1/8
    LOW_VOLTAGE_MINIMUM_BEND_RADIUS=5*LOW_VOLTAGE_CABLE_DIAMETER
    LOW_VOLTAGE_CAT6_COLOR=(0.05, 0.2, 0.8, 1.0)

    components = ComponentCollection()

    TAMBOUR_FRONT_BEND_BACKER_THICKNESS=0.75
    TAMBOUR_FRONT_BEND_BACKER_LENGTH=TAMBOUR_FABRICATION.minimum_backing_width/MM_PER_INCH
    TAMBOUR_FRONT_BEND_BACKER_BOTTOM_Z=max(
        members["rail_lt"].max_on("z"),
        members["rail_rt"].max_on("z"),
    )
    TAMBOUR_FRONT_BEND_BACKER_TOP_Z=min(
        members["brace_fl_bl"].min_on("z"),
        members["brace_fr_br"].min_on("z"),
    )
    TAMBOUR_FRONT_BEND_BACKER_HEIGHT=(
        TAMBOUR_FRONT_BEND_BACKER_TOP_Z
        -TAMBOUR_FRONT_BEND_BACKER_BOTTOM_Z
    )
    if TAMBOUR_FRONT_BEND_BACKER_HEIGHT <= 0:
        raise ValueError("tambour bend backers have no space above the side rails")
    tambour_bend_backer_type=ComponentType(
        name="three_quarter_inch_plywood_tambour_bend_backer",
        size=(
            TAMBOUR_FRONT_BEND_BACKER_HEIGHT,
            TAMBOUR_FRONT_BEND_BACKER_THICKNESS,
            TAMBOUR_FRONT_BEND_BACKER_LENGTH,
        ),
        color=(0.72, 0.58, 0.38, 1.0),
        default_face="narrow_pos",
        mount_point=(0, 0, 0),
    )
    for name,rail_name,minimum_x in (
        (
            "left_tambour_bend_backer",
            "rail_ltam_upper",
            members["rail_ltam_upper"].max_on("x")
            -TAMBOUR_FRONT_BEND_BACKER_THICKNESS,
        ),
        (
            "right_tambour_bend_backer",
            "rail_rtam_upper",
            members["rail_rtam_upper"].min_on("x"),
        ),
    ):
        rail=members[rail_name]
        components.add(
            name,
            assembly="tambour_supports",
            component_type=tambour_bend_backer_type,
            member=rail_name,
            at=TAMBOUR_FRONT_BEND_BACKER_BOTTOM_Z-rail.min_on("z"),
            face="narrow_pos",
            offset=(0, minimum_x-rail.center_on("x"), -1/8),
        )

    # Recess the 3/4-inch plywood facing into each front rail so its inside
    # face retains the track datum. The facing extends 1/8 inch on both edges.
    for side, rail_name, backing_name in (
        ("left", "rail_ltam", "left_tambour_vertical_backing"),
        ("right", "rail_rtam", "right_tambour_vertical_backing"),
        ("left", "rail_ltam_upper", "left_tambour_upper_backing"),
        ("right", "rail_rtam_upper", "right_tambour_upper_backing"),
    ):
        rail = members[rail_name]
        thickness = 0.75
        backing_type = ComponentType(
            name="recessed_three_quarter_inch_plywood_tambour_backing",
            size=(rail.length, thickness, TAMBOUR_FABRICATION.minimum_backing_width/MM_PER_INCH),
            color=(0.72, 0.58, 0.38, 1.0),
            default_face="narrow_pos",
            mount_point=(0, 0, 0),
        )
        minimum_x = rail.max_on("x") - thickness if side == "left" else rail.min_on("x")
        components.add(
            backing_name,
            assembly="tambour_supports",
            component_type=backing_type,
            member=rail_name,
            at=0,
            face="narrow_pos",
            offset=(0, minimum_x-rail.center_on("x"), -HEIGHT_2x4-1/8),
        )

    GUSSET_HARDWARE_PROJECTION=(
        GUSSET_THICKNESS_IN+GUSSET_SCREW_HEAD_HEIGHT_IN
    )
    gusset_with_screws_type=ComponentType(
        name="custom_6x6_g90_gusset_with_number_9_pan_head_screws",
        size=(GUSSET_SIZE_IN, GUSSET_SIZE_IN, GUSSET_HARDWARE_PROJECTION),
        color=(0.62, 0.66, 0.68, 1.0),
        default_face="wide_pos",
        mount_point=(0, 0, 0),
        shape="primitive_union",
        box_primitives=(
            ((0, 0, 0), (GUSSET_SIZE_IN, GUSSET_SIZE_IN, GUSSET_THICKNESS_IN)),
        ),
        cylinder_primitives=pan_head_cylinder_primitives(),
        include_primitive_envelope=True,
    )
    # The four holes nearest each supported plate corner form a 1.5-inch
    # square.  Center that fastener profile on the post in both plan axes.
    for name, member_name, face, across_offset in (
        ("gusset_back_left", "post_bl", "wide_neg", -4.5),
        ("gusset_front_right", "post_fr", "wide_pos", -1.5),
    ):
        components.add(
            name,
            assembly="top_bracing_hardware",
            component_type=gusset_with_screws_type,
            member=member_name,
            at=members[member_name].length,
            face=face,
            orientation="inward",
            offset=(0.25, across_offset, 0),
        )

    # Roof strips bear directly on the perimeter and diagonal. Keep the
    # space below the diagonal clear for the prototype tambour door.
    roof_gusset_envelopes = []
    for gusset_name in ("gusset_back_left", "gusset_front_right"):
        instance = components[gusset_name]
        gusset = instance.resolved(members[instance.member])
        roof_gusset_envelopes.append((gusset.box_min, gusset.box_size))

    components.add(
        "low_voltage_termination_box",
        assembly="low_voltage_fittings",
        component_type=CARLON_E987N_JUNCTION_BOX,
        member="front_center_rail",
        at=0,
        face="wide_neg",
        absolute_anchor=(
            LOW_VOLTAGE_BOX_CENTER_X,
            LOW_VOLTAGE_BOX_CENTER_Y+CARLON_E987N_JUNCTION_BOX.size[1]/2,
            LOW_VOLTAGE_BOX_CENTER_Z,
        ),
    )

    components.add(
        "low_voltage_input_adapter",
        assembly="low_voltage_fittings",
        component_type=MALE_TERMINAL_ADAPTERS["3/4"],
        member="front_center_rail",
        at=0,
        face="wide_neg",
        absolute_anchor=(
            LOW_VOLTAGE_INPUT_X,
            LOW_VOLTAGE_INPUT_Y,
            LOW_VOLTAGE_BOX_BOTTOM_Z,
        ),
        orientation="down",
    )

    for index,gland_x in enumerate(LOW_VOLTAGE_GLAND_XS, start=1):
        if index == 1:
            continue
        components.add(
            f"low_voltage_cable_gland_{index}",
            assembly="low_voltage_fittings",
            component_type=ONE_INCH_CABLE_GLAND,
            member="front_center_rail",
            at=0,
            face="wide_neg",
            absolute_anchor=(
                gland_x,
                LOW_VOLTAGE_GLAND_Y,
                LOW_VOLTAGE_BOX_BOTTOM_Z,
            ),
            orientation="down",
        )

    components.add(
        "low_voltage_unused_port_closure", assembly="low_voltage_fittings",
        component_type=ComponentType(
            name="half_inch_panel_hole_weatherproof_closure", size=(0.65,0.65,0.15),
            shape="primitive_union", cylinder_primitives=(((0.325,0.325,0),"out",0.15,0.65),),
        ), member="front_center_rail", at=0, face="wide_neg", orientation="down",
        absolute_anchor=(LOW_VOLTAGE_GLAND_XS[0], LOW_VOLTAGE_GLAND_Y, LOW_VOLTAGE_BOX_BOTTOM_Z),
    )

    components.add(
        "front_street_light", assembly="electrical", component_type=MOD_LIGHTING_BROOK_16,
        member="brace_fl_fr", at=0, face="wide_neg",
        absolute_anchor=(FRONT_STREET_LIGHT_CENTER_X, FRONT_STREET_LIGHT_BOX_FACE_Y,
                         FRONT_STREET_LIGHT_CENTER_Z),
        component_basis=((1,0,0),(0,0,1),(0,-1,0)),
    )
    components.add(
        "front_street_light_bracket", assembly="electrical",
        component_type=ComponentType(
            name="brook_supplied_bracket_schematic", size=(5.5,0.5,0.08),
            color=(0.55,0.57,0.59,1),
        ), member="brace_fl_fr", at=0, face="wide_neg",
        absolute_anchor=(FRONT_STREET_LIGHT_CENTER_X, FRONT_STREET_LIGHT_BOX_FACE_Y,
                         FRONT_STREET_LIGHT_CENTER_Z),
        component_basis=((1,0,0),(0,0,1),(0,-1,0)),
    )
    for index,digit in enumerate("4754", start=1):
        number_x=FRONT_STREET_LIGHT_CENTER_X-6+(index-1)*3.25+1.125
        components.add(
            f"front_address_number_{index}", assembly="exterior_fixtures",
            component_type=ComponentType(
                name=f"silver_address_digit_{digit}", size=(2.25,5,1),
                color=(0.75,0.77,0.8,1), shape="raised_numeral", text=digit,
            ), member="front_address_number_support", at=0, face="wide_neg",
            absolute_anchor=(number_x, FRONT_STREET_LIGHT_BOX_FACE_Y-1, FRONT_ADDRESS_CENTER_Z),
            component_basis=((1,0,0),(0,0,1),(0,-1,0)),
        )
        for pin,z_offset in enumerate((-1.5,1.5),start=1):
            components.add(
                f"front_address_number_{index}_standoff_{pin}", assembly="exterior_fixtures",
                component_type=ComponentType(
                    name="silver_address_number_standoff", size=(0.375,0.375,1),
                    color=(0.75,0.77,0.8,1), shape="primitive_union",
                    cylinder_primitives=(((0.1875,0.1875,0),"out",1,0.375),),
                ), member="front_address_number_support", at=0, face="wide_neg",
                absolute_anchor=(number_x,FRONT_STREET_LIGHT_BOX_FACE_Y, FRONT_ADDRESS_CENTER_Z+z_offset),
                component_basis=((1,0,0),(0,0,1),(0,-1,0)),
            )

    components.add(
        "front_ev_charger_plug",
        assembly="electrical",
        component_type=EV_CHARGER_PLUG,
        member="front_center_rail",
        at=members["front_center_rail"].length-2.5,
        face="wide_pos",
    )

    components.add(
        "front_ev_charger_body",
        assembly="electrical",
        component_type=EV_CHARGER_BODY,
        member="front_center_rail",
        at=0,
        face="wide_pos",
        absolute_anchor=(
            members["front_center_rail"].center_on("x"),
            members["front_center_rail"].max_on("y"),
            30.25,
        ),
    )

    components.add(
        "front_wifi_access_point",
        assembly="electrical",
        component_type=WIFI_ACCESS_POINT,
        member="right_center_rail",
        at=members["right_center_rail"].length-3,
        face="narrow_pos",
    )

    components.add(
        "back_right_outlet",
        assembly="electrical",
        component_type=CARLON_E980DFN_OUTLET_BOX,
        member="back_right_outlet_backer_lower",
        at=(
            BACK_RIGHT_OUTLET_CENTER_Y
            - members["back_right_outlet_backer_lower"].min_on("y")
        ),
        face="narrow_pos",
        offset=(BACK_RIGHT_OUTLET_MOUNT_SPACING / 2, 0, 0),
        orientation="left",
    )

    components.add(
        "back_right_outlet_cover",
        assembly="electrical",
        component_type=INTERMATIC_WP5100BL_IN_USE_COVER,
        member="back_right_outlet_backer_lower",
        at=(
            BACK_RIGHT_OUTLET_CENTER_Y
            - members["back_right_outlet_backer_lower"].min_on("y")
        ),
        face="narrow_pos",
        offset=(
            BACK_RIGHT_OUTLET_MOUNT_SPACING / 2,
            0,
            CARLON_E980DFN_OUTLET_BOX.size[2],
        ),
        orientation="left",
    )

    components.add(
        "power_junction_box",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E987N_JUNCTION_BOX,
        member="front_center_rail",
        at=0,
        face="wide_neg",
        absolute_anchor=(
            POWER_JUNCTION_X,
            members["front_center_rail"].min_on("y")+POWER_JUNCTION_Y_SHIFT,
            POWER_JUNCTION_CENTER_Z,
        ),
    )

    ev_body = components["front_ev_charger_body"].resolved(
        members["front_center_rail"]
    )
    POWER_EV_ENTRY_ANCHOR=ComponentAnchor(
        "front_ev_charger_body",
        position=(0, EV_CHARGER_BODY.size[1]-2.30),
        depth_offset=1.60-EV_CHARGER_BODY.size[2]/2,
    )
    POWER_EV_ENTRY=tuple(
        ev_body.origin[index]
        + ev_body.along_vec[index]*POWER_EV_ENTRY_ANCHOR.position[0]
        + ev_body.across_vec[index]*POWER_EV_ENTRY_ANCHOR.position[1]
        + ev_body.out_vec[index]
        * (
            EV_CHARGER_BODY.size[2]/2
            + POWER_EV_ENTRY_ANCHOR.depth_offset
        )
        for index in range(3)
    )

    # Retain the riser entry and charger axes. The shallow pull-box cover
    # faces positive Y; its back entry faces negative Y toward the power box.
    POWER_PULL_BOX_AXIS_X=POWER_EV_ENTRY[0]
    POWER_PULL_BOX_AXIS_Y=POWER_EV_ENTRY[1]
    # Preserve the surveyed default riser position while following resized frames.
    POWER_RISER_X=POWER_PULL_BOX_AXIS_X-0.295
    POWER_RISER_Y=POWER_PULL_BOX_AXIS_Y+0.2125
    # Center the two-inch interior on the retained riser, independently of
    # the charger/top-fitting axis. Include the cover and back-wall thickness.
    POWER_PULL_BOX_FRONT_Y=POWER_RISER_Y+1+0.155
    POWER_PULL_BOX_BACK_Y=POWER_PULL_BOX_FRONT_Y-CARLON_E989NNJ_JUNCTION_BOX.size[2]
    POWER_PULL_BOX_CENTER_Z=8.83
    POWER_PULL_BOX_BOTTOM_Z=POWER_PULL_BOX_CENTER_Z-2
    POWER_PULL_BOX_TOP_Z=POWER_PULL_BOX_CENTER_Z+2
    components.add(
        "power_ev_pull_box",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E989NNJ_JUNCTION_BOX,
        member="front_center_rail", at=0, face="wide_neg",
        absolute_anchor=(POWER_PULL_BOX_AXIS_X, POWER_PULL_BOX_FRONT_Y,
                         POWER_PULL_BOX_CENTER_Z),
        orientation="down",
    )

    def add_box_fitting(name, trade_size, anchor, orientation, *, basis=None):
        components.add(
            name, assembly="electrical_conduit_fittings",
            component_type=MALE_TERMINAL_ADAPTERS[trade_size],
            member="front_center_rail", at=0, face="wide_neg",
            absolute_anchor=anchor, orientation=orientation,
            component_basis=basis,
        )

    add_box_fitting("power_ev_top_adapter", "1",
                    (POWER_PULL_BOX_AXIS_X, POWER_PULL_BOX_AXIS_Y,
                     POWER_PULL_BOX_TOP_Z), "up")
    add_box_fitting("power_ev_bottom_adapter", "1-1/4",
                    (POWER_RISER_X, POWER_RISER_Y,
                     POWER_PULL_BOX_BOTTOM_Z), "down")
    # Explicit basis makes the back fitting project toward negative Y.
    add_box_fitting("power_ev_back_adapter", "3/4",
                    (POWER_PULL_BOX_AXIS_X, POWER_PULL_BOX_BACK_Y,
                     POWER_PULL_BOX_CENTER_Z), "up",
                    basis=((0, -1, 0), (1, 0, 0), (0, 0, 1)))
    add_box_fitting("power_junction_input_adapter", "3/4",
                    (POWER_PULL_BOX_AXIS_X,
                     POWER_JUNCTION_CENTER_Y+2, POWER_PULL_BOX_CENTER_Z),
                    "inward")
    POWER_UF_CONNECTOR_LENGTH=1.25  # Schematic envelope; measure actual hardware.
    power_uf_connector_type=ComponentType(
        name="commercial_electric_fsw50z_12_2_1",
        size=(1.12,1.12,POWER_UF_CONNECTOR_LENGTH),
        shape="primitive_union", color=(0.5,0.52,0.54,1),
        cylinder_primitives=(((0.56,0.56,0),"out",POWER_UF_CONNECTOR_LENGTH,1.12),),
    )
    for name, anchor, basis in (
        ("power_junction_light_uf_connector",
         (POWER_JUNCTION_RIGHT_X,POWER_JUNCTION_LIGHT_PORT_Y,POWER_JUNCTION_LIGHT_PORT_Z),
         ((0,1,0),(0,0,1),(1,0,0))),
        ("power_junction_outlet_uf_connector",
         (POWER_JUNCTION_RIGHT_X,POWER_JUNCTION_PORT_Y,POWER_JUNCTION_OUTLET_PORT_Z),
         ((0,1,0),(0,0,1),(1,0,0))),
        ("back_right_outlet_uf_connector",BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT,
         ((1,0,0),(0,-1,0),(0,0,-1))),
    ):
        components.add(name, assembly="electrical", component_type=power_uf_connector_type,
                       member="front_center_rail", at=0, face="wide_neg",
                       absolute_anchor=anchor, component_basis=basis)

    # Every male fitting is clamped through a cut hole: sealing washer
    # outside, locknut inside. Copy the fitting placement to keep them coaxial.
    box_fitting_sizes = {
        "power_ev_top_adapter": "1", "power_ev_bottom_adapter": "1-1/4",
        "power_ev_back_adapter": "3/4", "power_junction_input_adapter": "3/4",
        "low_voltage_input_adapter": "3/4",
    }
    for fitting_name, trade_size in box_fitting_sizes.items():
        fitting = components[fitting_name]
        for suffix, types in (("sealing_washer", SEALING_WASHERS),
                              ("locknut", FITTING_LOCKNUTS)):
            components.add(
                f"{fitting_name}_{suffix}", assembly=fitting.assembly,
                component_type=types[trade_size], member=fitting.member,
                at=fitting.at, face=fitting.face,
                absolute_anchor=fitting.absolute_anchor,
                orientation=fitting.orientation, component_basis=fitting.component_basis,
            )

    def fitting_end(name, trade_size):
        fitting_type = MALE_TERMINAL_ADAPTERS[trade_size]
        return ComponentAnchor(name, position=(fitting_type.size[0],
                                               fitting_type.size[1]/2))

    POWER_PULL_BOX_BRANCH_ANCHOR=fitting_end("power_ev_back_adapter", "3/4")
    POWER_JUNCTION_INPUT_END_ANCHOR=fitting_end("power_junction_input_adapter", "3/4")
    POWER_EV_TOP_END_ANCHOR=fitting_end("power_ev_top_adapter", "1")
    POWER_RISER_END_Z=POWER_PULL_BOX_BOTTOM_Z-(
        MALE_TERMINAL_ADAPTERS["1-1/4"].size[0]-MALE_FITTING_WALL_OFFSET
    )

    conduits = ConduitCollection()

    POWER_PULL_BOX_GROUND_Z=grounds[0].resolved(members).z_at(
        POWER_PULL_BOX_AXIS_X,
        POWER_PULL_BOX_AXIS_Y,
    )
    POWER_RISER_GROUND_Z=grounds[0].resolved(members).z_at(
        POWER_RISER_X,
        POWER_RISER_Y,
    )
    conduits.add(
        "power_ground_riser",
        trade_size="1-1/4",
        points=(
            _member_relative_coord(
                "front_center_rail",
                POWER_RISER_X,
                POWER_RISER_Y,
                POWER_RISER_GROUND_Z,
            ),
            _member_relative_coord(
                "front_center_rail",
                POWER_RISER_X,
                POWER_RISER_Y,
                POWER_RISER_END_Z,
            ),
        ),
    )
    conduits.add(
        "power_pull_box_junction_feed",
        trade_size="3/4",
        points=(
            POWER_PULL_BOX_BRANCH_ANCHOR,
            POWER_JUNCTION_INPUT_END_ANCHOR,
        ),
    )
    conduits.add(
        "power_ev_charger_feed",
        trade_size="1",
        points=(
            POWER_EV_TOP_END_ANCHOR,
            POWER_EV_ENTRY_ANCHOR,
        ),
    )

    POWER_LIGHT_UF_EXIT=(POWER_JUNCTION_RIGHT_X+POWER_UF_CONNECTOR_LENGTH,
                         POWER_JUNCTION_LIGHT_PORT_Y,POWER_JUNCTION_LIGHT_PORT_Z)
    POWER_LIGHT_POST_X=FRONT_LIGHT_ROUTE_X
    POWER_LIGHT_OFFSET_START=(POWER_LIGHT_POST_X,FRONT_LIGHT_ROUTE_Y+0.4,
                              POWER_JUNCTION_LIGHT_PORT_Z+10)
    POWER_LIGHT_OFFSET_END=(POWER_LIGHT_POST_X,FRONT_LIGHT_ROUTE_Y,
                            POWER_JUNCTION_LIGHT_PORT_Z+16)
    POWER_LIGHT_OFFSET_POINTS=cubic_bezier_conduit_points(
        POWER_LIGHT_OFFSET_START,
        (POWER_LIGHT_POST_X,POWER_LIGHT_OFFSET_START[1]
         +(POWER_LIGHT_OFFSET_START[1]-POWER_JUNCTION_LIGHT_PORT_Y)/5,
         POWER_LIGHT_OFFSET_START[2]+2),
        (POWER_LIGHT_POST_X,FRONT_LIGHT_ROUTE_Y,POWER_LIGHT_OFFSET_END[2]-2),
        POWER_LIGHT_OFFSET_END,
    )
    POWER_OUTLET_UF_EXIT=(POWER_JUNCTION_RIGHT_X+POWER_UF_CONNECTOR_LENGTH,
                          POWER_JUNCTION_PORT_Y,POWER_JUNCTION_OUTLET_PORT_Z)
    POWER_OUTLET_UF_ENTRY=(BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[0],
                           BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[1],
                           BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[2]-POWER_UF_CONNECTOR_LENGTH)

    LOW_VOLTAGE_INPUT_ADAPTER_END_Z=(
        LOW_VOLTAGE_BOX_BOTTOM_Z-CARLON_E943E_MALE_TERMINAL_ADAPTER.size[0]
    )
    for footing in footings:
        resolved_footing=footing.resolved(members)
        footing_clearance=math.hypot(
            LOW_VOLTAGE_RISER_X-resolved_footing.center[0],
            LOW_VOLTAGE_RISER_Y-resolved_footing.center[1],
        )
        if footing_clearance < LOW_VOLTAGE_FOOTING_CLEARANCE_RADIUS-1e-9:
            raise ValueError(
                f"low-voltage riser conflicts with {footing.name}"
            )
    # Two matching Carlon 45-degree elbows form a vertical offset toward
    # negative X. The second bell overlaps the first elbow's plain outlet.
    LOW_VOLTAGE_ELBOW_LOCAL_END=(
        LOW_VOLTAGE_ELBOW_RADIUS*LOW_VOLTAGE_ELBOW_SIN,
        0,
        LOW_VOLTAGE_ELBOW_RADIUS*(LOW_VOLTAGE_ELBOW_COS-1),
    )
    LOW_VOLTAGE_ELBOW_LOCAL_OUTLET=(
        LOW_VOLTAGE_ELBOW_LOCAL_END[0]
        + LOW_VOLTAGE_ELBOW_SPIGOT_LENGTH*LOW_VOLTAGE_ELBOW_COS,
        0,
        LOW_VOLTAGE_ELBOW_LOCAL_END[2]
        - LOW_VOLTAGE_ELBOW_SPIGOT_LENGTH*LOW_VOLTAGE_ELBOW_SIN,
    )
    # The elbow's local bend curves toward negative local out. Give it a
    # right-handed basis whose out axis is positive world X.
    LOW_VOLTAGE_FIRST_ELBOW_BASIS=(
        (0, 0, 1),
        (0, -1, 0),
        (1, 0, 0),
    )
    LOW_VOLTAGE_FIRST_ELBOW_ANCHOR_Z=(
        LOW_VOLTAGE_GROUND_Z+LOW_VOLTAGE_ELBOW_SOCKET_DEPTH
    )
    components.add(
        "low_voltage_ground_sweep_elbow_1",
        assembly="low_voltage_fittings",
        component_type=CARLON_UA7AEB_BELL_END_45_ELBOW,
        member="post_fr",
        at=0,
        face="narrow_pos",
        absolute_anchor=(
            LOW_VOLTAGE_RISER_X,
            LOW_VOLTAGE_RISER_Y,
            LOW_VOLTAGE_FIRST_ELBOW_ANCHOR_Z,
        ),
        component_basis=LOW_VOLTAGE_FIRST_ELBOW_BASIS,
    )
    lower_elbow=components["low_voltage_ground_sweep_elbow_1"].resolved(
        members["post_fr"]
    )
    elbow_mount=CARLON_UA7AEB_BELL_END_45_ELBOW.mount_point
    if elbow_mount is None:
        raise ValueError("Carlon elbow model is missing its mount point")

    def _elbow_path_point_world(
        resolved: Any,
        local_delta: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        local_end=tuple(
            elbow_mount[index]+local_delta[index]
            for index in range(3)
        )
        return tuple(
            resolved.origin[index]
            + resolved.along_vec[index]*local_end[0]
            + resolved.across_vec[index]*local_end[1]
            + resolved.out_vec[index]*local_end[2]
            for index in range(3)
        )

    LOW_VOLTAGE_ELBOW_JOINT=_elbow_path_point_world(
        lower_elbow,
        LOW_VOLTAGE_ELBOW_LOCAL_OUTLET,
    )
    LOW_VOLTAGE_SECOND_ELBOW_BASIS=(
        (
            -LOW_VOLTAGE_ELBOW_SIN,
            0,
            LOW_VOLTAGE_ELBOW_COS,
        ),
        (0, 1, 0),
        (
            -LOW_VOLTAGE_ELBOW_COS,
            0,
            -LOW_VOLTAGE_ELBOW_SIN,
        ),
    )
    components.add(
        "low_voltage_ground_sweep_elbow_2",
        assembly="low_voltage_fittings",
        component_type=CARLON_UA7AEB_BELL_END_45_ELBOW,
        member="post_fr",
        at=0,
        face="narrow_pos",
        absolute_anchor=LOW_VOLTAGE_ELBOW_JOINT,
        component_basis=LOW_VOLTAGE_SECOND_ELBOW_BASIS,
    )
    upper_elbow=components["low_voltage_ground_sweep_elbow_2"].resolved(
        members["post_fr"]
    )
    LOW_VOLTAGE_UPPER_ELBOW_OUTLET=_elbow_path_point_world(
        upper_elbow,
        LOW_VOLTAGE_ELBOW_LOCAL_OUTLET,
    )
    if any(
        not math.isclose(actual, expected, abs_tol=1e-9)
        for actual, expected in zip(
            LOW_VOLTAGE_UPPER_ELBOW_OUTLET,
            (LOW_VOLTAGE_INPUT_X, LOW_VOLTAGE_INPUT_Y,
             LOW_VOLTAGE_INPUT_ADAPTER_END_Z),
            strict=True,
        )
    ):
        raise ValueError("low-voltage box input does not meet upper elbow")

    conduits.add(
        "low_voltage_ground_riser_inlet",
        assembly="low_voltage_conduit",
        trade_size="3/4",
        points=(
            _member_relative_coord(
                "post_fr",
                LOW_VOLTAGE_RISER_X,
                LOW_VOLTAGE_RISER_Y,
                LOW_VOLTAGE_GROUND_Z,
            ),
            _member_relative_coord(
                "post_fr",
                LOW_VOLTAGE_RISER_X,
                LOW_VOLTAGE_RISER_Y,
                LOW_VOLTAGE_FIRST_ELBOW_ANCHOR_Z,
            ),
        ),
    )

    tambours = TambourCollection()

    TAMBOUR_LEFT_X = members["post_fl"].max_on("x")
    TAMBOUR_RIGHT_X = members["post_fr"].min_on("x")
    TAMBOUR_REAR_VERTICAL_LENGTH=(
        TAMBOUR_TRACK_TOP_Z-TAMBOUR_BACK_BOTTOM_Z-TAMBOUR_BEND_RADIUS
    )
    TAMBOUR_TOP_TANGENT_LENGTH=(
        TAMBOUR_TRACK_BACK_Y
        -TAMBOUR_TRACK_FRONT_Y
        -2*TAMBOUR_BEND_RADIUS
    )
    TAMBOUR_FRONT_VERTICAL_LENGTH=(
        TAMBOUR_TRACK_TOP_Z-TAMBOUR_FRONT_BOTTOM_Z-TAMBOUR_BEND_RADIUS
    )
    if min(
        TAMBOUR_REAR_VERTICAL_LENGTH,
        TAMBOUR_TOP_TANGENT_LENGTH,
        TAMBOUR_FRONT_VERTICAL_LENGTH,
    ) <= 0:
        raise ValueError("tambour path leaves no room for a straight track run")
    TAMBOUR_FABRICATION=replace(
        TAMBOUR_FABRICATION,
        rear_vertical_length=TAMBOUR_REAR_VERTICAL_LENGTH*MM_PER_INCH,
        top_tangent_length=TAMBOUR_TOP_TANGENT_LENGTH*MM_PER_INCH,
        front_vertical_length=TAMBOUR_FRONT_VERTICAL_LENGTH*MM_PER_INCH,
    )

    rear_fixed_length = (
        TAMBOUR_FABRICATION.rear_vertical_length
        - TAMBOUR_FABRICATION.bend_stub_length
        - TAMBOUR_FABRICATION.loading_section_length
    )
    top_fixed_length = (
        TAMBOUR_FABRICATION.top_tangent_length
        - 2 * TAMBOUR_FABRICATION.bend_stub_length
    )
    front_fixed_length = (
        TAMBOUR_FABRICATION.front_vertical_length
        - TAMBOUR_FABRICATION.bend_stub_length
    )
    rear_segments = split_segment_lengths(
        rear_fixed_length, TAMBOUR_FABRICATION.maximum_segment_length
    )
    top_segments = split_segment_lengths(
        top_fixed_length, TAMBOUR_FABRICATION.maximum_segment_length
    )
    front_segments = split_segment_lengths(
        front_fixed_length, TAMBOUR_FABRICATION.maximum_segment_length
    )
    quarter_arc = math.pi * TAMBOUR_FABRICATION.bend_radius / 2
    segment_seams_mm: list[float] = [TAMBOUR_FABRICATION.loading_section_length]
    cursor = TAMBOUR_FABRICATION.loading_section_length
    for length in rear_segments:
        cursor += length
        segment_seams_mm.append(cursor)
    cursor += 2 * TAMBOUR_FABRICATION.bend_stub_length + quarter_arc
    segment_seams_mm.append(cursor)
    for length in top_segments:
        cursor += length
        segment_seams_mm.append(cursor)
    cursor += 2 * TAMBOUR_FABRICATION.bend_stub_length + quarter_arc
    segment_seams_mm.append(cursor)
    for length in front_segments[:-1]:
        cursor += length
        segment_seams_mm.append(cursor)
    TAMBOUR_SEGMENT_SEAMS=tuple(
        distance/MM_PER_INCH for distance in sorted(set(segment_seams_mm))
    )
    TAMBOUR_INSTALLED_DETAILS=TambourInstalledDetails(
        channel_internal_width=(
            TAMBOUR_FABRICATION.channel_internal_width/MM_PER_INCH
        ),
        channel_wall_thickness=(
            TAMBOUR_FABRICATION.wall_thickness/MM_PER_INCH
        ),
        mounting_flange_thickness=(
            TAMBOUR_FABRICATION.mounting_flange_thickness/MM_PER_INCH
        ),
        flange_extension=TAMBOUR_FABRICATION.flange_extension/MM_PER_INCH,
        slat_end_engagement=(
            TAMBOUR_FABRICATION.slat_end_engagement/MM_PER_INCH
        ),
        slat_total_end_clearance=TAMBOUR_FABRICATION.slat_total_end_clearance/MM_PER_INCH,
        segment_seams=TAMBOUR_SEGMENT_SEAMS,
        joint_gap=TAMBOUR_FABRICATION.joint_expansion_gap/MM_PER_INCH,
        loading_section_length=(
            TAMBOUR_FABRICATION.loading_section_length/MM_PER_INCH
        ),
        end_stop_length=TAMBOUR_FABRICATION.end_stop_insertion/MM_PER_INCH,
        webbing_count=3,
        webbing_width=1.0,
        webbing_thickness=1/16,
        pull_slat_indices=(0, 23),
        handle_width=TAMBOUR_FABRICATION.handle_width/MM_PER_INCH,
        handle_height=TAMBOUR_FABRICATION.handle_height/MM_PER_INCH,
        handle_projection=TAMBOUR_FABRICATION.handle_projection/MM_PER_INCH,
        inward_hardware_projection=(
            TAMBOUR_FABRICATION.inward_hardware_projection/MM_PER_INCH
        ),
    )

    tambours.add(
        "enclosure_tambour_door",
        assembly="tambour_door",
        track_name="enclosure_tambour_track",
        track_assembly="tambour_track",
        left_points=(
            RelativeCoord(
                "post_bl",
                WIDTH_4x4,
                TAMBOUR_TRACK_BACK_Y-members["post_bl"].min_on("y"),
                BURIED_FRAME_Z+TAMBOUR_BACK_BOTTOM_Z,
            ),
            RelativeCoord(
                "post_bl",
                WIDTH_4x4,
                TAMBOUR_TRACK_BACK_Y-members["post_bl"].min_on("y"),
                BURIED_FRAME_Z+TAMBOUR_TRACK_TOP_Z,
            ),
            RelativeCoord(
                "post_fl",
                WIDTH_4x4,
                TAMBOUR_TRACK_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_TRACK_TOP_Z,
            ),
            RelativeCoord(
                "post_fl",
                WIDTH_4x4,
                TAMBOUR_TRACK_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_FRONT_BOTTOM_Z,
            ),
        ),
        right_points=(
            RelativeCoord(
                "post_br",
                0,
                TAMBOUR_TRACK_BACK_Y-members["post_br"].min_on("y"),
                BURIED_FRAME_Z+TAMBOUR_BACK_BOTTOM_Z,
            ),
            RelativeCoord(
                "post_br",
                0,
                TAMBOUR_TRACK_BACK_Y-members["post_br"].min_on("y"),
                BURIED_FRAME_Z+TAMBOUR_TRACK_TOP_Z,
            ),
            RelativeCoord(
                "post_fr",
                0,
                TAMBOUR_TRACK_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_TRACK_TOP_Z,
            ),
            RelativeCoord(
                "post_fr",
                0,
                TAMBOUR_TRACK_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_FRONT_BOTTOM_Z,
            ),
        ),
        bends=(
            TambourBend(point_index=1, radius=TAMBOUR_BEND_RADIUS, segments=48),
            TambourBend(point_index=2, radius=TAMBOUR_BEND_RADIUS, segments=48),
        ),
        door_length=44,
        slat_pitch=TAMBOUR_SLAT_PITCH,
        slat_thickness=TAMBOUR_SLAT_HEIGHT,
        slat_depth=TAMBOUR_SLAT_DEPTH,
        slat_track_offset=TAMBOUR_SLAT_TRACK_OFFSET,
        slat_envelope_depth=TAMBOUR_MAX_ENVELOPE_DEPTH,
        installed_details=TAMBOUR_INSTALLED_DETAILS,
        slat_color=TAMBOUR_DOOR_COLOR,
    )

    TAMBOUR_CEILING_THICKNESS=0.25
    TAMBOUR_CEILING_CLEARANCE=0.25
    TAMBOUR_CEILING_BEND_INSET=0.75
    TAMBOUR_CEILING_FRONT_Y=members["rail_ft"].max_on("y")
    TAMBOUR_CEILING_REAR_Y=(
        TAMBOUR_TRACK_BACK_Y-TAMBOUR_BEND_RADIUS-TAMBOUR_CEILING_BEND_INSET
    )
    TAMBOUR_CEILING_TOP_Z=FRAME_DIMS.z-3.5
    TAMBOUR_CEILING_BOTTOM_Z=(
        TAMBOUR_CEILING_TOP_Z-TAMBOUR_CEILING_THICKNESS
    )
    TAMBOUR_CEILING_DEPTH=(
        TAMBOUR_CEILING_REAR_Y-TAMBOUR_CEILING_FRONT_Y
    )
    TAMBOUR_CEILING_WIDTH=TAMBOUR_RIGHT_X-TAMBOUR_LEFT_X
    if TAMBOUR_CEILING_DEPTH <= 0:
        raise ValueError("enclosure depth leaves no room for the tambour ceiling")
    tambour_ceiling_type=ComponentType(
        name="quarter_inch_exterior_plywood_panel",
        size=(
            TAMBOUR_CEILING_DEPTH,
            TAMBOUR_CEILING_THICKNESS,
            TAMBOUR_CEILING_WIDTH,
        ),
        color=(0.72, 0.58, 0.38, 1.0),
        default_face="wide_pos",
        mount_point=(0, 0, 0),
    )
    components.add(
        "tambour_ceiling_panel",
        assembly="tambour_guard",
        component_type=tambour_ceiling_type,
        member="brace_fl_bl",
        at=(
            TAMBOUR_CEILING_FRONT_Y
            - members["brace_fl_bl"].min_on("y")
        ),
        face="wide_pos",
        offset=(
            0,
            TAMBOUR_CEILING_BOTTOM_Z
            - members["brace_fl_bl"].center_on("z"),
            0,
        ),
    )

    siding = US135Siding(
        "enclosure_siding",
        min_x=0,
        max_x=FRAME_DIMS.x + WIDTH_4x4,
        min_y=0,
        max_y=FRAME_DIMS.y + WIDTH_4x4,
        frame_top_z=FRAME_DIMS.z,
        roof_support_z=FRAME_DIMS.z+ROOF_STRIP_THICKNESS,
        roof_gussets=tuple(roof_gusset_envelopes),
        bottom_z=SIDING_BOTTOM_Z,
        rear_opening_min_x=TAMBOUR_LEFT_X,
        rear_opening_max_x=TAMBOUR_RIGHT_X,
        rear_opening_top_z=TAMBOUR_TOP_Z,
        front_bores=(FRONT_STREET_LIGHT_SIDING_BORE,),
        right_openings=(BACK_RIGHT_OUTLET_SIDING_OPENING,),
        stock_length=SIDING_STOCK_LENGTH_FT * 12,
        board_thickness=US135_THICKNESS,
        ground=grounds[0].resolved(members),
        framing=tuple((m.start,m.size) for m in members.values() if m.name != "brace_bl_fr"),
        diagonal=diagonal_footprint,
        front_trim_relief=(FRONT_STREET_LIGHT_CENTER_X-3.125,
                           FRONT_STREET_LIGHT_CENTER_X+3.125,
                           FRONT_STREET_LIGHT_CENTER_Z+1.2+1/8),
    )

    cables = CableCollection()
    cables.add(
        "front_ev_charger_cable",
        diameter=1,
        points=ev_charger_cable_points(
            components["front_ev_charger_body"].resolved(members["front_center_rail"]),
            components["front_ev_charger_plug"].resolved(members["front_center_rail"]),
            grounds[0].resolved(members),
        ),
    )


    def _join_centerline_sections(
        *sections: tuple[tuple[float, float, float], ...],
    ) -> tuple[tuple[float, float, float], ...]:
        joined: list[tuple[float, float, float]] = []
        for section in sections:
            if joined and section and joined[-1] == section[0]:
                joined.extend(section[1:])
            else:
                joined.extend(section)
        return tuple(joined)


    def _sweep_centerline_x(
        points: tuple[tuple[float, float, float], ...],
        end_x: float,
        end_z: float,
    ) -> tuple[tuple[float, float, float], ...]:
        lengths=[0.0]
        for start,end in zip(points, points[1:]):
            lengths.append(lengths[-1]+math.dist(start, end))
        sweep_length=next(
            length
            for point,length in zip(points, lengths, strict=True)
            if point[2] >= end_z
        )
        start_x=points[0][0]
        swept=[]
        for point,length in zip(points, lengths, strict=True):
            progress=min(1, (length/sweep_length)**2)
            eased=progress**3*(progress*(progress*6-15)+10)
            swept.append(
                (
                    start_x+(end_x-start_x)*eased,
                    point[1],
                    point[2],
                )
            )
        return tuple(swept)


    LOW_VOLTAGE_GLAND_END_Z=(
        LOW_VOLTAGE_BOX_BOTTOM_Z-ONE_INCH_CABLE_GLAND.size[0]
    )
    LOW_VOLTAGE_RISER_CABLE_CLEARANCE=(
        LOW_VOLTAGE_CONDUIT_RADIUS
        + LOW_VOLTAGE_CABLE_DIAMETER/2
        + LOW_VOLTAGE_CABLE_DIAMETER
    )
    LOW_VOLTAGE_RISER_BYPASS_Z=LOW_VOLTAGE_GLAND_END_Z-4
    LOW_VOLTAGE_GLAND_EXIT_BOTTOM_Z=LOW_VOLTAGE_GLAND_END_Z-2
    LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS=LOW_VOLTAGE_MINIMUM_BEND_RADIUS
    # Preserve the approved cable route while rail_fbu and the box mounting are
    # revised.  This is an absolute world-space elevation, not rail clearance.
    LOW_VOLTAGE_RAIL_FBU_CLEAR_Z=8.4375
    LOW_VOLTAGE_RIGHT_RAIL_NEG_X=(
        members["right_center_rail"].min_on("x")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_RIGHT_RAIL_POS_Y=(
        members["right_center_rail"].max_on("y")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_FRONT_RAIL_NEG_X=(
        members["front_center_rail"].min_on("x")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_FRONT_RAIL_POS_X=(
        members["front_center_rail"].max_on("x")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_RAIL_FT_POS_Y=(
        members["rail_ft"].max_on("y")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    FRONT_UF_CABLE_DIAMETER=POWER_UF_CABLE_DIAMETER
    FRONT_UF_MINIMUM_BEND_RADIUS=2.0
    FRONT_UF_RUN_Z=FRONT_STREET_LIGHT_CABLE_Z
    FRONT_UF_WALL_POINT=(FRONT_STREET_LIGHT_CENTER_X,0,FRONT_STREET_LIGHT_CABLE_Z)
    front_uf_rise=rounded_cable_points((
        POWER_LIGHT_UF_EXIT,
        (POWER_LIGHT_POST_X,POWER_JUNCTION_LIGHT_PORT_Y,POWER_JUNCTION_LIGHT_PORT_Z),
        POWER_LIGHT_OFFSET_START), {1:2.5})
    front_uf_top=rounded_cable_points((
        POWER_LIGHT_OFFSET_END,
        (POWER_LIGHT_POST_X,FRONT_LIGHT_ROUTE_Y,FRONT_UF_RUN_Z),
        (FRONT_STREET_LIGHT_CENTER_X,FRONT_LIGHT_ROUTE_Y,FRONT_UF_RUN_Z),
        FRONT_UF_WALL_POINT,
        (FRONT_STREET_LIGHT_CENTER_X,FRONT_STREET_LIGHT_BOX_FACE_Y-0.125,FRONT_STREET_LIGHT_CABLE_Z)),
        {1:FRONT_UF_MINIMUM_BEND_RADIUS,2:FRONT_UF_MINIMUM_BEND_RADIUS})
    cables.add("power_street_light_uf_b", assembly="electrical", diameter=FRONT_UF_CABLE_DIAMETER,
               points=(*front_uf_rise,*(p.resolve(members) for p in POWER_LIGHT_OFFSET_POINTS[1:-1]),*front_uf_top),
               color=(0.48,0.49,0.50,1))
    cables.add("power_back_right_outlet_uf_b", assembly="electrical", diameter=POWER_UF_CABLE_DIAMETER,
               points=rounded_cable_points((
                   POWER_OUTLET_UF_EXIT,
                   (POWER_OUTLET_UF_ENTRY[0],POWER_JUNCTION_PORT_Y,POWER_OUTLET_HORIZONTAL_RUN_Z),
                   (POWER_OUTLET_UF_ENTRY[0],POWER_OUTLET_UF_ENTRY[1],POWER_OUTLET_HORIZONTAL_RUN_Z),
                   POWER_OUTLET_UF_ENTRY), {1:4,2:4}), color=(0.48,0.49,0.50,1))

    LOW_VOLTAGE_WIFI_LANE_OFFSET=-LOW_VOLTAGE_CABLE_DIAMETER/2
    LOW_VOLTAGE_CHARGER_LANE_OFFSET=LOW_VOLTAGE_CABLE_DIAMETER/2
    # The surveyed grade raises the box and gland exits. Give the return's
    # X transition another 3/4 inch to retain the minimum cable bend radius.
    LOW_VOLTAGE_WIFI_X_SWEEP_END_Z=(
        11.0+max(0, width-DEFAULT_WIDTH)/4
    )
    LOW_VOLTAGE_WIFI_FACE_CENTER_Z=15

    wifi=components["front_wifi_access_point"].resolved(members["right_center_rail"])
    path_2_start=(LOW_VOLTAGE_GLAND_XS[2], LOW_VOLTAGE_GLAND_Y, LOW_VOLTAGE_GLAND_END_Z)
    path_2_riser_bypass=(
        max(
            path_2_start[0],
            LOW_VOLTAGE_INPUT_X
            + LOW_VOLTAGE_RISER_CABLE_CLEARANCE
            + LOW_VOLTAGE_CABLE_DIAMETER,
        ),
        LOW_VOLTAGE_INPUT_Y,
        LOW_VOLTAGE_RISER_BYPASS_Z,
    )
    path_2_riser_approach=(
        path_2_riser_bypass[0],
        path_2_riser_bypass[1]-0.75,
        path_2_riser_bypass[2],
    )
    path_2_riser_climb=(
        path_2_riser_bypass[0],
        path_2_riser_bypass[1],
        LOW_VOLTAGE_RAIL_FBU_CLEAR_Z,
    )
    path_2_front_rail=(
        LOW_VOLTAGE_FRONT_RAIL_POS_X,
        members["front_center_rail"].center_on("y"),
        LOW_VOLTAGE_WIFI_FACE_CENTER_Z,
    )
    path_2_top_clear=(
        path_2_front_rail[0],
        LOW_VOLTAGE_RAIL_FT_POS_Y,
        members["rail_ft"].center_on("z")+LOW_VOLTAGE_WIFI_LANE_OFFSET,
    )
    path_2_right_rail=(
        LOW_VOLTAGE_RIGHT_RAIL_NEG_X,
        members["right_center_rail"].center_on("y")+LOW_VOLTAGE_WIFI_LANE_OFFSET,
        path_2_top_clear[2],
    )
    path_2_entry=(
        wifi.box_min[0]+wifi.box_size[0]/2,
        wifi.box_min[1]+wifi.box_size[1]/2,
        wifi.box_min[2],
    )
    path_2_entry_sweep=(
        path_2_right_rail[0],
        path_2_entry[1],
        path_2_entry[2]-2,
    )
    path_2_entry_under=(path_2_entry[0], path_2_entry[1], path_2_entry_sweep[2])
    path_2_droop_points=cubic_bezier_points(
        path_2_start,
        (path_2_start[0], path_2_start[1], path_2_start[2]-1),
        (
            path_2_riser_approach[0],
            path_2_riser_approach[1]-1.5,
            path_2_riser_approach[2],
        ),
        path_2_riser_approach,
    )
    LOW_VOLTAGE_WIFI_RETURN_BEND_RADIUS=(
        LOW_VOLTAGE_MINIMUM_BEND_RADIUS+0.001
    )
    path_2_return_yz=rounded_cable_points(
        (path_2_riser_approach, path_2_riser_bypass, path_2_riser_climb),
        {1: LOW_VOLTAGE_WIFI_RETURN_BEND_RADIUS},
    )
    path_2_front_rail_yz=(
        path_2_riser_climb[0],
        path_2_front_rail[1],
        path_2_front_rail[2],
    )
    path_2_approach_yz=cubic_bezier_points(
        path_2_riser_climb,
        (path_2_riser_climb[0], path_2_riser_climb[1], path_2_riser_climb[2]+2),
        (path_2_riser_climb[0], path_2_front_rail[1], path_2_front_rail[2]-4),
        path_2_front_rail_yz,
    )
    path_2_x_sweep=_sweep_centerline_x(
        _join_centerline_sections(path_2_return_yz, path_2_approach_yz),
        LOW_VOLTAGE_FRONT_RAIL_POS_X,
        LOW_VOLTAGE_WIFI_X_SWEEP_END_Z,
    )
    path_2_points=_join_centerline_sections(
        path_2_droop_points,
        path_2_x_sweep,
        rounded_cable_points(
            (
                path_2_front_rail,
                (path_2_front_rail[0], path_2_front_rail[1], FRAME_DIMS.z-7),
                (path_2_front_rail[0], path_2_top_clear[1], FRAME_DIMS.z-7),
                path_2_top_clear,
                (path_2_right_rail[0], path_2_top_clear[1], path_2_top_clear[2]),
                path_2_right_rail,
                (path_2_right_rail[0], path_2_right_rail[1], path_2_entry_sweep[2]),
                path_2_entry_sweep,
                path_2_entry_under,
                path_2_entry,
            ),
            {
                1: 1.25,
                2: 1.25,
                3: 1.25,
                4: 0.75,
                5: 0.75,
                6: 0.7,
                7: 0.7,
                8: 0.8,
            },
        ),
    )

    charger=components["front_ev_charger_body"].resolved(members["front_center_rail"])
    path_3_start=(LOW_VOLTAGE_GLAND_XS[1], LOW_VOLTAGE_GLAND_Y, LOW_VOLTAGE_GLAND_END_Z)
    path_3_riser_bypass=(
        LOW_VOLTAGE_INPUT_X+LOW_VOLTAGE_RISER_CABLE_CLEARANCE,
        LOW_VOLTAGE_INPUT_Y,
        LOW_VOLTAGE_RISER_BYPASS_Z,
    )
    path_3_riser_approach=(
        path_3_riser_bypass[0],
        path_3_riser_bypass[1]-0.75,
        path_3_riser_bypass[2],
    )
    path_3_riser_climb=(
        path_3_riser_bypass[0],
        path_3_riser_bypass[1],
        LOW_VOLTAGE_RAIL_FBU_CLEAR_Z,
    )
    path_3_front_rail=(
        LOW_VOLTAGE_FRONT_RAIL_NEG_X,
        members["front_center_rail"].center_on("y")+LOW_VOLTAGE_CHARGER_LANE_OFFSET,
        16,
    )
    path_3_entry=(
        charger.box_min[0]+charger.box_size[0]/2,
        charger.box_min[1]+charger.box_size[1]/2,
        charger.box_min[2],
    )
    path_3_branch=(
        path_3_front_rail[0],
        path_3_front_rail[1],
        path_3_entry[2]-1.65,
    )
    path_3_rail_clear=(
        path_3_branch[0],
        members["front_center_rail"].max_on("y")
        + LOW_VOLTAGE_CABLE_DIAMETER/2,
        path_3_branch[2],
    )
    path_3_lower_yz=_join_centerline_sections(
        cubic_bezier_points(
            path_3_start,
            (path_3_start[0], path_3_start[1], path_3_start[2]-1),
            (
                path_3_riser_approach[0],
                path_3_riser_approach[1]-1.5,
                path_3_riser_approach[2],
            ),
            path_3_riser_approach,
        ),
        rounded_cable_points(
            (path_3_riser_approach, path_3_riser_bypass, path_3_riser_climb),
            {1: LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS},
        ),
        cubic_bezier_points(
            path_3_riser_climb,
            (path_3_riser_climb[0], path_3_riser_climb[1], path_3_riser_climb[2]+1.8),
            (path_3_front_rail[0], path_3_front_rail[1], path_3_front_rail[2]-4),
            path_3_front_rail,
        ),
    )
    path_3_lower_points=path_3_lower_yz
    path_3_points=_join_centerline_sections(
        path_3_lower_points,
        rounded_cable_points(
            (
                path_3_front_rail,
                path_3_branch,
                path_3_rail_clear,
            ),
            {1: 0.8},
        ),
        cubic_bezier_points(
            path_3_rail_clear,
            (path_3_rail_clear[0], path_3_rail_clear[1]+0.75, path_3_rail_clear[2]),
            (path_3_entry[0]-0.5, path_3_entry[1]-0.5, path_3_entry[2]-0.5),
            path_3_entry,
        ),
    )

    for name,points,color in (
        ("low_voltage_wifi_feed", path_2_points, LOW_VOLTAGE_CAT6_COLOR),
        ("low_voltage_ev_charger_feed", path_3_points, LOW_VOLTAGE_CAT6_COLOR),
    ):
        cables.add(
            name,
            assembly="low_voltage_cabling",
            diameter=LOW_VOLTAGE_CABLE_DIAMETER,
            points=points,
            color=color,
        )

    # The removable plywood panel carries cord contact into two uprights
    # anchored to the front rails.  Clearances follow the modeled pull-box envelope.
    POWER_GUARD_CLEARANCE=0.25
    POWER_GUARD_PULL_BOX=components["power_ev_pull_box"].resolved(members["front_center_rail"])
    POWER_GUARD_LEFT_X=POWER_GUARD_PULL_BOX.box_min[0]-POWER_GUARD_CLEARANCE-1.5
    POWER_GUARD_RIGHT_X=(
        POWER_GUARD_PULL_BOX.box_min[0]
        +POWER_GUARD_PULL_BOX.box_size[0]
        +POWER_GUARD_CLEARANCE
    )
    POWER_GUARD_REAR_Y=members["rail_fbl"].max_on("y")
    POWER_GUARD_PANEL_Y=(
        POWER_GUARD_PULL_BOX.box_min[1]+POWER_GUARD_PULL_BOX.box_size[1]
        +POWER_GUARD_CLEARANCE
    )
    POWER_GUARD_UPRIGHT_DEPTH=POWER_GUARD_PANEL_Y-POWER_GUARD_REAR_Y
    if not 0 < POWER_GUARD_UPRIGHT_DEPTH <= 3.5:
        raise ValueError("power guard upright cannot be ripped from a 2x4")
    POWER_GUARD_BOTTOM_Z=0.75
    POWER_GUARD_TOP_Z=math.ceil((POWER_PULL_BOX_TOP_Z+1)*4)/4
    POWER_GUARD_SPAN=(POWER_GUARD_RIGHT_X+1.5)-POWER_GUARD_LEFT_X
    for side,x in (("left",POWER_GUARD_LEFT_X),("right",POWER_GUARD_RIGHT_X)):
        members.add(
            f"power_guard_{side}_upright",
            assembly="power_cord_guard",
            type="2x4",
            axis="z",
            start=AbsoluteCoord(x,POWER_GUARD_REAR_Y,POWER_GUARD_BOTTOM_Z),
            length=POWER_GUARD_TOP_Z-POWER_GUARD_BOTTOM_Z,
            rotated=False,
            finished_wide=POWER_GUARD_UPRIGHT_DEPTH,
        )
    components.add(
        "power_guard_removable_panel",
        assembly="power_cord_guard",
        component_type=ComponentType(
            name="quarter_inch_exterior_plywood_guard_panel",
            size=(POWER_GUARD_TOP_Z-POWER_GUARD_BOTTOM_Z, POWER_GUARD_SPAN, 0.25),
            color=(0.52, 0.36, 0.20, 1),
            mount_point=(0, 0, 0),
        ),
        member="power_guard_left_upright",
        at=0,
        absolute_anchor=(
            POWER_GUARD_LEFT_X,
            POWER_GUARD_PANEL_Y,
            POWER_GUARD_BOTTOM_Z,
        ),
        component_basis=((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    )

    model = Model(
        members,
        components=components,
        conduits=conduits,
        cables=cables,
        grounds=grounds,
        footings=footings,
        tambours=tambours,
        sidings=[siding],
        routed_seats=routed_seats,
        purchased_items=(
            PurchasedItem("street_light_14_2_uf_b", "electrical",
                f"14/2 copper UF-B with ground, {math.ceil((cables['power_street_light_uf_b'].centerline_length+18)/12)} ft cut "
                f"(route {cables['power_street_light_uf_b'].centerline_length:.1f} in plus 18 in termination/service allowance); 15 A maximum", 1,
                category="cable", include_in_shopping_list=True),
            PurchasedItem("silver_address_numerals_4754", "exterior_fixtures",
                "Separate silver numerals 4754; each 5 in high x 1 in deep; 12 in total width", 1,
                include_in_shopping_list=True),
            PurchasedItem("silver_address_number_standoff", "exterior_fixtures",
                "Silver numeral standoff, 1 in long; schematic 3/8 in diameter", 8,
                include_in_shopping_list=True),
            PurchasedItem("outlet_12_2_uf_b", "electrical",
                f"12/2 copper UF-B with ground, {math.ceil((cables['power_back_right_outlet_uf_b'].centerline_length+18)/12)} ft cut "
                f"(route {cables['power_back_right_outlet_uf_b'].centerline_length:.1f} in plus 18 in termination/service allowance)", 1,
                category="cable", include_in_shopping_list=True),
            PurchasedItem("commercial_electric_fsw50z_12_2_1", "electrical",
                "Commercial Electric FSW50Z-12.2-1 watertight 1/2 in connector for 14/2 or 12/2 UF-B", 3),
            PurchasedItem("half_inch_panel_hole_weatherproof_closure", "low_voltage_fittings",
                "Weatherproof closure for unused 0.500 in low-voltage gland opening", 1),
            PurchasedItem(
                "mod_lighting_brook_16_black_3000k",
                "electrical",
                "MOD Lighting Brook MOD119, 16 in, black, 3000K; "
                "variant 45573961023747, supplied bracket included",
                1,
            ),
            PurchasedItem(
                "custom_6x6_g90_gusset_plate",
                "top_bracing_hardware",
                f"laser-cut 6 x 6 x {GUSSET_THICKNESS_IN:.3f} in {GUSSET_MATERIAL}",
                2,
            ),
            PurchasedItem(
                "number_9_pan_head_screw",
                "top_bracing_hardware",
                "#9 pan-head screw; length intentionally unspecified",
                2 * GUSSET_FASTENER_COUNT,
            ),
            PurchasedItem(
                "power_guard_rail_screw",
                "power_cord_guard_hardware",
                "exterior structural wood screw, 4 in",
                4,
            ),
            PurchasedItem(
                "power_guard_panel_screw",
                "power_cord_guard_hardware",
                "#10 exterior truss-head screw, 1 1/2 in",
                8,
            ),
            PurchasedItem(
                "power_guard_removable_panel",
                "power_cord_guard",
                f"1/4 in exterior plywood panel, {POWER_GUARD_SPAN:g} x "
                f"{POWER_GUARD_TOP_Z-POWER_GUARD_BOTTOM_Z:g} in",
                1,
                category="sheet",
                cut_size=(POWER_GUARD_SPAN, POWER_GUARD_TOP_Z-POWER_GUARD_BOTTOM_Z, 0.25),
            ),
        ),
        xygrid_origin=(
            members["post_fl"].min_on("x"),
            members["post_fl"].min_on("y"),
        ),
        build_steps=(
            BUILD_STEPS
            if (width, depth, height)
            == (DEFAULT_WIDTH, DEFAULT_DEPTH, DEFAULT_HEIGHT)
            else ()
        ),
        deferred_object_names=DEFERRED_OBJECT_NAMES,
    )

    build_values = dict(locals())
    anchors = {
        name: value
        for name, value in build_values.items()
        if name.isupper() or name.startswith("path_")
    }
    return EnclosureBuild(
        width=width,
        depth=depth,
        height=height,
        members=members,
        components=components,
        conduits=conduits,
        cables=cables,
        grounds=grounds,
        footings=footings,
        tambours=tambours,
        siding=siding,
        routed_seats=routed_seats,
        model=model,
        anchors=anchors,
    )


default_build = build_enclosure()
members = default_build.members
components = default_build.components
conduits = default_build.conduits
cables = default_build.cables
grounds = default_build.grounds
footings = default_build.footings
tambours = default_build.tambours
siding = default_build.siding
routed_seats = default_build.routed_seats
model = default_build.model
globals().update(default_build.anchors)


def write_outputs(
    enclosure: EnclosureBuild,
    output_dir: Path = Path("output"),
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    enclosure.model.write_scad(output_dir / "model.scad")
    enclosure.model.write_bom_csv(output_dir / "bom.csv")
    enclosure.model.write_bom_json(output_dir / "bom.json")
    enclosure.model.write_cut_list_csv(output_dir / "cut_list.csv")
    enclosure.model.write_cut_list_json(output_dir / "cut_list.json")
    enclosure.model.write_shopping_list_csv(output_dir / "shopping_list.csv")
    enclosure.model.write_shopping_list_json(output_dir / "shopping_list.json")
    enclosure.model.write_fabrication_csv(output_dir / "fabrication.csv")
    enclosure.model.write_fabrication_json(output_dir / "fabrication.json")
    enclosure.siding.write_artifacts(output_dir)
    generate_gusset_dxf(output_dir / "gusset_plate_6x6.dxf")
    generate_tambour_fabrication(
        output_dir / "tambour",
        config=enclosure.TAMBOUR_FABRICATION,
    )


def _playground_model_text(model_path: Path) -> str:
    """Return a Playground-ready model without changing the local output."""

    model_text = model_path.read_text()
    replaced_path = False
    for local_path, playground_path in PLAYGROUND_MESH_PATHS.items():
        if local_path in model_text:
            model_text = model_text.replace(local_path, playground_path)
            replaced_path = True
    if not replaced_path:
        expected = ", ".join(PLAYGROUND_MESH_PATHS)
        raise ValueError(
            "generated model does not reference any expected mesh path: "
            f"{expected}"
        )
    return model_text


def _validate_deployment_source(repository: str) -> None:
    """Require a clean checkout exactly synchronized with its upstream."""

    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise ValueError(
            "working tree is not clean; commit or remove local changes before "
            "deploying"
        )

    branch = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "config", "--get", f"branch.{branch}.remote"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    merge_ref = subprocess.run(
        ["git", "config", "--get", f"branch.{branch}.merge"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if remote == ".":
        raise ValueError(
            f"branch {branch!r} tracks a local branch; configure a remote upstream "
            "before deploying"
        )

    subprocess.run(
        ["git", "fetch", "--quiet", remote, merge_ref],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    local_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    remote_commit = subprocess.run(
        ["git", "rev-parse", "FETCH_HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if local_commit != remote_commit:
        raise ValueError(
            f"local branch {branch!r} is not synchronized with {remote}/{merge_ref}; "
            "push or update the branch before deploying"
        )


def deploy_generated_model(model_path: Path) -> bool:
    """Push a generated model commit that triggers the Pages workflow."""

    try:
        repository = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        _validate_deployment_source(repository)
        playground_text = _playground_model_text(model_path)
        remote_ref = (
            f"refs/remotes/{PLAYGROUND_REMOTE}/{PLAYGROUND_DEPLOY_BRANCH}"
        )
        remote_branch = f"refs/heads/{PLAYGROUND_DEPLOY_BRANCH}"
        remote_result = subprocess.run(
            [
                "git",
                "ls-remote",
                "--exit-code",
                "--heads",
                PLAYGROUND_REMOTE,
                remote_branch,
            ],
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
        )
        if remote_result.returncode not in (0, 2):
            raise subprocess.CalledProcessError(
                remote_result.returncode,
                remote_result.args,
                remote_result.stdout,
                remote_result.stderr,
            )
        has_remote_branch = remote_result.returncode == 0
        if has_remote_branch:
            subprocess.run(
                [
                    "git",
                    "fetch",
                    "--quiet",
                    PLAYGROUND_REMOTE,
                    f"+{remote_branch}:{remote_ref}",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

        with tempfile.TemporaryDirectory(prefix="openscad-pages-deploy-") as directory:
            temporary_directory = Path(directory)
            staged_model = Path(directory) / "model.scad"
            staged_model.write_text(playground_text)
            environment = os.environ.copy()
            environment["GIT_INDEX_FILE"] = str(temporary_directory / "index")
            subprocess.run(
                ["git", "read-tree", "HEAD"],
                cwd=repository,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            blob = subprocess.run(
                ["git", "hash-object", "-w", str(staged_model)],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            subprocess.run(
                [
                    "git",
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    "100644",
                    blob,
                    PLAYGROUND_DEPLOY_PATH,
                ],
                cwd=repository,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            tree = subprocess.run(
                ["git", "write-tree"],
                cwd=repository,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

        if has_remote_branch:
            remote_tree = subprocess.run(
                ["git", "rev-parse", f"{remote_ref}^{{tree}}"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if tree == remote_tree:
                print(f"Playground already up to date at {PLAYGROUND_MODEL_URL}")
                return True

        parent = remote_ref if has_remote_branch else "HEAD"
        commit = subprocess.run(
            [
                "git",
                "commit-tree",
                tree,
                "-p",
                parent,
                "-m",
                "Deploy generated enclosure model",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "push", PLAYGROUND_REMOTE, f"{commit}:{remote_branch}"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        detail = (
            exc.stderr.strip()
            if isinstance(exc, subprocess.CalledProcessError) and exc.stderr
            else str(exc)
        )
        print(
            f"warning: generated {model_path}, but deployment to GitHub Pages "
            f"failed: {detail}",
            file=sys.stderr,
        )
        return False

    print(f"Queued deployment of {model_path} to {PLAYGROUND_MODEL_URL}")
    return True


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an EV charger enclosure model. Dimensions are inches."
    )
    parser.add_argument(
        "--width",
        type=float,
        default=DEFAULT_WIDTH,
        help=f"post centerline spacing on the X/front axis (default: {DEFAULT_WIDTH:g})",
    )
    parser.add_argument(
        "--depth",
        type=float,
        default=DEFAULT_DEPTH,
        help=(
            "post centerline spacing on the Y/front-to-back axis "
            f"(default: {DEFAULT_DEPTH:g})"
        ),
    )
    parser.add_argument(
        "--height",
        type=float,
        default=DEFAULT_HEIGHT,
        help=f"level post-top elevation above the front-left ground datum (default: {DEFAULT_HEIGHT:g})",
    )
    parser.add_argument(
        "--no-deploy",
        action="store_true",
        help="generate local outputs without publishing to GitHub Pages",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _argument_parser()
    args = parser.parse_args(argv)
    try:
        enclosure = build_enclosure(
            args.width,
            args.depth,
            args.height,
        )
        write_outputs(enclosure)
        if not args.no_deploy:
            deploy_generated_model(Path("output/model.scad"))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
