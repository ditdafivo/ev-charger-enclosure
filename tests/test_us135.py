from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
import json
from itertools import combinations
from pathlib import Path
import tempfile
import unittest

import build
from lumber_model.us135 import US135Siding, US135_PREVIEW_CLEARANCE


def rebate_boxes(part):
    """Conservative solid boxes: omit polygon/bores, subtract actual rebates."""
    boxes = [(part.start, tuple(a+b for a,b in zip(part.start,part.size)))]
    for start,size in part.rebates:
        end = tuple(a+b for a,b in zip(start,size))
        remaining = []
        for lo,hi in boxes:
            cut_lo = tuple(max(a,b) for a,b in zip(lo,start))
            cut_hi = tuple(min(a,b) for a,b in zip(hi,end))
            if any(a>=b for a,b in zip(cut_lo,cut_hi)):
                remaining.append((lo,hi))
                continue
            lo,hi = list(lo),list(hi)
            for axis in range(3):
                if lo[axis]<cut_lo[axis]:
                    edge = hi.copy(); edge[axis] = cut_lo[axis]
                    remaining.append((tuple(lo),tuple(edge)))
                    lo[axis] = cut_lo[axis]
                if hi[axis]>cut_hi[axis]:
                    edge = lo.copy(); edge[axis] = cut_hi[axis]
                    remaining.append((tuple(edge),tuple(hi)))
                    hi[axis] = cut_hi[axis]
        boxes = remaining
    return boxes


