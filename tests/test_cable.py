from __future__ import annotations

import math
import unittest

from lumber_model import (
    EV_CHARGER_BODY,
    EV_CHARGER_PLUG,
    AbsoluteCoord,
    CableCollection,
    CableRun,
    ComponentCollection,
    GroundPlane,
    LumberCollection,
    Model,
    cable_centerline_length,
    ev_charger_cable_points,
    minimum_cable_bend_radius,
    rounded_cable_points,
)


class CableTests(unittest.TestCase):
    def charger_geometry(self):
        members = LumberCollection()
        members.add(
            "post_fl",
            assembly="frame",
            type="2x4",
            axis="z",
            start=AbsoluteCoord(13, 3, 3.75),
            length=45,
            rotated=False,
        )
        components = ComponentCollection()
        components.add(
            "front_ev_charger_body",
            component_type=EV_CHARGER_BODY,
            member="post_fl",
            at=24.5,
            face="wide_pos",
        )
        components.add(
            "front_ev_charger_plug",
            component_type=EV_CHARGER_PLUG,
            member="post_fl",
            at=36.5,
            face="wide_pos",
        )
        ground = GroundPlane(
            "ground",
            point_a=AbsoluteCoord(24, 0, 1),
            point_b=AbsoluteCoord(0, 20, -0.75),
            center=AbsoluteCoord(12, 10, 0.125),
            radius=48,
        ).resolved(members)
        member = members["post_fl"]
        body = components["front_ev_charger_body"].resolved(member)
        plug = components["front_ev_charger_plug"].resolved(member)
        return members, components, body, plug, ground

    def test_cable_run_validates_and_serializes(self) -> None:
        cable = CableRun(
            "cable",
            diameter=0.8,
            points=((0, 0, 0), (3, 4, 0)),
        )

        self.assertEqual(cable.centerline_length, 5)
        self.assertIn('"cable"', cable.resolved().scad_record())
        self.assertIn("0.8", cable.resolved().scad_record())

        with self.assertRaisesRegex(ValueError, "diameter"):
            CableRun("bad", diameter=0, points=((0, 0, 0), (1, 0, 0)))

    def test_cable_collection_rejects_duplicate_names(self) -> None:
        cables = CableCollection()
        cables.add("cable", diameter=0.8, points=((0, 0, 0), (1, 0, 0)))

        with self.assertRaisesRegex(ValueError, "Duplicate cable"):
            cables.add("cable", diameter=0.8, points=((0, 0, 0), (2, 0, 0)))

    def test_model_rejects_duplicate_cable_names(self) -> None:
        members, _, _, _, _ = self.charger_geometry()
        cables = [
            CableRun("cable", 0.8, ((0, 0, 0), (1, 0, 0))),
            CableRun("cable", 0.8, ((0, 0, 0), (2, 0, 0))),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate cable names"):
            Model(members, cables=cables).validate()

    def test_model_renders_cable_assembly(self) -> None:
        members, components, _, _, _ = self.charger_geometry()
        cables = CableCollection()
        cables.add("cable", diameter=0.8, points=((0, 0, 0), (1, 0, 0)))

        scad = Model(members, components=components, cables=cables).to_scad()

        self.assertIn("cables = [", scad)
        self.assertIn("cable_ev_charger_cable = true", scad)
        self.assertIn(
            "render_cable(c, object_is_highlighted(cable_name(c)))",
            scad,
        )

    def test_rounded_cable_points_replace_corner_with_requested_radius(self) -> None:
        points = rounded_cable_points(
            ((0, 0, 0), (4, 0, 0), (4, 4, 0)),
            {1: 1.25},
        )

        self.assertEqual(points[0], (0, 0, 0))
        self.assertEqual(points[-1], (4, 4, 0))
        self.assertAlmostEqual(minimum_cable_bend_radius(points), 1.25)
        self.assertTrue(all(a != b for a, b in zip(points, points[1:])))

        with self.assertRaisesRegex(ValueError, "90-degree"):
            rounded_cable_points(
                ((0, 0, 0), (4, 0, 0), (5, 1, 0)),
                {1: 1},
            )

    def test_ev_charger_cable_geometry_and_length(self) -> None:
        _, _, body, plug, ground = self.charger_geometry()
        points = ev_charger_cable_points(body, plug, ground)

        self.assertTrue(math.isclose(cable_centerline_length(points), 300, abs_tol=1e-7))
        self.assertEqual(
            points[0],
            (body.box_min[0] + 2.26, 8.10, body.box_min[2]),
        )
        self.assertEqual(
            points[-1],
            (
                plug.box_min[0] + plug.box_size[0] / 2,
                plug.box_min[1] + plug.box_size[1],
                plug.box_min[2],
            ),
        )
        self.assertGreater(points[2][0], points[1][0])
        self.assertAlmostEqual(
            max(point[0] for point in points[:27]),
            points[0][0] + 8.0,
        )

        first_bend_low = min(points[:27], key=lambda point: point[2])
        normal = ground.normal
        ground_z = ground.origin[2] - (
            normal[0] * (first_bend_low[0] - ground.origin[0])
            + normal[1] * (first_bend_low[1] - ground.origin[1])
        ) / normal[2]
        self.assertAlmostEqual(first_bend_low[2] - 0.4 - ground_z, 3)

        plug_top = plug.box_min[2] + plug.box_size[2]
        first_top_arc = points[27:52]
        over_plug = [
            point
            for point in first_top_arc
            if plug.box_min[0]
            <= point[0]
            <= plug.box_min[0] + plug.box_size[0]
        ]
        self.assertTrue(over_plug)
        self.assertGreaterEqual(
            min(point[2] - 0.4 for point in over_plug),
            plug_top - 1e-9,
        )

        self.assertLessEqual(min(point[0] for point in points), body.box_min[0] - 2.0)
        self.assertGreaterEqual(
            max(point[2] for point in points),
            plug.box_min[2] + plug.box_size[2] + 2.0,
        )
        self.assertEqual(points[-2][0:2], points[-1][0:2])
        self.assertLess(points[-2][2], points[-1][2])
        self.assertGreaterEqual(minimum_cable_bend_radius(points), 4.0 - 1e-6)

        terminal_points = points[-26:]
        terminal_start = terminal_points[0]
        target = points[-1]
        loop_low_point = (
            target[0],
            target[1],
            min(point[2] for point in points[:-26]),
        )
        plane_normal = (
            (loop_low_point[1] - target[1])
            * (terminal_start[2] - target[2])
            - (loop_low_point[2] - target[2])
            * (terminal_start[1] - target[1]),
            (loop_low_point[2] - target[2])
            * (terminal_start[0] - target[0])
            - (loop_low_point[0] - target[0])
            * (terminal_start[2] - target[2]),
            (loop_low_point[0] - target[0])
            * (terminal_start[1] - target[1])
            - (loop_low_point[1] - target[1])
            * (terminal_start[0] - target[0]),
        )
        for point in terminal_points:
            from_target = tuple(point[i] - target[i] for i in range(3))
            distance_from_plane = sum(
                plane_normal[i] * from_target[i] for i in range(3)
            )
            self.assertAlmostEqual(distance_from_plane, 0, places=8)


if __name__ == "__main__":
    unittest.main()
