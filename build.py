from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

from lumber_model import (
    CARLON_E980DFN_HUB_DEPTH,
    CARLON_E980DFN_OUTLET_BOX,
    CARLON_E983G_CONDUIT_T_BODY,
    CARLON_E986G_LB_CONDUIT_BODY,
    CARLON_E940D_COUPLING,
    CARLON_E940F_COUPLING,
    CARLON_E940G_COUPLING,
    CARLON_E943E_MALE_TERMINAL_ADAPTER,
    CARLON_E950GF_REDUCER_BUSHING,
    CARLON_E987N_JUNCTION_BOX,
    CARLON_E996D_BOX_ADAPTER,
    CARLON_E996F_BOX_ADAPTER,
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
    BuildStep,
    CableCollection,
    ComponentCollection,
    ComponentAnchor,
    CompositeSiding,
    ConduitBend,
    ConduitCollection,
    GroundPlane,
    FrontSidingOpening,
    LumberCollection,
    Model,
    RelativeCoord,
    RightSidingOpening,
    TambourBend,
    TambourCollection,
    cubic_bezier_conduit_points,
    cubic_bezier_points,
    ev_charger_cable_points,
    minimum_cable_bend_radius,
    parse_build_steps,
    rounded_cable_points,
)

DEFAULT_WIDTH = 24
DEFAULT_DEPTH = 18.375
DEFAULT_HEIGHT = 47
PowerConduitLayout = Literal[
    "junction-spline",
    "charger-riser",
    "junction-riser",
]
DEFAULT_POWER_CONDUIT_LAYOUT: PowerConduitLayout = "junction-spline"
POWER_CONDUIT_LAYOUTS: tuple[PowerConduitLayout, ...] = (
    "junction-spline",
    "charger-riser",
    "junction-riser",
)
BUILD_STEPS_PATH = Path(__file__).with_name("BUILD_STEPS.md")
JUNCTION_SPLINE_BUILD_STEPS = parse_build_steps(BUILD_STEPS_PATH)
PLAYGROUND_MODEL_URL = "https://ditdafivo.github.io/ev-charger-enclosure/"
PLAYGROUND_DEPLOY_BRANCH = "pages-source"
PLAYGROUND_DEPLOY_PATH = "pages/model.scad"
PLAYGROUND_REMOTE = "origin"
LOCAL_MESH_PATH = "../assets/components/ev_charger_plug/ev_charger_plug.stl"
PLAYGROUND_MESH_PATH = "ev_charger_plug.stl"


def _charger_riser_build_steps(
    steps: tuple[BuildStep, ...],
) -> tuple[BuildStep, ...]:
    """Translate the default spline objects to the T-body layout."""

    translated: list[BuildStep] = []
    for step in steps:
        object_names: list[str] = []
        for name in step.object_names:
            if name in (
                "power_junction_ev_adapter",
                "power_junction_ev_coupling",
            ):
                continue
            if name == "power_ev_charger_feed":
                object_names.extend(
                    (
                        "power_ev_t_body",
                        "power_ev_reducer",
                        "power_t_junction_feed",
                        name,
                    )
                )
            else:
                object_names.append(name)
        translated.append(BuildStep(step.number, tuple(object_names)))
    return tuple(translated)


def _junction_riser_build_steps(
    steps: tuple[BuildStep, ...],
) -> tuple[BuildStep, ...]:
    """Translate the default spline objects to the legacy LB-based layout."""

    translated: list[BuildStep] = []
    for step in steps:
        object_names: list[str] = []
        for name in step.object_names:
            if name == "power_ev_charger_feed":
                object_names.extend(
                    (
                        "power_ev_lb_body",
                        "power_ev_reducer",
                        "power_ev_lb_feed",
                        name,
                    )
                )
            else:
                object_names.append(name)
        translated.append(BuildStep(step.number, tuple(object_names)))
    return tuple(translated)


CHARGER_RISER_BUILD_STEPS = _charger_riser_build_steps(
    JUNCTION_SPLINE_BUILD_STEPS
)
JUNCTION_RISER_BUILD_STEPS = _junction_riser_build_steps(
    JUNCTION_SPLINE_BUILD_STEPS
)


