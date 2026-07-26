from __future__ import annotations

import unittest

import build
from lumber_model import AbsoluteCoord, Footing, LumberCollection, Model


class FootingTests(unittest.TestCase):
    def test_validates_and_renders_translucent_cylinder(self) -> None:
        members = LumberCollection()
        members.add(
            "post",
            assembly="posts",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, -32),
            length=79,
        )
        footing = Footing(
            "footing",
            center=AbsoluteCoord(1.75, 1.75, 0),
            diameter=10,
            bottom_z=-36,
            top_z=0,
        )
        model = Model(members, footings=[footing])

        resolved = footing.resolved(model)
        self.assertEqual(resolved.center, (1.75, 1.75, -18))
        self.assertEqual(resolved.color[3], 0.45)

        scad = model.to_scad()
        self.assertIn("footings = true;", scad)
        self.assertIn('["footing", [1.75, 1.75, -18], 10, -36, 0,', scad)
        self.assertIn("module render_footing(f, highlighted = false)", scad)

    def test_rejects_invalid_dimensions_and_duplicate_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "diameter must be positive"):
            Footing("bad", AbsoluteCoord(0, 0, 0), 0, -36, 0)
        with self.assertRaisesRegex(ValueError, "top_z must be greater"):
            Footing("bad", AbsoluteCoord(0, 0, 0), 10, 0, 0)

        footing = Footing("same", AbsoluteCoord(0, 0, 0), 10, -36, 0)
        with self.assertRaisesRegex(ValueError, "Duplicate footing names"):
            Model([], footings=[footing, footing]).validate()

    def test_default_enclosure_footings_match_post_centerlines(self) -> None:
        enclosure = build.default_build
        self.assertEqual(len(enclosure.footings), 4)

        for suffix in ("fl", "fr", "bl", "br"):
            post = enclosure.members[f"post_{suffix}"]
            footing = next(
                item for item in enclosure.footings if item.name == f"footing_{suffix}"
            ).resolved(enclosure.model)
            self.assertEqual(
                footing.center[:2],
                (post.center_on("x"), post.center_on("y")),
            )
            self.assertEqual(footing.diameter, 10)
            self.assertEqual((footing.bottom_z, footing.top_z), (-36, 0))


if __name__ == "__main__":
    unittest.main()
