from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
from lumber_model import (
    CARLON_E987N_JUNCTION_BOX,
    CONDUIT_OD_BY_TRADE_SIZE,
    ComponentAnchor,
    RelativeCoord,
    minimum_cable_bend_radius,
)
from lumber_model.gusset import GUSSET_HOLE_CENTERS_IN
from lumber_model.fabrication import clip_polygon_to_box


class TopBracingBuildTests(unittest.TestCase):
    def test_diagonal_friction_fits_between_post_faces_without_overlapping_posts(self) -> None:
        for enclosure in (build.default_build, build.build_enclosure(width=36, depth=30)):
            brace = enclosure.members["brace_bl_fr"]
            self.assertEqual(brace.type, "1x6")
            self.assertAlmostEqual(brace.thickness, 0.75)
            self.assertAlmostEqual(brace.width, 5.5)
            self.assertAlmostEqual(brace.min[2], enclosure.height-0.75)
            self.assertAlmostEqual(brace.max[2], enclosure.height)
            self.assertIsNotNone(brace.footprint)
            footprint = brace.footprint
            assert footprint is not None
            back = enclosure.members["post_bl"]
            front = enclosure.members["post_fr"]
            self.assertAlmostEqual(brace.min[1], front.max_on("y"))
            self.assertAlmostEqual(brace.max[1], back.min_on("y"))
            for post, face_y in ((back, back.min_on("y")), (front, front.max_on("y"))):
                contact_xs = [x for x, y in footprint if math.isclose(y, face_y)]
                self.assertGreaterEqual(len(contact_xs), 2)
                self.assertLessEqual(min(contact_xs), post.min_on("x")+1e-9)
                self.assertGreaterEqual(max(contact_xs), post.max_on("x")-1e-9)
            for name in build.POST_GROUND_TO_TOP:
                post = enclosure.members[name]
                overlap = clip_polygon_to_box(
                    footprint, min_x=post.min_on("x"), max_x=post.max_on("x"),
                    min_y=post.min_on("y"), max_y=post.max_on("y"),
                )
                area = abs(sum(a[0]*b[1]-b[0]*a[1]
                               for a,b in zip(overlap, overlap[1:]+overlap[:1])))/2
                self.assertAlmostEqual(area, 0)
            self.assertAlmostEqual(
                (brace.end[1]-brace.start[1])/(brace.end[0]-brace.start[0]),
                (front.center[1]-back.center[1])/(front.center[0]-back.center[0]),
            )

    def test_all_finished_post_tops_are_level_with_bracing_flush(self) -> None:
        for name in build.POST_GROUND_TO_TOP:
            self.assertAlmostEqual(build.members[name].max_on("z"), 49.625)
            self.assertAlmostEqual(build.members[name].length, 81.625)
        self.assertAlmostEqual(build.members["brace_bl_fr"].max[2], 49.625)
        self.assertNotIn("post_cap_fl", build.members)
        self.assertNotIn("post_cap_br", build.members)

    def test_custom_dimensions_recalculate_shallow_diagonal(self) -> None:
        enclosure = build.build_enclosure(width=36, depth=30, height=55)
        brace = enclosure.members["brace_bl_fr"]

        self.assertEqual(brace.type, "1x6")
        self.assertAlmostEqual(brace.thickness, 0.75)
        self.assertAlmostEqual(brace.max[2], 55)
        self.assertAlmostEqual(brace.min[2], 54.25)
        self.assertAlmostEqual(brace.length, 47.3096271352)
        self.assertAlmostEqual(brace.width, 5.5)

        square = build.build_enclosure(width=24, depth=24, height=47)
        square_brace = square.members["brace_bl_fr"]
        self.assertAlmostEqual(square_brace.cut_angle_deg, 45)
        self.assertAlmostEqual(square_brace.width, 5.5)

    def test_reports_include_fitted_one_by_six_brace(self) -> None:
        cut_row = next(
            row
            for row in build.model.cut_list_rows(rounding_increment=None)
            if row["members"] == "brace_bl_fr"
        )
        rounded_cut_row = next(
            row
            for row in build.model.cut_list_rows(rounding_increment=1 / 16)
            if row["members"] == "brace_bl_fr"
        )
        shopping_row = next(
            row for row in build.model.shopping_list_rows() if row["type"] == "1x6"
        )
        fabrication_row = next(
            row for row in build.model.fabrication_rows()
            if row["member"] == "brace_bl_fr"
        )

        self.assertEqual(cut_row["type"], "1x6")
        self.assertEqual(cut_row["start_cut_angle_deg"], "")
        self.assertEqual(cut_row["end_cut_angle_deg"], "")
        self.assertEqual(cut_row["qty"], 1)
        self.assertEqual(rounded_cut_row["length_in"], 31.375)
        self.assertEqual(shopping_row["stock_length_in"], 72)
        self.assertEqual(shopping_row["qty"], 1)
        self.assertIn("at least 31.3694", fabrication_row["operation"])
        self.assertIn("1x6 no narrower than 5.5000", fabrication_row["operation"])
        self.assertIn("jigsaw", fabrication_row["operation"])

    def test_side_brace_rabbets_and_custom_gusset_hardware_are_explicit(self) -> None:
        self.assertEqual(len(build.routed_seats), 2)
        self.assertEqual({seat.depth for seat in build.routed_seats}, {0.75})
        self.assertEqual({seat.top_z for seat in build.routed_seats}, {49.625})
        self.assertEqual(
            {seat.member for seat in build.routed_seats},
            {"brace_fl_bl", "brace_fr_br"},
        )
        for name in ("gusset_back_left", "gusset_front_right"):
            hardware = build.components[name]
            self.assertIn(hardware.member, {"post_bl", "post_fr"})
            self.assertEqual(hardware.component_type.size, (6, 6, 0.184))
            primitives = hardware.component_type.cylinder_primitives
            self.assertEqual(len(primitives), 64)
            self.assertTrue(all(length <= 0.045 for _, _, length, _ in primitives))
            self.assertTrue(
                all(origin[2] >= 0.074 for origin, _, _, _ in primitives)
            )
            resolved = hardware.resolved(build.members[hardware.member])
            self.assertAlmostEqual(resolved.box_min[2], 49.625)
            self.assertAlmostEqual(resolved.box_size[0], 6)
            self.assertAlmostEqual(resolved.box_size[1], 6)
            self.assertAlmostEqual(resolved.box_size[2], 0.184)

            post = build.members[hardware.member]
            hole_centers = [
                (
                    resolved.origin[0]
                    + local_x * resolved.along_vec[0]
                    + local_y * resolved.across_vec[0],
                    resolved.origin[1]
                    + local_x * resolved.along_vec[1]
                    + local_y * resolved.across_vec[1],
                )
                for local_x, local_y in GUSSET_HOLE_CENTERS_IN
            ]
            post_hole_centers = [
                center
                for center in hole_centers
                if post.min_on("x") <= center[0] <= post.max_on("x")
                and post.min_on("y") <= center[1] <= post.max_on("y")
            ]
            self.assertEqual(len(post_hole_centers), 4)
            self.assertAlmostEqual(
                (
                    min(x for x, _ in post_hole_centers)
                    + max(x for x, _ in post_hole_centers)
                )
                / 2,
                post.center_on("x"),
            )
            self.assertAlmostEqual(
                (
                    min(y for _, y in post_hole_centers)
                    + max(y for _, y in post_hole_centers)
                )
                / 2,
                post.center_on("y"),
            )

        hardware_rows = {
            row["name"]: row for row in build.model.bom_rows()
            if row["category"] == "hardware"
        }
        self.assertEqual(hardware_rows["custom_6x6_g90_gusset_plate"]["qty"], 2)
        self.assertEqual(hardware_rows["number_9_pan_head_screw"]["qty"], 32)
        self.assertNotIn("2-1/2", hardware_rows["number_9_pan_head_screw"]["type"])

    def test_roof_shims_raise_only_top_boards(self) -> None:
        self.assertEqual(build.ROOF_SHIM_THICKNESS, 0.25)
        self.assertEqual(build.siding.frame_top_z, 49.625)
        self.assertEqual(build.siding.roof_support_z, 49.875)
        self.assertEqual(build.siding.finished_top_z, 50.625)
        self.assertEqual(build.siding.roof_finished_top_z, 50.875)
        for part in build.siding.parts:
            if part.name.startswith("enclosure_siding_top_"):
                self.assertEqual(part.start[2], 49.875)

    def test_roof_shims_stop_at_gusset_envelopes(self) -> None:
        for enclosure in (
            build.default_build,
            build.build_enclosure(width=36, depth=30, height=55),
        ):
            gussets = [
                enclosure.components[name].resolved(
                    enclosure.members[enclosure.components[name].member]
                )
                for name in ("gusset_back_left", "gusset_front_right")
            ]
            shim_names = (
                "roof_shim_brace_fl_fr", "roof_shim_brace_fl_bl",
                "roof_shim_brace_bl_br", "roof_shim_brace_fr_br",
            )
            shims = []
            for name in shim_names:
                shim_instance = enclosure.components[name]
                shim = shim_instance.resolved(
                    enclosure.members[shim_instance.member]
                )
                shims.append(shim)
                self.assertAlmostEqual(shim.box_min[2], enclosure.FRAME_DIMS.z)
                self.assertAlmostEqual(
                    shim.box_min[2] + shim.box_size[2],
                    enclosure.FRAME_DIMS.z + build.ROOF_SHIM_THICKNESS,
                )
                for gusset in gussets:
                    overlap_x = min(
                        shim.box_min[0] + shim.box_size[0],
                        gusset.box_min[0] + gusset.box_size[0],
                    ) - max(shim.box_min[0], gusset.box_min[0])
                    overlap_y = min(
                        shim.box_min[1] + shim.box_size[1],
                        gusset.box_min[1] + gusset.box_size[1],
                    ) - max(shim.box_min[1], gusset.box_min[1])
                    self.assertFalse(
                        overlap_x > 1e-9 and overlap_y > 1e-9,
                        f"{name} overlaps {gusset.name}",
                    )

            for post_name in ("post_fl", "post_br"):
                post = enclosure.members[post_name]
                covering_shims = [
                    shim for shim in shims
                    if shim.box_min[0] <= post.min_on("x") + 1e-9
                    and shim.box_min[0] + shim.box_size[0]
                    >= post.max_on("x") - 1e-9
                    and shim.box_min[1] <= post.min_on("y") + 1e-9
                    and shim.box_min[1] + shim.box_size[1]
                    >= post.max_on("y") - 1e-9
                ]
                self.assertTrue(
                    covering_shims,
                    f"no roof shim covers non-gusseted {post_name}",
                )

    def test_side_4x4s_and_rails_support_tambour_and_header(self) -> None:
        enclosure = build.default_build
        for name in ("brace_fl_bl", "brace_fr_br"):
            with self.subTest(name=name):
                support = enclosure.members[name]
                self.assertEqual(support.type, "4x4")
                self.assertAlmostEqual(support.min_on("z"), 46.125)
                self.assertAlmostEqual(support.max_on("z"), 49.625)
        for name in ("rail_l_tambour", "rail_r_tambour"):
            self.assertNotIn(name, enclosure.members)
        for name in ("rail_ltam", "rail_rtam"):
            support = enclosure.members[name]
            self.assertAlmostEqual(support.center_on("y"), build.TAMBOUR_TRACK_FRONT_Y)
            self.assertAlmostEqual(support.min_on("z"), 13.75)
            self.assertAlmostEqual(support.max_on("z"), 43.5)
        self.assertAlmostEqual(
            enclosure.members["rail_lbu"].center_on("z"),
            enclosure.members["rail_rbu"].center_on("z"),
        )
        self.assertAlmostEqual(
            enclosure.members["rail_rbu"].min_on("y"),
            enclosure.members["post_fr"].max_on("y"),
        )
        self.assertAlmostEqual(
            enclosure.members["rail_rbu"].max_on("y"),
            enclosure.members["post_br"].min_on("y"),
        )
        self.assertAlmostEqual(
            enclosure.members["rail_rtam"].min_on("z"),
            enclosure.members["rail_rbu"].max_on("z"),
        )
        self.assertAlmostEqual(
            enclosure.members["rail_fbu"].min_on("x"),
            enclosure.members["rail_lbu"].max_on("x"),
        )
        self.assertAlmostEqual(
            enclosure.members["rail_fbu"].max_on("x"),
            enclosure.members["rail_rbu"].min_on("x"),
        )
        for name,minimum_x in (
            ("left_tambour_bend_backer", 2.75),
            ("right_tambour_bend_backer", 24.0),
        ):
            component = enclosure.components[name]
            support = component.resolved(enclosure.members[component.member])
            self.assertEqual(component.assembly, "tambour_supports")
            self.assertEqual(
                support.type_name,
                "three_quarter_inch_plywood_tambour_bend_backer",
            )
            self.assertAlmostEqual(support.box_min[1], 5.625)
            self.assertAlmostEqual(support.box_size[1], 1.75)
            self.assertAlmostEqual(support.box_min[2], 45.0)
            self.assertAlmostEqual(support.box_size[2], 1.125)
            self.assertAlmostEqual(support.box_min[0], minimum_x)
            self.assertAlmostEqual(support.box_size[0], 0.75)
            receiver = enclosure.members[
                "rail_lt" if name.startswith("left") else "rail_rt"
            ]
            self.assertAlmostEqual(
                support.box_min[2],
                receiver.max_on("z"),
            )
        for name in ("rail_lt", "rail_rt"):
            support = enclosure.members[name]
            self.assertAlmostEqual(support.min_on("y"), 3.5)
            self.assertAlmostEqual(support.min_on("z"), 43.5)
            self.assertAlmostEqual(support.max_on("z"), 45.0)

    def test_post_supported_receivers_and_split_future_guides(self) -> None:
        for side, front, back, top in (
            ("l", "post_fl", "post_bl", "brace_fl_bl"),
            ("r", "post_fr", "post_br", "brace_fr_br"),
        ):
            receiver = build.members[f"rail_{side}t"]
            lower = build.members[f"rail_{side}tam"]
            upper = build.members[f"rail_{side}tam_upper"]
            self.assertAlmostEqual(receiver.min_on("y"), build.members[front].max_on("y"))
            self.assertAlmostEqual(receiver.max_on("y"), build.members[back].min_on("y"))
            self.assertAlmostEqual(receiver.length, 15.875)
            self.assertAlmostEqual(lower.max_on("z"), receiver.min_on("z"))
            self.assertAlmostEqual(upper.min_on("z"), receiver.max_on("z"))
            self.assertAlmostEqual(upper.max_on("z"), build.members[top].min_on("z"))
            self.assertIn(lower.name, build.model.deferred_object_names)
            self.assertIn(upper.name, build.model.deferred_object_names)

    def test_lowered_front_header_bears_on_side_rails(self) -> None:
        header = build.members["rail_ft"]

        self.assertEqual(header.type, "2x4")
        self.assertAlmostEqual(header.min_on("z"), 43.5)
        self.assertAlmostEqual(header.max_on("z"), 45.0)
        self.assertAlmostEqual(
            build.members["front_center_rail"].max_on("z"),
            header.min_on("z"),
        )

        for name,header_x in (
            ("rail_lt", header.min_on("x")),
            ("rail_rt", header.max_on("x")),
        ):
            with self.subTest(name=name):
                support = build.members[name]
                self.assertEqual(support.type, "2x4")
                self.assertEqual(support.axis, "y")
                self.assertAlmostEqual(support.min_on("z"), header.min_on("z"))
                self.assertAlmostEqual(support.max_on("z"), header.max_on("z"))
                self.assertLessEqual(support.min_on("y"), header.min_on("y"))
                self.assertGreaterEqual(support.max_on("y"), header.max_on("y"))
                self.assertTrue(
                    math.isclose(support.min_on("x"), header_x)
                    or math.isclose(support.max_on("x"), header_x)
                )
        for name in ("rail_ft_left_support", "rail_ft_right_support"):
            self.assertNotIn(name, build.members)


