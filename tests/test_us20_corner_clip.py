"""Geometry and export checks for the open-backed measured US20 prototype."""
from dataclasses import replace
import math
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import unittest

from lumber_model.us20_corner import _box, _swap
from lumber_model.us20_corner_clip import ClipSpec, cap, coupon, generate, validation


class ClipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = ClipSpec()
        cls.cover = cap(cls.spec)

    def test_single_solid_and_coupon_options(self):
        for shape in (self.cover, *(coupon(replace(self.spec, clearance=c))
                                   for c in (0.15, 0.25, 0.40))):
            self.assertTrue(shape.is_valid)
            self.assertEqual(len(shape.solids()), 1)

    def test_travel_and_collision_detection(self):
        checks = validation(self.spec, self.cover)
        self.assertEqual(checks['travel_positions_checked'], 9)
        self.assertLess(checks['maximum_intersection_mm3'], 1e-5)
        self.assertAlmostEqual(checks['minimum_normal_overlap_mm'], 10-1/math.sqrt(2))
        self.assertAlmostEqual(checks['minimum_miter_gap_mm'], 2-math.sqrt(2))
        blocked = self.cover+_box(12, 2, -4, 2, 2, 5)
        with self.assertRaisesRegex(ValueError, 'collision'):
            validation(self.spec, blocked)

    def test_open_back_and_covered_seam(self):
        # Rear surfaces away from the small end hooks have no enclosing wall.
        for probe in (_box(20, 18, -10, 1, 1, 1),
                      _box(12, 9, -20, 1, 1, 1)):
            for p in (probe, _swap(probe)):
                common = self.cover & p
                self.assertLess(common.volume if common else 0, 1e-7)
        for shift in (-1, 0, 1):
            for across in (5, 20, 30):
                along = across+2/math.sqrt(2)+shift
                p = _box(along, across, 0.5, 0.05, 0.05, 0.05)
                for probe in (p, _swap(p)):
                    self.assertAlmostEqual((self.cover & probe).volume, probe.volume)

    def test_hook_returns_and_slots(self):
        s = self.spec
        # Rear capture reaches past the rounded-end tangent onto the flat back.
        p = _box(s.leg-s.end_radius-0.4+s.hook_offset, s.leg-s.end_radius-0.4,
                 -s.thickness-s.clearance-0.6, 0.1, 0.1, 0.1)
        for probe in (p, _swap(p)):
            self.assertAlmostEqual((self.cover & probe).volume, probe.volume)
        slot = _box(s.leg-6+s.hook_offset+s.tongue_width/2+0.2, s.leg-6,
                    0.5, 0.1, 0.1, 0.1)
        common = self.cover & slot
        self.assertLess(common.volume if common else 0, 1e-7)

    def test_invalid_dimensions(self):
        for options in (dict(miter_gap=1), dict(clearance=0),
                        dict(tongue_length=30), dict(overlap=2),
                        dict(thickness=7), dict(tongue_thickness=3)):
            with self.subTest(options=options), self.assertRaises(ValueError):
                replace(self.spec, **options)

        for radius in (0, -1, float('nan'), 5):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                replace(self.spec, exterior_transition_radius=radius)

    def test_smaller_outside_radius_only_adds_material(self):
        from build123d import GeomType
        s = self.spec
        previous = cap(replace(s, exterior_transition_radius=
                               s.outside_bend_radius+s.clearance+s.wall))
        missing = previous-self.cover
        self.assertLess(missing.volume if missing else 0, 1e-5)
        self.assertGreater(self.cover.volume, previous.volume+1)
        from lumber_model.us20_corner_clip import _exterior_prism
        # Miter cuts turn the cap's end arcs into ellipses. Inspect the analytic
        # section before that cut, then probe the finished cap on both sides.
        radii = [edge.radius for edge in _exterior_prism(s).edges().filter_by(GeomType.CIRCLE)]
        self.assertTrue(any(abs(radius-1) < 1e-6 for radius in radii))
        self.assertFalse(any(abs(radius-4.25) < 1e-6 for radius in radii))
        center = 1-s.clearance-s.wall
        for radius, filled in ((0.9, True), (1.1, False)):
            y = center-radius/math.sqrt(2)
            p = _box(6, y-0.005, -y-0.005, 0.01, 0.01, 0.01)
            common = self.cover & p
            self.assertAlmostEqual(common.volume if common else 0,
                                   p.volume if filled else 0, places=8)

    def test_tapered_shell_wings_removed_beside_hooks(self):
        # Probe the former rising shell extensions on both free edges,
        # away from the tongues. The flat face immediately before them stays.
        for probe in (_box(50, 38, 0.5, 0.1, 0.1, 0.1),
                      _box(7, -0.6, -38, 0.1, 0.1, 0.1)):
            for sample in (probe, _swap(probe)):
                common = self.cover & sample
                self.assertLess(common.volume if common else 0, 1e-7)
        face = _box(48, 34, 0.5, 0.1, 0.1, 0.1)
        self.assertAlmostEqual((self.cover & face).volume, face.volume)
        sample_coupon = coupon(self.spec)
        probe = _box(0.2, 38, 0.5, 0.1, 0.1, 0.1)
        common = sample_coupon & probe
        self.assertLess(common.volume if common else 0, 1e-7)

    def test_exports_and_print_orientation(self):
        from build123d import import_stl
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            paths = generate(directory)
            self.assertTrue(all(path.stat().st_size for path in paths))
            manifest = json.loads((directory/'manifest.json').read_text())
            self.assertEqual(manifest['design_revision'], 'small-radius-v4')
            self.assertEqual(len(manifest['parts']), 4)
            for record in manifest['parts']:
                mesh = import_stl(directory/f"{record['name']}.stl")
                self.assertTrue(all(abs(v) < 1e-5 for v in mesh.bounding_box().min))
                expected = record['size_mm']
                for actual, target in zip(mesh.bounding_box().size, expected):
                    self.assertAlmostEqual(actual, target, delta=0.06)
            for name in ('assembly', 'rear', 'exterior', 'coupon_section', 'drawing'):
                ET.parse(directory/f'{name}.svg')

    def test_lower_rear_clear_and_claws_above_bottom(self):
        from build123d import Plane, Polygon, extrude
        s = self.spec
        # Limit each butt interface to its own side of the miter; the other
        # incoming trim's front face lies behind this plane near the corner.
        half = extrude(Plane.XY*Polygon((-5, -5), (85, -5), (85, 85),
                                       align=None), amount=90).translate((0, 0, -85))
        forbidden = _box(-5, s.end_radius, -s.leg-5,
                         90, 90, s.end_radius+5) & half
        for region in (forbidden, _swap(forbidden)):
            common = self.cover & region
            self.assertLess(common.volume if common else 0, 1e-7)
        self.assertGreaterEqual(self.cover.bounding_box().min.Z, -s.leg-1e-7)
        # The shallow front claw exists, but stops at the 45-degree radial plane.
        p = _box(s.thickness/2+8, -0.2, -s.leg+2, 0.05, 0.05, 0.05)
        for probe in (p, _swap(p)):
            self.assertAlmostEqual((self.cover & probe).volume, probe.volume)
        lower = self.cover & _box(0, -5, -s.leg, 25, 10, s.end_radius-0.01)
        for vertex in lower.vertices():
            self.assertLessEqual(vertex.Y-vertex.Z, s.leg+1e-6)

    def test_upper_returns_each_engage_their_own_trim(self):
        s = self.spec
        # Inspect the complete rear capture solids, rather than just their centres.
        returns = self.cover & _box(25, 25,
            -s.thickness-s.clearance-s.tongue_thickness,
            45, 45, s.tongue_thickness-0.01)
        self.assertEqual(len(returns.solids()), 2)
        for solid in returns.solids():
            sign = 1 if solid.center().X > solid.center().Y else -1
            for vertex in solid.vertices():
                self.assertGreater(sign*(vertex.X-vertex.Y),
                                   s.miter_gap/math.sqrt(2)+s.travel)