@dataclass(frozen=True)
class EnclosureBuild:
    """A complete enclosure model and the geometry used to construct it."""

    width: float
    depth: float
    height: float
    power_conduit_layout: PowerConduitLayout
    members: LumberCollection
    components: ComponentCollection
    conduits: ConduitCollection
    cables: CableCollection
    grounds: list[GroundPlane]
    tambours: TambourCollection
    siding: CompositeSiding
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
    power_conduit_layout: PowerConduitLayout = DEFAULT_POWER_CONDUIT_LAYOUT,
) -> EnclosureBuild:
    """Build an enclosure for the requested post centerline spacing, in inches."""

    width = _finite_positive_dimension(width, "width")
    depth = _finite_positive_dimension(depth, "depth")
    height = _finite_positive_dimension(height, "height")
    if power_conduit_layout not in POWER_CONDUIT_LAYOUTS:
        raise ValueError(
            "power_conduit_layout must be one of "
            f"{POWER_CONDUIT_LAYOUTS}, got {power_conduit_layout!r}"
        )

    FRAME_DIMS=AbsoluteCoord(width, depth, height)
    BURIED_FRAME_Z=36
    FULL_POST_LEN=BURIED_FRAME_Z+FRAME_DIMS.z
    SIDING_BOTTOM_Z=2
    SIDING_STOCK_LENGTH_FT=16
    SIDING_BOARD_THICKNESS=1
    TAMBOUR_DOOR_COLOR=(0.10, 0.12, 0.14, 1.0)

    HEIGHT_2x4=1.5
    HALF_HEIGHT_2x4=HEIGHT_2x4/2
    WIDTH_4x4=3.5

    members = LumberCollection()

    members.add(
        "post_fl",
        assembly="posts",
        type="4x4",
        axis="z",
        start=AbsoluteCoord(0, 0, -BURIED_FRAME_Z),
        length=FULL_POST_LEN,
    )

    members.add(
        "post_fr",
        assembly="posts",
        type="4x4",
        axis="z",
        start=RelativeCoord("post_fl", FRAME_DIMS.x, 0, 0),
        length=FULL_POST_LEN,
    )

    members.add(
        "post_bl",
        assembly="posts",
        type="4x4",
        axis="z",
        start=RelativeCoord("post_fl", 0, FRAME_DIMS.y, 0),
        length=FULL_POST_LEN,
    )

    members.add(
        "post_br",
        assembly="posts",
        type="4x4",
        axis="z",
        start=RelativeCoord("post_fl", FRAME_DIMS.x, FRAME_DIMS.y, 0),
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


    for name,support_a,support_b in [
        ("brace_fl_fr","post_fl","post_fr"),
        ("brace_fl_bl","post_fl","post_bl"),
        ("brace_bl_br","post_bl","post_br"),
        ("brace_fr_br","post_fr","post_br"),
    ]:
        members.between(
            name,
            assembly="frame",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=FRAME_DIMS.z-HALF_HEIGHT_2x4,
        )

    for name,support_a,support_b in [
        ("brace_bl_fr","post_bl","post_fr"),
        ("brace_br_fl","post_br","post_fl"),
    ]:
        members.diagonal_between(
            name,
            assembly="frame",
            type="2x4",
            support_a=support_a,
            support_b=support_b,
            position=FRAME_DIMS.z-HALF_HEIGHT_2x4,
        )

    CENTER_RAIL_OFFSET=-3
    TAMBOUR_TOP_OFFSET=2
    UPPER_RAIL_OFFSET=3.5

    for name,support_a,support_b,position,cross_offset,position_axis, rotated in [
        ("rail_rb","post_fr","post_br", 7, 0, None, True),
        ("rail_lb","post_fl","post_bl", 7, 0, None, True),
        ("rail_fb","rail_lb","rail_rb", 7, CENTER_RAIL_OFFSET, None, True),
        ("rail_rbu","post_fr","post_br", 12, 0, None, True),
        ("rail_r_tambour","post_fr","post_br", FRAME_DIMS.z-TAMBOUR_TOP_OFFSET, 0, None, True),
        ("rail_l_tambour","post_fl","post_bl", FRAME_DIMS.z-TAMBOUR_TOP_OFFSET, 0, None, True),
        ("rail_rt","post_fr","post_br", FRAME_DIMS.z-UPPER_RAIL_OFFSET, 0, None, True),
        ("rail_lt","post_fl","post_bl", FRAME_DIMS.z-UPPER_RAIL_OFFSET, 0, None, True),
        (
            "rail_ft",
            "rail_rt",
            "rail_lt",
            FRAME_DIMS.z-UPPER_RAIL_OFFSET,
            CENTER_RAIL_OFFSET,
            None,
            True,
        ),
        ("front_center_rail","rail_fb","rail_ft",(WIDTH_4x4+FRAME_DIMS.x)/2, 0, None, False),
        ("right_center_rail","rail_rbu","rail_rt",(WIDTH_4x4+FRAME_DIMS.y)/2, 0, "y", True),
        ("right_tambour_rail","rail_rbu","rail_rt", 4.25, 0, "y", True),
        ("left_tambour_rail","rail_lb","rail_lt", 4.25, 0, "y", True),
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
    FRONT_STREET_LIGHT_FACE_PROJECTION=0
    FRONT_STREET_LIGHT_BOX_FACE_Y=(
        -SIDING_BOARD_THICKNESS - FRONT_STREET_LIGHT_FACE_PROJECTION
    )
    FRONT_STREET_LIGHT_BOX_BACK_Y=(
        FRONT_STREET_LIGHT_BOX_FACE_Y
        + COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2]
        + COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING.size[2]
    )
    FRONT_STREET_LIGHT_BACKER_CROSS_OFFSET=(
        FRONT_STREET_LIGHT_BOX_BACK_Y
        + HEIGHT_2x4 / 2
        - WIDTH_4x4 / 2
    )
    FRONT_STREET_LIGHT_BACKER_CENTER_OFFSET=3.5 / 2

    for name,position in [
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

    FRONT_STREET_LIGHT_CONDUIT_ENTRY=_member_relative_coord(
        "post_fl",
        FRONT_STREET_LIGHT_CENTER_X,
        (
            FRONT_STREET_LIGHT_BOX_BACK_Y
            - COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[2] / 2
        ),
        (
            FRONT_STREET_LIGHT_CENTER_Z
            - COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX.size[1] / 2
        ),
    )
    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT=(
        FRONT_STREET_LIGHT_CONDUIT_ENTRY.resolve(members)
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

    POWER_JUNCTION_X=(members["front_center_rail"].center_on("x")+1.25)
    POWER_JUNCTION_PORT_Y=(members["front_center_rail"].min_on("y")-1)
    POWER_JUNCTION_GROUND_Z=grounds[0].resolved(members).z_at(
        POWER_JUNCTION_X,
        POWER_JUNCTION_PORT_Y,
    )
    POWER_JUNCTION_BOTTOM_Z=POWER_JUNCTION_GROUND_Z+6
    POWER_JUNCTION_TOP_Z=(
        POWER_JUNCTION_BOTTOM_Z + CARLON_E987N_JUNCTION_BOX.size[0]
    )
    POWER_JUNCTION_CENTER_Z=(POWER_JUNCTION_BOTTOM_Z+POWER_JUNCTION_TOP_Z)/2
    POWER_JUNCTION_CENTER_Y=(
        members["front_center_rail"].min_on("y")
        - CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    POWER_JUNCTION_RIGHT_X=(
        POWER_JUNCTION_X + CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    POWER_JUNCTION_EV_PORT_X=POWER_JUNCTION_X+0.875
    POWER_JUNCTION_EV_PORT_Y=members["front_center_rail"].min_on("y")
    POWER_JUNCTION_EV_PORT_Z=POWER_JUNCTION_CENTER_Z
    POWER_JUNCTION_LIGHT_PORT_X=POWER_JUNCTION_X-1.25
    POWER_JUNCTION_LIGHT_PORT_Y=(POWER_JUNCTION_PORT_Y-2)
    POWER_JUNCTION_OUTLET_PORT_Z=POWER_JUNCTION_CENTER_Z

    # In the charger-riser layout the #6 group bypasses the junction through the
    # T body; only the #12 supply and branch-circuit groups enter this box.
    if power_conduit_layout == "charger-riser":
        POWER_JUNCTION_BOX_FILL=BoxFillCalculation(
            marked_volume=49,
            conductor_groups=((12, 7),),
            equipment_grounding_awgs=(12, 12, 12),
        )
    else:
        POWER_JUNCTION_BOX_FILL=BoxFillCalculation(
            marked_volume=49,
            conductor_groups=((6, 3), (12, 7)),
            equipment_grounding_awgs=(6, 6, 12, 12, 12),
        )
    POWER_JUNCTION_BOX_FILL.validate()
    POWER_EV_LB_FILL=None
    if power_conduit_layout == "junction-riser":
        POWER_EV_LB_FILL=BoxFillCalculation(
            marked_volume=32,
            conductor_groups=((6, 3),),
            equipment_grounding_awgs=(6,),
        )
        POWER_EV_LB_FILL.validate()

    LOW_VOLTAGE_BOX_CENTER_Z=13
    LOW_VOLTAGE_BOX_FRONT_SETBACK=0.25
    LOW_VOLTAGE_BOX_CENTER_Y=(
        members["post_fr"].min_on("y")
        + LOW_VOLTAGE_BOX_FRONT_SETBACK
        + CARLON_E987N_JUNCTION_BOX.size[1]/2
    )
    LOW_VOLTAGE_BOX_REAR_X=members["post_fr"].min_on("x")
    LOW_VOLTAGE_BOX_BOTTOM_Z=(
        LOW_VOLTAGE_BOX_CENTER_Z - CARLON_E987N_JUNCTION_BOX.size[0]/2
    )
    LOW_VOLTAGE_INPUT_X=members["post_fr"].min_on("x")-3
    LOW_VOLTAGE_INPUT_Y=LOW_VOLTAGE_BOX_CENTER_Y
    LOW_VOLTAGE_GLAND_X=members["post_fr"].min_on("x")-1
    LOW_VOLTAGE_GLAND_SPACING=1.2
    LOW_VOLTAGE_GLAND_YS=tuple(
        LOW_VOLTAGE_BOX_CENTER_Y + index*LOW_VOLTAGE_GLAND_SPACING
        for index in (-1, 0, 1)
    )
    LOW_VOLTAGE_CABLE_DIAMETER=1/8
    LOW_VOLTAGE_MINIMUM_BEND_RADIUS=5*LOW_VOLTAGE_CABLE_DIAMETER

    components = ComponentCollection()

    components.add(
        "low_voltage_termination_box",
        assembly="low_voltage_fittings",
        component_type=CARLON_E987N_JUNCTION_BOX,
        member="post_fr",
        at=LOW_VOLTAGE_BOX_CENTER_Z-members["post_fr"].min_on("z"),
        face="wide_neg",
        offset=(
            0,
            LOW_VOLTAGE_BOX_CENTER_Y-members["post_fr"].center_on("y"),
            0,
        ),
    )

    components.add(
        "low_voltage_input_adapter",
        assembly="low_voltage_fittings",
        component_type=CARLON_E943E_MALE_TERMINAL_ADAPTER,
        member="post_fr",
        at=LOW_VOLTAGE_BOX_BOTTOM_Z-members["post_fr"].min_on("z"),
        face="wide_neg",
        offset=(
            0,
            members["post_fr"].center_on("y")-LOW_VOLTAGE_INPUT_Y,
            LOW_VOLTAGE_BOX_REAR_X-LOW_VOLTAGE_INPUT_X,
        ),
        orientation="down",
    )

    for index,gland_y in enumerate(LOW_VOLTAGE_GLAND_YS, start=1):
        components.add(
            f"low_voltage_cable_gland_{index}",
            assembly="low_voltage_fittings",
            component_type=ONE_INCH_CABLE_GLAND,
            member="post_fr",
            at=LOW_VOLTAGE_BOX_BOTTOM_Z-members["post_fr"].min_on("z"),
            face="wide_neg",
            offset=(
                0,
                members["post_fr"].center_on("y")-gland_y,
                LOW_VOLTAGE_BOX_REAR_X-LOW_VOLTAGE_GLAND_X,
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
        at=24.5,
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
        offset=(0, POWER_JUNCTION_X-members["front_center_rail"].center_on("x"), 0),
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

    if power_conduit_layout == "charger-riser":
        # The T's local along axis is vertical. Its side channel points along
        # negative Y, while the main channel is coaxial with the charger port.
        POWER_T_MAIN_CHANNEL_WIDTH=2+5/16
        POWER_T_AXIS_X=POWER_EV_ENTRY[0]
        POWER_T_AXIS_Y=POWER_EV_ENTRY[1]
        POWER_T_CENTER_Z=POWER_JUNCTION_CENTER_Z
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

        # The former input adapter/coupling move to the box's rear face and
        # receive the T's 1-1/4-inch negative-Y branch.
        POWER_JUNCTION_INPUT_PORT_X=POWER_T_AXIS_X
        POWER_JUNCTION_INPUT_PORT_Y=members["front_center_rail"].min_on("y")
        POWER_JUNCTION_INPUT_PORT_Z=POWER_T_CENTER_Z
        components.add(
            "power_junction_input_adapter",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E996G_BOX_ADAPTER,
            member="front_center_rail",
            at=(
                POWER_JUNCTION_INPUT_PORT_Z
                - members["front_center_rail"].min_on("z")
            ),
            face="wide_neg",
            offset=(
                0,
                POWER_JUNCTION_INPUT_PORT_X
                - members["front_center_rail"].center_on("x"),
                0,
            ),
            orientation="inward",
        )
        components.add(
            "power_junction_input_coupling",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E940G_COUPLING,
            member="front_center_rail",
            at=(
                POWER_JUNCTION_INPUT_PORT_Z
                - members["front_center_rail"].min_on("z")
            ),
            face="wide_neg",
            offset=(
                CARLON_E996G_BOX_ADAPTER.size[0]/2,
                POWER_JUNCTION_INPUT_PORT_X
                - members["front_center_rail"].center_on("x"),
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
    elif power_conduit_layout == "junction-spline":
        # Keep the junction-riser's bottom 1-1/4-inch supply connection.
        input_adapter_position=(
            POWER_JUNCTION_BOTTOM_Z-members["front_center_rail"].min_on("z")
        )
        components.add(
            "power_junction_input_adapter",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E996G_BOX_ADAPTER,
            member="front_center_rail",
            at=max(0, input_adapter_position),
            face="wide_neg",
            offset=(
                max(0, -input_adapter_position),
                -(POWER_JUNCTION_X-members["front_center_rail"].center_on("x")),
                members["front_center_rail"].min_on("y")
                - POWER_JUNCTION_CENTER_Y,
            ),
            orientation="down",
        )
        input_coupling_z=(
            POWER_JUNCTION_BOTTOM_Z-CARLON_E996G_BOX_ADAPTER.size[0]/2
        )
        input_coupling_position=(
            input_coupling_z-members["front_center_rail"].min_on("z")
        )
        components.add(
            "power_junction_input_coupling",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E940G_COUPLING,
            member="front_center_rail",
            at=max(0, input_coupling_position),
            face="wide_neg",
            offset=(
                max(0, -input_coupling_position),
                -(POWER_JUNCTION_X-members["front_center_rail"].center_on("x")),
                members["front_center_rail"].min_on("y")
                - POWER_JUNCTION_CENTER_Y,
            ),
            orientation="down",
        )

        POWER_JUNCTION_SPLINE_PORT_X=POWER_JUNCTION_RIGHT_X-1
        POWER_JUNCTION_SPLINE_PORT_Y=(
            members["front_center_rail"].min_on("y")-1
        )
        POWER_JUNCTION_SPLINE_PORT_Z=POWER_JUNCTION_TOP_Z

        components.add(
            "power_junction_ev_adapter",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E996F_BOX_ADAPTER,
            member="front_center_rail",
            at=(
                POWER_JUNCTION_SPLINE_PORT_Z
                - members["front_center_rail"].min_on("z")
            ),
            face="wide_neg",
            offset=(
                0,
                POWER_JUNCTION_SPLINE_PORT_X
                - members["front_center_rail"].center_on("x"),
                members["front_center_rail"].min_on("y")
                - POWER_JUNCTION_SPLINE_PORT_Y,
            ),
        )
        components.add(
            "power_junction_ev_coupling",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E940F_COUPLING,
            member="front_center_rail",
            at=(
                POWER_JUNCTION_SPLINE_PORT_Z
                + CARLON_E996F_BOX_ADAPTER.size[0]/2
                - members["front_center_rail"].min_on("z")
            ),
            face="wide_neg",
            offset=(
                0,
                POWER_JUNCTION_SPLINE_PORT_X
                - members["front_center_rail"].center_on("x"),
                members["front_center_rail"].min_on("y")
                - POWER_JUNCTION_SPLINE_PORT_Y,
            ),
        )
        POWER_JUNCTION_EV_COUPLING_END_ANCHOR=ComponentAnchor(
            "power_junction_ev_coupling",
            position=(
                CARLON_E940F_COUPLING.size[0],
                CARLON_E940F_COUPLING.size[1]/2,
            ),
        )
        POWER_JUNCTION_EV_COUPLING_END=(
            POWER_JUNCTION_SPLINE_PORT_X,
            POWER_JUNCTION_SPLINE_PORT_Y,
            POWER_JUNCTION_SPLINE_PORT_Z
            + CARLON_E996F_BOX_ADAPTER.size[0]/2
            + CARLON_E940F_COUPLING.size[0],
        )
    else:
        # Bottom 1-1/4-inch junction input. Clamp the member anchor at zero
        # because the fitting connection planes sit below the raised rail.
        input_adapter_position=(
            POWER_JUNCTION_BOTTOM_Z-members["front_center_rail"].min_on("z")
        )
        components.add(
            "power_junction_input_adapter",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E996G_BOX_ADAPTER,
            member="front_center_rail",
            at=max(0, input_adapter_position),
            face="wide_neg",
            offset=(
                max(0, -input_adapter_position),
                -(POWER_JUNCTION_X-members["front_center_rail"].center_on("x")),
                1,
            ),
            orientation="down",
        )
        input_coupling_z=(
            POWER_JUNCTION_BOTTOM_Z-CARLON_E996G_BOX_ADAPTER.size[0]/2
        )
        input_coupling_position=(
            input_coupling_z-members["front_center_rail"].min_on("z")
        )
        components.add(
            "power_junction_input_coupling",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E940G_COUPLING,
            member="front_center_rail",
            at=max(0, input_coupling_position),
            face="wide_neg",
            offset=(
                max(0, -input_coupling_position),
                -(POWER_JUNCTION_X-members["front_center_rail"].center_on("x")),
                1,
            ),
            orientation="down",
        )

        components.add(
            "power_junction_ev_adapter",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E996G_BOX_ADAPTER,
            member="front_center_rail",
            at=POWER_JUNCTION_EV_PORT_Z-members["front_center_rail"].min_on("z"),
            face="wide_neg",
            offset=(
                0,
                POWER_JUNCTION_EV_PORT_X
                - members["front_center_rail"].center_on("x"),
                0,
            ),
            orientation="inward",
        )
        components.add(
            "power_junction_ev_coupling",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E940G_COUPLING,
            member="front_center_rail",
            at=POWER_JUNCTION_EV_PORT_Z-members["front_center_rail"].min_on("z"),
            face="wide_neg",
            offset=(
                CARLON_E996G_BOX_ADAPTER.size[0]/2,
                POWER_JUNCTION_EV_PORT_X
                - members["front_center_rail"].center_on("x"),
                0,
            ),
            orientation="inward",
        )

        POWER_EV_LB_OUTLET_OFFSET_Y=2+3/4-(1+63/64)/2
        POWER_EV_LB_INLET=(
            POWER_JUNCTION_EV_PORT_X,
            POWER_EV_ENTRY[1]-POWER_EV_LB_OUTLET_OFFSET_Y,
            POWER_JUNCTION_EV_PORT_Z,
        )
        components.add(
            "power_ev_lb_body",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E986G_LB_CONDUIT_BODY,
            member="front_center_rail",
            at=POWER_JUNCTION_EV_PORT_Z-members["front_center_rail"].min_on("z"),
            face="wide_neg",
            offset=(
                POWER_EV_LB_INLET[1]-POWER_JUNCTION_EV_PORT_Y,
                POWER_JUNCTION_EV_PORT_X
                - members["front_center_rail"].center_on("x"),
                0,
            ),
            orientation="inward",
        )

        POWER_EV_LB_OUTLET=(
            POWER_JUNCTION_EV_PORT_X,
            POWER_EV_ENTRY[1],
            POWER_JUNCTION_EV_PORT_Z+6,
        )
        components.add(
            "power_ev_reducer",
            assembly="electrical_conduit_fittings",
            component_type=CARLON_E950GF_REDUCER_BUSHING,
            member="front_center_rail",
            at=POWER_EV_LB_OUTLET[2]-members["front_center_rail"].min_on("z"),
            face="wide_neg",
            offset=(
                0,
                POWER_EV_LB_OUTLET[0]
                - members["front_center_rail"].center_on("x"),
                members["front_center_rail"].min_on("y")-POWER_EV_LB_OUTLET[1],
            ),
        )

    # Top-facing 1/2-inch street-light penetration.
    components.add(
        "power_junction_light_adapter",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E996D_BOX_ADAPTER,
        member="front_center_rail",
        at=POWER_JUNCTION_TOP_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(
            0,
            POWER_JUNCTION_LIGHT_PORT_X-members["front_center_rail"].center_on("x"),
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_LIGHT_PORT_Y,
        ),
    )
    components.add(
        "power_junction_light_coupling",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E940D_COUPLING,
        member="front_center_rail",
        at=(
            POWER_JUNCTION_TOP_Z
            + CARLON_E996D_BOX_ADAPTER.size[0]/2
            - members["front_center_rail"].min_on("z")
        ),
        face="wide_neg",
        offset=(
            0,
            POWER_JUNCTION_LIGHT_PORT_X-members["front_center_rail"].center_on("x"),
            members["front_center_rail"].min_on("y")-POWER_JUNCTION_LIGHT_PORT_Y,
        ),
    )

    # Right-side 1/2-inch outlet penetration.
    components.add(
        "power_junction_outlet_adapter",
        assembly="electrical_conduit_fittings",
        component_type=CARLON_E996D_BOX_ADAPTER,
        member="front_center_rail",
        at=POWER_JUNCTION_OUTLET_PORT_Z-members["front_center_rail"].min_on("z"),
        face="wide_neg",
        offset=(POWER_JUNCTION_RIGHT_X-members["front_center_rail"].center_on("x"), 0, 1),
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
            1,
        ),
        orientation="left",
    )

    conduits = ConduitCollection()

    if power_conduit_layout == "charger-riser":
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
    elif power_conduit_layout == "junction-spline":
        POWER_JUNCTION_SPLINE_GROUND_Z=grounds[0].resolved(members).z_at(
            POWER_JUNCTION_X,
            POWER_JUNCTION_CENTER_Y,
        )
        POWER_INPUT_COUPLING_END_Z=(
            POWER_JUNCTION_BOTTOM_Z
            - CARLON_E996G_BOX_ADAPTER.size[0]/2
            - CARLON_E940G_COUPLING.size[0]
        )
        conduits.add(
            "power_ground_riser",
            trade_size="1-1/4",
            points=(
                _member_relative_coord(
                    "front_center_rail",
                    POWER_JUNCTION_X,
                    POWER_JUNCTION_CENTER_Y,
                    POWER_JUNCTION_SPLINE_GROUND_Z,
                ),
                _member_relative_coord(
                    "front_center_rail",
                    POWER_JUNCTION_X,
                    POWER_JUNCTION_CENTER_Y,
                    POWER_INPUT_COUPLING_END_Z,
                ),
            ),
        )

        POWER_EV_OFFSET_CONTROL_A=(
            POWER_JUNCTION_EV_COUPLING_END[0],
            POWER_JUNCTION_EV_COUPLING_END[1],
            POWER_JUNCTION_EV_COUPLING_END[2]+2,
        )
        POWER_EV_OFFSET_CONTROL_B=(
            POWER_EV_ENTRY[0],
            POWER_EV_ENTRY[1],
            POWER_EV_ENTRY[2]-2,
        )
        power_ev_offset_points=list(
            cubic_bezier_conduit_points(
                POWER_JUNCTION_EV_COUPLING_END,
                POWER_EV_OFFSET_CONTROL_A,
                POWER_EV_OFFSET_CONTROL_B,
                POWER_EV_ENTRY,
            )
        )
        power_ev_offset_points[0]=POWER_JUNCTION_EV_COUPLING_END_ANCHOR
        power_ev_offset_points[-1]=POWER_EV_ENTRY_ANCHOR
        conduits.add(
            "power_ev_charger_feed",
            trade_size="1",
            points=tuple(power_ev_offset_points),
        )
    else:
        POWER_INPUT_COUPLING_END_Z=(
            POWER_JUNCTION_BOTTOM_Z
            - CARLON_E996G_BOX_ADAPTER.size[0]/2
            - CARLON_E940G_COUPLING.size[0]
        )
        conduits.add(
            "power_ground_riser",
            trade_size="1-1/4",
            points=(
                _member_relative_coord(
                    "front_center_rail",
                    POWER_JUNCTION_X,
                    POWER_JUNCTION_PORT_Y,
                    POWER_JUNCTION_GROUND_Z,
                ),
                _member_relative_coord(
                    "front_center_rail",
                    POWER_JUNCTION_X,
                    POWER_JUNCTION_PORT_Y,
                    POWER_INPUT_COUPLING_END_Z,
                ),
            ),
        )

        POWER_EV_COUPLING_END=(
            POWER_JUNCTION_EV_PORT_X,
            POWER_JUNCTION_EV_PORT_Y
            + CARLON_E996G_BOX_ADAPTER.size[0]/2
            + CARLON_E940G_COUPLING.size[0],
            POWER_JUNCTION_EV_PORT_Z,
        )
        conduits.add(
            "power_ev_lb_feed",
            trade_size="1-1/4",
            points=(
                AbsoluteCoord(*POWER_EV_COUPLING_END),
                AbsoluteCoord(*POWER_EV_LB_INLET),
            ),
        )

        POWER_EV_REDUCER_END=(
            POWER_EV_LB_OUTLET[0],
            POWER_EV_LB_OUTLET[1],
            POWER_EV_LB_OUTLET[2]+CARLON_E950GF_REDUCER_BUSHING.size[0],
        )
        POWER_EV_OFFSET_CONTROL_A=(
            POWER_EV_REDUCER_END[0],
            POWER_EV_REDUCER_END[1],
            POWER_EV_REDUCER_END[2]+2,
        )
        POWER_EV_OFFSET_CONTROL_B=(
            POWER_EV_ENTRY[0],
            POWER_EV_ENTRY[1],
            POWER_EV_ENTRY[2]-2,
        )
        power_ev_offset_points=cubic_bezier_conduit_points(
            POWER_EV_REDUCER_END,
            POWER_EV_OFFSET_CONTROL_A,
            POWER_EV_OFFSET_CONTROL_B,
            POWER_EV_ENTRY,
        )
        conduits.add(
            "power_ev_charger_feed",
            trade_size="1",
            points=power_ev_offset_points,
        )

    POWER_LIGHT_COUPLING_END=(
        POWER_JUNCTION_LIGHT_PORT_X,
        POWER_JUNCTION_LIGHT_PORT_Y,
        POWER_JUNCTION_TOP_Z
        + CARLON_E996D_BOX_ADAPTER.size[0]/2
        + CARLON_E940D_COUPLING.size[0],
    )
    power_light_entry=FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT
    conduits.add(
        "power_street_light_feed",
        trade_size="1/2",
        points=cubic_bezier_conduit_points(
            POWER_LIGHT_COUPLING_END,
            (
                POWER_LIGHT_COUPLING_END[0],
                POWER_LIGHT_COUPLING_END[1],
                POWER_LIGHT_COUPLING_END[2]+8,
            ),
            (
                power_light_entry[0],
                power_light_entry[1],
                power_light_entry[2]-8,
            ),
            power_light_entry,
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
    TAMBOUR_BACK_Y = members["post_bl"].max_on("y") - 0.5
    TAMBOUR_FRONT_Y = 3.75
    TAMBOUR_TOP_Z = FRAME_DIMS.z-TAMBOUR_TOP_OFFSET
    TAMBOUR_BACK_BOTTOM_Z = 3
    TAMBOUR_FRONT_BOTTOM_Z = 16
    TAMBOUR_BEND_RADIUS = 3

    tambours.add(
        "enclosure_tambour_door",
        assembly="tambour_door",
        left_points=(
            RelativeCoord(
                "post_bl",
                WIDTH_4x4,
                WIDTH_4x4-0.5,
                BURIED_FRAME_Z+TAMBOUR_BACK_BOTTOM_Z,
            ),
            RelativeCoord("post_bl", WIDTH_4x4, WIDTH_4x4-0.5, BURIED_FRAME_Z+TAMBOUR_TOP_Z),
            RelativeCoord("post_fl", WIDTH_4x4, TAMBOUR_FRONT_Y, BURIED_FRAME_Z+TAMBOUR_TOP_Z),
            RelativeCoord(
                "post_fl",
                WIDTH_4x4,
                TAMBOUR_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_FRONT_BOTTOM_Z,
            ),
        ),
        right_points=(
            RelativeCoord("post_br", 0, WIDTH_4x4-0.5, BURIED_FRAME_Z+TAMBOUR_BACK_BOTTOM_Z),
            RelativeCoord("post_br", 0, WIDTH_4x4-0.5, BURIED_FRAME_Z+TAMBOUR_TOP_Z),
            RelativeCoord("post_fr", 0, TAMBOUR_FRONT_Y, BURIED_FRAME_Z+TAMBOUR_TOP_Z),
            RelativeCoord(
                "post_fr",
                0,
                TAMBOUR_FRONT_Y,
                BURIED_FRAME_Z+TAMBOUR_FRONT_BOTTOM_Z,
            ),
        ),
        bends=(
            TambourBend(point_index=1, radius=TAMBOUR_BEND_RADIUS),
            TambourBend(point_index=2, radius=TAMBOUR_BEND_RADIUS),
        ),
        door_length=44,
        slat_color=TAMBOUR_DOOR_COLOR,
    )

    siding = CompositeSiding(
        "enclosure_siding",
        min_x=0,
        max_x=FRAME_DIMS.x + WIDTH_4x4,
        min_y=0,
        max_y=FRAME_DIMS.y + WIDTH_4x4,
        frame_top_z=FRAME_DIMS.z,
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


    LOW_VOLTAGE_GLAND_END_Z=(
        LOW_VOLTAGE_BOX_BOTTOM_Z-ONE_INCH_CABLE_GLAND.size[0]
    )
    LOW_VOLTAGE_POST_NEG_X=members["post_fr"].min_on("x")-LOW_VOLTAGE_CABLE_DIAMETER/2
    LOW_VOLTAGE_RIGHT_RAIL_POS_Y=(
        members["right_center_rail"].max_on("y")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_RIGHT_RAIL_NEG_X=(
        members["right_center_rail"].min_on("x")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_FRONT_RAIL_POS_X=(
        members["front_center_rail"].max_on("x")+LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_BRACE_UNDERSIDE_Z=(
        members["brace_fl_fr"].min_on("z")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )
    LOW_VOLTAGE_SERVICE_LOOP_TOP_Z=LOW_VOLTAGE_BRACE_UNDERSIDE_Z-2.5
    LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z=(
        members["rail_ft"].min_on("z")-LOW_VOLTAGE_CABLE_DIAMETER/2
    )

    path_1_start=(LOW_VOLTAGE_GLAND_X, LOW_VOLTAGE_GLAND_YS[0], LOW_VOLTAGE_GLAND_END_Z)
    path_1_post=(LOW_VOLTAGE_POST_NEG_X, LOW_VOLTAGE_GLAND_YS[0], 16)
    PATH_1_BRIDGE_RIGHT_X=LOW_VOLTAGE_POST_NEG_X-3.9375
    PATH_1_LOOP_RIGHT_X=FRONT_STREET_LIGHT_CENTER_X+3.25
    PATH_1_LOOP_INNER_X=FRONT_STREET_LIGHT_CENTER_X+1.75
    PATH_1_LOOP_LEFT_X=FRONT_STREET_LIGHT_CENTER_X-1.75
    path_1_points=_join_centerline_sections(
        cubic_bezier_points(
            path_1_start,
            (path_1_start[0], path_1_start[1], path_1_start[2]+2.5),
            (path_1_post[0], path_1_post[1], path_1_post[2]-2.5),
            path_1_post,
        ),
        rounded_cable_points(
            (
                path_1_post,
                (path_1_post[0], path_1_post[1], LOW_VOLTAGE_BRACE_UNDERSIDE_Z),
                (
                    PATH_1_BRIDGE_RIGHT_X,
                    path_1_post[1],
                    LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
                ),
            ),
            {1: 2},
        ),
        cubic_bezier_points(
            (
                PATH_1_BRIDGE_RIGHT_X,
                path_1_post[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_BRIDGE_RIGHT_X-1,
                path_1_post[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_LOOP_RIGHT_X+1,
                FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            (
                PATH_1_LOOP_RIGHT_X,
                FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
        ),
        rounded_cable_points(
            (
                (
                    PATH_1_LOOP_RIGHT_X,
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
                    PATH_1_LOOP_LEFT_X,
                    FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
                    LOW_VOLTAGE_SERVICE_LOOP_TOP_Z,
                ),
                (
                    PATH_1_LOOP_LEFT_X,
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

    wifi=components["front_wifi_access_point"].resolved(members["right_center_rail"])
    path_2_start=(LOW_VOLTAGE_GLAND_X, LOW_VOLTAGE_GLAND_YS[1], LOW_VOLTAGE_GLAND_END_Z)
    path_2_rail=(
        members["right_center_rail"].center_on("x"),
        LOW_VOLTAGE_RIGHT_RAIL_POS_Y,
        16,
    )
    path_2_entry=(
        wifi.box_min[0]+wifi.box_size[0]/2,
        wifi.box_min[1]+wifi.box_size[1]/2,
        wifi.box_min[2],
    )
    path_2_transition=(path_2_rail[0], path_2_rail[1], 27)
    path_2_points=_join_centerline_sections(
        cubic_bezier_points(
            path_2_start,
            (path_2_start[0], path_2_start[1], path_2_start[2]-4),
            (path_2_rail[0], path_2_rail[1], path_2_rail[2]-8),
            path_2_rail,
        ),
        (path_2_rail, path_2_transition),
        cubic_bezier_points(
            path_2_transition,
            (path_2_transition[0], path_2_transition[1], path_2_transition[2]+3),
            (path_2_entry[0], path_2_entry[1], path_2_entry[2]-3),
            path_2_entry,
        ),
    )

    charger=components["front_ev_charger_body"].resolved(members["front_center_rail"])
    path_3_start=(LOW_VOLTAGE_GLAND_X, LOW_VOLTAGE_GLAND_YS[2], LOW_VOLTAGE_GLAND_END_Z)
    path_3_rail=(
        LOW_VOLTAGE_RIGHT_RAIL_NEG_X,
        members["right_center_rail"].center_on("y"),
        16,
    )
    path_3_under_rail_y=members["rail_ft"].center_on("y")
    path_3_side_y=members["front_center_rail"].max_on("y")-LOW_VOLTAGE_CABLE_DIAMETER/2
    path_3_entry=(
        charger.box_min[0]+charger.box_size[0]/2,
        charger.box_min[1]+charger.box_size[1]/2,
        charger.box_min[2],
    )
    PATH_3_BRIDGE_RIGHT_X=LOW_VOLTAGE_RIGHT_RAIL_NEG_X-3.9375
    PATH_3_BRIDGE_LEFT_X=LOW_VOLTAGE_FRONT_RAIL_POS_X+2.4375
    path_3_u_turn_start=(LOW_VOLTAGE_FRONT_RAIL_POS_X, path_3_side_y, 25)
    path_3_points=_join_centerline_sections(
        cubic_bezier_points(
            path_3_start,
            (path_3_start[0], path_3_start[1], path_3_start[2]-4),
            (path_3_rail[0], path_3_rail[1], path_3_rail[2]-8),
            path_3_rail,
        ),
        rounded_cable_points(
            (
                path_3_rail,
                (path_3_rail[0], path_3_rail[1], LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z),
                (path_3_rail[0], path_3_under_rail_y, LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z),
                (
                    PATH_3_BRIDGE_RIGHT_X,
                    path_3_under_rail_y,
                    LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
                ),
            ),
            {1: 1.25, 2: 1.25},
        ),
        cubic_bezier_points(
            (
                PATH_3_BRIDGE_RIGHT_X,
                path_3_under_rail_y,
                LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
            ),
            (
                PATH_3_BRIDGE_RIGHT_X-1,
                path_3_under_rail_y,
                LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
            ),
            (
                PATH_3_BRIDGE_LEFT_X+1,
                path_3_side_y,
                LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
            ),
            (
                PATH_3_BRIDGE_LEFT_X,
                path_3_side_y,
                LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
            ),
        ),
        rounded_cable_points(
            (
                (
                    PATH_3_BRIDGE_LEFT_X,
                    path_3_side_y,
                    LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
                ),
                (
                    LOW_VOLTAGE_FRONT_RAIL_POS_X,
                    path_3_side_y,
                    LOW_VOLTAGE_RAIL_FT_UNDERSIDE_Z,
                ),
                path_3_u_turn_start,
            ),
            {1: 2},
        ),
        rounded_cable_points(
            (
                path_3_u_turn_start,
                (path_3_u_turn_start[0], path_3_u_turn_start[1], 19.75),
                (path_3_entry[0], path_3_entry[1], 19.75),
                path_3_entry,
            ),
            {1: 0.8, 2: 0.8},
        ),
    )

    for name,points in (
        ("low_voltage_street_light_service", path_1_points),
        ("low_voltage_wifi_feed", path_2_points),
        ("low_voltage_ev_charger_feed", path_3_points),
    ):
        measured_radius=minimum_cable_bend_radius(points)
        if measured_radius < LOW_VOLTAGE_MINIMUM_BEND_RADIUS-1e-6:
            raise ValueError(
                f"{name}: minimum bend radius {measured_radius:.3f} is below "
                f"{LOW_VOLTAGE_MINIMUM_BEND_RADIUS:.3f}"
            )
        cables.add(
            name,
            assembly="low_voltage_cabling",
            diameter=LOW_VOLTAGE_CABLE_DIAMETER,
            points=points,
        )

    model = Model(
        members,
        components=components,
        conduits=conduits,
        cables=cables,
        grounds=grounds,
        tambours=tambours,
        sidings=[siding],
        xygrid_origin=(
            members["post_fr"].max_on("x"),
            members["post_fr"].min_on("y"),
        ),
        build_steps=(
            {
                "junction-spline": JUNCTION_SPLINE_BUILD_STEPS,
                "charger-riser": CHARGER_RISER_BUILD_STEPS,
                "junction-riser": JUNCTION_RISER_BUILD_STEPS,
            }[power_conduit_layout]
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
        power_conduit_layout=power_conduit_layout,
        members=members,
        components=components,
        conduits=conduits,
        cables=cables,
        grounds=grounds,
        tambours=tambours,
        siding=siding,
        model=model,
        anchors=anchors,
    )


default_build = build_enclosure()
members = default_build.members
components = default_build.components
conduits = default_build.conduits
cables = default_build.cables
grounds = default_build.grounds
tambours = default_build.tambours
siding = default_build.siding
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
        "--power-conduit-layout",
        choices=POWER_CONDUIT_LAYOUTS,
        default=DEFAULT_POWER_CONDUIT_LAYOUT,
        help=(
            "power routing: a junction-box riser with a direct 1-inch spline, "
            "a charger riser through a T body, or the legacy junction-box LB "
            f"(default: {DEFAULT_POWER_CONDUIT_LAYOUT})"
        ),
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
            args.power_conduit_layout,
        )
        write_outputs(enclosure)
        if not args.no_deploy:
            deploy_generated_model(Path("output/model.scad"))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