class TambourClearanceBuildTests(unittest.TestCase):
    @staticmethod
    def _convex_polygons_overlap(
        first: list[tuple[float, float]],
        second: list[tuple[float, float]],
    ) -> bool:
        """Return true for positive-area overlap; touching edges are clear."""
        for polygon in (first, second):
            for start, end in zip(polygon, polygon[1:] + polygon[:1]):
                axis = (-(end[1] - start[1]), end[0] - start[0])
                first_projection = [y * axis[0] + z * axis[1] for y, z in first]
                second_projection = [y * axis[0] + z * axis[1] for y, z in second]
                if min(max(first_projection), max(second_projection)) <= max(
                    min(first_projection), min(second_projection)
                ) + 1e-9:
                    return False
        return True

    @staticmethod
    def _minimum_slat_z_over_y_interval(
        enclosure: build.EnclosureBuild,
        min_y: float,
        max_y: float,
    ) -> float:
        tambour = enclosure.tambours["enclosure_tambour_door"].resolved(
            enclosure.model
        )
        details=tambour.installed_details
        rendered_depth=tambour.slat_depth
        if details is not None:
            rendered_depth+=2*details.webbing_thickness
        minimum = math.inf
        for start,end in zip(tambour.left_points, tambour.left_points[1:]):
            dy=end[1]-start[1]
            dz=end[2]-start[2]
            segment_length=math.hypot(dy, dz)
            travel_y=dy/segment_length
            travel_z=dz/segment_length
            depth_y=-travel_z
            depth_z=travel_y
            for step in range(9):
                fraction=step/8
                center_y=(
                    start[1]+fraction*dy
                    -tambour.slat_track_offset*depth_y
                )
                center_z=(
                    start[2]+fraction*dz
                    -tambour.slat_track_offset*depth_z
                )
                vertices = [
                    (
                        center_y
                        + travel_sign*tambour.slat_thickness/2*travel_y
                        + depth_sign*rendered_depth/2*depth_y,
                        center_z
                        + travel_sign*tambour.slat_thickness/2*travel_z
                        + depth_sign*rendered_depth/2*depth_z,
                    )
                    for travel_sign in (-1, 1)
                    for depth_sign in (-1, 1)
                ]
                mean_y=sum(vertex[0] for vertex in vertices)/4
                mean_z=sum(vertex[1] for vertex in vertices)/4
                vertices.sort(
                    key=lambda vertex: math.atan2(
                        vertex[1]-mean_z,
                        vertex[0]-mean_y,
                    )
                )
                candidates = [
                    z for y,z in vertices if min_y <= y <= max_y
                ]
                for a,b in zip(vertices, vertices[1:]+vertices[:1]):
                    for boundary_y in (min_y, max_y):
                        if (a[0]-boundary_y)*(b[0]-boundary_y) > 0:
                            continue
                        if math.isclose(a[0], b[0]):
                            continue
                        edge_fraction=(boundary_y-a[0])/(b[0]-a[0])
                        if 0 <= edge_fraction <= 1:
                            candidates.append(
                                a[1]+edge_fraction*(b[1]-a[1])
                            )
                if candidates:
                    minimum=min(minimum, *candidates)
        return minimum

    def test_front_path_clears_backers_and_lowered_header(self) -> None:
        tambour = build.tambours["enclosure_tambour_door"].resolved(build.model)
        self.assertEqual(tambour.slat_depth, 0.5)
        self.assertEqual(tambour.slat_thickness, 0.75)
        self.assertEqual(tambour.slat_pitch, 25/32)
        self.assertEqual(tambour.slat_envelope_depth, 1.5)
        self.assertEqual(tambour.slat_track_offset, 0)
        details = tambour.installed_details
        self.assertIsNotNone(details)
        assert details is not None
        self.assertAlmostEqual(details.channel_internal_width, 13.7/25.4)
        self.assertAlmostEqual(details.channel_wall_thickness, 4.8/25.4)
        self.assertAlmostEqual(details.mounting_flange_thickness, 4.8/25.4)
        self.assertAlmostEqual(details.flange_extension, 8.2/25.4)
        self.assertAlmostEqual(details.slat_end_engagement, 40/25.4)
        self.assertAlmostEqual(details.joint_gap, 0.6/25.4)
        self.assertAlmostEqual(details.loading_section_length, 100/25.4)
        self.assertAlmostEqual(details.end_stop_length, 12/25.4)
        self.assertEqual(details.webbing_count, 3)
        self.assertEqual(details.pull_slat_indices, (0, 23))
        self.assertAlmostEqual(details.handle_width, 300/25.4)
        self.assertAlmostEqual(details.inward_hardware_projection, 1/16)
        self.assertEqual(len(tambour.slats), 56)
        self.assertEqual(len(tambour.installed_seams), len(details.segment_seams))
        self.assertEqual(tambour.bends, ((1, 2.625), (2, 2.625)))
        self.assertEqual(build.TAMBOUR_FRONT_Y, 5)
        self.assertEqual(build.TAMBOUR_TRACK_FRONT_Y, 5)
        self.assertEqual(build.TAMBOUR_TRACK_TOP_Z, 47.0)
        self.assertEqual(build.TAMBOUR_TRACK_BACK_Y, 22)
        self.assertEqual(build.TAMBOUR_REAR_VERTICAL_LENGTH, 41.375)
        self.assertEqual(build.TAMBOUR_TOP_TANGENT_LENGTH, 11.75)
        self.assertEqual(build.TAMBOUR_FRONT_VERTICAL_LENGTH, 28.375)
        self.assertAlmostEqual(
            build.TAMBOUR_FABRICATION.rear_vertical_length/25.4,
            build.TAMBOUR_REAR_VERTICAL_LENGTH,
        )
        self.assertAlmostEqual(
            build.TAMBOUR_FABRICATION.top_tangent_length/25.4,
            build.TAMBOUR_TOP_TANGENT_LENGTH,
        )
        self.assertAlmostEqual(
            build.TAMBOUR_FABRICATION.front_vertical_length/25.4,
            build.TAMBOUR_FRONT_VERTICAL_LENGTH,
        )
        self.assertEqual(build.TAMBOUR_MINIMUM_TRACK_FRONT_Y, 4.925)
        self.assertEqual(build.TAMBOUR_PLACEMENT_INCREMENT, 1/8)
        self.assertAlmostEqual(
            build.TAMBOUR_TRACK_SUPPORT_EDGE_MARGIN,
            (1.75-build.TAMBOUR_TRACK_FOOTPRINT_WIDTH)/2,
        )
        for name in ("rail_ltam", "rail_rtam"):
            self.assertAlmostEqual(
                build.members[name].center_on("y"),
                build.TAMBOUR_TRACK_FRONT_Y,
            )

        backer_rear=max(
            build.members[name].max_on("y")
            for name in (
                "front_street_light_backer_bottom",
                "front_street_light_backer_lower",
                "front_street_light_backer_upper",
            )
        )
        self.assertGreaterEqual(
            build.TAMBOUR_TRACK_FRONT_Y
            -tambour.slat_envelope_depth/2
            -backer_rear,
            build.TAMBOUR_BRACE_CLEARANCE,
        )
        outward_clearance=(
            build.TAMBOUR_TRACK_FRONT_Y
            -build.TAMBOUR_OUTWARD_ENVELOPE_DEPTH
            -backer_rear
        )
        self.assertAlmostEqual(outward_clearance, 0.325)
        self.assertGreaterEqual(outward_clearance, build.TAMBOUR_BRACE_CLEARANCE)

        header=build.members["rail_ft"]
        minimum_slat_z=self._minimum_slat_z_over_y_interval(
            build.default_build,
            header.min_on("y"),
            header.max_on("y"),
        )
        self.assertGreaterEqual(
            minimum_slat_z-header.max_on("z"),
            build.TAMBOUR_BRACE_CLEARANCE,
        )

    def test_asymmetric_hardware_envelope_clears_fixed_material(self) -> None:
        tambour = build.tambours["enclosure_tambour_door"].resolved(build.model)
        details = tambour.installed_details
        assert details is not None
        outward_depth = tambour.slat_depth / 2 + details.handle_projection
        self.assertAlmostEqual(outward_depth, build.TAMBOUR_OUTWARD_ENVELOPE_DEPTH)
        self.assertAlmostEqual(
            tambour.slat_depth / 2
            + build.TAMBOUR_FABRICATION.inward_hardware_projection / 25.4,
            build.TAMBOUR_INWARD_ENVELOPE_DEPTH,
        )

        ceiling_instance = build.components["tambour_ceiling_panel"]
        ceiling = ceiling_instance.resolved(build.members[ceiling_instance.member])
        obstacles = [
            (name, member.min, member.max)
            for name, member in build.members.items()
        ] + [
            (
                part.name,
                part.start,
                tuple(a + b for a, b in zip(part.start, part.size, strict=True)),
            )
            for part in build.siding.board_parts
        ] + [
            (
                "tambour_ceiling_panel",
                ceiling.box_min,
                tuple(
                    a + b
                    for a, b in zip(ceiling.box_min, ceiling.box_size, strict=True)
                ),
            )
        ]
        handle_center_x = (
            tambour.left_points[0][0] + tambour.right_points[0][0]
        ) / 2
        handle_min_x = handle_center_x - details.handle_width / 2
        handle_max_x = handle_center_x + details.handle_width / 2

        for side, depth_sign, envelope_depth in (
            ("outward handle", -1, outward_depth),
            ("inward hardware", 1, build.TAMBOUR_INWARD_ENVELOPE_DEPTH),
        ):
            for left, right, tangent in tambour.track_samples(subdivisions=8):
                center_y = (left[1] + right[1]) / 2
                center_z = (left[2] + right[2]) / 2
                travel_y, travel_z = tangent[1], tangent[2]
                depth_y, depth_z = -travel_z, travel_y
                envelope = [
                    (
                        center_y
                        + travel_sign * tambour.slat_thickness / 2 * travel_y
                        + depth_sign * depth_fraction * envelope_depth * depth_y,
                        center_z
                        + travel_sign * tambour.slat_thickness / 2 * travel_z
                        + depth_sign * depth_fraction * envelope_depth * depth_z,
                    )
                    for travel_sign, depth_fraction in (
                        (-1, 0),
                        (1, 0),
                        (1, 1),
                        (-1, 1),
                    )
                ]
                for name, minimum, maximum in obstacles:
                    if min(handle_max_x, maximum[0]) <= max(
                        handle_min_x, minimum[0]
                    ):
                        continue
                    obstacle = [
                        (minimum[1], minimum[2]),
                        (maximum[1], minimum[2]),
                        (maximum[1], maximum[2]),
                        (minimum[1], maximum[2]),
                    ]
                    self.assertFalse(
                        self._convex_polygons_overlap(envelope, obstacle),
                        f"{side} sweep conflicts with "
                        f"{name} at {(center_y, center_z)}",
                    )

    def test_slats_run_between_both_track_walls(self) -> None:
        tambour=build.tambours["enclosure_tambour_door"].resolved(build.model)
        details=tambour.installed_details
        assert details is not None

        self.assertAlmostEqual(
            details.channel_internal_width-tambour.slat_depth,
            2*build.TAMBOUR_FABRICATION.running_clearance/25.4,
        )

        def distance_to_track(point, track_points):
            minimum=math.inf
            for start,end in zip(track_points, track_points[1:]):
                delta=tuple(b-a for a,b in zip(start,end))
                relative=tuple(value-a for value,a in zip(point,start))
                length_squared=sum(value*value for value in delta)
                fraction=max(
                    0,
                    min(1, sum(a*b for a,b in zip(relative,delta))/length_squared),
                )
                closest=tuple(a+fraction*d for a,d in zip(start,delta))
                minimum=min(
                    minimum,
                    math.sqrt(sum((a-b)**2 for a,b in zip(point,closest))),
                )
            return minimum

        for slats in (tambour.slats, tambour.closed_slats):
            for left,right,_tangent in slats:
                self.assertAlmostEqual(
                    distance_to_track(left, tambour.left_points),
                    details.mounting_flange_thickness + details.slat_total_end_clearance/2,
                )
                self.assertAlmostEqual(
                    distance_to_track(right, tambour.right_points),
                    details.mounting_flange_thickness + details.slat_total_end_clearance/2,
                )

    def test_every_track_section_is_backed_and_clears_other_lumber(self) -> None:
        enclosure=build.default_build
        tambour=enclosure.tambours["enclosure_tambour_door"].resolved(
            enclosure.model
        )
        details=tambour.installed_details
        assert details is not None
        footprint_width=(
            details.channel_internal_width
            +2*details.channel_wall_thickness
            +2*details.flange_extension
        )
        channel_outer_width=(
            details.channel_internal_width+2*details.channel_wall_thickness
        )
        edge_margin=1/16
        self.assertLessEqual(footprint_width, 1.75-2*edge_margin)

        sides=(
            (
                0,
                1,
                {
                    "post_bl",
                    "brace_fl_bl",
                    "rail_ltam",
                    "rail_ltam_upper",
                    "left_tambour_upper_backing",
                    "rail_lt",
                    "left_tambour_bend_backer",
                    "left_tambour_vertical_backing",
                },
            ),
            (
                1,
                -1,
                {
                    "post_br",
                    "brace_fr_br",
                    "rail_rtam",
                    "rail_rtam_upper",
                    "right_tambour_upper_backing",
                    "rail_rt",
                    "right_tambour_bend_backer",
                    "right_tambour_vertical_backing",
                },
            ),
        )
        for endpoint_index,opening_sign,support_names in sides:
            supports=[]
            for name in support_names:
                member=enclosure.members.get(name)
                if member is not None:
                    supports.append((member.min,member.max))
                    continue
                component=enclosure.components[name]
                resolved=component.resolved(enclosure.members[component.member])
                supports.append(
                    (
                        resolved.box_min,
                        tuple(
                            a+b
                            for a,b in zip(
                                resolved.box_min,
                                resolved.box_size,
                                strict=True,
                            )
                        ),
                    )
                )
            for left,right,tangent in tambour.track_samples(subdivisions=4):
                point=(left,right)[endpoint_index]
                depth_y=-opening_sign*tangent[2]
                depth_z=opening_sign*tangent[1]

                # Check the full flange width, rather than only its edges, so
                # concave gaps between backing members are detected at bends.
                for index in range(65):
                    offset=(index/64-0.5)*footprint_width
                    y=point[1]+offset*depth_y
                    z=point[2]+offset*depth_z
                    self.assertTrue(
                        any(
                            minimum[1]-1e-9 <= y <= maximum[1]+1e-9
                            and minimum[2]-1e-9 <= z <= maximum[2]+1e-9
                            for minimum,maximum in supports
                        ),
                        f"unsupported track at {(point, y, z)}",
                    )

                # The channel walls project into the door opening.  Their
                # conservative outer envelope must not enter unrelated lumber.
                wall_min_x=(
                    point[0]
                    if opening_sign > 0
                    else point[0]-details.slat_end_engagement
                )
                wall_max_x=(
                    point[0]+details.slat_end_engagement
                    if opening_sign > 0
                    else point[0]
                )
                for index in range(33):
                    offset=(index/32-0.5)*channel_outer_width
                    y=point[1]+offset*depth_y
                    z=point[2]+offset*depth_z
                    for name,member in enclosure.members.items():
                        if name in support_names:
                            continue
                        overlap_x=(
                            min(wall_max_x, member.max[0])
                            -max(wall_min_x, member.min[0])
                        )
                        conflicts=(
                            overlap_x > 1e-9
                            and member.min[1]+1e-9 < y < member.max[1]-1e-9
                            and member.min[2]+1e-9 < z < member.max[2]-1e-9
                        )
                        self.assertFalse(
                            conflicts,
                            f"track channel conflicts with lumber {name}",
                        )

    def test_removable_ceiling_guards_horizontal_run(self) -> None:
        panel_instance=build.components["tambour_ceiling_panel"]
        panel=panel_instance.resolved(build.members[panel_instance.member])

        self.assertEqual(panel_instance.assembly, "tambour_guard")
        self.assertEqual(panel.type_name, "quarter_inch_exterior_plywood_panel")
        self.assertEqual(panel.box_min, (3.5, 10.6875, 45.875))
        self.assertEqual(panel.box_size, (20.5, 7.9375, 0.25))
        self.assertEqual(panel.box_min[1], build.members["rail_ft"].max_on("y"))
        self.assertGreaterEqual(
            build.TAMBOUR_TOP_Z-build.TAMBOUR_INWARD_ENVELOPE_DEPTH
            -(panel.box_min[2]+panel.box_size[2]),
            build.TAMBOUR_CEILING_CLEARANCE,
        )
        self.assertGreaterEqual(
            panel.box_min[2]-build.members["rail_ft"].max_on("z"),
            build.TAMBOUR_CEILING_BEND_INSET,
        )

    def test_charger_riser_stays_below_or_behind_front_curtain(self) -> None:
        branch=build.conduits["power_pull_box_junction_feed"].resolved(
            build.components.as_dict(),
            build.members.as_dict(),
        )
        self.assertLess(
            max(point[2] for point in branch.points)+branch.od/2,
            build.TAMBOUR_FRONT_BOTTOM_Z-0.25,
        )
        charger_feed=build.conduits["power_ev_charger_feed"].resolved(
            build.components.as_dict(),
            build.members.as_dict(),
        )
        self.assertGreaterEqual(
            min(point[1] for point in charger_feed.points)
            - charger_feed.od/2
            - (build.TAMBOUR_FRONT_Y+build.TAMBOUR_MAX_ENVELOPE_DEPTH/2),
            0.25,
        )


class BackRightOutletBuildTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_outlet_backers_span_center_rail_to_back_post(self) -> None:
        for name, expected_z in (
            ("back_right_outlet_backer_lower", 15.38),
            ("back_right_outlet_backer_upper", 20.62),
        ):
            with self.subTest(name=name):
                backer = build.members[name]
                self.assertEqual(backer.axis, "y")
                self.assertEqual(backer.length, 6.6875)
                self.assertFalse(backer.rotated)
                self.assertAlmostEqual(backer.max_on("x"), 26.45)
                self.assertAlmostEqual(backer.center_on("z"), expected_z)

    def test_outlet_and_cover_have_parameterized_finished_position(self) -> None:
        lower_backer = build.members["back_right_outlet_backer_lower"]
        outlet = build.components["back_right_outlet"].resolved(lower_backer)
        cover = build.components["back_right_outlet_cover"].resolved(lower_backer)

        self.assertVectorAlmostEqual(outlet.box_min, (26.45, 16.475, 15.15))
        self.assertVectorAlmostEqual(outlet.box_size, (2.3, 2.8, 5.7))
        self.assertAlmostEqual(outlet.box_min[0] + outlet.box_size[0], 28.75)
        self.assertVectorAlmostEqual(cover.box_min, (28.75, 15.545, 14.835))
        self.assertVectorAlmostEqual(cover.box_size, (2.75, 4.66, 6.33))

    def test_bottom_hub_entry_is_available_for_future_conduit(self) -> None:
        self.assertVectorAlmostEqual(
            build.BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(build.members),
            (27.016, 17.875, 15.15),
        )

    def test_right_siding_is_cut_out_for_outlet_box(self) -> None:
        opening = build.BACK_RIGHT_OUTLET_SIDING_OPENING

        for part in build.siding.board_parts:
            if "_right_" not in part.name:
                continue
            overlaps_y = max(part.start[1], opening.min_y) < min(
                part.start[1] + part.size[1],
                opening.max_y,
            )
            overlaps_z = max(part.start[2], opening.bottom_z) < min(
                part.start[2] + part.size[2],
                opening.top_z,
            )
            self.assertFalse(
                overlaps_y and overlaps_z
                and min(
                    part.start[1] + part.size[1],
                    opening.max_y,
                ) - max(part.start[1], opening.min_y) > 1e-9,
                part.name,
            )


