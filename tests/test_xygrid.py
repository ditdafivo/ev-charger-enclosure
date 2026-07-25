from __future__ import annotations

import unittest

import build
from lumber_model import AbsoluteCoord, GroundPlane, LumberCollection, Model


class XYGridTests(unittest.TestCase):
    @staticmethod
    def sample_members() -> LumberCollection:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )
        return members

    def test_bounds_add_one_inch_and_ignore_ground_disk(self) -> None:
        members = self.sample_members()
        plain_model = Model(members)
        model_with_ground = Model(
            members,
            grounds=[
                GroundPlane(
                    "ground",
                    point_a=AbsoluteCoord(10, 0, 1),
                    point_b=AbsoluteCoord(0, 10, 1),
                    center=AbsoluteCoord(100, 100, 0),
                    radius=500,
                    origin_reference="rail",
                )
            ],
        )

        expected = (-1, 11, -1, 4.5)
        self.assertEqual(plain_model._xygrid_bounds(), expected)
        self.assertEqual(model_with_ground._xygrid_bounds(), expected)
        self.assertIn("xygrid_bounds = [-1, 11, -1, 4.5];", model_with_ground.to_scad())

    def test_empty_non_ground_geometry_emits_no_grid_bounds(self) -> None:
        model = Model([])

        self.assertIsNone(model._xygrid_bounds())
        self.assertIn("xygrid_bounds = [];", model.to_scad())

    def test_generated_scad_contains_customizer_and_preview_only_grid(self) -> None:
        scad = Model(self.sample_members()).to_scad()

        self.assertIn("ground = false;", scad)
        self.assertIn("xygrid_origin = [0, 0];", scad)
        self.assertIn("xygrid_zloc == floor(xygrid_zloc)", scad)
        self.assertIn("module render_xygrid(bounds, origin, zloc)", scad)
        self.assertIn("coordinate % 10 == 0", scad)
        self.assertIn("coordinate % 5 == 0", scad)
        self.assertIn(
            "[ceil(min_x - origin_x) : floor(max_x - origin_x)]",
            scad,
        )
        self.assertIn(
            "[ceil(min_y - origin_y) : floor(max_y - origin_y)]",
            scad,
        )
        self.assertIn(
            "if ($preview && xygrid_zloc >= 0 && len(xygrid_bounds) == 4)",
            scad,
        )

    def test_full_enclosure_grid_origin_is_post_fr_outer_front_corner(self) -> None:
        post_fr = build.members["post_fr"]

        self.assertEqual(
            build.model.xygrid_origin,
            (post_fr.max_on("x"), post_fr.min_on("y")),
        )
        self.assertEqual(build.model.xygrid_origin, (27.5, 0))
        self.assertIn("xygrid_origin = [27.5, 0];", build.model.to_scad())

    def test_enclosure_grid_origin_tracks_non_default_width(self) -> None:
        enclosure = build.build_enclosure(width=30)

        self.assertEqual(enclosure.model.xygrid_origin, (33.5, 0))

    def test_full_enclosure_bounds_cover_non_ground_geometry(self) -> None:
        self.assertEqual(
            build.model._xygrid_bounds(),
            (-2.125, 32.5, -6.0, 24.0),
        )


if __name__ == "__main__":
    unittest.main()
