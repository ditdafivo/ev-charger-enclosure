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

    def test_bounds_include_ground_and_add_grid_margin(self) -> None:
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

        self.assertEqual(plain_model._model_bounds(), (0, 10, 0, 3.5, 0, 1.5))
        self.assertEqual(plain_model._xygrid_bounds(), (-1, 11, -1, 4.5))

        bounds = model_with_ground._model_bounds()
        self.assertIsNotNone(bounds)
        assert bounds is not None
        self.assertLess(bounds[0], -390)
        self.assertGreater(bounds[1], 590)
        self.assertLess(bounds[2], -390)
        self.assertGreater(bounds[3], 590)
        self.assertLess(bounds[4], -60)
        self.assertGreater(bounds[5], 60)

    def test_empty_non_ground_geometry_emits_no_grid_bounds(self) -> None:
        model = Model([])

        self.assertIsNone(model._xygrid_bounds())
        self.assertIn("xygrid_bounds = [];", model.to_scad())
        self.assertIn("model_bounds = [];", model.to_scad())
        self.assertIn("xygrid_zloc = 0; // [-1:1:1]", model.to_scad())

    def test_generated_scad_contains_three_grids_and_preview_clipping(self) -> None:
        scad = Model(self.sample_members()).to_scad()

        self.assertIn("ground = false;", scad)
        self.assertIn("/* [Grids] */", scad)
        self.assertIn("xygrid_enabled = false;", scad)
        self.assertIn("xygrid_zloc = 0; // [-1:1:3]", scad)
        self.assertIn("xzgrid_enabled = false;", scad)
        self.assertIn("xzgrid_yloc = 0; // [-1:1:5]", scad)
        self.assertIn("yzgrid_enabled = false;", scad)
        self.assertIn("yzgrid_xloc = 0; // [-1:1:11]", scad)
        self.assertIn("xygrid_region = 0; // [-1:1:1]", scad)
        self.assertIn("xygrid_origin = [0, 0];", scad)
        self.assertIn("xygrid_zloc == floor(xygrid_zloc)", scad)
        self.assertIn("module render_xygrid(bounds, origin, zloc)", scad)
        self.assertIn("module render_xzgrid(bounds, origin, yloc)", scad)
        self.assertIn("module render_yzgrid(bounds, origin, xloc)", scad)
        self.assertIn("module render_model()", scad)
        self.assertIn("module render_preview_region()", scad)
        self.assertIn("intersection()", scad)
        self.assertIn("yzgrid_region == 1 ? yzgrid_xloc", scad)
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
            "if ($preview && xygrid_enabled && len(xygrid_bounds) == 4)",
            scad,
        )
        self.assertIn("if ($preview && region_enabled", scad)
        self.assertIn("else {\n    render_model();\n}", scad)

    def test_grid_slider_ranges_extend_beyond_geometry(self) -> None:
        model = Model(self.sample_members())

        self.assertEqual(model._grid_slider_range(0), "-1:1:11")
        self.assertEqual(model._grid_slider_range(1), "-1:1:5")
        self.assertEqual(model._grid_slider_range(2), "-1:1:3")

    def test_grid_location_defaults_are_inside_dynamic_ranges(self) -> None:
        members = LumberCollection()
        members.add(
            "positive_rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(10, 20, 30),
            length=5,
        )
        scad = Model(members).to_scad()

        self.assertIn("yzgrid_xloc = 9; // [9:1:16]", scad)
        self.assertIn("xzgrid_yloc = 19; // [19:1:25]", scad)
        self.assertIn("xygrid_zloc = 29; // [29:1:33]", scad)

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

    def test_full_enclosure_ranges_cover_all_renderable_geometry(self) -> None:
        self.assertEqual(
            build.model._grid_slider_range(0),
            "-37:1:61",
        )
        self.assertEqual(build.model._grid_slider_range(1), "-40:1:59")
        self.assertEqual(build.model._grid_slider_range(2), "-37:1:50")


if __name__ == "__main__":
    unittest.main()