class FrontStreetLightBuildTests(unittest.TestCase):
    def test_address_plaque_position_tracks_light_and_siding(self) -> None:
        for dimensions in ((24, 19.375, 49.625), (36, 24, 55)):
            with self.subTest(dimensions=dimensions):
                enclosure = build.build_enclosure(*dimensions)
                instance = enclosure.components["front_address_plaque"]
                plaque = instance.resolved(enclosure.members[instance.member])
                light_instance = enclosure.components["front_street_light"]
                light = light_instance.resolved(enclosure.members[light_instance.member])
                self.assertVectorAlmostEqual(plaque.box_size, (16, 0.5, 3))
                self.assertAlmostEqual(plaque.box_min[0], light.box_min[0])
                self.assertAlmostEqual(
                    plaque.box_min[1] + plaque.box_size[1],
                    enclosure.siding.min_y - enclosure.siding.board_thickness,
                )
                self.assertAlmostEqual(
                    light.box_min[2] - (plaque.box_min[2] + plaque.box_size[2]), 3,
                )
                # Outside view reads left-to-right and upright toward negative Y.
                self.assertEqual(plaque.along_vec, (1, 0, 0))
                self.assertEqual(plaque.across_vec, (0, 0, 1))
                self.assertEqual(plaque.out_vec, (0, -1, 0))
                self.assertEqual(plaque.text, "4754")
                self.assertIn('"address_plaque"', plaque.scad_record())
                self.assertIn('"4754", [16, 3, 0.5]', plaque.scad_record())

        self.assertVectorAlmostEqual(plaque.box_min, (11.75, -1.5, 40.8))
        instance = build.components["front_address_plaque"]
        self.assertVectorAlmostEqual(
            instance.resolved(build.members[instance.member]).box_min,
            (5.75, -1.5, 35.425),
        )

    def test_address_plaque_inventory_has_one_finished_sign(self) -> None:
        for rows in (build.model.bom_rows(), build.model.shopping_list_rows()):
            plaque = next(row for row in rows if "address plaque 4754" in row["type"])
            self.assertEqual(plaque["qty"], 1)
            self.assertIn("16 x 3 x 0.5", plaque["type"])

    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_backers_span_front_posts_and_form_contiguous_backing_field(self) -> None:
        for name, expected_z in (
            ("front_street_light_backer_bottom", 37.375),
            ("front_street_light_backer_lower", 40.875),
            ("front_street_light_backer_upper", 44.375),
        ):
            with self.subTest(name=name):
                backer = build.members[name]
                self.assertEqual(backer.axis, "x")
                self.assertEqual(backer.length, 20.5)
                self.assertFalse(backer.rotated)
                self.assertAlmostEqual(backer.min_on("y"), 2.30)
                self.assertAlmostEqual(backer.center_on("z"), expected_z)

        bottom = build.members["front_street_light_backer_bottom"]
        lower = build.members["front_street_light_backer_lower"]
        upper = build.members["front_street_light_backer_upper"]
        self.assertAlmostEqual(bottom.min_on("z"), 35.625)
        self.assertAlmostEqual(bottom.max_on("z"), lower.min_on("z"))
        self.assertAlmostEqual(lower.max_on("z"), upper.min_on("z"))
        self.assertAlmostEqual(upper.max_on("z"), 46.125)

    def test_recessed_box_and_brook_have_finished_position(self) -> None:
        lower_backer = build.members["front_street_light_backer_lower"]
        box = build.components["front_street_light_base_box"].resolved(lower_backer)
        light = build.components["front_street_light"].resolved(lower_backer)

        self.assertVectorAlmostEqual(box.box_min, (11.75, -1.0, 41.625))
        self.assertVectorAlmostEqual(box.box_size, (4.0, 3.3, 2.0))
        self.assertVectorAlmostEqual(light.box_min, (5.75, -4.9, 41.425))
        self.assertVectorAlmostEqual(light.box_size, (16.0, 3.9, 2.4))
        self.assertAlmostEqual(box.box_min[1]+box.box_size[1], lower_backer.min_on("y"))
        self.assertAlmostEqual(light.box_min[1]+light.box_size[1], box.box_min[1])
        self.assertAlmostEqual(box.box_min[1], build.siding.min_y-build.siding.board_thickness)
        self.assertNotIn("front_street_light_extension_ring", build.components)

    def test_bottom_port_receives_conduit(self) -> None:
        self.assertVectorAlmostEqual(
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY.resolve(build.members),
            (13.75, 0.65, 41.625),
        )
        self.assertIsInstance(
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY_ANCHOR,
            ComponentAnchor,
        )

    def test_siding_is_cut_out_around_recessed_box(self) -> None:
        opening = build.FRONT_STREET_LIGHT_SIDING_OPENING

        for part in build.siding.board_parts:
            if "_front_" not in part.name:
                continue
            overlaps_x = max(part.start[0], opening.min_x) < min(
                part.start[0] + part.size[0],
                opening.max_x,
            )
            overlaps_z = max(part.start[2], opening.bottom_z) < min(
                part.start[2] + part.size[2],
                opening.top_z,
            )
            self.assertFalse(overlaps_x and overlaps_z, part.name)

    def test_brook_mount_and_clearances_follow_enclosure_dimensions(self) -> None:
        for dimensions in ((24, 19.375, 49.625), (36, 24, 55)):
            with self.subTest(dimensions=dimensions):
                enclosure = build.build_enclosure(*dimensions)
                backer = enclosure.members["front_street_light_backer_lower"]
                light = enclosure.components["front_street_light"].resolved(backer)
                box = enclosure.components["front_street_light_base_box"].resolved(backer)
                opening = enclosure.FRONT_STREET_LIGHT_SIDING_OPENING
                # Test the actual central primitive, rather than the full bar's
                # envelope, so a visible hole cannot hide behind an empty region.
                plate_min, plate_size = light.box_primitives[0]
                plate_x = light.origin[0]+plate_min[0]
                plate_z = light.origin[2]+plate_min[1]
                self.assertLess(plate_x, opening.min_x)
                self.assertGreater(plate_x+plate_size[0], opening.max_x)
                self.assertLess(plate_z, opening.bottom_z)
                self.assertGreater(plate_z+plate_size[1], opening.top_z)
                self.assertAlmostEqual(light.origin[1], box.box_min[1])
                self.assertAlmostEqual(backer.min_on("y"), 2.3)
                self.assertAlmostEqual(enclosure.TAMBOUR_TRACK_FRONT_Y, 5.0)
                self.assertAlmostEqual(light.origin[0]+8, (dimensions[0]+3.5)/2)
                self.assertAlmostEqual(light.origin[2]+1.2, dimensions[2]-7)
                conduit = enclosure.conduits["power_street_light_feed"].resolved(
                    enclosure.components, enclosure.members
                )
                self.assertVectorAlmostEqual(conduit.points[-1], (
                    box.box_min[0]+box.box_size[0]/2,
                    box.box_min[1]+box.box_size[1]/2,
                    box.box_min[2],
                ))
                service = enclosure.cables["low_voltage_street_light_service"]
                self.assertAlmostEqual(service.points[-1][1], conduit.points[-1][1])
                self.assertGreater(service.points[-1][2], box.box_min[2]+box.box_size[2])

    def test_inventory_identifies_brook_and_provisional_box(self) -> None:
        rows = {row["name"]: row for row in build.model.bom_rows()}
        light = rows["mod_lighting_brook_16_black_3000k"]
        box = rows["provisional_brook_recessed_junction_box"]
        self.assertEqual(light["qty"], 1)
        self.assertIn("45573961023747", light["type"])
        self.assertEqual(box["qty"], 1)
        self.assertIn("PROVISIONAL", box["type"])


