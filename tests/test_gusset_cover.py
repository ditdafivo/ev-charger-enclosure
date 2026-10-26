"""Fit checks against the actual roof, plate hardware, and shortened plywood."""
import unittest

from build import default_build
from lumber_model.gusset import GUSSET_HOLE_CENTERS_IN, GUSSET_SCREW_HEAD_DIAMETER_IN
from lumber_model.gusset_cover import covers_for_siding, DECK_BOTTOM, HEIGHT, MM, OVERHANG, PLATE


def overlap(a, b):
    return all(a[0][i] < b[0][i]+b[1][i]-1e-7 and
               b[0][i] < a[0][i]+a[1][i]-1e-7 for i in range(3))


class GussetCoverTests(unittest.TestCase):
    def test_cover_fits_frame_margin_and_avoids_hardware_and_plywood(self):
        s = default_build.siding
        covers = covers_for_siding(s)
        self.assertEqual(len(covers), 2)
        self.assertLess(OVERHANG, 0.25*MM)
        for cover in covers:
            for pos, size in cover.boxes:
                self.assertGreater(min(size), 0)
                self.assertGreaterEqual(pos[2], 0)
                self.assertLessEqual(pos[2]+size[2], HEIGHT+1e-7)
                world = (tuple(cover.origin_in[i]+pos[i]/MM for i in range(3)),
                         tuple(v/MM for v in size))
                for strip in s.roof_strips:
                    self.assertFalse(overlap(world, (strip.start, strip.size)))
                # Conservative square envelope around each 0.35-inch pan head.
                for x, y in GUSSET_HOLE_CENTERS_IN:
                    radius = GUSSET_SCREW_HEAD_DIAMETER_IN*MM/2
                    self.assertFalse(overlap((pos,size),
                        ((x*MM-radius,y*MM-radius,0.074*MM),
                         (2*radius,2*radius,0.11*MM))))
                self.assertFalse(overlap((pos,size), ((0,0,0),(6*MM,6*MM,0.074*MM))))
            for a, b in cover.bearing_bands_mm:
                self.assertTrue(any(
                    a/MM+cover.origin_in[1] >= board.start[1]+s.board_width-s.course_pitch-1e-7
                    and b/MM+cover.origin_in[1] <= min(board.start[1]+board.size[1],board.start[1]+s.course_pitch)+1e-7
                    for board in s.board_parts if '_top_' in board.name))
            component = default_build.components[cover.name]
            resolved = component.resolved(default_build.members[component.member])
            self.assertAlmostEqual(resolved.box_min[2]+resolved.box_size[2],s.roof_support_z)
            self.assertAlmostEqual(resolved.box_size[0],6+2*OVERHANG/MM)
            self.assertAlmostEqual(resolved.box_min[1],cover.origin_in[1]+cover.y_bounds_mm[0]/MM)
            self.assertAlmostEqual(resolved.box_size[1],(cover.y_bounds_mm[1]-cover.y_bounds_mm[0])/MM)

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
            for pos,size in cover.boxes:
                if pos[2]+size[2] > DECK_BOTTOM+1e-7:
                    self.assertTrue(any(a-1e-7<=pos[1] and pos[1]+size[1]<=b+1e-7
                                        for a,b in cover.bearing_bands_mm))
                if pos[2]==0 and (pos[1]<-OVERHANG-1e-7 or
                                  pos[1]+size[1]>PLATE+OVERHANG+1e-7):
                    self.assertTrue(any(fx-1e-7<=pos[0] and pos[0]+size[0]<=fx+fw+1e-7
                                        and fy-1e-7<=pos[1] and pos[1]+size[1]<=fy+fh+1e-7
                                        for fx,fy,fw,fh in cover.framing_rectangles_mm))

    def test_inward_extension_reaches_interrupted_run_edges(self):
        rear,front = covers_for_siding(default_build.siding)
        self.assertAlmostEqual(rear.y_bounds_mm[0],rear.bearing_bands_mm[0][0])
        self.assertAlmostEqual(rear.y_bounds_mm[1],PLATE+OVERHANG)
        self.assertAlmostEqual(front.y_bounds_mm[0],-OVERHANG)
        self.assertAlmostEqual(front.y_bounds_mm[1],front.bearing_bands_mm[-1][1])
        self.assertAlmostEqual(rear.y_bounds_mm[1]-rear.y_bounds_mm[0],175)
        self.assertAlmostEqual(front.y_bounds_mm[1]-front.y_bounds_mm[0],182.425)

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


if __name__ == '__main__':
    unittest.main()
