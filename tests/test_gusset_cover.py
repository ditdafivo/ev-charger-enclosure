"""Fit checks against the actual roof, plate hardware, and shortened plywood."""
import unittest
from dataclasses import replace
import json
from pathlib import Path
import struct
import tempfile

from build import default_build
from lumber_model.gusset import GUSSET_HOLE_CENTERS_IN, GUSSET_SCREW_HEAD_DIAMETER_IN
from lumber_model.gusset_cover import DEFAULT_SPEC, GussetCoverSpec, generate_gusset_covers, covers_for_siding, DECK_BOTTOM, HEIGHT, MM, OVERHANG, PLATE


def overlap(a, b):
    return all(a[0][i] < b[0][i]+b[1][i]-1e-7 and
               b[0][i] < a[0][i]+a[1][i]-1e-7 for i in range(3))


class GussetCoverTests(unittest.TestCase):
    def test_field_trim_only_changes_back_left_rear_edge(self):
        nominal, nominal_front = covers_for_siding(default_build.siding)
        trimmed, front = covers_for_siding(default_build.siding, fabrication=True)
        self.assertEqual(front, nominal_front)
        self.assertEqual(front.boxes, nominal_front.boxes)
        self.assertEqual(trimmed.origin_in, nominal.origin_in)
        self.assertEqual(trimmed.source_strips, nominal.source_strips)
        self.assertEqual(trimmed.y_bounds_mm[0], nominal.y_bounds_mm[0])
        self.assertAlmostEqual(nominal.y_bounds_mm[1]-trimmed.y_bounds_mm[1], 2.325)
        self.assertAlmostEqual(trimmed.y_bounds_mm[1]-trimmed.y_bounds_mm[0], 184.675)
        self.assertAlmostEqual(trimmed.y_bounds_mm[1], trimmed.bearing_bands_mm[-1][1])
        self.assertEqual(trimmed.bearing_bands_mm, nominal.bearing_bands_mm)
        for pos, size in trimmed.base_boxes:
            self.assertGreater(min(size), 0)
            self.assertLessEqual(pos[1]+size[1], trimmed.y_bounds_mm[1]+1e-7)
            self.assertFalse(overlap((pos, size), ((0,0,0),(6*MM,6*MM,0.074*MM))))
            for x, y in GUSSET_HOLE_CENTERS_IN:
                radius = GUSSET_SCREW_HEAD_DIAMETER_IN*MM/2
                self.assertFalse(overlap((pos, size),
                    ((x*MM-radius,y*MM-radius,0.074*MM),
                     (2*radius,2*radius,0.11*MM))))

    def test_cover_fits_frame_margin_and_avoids_hardware_and_plywood(self):
        s = default_build.siding
        covers = covers_for_siding(s)
        self.assertEqual(len(covers), 2)
        self.assertEqual([cover.name for cover in covers],
                         ['gusset_cover_bl', 'gusset_covet_fr'])
        self.assertLess(OVERHANG, 0.25*MM)
        for cover in covers:
            for pos, size in cover.boxes:
                self.assertGreater(min(size), 0)
                self.assertGreaterEqual(pos[2], 0)
                self.assertLessEqual(pos[2]+size[2], HEIGHT+1e-7)
                world = (tuple(cover.origin_in[i]+pos[i]/MM for i in range(3)),
                         tuple(v/MM for v in size))
                for strip in s.roof_strips:
                    if overlap(world, (strip.start, strip.size)):
                        self.assertIn((pos, size), cover.anchor_tabs)
                # Conservative square envelope around each 0.35-inch pan head.
                for x, y in GUSSET_HOLE_CENTERS_IN:
                    radius = GUSSET_SCREW_HEAD_DIAMETER_IN*MM/2
                    self.assertFalse(overlap((pos,size),
                        ((x*MM-radius,y*MM-radius,0.074*MM),
                         (2*radius,2*radius,0.11*MM))))
                self.assertFalse(overlap((pos,size), ((0,0,0),(6*MM,6*MM,0.074*MM))))
            for a, b in cover.bearing_bands_mm:
                self.assertTrue(any(
                    a/MM+cover.origin_in[1] >= board.start[1]-1e-7
                    and b/MM+cover.origin_in[1] <= min(board.start[1]+board.size[1],board.start[1]+s.course_pitch)+1e-7
                    for board in s.board_parts if '_top_' in board.name))
            component = default_build.components[cover.name]
            resolved = component.resolved(default_build.members[component.member])
            self.assertAlmostEqual(resolved.box_min[2]+resolved.box_size[2],s.roof_support_z)
            lower, extent = cover.bounds_mm
            self.assertAlmostEqual(resolved.box_size[0], extent[0]/MM)
            self.assertAlmostEqual(resolved.box_min[1],cover.origin_in[1]+lower[1]/MM)
            self.assertAlmostEqual(resolved.box_size[1],extent[1]/MM)

    def test_only_interrupted_plywood_projections_have_a_deck(self):
        s = default_build.siding
        strips = {p.name: p for p in s.roof_strips}
        for cover in covers_for_siding(s):
            self.assertEqual(len(cover.source_strips),3)
            for (a,b), name in zip(cover.bearing_bands_mm,cover.source_strips):
                strip = strips[name]
                self.assertAlmostEqual(a/MM+cover.origin_in[1],strip.start[1])
                self.assertAlmostEqual(b-a,strip.size[1]*MM)
            # Every piece above the recessed framework must lie entirely in a
            # projected plywood band: no connecting sheet in the open gaps.
            for pos,size in cover.base_boxes:
                if pos[2]+size[2] > DECK_BOTTOM+1e-7:
                    self.assertTrue(any(a-1e-7<=pos[1] and pos[1]+size[1]<=b+1e-7
                                        for a,b in cover.bearing_bands_mm))

    def test_extension_corners_reach_framing_plane(self):
        # The inward edge must not have the former 5.6 mm raised half, even
        # where the nominal framing footprint ends. Small drains stay open.
        for cover in covers_for_siding(default_build.siding):
            edge = (cover.y_bounds_mm[0]+1 if cover.y_bounds_mm[0] < -OVERHANG
                    else cover.y_bounds_mm[1]-1)
            for x in (-OVERHANG+1, 110, PLATE+OVERHANG-1):
                self.assertTrue(any(
                    all(pos[i] <= v <= pos[i]+size[i]
                        for i, v in enumerate((x, edge, 0.1)))
                    for pos, size in cover.boxes), (cover.name, x, edge))

    def test_inward_extension_reaches_interrupted_run_edges(self):
        rear,front = covers_for_siding(default_build.siding)
        self.assertAlmostEqual(rear.y_bounds_mm[0],rear.bearing_bands_mm[0][0])
        self.assertAlmostEqual(rear.y_bounds_mm[1],PLATE+OVERHANG)
        self.assertAlmostEqual(front.y_bounds_mm[0],-OVERHANG)
        self.assertAlmostEqual(front.y_bounds_mm[1],front.bearing_bands_mm[-1][1])
        self.assertAlmostEqual(rear.y_bounds_mm[1]-rear.y_bounds_mm[0],187)
        self.assertAlmostEqual(front.y_bounds_mm[1]-front.y_bounds_mm[0],170.425)

    def test_covers_follow_changed_roof_depth(self):
        from build import build_enclosure
        s = build_enclosure(depth=21).siding
        covers = covers_for_siding(s)
        self.assertNotEqual(covers[0].bearing_bands_mm,
                            covers_for_siding(default_build.siding)[0].bearing_bands_mm)
        for cover in covers:
            self.assertTrue(cover.bearing_bands_mm)
            for name,(a,b) in zip(cover.source_strips,cover.bearing_bands_mm):
                strip = next(p for p in s.roof_strips if p.name==name)
                self.assertAlmostEqual(a/MM+cover.origin_in[1],strip.start[1])
                self.assertAlmostEqual(b/MM+cover.origin_in[1],strip.start[1]+strip.size[1])

    def test_outer_lands_follow_frame_edges_and_survive_rear_trim(self):
        siding = default_build.siding
        for fabrication in (False, True):
            for i, cover in enumerate(covers_for_siding(siding, fabrication=fabrication)):
                lo, size = cover.bounds_mm
                world_lo = [cover.origin_in[k]+lo[k]/MM for k in range(3)]
                world_hi = [world_lo[k]+size[k]/MM for k in range(3)]
                self.assertAlmostEqual(world_lo[0] if i == 0 else world_hi[0],
                                      siding.min_x-11.85/MM if i == 0 else siding.max_x+.375)
                self.assertAlmostEqual(world_hi[1] if i == 0 else world_lo[1],
                                      siding.max_y+.4375 if i == 0 else siding.min_y-.4375)
                self.assertTrue(all(abs(p[2]+s[2]-HEIGHT) < 1e-7 for p,s in cover.trim_lands))

    def test_tabs_reach_frame_and_leave_head_clearance(self):
        s = default_build.siding
        for index, cover in enumerate(covers_for_siding(s)):
            for axis, (pos, size) in enumerate(cover.anchor_tabs):
                self.assertAlmostEqual(size[axis], 25)
                self.assertAlmostEqual(size[1-axis], 25)
                self.assertEqual(pos[2], 0)
                self.assertAlmostEqual(HEIGHT-size[2], 6)
                end = pos[axis]+size[axis]
                start = (PLATE+OVERHANG if index == 0 else -OVERHANG) if axis == 0 else (
                    cover.y_bounds_mm[0] if index == 0 else cover.y_bounds_mm[1])
                self.assertAlmostEqual(pos[axis] if (index == 0) == (axis == 0) else end, start)
                center = [cover.origin_in[k]+(pos[k]+size[k]/2)/MM for k in range(2)]
                self.assertTrue(any(p[0] <= center[0] <= p[0]+z[0]
                                    and p[1] <= center[1] <= p[1]+z[1]
                                    and abs(p[2]+z[2]-cover.origin_in[2]) < 1e-6
                                    for p,z in s.framing))

    def test_independent_field_parameters(self):
        base = covers_for_siding(default_build.siding)
        for name in DEFAULT_SPEC.__dataclass_fields__:
            value = getattr(DEFAULT_SPEC, name)+2
            changed = covers_for_siding(default_build.siding, spec=replace(DEFAULT_SPEC, **{name: value}))
            for old, new in zip(base, changed):
                self.assertEqual(old.base_boxes, new.base_boxes)
                if 'outward' in name:
                    self.assertEqual(old.anchor_tabs, new.anchor_tabs)
                    axis = 0 if '_x_' in name else 1
                    affected = (not name.startswith(('front_right_', 'back_left_')) or
                                name.startswith('front_right_') and new.name == 'gusset_covet_fr' or
                                name.startswith('back_left_') and new.name == 'gusset_cover_bl')
                    expected_delta = 2 if affected else 0
                    self.assertAlmostEqual(new.bounds_mm[1][axis]-old.bounds_mm[1][axis], expected_delta)
                    self.assertAlmostEqual(new.bounds_mm[1][1-axis], old.bounds_mm[1][1-axis])
                else:
                    self.assertEqual(old.trim_lands, new.trim_lands)
                    axis = 0 if '_x_' in name else 1
                    self.assertEqual(old.anchor_tabs[1-axis], new.anchor_tabs[1-axis])
                    self.assertNotEqual(old.anchor_tabs[axis], new.anchor_tabs[axis])
        disabled = covers_for_siding(default_build.siding, spec=replace(DEFAULT_SPEC, inward_x_mm=0, inward_y_mm=0))
        self.assertTrue(all(not c.anchor_tabs for c in disabled))

    def test_invalid_parameters(self):
        for name in DEFAULT_SPEC.__dataclass_fields__:
            for value in (-1, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    replace(DEFAULT_SPEC, **{name: value})
        for name in ('tab_width_x_mm', 'tab_width_y_mm', 'tab_recess_x_mm', 'tab_recess_y_mm'):
            with self.assertRaises(ValueError):
                replace(DEFAULT_SPEC, **{name: 0})
        with self.assertRaises(ValueError):
            GussetCoverSpec(tab_recess_x_mm=HEIGHT)
        with self.assertRaises(ValueError):
            covers_for_siding(default_build.siding, spec=GussetCoverSpec(tab_width_x_mm=100))

    def test_fabrication_exports(self):
        from build123d import import_step
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            generate_gusset_covers(default_build.siding, path)
            manifest = json.loads((path/'manifest.json').read_text())
            self.assertEqual(manifest['parameters']['outward_x_mm'], 6.35)
            import xml.etree.ElementTree as ET
            ET.parse(path/'preview.svg')
            self.assertIn('201.1 × ', (path/'preview.svg').read_text())
            for cover, record in zip(covers_for_siding(default_build.siding, fabrication=True), manifest['parts']):
                solid = import_step(path/f'{cover.name}.step')
                self.assertTrue(solid.is_valid)
                self.assertEqual(len(solid.solids()), 1)
                for actual, expected in zip(solid.bounding_box().size, cover.bounds_mm[1]):
                    self.assertAlmostEqual(actual, expected, places=5)
                data = (path/f'{cover.name}.stl').read_bytes()
                triangles = struct.unpack_from('<I', data, 80)[0]
                vertices = []
                for i in range(triangles):
                    values = struct.unpack_from('<12fH', data, 84+50*i)
                    vertices.extend((values[3:6], values[6:9], values[9:12]))
                self.assertGreater(triangles, 0)
                for axis in range(3):
                    self.assertAlmostEqual(min(v[axis] for v in vertices), 0, places=4)
                self.assertTrue(record['plywood_relief_required'])
                self.assertEqual(len(record['anchor_tabs_mm']), 2)
                scad = (path/f'{cover.name}.scad').read_text()
                self.assertEqual(scad.count('cube('), len(cover.boxes))


if __name__ == '__main__':
    unittest.main()
