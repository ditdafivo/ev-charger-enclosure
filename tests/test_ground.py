from __future__ import annotations

import unittest

from lumber_model import AbsoluteCoord, GroundPlane, LumberCollection, Model, RelativeCoord


class GroundPlaneTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_ground_plane_anchors_post_fl_at_zero_z(self) -> None:
        members = LumberCollection()
        members.add(
            "post_fl",
            assembly="posts",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(10, 20, -36),
            length=84,
        )
        members.add(
            "post_fr",
            assembly="posts",
            type="4x4",
            axis="z",
            start=RelativeCoord("post_fl", 24, 0, 0),
            length=84,
        )
        members.add(
            "post_bl",
            assembly="posts",
            type="4x4",
            axis="z",
            start=RelativeCoord("post_fl", 0, 20, 0),
            length=84,
        )
        model = Model(
            members,
            grounds=[
                GroundPlane(
                    "sloped_ground",
                    point_a=AbsoluteCoord(34, 20, 2),
                    point_b=RelativeCoord("post_bl", 0, 0, 37),
                    center=RelativeCoord("post_fl", 12, 10, 36),
                    radius=36,
                )
            ],
        )

        ground = model.grounds[0].resolved(model)

        self.assertVectorAlmostEqual(ground.origin, (10, 20, 0))
        self.assertVectorAlmostEqual(ground.point_a, (34, 20, 2))
        self.assertVectorAlmostEqual(ground.point_b, (10, 40, 1))
        self.assertVectorAlmostEqual(ground.center, (22, 30, 0))
        self.assertGreater(ground.normal[2], 0)
        self.assertAlmostEqual(ground.z_at(10, 20), 0)
        self.assertAlmostEqual(ground.z_at(34, 20), 2)
        self.assertAlmostEqual(ground.z_at(10, 40), 1)

    def test_ground_plane_is_rendered_to_scad(self) -> None:
        members = LumberCollection()
        members.add(
            "post_fl",
            assembly="posts",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, -36),
            length=84,
        )
        model = Model(
            members,
            grounds=[
                GroundPlane(
                    "ground",
                    point_a=AbsoluteCoord(24, 0, 1),
                    point_b=AbsoluteCoord(0, 20, 0.5),
                    center=AbsoluteCoord(12, 10, 0),
                    radius=30,
                )
            ],
        )

        scad = model.to_scad()

        self.assertIn("grounds = [", scad)
        self.assertIn('"ground"', scad)
        self.assertIn("render_ground(g)", scad)

    def test_ground_plane_rejects_collinear_points(self) -> None:
        members = LumberCollection()
        members.add(
            "post_fl",
            assembly="posts",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, -36),
            length=84,
        )
        model = Model(
            members,
            grounds=[
                GroundPlane(
                    "bad_ground",
                    point_a=AbsoluteCoord(1, 0, 0),
                    point_b=AbsoluteCoord(2, 0, 0),
                    center=AbsoluteCoord(0, 0, 0),
                    radius=30,
                )
            ],
        )

        with self.assertRaisesRegex(ValueError, "bad_ground"):
            model.validate()


if __name__ == "__main__":
    unittest.main()
