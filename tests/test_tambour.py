from __future__ import annotations

import unittest

from lumber_model import (
    AbsoluteCoord,
    LumberCollection,
    Model,
    TambourBend,
    TambourDoor,
    TambourInstalledDetails,
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
        self.assertEqual(resolved.slat_track_offset, 0)
        for left, right, _tangent in resolved.closed_slats:
            self.assertEqual(right[0] - left[0], 5)
            self.assertEqual(left[1], 10)

        self.assertLess(
            resolved.closed_slats[0][0][2], resolved.closed_slats[-1][0][2]
        )

    def test_track_offset_moves_slat_center_outward_from_track(self) -> None:
        door = sample_tambour()
        offset_door = TambourDoor(
            **{
                **door.__dict__,
                "slat_depth": 1.5,
                "slat_track_offset": 0.375,
            }
        )
        resolved = offset_door.resolved()

        self.assertEqual(resolved.slat_track_offset, 0.375)
        self.assertAlmostEqual(resolved.closed_slats[0][0][1], 10.375)
        self.assertEqual(resolved.left_points[0][1], 10)

    def test_track_offset_must_remain_within_envelope(self) -> None:
        door = sample_tambour()
        with self.assertRaisesRegex(ValueError, "must remain within the envelope"):
            TambourDoor(**{**door.__dict__, "slat_track_offset": 0.5})

    def test_envelope_can_exceed_rendered_slat_depth(self) -> None:
        door = sample_tambour()
        resolved = TambourDoor(
            **{
                **door.__dict__,
                "slat_depth": 0.5,
                "slat_envelope_depth": 1.5,
                "slat_track_offset": 0.375,
            }
        ).resolved()

        self.assertEqual(resolved.slat_depth, 0.5)
        self.assertEqual(resolved.slat_envelope_depth, 1.5)
        self.assertEqual(resolved.slat_track_offset, 0.375)

    def test_envelope_cannot_be_smaller_than_rendered_slat(self) -> None:
        door = sample_tambour()
        with self.assertRaisesRegex(ValueError, "cannot be less than slat_depth"):
            TambourDoor(
                **{
                    **door.__dict__,
                    "slat_depth": 1.0,
                    "slat_envelope_depth": 0.75,
                }
            )

    def test_envelope_must_be_positive(self) -> None:
        door = sample_tambour()
        with self.assertRaisesRegex(ValueError, "must be finite and positive"):
            TambourDoor(**{**door.__dict__, "slat_envelope_depth": 0})

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
            "function t_slats(t, is_open) = is_open ? t[12] : t[13];", scad
        )

    def test_installed_details_are_resolved_and_rendered(self) -> None:
        door = sample_tambour()
        detailed = TambourDoor(
            **{
                **door.__dict__,
                "installed_details": TambourInstalledDetails(
                    channel_internal_width=0.54,
                    channel_wall_thickness=0.095,
                    mounting_flange_thickness=0.19,
                    flange_extension=0.39,
                    slat_end_engagement=0.47,
                    segment_seams=(2.0, 8.0),
                    joint_gap=0.024,
                    loading_section_length=2.0,
                    end_stop_length=0.5,
                    pull_slat_indices=(0, 2),
                    handle_width=4.0,
                ),
            }
        )
        resolved = detailed.resolved()

        self.assertEqual(len(resolved.installed_seams), 2)
        self.assertEqual(resolved.installed_seams[0][0], (0.0, 10.0, 2.0))
        scad = Model([], tambours=[detailed]).to_scad()
        self.assertIn("module render_tambour_channel", scad)
        self.assertIn("module render_tambour_slat_details", scad)
        self.assertIn("function t_installed(t) = len(t) > 14 ? t[14] : [];", scad)
        self.assertIn(
            "v_add(center, v_scale(opening_dir, flange_thickness / 2))",
            scad,
        )
        self.assertNotIn(
            "v_add(center, v_scale(opening_dir, -flange_thickness / 2))",
            scad,
        )

    def test_track_samples_cover_facets_and_reject_invalid_subdivisions(self) -> None:
        resolved = sample_tambour().resolved()
        samples = resolved.track_samples(subdivisions=2)

        self.assertEqual(samples[0][0], resolved.left_points[0])
        self.assertEqual(samples[-1][0], resolved.left_points[-1])
        self.assertEqual(
            len(samples),
            3 * (len(resolved.left_points) - 1),
        )
        with self.assertRaisesRegex(ValueError, "at least one"):
            resolved.track_samples(subdivisions=0)

    def test_inward_hardware_projection_covers_webbing(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be less than webbing"):
            TambourInstalledDetails(
                channel_internal_width=0.54,
                channel_wall_thickness=0.095,
                mounting_flange_thickness=0.19,
                flange_extension=0.39,
                slat_end_engagement=0.47,
                webbing_thickness=0.1,
                inward_hardware_projection=0.09,
            )


if __name__ == "__main__":
    unittest.main()