class PowerJunctionBuildTests(unittest.TestCase):
    def assertVectorAlmostEqual(self, actual, expected) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def resolved_conduit(self, name: str, enclosure=None):
        enclosure = build.default_build if enclosure is None else enclosure
        return enclosure.conduits[name].resolved(
            enclosure.components.as_dict(),
            enclosure.members.as_dict(),
        )

    def test_box_has_finished_position_and_revised_fill_margin(self) -> None:
        instance = build.components["power_junction_box"]
        box = instance.resolved(build.members[instance.member])

        self.assertVectorAlmostEqual(
            box.box_min,
            (13, 3.1875, build.POWER_JUNCTION_BOTTOM_Z),
        )
        self.assertVectorAlmostEqual(box.box_size, (4, 4, 4))
        self.assertAlmostEqual(
            build.POWER_JUNCTION_BOTTOM_Z-build.POWER_JUNCTION_GROUND_Z,
            6,
        )
        self.assertEqual(build.POWER_JUNCTION_BOX_FILL.required_volume, 18)
        self.assertEqual(build.POWER_JUNCTION_BOX_FILL.remaining_volume, 31)
        self.assertAlmostEqual(build.POWER_LIGHT_ADAPTER_END[0], 18.25)
        self.assertAlmostEqual(build.POWER_OUTLET_ADAPTER_END_X, 18.25)

    def test_default_charger_riser_fittings_and_route(self) -> None:
        expected_types = {
            "power_junction_input_adapter": "pvc_3/4_male_terminal_adapter",
            "power_ev_pull_box": "carlon_e989nnj_junction_box",
            "power_ev_top_adapter": "pvc_1_male_terminal_adapter",
            "power_ev_back_adapter": "pvc_3/4_male_terminal_adapter",
            "power_ev_bottom_adapter": "pvc_1-1/4_male_terminal_adapter",
        }
        for name, expected_type in expected_types.items():
            with self.subTest(name=name):
                self.assertEqual(
                    build.components[name].component_type.name,
                    expected_type,
                )

        self.assertNotIn("power_ev_lb_body", build.components)
        self.assertNotIn("power_ev_lb_feed", build.conduits)
        self.assertNotIn("power_junction_ev_adapter", build.components)
        self.assertNotIn("power_junction_ev_coupling", build.components)

        riser = self.resolved_conduit("power_ground_riser")
        branch = self.resolved_conduit("power_pull_box_junction_feed")
        ev = self.resolved_conduit("power_ev_charger_feed")
        self.assertVectorAlmostEqual(
            riser.points[0][:2],
            (build.POWER_RISER_X, build.POWER_RISER_Y),
        )
        self.assertVectorAlmostEqual(
            riser.points[-1][:2],
            (build.POWER_RISER_X, build.POWER_RISER_Y),
        )
        self.assertEqual(branch.trade_size, "3/4")
        self.assertEqual(branch.points[0][0], branch.points[-1][0])
        self.assertAlmostEqual(branch.points[0][0], build.POWER_EV_ENTRY[0])
        self.assertAlmostEqual(branch.points[0][2], branch.points[-1][2])
        self.assertGreater(branch.points[0][1]-branch.points[-1][1], 0)
        self.assertAlmostEqual(
            branch.points[0][2]-branch.od/2,
            8.305,
        )
        self.assertEqual(
            build.conduits["power_pull_box_junction_feed"].points,
            (
                build.POWER_PULL_BOX_BRANCH_ANCHOR,
                build.POWER_JUNCTION_INPUT_END_ANCHOR,
            ),
        )
        box_instance = build.components["power_junction_box"]
        box = box_instance.resolved(build.members[box_instance.member])
        adapter_instance = build.components["power_junction_input_adapter"]
        adapter = adapter_instance.resolved(build.members[adapter_instance.member])
        self.assertAlmostEqual(
            adapter.box_min[1], box.box_min[1]+box.box_size[1]-0.5,
        )
        self.assertAlmostEqual(
            adapter.box_min[0]+adapter.box_size[0]/2, build.POWER_EV_ENTRY[0],
        )
        self.assertAlmostEqual(
            branch.points[-1][1], adapter.box_min[1]+adapter.box_size[1],
        )
        for obsolete in ("power_ev_tb_body", "power_ev_reducer",
                         "power_junction_input_coupling",
                         "power_junction_light_coupling",
                         "power_junction_outlet_coupling"):
            self.assertNotIn(obsolete, build.components)

        self.assertEqual(ev.trade_size, "1")
        self.assertEqual(len(ev.points), 2)
        self.assertVectorAlmostEqual(ev.points[-1], build.POWER_EV_ENTRY)
        self.assertVectorAlmostEqual(ev.points[0][:2], ev.points[-1][:2])
        self.assertIsInstance(
            build.conduits["power_ev_charger_feed"].points[0],
            ComponentAnchor,
        )
        self.assertIsInstance(
            build.conduits["power_ev_charger_feed"].points[-1],
            ComponentAnchor,
        )
        self.assertVectorAlmostEqual(
            build.POWER_EV_ENTRY,
            (15.35, 12.2875, 22.35),
        )
        charger = build.components["front_ev_charger_body"].resolved(
            build.members["front_center_rail"]
        )
        holster = build.components["front_ev_charger_plug"].resolved(
            build.members["front_center_rail"]
        )
        self.assertAlmostEqual(charger.box_min[2], 22.35)
        self.assertAlmostEqual(holster.box_min[2], 30.83492125984252)

    def test_pull_box_and_clamping_hardware(self) -> None:
        for enclosure in (build.default_build, build.build_enclosure(width=36, depth=30)):
            def resolved(name):
                item = enclosure.components[name]
                return item.resolved(enclosure.members[item.member])

            box = resolved("power_ev_pull_box")
            self.assertVectorAlmostEqual(box.box_size, (4, 2.315, 4))
            self.assertAlmostEqual(box.box_min[2], 6.83)
            branch = self.resolved_conduit("power_pull_box_junction_feed", enclosure)
            # Socket ends face each other with a positive straight conduit span.
            self.assertGreater(branch.points[0][1], branch.points[-1][1])
            riser = self.resolved_conduit("power_ground_riser", enclosure)
            bottom = resolved("power_ev_bottom_adapter")
            self.assertVectorAlmostEqual(
                riser.points[-1],
                (bottom.box_min[0]+bottom.box_size[0]/2,
                 bottom.box_min[1]+bottom.box_size[1]/2, bottom.box_min[2]),
            )
            for name in ("power_ev_top_adapter", "power_ev_bottom_adapter",
                         "power_ev_back_adapter", "power_junction_input_adapter",
                         "power_junction_light_adapter", "power_junction_outlet_adapter",
                         "low_voltage_input_adapter"):
                fitting = resolved(name)
                instance = enclosure.components[name]
                for suffix in ("sealing_washer", "locknut"):
                    hardware_instance = enclosure.components[f"{name}_{suffix}"]
                    self.assertEqual(hardware_instance.absolute_anchor, instance.absolute_anchor)
                    hardware = resolved(f"{name}_{suffix}")
                    self.assertVectorAlmostEqual(hardware.along_vec, fitting.along_vec)
                # The wall lies 0.5 in from the threaded end; clamps straddle it.
                washer_type = enclosure.components[f"{name}_sealing_washer"].component_type
                nut_type = enclosure.components[f"{name}_locknut"].component_type
                self.assertGreaterEqual(washer_type.cylinder_primitives[0][0][0], 0.5)
                nut_start, _, nut_length, _ = nut_type.cylinder_primitives[0]
                self.assertLess(nut_start[0]+nut_length, 0.5)

    def test_riser_thread_and_locknut_fit_inside_pull_box(self) -> None:
        for enclosure in (build.default_build, build.build_enclosure(width=36, depth=30)):
            instance = enclosure.components["power_ev_bottom_adapter"]
            fitting = instance.resolved(enclosure.members[instance.member])
            box_instance = enclosure.components["power_ev_pull_box"]
            box = box_instance.resolved(enclosure.members[box_instance.member])
            # Cover is at positive Y; two inches of clear depth lie behind it.
            inner_min_y = box.box_min[1] + 0.160
            inner_max_y = box.box_min[1] + box.box_size[1] - 0.155
            self.assertAlmostEqual((inner_min_y + inner_max_y) / 2,
                                   enclosure.POWER_RISER_Y)
            stem, socket = instance.component_type.cylinder_primitives
            self.assertLess(stem[3], socket[3])
            self.assertLess(stem[0][0], 0.5)
            self.assertGreater(socket[0][0], 0.5)
            # Only the narrow stem enters; the socket begins below the wall.
            socket_top_z = fitting.origin[2] - socket[0][0]
            self.assertLess(socket_top_z, box.box_min[2])
            nut = enclosure.components["power_ev_bottom_adapter_locknut"].component_type
            for diameter in (stem[3], nut.cylinder_primitives[0][3]):
                self.assertGreater(enclosure.POWER_RISER_Y - diameter / 2, inner_min_y)
                self.assertLess(enclosure.POWER_RISER_Y + diameter / 2, inner_max_y)
            # The top fitting remains aligned with the charger's entry.
            self.assertAlmostEqual(enclosure.components["power_ev_top_adapter"].absolute_anchor[1],
                                   enclosure.POWER_EV_ENTRY[1])

    def test_riser_and_equipment_feeds_use_relative_endpoints(self) -> None:
        enclosure = build.default_build
        riser = self.resolved_conduit("power_ground_riser", enclosure)
        branch = self.resolved_conduit("power_pull_box_junction_feed", enclosure)
        ev = self.resolved_conduit("power_ev_charger_feed", enclosure)
        light = self.resolved_conduit("power_street_light_feed", enclosure)

        self.assertEqual(riser.trade_size, "1-1/4")
        self.assertVectorAlmostEqual(
            riser.points[0],
            (
                enclosure.POWER_RISER_X,
                enclosure.POWER_RISER_Y,
                enclosure.POWER_RISER_GROUND_Z,
            ),
        )
        self.assertEqual(riser.points[0][:2], riser.points[-1][:2])
        self.assertEqual(ev.trade_size, "1")
        self.assertVectorAlmostEqual(ev.points[-1], enclosure.POWER_EV_ENTRY)

        self.assertTrue(
            all(
                isinstance(point, (RelativeCoord, ComponentAnchor))
                for point in enclosure.conduits["power_ground_riser"].points
            )
        )
        self.assertTrue(
            all(
                isinstance(point, ComponentAnchor)
                for point in enclosure.conduits["power_pull_box_junction_feed"].points
            )
        )
        self.assertEqual(branch.points[0][0], enclosure.POWER_EV_ENTRY[0])
        self.assertIsInstance(
            enclosure.conduits["power_ev_charger_feed"].points[0],
            ComponentAnchor,
        )
        self.assertIsInstance(
            enclosure.conduits["power_ev_charger_feed"].points[-1],
            ComponentAnchor,
        )

        self.assertEqual(light.trade_size, "1/2")
        self.assertVectorAlmostEqual(
            light.points[0], enclosure.POWER_LIGHT_ADAPTER_END
        )
        self.assertVectorAlmostEqual(
            light.points[-1],
            enclosure.FRONT_STREET_LIGHT_CONDUIT_ENTRY.resolve(enclosure.members),
        )
        self.assertEqual(len(ev.points), 2)
        self.assertEqual(light.bends, ((1, 2.5), (2, 3), (3, 3)))
        self.assertGreater(len(light.points), 20)

    def test_street_light_feed_sweeps_left_into_bottom_port(self) -> None:
        light = self.resolved_conduit("power_street_light_feed")
        adapter = build.components["power_junction_light_adapter"].resolved(
            build.members["front_center_rail"]
        )
        outlet = build.components["power_junction_outlet_adapter"].resolved(
            build.members["front_center_rail"]
        )

        self.assertEqual(
            build.components["power_junction_light_adapter"].orientation,
            "left",
        )
        self.assertAlmostEqual(adapter.box_min[0], build.POWER_JUNCTION_RIGHT_X-0.5)
        self.assertLess(
            adapter.box_min[1]+adapter.box_size[1]/2,
            outlet.box_min[1]+outlet.box_size[1]/2,
        )
        self.assertAlmostEqual(
            adapter.box_min[2]+adapter.box_size[2]/2,
            build.POWER_JUNCTION_LIGHT_PORT_Z,
        )
        self.assertAlmostEqual(
            outlet.box_min[2]+outlet.box_size[2]/2,
            build.POWER_OUTLET_HORIZONTAL_RUN_Z,
        )
        self.assertVectorAlmostEqual(
            light.points[0],
            build.POWER_LIGHT_ADAPTER_END,
        )
        self.assertVectorAlmostEqual(
            light.points[-1], build.FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT
        )
        self.assertAlmostEqual(
            max(point[0] for point in light.points),
            build.POWER_LIGHT_POST_X,
        )
        self.assertGreaterEqual(
            build.TAMBOUR_FRONT_Y
            - max(point[1] for point in light.points)
            - CONDUIT_OD_BY_TRADE_SIZE["1/2"]/2,
            build.TAMBOUR_BRACE_CLEARANCE,
        )
        self.assertGreater(light.points[-1][2], light.points[0][2])
        self.assertAlmostEqual(
            light.points[-1][0],
            build.FRONT_STREET_LIGHT_CENTER_X,
        )

        raw_points = build.conduits["power_street_light_feed"].points
        lower_post_point = raw_points[1].resolve(build.members)
        upper_post_point = raw_points[2].resolve(build.members)
        horizontal_end = raw_points[3].resolve(build.members)
        self.assertAlmostEqual(lower_post_point[0], build.POWER_LIGHT_POST_X)
        self.assertAlmostEqual(upper_post_point[0], build.POWER_LIGHT_POST_X)
        self.assertAlmostEqual(
            lower_post_point[1],
            build.POWER_JUNCTION_LIGHT_PORT_Y,
        )
        self.assertAlmostEqual(
            upper_post_point[1],
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[1],
        )
        self.assertAlmostEqual(
            upper_post_point[2],
            build.POWER_LIGHT_HORIZONTAL_RUN_Z,
        )
        self.assertAlmostEqual(
            horizontal_end[2],
            build.POWER_LIGHT_HORIZONTAL_RUN_Z,
        )
        self.assertGreater(upper_post_point[0], horizontal_end[0])
        self.assertAlmostEqual(
            horizontal_end[0],
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY_POINT[0],
        )

    def test_layout_tracks_resized_enclosures(self) -> None:
        for enclosure in (
            build.build_enclosure(width=30, depth=26),
            build.build_enclosure(height=55),
        ):
            ev = self.resolved_conduit("power_ev_charger_feed", enclosure)
            self.assertVectorAlmostEqual(ev.points[-1], enclosure.POWER_EV_ENTRY)
            self.assertVectorAlmostEqual(ev.points[0][:2], ev.points[-1][:2])
            riser = self.resolved_conduit("power_ground_riser", enclosure)
            self.assertVectorAlmostEqual(
                riser.points[0][:2],
                (enclosure.POWER_RISER_X, enclosure.POWER_RISER_Y),
            )

    def test_outlet_feed_rests_on_lower_right_rail(self) -> None:
        outlet = self.resolved_conduit("power_back_right_outlet_feed")

        self.assertEqual(outlet.trade_size, "1/2")
        self.assertEqual(outlet.bends, ((1, 4), (2, 4)))
        adapter = build.components["power_junction_outlet_adapter"].resolved(
            build.members["front_center_rail"]
        )
        self.assertAlmostEqual(
            adapter.box_min[2]+adapter.box_size[2]/2,
            build.POWER_OUTLET_HORIZONTAL_RUN_Z,
        )
        self.assertAlmostEqual(outlet.points[0][2], build.POWER_OUTLET_HORIZONTAL_RUN_Z)
        self.assertVectorAlmostEqual(
            outlet.points[0],
            (
                build.POWER_OUTLET_ADAPTER_END_X,
                build.POWER_JUNCTION_PORT_Y,
                build.POWER_JUNCTION_OUTLET_PORT_Z,
            ),
        )
        self.assertVectorAlmostEqual(
            outlet.points[-1],
            build.BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(build.members),
        )
        rail = build.members["rail_rbl"]
        run_points = [point for point in outlet.points
                      if abs(point[0]-build.BACK_RIGHT_OUTLET_CONDUIT_ENTRY_POINT[0]) < 1e-9
                      and abs(point[2]-build.POWER_OUTLET_HORIZONTAL_RUN_Z) < 1e-9]
        self.assertEqual(len(run_points), 2)
        self.assertGreater(run_points[1][1]-run_points[0][1], 3)
        for x, y, z in run_points:
            self.assertAlmostEqual(z-outlet.od/2, rail.max_on("z"))
            self.assertGreaterEqual(x-outlet.od/2, rail.min_on("x"))
            self.assertLessEqual(x+outlet.od/2, rail.max_on("x"))
            self.assertGreaterEqual(y, rail.min_on("y"))
            self.assertLessEqual(y, rail.max_on("y"))
        self.assertAlmostEqual(min(point[2] for point in outlet.points),
                               build.POWER_OUTLET_HORIZONTAL_RUN_Z)
        self.assertLess(
            max(point[0] for point in outlet.points)
            + CONDUIT_OD_BY_TRADE_SIZE["1/2"]/2,
            build.siding.max_x,
        )


class LowVoltageBuildTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def resolved_component(self, name: str):
        instance = build.components[name]
        return instance.resolved(build.members[instance.member])

    def resolved_conduit(self, name: str):
        return build.conduits[name].resolved(
            build.components.as_dict(),
            build.members.as_dict(),
        )

    def test_center_gland_cat6_rendering_is_enabled(self) -> None:
        scad=build.model.to_scad()
        self.assertIn("center_gland_cat6 = true;", scad)
        self.assertIn(
            'center_gland_cat6\n                            '
            '|| cable_name(c) != "low_voltage_ev_charger_feed"',
            scad,
        )

    def test_right_gland_wifi_route_exact_regression(self) -> None:
        points=build.cables["low_voltage_wifi_feed"].points
        encoded=b"".join(struct.pack("!ddd", *point) for point in points)

        self.assertEqual(len(points), 168)
        self.assertEqual(
            hashlib.sha256(encoded).hexdigest(),
            "9c8606e607b63653327897d0e5f693809a756ad02ac4fbbad0af1466cc8f7a82",
        )

    def test_center_gland_charger_route_exact_regression(self) -> None:
        points=build.cables["low_voltage_ev_charger_feed"].points
        encoded=b"".join(struct.pack("!ddd", *point) for point in points)

        self.assertEqual(len(points), 101)
        self.assertEqual(
            hashlib.sha256(encoded).hexdigest(),
            "e8de699f2b499fe1ba6f3f61bc1eeda5715764b1f5120ea67f8b3e4f6c7ba323",
        )

    def test_low_voltage_box_sits_on_upper_elbow(self) -> None:
        instance = build.components["low_voltage_termination_box"]
        box = self.resolved_component("low_voltage_termination_box")

        self.assertIs(instance.component_type, CARLON_E987N_JUNCTION_BOX)
        self.assertEqual(instance.face, "wide_neg")
        self.assertVectorAlmostEqual(
            box.box_min,
            (build.LOW_VOLTAGE_INPUT_X-2, build.LOW_VOLTAGE_BOX_CENTER_Y-2,
             build.LOW_VOLTAGE_BOX_BOTTOM_Z),
        )
        self.assertVectorAlmostEqual(box.box_size, (4, 4, 4))
        self.assertAlmostEqual(
            box.box_min[1]+box.box_size[1],
            build.members["rail_fbu"].min_on("y"),
        )
        self.assertVectorAlmostEqual(
            build.LOW_VOLTAGE_UPPER_ELBOW_OUTLET,
            (build.LOW_VOLTAGE_INPUT_X, build.LOW_VOLTAGE_INPUT_Y,
             build.LOW_VOLTAGE_INPUT_ADAPTER_END_Z),
        )
        self.assertNotIn("low_voltage_ground_riser", build.conduits)

    def test_bottom_fittings_are_inside_the_box_and_do_not_overlap(self) -> None:
        box = self.resolved_component("low_voltage_termination_box")
        fittings = [
            self.resolved_component("low_voltage_input_adapter"),
            *(
                self.resolved_component(f"low_voltage_cable_gland_{index}")
                for index in range(1, 4)
            ),
        ]

        for fitting in fittings:
            self.assertGreaterEqual(fitting.box_min[0], box.box_min[0])
            self.assertLessEqual(
                fitting.box_min[0]+fitting.box_size[0],
                box.box_min[0]+box.box_size[0],
            )
            self.assertGreaterEqual(fitting.box_min[1], box.box_min[1])
            self.assertLessEqual(
                fitting.box_min[1]+fitting.box_size[1],
                box.box_min[1]+box.box_size[1],
            )
            self.assertAlmostEqual(
                fitting.box_min[2]+fitting.box_size[2],
                build.LOW_VOLTAGE_BOX_BOTTOM_Z+(0.5 if fitting is fittings[0] else 0),
            )

        input_adapter = fittings[0]
        input_center = (
            input_adapter.box_min[0]+input_adapter.box_size[0]/2,
            input_adapter.box_min[1]+input_adapter.box_size[1]/2,
        )
        self.assertGreaterEqual(
            input_center[0]-box.box_min[0],
            build.LOW_VOLTAGE_PORT_EDGE_CLEARANCE,
        )
        self.assertGreaterEqual(
            box.box_min[1]+box.box_size[1]-input_center[1],
            build.LOW_VOLTAGE_PORT_EDGE_CLEARANCE,
        )

        gland_centers = [
            (
                fitting.box_min[0]+fitting.box_size[0]/2,
                fitting.box_min[1]+fitting.box_size[1]/2,
            )
            for fitting in fittings[1:]
        ]
        self.assertTrue(all(center[1] < input_center[1] for center in gland_centers))

        for index, fitting in enumerate(fittings):
            for other in fittings[index+1:]:
                x_overlap = min(
                    fitting.box_min[0]+fitting.box_size[0],
                    other.box_min[0]+other.box_size[0],
                )-max(fitting.box_min[0], other.box_min[0])
                y_overlap = min(
                    fitting.box_min[1]+fitting.box_size[1],
                    other.box_min[1]+other.box_size[1],
                )-max(fitting.box_min[1], other.box_min[1])
                self.assertFalse(x_overlap > 0 and y_overlap > 0)

    def test_three_quarter_riser_uses_requested_plumb_axis(self) -> None:
        riser = self.resolved_conduit("low_voltage_ground_riser_inlet")

        self.assertEqual(riser.trade_size, "3/4")
        self.assertEqual(riser.assembly, "low_voltage_conduit")
        self.assertAlmostEqual(build.LOW_VOLTAGE_RISER_X, 14)
        self.assertAlmostEqual(build.LOW_VOLTAGE_RISER_Y, 6.25)
        self.assertVectorAlmostEqual(
            riser.points[0],
            (
                build.LOW_VOLTAGE_RISER_X,
                build.LOW_VOLTAGE_RISER_Y,
                build.LOW_VOLTAGE_GROUND_Z,
            ),
        )
        self.assertVectorAlmostEqual(
            riser.points[-1],
            (
                build.LOW_VOLTAGE_RISER_X,
                build.LOW_VOLTAGE_RISER_Y,
                build.LOW_VOLTAGE_FIRST_ELBOW_ANCHOR_Z,
            ),
        )
        self.assertEqual(riser.points[0][:2], riser.points[-1][:2])

        ground_z=build.grounds[0].resolved(build.members).z_at(
            build.LOW_VOLTAGE_RISER_X,
            build.LOW_VOLTAGE_RISER_Y,
        )
        self.assertAlmostEqual(riser.points[0][2], ground_z)

        self.assertAlmostEqual(build.LOW_VOLTAGE_INPUT_X, 10.65685424949238)
        self.assertAlmostEqual(build.LOW_VOLTAGE_INPUT_Y, 6.25)
        self.assertAlmostEqual(
            build.LOW_VOLTAGE_INPUT_X,
            build.LOW_VOLTAGE_BOX_CENTER_X,
        )
        self.assertAlmostEqual(
            build.LOW_VOLTAGE_INPUT_Y-build.LOW_VOLTAGE_BOX_CENTER_Y,
            1.0625,
        )
        self.assertNotEqual(
            riser.points[-1][:2],
            (build.LOW_VOLTAGE_INPUT_X, build.LOW_VOLTAGE_INPUT_Y),
        )

        for footing in build.footings:
            resolved = footing.resolved(build.model)
            center_distance = math.hypot(
                riser.points[0][0]-resolved.center[0],
                riser.points[0][1]-resolved.center[1],
            )
            self.assertGreaterEqual(
                center_distance,
                resolved.diameter/2+CONDUIT_OD_BY_TRADE_SIZE["3/4"]/2-1e-9,
            )

    def test_low_voltage_cables_follow_routes_and_bend_limits(self) -> None:
        expected_endpoints = {
            "low_voltage_street_light_service": (
                build.FRONT_STREET_LIGHT_CENTER_X,
                build.FRONT_STREET_LIGHT_CONDUIT_ENTRY.y,
                build.LOW_VOLTAGE_BRACE_UNDERSIDE_Z,
            ),
            "low_voltage_wifi_feed": build.path_2_entry,
            "low_voltage_ev_charger_feed": build.path_3_entry,
        }
        expected_colors = {
            "low_voltage_street_light_service": build.LOW_VOLTAGE_STREET_LIGHT_COLOR,
            "low_voltage_wifi_feed": build.LOW_VOLTAGE_CAT6_COLOR,
            "low_voltage_ev_charger_feed": build.LOW_VOLTAGE_CAT6_COLOR,
        }
        expected_gland_indices = {
            "low_voltage_street_light_service": 0,
            "low_voltage_wifi_feed": 2,
            "low_voltage_ev_charger_feed": 1,
        }

        for name,endpoint in expected_endpoints.items():
            cable = build.cables[name]
            self.assertEqual(cable.assembly, "low_voltage_cabling")
            self.assertEqual(cable.diameter, 1/8)
            self.assertEqual(cable.color, expected_colors[name])
            self.assertVectorAlmostEqual(
                cable.points[0],
                (
                    build.LOW_VOLTAGE_GLAND_XS[expected_gland_indices[name]],
                    build.LOW_VOLTAGE_GLAND_Y,
                    build.LOW_VOLTAGE_GLAND_END_Z,
                ),
            )
            self.assertVectorAlmostEqual(cable.points[-1], endpoint)
            self.assertGreaterEqual(
                minimum_cable_bend_radius(cable.points),
                build.LOW_VOLTAGE_MINIMUM_BEND_RADIUS-1e-6,
            )

        service = build.cables["low_voltage_street_light_service"]
        self.assertAlmostEqual(min(point[2] for point in service.points[-50:]), 45.5625)
        self.assertIn(build.path_1_post, service.points)
        self.assertGreater(
            build.path_1_post[0],
            build.members["post_fl"].max_on("x"),
        )
        self.assertGreater(service.points[-2][0], service.points[-1][0])
        light_backers = (
            build.members["front_street_light_backer_lower"],
            build.members["front_street_light_backer_upper"],
        )
        for point in service.points:
            for backer in light_backers:
                clearance = build.LOW_VOLTAGE_CABLE_DIAMETER/2
                inside_backer = all(
                    backer.min_on(axis)-clearance
                    <= point[index]
                    <= backer.max_on(axis)+clearance
                    for index,axis in enumerate("xyz")
                )
                self.assertFalse(inside_backer)

        wifi_feed = build.cables["low_voltage_wifi_feed"]
        self.assertEqual(
            wifi_feed.points[:len(build.path_2_droop_points)],
            build.path_2_droop_points,
        )
        self.assertGreater(build.path_2_riser_bypass[0], build.LOW_VOLTAGE_INPUT_X)
        self.assertTrue(
            all(
                start[0] <= end[0]+1e-9
                for start,end in zip(wifi_feed.points, wifi_feed.points[1:])
            )
        )
        self.assertIn(build.path_2_front_rail, wifi_feed.points)
        self.assertGreater(build.path_2_front_rail[0], build.path_2_start[0])
        self.assertGreater(build.path_2_front_rail[1], build.path_2_start[1])
        self.assertGreater(
            build.path_2_front_rail[0],
            build.members["front_center_rail"].max_on("x"),
        )
        self.assertAlmostEqual(
            build.path_2_front_rail[1],
            build.members["front_center_rail"].center_on("y"),
        )
        self.assertTrue(
            all(
                start[0] <= end[0]
                for start,end in zip(build.path_2_x_sweep, build.path_2_x_sweep[1:])
            )
        )
        face_start_index=next(
            index
            for index,point in enumerate(build.path_2_x_sweep)
            if math.isclose(point[0], build.LOW_VOLTAGE_FRONT_RAIL_POS_X)
        )
        face_start=build.path_2_x_sweep[face_start_index]
        self.assertGreaterEqual(
            face_start[2],
            build.LOW_VOLTAGE_WIFI_X_SWEEP_END_Z,
        )
        self.assertLess(face_start[2], build.LOW_VOLTAGE_WIFI_X_SWEEP_END_Z+0.5)
        self.assertLess(face_start[1], build.path_2_front_rail[1])
        self.assertTrue(
            all(
                math.isclose(point[0], build.LOW_VOLTAGE_FRONT_RAIL_POS_X)
                for point in build.path_2_x_sweep[face_start_index:]
            )
        )
        self.assertVectorAlmostEqual(build.path_2_x_sweep[-1], build.path_2_front_rail)
        self.assertEqual(
            build.path_2_front_rail[2],
            build.LOW_VOLTAGE_WIFI_FACE_CENTER_Z,
        )
        vertical_points = tuple(
            point
            for point in wifi_feed.points
            if build.path_2_front_rail[2] <= point[2] <= 40
            and math.isclose(point[1], build.path_2_front_rail[1])
        )
        self.assertTrue(vertical_points)
        self.assertTrue(
            all(point[:2] == build.path_2_front_rail[:2] for point in vertical_points)
        )
        self.assertGreater(
            build.path_2_top_clear[1],
            build.members["rail_ft"].max_on("y"),
        )
        self.assertGreater(build.path_2_right_rail[0], build.path_2_top_clear[0])
        self.assertLess(
            build.path_2_right_rail[0],
            build.members["right_center_rail"].min_on("x"),
        )
        self.assertGreater(
            build.path_2_entry_sweep[1],
            build.members["right_center_rail"].max_on("y"),
        )
        self.assertGreater(build.path_2_entry[0], build.path_2_entry_sweep[0])
        self.assertGreater(build.path_2_entry[2], build.path_2_entry_sweep[2])

        ev_feed = build.cables["low_voltage_ev_charger_feed"]
        self.assertGreater(
            max(
                point[0]
                for point in build.path_3_lower_points
                if point[2] <= build.LOW_VOLTAGE_INPUT_ADAPTER_END_Z
            ),
            build.path_3_start[0],
        )
        self.assertIn(build.path_3_front_rail, ev_feed.points)
        self.assertGreater(build.path_3_front_rail[1], build.path_3_start[1])
        self.assertVectorAlmostEqual(
            build.path_3_front_rail,
            (
                build.LOW_VOLTAGE_FRONT_RAIL_NEG_X,
                build.members["front_center_rail"].center_on("y")
                +build.LOW_VOLTAGE_CHARGER_LANE_OFFSET,
                16,
            ),
        )
        self.assertLess(build.path_3_branch[2], build.path_3_entry[2])
        self.assertGreater(
            build.path_3_rail_clear[1],
            build.members["front_center_rail"].max_on("y"),
        )
        self.assertLess(
            max(point[2] for point in ev_feed.points),
            build.members["rail_ft"].min_on("z"),
        )
        self.assertLess(
            max(point[0] for point in ev_feed.points[:-1]),
            build.members["right_center_rail"].min_on("x"),
        )
        self.assertGreater(build.path_3_entry[1], build.path_3_rail_clear[1])
        self.assertGreater(build.path_3_entry[2], build.path_3_rail_clear[2])
        self.assertTrue(all(point[1] < build.path_3_entry[1] for point in ev_feed.points[:-1]))

        for cable in (service, wifi_feed, ev_feed):
            self.assertLess(cable.points[1][2], cable.points[0][2])

        self.assertIn(build.path_1_spline_bottom, service.points)
        self.assertAlmostEqual(
            min(point[2] for point in service.points),
            build.LOW_VOLTAGE_GLAND_EXIT_BOTTOM_Z,
        )
        self.assertGreaterEqual(
            minimum_cable_bend_radius(wifi_feed.points),
            build.LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS,
        )
        self.assertAlmostEqual(
            minimum_cable_bend_radius(ev_feed.points),
            build.LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS,
        )

        required_riser_clearance = (
            build.LOW_VOLTAGE_CONDUIT_RADIUS
            + build.LOW_VOLTAGE_CABLE_DIAMETER/2
        )
        for cable in (wifi_feed, ev_feed):
            for start,end in zip(cable.points, cable.points[1:]):
                if min(start[2], end[2]) > build.LOW_VOLTAGE_INPUT_ADAPTER_END_Z:
                    continue
                segment_x=end[0]-start[0]
                segment_y=end[1]-start[1]
                segment_length_squared=segment_x**2+segment_y**2
                projection=(
                    (
                        (build.LOW_VOLTAGE_INPUT_X-start[0])*segment_x
                        +(build.LOW_VOLTAGE_INPUT_Y-start[1])*segment_y
                    )/segment_length_squared
                    if segment_length_squared
                    else 0
                )
                projection=max(0, min(1, projection))
                center_distance = math.hypot(
                    start[0]+projection*segment_x-build.LOW_VOLTAGE_INPUT_X,
                    start[1]+projection*segment_y-build.LOW_VOLTAGE_INPUT_Y,
                )
                self.assertGreaterEqual(
                    center_distance,
                    required_riser_clearance-1e-9,
                )

    def test_wifi_and_charger_droops_clear_open_tambour_edge(self) -> None:
        for name in ("low_voltage_wifi_feed", "low_voltage_ev_charger_feed"):
            points = build.cables[name].points
            crossings = []
            for a, b in zip(points, points[1:]):
                if (a[1]-build.TAMBOUR_FRONT_Y)*(b[1]-build.TAMBOUR_FRONT_Y) > 0:
                    continue
                if a[1] == b[1]:
                    continue
                t=(build.TAMBOUR_FRONT_Y-a[1])/(b[1]-a[1])
                if 0 <= t <= 1:
                    crossings.append(a[2]+t*(b[2]-a[2]))
            self.assertTrue(crossings)
            self.assertLess(
                max(crossings)+build.LOW_VOLTAGE_CABLE_DIAMETER/2,
                build.TAMBOUR_FRONT_BOTTOM_Z,
            )


class ParameterizedBuildTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def resolved_component(self, enclosure: build.EnclosureBuild, name: str):
        instance = enclosure.components[name]
        return instance.resolved(enclosure.members[instance.member])

    def resolved_conduit(self, enclosure: build.EnclosureBuild, name: str):
        return enclosure.conduits[name].resolved(
            enclosure.components.as_dict(),
            enclosure.members.as_dict(),
        )

    def test_default_depth_shifts_center_rail_assembly_and_preserves_riser_axes(self) -> None:
        enclosure = build.default_build

        self.assertEqual(enclosure.depth, 19.375)
        self.assertAlmostEqual(enclosure.members["post_br"].start[1], 19.375)
        self.assertAlmostEqual(
            enclosure.members["front_center_rail"].center_on("y"),
            8.9375,
        )
        self.assertAlmostEqual(
            enclosure.members["right_center_rail"].center_on("y"),
            11.9375,
        )
        for name in ("rail_fbu", "rail_ft"):
            with self.subTest(name=name):
                self.assertAlmostEqual(
                    enclosure.members[name].center_on("y"),
                    8.9375,
                )

        for name, expected_y in (
            ("power_junction_box", 3.1875),
            ("low_voltage_termination_box", 3.1875),
            ("front_ev_charger_body", 10.6875),
            ("front_wifi_access_point", 12.6875),
        ):
            with self.subTest(name=name):
                self.assertAlmostEqual(
                    self.resolved_component(enclosure, name).box_min[1],
                    expected_y,
                )

        ground = enclosure.grounds[0].resolved(enclosure.members)
        for name, x, y in (
            ("power_ground_riser", 15.055, 12.5),
            (
                "low_voltage_ground_riser_inlet",
                14,
                enclosure.members["rail_fbu"].min_on("y")-0.9375,
            ),
        ):
            with self.subTest(name=name):
                riser = self.resolved_conduit(enclosure, name)
                self.assertAlmostEqual(riser.points[0][0], x)
                self.assertAlmostEqual(riser.points[0][1], y)
                self.assertAlmostEqual(riser.points[-1][0], x)
                self.assertAlmostEqual(riser.points[-1][1], y)
                self.assertAlmostEqual(riser.points[0][2], ground.z_at(x, y))

    def test_larger_footprint_moves_geometry_with_mounting_surfaces(self) -> None:
        enclosure = build.build_enclosure(width=30, depth=26)
        enclosure.model.validate()

        self.assertEqual(enclosure.width, 30)
        self.assertEqual(enclosure.depth, 26)
        self.assertVectorAlmostEqual(
            enclosure.members["post_br"].start,
            (30, 26, -32),
        )
        self.assertAlmostEqual(enclosure.siding.max_x, 33.5)
        self.assertAlmostEqual(enclosure.siding.max_y, 29.5)

        light = self.resolved_component(enclosure, "front_street_light")
        self.assertAlmostEqual(
            light.box_min[0]+light.box_size[0]/2,
            (30+3.5)/2,
        )

        outlet = self.resolved_component(enclosure, "back_right_outlet")
        self.assertAlmostEqual(
            outlet.box_min[1]+outlet.box_size[1]/2,
            enclosure.members["post_br"].min_on("y")-1.5,
        )
        self.assertAlmostEqual(
            outlet.box_min[0],
            enclosure.members["post_br"].max_on("x")-1.05,
        )

        low_voltage_box = self.resolved_component(
            enclosure,
            "low_voltage_termination_box",
        )
        junction = self.resolved_component(enclosure, "power_junction_box")
        self.assertAlmostEqual(
            low_voltage_box.box_min[0]+low_voltage_box.box_size[0]/2,
            enclosure.LOW_VOLTAGE_UPPER_ELBOW_OUTLET[0],
        )
        front_center_rail = enclosure.members["front_center_rail"]
        self.assertAlmostEqual(
            junction.box_min[0]+junction.box_size[0]/2,
            front_center_rail.center_on("x")
            + 1.25
            + enclosure.POWER_JUNCTION_RIGHT_SHIFT,
        )
        self.assertAlmostEqual(
            junction.box_min[1]+junction.box_size[1],
            front_center_rail.min_on("y")+enclosure.POWER_JUNCTION_Y_SHIFT,
        )
        self.assertAlmostEqual(
            low_voltage_box.box_min[1],
            enclosure.members["rail_fbu"].min_on("y")-low_voltage_box.box_size[1],
        )

        outlet_feed = self.resolved_conduit(
            enclosure,
            "power_back_right_outlet_feed",
        )
        self.assertVectorAlmostEqual(
            outlet_feed.points[-1],
            enclosure.BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(enclosure.members),
        )
        for name in (
            "low_voltage_street_light_service",
            "low_voltage_wifi_feed",
            "low_voltage_ev_charger_feed",
        ):
            self.assertGreaterEqual(
                minimum_cable_bend_radius(enclosure.cables[name].points),
                enclosure.LOW_VOLTAGE_MINIMUM_BEND_RADIUS-1e-6,
            )

        tambour = enclosure.tambours["enclosure_tambour_door"].resolved(
            enclosure.model
        )
        self.assertAlmostEqual(tambour.left_points[0][1], 28.625)
        self.assertAlmostEqual(tambour.right_points[0][1], 28.625)
        self.assertAlmostEqual(tambour.left_points[0][0], 3.5)
        self.assertAlmostEqual(tambour.right_points[0][0], 30)

    def test_width_and_depth_can_be_overridden_independently(self) -> None:
        wider = build.build_enclosure(width=36)
        deeper = build.build_enclosure(depth=30)

        self.assertVectorAlmostEqual(
            wider.members["post_br"].start,
            (36, build.DEFAULT_DEPTH, -32),
        )
        self.assertVectorAlmostEqual(deeper.members["post_br"].start, (24, 30, -32))
        self.assertAlmostEqual(wider.FRONT_STREET_LIGHT_CENTER_X, (36+3.5)/2)
        self.assertAlmostEqual(deeper.BACK_RIGHT_OUTLET_CENTER_Y, 28.5)

    def test_taller_height_moves_only_top_referenced_geometry(self) -> None:
        baseline = build.default_build
        taller = build.build_enclosure(height=55)
        taller.model.validate()

        self.assertEqual(taller.height, 55)
        self.assertEqual(taller.members["post_br"].length, 87)
        self.assertAlmostEqual(taller.members["brace_fl_fr"].max_on("z"), 55)
        self.assertAlmostEqual(taller.members["brace_fr_br"].min_on("z"), 51.5)
        self.assertNotIn("rail_r_tambour", taller.members)
        self.assertAlmostEqual(taller.members["rail_rt"].min_on("z"), 48.875)
        self.assertAlmostEqual(taller.members["rail_rt"].max_on("z"), 50.375)
        self.assertAlmostEqual(taller.members["rail_rtam"].max_on("z"), 48.875)
        self.assertAlmostEqual(taller.siding.frame_top_z, 55)
        self.assertAlmostEqual(taller.siding.roof_support_z, 55.25)
        self.assertAlmostEqual(taller.TAMBOUR_TOP_Z, 52.375)
        self.assertAlmostEqual(taller.TAMBOUR_REAR_VERTICAL_LENGTH, 46.75)
        self.assertAlmostEqual(taller.TAMBOUR_TOP_TANGENT_LENGTH, 11.75)
        self.assertAlmostEqual(taller.TAMBOUR_FRONT_VERTICAL_LENGTH, 33.75)
        self.assertAlmostEqual(taller.LOW_VOLTAGE_SERVICE_LOOP_TOP_Z, 50.9375)

        for name in (
            "front_street_light",
            "front_ev_charger_plug",
            "front_wifi_access_point",
        ):
            baseline_component = self.resolved_component(baseline, name)
            taller_component = self.resolved_component(taller, name)
            self.assertAlmostEqual(
                taller_component.box_min[2]-baseline_component.box_min[2],
                55-build.DEFAULT_HEIGHT,
            )

        for name in (
            "front_ev_charger_body",
            "back_right_outlet",
            "power_junction_box",
            "low_voltage_termination_box",
        ):
            baseline_component = self.resolved_component(baseline, name)
            taller_component = self.resolved_component(taller, name)
            self.assertAlmostEqual(
                taller_component.box_min[2],
                baseline_component.box_min[2],
            )

        baseline_light_feed = self.resolved_conduit(
            baseline,
            "power_street_light_feed",
        )
        taller_light_feed = self.resolved_conduit(
            taller,
            "power_street_light_feed",
        )
        self.assertAlmostEqual(
            taller_light_feed.points[-1][2]-baseline_light_feed.points[-1][2],
            55-build.DEFAULT_HEIGHT,
        )

        baseline_outlet_feed = self.resolved_conduit(
            baseline,
            "power_back_right_outlet_feed",
        )
        taller_outlet_feed = self.resolved_conduit(
            taller,
            "power_back_right_outlet_feed",
        )
        self.assertVectorAlmostEqual(
            taller_outlet_feed.points[-1],
            baseline_outlet_feed.points[-1],
        )

        for name in (
            "low_voltage_street_light_service",
            "low_voltage_wifi_feed",
            "low_voltage_ev_charger_feed",
        ):
            self.assertGreaterEqual(
                minimum_cable_bend_radius(taller.cables[name].points),
                taller.LOW_VOLTAGE_MINIMUM_BEND_RADIUS-1e-6,
            )

        tambour = taller.tambours["enclosure_tambour_door"].resolved(taller.model)
        self.assertAlmostEqual(
            max(point[2] for point in tambour.left_points),
            taller.TAMBOUR_TRACK_TOP_Z,
        )

    def test_dimensions_must_be_finite_and_positive(self) -> None:
        for value in (0, -1, math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "finite positive"):
                    build.build_enclosure(width=value)
                with self.assertRaisesRegex(ValueError, "finite positive"):
                    build.build_enclosure(depth=value)
                with self.assertRaisesRegex(ValueError, "finite positive"):
                    build.build_enclosure(height=value)

    def test_main_accepts_named_dimension_flags(self) -> None:
        with (
            patch.object(build, "write_outputs") as write_outputs,
            patch.object(build, "deploy_generated_model") as deploy,
        ):
            self.assertEqual(
                build.main(
                    [
                        "--width",
                        "30.5",
                        "--depth",
                        "26.25",
                        "--height",
                        "55.5",
                    ]
                ),
                0,
            )

        enclosure = write_outputs.call_args.args[0]
        self.assertEqual(enclosure.width, 30.5)
        self.assertEqual(enclosure.depth, 26.25)
        self.assertEqual(enclosure.height, 55.5)
        deploy.assert_called_once_with(Path("output/model.scad"))

    def test_main_rejects_removed_power_conduit_layout_option(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, "2"):
                build.main(["--power-conduit-layout", "junction-riser"])

    def test_main_can_skip_deployment(self) -> None:
        with (
            patch.object(build, "write_outputs"),
            patch.object(build, "deploy_generated_model") as deploy,
        ):
            self.assertEqual(build.main(["--no-deploy"]), 0)
        deploy.assert_not_called()

    def test_playground_model_rewrites_only_the_remote_asset_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_path = Path(temporary_directory) / "model.scad"
            original = f'import("{build.LOCAL_MESH_PATH}");\n'
            model_path.write_text(original)

            transformed = build._playground_model_text(model_path)

            self.assertEqual(
                transformed,
                f'import("{build.PLAYGROUND_MESH_PATH}");\n',
            )
            self.assertEqual(model_path.read_text(), original)

    def test_playground_model_rewrites_every_component_mesh(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_path = Path(temporary_directory) / "model.scad"
            original = (
                f'import("{build.LOCAL_MESH_PATH}");\n'
                f'import("{build.LOCAL_CHARGER_BODY_MESH_PATH}");\n'
            )
            model_path.write_text(original)

            transformed = build._playground_model_text(model_path)

            self.assertEqual(
                transformed,
                f'import("{build.PLAYGROUND_MESH_PATH}");\n'
                f'import("{build.PLAYGROUND_CHARGER_BODY_MESH_PATH}");\n',
            )

    def test_deployment_failure_warns_and_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_path = Path(temporary_directory) / "model.scad"
            model_path.write_text(f'import("{build.LOCAL_MESH_PATH}");\n')
            failure = subprocess.CalledProcessError(
                128,
                ["git", "rev-parse"],
                stderr="fatal: not a git repository",
            )
            stderr = io.StringIO()
            with (
                patch.object(build.subprocess, "run", side_effect=failure),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertFalse(build.deploy_generated_model(model_path))

        self.assertIn("deployment to GitHub Pages failed", stderr.getvalue())

    def test_deployment_pushes_transformed_model_without_touching_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repository = root / "repository"
            remote = root / "remote.git"
            repository.mkdir()
            subprocess.run(
                ["git", "init", "--bare", str(remote)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repository,
                check=True,
            )
            (repository / "README.md").write_text("test repository\n")
            subprocess.run(
                ["git", "add", "README.md"], cwd=repository, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "remote", "add", "origin", str(remote)],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "push", "--quiet", "-u", "origin", "main"],
                cwd=repository,
                check=True,
            )

            model_path = root / "model.scad"
            model_path.write_text(f'import("{build.LOCAL_MESH_PATH}");\n')
            dirty_file = repository / "uncommitted.txt"
            dirty_file.write_text("not committed\n")
            dirty_stderr = io.StringIO()
            with contextlib.chdir(repository), contextlib.redirect_stderr(
                dirty_stderr
            ):
                self.assertFalse(build.deploy_generated_model(model_path))
            dirty_file.unlink()

            with contextlib.chdir(repository), contextlib.redirect_stdout(
                io.StringIO()
            ):
                self.assertTrue(build.deploy_generated_model(model_path))
                first_commit = subprocess.run(
                    [
                        "git",
                        f"--git-dir={remote}",
                        "rev-parse",
                        "refs/heads/pages-source",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                self.assertTrue(build.deploy_generated_model(model_path))
                second_commit = subprocess.run(
                    [
                        "git",
                        f"--git-dir={remote}",
                        "rev-parse",
                        "refs/heads/pages-source",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

            deployed_model = subprocess.run(
                [
                    "git",
                    f"--git-dir={remote}",
                    "show",
                    f"refs/heads/pages-source:{build.PLAYGROUND_DEPLOY_PATH}",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

            (repository / "README.md").write_text("local commit not pushed\n")
            subprocess.run(
                ["git", "add", "README.md"], cwd=repository, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Local only"],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            unsynced_stderr = io.StringIO()
            with contextlib.chdir(repository), contextlib.redirect_stderr(
                unsynced_stderr
            ):
                self.assertFalse(build.deploy_generated_model(model_path))
            final_commit = subprocess.run(
                [
                    "git",
                    f"--git-dir={remote}",
                    "rev-parse",
                    "refs/heads/pages-source",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout

        self.assertEqual(first_commit, second_commit)
        self.assertEqual(second_commit, final_commit)
        self.assertIn("working tree is not clean", dirty_stderr.getvalue())
        self.assertIn("is not synchronized", unsynced_stderr.getvalue())
        self.assertEqual(
            deployed_model,
            f'import("{build.PLAYGROUND_MESH_PATH}");\n',
        )
        self.assertEqual(status, "")

    def test_main_reports_invalid_dimensions_as_cli_errors(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, "2"):
                build.main(["--width", "nan"])

    def test_api_rejects_removed_power_conduit_layout_argument(self) -> None:
        with self.assertRaisesRegex(TypeError, "power_conduit_layout"):
            build.build_enclosure(power_conduit_layout="invalid")

    def test_write_outputs_uses_the_existing_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            build.write_outputs(build.build_enclosure(), output_dir)
            self.assertEqual(
                {path.name for path in output_dir.iterdir()},
                {
                    "model.scad",
                    "bom.csv",
                    "bom.json",
                    "cut_list.csv",
                    "cut_list.json",
                    "shopping_list.csv",
                    "shopping_list.json",
                    "fabrication.csv",
                    "fabrication.json",
                    "gusset_plate_6x6.dxf",
                    "tambour",
                },
            )
            manifest = json.loads(
                (output_dir / "tambour" / "manifest.json").read_text()
            )
            top_track = next(
                row for row in manifest if row["name"] == "left_top_straight_01"
            )
            self.assertEqual(top_track["size_y_mm"], 258.45)
            self.assertTrue((output_dir / "tambour" / "pull_handle.step").is_file())
            self.assertTrue((output_dir / "tambour" / "pull_handle.stl").is_file())
            manifest = json.loads(
                (output_dir / "tambour" / "manifest.json").read_text()
            )
            quantities = {row["name"]: row["quantity"] for row in manifest}
            self.assertEqual(quantities["pull_handle"], 2)
            self.assertEqual(quantities["joint_collar"], 40)
            self.assertTrue(
                (output_dir / "tambour" / "joint_fit_preview.step").is_file()
            )


if __name__ == "__main__":
    unittest.main()
