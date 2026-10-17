from __future__ import annotations

import unittest

from lumber_model import AbsoluteCoord, GroundPlane, LumberCollection, Model, RelativeCoord
from lumber_model import GroundSurface
import build


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
        self.assertIn("ground = false;", scad)
        self.assertIn("if (ground)", scad)
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


class GroundSurfaceTests(unittest.TestCase):
    def test_survey_matches_outside_corners_with_level_finished_tops(self) -> None:
        enclosure = build.default_build
        ground = enclosure.grounds[0].resolved(enclosure.model)
        for name, x, y, measured in (
            ("post_fl", 0, 0, 49.625),
            ("post_fr", 27.5, 0, 49.25),
            ("post_br", 27.5, 22.875, 47),
            ("post_bl", 0, 22.875, 48.5),
        ):
            with self.subTest(post=name):
                top = enclosure.members[name].max_on("z")
                self.assertAlmostEqual(top, 49.625)
                self.assertAlmostEqual(top-ground.z_at(x, y), measured)
        self.assertAlmostEqual(ground.z_at(13.75, 11.4375), 1.03125)
        self.assertEqual(ground.z_at(-20, -20), 0)
        self.assertEqual(ground.z_at(100, 100), 2.625)

    def test_custom_height_keeps_survey_ground_fixed(self) -> None:
        enclosure = build.build_enclosure(width=36, depth=30, height=55)
        ground = enclosure.grounds[0].resolved(enclosure.model)
        self.assertEqual(ground.z_at(39.5, 33.5), 2.625)
        self.assertEqual(ground.z_at(0, 0), 0)
        self.assertEqual(enclosure.members["post_br"].max_on("z"), 55)

    def test_mesh_is_closed_and_uses_survey_elevations(self) -> None:
        ground = build.grounds[0].resolved(build.model)
        vertices, faces = ground.mesh()
        directed_edges: dict[tuple[int, int], int] = {}
        for face in faces:
            for a, b in zip(face, face[1:]+face[:1]):
                directed_edges[a, b] = directed_edges.get((a, b), 0)+1
        for (a, b), count in directed_edges.items():
            self.assertEqual(count, 1)
            self.assertEqual(directed_edges.get((b, a)), 1)
        for x, y, z in vertices[:len(vertices)//2]:
            self.assertAlmostEqual(z, ground.z_at(x, y))
        for point in ground.corners:
            self.assertIn(point, vertices)
        scad = build.model.to_scad()
        self.assertIn("polyhedron(points = g[6], faces = g[7]", scad)
        self.assertLessEqual(build.model._model_bounds()[4], ground.z_bounds[0])

    def test_nonrectangular_survey_is_rejected(self) -> None:
        ground = GroundSurface(
            "bad_survey",
            corners=(AbsoluteCoord(0, 0, 0), AbsoluteCoord(2, 0, 0),
                     AbsoluteCoord(3, 2, 1), AbsoluteCoord(0, 2, 1)),
            center=AbsoluteCoord(1, 1, 0), radius=10,
        )
        with self.assertRaisesRegex(ValueError, "rectangle"):
            ground.resolved(LumberCollection())


if __name__ == "__main__":
    unittest.main()
