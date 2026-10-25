import unittest

import build
from lumber_model.plywood import plan_plywood


class PlywoodTests(unittest.TestCase):
    def test_shared_layout_contains_all_parts_without_overlap_or_kerf_conflicts(self):
        for enclosure in (build.default_build, build.build_enclosure(36, 30, 55)):
            siding = enclosure.siding
            layout = siding.plywood_layout
            expected = {p.name for p in (*siding.roof_strips, *siding.infill_parts)}
            self.assertEqual({c['name'] for c in layout['cuts']}, expected)
            self.assertEqual(len(layout['cuts']), len(expected))
            for cut in layout['cuts']:
                sheet = layout['sheets'][cut['sheet']-1]
                self.assertGreaterEqual(cut['x_in'], 0)
                self.assertGreaterEqual(cut['y_in'], 0)
                self.assertLessEqual(cut['x_in']+cut['width_in'], sheet['width_in']+1e-8)
                self.assertLessEqual(cut['y_in']+cut['height_in'], sheet['height_in']+1e-8)
                if '_roof_strip_' in cut['name']:
                    self.assertFalse(cut['rotated'])
            for i, a in enumerate(layout['cuts']):
                for b in layout['cuts'][i+1:]:
                    if a['sheet'] != b['sheet']:
                        continue
                    gap = layout['kerf_in']-1e-8
                    self.assertTrue(a['x_in']+a['width_in']+gap <= b['x_in'] or
                                    b['x_in']+b['width_in']+gap <= a['x_in'] or
                                    a['y_in']+a['height_in']+gap <= b['y_in'] or
                                    b['y_in']+b['height_in']+gap <= a['y_in'])
        self.assertEqual(build.siding.plywood_layout['purchases'], {'4x8':1, '2x4':0})

    def test_small_supplement_is_chosen_when_it_fits(self):
        plan = plan_plywood([('roof',96,40,False), ('infill',48,20,True)], .125)
        self.assertEqual(plan['purchases'], {'4x8':1, '2x4':1})
        plan = plan_plywood([('roof',96,40,False), ('infill',70,30,True)], .125)
        self.assertEqual(plan['purchases'], {'4x8':2, '2x4':0})

    def test_wall_infill_preserves_interior_and_rear_opening(self):
        siding = build.siding
        for part in siding.infill_parts:
            self.assertEqual(part.material, 'PT_exterior_plywood_3_4')
            normal_axis = 1 if part.plane == 'xz' else 0
            self.assertEqual(part.size[normal_axis], .75)
            if '_front_' in part.name:
                self.assertEqual(part.start[1], .25)
            elif '_left_' in part.name:
                self.assertEqual(part.start[0], .25)
            elif '_right_' in part.name:
                self.assertEqual(part.start[0]+.75, siding.max_x-.25)
            else:
                self.assertGreaterEqual(part.start[2], siding.rear_opening_top_z)
        upper = [p for p in siding.infill_parts if '_address_' in p.name]
        self.assertEqual(len(upper), 2)
        self.assertTrue(all(p.start[2]+p.size[2] == build.members['brace_fl_fr'].min_on('z') for p in upper))
        self.assertNotIn('tambour_ceiling_panel', build.components)

    def test_each_panel_has_toe_screw_candidates_in_adjacent_timber(self):
        siding = build.siding
        entries = siding.infill_toe_entries
        self.assertEqual({e['panel'] for e in entries}, {p.name for p in siding.infill_parts})
        for entry in entries:
            self.assertAlmostEqual(sum(v*v for v in entry['axis']), 1)
            panel = next(p for p in siding.infill_parts if p.name == entry['panel'])
            normal = 1 if panel.plane == 'xz' else 0
            self.assertIn(entry['entry_in'][normal], (panel.start[normal], panel.start[normal]+.75))
