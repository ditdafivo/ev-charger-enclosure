from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from build123d import Location

from lumber_model import (
    TambourFabricationConfig,
    generate_tambour_fabrication,
    split_segment_lengths,
    tambour_parts,
)
from lumber_model.tambour_fabrication import (
    make_bend_track,
    make_clearance_coupon,
    make_handle,
    make_joint_collar,
    make_joint_preview,
    make_straight_track,
)


class TambourFabricationTests(unittest.TestCase):
    def test_default_curtain_dimensions_are_independent(self) -> None:
        config = TambourFabricationConfig()

        self.assertAlmostEqual(config.slat_depth, 12.7)
        self.assertAlmostEqual(config.slat_height, 19.05)
        self.assertAlmostEqual(config.slat_pitch, 19.84375)
        self.assertEqual(config.slat_count, 56)
        self.assertAlmostEqual(config.swept_envelope_depth, 38.1)
        self.assertAlmostEqual(config.end_stop_insertion, 12.0)
        self.assertAlmostEqual(config.centerline_length / 25.4, 82.621681, places=5)
        self.assertAlmostEqual(config.flange_extension, 8.2)
        self.assertLessEqual(config.mounting_footprint_width / 25.4, 1.375)
        self.assertGreaterEqual(
            (1.5 - config.mounting_footprint_width / 25.4) / 2,
            1 / 16,
        )

    def test_straight_runs_split_evenly_below_bed_limit(self) -> None:
        lengths = split_segment_lengths(1024.55, 300)

        self.assertEqual(len(lengths), 4)
        self.assertTrue(all(length <= 300 for length in lengths))
        self.assertAlmostEqual(sum(lengths), 1024.55)

    def test_bend_is_valid_exact_radius_sweep_with_tangent_stubs(self) -> None:
        config = TambourFabricationConfig()
        bend = make_bend_track(config)
        size = bend.bounding_box().size

        self.assertTrue(bend.is_valid)
        self.assertEqual(len(bend.solids()), 1)
        expected_plan_extent = (
            config.bend_radius
            + config.bend_stub_length
            + config.channel_outer_width
            + config.flange_extension
        )
        self.assertAlmostEqual(size.X, expected_plan_extent)
        self.assertAlmostEqual(size.Y, expected_plan_extent)

    def test_clearance_coupons_change_channel_width(self) -> None:
        config = TambourFabricationConfig()
        narrow = make_clearance_coupon(0.3, config).bounding_box().size.X
        wide = make_clearance_coupon(0.7, config).bounding_box().size.X

        self.assertAlmostEqual(wide - narrow, 0.8)

    def test_collar_dovetails_align_joint_and_preserve_expansion_gap(self) -> None:
        config = TambourFabricationConfig()
        length = 40.0
        seam = length + config.joint_expansion_gap / 2
        first = make_straight_track(length, config)
        second = Location((0, length + config.joint_expansion_gap, 0)) * (
            make_straight_track(length, config)
        )
        collar = Location(
            (0, seam, config.mounting_flange_thickness)
        ) * make_joint_collar(config)
        preview = make_joint_preview(config)

        self.assertTrue(collar.is_valid)
        self.assertTrue(preview.is_valid)
        self.assertEqual(len(preview.solids()), 4)
        self.assertAlmostEqual(
            second.bounding_box().min.Y - first.bounding_box().max.Y,
            config.joint_expansion_gap,
        )
        self.assertIsNone(collar.intersect(first))
        self.assertIsNone(collar.intersect(second))
        self.assertGreater(
            config.collar_pad_head_width,
            config.collar_pad_neck_width,
        )

    def test_handle_fits_bed_and_swept_depth(self) -> None:
        config = TambourFabricationConfig()
        handle = make_handle(config)
        size = handle.bounding_box().size

        self.assertTrue(handle.is_valid)
        self.assertLessEqual(size.X, 350)
        self.assertAlmostEqual(size.Z, config.handle_projection)
        self.assertLessEqual(
            config.slat_depth + size.Z,
            config.swept_envelope_depth,
        )

    def test_invalid_four_perimeter_wall_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "four nozzle widths"):
            replace(TambourFabricationConfig(), wall_thickness=2.39)

    def test_invalid_collar_wall_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "three nozzle widths"):
            replace(TambourFabricationConfig(), collar_wall_thickness=1.79)

    def test_all_named_parts_are_valid_and_fit_350_mm_bed(self) -> None:
        parts = tambour_parts()
        names = [part.name for part in parts]

        self.assertEqual(len(names), len(set(names)))
        self.assertIn("left_rear_bend", names)
        self.assertIn("right_front_bend", names)
        self.assertIn("left_loading_section", names)
        self.assertIn("joint_collar", names)
        self.assertIn("joint_test_track", names)
        self.assertIn("pull_handle", names)
        self.assertTrue(all(part.shape.is_valid for part in parts))
        self.assertTrue(all(part.fits_bed() for part in parts))
        quantities = {part.name: part.quantity for part in parts}
        self.assertEqual(quantities["pull_handle"], 2)
        self.assertEqual(quantities["joint_collar"], 36)
        self.assertEqual(quantities["joint_test_track"], 2)

    def test_generator_exports_named_step_and_stl(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = generate_tambour_fabrication(
                Path(temporary_directory),
                part_name="joint_collar",
            )

            self.assertEqual(
                {path.name for path in paths},
                {"joint_collar.step", "joint_collar.stl"},
            )
            self.assertTrue(all(path.stat().st_size > 0 for path in paths))

    def test_unknown_part_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(KeyError, "unknown tambour"):
                generate_tambour_fabrication(
                    Path(temporary_directory),
                    part_name="not-a-part",
                )


if __name__ == "__main__":
    unittest.main()
