"""Slip-socket enclosure, insertion, travel and fabrication checks."""
from dataclasses import replace
import json
import itertools
import math
from pathlib import Path
import tempfile
import unittest

from lumber_model.us20_corner import (
    CornerSpec, _box, _profile_prism, _swap, cap, coupon, generate,
    insertion_sweep, trim_fixture, validation,
)


class US20CornerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = CornerSpec()
        cls.cover = cap(cls.spec)

    def test_valid_single_solids_and_mirrored_fixtures(self):
        for shape in (self.cover, trim_fixture(),
                      *(coupon(replace(self.spec, clearance=c)) for c in (0.5, 0.75, 1.0))):
            self.assertTrue(shape.is_valid)
            self.assertEqual(len(shape.solids()), 1)
        mirrored = _swap(trim_fixture())
        bounds = mirrored.bounding_box()
        self.assertAlmostEqual(bounds.max.Y, 95)
        self.assertAlmostEqual(bounds.max.X, 42)

    def test_independent_travel_and_continuous_insertion_paths(self):
        checks = validation(self.spec, self.cover)
        self.assertEqual(checks['travel_positions_checked'], 9)
        self.assertEqual(checks['insertion_sweeps_checked'], 2)
        self.assertEqual(checks['insertion_neighbor_positions_checked'], 6)
        self.assertLess(checks['maximum_intersection_mm3'], 1e-5)
        self.assertGreater(checks['minimum_miter_gap_mm'], 1.4)
        self.assertGreaterEqual(checks['minimum_full_profile_engagement_mm'], 17)
        self.assertAlmostEqual(checks['required_space_behind_trim_mm'], 2.75)
        self.assertAlmostEqual(checks['minimum_full_profile_engagement_mm'], 18.5573593)
        # The sweep includes each intermediate insertion position, not just
        # its endpoints. A blocking web must be detected by the validator.
        for shift in (-3.2, 0, 20, 40, 70.75):
            stock = trim_fixture().translate((shift, 0, 0))
            self.assertAlmostEqual((stock & insertion_sweep(self.spec)).volume,
                                   stock.volume, places=5)
        blocked = self.cover+_box(59, 19, -3, 3, 3, 6)
        with self.assertRaisesRegex(ValueError, 'collision'):
            validation(self.spec, blocked)

    def test_both_sockets_wrap_every_profile_face_and_edge(self):
        s = self.spec
        # Independent samples on all six surfaces of an L-shaped cross section:
        # top, underside, outer/inner vertical faces, and the two free edges.
        locations = ((20, s.clearance+s.wall/2),
                     (20, -s.thickness-s.clearance-s.wall/2),
                     (-s.clearance-s.wall/2, -20),
                     (s.thickness+s.clearance+s.wall/2, -20),
                     (s.leg+s.clearance+s.wall/2, -s.thickness/2),
                     (s.thickness/2, -s.leg-s.clearance-s.wall/2))
        for y, z in locations:
            probe = _box(60, y-0.05, z-0.05, 0.1, 0.1, 0.1)
            for sample in (probe, _swap(probe)):
                self.assertAlmostEqual((self.cover & sample).volume,
                                       sample.volume, places=6)
            coupon_probe = probe.translate((-50, 0, 0))
            self.assertAlmostEqual((coupon(s) & coupon_probe).volume,
                                   coupon_probe.volume, places=6)
        # Near-full clearance envelopes must pass through both mouths without
        # hitting ribs, pads, mouth closures or stops.
        envelope = _profile_prism(s, s.clearance-0.01, 48, 25)
        for passage in (envelope, _swap(envelope)):
            common = self.cover & passage
            self.assertEqual(len(common.solids()) if common else 0, 0)
            self.assertLess(common.volume if common else 0, 1e-6)
        sample = coupon(s)
        self.assertAlmostEqual(sample.bounding_box().size.X, 20)

    def test_miter_cut_edges_stay_covered_at_travel_limits(self):
        s = self.spec
        for shift in (-s.travel, 0, s.travel):
            for across in (0, s.leg/2, s.leg):
                along = across+s.miter_gap/math.sqrt(2)+shift
                probe = _box(along-0.05, across-0.05, s.clearance+0.2,
                             0.1, 0.1, 0.1)
                for sample in (probe, _swap(probe)):
                    self.assertAlmostEqual((self.cover & sample).volume,
                                           sample.volume, places=6)

    def test_estimated_profile_range_fits_generous_cavity(self):
        # All valid endpoint combinations of the photographic estimates. The
        # conservative reference uses the least rounded convex corners and the
        # largest concave bend, rather than assuming every larger radius fits.
        cavity = _profile_prism(self.spec, self.spec.clearance, 0, 20)
        count = 0
        for leg, thickness, outside, inside, end in itertools.product(
                (40, 42), (8, 10), (2, 4), (2, 4), (4, 5)):
            if 2*end > thickness:
                continue
            actual = replace(self.spec, leg=leg, thickness=thickness,
                             outside_bend_radius=outside,
                             inside_bend_radius=inside, end_radius=end)
            with self.subTest(profile=actual):
                stock = _profile_prism(actual, 0, 0, 20)
                self.assertTrue(stock.is_valid)
                difference = stock-cavity
                self.assertLess(difference.volume if difference else 0, 1e-5)
            count += 1
        self.assertEqual(count, 24)

    def test_rounded_walls_have_clearance_and_two_mm_radial_thickness(self):
        # Probe curved walls, not just the six straight profile surfaces.
        # Centres in local Y/-Z remain fixed under both analytic offsets.
        s = self.spec
        for cy, cv, reference_radius, convex in (
                (s.outside_bend_radius, s.outside_bend_radius,
                 s.outside_bend_radius, True),
                (s.leg-s.end_radius, s.end_radius, s.end_radius, True),
                (s.thickness+s.inside_bend_radius,
                 s.thickness+s.inside_bend_radius, s.inside_bend_radius, False)):
            cavity_r = reference_radius+(s.clearance if convex else -s.clearance)
            outer_r = reference_radius+(s.outer if convex else -s.outer)
            sign = 1 if cy == s.leg-s.end_radius else -1
            for radius, material in (((cavity_r+outer_r)/2, True),
                                      (cavity_r+(-0.1 if convex else 0.1), False),
                                      (outer_r+(0.1 if convex else -0.1), False)):
                delta = radius/math.sqrt(2)
                probe = _box(60, cy+sign*delta-0.01, -cv+delta-0.01,
                             0.02, 0.02, 0.02)
                common = self.cover & probe
                volume = common.volume if common else 0
                self.assertAlmostEqual(volume, probe.volume if material else 0,
                                       places=7)
            self.assertAlmostEqual(abs(outer_r-cavity_r), 2)

    def test_rounded_sweeps_meet_without_exterior_corner_bulges(self):
        # The neighboring sweep must not fill the rounded-away upper/lower
        # edges on an exterior face. Overlapping uncut prisms would do so.
        for z in (0, -41):
            probe = _box(8, -self.spec.outer+0.025, z, 0.1, 0.05, 0.05)
            for sample in (probe, _swap(probe)):
                common = self.cover & sample
                self.assertLess(common.volume if common else 0, 1e-7)

    def test_invalid_dimensions_fail_early(self):
        for options in (dict(clearance=0), dict(thickness=41), dict(miter_gap=1),
                        dict(length=60), dict(outside_bend_radius=11),
                        dict(inside_bend_radius=30), dict(end_radius=6),
                        dict(travel=float('nan'))):
            with self.subTest(options=options), self.assertRaises(ValueError):
                replace(self.spec, **options)

    def test_exports_include_printable_parts_and_true_cad_views(self):
        from build123d import import_stl
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            paths = generate(directory)
            self.assertTrue(all(path.stat().st_size > 0 for path in paths))
            manifest = json.loads((directory/'manifest.json').read_text())
            self.assertEqual(manifest['units'], 'mm')
            self.assertEqual(manifest['design_revision'], 'rounded-slip-socket-v3')
            self.assertIn('Conservative estimates', manifest['dimension_basis'])
            self.assertEqual(manifest['dimensions']['thickness'], 10)
            self.assertEqual(len(manifest['parts']), 6)
            for record in manifest['parts']:
                shape = import_stl(directory/f"{record['name']}.stl")
                minimum = shape.bounding_box().min
                self.assertTrue(all(abs(v) < 1e-4 for v in minimum))
                if record['name'].startswith('fit_coupon_'):
                    self.assertIn(record['clearance_per_face_mm'], (0.5, 0.75, 1.0))
            self.assertTrue((directory/'socket_mouth.svg').exists())


if __name__ == '__main__':
    unittest.main()
