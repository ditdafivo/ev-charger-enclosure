from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from lumber_model import (
    AbsoluteCoord,
    CompositeSiding,
    FrontSidingOpening,
    LumberCollection,
    Model,
    RightSidingOpening,
    minimum_stock_board_count,
)


def sample_siding(
    name: str = "shell",
    stock_length: float = 192,
    front_openings: tuple[FrontSidingOpening, ...] = (),
    right_openings: tuple[RightSidingOpening, ...] = (),
) -> CompositeSiding:
    return CompositeSiding(
        name,
        min_x=0,
        max_x=27.5,
        min_y=0,
        max_y=23.5,
        frame_top_z=47,
        bottom_z=2,
        rear_opening_min_x=3.5,
        rear_opening_max_x=24,
        rear_opening_top_z=45,
        front_openings=front_openings,
        right_openings=right_openings,
        stock_length=stock_length,
    )


def sample_model(*sidings: CompositeSiding) -> Model:
    members = LumberCollection()
    members.add(
        "post",
        assembly="frame",
        type="4x4",
        axis="z",
        start=AbsoluteCoord(0, 0, 0),
        length=47,
    )
    return Model(members, sidings=sidings)


class CompositeSidingTests(unittest.TestCase):
    def test_top_boards_fill_depth_with_ripped_final_board(self) -> None:
        siding = sample_siding()
        top = [
            part for part in siding.board_parts if part.name.startswith("shell_top_")
        ]

        self.assertEqual(len(top), 5)
        self.assertEqual([part.size[1] for part in top], [5.5] * 4 + [0.75])
        self.assertEqual(top[-1].start, (0, 22.75, 47))
        self.assertEqual(top[-1].size, (27.5, 0.75, 1.0))

    def test_wall_courses_descend_to_uniform_two_inch_datum(self) -> None:
        siding = sample_siding()
        front = [part for part in siding.board_parts if "_front_" in part.name]
        left = [
            part for part in siding.board_parts if part.name.startswith("shell_left_")
        ]

        self.assertEqual(len(front), 9)
        self.assertEqual(front[-1].start, (0, -1.0, 2.0))
        self.assertEqual(front[-1].size, (27.5, 1.0, 0.5))
        self.assertEqual(left[-1].size, (1.0, 25.5, 0.5))

    def test_rear_wings_end_at_tambour_tracks(self) -> None:
        siding = sample_siding()
        rear_left = next(
            part for part in siding.board_parts if part.name == "shell_rear_top_left"
        )
        rear_right = next(
            part for part in siding.board_parts if part.name == "shell_rear_top_right"
        )
        header = next(
            part for part in siding.board_parts if part.name == "shell_rear_top_header"
        )

        self.assertEqual(rear_left.start, (0, 23.5, 42.5))
        self.assertEqual(rear_left.size, (3.5, 1.0, 5.5))
        self.assertEqual(rear_right.start, (24, 23.5, 42.5))
        self.assertEqual(rear_right.size, (3.5, 1.0, 5.5))
        self.assertEqual(header.start, (3.5, 23.5, 45))
        self.assertEqual(header.size, (20.5, 1.0, 3))
        self.assertEqual(rear_left.cut_length, 27.5)
        self.assertIsNone(header.cut_length)
        self.assertIsNone(rear_right.cut_length)

    def test_front_opening_splits_rendered_parts_without_adding_boards(self) -> None:
        opening = FrontSidingOpening(
            "fixture",
            min_x=11.55,
            max_x=15.95,
            bottom_z=37.8,
            top_z=42.2,
        )
        baseline = sample_siding()
        siding = sample_siding(front_openings=(opening,))

        self.assertEqual(siding.cut_lengths, baseline.cut_lengths)
        self.assertGreater(len(siding.board_parts), len(baseline.board_parts))
        for part in siding.board_parts:
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

    def test_right_opening_splits_rendered_parts_without_adding_boards(self) -> None:
        opening = RightSidingOpening(
            "outlet",
            min_y=17.1,
            max_y=19.9,
            bottom_z=15.15,
            top_z=20.85,
        )
        baseline = sample_siding()
        siding = sample_siding(right_openings=(opening,))

        self.assertEqual(siding.cut_lengths, baseline.cut_lengths)
        self.assertGreater(len(siding.board_parts), len(baseline.board_parts))
        for part in siding.board_parts:
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
            self.assertFalse(overlaps_y and overlaps_z, part.name)

    def test_six_vertical_angles_and_opening_angle_are_rendered(self) -> None:
        siding = sample_siding()

        self.assertEqual(len(siding.angle_parts), 14)
        for part in siding.angle_parts:
            self.assertEqual(part.material, "black_aluminum_angle")
            self.assertEqual(part.color, (0.03, 0.03, 0.03, 1.0))

        vertical_parts = [
            part
            for part in siding.angle_parts
            if "angle_tambour_header" not in part.name
        ]
        self.assertEqual(len(vertical_parts), 12)
        for part in vertical_parts:
            self.assertEqual(part.start[2], 2)
            self.assertEqual(part.size[2], 46)

        tambour_left = next(
            part
            for part in siding.angle_parts
            if part.name == "shell_angle_tambour_left_a"
        )
        self.assertEqual(tambour_left.start, (2.25, 24.5, 2))
        self.assertEqual(tambour_left.size, (1.25, 0.125, 46))

        header_bottom = next(
            part
            for part in siding.angle_parts
            if part.name == "shell_angle_tambour_header_bottom"
        )
        self.assertEqual(header_bottom.start, (3.5, 23.25, 44.875))
        self.assertEqual(header_bottom.size, (20.5, 1.25, 0.125))

    def test_bom_reports_linear_feet_and_cut_aware_stock_quantity(self) -> None:
        decking, angles, opening_angle = sample_siding().bom_rows()

        self.assertEqual(decking["qty"], 49)
        self.assertEqual(decking["length_in"], 927.5)
        self.assertAlmostEqual(decking["total_linear_ft"], 77.2917)
        self.assertEqual(decking["stock_length_ft"], 16)
        self.assertEqual(decking["stock_board_qty"], 5)
        self.assertEqual(angles["qty"], 6)
        self.assertEqual(angles["length_in"], 46)
        self.assertEqual(opening_angle["qty"], 1)
        self.assertEqual(opening_angle["length_in"], 20.5)

    def test_exact_stock_packing_reuses_offcuts(self) -> None:
        self.assertEqual(minimum_stock_board_count((6, 4, 6, 4), 10), 2)

    def test_exact_stock_packing_can_exceed_linear_feet_ceiling(self) -> None:
        self.assertEqual(minimum_stock_board_count((6, 6, 6, 2), 10), 3)

    def test_stock_packing_rejects_oversized_cut(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds stock length"):
            sample_siding(stock_length=24).bom_rows()

    def test_model_rejects_duplicate_siding_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate siding names"):
            sample_model(sample_siding(), sample_siding()).validate()

    def test_scad_contains_visibility_parameter_and_siding_parts(self) -> None:
        scad = sample_model(sample_siding()).to_scad()

        self.assertIn("siding = true;", scad)
        self.assertIn('"shell_top_5", "composite_decking"', scad)
        self.assertIn('"shell_angle_tambour_right_b"', scad)
        self.assertIn("if (siding)", scad)
        self.assertIn("module render_siding_part(s, highlighted = false)", scad)

    def test_bom_serializes_siding_rows_to_csv_and_json(self) -> None:
        model = sample_model(sample_siding())
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "bom.csv"
            json_path = Path(tmpdir) / "bom.json"
            model.write_bom_csv(csv_path)
            model.write_bom_json(json_path)

            with csv_path.open(newline="") as file:
                csv_rows = list(csv.DictReader(file))
            json_rows = json.loads(json_path.read_text())

        decking_csv = next(
            row for row in csv_rows if row["name"] == "shell_composite_decking"
        )
        decking_json = next(
            row for row in json_rows if row["name"] == "shell_composite_decking"
        )
        self.assertEqual(decking_csv["stock_board_qty"], "5")
        self.assertEqual(decking_json["stock_board_qty"], 5)

    def test_rejects_rear_opening_outside_envelope(self) -> None:
        with self.assertRaisesRegex(ValueError, "rear opening"):
            CompositeSiding(
                "bad",
                min_x=0,
                max_x=10,
                min_y=0,
                max_y=10,
                frame_top_z=20,
                bottom_z=2,
                rear_opening_min_x=0,
                rear_opening_max_x=8,
                rear_opening_top_z=18,
            )

    def test_rejects_front_opening_outside_wall(self) -> None:
        with self.assertRaisesRegex(ValueError, "must lie within the front wall"):
            sample_siding(
                front_openings=(
                    FrontSidingOpening(
                        "outside",
                        min_x=-1,
                        max_x=2,
                        bottom_z=10,
                        top_z=12,
                    ),
                )
            )

    def test_rejects_overlapping_front_openings(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap"):
            sample_siding(
                front_openings=(
                    FrontSidingOpening("one", 5, 10, 10, 15),
                    FrontSidingOpening("two", 9, 12, 14, 18),
                )
            )

    def test_rejects_right_opening_outside_wall(self) -> None:
        with self.assertRaisesRegex(ValueError, "must lie within the right wall"):
            sample_siding(
                right_openings=(
                    RightSidingOpening("outside", -1, 2, 10, 12),
                )
            )

    def test_rejects_overlapping_right_openings(self) -> None:
        with self.assertRaisesRegex(ValueError, "overlap"):
            sample_siding(
                right_openings=(
                    RightSidingOpening("one", 5, 10, 10, 15),
                    RightSidingOpening("two", 9, 12, 14, 18),
                )
            )


if __name__ == "__main__":
    unittest.main()
