from __future__ import annotations

import unittest

from lumber_model import (
    AbsoluteCoord,
    LumberCollection,
    Model,
    TambourBend,
    TambourDoor,
)


def sample_tambour(name: str = "door") -> TambourDoor:
    return TambourDoor(
        name=name,
        left_points=(
            AbsoluteCoord(0, 10, 0),
            AbsoluteCoord(0, 10, 10),
            AbsoluteCoord(0, 0, 10),
            AbsoluteCoord(0, 0, 6),
        ),
        right_points=(
            AbsoluteCoord(5, 10, 0),
            AbsoluteCoord(5, 10, 10),
            AbsoluteCoord(5, 0, 10),
            AbsoluteCoord(5, 0, 6),
        ),
        bends=(
            TambourBend(point_index=1, radius=2, segments=4),
            TambourBend(point_index=2, radius=2, segments=4),
        ),
        door_length=4,
    )


class TambourTests(unittest.TestCase):
    def test_bends_expand_both_tracks_to_matching_arc_points(self) -> None:
        resolved = sample_tambour().resolved()

        self.assertEqual(len(resolved.left_points), len(resolved.right_points))
        self.assertGreater(len(resolved.left_points), 4)
        self.assertEqual(resolved.bends, ((1, 2), (2, 2)))
        self.assertEqual(resolved.left_points[1], (0.0, 10.0, 8.0))
        self.assertEqual(resolved.right_points[1], (5.0, 10.0, 8.0))
        self.assertEqual(resolved.left_points[-2], (0.0, 0.0, 8.0))
        self.assertEqual(resolved.left_points[-1], (0.0, 0.0, 6.0))

    def test_open_stowed_slats_occupy_end_of_path(self) -> None:
        resolved = sample_tambour().resolved()

        self.assertEqual(len(resolved.slats), 4)
        for left, right, _tangent in resolved.slats:
            self.assertEqual(right[0] - left[0], 5)
            self.assertLessEqual(left[1], 2)

        self.assertGreater(resolved.slats[0][0][2], resolved.slats[-1][0][2])

    def test_closed_slats_occupy_start_of_path(self) -> None:
        resolved = sample_tambour().resolved()

        self.assertEqual(len(resolved.closed_slats), 4)
        self.assertEqual(resolved.slat_thickness, 0.9)
        for left, right, _tangent in resolved.closed_slats:
            self.assertEqual(right[0] - left[0], 5)
            self.assertEqual(left[1], 10)

        self.assertLess(
            resolved.closed_slats[0][0][2], resolved.closed_slats[-1][0][2]
        )

    def test_model_rejects_duplicate_tambour_names(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        with self.assertRaisesRegex(ValueError, "Duplicate tambour names"):
            Model(members, tambours=[sample_tambour(), sample_tambour()]).validate()

    def test_scad_contains_tambour_records_and_assembly_toggle(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )
        scad = Model(members, tambours=[sample_tambour()]).to_scad()

        self.assertIn("tambour_tambour = true;", scad)
        self.assertIn("tambour_door_open = true;", scad)
        self.assertIn('"door", "tambour"', scad)
        self.assertIn(
            "module render_tambour(t, is_open, highlighted = false)",
            scad,
        )
        self.assertIn(
            "function t_slats(t, is_open) = is_open ? t[11] : t[12];", scad
        )


if __name__ == "__main__":
    unittest.main()
