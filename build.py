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
    CARLON_E983G_CONDUIT_T_BODY,
    CARLON_E950GF_REDUCER_BUSHING,
    CARLON_E940D_COUPLING,
    CARLON_E940G_COUPLING,
    CARLON_E943E_MALE_TERMINAL_ADAPTER,
    CARLON_E987N_JUNCTION_BOX,
    CARLON_E996D_BOX_ADAPTER,
    CARLON_E996G_BOX_ADAPTER,
    COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX,
    COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING,
    EV_CHARGER_BODY,
    EV_CHARGER_PLUG,
    GENERIC_DOWNWARD_STREET_LIGHT,
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
    GroundPlane,
    FrontSidingOpening,
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
from lumber_model.gusset import (
    GUSSET_FASTENER_COUNT,
    GUSSET_MATERIAL,
    GUSSET_SCREW_HEAD_HEIGHT_IN,
    GUSSET_SIZE_IN,
    GUSSET_THICKNESS_IN,
    pan_head_cylinder_primitives,
)
from lumber_model.gusset_dxf import generate_gusset_dxf

DEFAULT_WIDTH = 24
DEFAULT_DEPTH = 18.375
DEFAULT_HEIGHT = 47
BUILD_STEPS_PATH = Path(__file__).with_name("BUILD_STEPS.md")
BUILD_STEPS = parse_build_steps(BUILD_STEPS_PATH)
PLAYGROUND_MODEL_URL = "https://ditdafivo.github.io/ev-charger-enclosure/"
PLAYGROUND_DEPLOY_BRANCH = "pages-source"
PLAYGROUND_DEPLOY_PATH = "pages/model.scad"
PLAYGROUND_REMOTE = "origin"
LOCAL_MESH_PATH = "../assets/components/ev_charger_plug/ev_charger_plug.stl"
PLAYGROUND_MESH_PATH = "ev_charger_plug.stl"


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
    grounds: list[GroundPlane]
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
    FRAME_DIMS=AbsoluteCoord(width, depth, height)
    BURIED_FRAME_Z=32
    FULL_POST_LEN=BURIED_FRAME_Z+FRAME_DIMS.z
    SIDING_BOTTOM_Z=2
    SIDING_STOCK_LENGTH_FT=16
    SIDING_BOARD_THICKNESS=1
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
            length=(
                FULL_POST_LEN - HEIGHT_1X_BOARD
                if name in {"post_bl", "post_fr"}
                else FULL_POST_LEN
            ),
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
        cover_supports_xy=True,
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
            "brace_bl_br",
            "brace_fr_br",
            "brace_fl_fr",
        )
    )

    CENTER_RAIL_OFFSET=-3
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
        HEIGHT_2x4-TAMBOUR_TRACK_FOOTPRINT_WIDTH
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

    # The front electrical assembly remains fixed.  Put the curtain as far
    # forward as its outward envelope and required clearance allow, rounded
    # rearward to construction-friendly 1/8-inch resolution.
    FRONT_STREET_LIGHT_FACE_PROJECTION=0
    FRONT_STREET_LIGHT_BOX_FACE_Y=(
        -SIDING_BOARD_THICKNESS-FRONT_STREET_LIGHT_FACE_PROJECTION
    )
    FRONT_STREET_LIGHT_BOX_BACK_Y=(
        FRONT_STREET_LIGHT_BOX_FACE_Y
        +COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2]
        +COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[2]
    )
    FRONT_STREET_LIGHT_BACKER_REAR_Y=(
        FRONT_STREET_LIGHT_BOX_BACK_Y+HEIGHT_2x4
    )
    TAMBOUR_PLACEMENT_INCREMENT=1/8
    TAMBOUR_MINIMUM_TRACK_FRONT_Y=(
        FRONT_STREET_LIGHT_BACKER_REAR_Y
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
    for name,support_a,support_b,position,cross_offset,position_axis,rotated in [
        ("rail_rb","post_fr","post_br", 7, 0, None, True),
        ("rail_lb","post_fl","post_bl", 7, 0, None, True),
        ("rail_fb","rail_lb","rail_rb", 7, CENTER_RAIL_OFFSET, None, True),
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

    tambour_support_overlap_center_y=(
        max(
            members["brace_fl_bl"].min_on("y"),
            members["rail_lb"].min_on("y"),
        )
        +min(
            members["brace_fl_bl"].max_on("y"),
            members["rail_lb"].max_on("y"),
        )
    )/2
    tambour_support_cross_offset=(
        TAMBOUR_VERTICAL_SUPPORT_CENTER_Y-tambour_support_overlap_center_y
    )
    for name,support_a,support_b,position in (
        (
            "rail_ltam",
            "brace_fl_bl",
            "rail_lb",
            members["post_fl"].center_on("x"),
        ),
        (
            "rail_rtam",
            "brace_fr_br",
            "rail_rb",
            members["post_fr"].center_on("x"),
        ),
    ):
        members.between(
            name,
            assembly="frame",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=position,
            cross_offset=tambour_support_cross_offset,
            rotated=True,
        )

    for name,support_a,support_b,position,position_axis in [
        ("rail_rbu", "rail_rtam", "post_br", 13, None),
        (
            "rail_lt",
            "rail_ltam",
            "post_bl",
            TAMBOUR_FRONT_HEADER_CENTER_Z,
            None,
        ),
        (
            "rail_rt",
            "rail_rtam",
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
        support_a="rail_fb",
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
        position=(WIDTH_4x4+FRAME_DIMS.y)/2,
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
    FRONT_STREET_LIGHT_TOP_OFFSET=7
    FRONT_STREET_LIGHT_CENTER_Z=FRAME_DIMS.z-FRONT_STREET_LIGHT_TOP_OFFSET
    FRONT_STREET_LIGHT_BACKER_CROSS_OFFSET=(
        FRONT_STREET_LIGHT_BOX_BACK_Y
        + HEIGHT_2x4 / 2
        - WIDTH_4x4 / 2
    )
    FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET=3.5 / 2

    for name,position in [
        (
            "front_street_light_backer_bottom",
            FRONT_STREET_LIGHT_CENTER_Z
            - 3 * FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET,
        ),
        (
            "front_street_light_backer_lower",
            FRONT_STREET_LIGHT_CENTER_Z - FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET,
        ),
        (
            "front_street_light_backer_upper",
            FRONT_STREET_LIGHT_CENTER_Z + FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET,
        ),
    ]:
        members.between(
            name,
            assembly="electrical_backing",
            type="2x4",
            support_a="post_fl",
            support_b="post_fr",
            position=position,
            cross_offset=FRONT_STREET_LIGHT_BACKER_CROSS_OFFSET,
            rotated=False,
        )

    FRONT_STREET_LIGHT_CONDUIT_ENTRY_ANCHOR=ComponentAnchor(
        "front_street_light_base_box",
        position=(
            COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[0]/2,
            0,
        ),
    )
    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT=(
        FRONT_STREET_LIGHT_CENTER_X,
        FRONT_STREET_LIGHT_BOX_BACK_Y
        - COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2]/2,
        FRONT_STREET_LIGHT_CENTER_Z
        - COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[1]/2,
    )
    FRONT_STREET_LIGHT_CONDUIT_ENTRY=_member_relative_coord(
        "post_fl",
        *FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT,
    )

    FRONT_STREET_LIGHT_SIDING_OPENING=FrontSidingOpening(
        "front_street_light",
        min_x=(
            FRONT_STREET_LIGHT_CENTER_X
            - COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[0] / 2
        ),
        max_x=(
            FRONT_STREET_LIGHT_CENTER_X
            + COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[0] / 2
        ),
        bottom_z=(
            FRONT_STREET_LIGHT_CENTER_Z
            - COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[1] / 2
        ),
        top_z=(
            FRONT_STREET_LIGHT_CENTER_Z
            + COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[1] / 2
        ),
    )

    grounds = [
        GroundPlane(
            "ground",
            point_a=RelativeCoord("post_fr", 0, 0, BURIED_FRAME_Z+1),
            point_b=RelativeCoord("post_bl", 0, 0, BURIED_FRAME_Z-0.75),
            center=RelativeCoord(
                "post_fl",
                FRAME_DIMS.x / 2,
                FRAME_DIMS.y / 2,
                BURIED_FRAME_Z+0.125,
            ),
            radius=48,
        )
    ]

    FOOTING_DIAMETER=10
    FOOTING_BOTTOM_Z=-36
    FOOTING_TOP_Z=0
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
            top_z=FOOTING_TOP_Z,
        )
        for post_name in ("post_fl", "post_fr", "post_bl", "post_br")
    ]

    POWER_JUNCTION_RIGHT_SHIFT=2
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
    POWER_JUNCTION_GROUND_REFERENCE_X=POWER_JUNCTION_X+1
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
    POWER_JUNCTION_OUTLET_PORT_Z=POWER_JUNCTION_CENTER_Z

    POWER_JUNCTION_BOX_FILL=BoxFillCalculation(
        marked_volume=49,
        conductor_groups=((12, 7),),
        equipment_grounding_awgs=(12, 12, 12),
    )
    POWER_JUNCTION_BOX_FILL.validate()

    LOW_VOLTAGE_BOX_CENTER_Z=13
    LOW_VOLTAGE_BOX_CENTER_Y=(
        members["front_center_rail"].min_on("y")
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    LOW_VOLTAGE_BOX_FRONT_SETBACK=(
        LOW_VOLTAGE_BOX_CENTER_Y
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
        - members["post_fr"].min_on("y")
    )
    LOW_VOLTAGE_BOX_GAP=1
    LOW_VOLTAGE_BOX_REAR_X=(
        POWER_JUNCTION_X
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
        - LOW_VOLTAGE_BOX_GAP
    )
    LOW_VOLTAGE_BOX_LEFT_X=(
        LOW_VOLTAGE_BOX_REAR_X-CARLON_E987N_JUNCTION_BOX.size[1]
    )
    LOW_VOLTAGE_BOX_CENTER_X=(
        LOW_VOLTAGE_BOX_LEFT_X+CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    LOW_VOLTAGE_BOX_BOTTOM_Z=(
        LOW_VOLTAGE_BOX_CENTER_Z - CARLON_E987N_JUNCTION_BOX.size[0]/2
    )
    LOW_VOLTAGE_PORT_EDGE_CLEARANCE=0.75
    LOW_VOLTAGE_INPUT_Y=(
        LOW_VOLTAGE_BOX_CENTER_Y
        + CARLON_E987N_JUNCTION_BOX.size[1]/2
        - LOW_VOLTAGE_PORT_EDGE_CLEARANCE
    )
    LOW_VOLTAGE_CONDUIT_RADIUS=CONDUIT_OD_BY_TRADE_SIZE["3/4"]/2
    LOW_VOLTAGE_FOOTING_CLEARANCE_RADIUS=(
        FOOTING_DIAMETER/2+LOW_VOLTAGE_CONDUIT_RADIUS
    )
    LOW_VOLTAGE_POST_FL_CENTER=(
        members["post_fl"].center_on("x"),
        members["post_fl"].center_on("y"),
    )
    LOW_VOLTAGE_POST_FL_Y_OFFSET=(
        LOW_VOLTAGE_INPUT_Y-LOW_VOLTAGE_POST_FL_CENTER[1]
    )
    LOW_VOLTAGE_POST_FL_MIN_X=(
        LOW_VOLTAGE_POST_FL_CENTER[0]
        + math.sqrt(12**2-LOW_VOLTAGE_POST_FL_Y_OFFSET**2)
        if abs(LOW_VOLTAGE_POST_FL_Y_OFFSET) < 12
        else -math.inf
    )
    # Translate the former riser axis one inch in positive X with both boxes.
    # The old 12-inch post_fl clearance intentionally yields to the requested
    # location; footing collision checks remain.
    LOW_VOLTAGE_INPUT_X=max(
        LOW_VOLTAGE_BOX_LEFT_X+LOW_VOLTAGE_PORT_EDGE_CLEARANCE,
        LOW_VOLTAGE_POST_FL_MIN_X,
    )
    if LOW_VOLTAGE_INPUT_X > (
        LOW_VOLTAGE_BOX_REAR_X-LOW_VOLTAGE_PORT_EDGE_CLEARANCE
    ):
        raise ValueError(
            "low-voltage riser cannot maintain post clearance within the junction box"
        )
    for footing in footings:
        resolved_footing=footing.resolved(members)
        footing_clearance=math.hypot(
            LOW_VOLTAGE_INPUT_X-resolved_footing.center[0],
            LOW_VOLTAGE_INPUT_Y-resolved_footing.center[1],
        )
        if footing_clearance < LOW_VOLTAGE_FOOTING_CLEARANCE_RADIUS-1e-9:
            raise ValueError(
                f"low-voltage riser conflicts with {footing.name}"
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
    LOW_VOLTAGE_STREET_LIGHT_COLOR=(0.18, 0.07, 0.025, 1.0)

    components = ComponentCollection()

    TAMBOUR_FRONT_BEND_BACKER_THICKNESS=0.75
    TAMBOUR_FRONT_BEND_BACKER_LENGTH=HEIGHT_2x4
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
            "rail_ltam",
            members["rail_ltam"].max_on("x")
            -TAMBOUR_FRONT_BEND_BACKER_THICKNESS,
        ),
        (
            "right_tambour_bend_backer",
            "rail_rtam",
            members["rail_rtam"].min_on("x"),
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
            offset=(0, minimum_x-rail.center_on("x"), 0),
        )

    GUSSET_HARDWARE_PROJECTION=(
        GUSSET_THICKNESS_IN+GUSSET_SCREW_HEAD_HEIGHT_IN
    )
    ROOF_SHIM_THICKNESS=math.ceil(GUSSET_HARDWARE_PROJECTION*8)/8
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
            offset=(0.25, across_offset, diagonal.thickness),
        )

    # Stop each shim at the resolved hardware envelope.  The shim establishes a
    # support plane above the gusset; placing it on the gusset would instead
    # stack the two parts and raise the decking locally.
    for member_name, gusset_name, keep_side, end_post_name in (
        ("brace_fl_fr", "gusset_front_right", "before", "post_fl"),
        ("brace_fl_bl", "gusset_back_left", "before", None),
        ("brace_bl_br", "gusset_back_left", "after", "post_br"),
        ("brace_fr_br", "gusset_front_right", "after", None),
    ):
        member=members[member_name]
        gusset=components[gusset_name]
        resolved_gusset=gusset.resolved(members[gusset.member])
        along_index={"x": 0, "y": 1}[member.axis]
        gusset_min=resolved_gusset.box_min[along_index]
        gusset_max=gusset_min+resolved_gusset.box_size[along_index]
        member_min=member.min_on(member.axis)
        member_max=member.max_on(member.axis)
        if keep_side == "before":
            shim_start=(
                members[end_post_name].min_on(member.axis)
                if end_post_name is not None
                else member_min
            )
            shim_end=min(gusset_min, member_max)
        else:
            shim_start=max(gusset_max, member_min)
            shim_end=(
                members[end_post_name].max_on(member.axis)
                if end_post_name is not None
                else member_max
            )
        shim_length=shim_end-shim_start
        if shim_length <= 0:
            raise ValueError(
                f"{gusset_name} leaves no roof-shim support on {member_name}"
            )
        shim_type=ComponentType(
            name=f"continuous_pt_roof_shim_{member_name}",
            size=(shim_length, 3.5, ROOF_SHIM_THICKNESS),
            color=(0.44, 0.26, 0.11, 1.0),
            default_face="narrow_pos",
            mount_point=(0, 1.75, 0),
        )
        components.add(
            f"roof_shim_{member_name}",
            assembly="roof_shims",
            component_type=shim_type,
            member=member_name,
            at=max(shim_start-member_min, 0),
            face="narrow_pos",
            offset=(min(shim_start-member_min, 0), 0, 0),
        )

    components.add(
        "low_voltage_termination_box",
        assembly="low_voltage_fittings",
        component_type=CARLON_E987N_JUNCTION_BOX,
        member="front_center_rail",
        at=(
            LOW_VOLTAGE_BOX_CENTER_Z
            - members["front_center_rail"].min_on("z")
        ),
        face="wide_neg",
        offset=(
            0,
            LOW_VOLTAGE_BOX_CENTER_X
            - members["front_center_rail"].center_on("x"),
            0,
        ),
    )

    components.add(
        "low_voltage_input_adapter",
        assembly="low_voltage_fittings",
        component_type=CARLON_E943E_MALE_TERMINAL_ADAPTER,
        member="front_center_rail",
        at=(
            LOW_VOLTAGE_BOX_BOTTOM_Z
            - members["front_center_rail"].min_on("z")
        ),
        face="wide_neg",
        offset=(
            0,
            -(
                LOW_VOLTAGE_INPUT_X
                - members["front_center_rail"].center_on("x")
            ),
            members["front_center_rail"].min_on("y")
            - LOW_VOLTAGE_INPUT_Y,
        ),
        orientation="down",
    )

    for index,gland_x in enumerate(LOW_VOLTAGE_GLAND_XS, start=1):
        components.add(
            f"low_voltage_cable_gland_{index}",
            assembly="low_voltage_fittings",
            component_type=ONE_INCH_CABLE_GLAND,
            member="front_center_rail",
            at=(
                LOW_VOLTAGE_BOX_BOTTOM_Z
                - members["front_center_rail"].min_on("z")
            ),
            face="wide_neg",
            offset=(
                0,
                -(gland_x-members["front_center_rail"].center_on("x")),
                members["front_center_rail"].min_on("y")
                - LOW_VOLTAGE_GLAND_Y,
            ),
            orientation="down",
        )

    components.add(
        "front_street_light_base_box",
        assembly="electrical",
        component_type=COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX,
        member="front_street_light_backer_lower",
        at=(
            FRONT_STREET_LIGHT_CENTER_X
            - members["front_street_light_backer_lower"].min_on("x")
        ),
        face="narrow_neg",
        offset=(0, FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET, 0),
    )

    components.add(
        "front_street_light_extension_ring",
        assembly="electrical",
        component_type=COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING,
        member="front_street_light_backer_lower",
        at=(
            FRONT_STREET_LIGHT_CENTER_X
            - members["front_street_light_backer_lower"].min_on("x")
        ),
        face="narrow_neg",
        offset=(
            0,
            FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET,
            COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2],
        ),
    )

    components.add(
        "front_street_light",
        assembly="electrical",
        component_type=GENERIC_DOWNWARD_STREET_LIGHT,
        member="front_street_light_backer_lower",
        at=(
            FRONT_STREET_LIGHT_CENTER_X
            - members["front_street_light_backer_lower"].min_on("x")
        ),
        face="narrow_neg",
        offset=(
            0,
            FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET,
            COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2]
            + COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[2],
        ),
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
        at=22.5,
        face="wide_pos",
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
        at=(
            POWER_JUNCTION_CENTER_Z
            - members["front_center_rail"].min_on("z")
        ),
        face="wide_neg",
        offset=(
            0,
            POWER_JUNCTION_X-members["front_center_rail"].center_on("x"),
            -POWER_JUNCTION_Y_SHIFT,
        ),
    )

    ev_body = components["front_ev_charger_body"].resolved(
        members["front_center_rail"]
    )
    POWER_EV_ENTRY=(
        ev_body.box_min[0]+ev_body.box_size[0]/2+2.25,
        ev_body.box_min[1]+ev_body.box_size[1]/2,
        ev_body.box_min[2],
    )
    POWER_EV_ENTRY_ANCHOR=ComponentAnchor(
        "front_ev_charger_body",
        position=(0, EV_CHARGER_BODY.size[1]/2+2.25),
    )

    # Keep the T's vertical channel coaxial with the charger entry and raise
    # its horizontal branch until the complete conduit envelope clears rail_fb.
    POWER_T_MAIN_CHANNEL_WIDTH=2+5/16
    POWER_T_AXIS_X=POWER_EV_ENTRY[0]
    POWER_T_AXIS_Y=POWER_EV_ENTRY[1]
    POWER_T_RAIL_CLEARANCE=0.25
    POWER_T_CENTER_Z=(
        members["rail_fb"].max_on("z")
        + CONDUIT_OD_BY_TRADE_SIZE["1-1/4"]/2
        + POWER_T_RAIL_CLEARANCE
    )
    POWER_T_ANCHOR_X=(
        POWER_T_AXIS_X-CARLON_E983G_CONDUIT_T_BODY.size[2]/2
    )
    POWER_T_ANCHOR_Y=(
        POWER_T_AXIS_Y
        - (
            CARLON_E983G_CONDUIT_T_BODY.size[1]
            - POWER_T_MAIN_CHANNEL_WIDTH
        )/2
    )
    components.add(
        "power_ev_t_body",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E983G_CONDUIT_T_BODY,
        member="front_center_rail",
        at=POWER_T_CENTER_Z-members["front_center_rail"].min_on("z"),
        face="narrow_pos",
        offset=(
            0,
            members["front_center_rail"].center_on("y")-POWER_T_ANCHOR_Y,
            POWER_T_ANCHOR_X-members["front_center_rail"].max_on("x"),
        ),
        orientation="down",
    )
    POWER_T_TOP_ANCHOR=ComponentAnchor(
        "power_ev_t_body",
        position=(0, POWER_T_MAIN_CHANNEL_WIDTH/2),
    )
    POWER_T_BOTTOM_ANCHOR=ComponentAnchor(
        "power_ev_t_body",
        position=(
            CARLON_E983G_CONDUIT_T_BODY.size[0],
            POWER_T_MAIN_CHANNEL_WIDTH/2,
        ),
    )
    POWER_T_BRANCH_ANCHOR=ComponentAnchor(
        "power_ev_t_body",
        position=(
            CARLON_E983G_CONDUIT_T_BODY.size[0]/2,
            CARLON_E983G_CONDUIT_T_BODY.size[1],
        ),
    )

    # The junction input is on its rear face, aligned with the raised branch.
    POWER_JUNCTION_T_PORT_X=POWER_T_AXIS_X
    POWER_JUNCTION_T_PORT_Y=(
        POWER_JUNCTION_CENTER_Y+CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    POWER_JUNCTION_T_PORT_Z=POWER_T_CENTER_Z
    POWER_JUNCTION_T_FACE_OFFSET=(
        members["front_center_rail"].min_on("y")-POWER_JUNCTION_T_PORT_Y
    )
    components.add(
        "power_junction_input_adapter",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E996G_BOX_ADAPTER,
        member="front_center_rail",
        at=POWER_JUNCTION_T_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            -POWER_JUNCTION_T_FACE_OFFSET,
            POWER_JUNCTION_T_PORT_X-members["front_center_rail"].center_on("x"),
            0,
        ),
        orientation="inward",
    )
    components.add(
        "power_junction_input_coupling",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E940G_COUPLING,
        member="front_center_rail",
        at=POWER_JUNCTION_T_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            (
                CARLON_E996G_BOX_ADAPTER.size[0]/2
                - POWER_JUNCTION_T_FACE_OFFSET
            ),
            POWER_JUNCTION_T_PORT_X-members["front_center_rail"].center_on("x"),
            0,
        ),
        orientation="inward",
    )
    POWER_JUNCTION_INPUT_COUPLING_END_ANCHOR=ComponentAnchor(
        "power_junction_input_coupling",
        position=(
            CARLON_E940G_COUPLING.size[0],
            CARLON_E940G_COUPLING.size[1]/2,
        ),
    )
    POWER_T_TOP_Z=(
        POWER_T_CENTER_Z+CARLON_E983G_CONDUIT_T_BODY.size[0]/2
    )
    components.add(
        "power_ev_reducer",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E950GF_REDUCER_BUSHING,
        member="front_center_rail",
        at=POWER_T_TOP_Z-members["front_center_rail"].min_on("z"),
        face="narrow_pos",
        offset=(
            0,
            POWER_T_AXIS_Y-members["front_center_rail"].center_on("y"),
            POWER_T_AXIS_X-members["front_center_rail"].max_on("x"),
        ),
    )

    # Positive-X-facing 1/2-inch street-light penetration.  It shares the
    # right side with the outlet fitting but sits farther forward (negative Y).
    components.add(
        "power_junction_light_adapter",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E996D_BOX_ADAPTER,
        member="front_center_rail",
        at=POWER_JUNCTION_OUTLET_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            POWER_JUNCTION_RIGHT_X-members["front_center_rail"].center_on("x"),
            0,
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_LIGHT_PORT_Y,
        ),
        orientation="left",
    )
    components.add(
        "power_junction_light_coupling",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E940D_COUPLING,
        member="front_center_rail",
        at=POWER_JUNCTION_OUTLET_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            POWER_JUNCTION_RIGHT_X
            + CARLON_E996D_BOX_ADAPTER.size[0]/2
            - members["front_center_rail"].center_on("x"),
            0,
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_LIGHT_PORT_Y,
        ),
        orientation="left",
    )

    # Right-side 1/2-inch outlet penetration.
    components.add(
        "power_junction_outlet_adapter",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E996D_BOX_ADAPTER,
        member="front_center_rail",
        at=POWER_JUNCTION_OUTLET_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            POWER_JUNCTION_RIGHT_X-members["front_center_rail"].center_on("x"),
            0,
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_PORT_Y,
        ),
        orientation="left",
    )
    components.add(
        "power_junction_outlet_coupling",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E940D_COUPLING,
        member="front_center_rail",
        at=POWER_JUNCTION_OUTLET_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            POWER_JUNCTION_RIGHT_X
            + CARLON_E996D_BOX_ADAPTER.size[0]/2
            - members["front_center_rail"].center_on("x"),
            0,
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_PORT_Y,
        ),
        orientation="left",
    )

    conduits = ConduitCollection()

    POWER_T_GROUND_Z=grounds[0].resolved(members).z_at(
        POWER_T_AXIS_X,
        POWER_T_AXIS_Y,
    )
    conduits.add(
        "power_ground_riser",
        trade_size="1-1/4",
        points=(
            _member_relative_coord(
                "front_center_rail",
                POWER_T_AXIS_X,
                POWER_T_AXIS_Y,
                POWER_T_GROUND_Z,
            ),
            POWER_T_BOTTOM_ANCHOR,
        ),
    )
    conduits.add(
        "power_t_junction_feed",
        trade_size="1-1/4",
        points=(
            POWER_T_BRANCH_ANCHOR,
            POWER_JUNCTION_INPUT_COUPLING_END_ANCHOR,
        ),
    )
    POWER_EV_REDUCER_END_ANCHOR=ComponentAnchor(
        "power_ev_reducer",
        position=(
            CARLON_E950GF_REDUCER_BUSHING.size[0],
            CARLON_E950GF_REDUCER_BUSHING.size[1]/2,
        ),
    )
    conduits.add(
        "power_ev_charger_feed",
        trade_size="1",
        points=(
            POWER_EV_REDUCER_END_ANCHOR,
            POWER_EV_ENTRY_ANCHOR,
        ),
    )

    POWER_LIGHT_COUPLING_END=(
        POWER_JUNCTION_RIGHT_X
        + CARLON_E996D_BOX_ADAPTER.size[0]/2
        + CARLON_E940D_COUPLING.size[0],
        POWER_JUNCTION_LIGHT_PORT_Y,
        POWER_JUNCTION_OUTLET_PORT_Z,
    )
    power_light_entry=FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT
    POWER_LIGHT_POST_X=(
        members["post_fr"].min_on("x")
        - CONDUIT_OD_BY_TRADE_SIZE["1/2"]/2
    )
    POWER_LIGHT_HORIZONTAL_RUN_Z=(
        members["front_street_light_backer_bottom"].center_on("z")
        - HEIGHT_2x4/2
    )
    conduits.add(
        "power_street_light_feed",
        trade_size="1/2",
        points=(
            ComponentAnchor(
                "power_junction_light_coupling",
                position=(
                    CARLON_E940D_COUPLING.size[0],
                    CARLON_E940D_COUPLING.size[1]/2,
                ),
            ),
            _member_relative_coord(
                "post_fr",
                POWER_LIGHT_POST_X,
                POWER_JUNCTION_LIGHT_PORT_Y,
                POWER_JUNCTION_OUTLET_PORT_Z,
            ),
            _member_relative_coord(
                "post_fr",
                POWER_LIGHT_POST_X,
                power_light_entry[1],
                POWER_LIGHT_HORIZONTAL_RUN_Z,
            ),
            _member_relative_coord(
                "front_street_light_backer_bottom",
                power_light_entry[0],
                power_light_entry[1],
                POWER_LIGHT_HORIZONTAL_RUN_Z,
            ),
            FRONT_STREET_LIGHT_CONDUIT_ENTRY_ANCHOR,
        ),
        bends=(
            ConduitBend(point_index=1, radius=2.5),
            ConduitBend(point_index=2, radius=3),
            ConduitBend(point_index=3, radius=3),
        ),
    )

    POWER_OUTLET_COUPLING_END_X=(
        POWER_JUNCTION_RIGHT_X
        + CARLON_E996D_BOX_ADAPTER.size[0]/2
        + CARLON_E940D_COUPLING.size[0]
    )
    conduits.add(
        "power_back_right_outlet_feed",
        trade_size="1/2",
        points=(
            _member_relative_coord(
                "front_center_rail",
                POWER_OUTLET_COUPLING_END_X,
                POWER_JUNCTION_PORT_Y,
                POWER_JUNCTION_OUTLET_PORT_Z,
            ),
            _member_relative_coord(
                "post_br",
                BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[0],
                POWER_JUNCTION_PORT_Y,
                POWER_JUNCTION_OUTLET_PORT_Z,
            ),
            _member_relative_coord(
                "post_br",
                BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[0],
                BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[1],
                POWER_JUNCTION_OUTLET_PORT_Z,
            ),
            BACK_RIGHT_OUTLET_CONDUIT_ENTRY,
        ),
        bends=(
            ConduitBend(point_index=1, radius=4),
            ConduitBend(point_index=2, radius=4),
        ),
    )

    LOW_VOLTAGE_INPUT_ADAPTER_END_Z=(
        LOW_VOLTAGE_BOX_BOTTOM_Z-CARLON_E943E_MALE_TERMINAL_ADAPTER.size[0]
    )
    LOW_VOLTAGE_GROUND_Z=grounds[0].resolved(members).z_at(
        LOW_VOLTAGE_INPUT_X,
        LOW_VOLTAGE_INPUT_Y,
    )
    conduits.add(
        "low_voltage_ground_riser",
        assembly="low_voltage_conduit",
        trade_size="3/4",
        points=(
            _member_relative_coord(
                "post_fr",
                LOW_VOLTAGE_INPUT_X,
                LOW_VOLTAGE_INPUT_Y,
                LOW_VOLTAGE_GROUND_Z,
            ),
            _member_relative_coord(
                "post_fr",
                LOW_VOLTAGE_INPUT_X,
                LOW_VOLTAGE_INPUT_Y,
                LOW_VOLTAGE_INPUT_ADAPTER_END_Z,
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

    siding = CompositeSiding(
        "enclosure_siding",
        min_x=0,
        max_x=FRAME_DIMS.x + WIDTH_4x4,
        min_y=0,
        max_y=FRAME_DIMS.y + WIDTH_4x4,
        frame_top_z=FRAME_DIMS.z,
        roof_support_z=FRAME_DIMS.z+ROOF_SHIM_THICKNESS,
        bottom_z=SIDING_BOTTOM_Z,
        rear_opening_min_x=TAMBOUR_LEFT_X,
        rear_opening_max_x=TAMBOUR_RIGHT_X,
        rear_opening_top_z=TAMBOUR_TOP_Z,
        front_openings=(FRONT_STREET_LIGHT_SIDING_OPENING,),
        right_openings=(BACK_RIGHT_OUTLET_SIDING_OPENING,),
        stock_length=SIDING_STOCK_LENGTH_FT * 12,
        board_thickness=SIDING_BOARD_THICKNESS,
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


    def _hold_then_sweep_centerline_x(
        points: tuple[tuple[float, float, float], ...],
        hold_x: float,
        end_x: float,
        hold_until_z: float,
    ) -> tuple[tuple[float, float, float], ...]:
        lowest_index=min(range(len(points)), key=lambda index: points[index][2])
        sweep_start_index=next(
            index
            for index in range(lowest_index, len(points))
            if points[index][2] >= hold_until_z
        )
        sweep_lengths=[0.0]
        for start,end in zip(points[sweep_start_index:], points[sweep_start_index+1:]):
            sweep_lengths.append(sweep_lengths[-1]+math.dist(start, end))
        sweep_length=sweep_lengths[-1]

        held=[(hold_x, point[1], point[2]) for point in points[:sweep_start_index]]
        for point,length in zip(
            points[sweep_start_index:],
            sweep_lengths,
            strict=True,
        ):
            progress=length/sweep_length
            eased=progress**3*(progress*(progress*6-15)+10)
            held.append(
                (
                    hold_x+(end_x-hold_x)*eased,
                    point[1],
                    point[2],
                )
            )
        return tuple(held)


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
    LOW_VOLTAGE_RAIL_FB_CLEAR_Z=(
        members["rail_fb"].max_on("z")
        + LOW_VOLTAGE_CABLE_DIAMETER/2
        + LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS
    )
    LOW_VOLTAGE_POST_FL_POS_X=(
        members["post_fl"].max_on("x")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
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
    LOW_VOLTAGE_BRACE_UNDERSIDE_Z=(
        members["brace_fl_fr"].min_on("z")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_SERVICE_LOOP_TOP_Z=LOW_VOLTAGE_BRACE_UNDERSIDE_Z-2.5

    path_1_start=(LOW_VOLTAGE_GLAND_XS[0], LOW_VOLTAGE_GLAND_Y, LOW_VOLTAGE_GLAND_END_Z)
    path_1_post=(
        LOW_VOLTAGE_POST_FL_POS_X,
        members["post_fl"].center_on("y"),
        16,
    )
    PATH_1_EXIT_SPLINE_HANDLE=1.5
    path_1_exit_direction=(
        path_1_post[0]-path_1_start[0],
        path_1_post[1]-path_1_start[1],
    )
    path_1_exit_direction_length=math.hypot(*path_1_exit_direction)
    path_1_exit_unit=(
        path_1_exit_direction[0]/path_1_exit_direction_length,
        path_1_exit_direction[1]/path_1_exit_direction_length,
    )
    path_1_spline_bottom=(
        (path_1_start[0]+path_1_post[0])/2,
        (path_1_start[1]+path_1_post[1])/2,
        LOW_VOLTAGE_GLAND_EXIT_BOTTOM_Z,
    )
    PATH_1_BRIDGE_LEFT_X=LOW_VOLTAGE_POST_FL_POS_X+3.9375
    PATH_1_LOOP_LEFT_X=FRONT_STREET_LIGHT_CENTER_X-3.25
    PATH_1_LOOP_INNER_X=FRONT_STREET_LIGHT_CENTER_X-1.75
    PATH_1_LOOP_RIGHT_X=FRONT_STREET_LIGHT_CENTER_X+1.75
    path_1_points=_join_centerline_sections(
        cubic_bezier_points(
            path_1_start,
            (path_1_start[0], path_1_start[1], path_1_start[2]-2),
            (
                path_1_spline_bottom[0]
                - path_1_exit_unit[0]*PATH_1_EXIT_SPLINE_HANDLE,
                path_1_spline_bottom[1]
                - path_1_exit_unit[1]*PATH_1_EXIT_SPLINE_HANDLE,
                path_1_spline_bottom[2],
            ),
            path_1_spline_bottom,
        ),
        cubic_bezier_points(
            path_1_spline_bottom,
            (
                path_1_spline_bottom[0]
                + path_1_exit_unit[0]*PATH_1_EXIT_SPLINE_HANDLE,
                path_1_spline_bottom[1]
                + path_1_exit_unit[1]*PATH_1_EXIT_SPLINE_HANDLE,
                path_1_spline_bottom[2],
            ),
            (path_1_post[0], path_1_post[1], path_1_post[2]-3),
            path_1_post,
        ),
        rounded_cable_points(
            (
                path_1_post,
                (path_1_post[0], path_1_post[1], LOW_VOLTAGE_BRACE_UNDERSIDE_Z),
                (
                    PATH_1_BRIDGE_LEFT_X,
                    path_1_post[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
            ),
            {1: 2},
        ),
        cubic_bezier_points(
            (
                PATH_1_BRIDGE_LEFT_X,
                path_1_post[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_BRIDGE_LEFT_X+1,
                path_1_post[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_LOOP_LEFT_X-1,
                FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_LOOP_LEFT_X,
                FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
        ),
        rounded_cable_points(
            (
                (
                    PATH_1_LOOP_LEFT_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
                (
                    PATH_1_LOOP_INNER_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
                (
                    PATH_1_LOOP_INNER_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_SERVICE_LOOP_TOP_Z,
                ),
                (
                    PATH_1_LOOP_RIGHT_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_SERVICE_LOOP_TOP_Z,
                ),
                (
                    PATH_1_LOOP_RIGHT_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
                (
                    FRONT_STREET_LIGHT_CENTER_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
            ),
            {1: 1.25, 2: 1.25, 3: 1.25, 4: 1.25},
        ),
    )

    LOW_VOLTAGE_WIFI_LANE_OFFSET=-LOW_VOLTAGE_CABLE_DIAMETER/2
    LOW_VOLTAGE_CHARGER_LANE_OFFSET=LOW_VOLTAGE_CABLE_DIAMETER/2
    LOW_VOLTAGE_WIFI_X_SWEEP_END_Z=10.25
    LOW_VOLTAGE_WIFI_FACE_CENTER_Z=15
    LOW_VOLTAGE_CENTER_GLAND_HOLD_X_UNTIL_Z=10

    wifi=components["front_wifi_access_point"].resolved(members["right_center_rail"])
    path_2_start=(LOW_VOLTAGE_GLAND_XS[2], LOW_VOLTAGE_GLAND_Y, LOW_VOLTAGE_GLAND_END_Z)
    path_2_riser_bypass=(
        LOW_VOLTAGE_INPUT_X
        + LOW_VOLTAGE_RISER_CABLE_CLEARANCE
        + LOW_VOLTAGE_CABLE_DIAMETER,
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
        LOW_VOLTAGE_RAIL_FB_CLEAR_Z,
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
        (path_2_start[0], path_2_start[1], path_2_start[2]-2.5),
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
        (path_2_riser_climb[0], path_2_riser_climb[1], path_2_riser_climb[2]+1.8),
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
                (path_2_front_rail[0], path_2_front_rail[1], 40),
                (path_2_front_rail[0], path_2_top_clear[1], 40),
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
        LOW_VOLTAGE_RAIL_FB_CLEAR_Z,
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
            (path_3_start[0], path_3_start[1], path_3_start[2]-2.5),
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
    path_3_lower_points=_hold_then_sweep_centerline_x(
        path_3_lower_yz,
        path_3_start[0],
        path_3_front_rail[0],
        LOW_VOLTAGE_CENTER_GLAND_HOLD_X_UNTIL_Z,
    )
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
        (
            "low_voltage_street_light_service",
            path_1_points,
            LOW_VOLTAGE_STREET_LIGHT_COLOR,
        ),
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
                "continuous_pt_roof_shim",
                "roof_shims",
                f"continuous ripped PT lumber, {ROOF_SHIM_THICKNESS:g} in thick",
                4,
            ),
        ),
        xygrid_origin=(
            members["post_fr"].max_on("x"),
            members["post_fr"].min_on("y"),
        ),
        build_steps=(
            BUILD_STEPS
            if (width, depth, height)
            == (DEFAULT_WIDTH, DEFAULT_DEPTH, DEFAULT_HEIGHT)
            else ()
        ),
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
    generate_gusset_dxf(output_dir / "gusset_plate_6x6.dxf")
    generate_tambour_fabrication(
        output_dir / "tambour",
        config=enclosure.TAMBOUR_FABRICATION,
    )


def _playground_model_text(model_path: Path) -> str:
    """Return a Playground-ready model without changing the local output."""

    model_text = model_path.read_text()
    if LOCAL_MESH_PATH not in model_text:
        raise ValueError(
            f"generated model does not reference the expected mesh path: "
            f"{LOCAL_MESH_PATH}"
        )
    return model_text.replace(LOCAL_MESH_PATH, PLAYGROUND_MESH_PATH)


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
        help=f"above-grade frame height (default: {DEFAULT_HEIGHT:g})",
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
