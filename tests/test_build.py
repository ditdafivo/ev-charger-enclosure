from __future__ import annotations

import contextlib
import io
import math
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


class TopBracingBuildTests(unittest.TestCase):
    def test_default_uses_one_shallow_diagonal_at_the_existing_frame_top(self) -> None:
        brace = build.members["brace_bl_fr"]

        self.assertNotIn("brace_br_fl", build.members)
        self.assertEqual(brace.type, "1x4")
        self.assertAlmostEqual(brace.thickness, 0.75)
        self.assertAlmostEqual(brace.min[2], 46.25)
        self.assertAlmostEqual(brace.max[2], build.DEFAULT_HEIGHT)
        self.assertAlmostEqual(brace.length, 25.3281587)
        self.assertAlmostEqual(brace.cut_angle_deg, 35.965005)

    def test_custom_dimensions_recalculate_shallow_diagonal(self) -> None:
        enclosure = build.build_enclosure(width=36, depth=30, height=55)
        brace = enclosure.members["brace_bl_fr"]

        self.assertEqual(brace.type, "1x4")
        self.assertAlmostEqual(brace.thickness, 0.75)
        self.assertAlmostEqual(brace.max[2], 55)
        self.assertAlmostEqual(brace.min[2], 54.25)
        self.assertAlmostEqual(
            brace.length,
            math.hypot(36 - 3.5, 30 - 3.5),
        )

    def test_cut_and_shopping_lists_include_one_by_four_brace(self) -> None:
        cut_row = next(
            row
            for row in build.model.cut_list_rows(rounding_increment=None)
            if row["members"] == "brace_bl_fr"
        )
        shopping_row = next(
            row for row in build.model.shopping_list_rows() if row["type"] == "1x4"
        )

        self.assertEqual(cut_row["type"], "1x4")
        self.assertEqual(cut_row["qty"], 1)
        self.assertEqual(shopping_row["stock_length_in"], 72)
        self.assertEqual(shopping_row["qty"], 1)

    def test_tambour_top_support_and_maximum_curtain_clear_bracing(self) -> None:
        enclosure = build.default_build
        brace_bottom = enclosure.members["brace_fl_bl"].min_on("z")

        for name in ("rail_l_tambour", "rail_r_tambour"):
            with self.subTest(name=name):
                support = enclosure.members[name]
                self.assertAlmostEqual(support.min_on("z"), 43.75)
                self.assertAlmostEqual(support.max_on("z"), 45.25)
                self.assertAlmostEqual(
                    brace_bottom-support.max_on("z"),
                    enclosure.TAMBOUR_BRACE_CLEARANCE,
                )

        maximum_curtain_top = (
            enclosure.TAMBOUR_TOP_Z+enclosure.TAMBOUR_MAX_SLAT_DEPTH/2
        )
        self.assertAlmostEqual(maximum_curtain_top, 45.25)
        self.assertAlmostEqual(
            brace_bottom-maximum_curtain_top,
            enclosure.TAMBOUR_BRACE_CLEARANCE,
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

        self.assertVectorAlmostEqual(outlet.box_min, (26.45, 15.475, 15.15))
        self.assertVectorAlmostEqual(outlet.box_size, (2.3, 2.8, 5.7))
        self.assertAlmostEqual(outlet.box_min[0] + outlet.box_size[0], 28.75)
        self.assertVectorAlmostEqual(cover.box_min, (28.75, 14.545, 14.835))
        self.assertVectorAlmostEqual(cover.box_size, (2.75, 4.66, 6.33))

    def test_bottom_hub_entry_is_available_for_future_conduit(self) -> None:
        self.assertVectorAlmostEqual(
            build.BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(build.members),
            (27.016, 16.875, 15.15),
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
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_backers_span_front_posts_and_form_contiguous_backing_field(self) -> None:
        for name, expected_z in (
            ("front_street_light_backer_bottom", 34.75),
            ("front_street_light_backer_lower", 38.25),
            ("front_street_light_backer_upper", 41.75),
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
        self.assertAlmostEqual(bottom.min_on("z"), 33)
        self.assertAlmostEqual(bottom.max_on("z"), lower.min_on("z"))
        self.assertAlmostEqual(lower.max_on("z"), upper.min_on("z"))
        self.assertAlmostEqual(upper.max_on("z"), 43.5)

    def test_box_stack_and_light_have_finished_position(self) -> None:
        lower_backer = build.members["front_street_light_backer_lower"]
        box = build.components["front_street_light_base_box"].resolved(lower_backer)
        ring = build.components["front_street_light_extension_ring"].resolved(
            lower_backer
        )
        light = build.components["front_street_light"].resolved(lower_backer)

        self.assertVectorAlmostEqual(box.box_min, (11.65, 0.70, 37.3))
        self.assertVectorAlmostEqual(box.box_size, (4.2, 1.6, 5.4))
        self.assertVectorAlmostEqual(ring.box_min, (11.55, -1.0, 37.8))
        self.assertVectorAlmostEqual(ring.box_size, (4.4, 1.7, 4.4))
        self.assertVectorAlmostEqual(light.box_min, (4.75, -5.0, 38.0))
        self.assertVectorAlmostEqual(light.box_size, (18.0, 4.0, 4.0))
        self.assertAlmostEqual(
            ring.box_min[1] + ring.box_size[1],
            box.box_min[1],
        )
        self.assertAlmostEqual(light.box_min[1] + light.box_size[1], ring.box_min[1])
        self.assertAlmostEqual(
            light.box_min[1] + light.box_size[1],
            build.siding.min_y - build.siding.board_thickness,
        )

    def test_bottom_port_receives_conduit(self) -> None:
        self.assertVectorAlmostEqual(
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY.resolve(build.members),
            (13.75, 1.5, 37.3),
        )
        self.assertIsInstance(
            build.FRONT_STREET_LIGHT_CONDUIT_ENTRY_ANCHOR,
            ComponentAnchor,
        )

    def test_siding_is_cut_out_around_extension_ring(self) -> None:
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
            (14, 1.1875, build.POWER_JUNCTION_BOTTOM_Z),
        )
        self.assertVectorAlmostEqual(box.box_size, (4, 4, 4))
        self.assertAlmostEqual(
            build.POWER_JUNCTION_BOTTOM_Z-build.POWER_JUNCTION_GROUND_Z,
            6,
        )
        self.assertEqual(build.POWER_JUNCTION_BOX_FILL.required_volume, 37)
        self.assertEqual(build.POWER_JUNCTION_BOX_FILL.remaining_volume, 12)

    def test_default_spline_fittings_and_route(self) -> None:
        expected_types = {
            "power_junction_input_adapter": "carlon_e996g_box_adapter",
            "power_junction_input_coupling": "carlon_e940g_coupling",
            "power_junction_ev_adapter": "carlon_e996f_box_adapter",
            "power_junction_ev_coupling": "carlon_e940f_coupling",
        }
        for name, expected_type in expected_types.items():
            with self.subTest(name=name):
                self.assertEqual(
                    build.components[name].component_type.name,
                    expected_type,
                )

        for name in ("power_ev_t_body", "power_ev_lb_body", "power_ev_reducer"):
            self.assertNotIn(name, build.components)
        self.assertNotIn("power_t_junction_feed", build.conduits)
        self.assertNotIn("power_ev_lb_feed", build.conduits)

        box_instance = build.components["power_junction_box"]
        box = box_instance.resolved(build.members[box_instance.member])
        input_port_xy = (
            build.POWER_JUNCTION_INPUT_PORT_X,
            build.POWER_JUNCTION_INPUT_PORT_Y,
        )
        self.assertVectorAlmostEqual(input_port_xy, (14.975, 4.2125))
        riser = self.resolved_conduit("power_ground_riser")
        self.assertVectorAlmostEqual(riser.points[0][:2], input_port_xy)
        self.assertVectorAlmostEqual(riser.points[-1][:2], input_port_xy)
        for name in (
            "power_junction_input_adapter",
            "power_junction_input_coupling",
        ):
            instance = build.components[name]
            fitting = instance.resolved(build.members[instance.member])
            fitting_center_xy = (
                fitting.box_min[0]+fitting.box_size[0]/2,
                fitting.box_min[1]+fitting.box_size[1]/2,
            )
            self.assertVectorAlmostEqual(fitting_center_xy, input_port_xy)

        self.assertAlmostEqual(
            input_port_xy[0]-box.box_min[0],
            build.POWER_JUNCTION_INPUT_EDGE_CLEARANCE,
        )
        self.assertAlmostEqual(
            box.box_min[1]+box.box_size[1]-input_port_xy[1],
            build.POWER_JUNCTION_INPUT_EDGE_CLEARANCE,
        )

        rail = build.members["front_center_rail"]
        self.assertAlmostEqual(
            build.POWER_JUNCTION_SPLINE_PORT_X,
            rail.max_on("x")
            + CONDUIT_OD_BY_TRADE_SIZE["1"]/2
            + build.POWER_EV_RAIL_CLEARANCE,
        )
        self.assertAlmostEqual(build.POWER_JUNCTION_SPLINE_PORT_Y, box.box_min[1]+3)

        ev = self.resolved_conduit("power_ev_charger_feed")
        self.assertEqual(ev.trade_size, "1")
        self.assertEqual(len(ev.points), 25)
        self.assertVectorAlmostEqual(
            ev.points[0],
            build.POWER_JUNCTION_EV_COUPLING_END,
        )
        self.assertVectorAlmostEqual(ev.points[-1], build.POWER_EV_ENTRY)
        self.assertVectorAlmostEqual(
            build.POWER_EV_OFFSET_CONTROL_A[:2], ev.points[0][:2]
        )
        self.assertVectorAlmostEqual(
            build.POWER_EV_OFFSET_CONTROL_B[:2], ev.points[-1][:2]
        )
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
            (16, 11.3375, 25.65),
        )
        self.assertAlmostEqual(
            ev.points[0][0]
            - CONDUIT_OD_BY_TRADE_SIZE["1"]/2
            - rail.max_on("x"),
            0.25,
        )

    def test_riser_and_equipment_feeds_use_relative_endpoints(self) -> None:
        enclosure = build.default_build
        riser = self.resolved_conduit("power_ground_riser", enclosure)
        ev = self.resolved_conduit("power_ev_charger_feed", enclosure)
        light = self.resolved_conduit("power_street_light_feed", enclosure)

        self.assertEqual(riser.trade_size, "1-1/4")
        self.assertVectorAlmostEqual(
            riser.points[0],
            (
                enclosure.POWER_JUNCTION_INPUT_PORT_X,
                enclosure.POWER_JUNCTION_INPUT_PORT_Y,
                enclosure.POWER_JUNCTION_INPUT_GROUND_Z,
            ),
        )
        self.assertEqual(riser.points[0][:2], riser.points[-1][:2])
        self.assertEqual(ev.trade_size, "1")
        self.assertVectorAlmostEqual(ev.points[-1], enclosure.POWER_EV_ENTRY)

        self.assertTrue(
            all(
                isinstance(point, RelativeCoord)
                for point in enclosure.conduits["power_ground_riser"].points
            )
        )
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
            light.points[0], enclosure.POWER_LIGHT_COUPLING_END
        )
        self.assertVectorAlmostEqual(
            light.points[-1],
            enclosure.FRONT_STREET_LIGHT_CONDUIT_ENTRY.resolve(enclosure.members),
        )
        self.assertEqual(len(ev.points), 25)
        self.assertEqual(light.bends, ((1, 3), (2, 3), (3, 3)))
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
        self.assertAlmostEqual(adapter.box_min[0], build.POWER_JUNCTION_RIGHT_X)
        self.assertLess(
            adapter.box_min[1]+adapter.box_size[1]/2,
            outlet.box_min[1]+outlet.box_size[1]/2,
        )
        self.assertAlmostEqual(
            adapter.box_min[2]+adapter.box_size[2]/2,
            outlet.box_min[2]+outlet.box_size[2]/2,
        )
        self.assertVectorAlmostEqual(
            light.points[0],
            build.POWER_LIGHT_COUPLING_END,
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
            1,
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
            self.assertVectorAlmostEqual(
                ev.points[0],
                enclosure.POWER_JUNCTION_EV_COUPLING_END,
            )
            self.assertVectorAlmostEqual(ev.points[-1], enclosure.POWER_EV_ENTRY)
            self.assertVectorAlmostEqual(
                enclosure.POWER_EV_OFFSET_CONTROL_A[:2], ev.points[0][:2]
            )
            self.assertVectorAlmostEqual(
                enclosure.POWER_EV_OFFSET_CONTROL_B[:2], ev.points[-1][:2]
            )

    def test_outlet_feed_has_two_sweeps_and_clears_low_rail(self) -> None:
        outlet = self.resolved_conduit("power_back_right_outlet_feed")

        self.assertEqual(outlet.trade_size, "1/2")
        self.assertEqual(outlet.bends, ((1, 4), (2, 4)))
        self.assertVectorAlmostEqual(
            outlet.points[0],
            (
                build.POWER_OUTLET_COUPLING_END_X,
                build.POWER_JUNCTION_PORT_Y,
                build.POWER_JUNCTION_OUTLET_PORT_Z,
            ),
        )
        self.assertVectorAlmostEqual(
            outlet.points[-1],
            build.BACK_RIGHT_OUTLET_CONDUIT_ENTRY.resolve(build.members),
        )
        self.assertGreater(
            min(point[2] for point in outlet.points),
            build.members["rail_rb"].max_on("z"),
        )
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

    def test_low_voltage_box_stays_one_inch_behind_shifted_power_box(self) -> None:
        instance = build.components["low_voltage_termination_box"]
        box = self.resolved_component("low_voltage_termination_box")

        self.assertIs(instance.component_type, CARLON_E987N_JUNCTION_BOX)
        self.assertEqual(instance.face, "wide_neg")
        self.assertVectorAlmostEqual(box.box_min, (9, 2.1875, 11))
        self.assertVectorAlmostEqual(box.box_size, (4, 4, 4))
        self.assertAlmostEqual(box.box_min[0]+box.box_size[0], 13)
        self.assertAlmostEqual(box.box_min[2]+box.box_size[2]/2, 13)

        box_min_y = box.box_min[1]
        box_max_y = box_min_y+box.box_size[1]
        power = self.resolved_component("power_junction_box")
        self.assertAlmostEqual(box_min_y, power.box_min[1]+1)
        self.assertAlmostEqual(
            box_max_y,
            power.box_min[1]+power.box_size[1]+1,
        )
        self.assertAlmostEqual(power.box_min[0]-(box.box_min[0]+box.box_size[0]), 1)

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
                build.LOW_VOLTAGE_BOX_BOTTOM_Z,
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

    def test_three_quarter_riser_has_exact_ground_and_adapter_endpoints(self) -> None:
        riser = self.resolved_conduit("low_voltage_ground_riser")

        self.assertEqual(riser.trade_size, "3/4")
        self.assertEqual(riser.assembly, "low_voltage_conduit")
        self.assertVectorAlmostEqual(
            riser.points[0],
            (
                build.LOW_VOLTAGE_INPUT_X,
                build.LOW_VOLTAGE_INPUT_Y,
                build.LOW_VOLTAGE_GROUND_Z,
            ),
        )
        self.assertVectorAlmostEqual(
            riser.points[-1],
            (
                build.LOW_VOLTAGE_INPUT_X,
                build.LOW_VOLTAGE_INPUT_Y,
                build.LOW_VOLTAGE_INPUT_ADAPTER_END_Z,
            ),
        )
        self.assertEqual(riser.points[0][:2], riser.points[-1][:2])

        self.assertAlmostEqual(
            riser.points[0][0],
            build.LOW_VOLTAGE_POST_FL_MIN_X-1,
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

        for index, (name, endpoint) in enumerate(expected_endpoints.items()):
            cable = build.cables[name]
            self.assertEqual(cable.assembly, "low_voltage_cabling")
            self.assertEqual(cable.diameter, 1/8)
            self.assertEqual(cable.color, expected_colors[name])
            self.assertVectorAlmostEqual(
                cable.points[0],
                (
                build.LOW_VOLTAGE_GLAND_XS[index],
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
        self.assertAlmostEqual(min(point[2] for point in service.points[-50:]), 42.9375)
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
        self.assertLess(build.path_2_riser_bypass[0], build.LOW_VOLTAGE_INPUT_X)
        self.assertIn(build.path_2_front_rail, wifi_feed.points)
        self.assertGreater(build.path_2_front_rail[0], build.path_2_start[0])
        self.assertGreater(build.path_2_front_rail[1], build.path_2_start[1])
        self.assertLess(
            build.path_2_front_rail[0],
            build.members["front_center_rail"].min_on("x"),
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
        self.assertGreater(build.path_3_riser_bypass[0], build.LOW_VOLTAGE_INPUT_X)
        self.assertIn(build.path_3_front_rail, ev_feed.points)
        self.assertGreater(build.path_3_front_rail[0], build.path_3_start[0])
        self.assertGreater(build.path_3_front_rail[1], build.path_3_start[1])
        self.assertAlmostEqual(
            build.path_3_front_rail[1]-build.path_2_front_rail[1],
            build.LOW_VOLTAGE_CABLE_DIAMETER,
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
        for cable in (wifi_feed, ev_feed):
            self.assertAlmostEqual(
                minimum_cable_bend_radius(cable.points),
                build.LOW_VOLTAGE_GLAND_EXIT_TURN_RADIUS,
            )

        rail_fb=build.members["rail_fb"]
        cable_radius=build.LOW_VOLTAGE_CABLE_DIAMETER/2
        rail_min=tuple(rail_fb.min_on(axis)-cable_radius for axis in "xyz")
        rail_max=tuple(rail_fb.max_on(axis)+cable_radius for axis in "xyz")

        def segment_intersects_rail(
            start: tuple[float,float,float],
            end: tuple[float,float,float],
        ) -> bool:
            interval_min=0.0
            interval_max=1.0
            for index in range(3):
                delta=end[index]-start[index]
                if abs(delta) < 1e-12:
                    if not rail_min[index] <= start[index] <= rail_max[index]:
                        return False
                    continue
                near=(rail_min[index]-start[index])/delta
                far=(rail_max[index]-start[index])/delta
                if near > far:
                    near,far=far,near
                interval_min=max(interval_min, near)
                interval_max=min(interval_max, far)
                if interval_min > interval_max:
                    return False
            return True

        for cable in (wifi_feed, ev_feed):
            self.assertFalse(
                any(
                    segment_intersects_rail(start, end)
                    for start,end in zip(cable.points, cable.points[1:])
                )
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
            junction.box_min[0]
            - (low_voltage_box.box_min[0]+low_voltage_box.box_size[0]),
            enclosure.LOW_VOLTAGE_BOX_GAP,
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
            front_center_rail.min_on("y")-low_voltage_box.box_size[1],
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
        self.assertAlmostEqual(tambour.left_points[0][1], 29)
        self.assertAlmostEqual(tambour.right_points[0][1], 29)
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
        self.assertAlmostEqual(taller.members["rail_r_tambour"].center_on("z"), 52.5)
        self.assertAlmostEqual(taller.members["rail_rt"].center_on("z"), 51.5)
        self.assertAlmostEqual(taller.siding.frame_top_z, 55)
        self.assertAlmostEqual(taller.TAMBOUR_TOP_Z, 52.5)
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
                8,
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
            8,
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
            52.5,
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
                },
            )


if __name__ == "__main__":
    unittest.main()