class US135Tests(unittest.TestCase):
    def test_lapped_boards_have_preview_clearance(self):
        for dims in ((24,19.375,49.625),(30,26,55),(36,30,55)):
            siding = build.build_enclosure(*dims).siding
            for wall in ('front','rear','left','right','top'):
                boards = [p for p in siding.board_parts if f'_{wall}_' in p.name]
                joints = 0
                for a,b in combinations(boards,2):
                    if not all(min(a.start[k]+a.size[k],b.start[k]+b.size[k])
                               > max(a.start[k],b.start[k])+1e-8 for k in range(3)):
                        continue
                    joints += 1
                    for (alo,ahi),(blo,bhi) in ((x,y) for x in rebate_boxes(a) for y in rebate_boxes(b)):
                        # A shared face also fails: distinct highlighted boards
                        # need air between their mating faces in the preview.
                        separation = max(max(alo[k]-bhi[k],blo[k]-ahi[k]) for k in range(3))
                        self.assertGreaterEqual(separation,US135_PREVIEW_CLEARANCE/2-1e-8,
                                                (a.name,b.name,alo,ahi,blo,bhi))
                self.assertGreater(joints,0,wall)

    def test_full_top_course_and_scribed_bottom(self):
        s=build.siding
        self.assertIsInstance(s,US135Siding)
        self.assertAlmostEqual(s.board_width,142/25.4)
        self.assertEqual(s.board_thickness,0.5)
        for wall in ('front','left','right'):
            cuts=[c for c in s.cuts if c.wall==wall]
            self.assertAlmostEqual(cuts[0].top-cuts[0].bottom,s.board_width)
            self.assertEqual([c.course for c in cuts],list(range(1,len(cuts)+1)))
            self.assertTrue(all(c.top-c.bottom==cuts[0].top-cuts[0].bottom or
                                abs((c.top-c.bottom)-s.board_width)<1e-8 for c in cuts))
            for along,z in cuts[-1].bottom_edge:
                self.assertAlmostEqual(z-s.ground_z(*s.xy(wall,along)),0.75)
        # Physical profiles overlap; pitch is not overall width plus a gap.
        self.assertAlmostEqual(s.courses[0][0]-s.courses[1][0],s.course_pitch)
        self.assertLess(s.course_pitch,s.board_width)
        self.assertTrue(all(p.rebates for p in s.board_parts))

    def test_openings_and_one_physical_notched_rear_board(self):
        s=build.siding
        rear=next(c for c in s.cuts if c.notched)
        fragments=[p for p in s.board_parts if p.name.startswith(rear.name+'_piece_')]
        self.assertEqual(len(fragments),3)
        self.assertEqual(sum(p.cut_length is not None for p in fragments),1)
        self.assertEqual(sum(a.locked for a in s.attachments if a.board==rear.name),1)
        for part in s.board_parts:
            if '_right_' not in part.name: continue
            for opening in s.right_openings:
                self.assertFalse(part.start[1]<opening.max_y and part.start[1]+part.size[1]>opening.min_y
                    and part.start[2]<opening.top_z and part.start[2]+part.size[2]>opening.bottom_z)
        self.assertEqual(sum(bool(p.front_bores) for p in s.board_parts),1)

    def test_attachments_backing_and_spans_for_multiple_envelopes(self):
        for dims in ((24,19.375,49.625),(30,26,55),(36,30,55)):
            s=build.build_enclosure(*dims).siding
            groups=defaultdict(list)
            for a in s.attachments:
                groups[a.board].append(a)
                if a.wall=='roof':
                    self.assertTrue(s._roof_supported(a.along,a.elevation),a)
                else:
                    self.assertTrue(s._surface_supported(a.wall,a.along,a.elevation),a)
            for name,attachments in groups.items():
                self.assertEqual(sum(a.locked for a in attachments),1,name)
                at_edge=sorted(set(a.along for a in attachments))
                maximum=12 if attachments[0].wall=='roof' else 16
                self.assertTrue(all(b-a<=maximum+1e-8 for a,b in zip(at_edge,at_edge[1:])),name)
            for p in s.backing_parts:
                if p.material=='PT_roof_shim': continue
                # Added wood must fit around existing wood, not occupy it.
                for loc,size in s.framing:
                    self.assertFalse(all(p.start[k]<loc[k]+size[k]-1e-7 and
                        p.start[k]+p.size[k]>loc[k]+1e-7 for k in range(3)),p.name)

    def test_outlet_backing_and_screws_are_local_to_notched_courses(self):
        for dims in ((24,19.375,49.625),(30,26,55),(36,30,55)):
            s=build.build_enclosure(*dims).siding
            opening=s.right_openings[0]
            affected=[c for c in s.cuts if c.wall=='right'
                      and c.bottom<opening.top_z and c.top>opening.bottom_z]
            bottom=min(c.bottom for c in affected)
            top=max(c.top for c in affected)
            backing=[p for p in s.backing_parts if 'backing_right_opening_' in p.name]
            self.assertTrue(backing)
            for p in backing:
                self.assertGreaterEqual(p.start[2],bottom)
                self.assertLessEqual(p.start[2]+p.size[2],top)
            for station in (opening.min_y-0.5,opening.max_y+0.5):
                screws=[a for a in s.attachments if a.wall=='right' and a.along==station]
                self.assertTrue(screws)
                self.assertTrue(all(a.board in {c.name for c in affected} for a in screws))
                for cut in affected:
                    self.assertTrue(any(a.board==cut.name for a in screws),cut.name)

    def test_roof_strips_drainage_clearances_and_independent_fasteners(self):
        for dims in ((24,19.375,49.625),(30,26,55),(36,30,55)):
            enclosure=build.build_enclosure(*dims); s=enclosure.siding
            self.assertFalse(any("backing_roof" in p.name or "shim" in p.name for p in s.backing_parts))
            for board in (p for p in s.board_parts if "_top_" in p.name):
                course=board.name.rsplit('_',1)[1]
                strips=[p for p in s.roof_strips if p.name.startswith(f"{s.name}_roof_strip_{course}_")]
                self.assertIn(len(strips),(1,2))
                if len(strips)==2:
                    self.assertGreater(strips[1].start[1]-strips[0].start[1]-strips[0].size[1],0)
                for strip in strips:
                    self.assertEqual(strip.size[2],0.75)
                    # The entire strip bears beneath solid profile, not a groove lip.
                    self.assertGreaterEqual(strip.start[1],board.start[1]+s.board_width-s.course_pitch-1e-8)
                    self.assertLessEqual(strip.start[1]+strip.size[1],min(board.start[1]+board.size[1],board.start[1]+s.course_pitch)+1e-8)
                    for loc,size in s.roof_gussets:
                        self.assertFalse(all(strip.start[k]<loc[k]+size[k]+0.125-1e-8 and
                            strip.start[k]+strip.size[k]>loc[k]-0.125+1e-8 for k in (0,1)))
                    anchors=[a for a in s.roof_strip_anchors if a.board==strip.name]
                    self.assertEqual(len(anchors),2)
                    self.assertLess(anchors[0].along,anchors[1].along)
                    for a in anchors:
                        self.assertTrue(s._base_supported(a.along,a.elevation))
                        self.assertGreaterEqual(a.along,strip.start[0]+0.75-1e-8)
                        self.assertLessEqual(a.along,strip.start[0]+strip.size[0]-0.75+1e-8)
                attachments=[a for a in s.attachments if a.board==board.name]
                fixed=next(a for a in attachments if a.locked)
                self.assertAlmostEqual(fixed.along,(s.min_x+s.max_x)/2)
                for strip in strips:
                    row=[a for a in attachments if abs(a.elevation-strip.start[1]-strip.size[1]/2)<1e-8]
                    xs=sorted(a.along for a in row)
                    self.assertTrue(xs)
                    self.assertTrue(all(b-a<=10+1e-8 for a,b in zip(xs,xs[1:])))
                    for a in row:
                        self.assertEqual(a.length_in,1.125)
                        self.assertGreater(board.start[2]+board.size[2]-a.length_in,strip.start[2])
            if dims[0]==24:
                self.assertEqual(len(s.roof_strips),9)
                self.assertEqual(len([p for p in s.roof_strips if "strip_5_" in p.name]),1)
            rows={r['name']:r for r in s.bom_rows()}
            self.assertEqual(rows[f'{s.name}_roof_face_screws']['qty'],sum(a.wall=='roof' for a in s.attachments))
            self.assertEqual(rows[f'{s.name}_roof_strip_anchors']['qty'],len(s.roof_strip_anchors))
            self.assertEqual(rows[f'{s.name}_roof_support_toe_screws']['qty'],4)
            plywood=rows[f'{s.name}_PT_exterior_plywood_3_4']
            self.assertEqual(plywood['category'],'sheet')
            self.assertEqual(plywood['stock_length_ft'],'')

    def test_trim_ground_clearance_and_upper_corner_junctions(self):
        s=build.siding
        for p in s.angle_parts:
            if '_US20_corner_' in p.name:
                self.assertAlmostEqual(p.start[2]+p.size[2],s.roof_finished_top_z+0.22-40/25.4-s.end_gap)
            if p.material=='US20' and p.name.endswith('_top'):
                self.assertEqual(len(p.polygon),4)
                self.assertAlmostEqual(p.start[2],s.roof_finished_top_z)
        relief=next(p for p in s.angle_parts if p.name.endswith('US20_front_face'))
        self.assertTrue(relief.rebates)
        a,dim=relief.rebates[0]
        self.assertAlmostEqual(a[0],s.front_trim_relief[0])
        self.assertAlmostEqual(a[2]+dim[2],s.front_trim_relief[2])
        for name,x in (('left',s.rear_opening_min_x),('right',s.rear_opening_max_x)):
            p=next(p for p in s.angle_parts if p.name.endswith(f'US20_opening_{name}_1'))
            self.assertAlmostEqual(p.start[2],s.ground_z(x,s.max_y)+0.75)

    def test_direct_seating_and_applied_trim(self):
        s=build.siding
        self.assertEqual(s.exterior_offset,0.5)
        self.assertEqual(s.xy('front',s.min_x)[1],-0.5)
        self.assertTrue(all(p.start[2]==s.roof_support_z for p in s.board_parts if '_top_' in p.name))
        self.assertEqual({p.material for p in s.angle_parts},{'US20'})
        for p in s.angle_parts:
            if '_US20_corner_' in p.name:
                self.assertAlmostEqual(max(p.size[:2]),40/25.4)
            if p.name.endswith('US20_front_face'):
                self.assertAlmostEqual(p.start[2]+p.size[2],s.roof_finished_top_z+0.22)
        self.assertEqual({p.material for p in s.hardware_parts},{'face_screw','strip_anchor'})
        for p in s.hardware_parts:
            self.assertTrue(all(d>0 for d in p.size))
        jamb=next(p for p in s.angle_parts if p.name.endswith('opening_left_1'))
        header=next(p for p in s.angle_parts if p.name.endswith('opening_header_return'))
        self.assertAlmostEqual(header.start[2]-(jamb.start[2]+jamb.size[2]),s.end_gap)

    def test_screws_land_on_boards_and_retain_both_edges(self):
        for dims in ((24,19.375,49.625),(30,26,55),(36,30,55)):
            s=build.build_enclosure(*dims).siding
            for a in s.attachments:
                if a.wall=='roof':
                    p=next(p for p in s.board_parts if p.name==a.board)
                    self.assertTrue(p.start[0]<a.along<p.start[0]+p.size[0])
                    self.assertTrue(p.start[1]<a.elevation<p.start[1]+p.size[1])
                else:
                    c=next(c for c in s.cuts if c.name==a.board)
                    self.assertTrue(c.start<a.along<c.end)
                    self.assertTrue(max(c.bottom,s.ground_z(*s.xy(c.wall,a.along))+s.ground_clearance)<a.elevation<c.top)
                    if c.notched and s.rear_opening_min_x<=a.along<=s.rear_opening_max_x:
                        self.assertGreater(a.elevation,s.rear_opening_top_z+s.end_gap)
                    openings=s.front_openings if c.wall=='front' else s.right_openings if c.wall=='right' else ()
                    for o in openings:
                        lo,hi=(o.min_x,o.max_x) if c.wall=='front' else (o.min_y,o.max_y)
                        self.assertFalse(lo<=a.along<=hi and o.bottom_z<=a.elevation<=o.top_z)
            # Intact full courses have supported fastening at both edges.
            for c in s.cuts:
                if c.wall not in ('front','left') or c.course!=2: continue
                rows={round(a.elevation,6) for a in s.attachments if a.board==c.name}
                self.assertEqual(rows,{round(c.bottom+0.75,6),round(c.top-0.75,6)})

    def test_cut_bom_shopping_and_generated_artifacts(self):
        s=build.siding
        bom={r['name']:r for r in s.bom_rows()}
        self.assertEqual(bom[f'{s.name}_face_screws']['qty'],sum(a.wall!='roof' for a in s.attachments))
        self.assertEqual(bom[f'{s.name}_US20']['stock_board_qty'],5)
        self.assertEqual(bom[f'{s.name}_US135']['stock_board_qty'],10)
        self.assertEqual(bom[f'{s.name}_US20']['qty'],11)
        self.assertFalse(any(token in row['name'] for row in bom.values()
                             for token in ('AW08','T-7','US44','US46','clip_screws','locking_screws','stopper_screws')))
        purchases={r['item']:r for r in s.purchase_bom_rows()}
        self.assertEqual(purchases['face_screws']['quantity'],sum(a.wall!='roof' for a in s.attachments))
        self.assertEqual(purchases['US20']['quantity'],5)
        self.assertEqual(bom[f'{s.name}_US135']['qty'],len(s.cut_lengths))
        self.assertTrue(any(r['type'].startswith('US135') for r in build.model.shopping_list_rows()))
        rows=s.fabrication_rows()
        self.assertEqual(sum(r['material']=='US135' for r in rows),len(s.cut_lengths))
        with tempfile.TemporaryDirectory() as tmp:
            s.write_artifacts(tmp)
            manifest=json.loads((Path(tmp)/'siding_installation.json').read_text())
            self.assertEqual(manifest['board_standoff_in'],0)
            self.assertIn('custom direct face fastening',manifest['attachment_method'])
            self.assertTrue((Path(tmp)/'siding_bom.csv').exists())
            self.assertEqual(manifest['product'],'US135')
            self.assertEqual(manifest['product_line'],'All Weather Pro')
            self.assertIn('top downward',manifest['wall_installation'])
            self.assertIn('NOT PERFORMED',manifest['physical_dry_fit_status'])
            self.assertEqual(len(list(Path(tmp).glob('siding_corner_*.scad'))),4)
        # Increasing saw kerf must never decrease stock requirements.
        wide={r['name']:r for r in replace(s,kerf=0.25).bom_rows()}
        self.assertGreaterEqual(wide[f'{s.name}_US135']['stock_board_qty'],bom[f'{s.name}_US135']['stock_board_qty'])

    def test_viewer_installs_wall_courses_downward(self):
        steps={name:step.number for step in build.model.build_steps for name in step.object_names}
        s=build.siding
        for wall in ('front','left','right'):
            cuts=[c for c in s.cuts if c.wall==wall]
            numbers=[min(steps[p.name] for p in s.board_parts if p.name==c.name or p.name.startswith(c.name+'_piece_')) for c in cuts]
            self.assertEqual(numbers,sorted(numbers))
            self.assertEqual(len(set(numbers)),len(cuts))
        build.model.validate()

    def test_rejects_invalid_pitch_and_clearance(self):
        for kwargs in ({'course_pitch':0},{'course_pitch':7},{'ground_clearance':0.5},
                       {'course_pitch':float('nan')},{'ground':None},{'roof_strip_width':0},
                       {'roof_strip_thickness':0.5},{'roof_hardware_clearance':0}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                replace(build.siding,**kwargs)


if __name__=='__main__':
    unittest.main()
