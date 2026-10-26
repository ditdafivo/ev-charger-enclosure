import math
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
            if '_address_' in part.name:
                self.assertEqual(part.start[1], .25)
            elif '_front_' in part.name:
                expected = build.members['post_fl'].max_on('y') if part.start[2] >= build.members['rail_ft'].max_on('z') else build.members['front_center_rail'].max_on('y')
                self.assertEqual(part.start[1]+.75, expected)
            elif '_left_' in part.name:
                self.assertEqual(part.start[0]+.75, build.members['post_fl'].max_on('x'))
            elif '_right_' in part.name:
                self.assertEqual(part.start[0], build.members['post_fr'].min_on('x'))
            else:
                self.assertEqual(part.start[1], build.members['post_bl'].min_on('y'))
                self.assertGreaterEqual(part.start[2], siding.rear_opening_top_z)
        self.assertFalse(any('_rear_' in p.name for p in siding.infill_parts))
        upper = [p for p in siding.infill_parts if '_address_' in p.name]
        self.assertEqual(len(upper), 2)
        self.assertTrue(all(p.start[2]+p.size[2] == build.members['brace_fl_fr'].min_on('z') for p in upper))
        self.assertNotIn('tambour_ceiling_panel', build.components)

    def test_front_closure_covers_all_bays_for_multiple_sizes(self):
        for dims in ((24, 19.375, 49.625), (30, 26, 55), (36, 30, 55)):
            enclosure = build.build_enclosure(*dims)
            siding, members = enclosure.siding, enclosure.members
            panels = [p for p in siding.infill_parts if '_front_animal_' in p.name and p.start[2] < members['rail_ft'].max_on('z')]
            self.assertEqual(len(panels), 4)
            upper = [p for p in siding.infill_parts if '_front_animal_' in p.name and p.start[2] >= members['rail_ft'].max_on('z')]
            self.assertEqual(len(upper), 1)
            self.assertEqual(upper[0].start[1]+.75, members['post_fl'].max_on('y'))
            rear = members['front_center_rail'].max_on('y')
            left, right = members['post_fl'].max_on('x'), members['post_fr'].min_on('x')
            top = members['rail_ft'].max_on('z')
            for p in panels:
                self.assertEqual(p.start[1]+p.size[1], rear)
                self.assertGreaterEqual(p.start[0], left)
                self.assertLessEqual(p.start[0]+p.size[0], right)
                self.assertLessEqual(p.start[2]+p.size[2], top)
            # Sample the complete closure plane: every point above the scribed
            # ground edge must be occupied by fitted plywood or permanent wood.
            solids = [(p.start, p.size) for p in panels] + list(siding.infill_framing)
            for i in range(41):
                x = left+(right-left)*(i+.5)/41
                for j in range(97):
                    z = top*(j+.5)/97
                    low = panels[0]
                    (a, za), (b, zb) = low.polygon[:2]
                    bottom = low.start[2]+za+(zb-za)*(x-left-a)/(b-a)
                    if z < bottom:
                        continue
                    self.assertTrue(any(all(start[k]-1e-8 <= v <= start[k]+size[k]+1e-8
                        for k, v in enumerate((x, rear-.375, z)))
                        for start, size in solids), (dims, x, z))
            lower = panels[0]
            for along, height in lower.polygon[:2]:
                self.assertAlmostEqual(lower.start[2]+height,
                    siding.ground_z(lower.start[0]+along, rear)+.75)

    def test_front_infill_bore_fits_existing_conduit_adapter(self):
        for enclosure in (build.default_build, build.build_enclosure(36, 30, 55)):
            panels = [p for p in enclosure.siding.infill_parts if '_front_animal_' in p.name and any(b.name == 'power_ev_back_adapter' for b in p.front_bores)]
            self.assertEqual(len(panels), 1)
            panel = panels[0]
            bore, = panel.front_bores
            adapter = enclosure.components['power_ev_back_adapter']
            resolved = adapter.resolved(enclosure.members[adapter.member])
            self.assertAlmostEqual(bore.center_x, resolved.box_min[0]+resolved.box_size[0]/2)
            self.assertAlmostEqual(bore.center_z, resolved.box_min[2]+resolved.box_size[2]/2)
            self.assertAlmostEqual(bore.diameter, resolved.box_size[0])
            self.assertGreater(bore.center_z-bore.diameter/2, panel.start[2])
            self.assertLess(bore.center_z+bore.diameter/2, panel.start[2]+panel.size[2])
            operation = next(r['operation'] for r in enclosure.siding.fabrication_rows() if r['name'] == panel.name)
            self.assertIn('snug bore', operation)

    def test_inner_mesh_closes_ground_gaps_and_updates_purchase_length(self):
        for enclosure in (build.default_build, build.build_enclosure(36, 30, 55)):
            s = enclosure.siding
            inner = {n: (w, a, b, c) for n,w,a,b,c in s.mesh_segments if n.startswith('inner_')}
            self.assertEqual(len(inner), 3)
            _, left, right, rear = inner['inner_front_1']
            self.assertEqual(rear, enclosure.members['front_center_rail'].max_on('y'))
            for name, x in (('inner_left_1', left), ('inner_right_1', right-.025)):
                _, a, b, normal = inner[name]
                self.assertEqual(normal, x)
                self.assertEqual(a, enclosure.members['post_fl'].max_on('y'))
                self.assertEqual(b, enclosure.members['post_bl'].min_on('y'))
                self.assertLess(a, rear)
                self.assertGreater(b, rear)
            for p in s.mesh_parts:
                if '_inner_' not in p.name or '_wire_' not in p.name:
                    continue
                x,y,z = p.start
                self.assertAlmostEqual(z, s.ground_z(x,y)-.25)
                self.assertGreaterEqual(z+p.size[2], s.ground_z(x,y)+.75)
            self.assertAlmostEqual(s.mesh_purchase_length_in,
                sum(b-a+2 for _,_,a,b,_ in s.mesh_segments))
            row = next(r for r in s.bom_rows() if r['name'] == s.name+'_mesh')
            self.assertEqual(row['total_linear_ft'], math.ceil(s.mesh_purchase_length_in/12))

    def test_each_panel_has_toe_screw_candidates_in_adjacent_timber(self):
        siding = build.siding
        entries = siding.infill_toe_entries
        self.assertEqual({e['panel'] for e in entries}, {p.name for p in siding.infill_parts})
        for entry in entries:
            self.assertAlmostEqual(sum(v*v for v in entry['axis']), 1)
            panel = next(p for p in siding.infill_parts if p.name == entry['panel'])
            normal = 1 if panel.plane == 'xz' else 0
            self.assertIn(entry['entry_in'][normal], (panel.start[normal], panel.start[normal]+.75))
