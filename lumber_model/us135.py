"""US135 enclosure cladding; product envelopes, not manufacturing CAD.

The 130 mm course pitch and direct face fastening are prototype assumptions.
See SIDING.md before cutting stock or installing this roof-cover adaptation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cached_property
import math
from typing import Any

from lumber_model.fabrication import clip_polygon_to_box
from lumber_model.ground import ResolvedGroundSurface
from lumber_model.siding import (
    CompositeSiding, SidingPart, FrontSidingBore, FrontSidingOpening, _subtract_front_opening, _subtract_right_opening,
    minimum_stock_board_count,
)

ROOF_STRIP_THICKNESS = 0.75
ROOF_STRIP_MATERIAL = "PT_exterior_plywood_3_4"
US135_THICKNESS = 0.5
US135_PROFILE_WIDTH = 142 / 25.4
US135_COURSE_PITCH = 130 / 25.4  # provisional: verify two engaged samples
# Visualization clearance only; stock dimensions and installed pitch stay exact.
US135_PREVIEW_CLEARANCE = 0.002


def _preview_rebate(start: tuple[float, float, float], size: tuple[float, float, float]):
    """Overcut rebate faces to avoid coplanar cutters and mating-board faces."""
    margin = US135_PREVIEW_CLEARANCE / 2
    return (tuple(v-margin for v in start), tuple(v+2*margin for v in size))


@dataclass(frozen=True)
class BoardCut:
    name: str
    wall: str
    course: int
    length: float
    bottom: float
    top: float
    start: float
    end: float
    bottom_edge: tuple[tuple[float, float], ...]
    notched: bool = False


@dataclass(frozen=True)
class Attachment:
    board: str
    wall: str
    along: float
    elevation: float
    kind: str
    locked: bool = False
    length_in: float | None = None
    concealment: str = "exposed"
    exception_reason: str | None = None
    recessed: bool = False


@dataclass(frozen=True)
class US135Siding(CompositeSiding):
    board_width: float = US135_PROFILE_WIDTH
    board_thickness: float = US135_THICKNESS
    gap: float = 0.0
    course_pitch: float = US135_COURSE_PITCH
    ground_clearance: float = 0.75
    end_gap: float = 1 / 8
    kerf: float = 1 / 8
    ground: ResolvedGroundSurface | None = None
    # Existing lumber bounding boxes, used to notch added backing around it.
    framing: tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...] = ()
    infill_framing: tuple[tuple[tuple[float,float,float],tuple[float,float,float]], ...] = ()
    front_infill_back_y: float | None = None
    front_infill_top_z: float | None = None
    front_infill_header_top_z: float | None = None
    front_infill_bores: tuple[FrontSidingBore, ...] = ()
    diagonal: tuple[tuple[float, float], ...] = ()
    roof_strip_thickness: float = ROOF_STRIP_THICKNESS
    roof_strip_width: float = 1.5
    roof_hardware_clearance: float = 1/8
    roof_gussets: tuple[tuple[tuple[float,float,float],tuple[float,float,float]], ...] = ()
    front_trim_relief: tuple[float,float,float] | None = None  # x min/max, clear-above Z

    def __post_init__(self) -> None:
        super().__post_init__()
        for value in (self.course_pitch, self.ground_clearance,
                      self.end_gap, self.kerf, self.roof_strip_thickness,
                      self.roof_strip_width, self.roof_hardware_clearance):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("US135 layout dimensions must be finite and positive")
        if self.front_infill_back_y is not None and (not math.isfinite(self.front_infill_back_y) or
                not self.min_y + 3.5 <= self.front_infill_back_y <= self.max_y - 3.5):
            raise ValueError("front infill rear plane must lie between the post rows")
        for elevation in (self.front_infill_top_z, self.front_infill_header_top_z):
            if elevation is not None and not math.isfinite(elevation):
                raise ValueError("front infill elevations must be finite")
        if abs(self.roof_support_z-self.frame_top_z-self.roof_strip_thickness)>1e-8:
            raise ValueError("roof support plane must match plywood strip thickness")
        if self.course_pitch > self.board_width:
            raise ValueError("US135 course pitch exceeds profile width")
        if max(self.max_x-self.min_x,self.max_y-self.min_y,self.frame_top_z-self.bottom_z)>96:
            raise ValueError("US135 layout exceeds the 8 ft / 32 F expansion-gap design envelope")
        if self.ground is None:
            raise ValueError("US135 siding requires surveyed ground")
        if self.ground_clearance < 0.75:
            raise ValueError("US135 siding requires at least 3/4 inch ground clearance")
        if self.frame_top_z - self.ground_z(self.max_x, self.max_y) < self.board_width:
            raise ValueError("US135 enclosure is too short for a full top course")

    @property
    def exterior_offset(self) -> float:
        return self.board_thickness

    @property
    def roof_finished_top_z(self) -> float:
        return self.roof_support_z + self.exterior_offset

    def ground_z(self, x: float, y: float) -> float:
        assert self.ground is not None
        return self.ground.z_at(x, y)

    def xy(self, wall: str, along: float, *, outside: bool = True) -> tuple[float, float]:
        d = self.exterior_offset if outside else 0
        return {
            "front": (along, self.min_y-d), "rear": (along, self.max_y+d),
            "left": (self.min_x-d, along), "right": (self.max_x+d, along),
        }[wall]

    def span(self, wall: str) -> tuple[float, float]:
        if wall in ("front", "rear"):
            return self.min_x+self.end_gap, self.max_x-self.end_gap
        return self.min_y+self.end_gap, self.max_y-self.end_gap

    @cached_property
    def courses(self) -> tuple[tuple[float, float], ...]:
        floor = min(self.ground_z(x,y) for x,y in (
            (self.min_x,self.min_y),(self.max_x,self.min_y),
            (self.min_x,self.max_y),(self.max_x,self.max_y)))+self.ground_clearance
        # Physical top profile remains full width. Lower profiles overlap its
        # tongue allowance; exposed faces repeat on the installed pitch.
        result = []
        top = self.finished_top_z
        bottom = top-self.board_width
        while top > floor + 1e-9:
            result.append((bottom, top))
            top = bottom + (self.board_width-self.course_pitch)
            bottom -= self.course_pitch
        return tuple(result)

    def _edge(self, wall: str, a: float, b: float, bottom: float) -> tuple[tuple[float,float], ...]:
        # Clamped bilinear survey has slope breaks at the survey bounds.
        assert self.ground is not None
        axis = 0 if wall in ("front", "rear") else 1
        knots = sorted({a,b,*(p[axis] for p in self.ground.corners if a < p[axis] < b)})
        points = [(s,max(bottom,self.ground_z(*self.xy(wall,s))+self.ground_clearance)) for s in knots]
        result = []
        for left,right in zip(points,points[1:]):
            result.append(left)
            gl = self.ground_z(*self.xy(wall,left[0]))+self.ground_clearance-bottom
            gr = self.ground_z(*self.xy(wall,right[0]))+self.ground_clearance-bottom
            if gl*gr < 0:
                result.append((left[0]+(right[0]-left[0])*(-gl)/(gr-gl),bottom))
        result.append(points[-1])
        return tuple(result)

    @cached_property
    def cuts(self) -> tuple[BoardCut, ...]:
        result = []
        for i,(bottom,top) in enumerate(self.courses,1):
            for wall in ("front","left","right","rear"):
                a,b = self.span(wall)
                spans = [(a,b)]
                if wall == "rear" and i > 1:
                    spans = [(a,self.rear_opening_min_x-self.end_gap),
                             (self.rear_opening_max_x+self.end_gap,b)]
                for j,(a,b) in enumerate(spans,1):
                    if b <= a:
                        raise ValueError("US135 trim clearance consumes a rear wing")
                    edge = self._edge(wall,a,b,bottom)
                    if min(z for _,z in edge) >= top-1e-9:
                        continue
                    # If grade removes a complete end of a course, clip the
                    # polygon there; retain the full blank for the cut list.
                    suffix = f"_{j}" if len(spans)>1 else ""
                    result.append(BoardCut(f"{self.name}_{wall}_{i}{suffix}",wall,i,b-a,
                        bottom,top,a,b,edge,wall=="rear" and i==1))
        return tuple(result)

    def _wall_part(self, cut: BoardCut, rect: tuple[float,float,float,float], suffix: str) -> SidingPart | None:
        a,b,lo,hi = rect
        edge = self._edge(cut.wall,a,b,lo)
        poly = (*edge,(b,hi),(a,hi))
        poly = clip_polygon_to_box(poly,min_x=a,max_x=b,min_y=lo,max_y=hi)
        if len(poly)<3 or min(z for _,z in poly) >= hi-1e-8:
            return None
        z0 = min(z for _,z in poly)
        t = self.board_thickness
        d = 0.0
        start,size,plane = {
            "front": ((a,self.min_y-d-t,z0),(b-a,t,hi-z0),"xz"),
            "rear": ((a,self.max_y+d,z0),(b-a,t,hi-z0),"xz"),
            "left": ((self.min_x-d-t,a,z0),(t,b-a,hi-z0),"yz"),
            "right": ((self.max_x+d,a,z0),(t,b-a,hi-z0),"yz"),
        }[cut.wall]
        # Simplified mating rabbets represent the tongue allowance. Detailed
        # groove/clip machining remains a sample-check dimension, not CAD.
        lap=self.board_width-self.course_pitch
        x,y,z=start; dx,dy,dz=size
        if cut.wall in ("front","rear"):
            outer=y if cut.wall=="front" else y+t/2
            inner=y+t/2 if cut.wall=="front" else y
            rebates=(((x,outer,cut.bottom),(dx,t/2,lap)),
                     ((x,inner,cut.top-lap),(dx,t/2,lap)))
        else:
            outer=x if cut.wall=="left" else x+t/2
            inner=x+t/2 if cut.wall=="left" else x
            rebates=(((outer,y,cut.bottom),(t/2,dy,lap)),
                     ((inner,y,cut.top-lap),(t/2,dy,lap)))
        return SidingPart(cut.name+suffix,"US135",start,size,self.decking_color,
            front_bores=tuple(bore for bore in self.front_bores if cut.wall=="front"
                and bore.center_x+bore.diameter/2>a and bore.center_x-bore.diameter/2<b
                and bore.center_z+bore.diameter/2>z0 and bore.center_z-bore.diameter/2<hi),
            polygon=tuple((s-a,z-z0) for s,z in poly),plane=plane,
            rebates=tuple(_preview_rebate(pos,extent) for pos,extent in rebates))

    @cached_property
    def board_parts(self) -> tuple[SidingPart, ...]:
        parts = []
        for cut in self.cuts:
            rects = ((cut.start,cut.end,cut.bottom,cut.top),)
            if cut.wall == "front":
                for opening in self.front_openings:
                    rects = tuple(p for r in rects for p in _subtract_front_opening(r,opening))
            if cut.wall == "right":
                for opening in self.right_openings:
                    rects = tuple(p for r in rects for p in _subtract_right_opening(r,opening))
            if cut.notched:
                a,b,lo,hi = rects[0]
                rects = ((a,self.rear_opening_min_x-self.end_gap,lo,hi),
                         (self.rear_opening_max_x+self.end_gap,b,lo,hi),
                         (self.rear_opening_min_x-self.end_gap,self.rear_opening_max_x+self.end_gap,
                          self.rear_opening_top_z+self.end_gap,hi))
            cut_parts = []
            for j,r in enumerate(rects,1):
                part = self._wall_part(cut,r,"" if len(rects)==1 else f"_piece_{j}")
                if part:
                    cut_parts.append(part)
            if cut_parts:
                cut_parts[0] = replace(cut_parts[0],cut_length=cut.length)
                parts.extend(cut_parts)
        y = self.min_y+self.end_gap
        i = 1
        while y < self.max_y-self.end_gap-1e-9:
            width = min(self.board_width,self.max_y-self.end_gap-y)
            x=self.min_x+self.end_gap; z=self.roof_support_z
            lap=self.board_width-self.course_pitch
            parts.append(SidingPart(f"{self.name}_top_{i}","US135",
                (self.min_x+self.end_gap,y,self.roof_support_z),
                (self.max_x-self.min_x-2*self.end_gap,width,self.board_thickness),
                self.decking_color,cut_length=self.max_x-self.min_x-2*self.end_gap,
                rebates=tuple(_preview_rebate(pos,extent) for pos,extent in (
                    ((x,y,z+self.board_thickness/2),(self.max_x-self.min_x-2*self.end_gap,lap,self.board_thickness/2)),
                    ((x,y+self.board_width-lap,z),(self.max_x-self.min_x-2*self.end_gap,lap,self.board_thickness/2))))))
            y += self.course_pitch
            i += 1
            if y+self.board_width-self.course_pitch >= self.max_y-self.end_gap:
                break
        return tuple(parts)

    @staticmethod
    def _stations(a: float,b: float,maximum: float) -> tuple[float,...]:
        n = max(2,math.ceil((b-a)/maximum))
        if n%2:
            n += 1  # a support at the midpoint for the single locking screw
        return tuple(a+(b-a)*i/n for i in range(n+1))

    def wall_stations(self, wall: str) -> tuple[float,...]:
        a,b = self.span(wall)
        return self._stations(a+1.6875,b-1.6875,16)

    def opening_supports(self, wall: str) -> tuple[tuple[float,float,float], ...]:
        """Local screw stations and backing bounds for cutout-affected courses."""
        openings = self.front_openings if wall=="front" else self.right_openings if wall=="right" else ()
        a,b = self.span(wall)
        supports = []
        for opening in openings:
            courses = [c for c in self.cuts if c.wall==wall
                       and c.bottom<opening.top_z and c.top>opening.bottom_z]
            if not courses:
                continue
            bottom = min(c.bottom for c in courses)
            top = max(c.top for c in courses)
            lo,hi = (opening.min_x,opening.max_x) if wall=="front" else (opening.min_y,opening.max_y)
            supports.extend((s,bottom,top) for s in (lo-0.5,hi+0.5) if a<=s<=b)
        return tuple(supports)

    @property
    def roof_stations(self) -> tuple[float,...]:
        return self._stations(self.min_x+1.75,self.max_x-1.75,10)

    @cached_property
    def wall_backing_parts(self) -> tuple[SidingPart,...]:
        parts = []
        def add_notched(name: str, start: tuple[float,float,float], size: tuple[float,float,float], axis: int,
                        extra: tuple = ()) -> None:
            intervals = [(start[axis],start[axis]+size[axis])]
            for loc,extent in (*self.framing,*extra):
                if all(start[k]<loc[k]+extent[k]-1e-8 and start[k]+size[k]>loc[k]+1e-8 for k in range(3) if k!=axis):
                    intervals = [(c,d) for a,b in intervals for c,d in [(a,min(b,loc[axis])),(max(a,loc[axis]+extent[axis]),b)] if d>c+1e-6]
            for i,(a,b) in enumerate(intervals,1):
                pos=list(start); dims=list(size); pos[axis]=a; dims[axis]=b-a
                parts.append(SidingPart(f"{self.name}_{name}_{i}","PT_5/4x6_backing",tuple(pos),tuple(dims),
                    (0.44,0.26,0.11,1),cut_length=b-a))
        for wall in ("front","left","right"):
            regular = self.wall_stations(wall)
            supports = [(str(j),s,None,None) for j,s in enumerate(regular[1:-1],1)]
            supports.extend((f"opening_{j}",s,bottom,top)
                            for j,(s,bottom,top) in enumerate(self.opening_supports(wall),1)
                            if s not in regular)
            for j,s,bottom,top in supports:
                wa,wb=(self.min_x,self.max_x) if wall=="front" else (self.min_y,self.max_y)
                if s <= wa+3.5 or s >= wb-3.5:
                    continue  # already backed by a corner post
                a=max(wa+3.5,s-1.75); b=min(wb-3.5,s+1.75)
                z = self.ground_z(*self.xy(wall,s))+self.ground_clearance
                if bottom is not None:
                    z = max(z,bottom)
                end_z = self.frame_top_z if top is None else min(top,self.frame_top_z)
                if end_z<=z:
                    continue
                start,size = {
                    "front": ((a,self.min_y,z),(b-a,1,end_z-z)),
                    "left": ((self.min_x,a,z),(1,b-a,end_z-z)),
                    "right": ((self.max_x-1,a,z),(1,b-a,end_z-z)),
                }[wall]
                add_notched(f"backing_{wall}_{j}",start,size,2)
        return tuple(parts)

    @cached_property
    def infill_parts(self) -> tuple[SidingPart, ...]:
        """Recessed wall infill, fitted between all intersecting timber/backing."""
        parts = []
        passes = [("front", False, False), ("left", False, False),
                  ("right", False, False), ("rear", False, False)]
        if self.front_infill_header_top_z is not None:
            passes.append(("front", False, True))
        passes.append(("front", True, False))
        for wall, address, upper_front in passes:
            along_axis, normal_axis = (0, 1) if wall in ("front", "rear") else (1, 0)
            lo, hi = (self.min_x, self.max_x) if along_axis == 0 else (self.min_y, self.max_y)
            # Side infill stays within the posts; front infill moves to the
            # rail rear plane. The upper strip stays forward of the handle sweep.
            normal = {"front": self.min_y + 2.75, "rear": self.max_y - 3.5,
                      "left": self.min_x + 2.75, "right": self.max_x - 3.5}[wall]
            if wall == "front" and not address and not upper_front and self.front_infill_back_y is not None:
                normal = self.front_infill_back_y - .75
                lo, hi = self.min_x + 3.5, self.max_x - 3.5
            def panel_xy(a):
                if address:
                    return self.xy(wall, a)
                return (a, normal + .75) if along_axis == 0 else (normal + (.75 if wall == "left" else 0), a)
            if address:
                normal = self.min_y + .25
            bottom = min(self.ground_z(*panel_xy(a)) for a in (lo, hi)) + self.ground_clearance
            halfway = (bottom + self.frame_top_z) / 2
            top = self.frame_top_z
            if wall == "front" and not address:
                top = self.front_infill_top_z if self.front_infill_top_z is not None else top
                if upper_front:
                    bottom = self.front_infill_header_top_z
                elif self.front_infill_header_top_z is not None:
                    top = self.front_infill_header_top_z
            bands = ((halfway, top),) if address else ((bottom, top),)
            for band_index, (z0, z1) in enumerate(bands):
                rectangles = [(lo, hi, z0, z1)]
                obstacles = list(self.infill_framing or self.framing) + [(p.start, p.size) for p in self.wall_backing_parts]
                if wall == "rear":
                    # Keep the service opening clear up to the brace for the future rear bend.
                    start = (self.rear_opening_min_x, normal, bottom)
                    size = (self.rear_opening_max_x-self.rear_opening_min_x, .75,
                            self.frame_top_z-bottom)
                    obstacles.append((start, size))
                if wall == "right":
                    obstacles.extend(((normal, o.min_y, o.bottom_z), (.75, o.max_y-o.min_y, o.top_z-o.bottom_z)) for o in self.right_openings)
                for start, size in obstacles:
                    if normal >= start[normal_axis]+size[normal_axis]-1e-8 or normal+.75 <= start[normal_axis]+1e-8:
                        continue
                    opening = FrontSidingOpening("timber", start[along_axis], start[along_axis]+size[along_axis], start[2], start[2]+size[2])
                    rectangles = [r for rectangle in rectangles for r in _subtract_front_opening(rectangle, opening)]
                # Rejoin artificial splits introduced by subtracting disconnected framing.
                changed = True
                while changed:
                    changed = False
                    for i, a in enumerate(rectangles):
                        for j in range(i+1, len(rectangles)):
                            b = rectangles[j]
                            if a[2:] == b[2:] and (abs(a[1]-b[0])<1e-8 or abs(b[1]-a[0])<1e-8):
                                merged = (min(a[0], b[0]), max(a[1], b[1]), a[2], a[3])
                            elif a[:2] == b[:2] and (abs(a[3]-b[2])<1e-8 or abs(b[3]-a[2])<1e-8):
                                merged = (a[0], a[1], min(a[2], b[2]), max(a[3], b[3]))
                            else:
                                continue
                            rectangles[i] = merged
                            rectangles.pop(j)
                            changed = True
                            break
                        if changed:
                            break
                for a, b, c, d in rectangles:
                    # Scribe only grade-adjacent edges; retain the independent mesh skirt.
                    ca = max(c, self.ground_z(*panel_xy(a))+self.ground_clearance)
                    cb = max(c, self.ground_z(*panel_xy(b))+self.ground_clearance)
                    if min(ca, cb) >= d:
                        continue
                    base = min(ca, cb)
                    if min(d-base, b-a) < .25:
                        continue  # Screen tiny seams rather than fragile plywood slivers.
                    pos = [0., 0., base]; size = [0., 0., d-base]
                    pos[along_axis] = a; pos[normal_axis] = normal
                    size[along_axis] = b-a; size[normal_axis] = .75
                    label = "address" if address else "animal"
                    name = f"{self.name}_infill_{wall}_{label}_{len(parts)+1}"
                    polygon = ((0, ca-base), (b-a, cb-base), (b-a, d-base), (0, d-base))
                    bore_candidates = self.front_infill_bores if wall == "front" and not address and not upper_front else self.front_bores
                    bores = tuple(bore for bore in bore_candidates if a <= bore.center_x <= b and c <= bore.center_z <= d) if wall == "front" else ()
                    parts.append(SidingPart(name, ROOF_STRIP_MATERIAL, tuple(pos), tuple(size),
                                           (.56,.38,.19,1), cut_length=d-base,
                                           polygon=polygon, plane="xz" if along_axis == 0 else "yz", front_bores=bores))
        return tuple(parts)

    @cached_property
    def backing_parts(self) -> tuple[SidingPart, ...]:
        return self.wall_backing_parts + self.roof_strips + self.infill_parts

    @cached_property
    def infill_toe_entries(self) -> tuple[dict[str, Any], ...]:
        """Candidate face entries into verified adjacent timber, not edge drives."""
        entries = []
        timber = (self.infill_framing or self.framing) + tuple((p.start,p.size) for p in self.wall_backing_parts)
        for panel in self.infill_parts:
            along, normal = (0,1) if panel.plane == "xz" else (1,0)
            inward = -1 if "_right_" in panel.name or "_rear_" in panel.name else 1
            face = panel.start[normal] + (panel.size[normal] if inward == 1 else 0)
            for edge_axis, transverse_axis in ((along,2),(2,along)):
                for direction in (-1, 1):
                    edge = panel.start[edge_axis] + (panel.size[edge_axis] if direction == 1 else 0)
                    for fraction in (1/3, 2/3):
                        point = list(panel.start)
                        point[edge_axis] = edge + direction*.01
                        point[normal] = face-inward*.1
                        point[transverse_axis] += panel.size[transverse_axis]*fraction
                        support = next(((loc,size) for loc,size in timber if all(loc[k]-1e-8 <= point[k] <= loc[k]+size[k]+1e-8 for k in range(3))), None)
                        if support is None:
                            continue
                        point[edge_axis] = edge-direction*min(.25,panel.size[edge_axis]/4)
                        point[normal] = face
                        axis = [0.,0.,0.]
                        axis[edge_axis] = direction/math.sqrt(1.0625)
                        axis[normal] = -inward*.25/math.sqrt(1.0625)
                        entries.append(dict(panel=panel.name, entry_in=tuple(point), axis=tuple(axis),
                                            supporting_timber_start_in=support[0],
                                            status="Candidate only; field-select length and confirm contained tip and engagement"))
        return tuple(entries)

    @cached_property
    def plywood_layout(self) -> dict[str, Any]:
        from lumber_model.plywood import plan_plywood
        cuts = [(p.name, p.size[0], p.size[1], False) for p in self.roof_strips]
        cuts += [(p.name, p.size[0] if p.plane == "xz" else p.size[1], p.size[2], True) for p in self.infill_parts]
        return plan_plywood(cuts, self.kerf)

    @cached_property
    def roof_strips(self) -> tuple[SidingPart,...]:
        """Continuous X strips; shorten ends where a gusset interrupts bearing."""
        result=[]
        lap=self.board_width-self.course_pitch
        for board in self.board_parts:
            if "_top_" not in board.name: continue
            # The low-Y recessed lip retains its underside: back it directly.
            # Keep the other strip clear of the high-Y underside rebate.
            lo=board.start[1]
            hi=min(board.start[1]+board.size[1],board.start[1]+self.course_pitch)
            width=hi-lo
            if width<=0: raise ValueError(f"{board.name}: no solid underside for roof support")
            bands=((lo,hi),) if width<=2*self.roof_strip_width else (
                (lo,lo+self.roof_strip_width),(hi-self.roof_strip_width,hi))
            for i,(ya,yb) in enumerate(bands,1):
                xa=board.start[0]; xb=xa+board.size[0]
                for loc,size in self.roof_gussets:
                    c=self.roof_hardware_clearance
                    if ya<loc[1]+size[1]+c and yb>loc[1]-c:
                        if loc[0]+size[0]/2<(self.min_x+self.max_x)/2:
                            xa=max(xa,loc[0]+size[0]+c)
                        else: xb=min(xb,loc[0]-c)
                if xb-xa<1.5:
                    raise ValueError(f"{board.name}: gusset cutout leaves insufficient strip length")
                result.append(SidingPart(f"{self.name}_roof_strip_{board.name.rsplit('_',1)[1]}_{i}",
                    ROOF_STRIP_MATERIAL,(xa,ya,self.frame_top_z),
                    (xb-xa,yb-ya,self.roof_strip_thickness),(0.56,0.38,0.19,1),cut_length=xb-xa))
        return tuple(result)

    @staticmethod
    def _inside_polygon(x: float,y: float,poly: tuple) -> bool:
        crosses=[(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
                 for a,b in zip(poly,poly[1:]+poly[:1])]
        return bool(crosses) and (all(v>=-1e-8 for v in crosses) or all(v<=1e-8 for v in crosses))

    def _base_supported(self,x: float,y: float) -> bool:
        return any(abs(loc[2]+size[2]-self.frame_top_z)<1e-6
                   and loc[0]<=x<=loc[0]+size[0] and loc[1]<=y<=loc[1]+size[1]
                   for loc,size in self.framing) or self._inside_polygon(x,y,self.diagonal)

    @cached_property
    def roof_strip_anchors(self) -> tuple[Attachment,...]:
        anchors=[]
        for strip in self.roof_strips:
            y=strip.start[1]+strip.size[1]/2
            for end in (0,1):
                # Search inward from the cut end for actual frame/diagonal bearing.
                candidates=[strip.start[0]+0.75+i*0.125 for i in
                            range(max(1,math.floor((strip.size[0]-1.5)/0.125)+1))]
                if end: candidates.reverse()
                x=next((x for x in candidates if self._base_supported(x,y)),None)
                if x is None: raise ValueError(f"{strip.name}: no framing for end anchor")
                anchors.append(Attachment(strip.name,"roof",x,y,"strip_anchor"))
        return tuple(anchors)

    def _surface_supported(self, wall: str, s: float, z: float) -> bool:
        x,y=self.xy(wall,s,outside=False)
        # Screw passes inward from the supporting face.
        eps=0.02
        if wall=="front": y+=eps
        elif wall=="rear": y-=eps
        elif wall=="left": x+=eps
        else: x-=eps
        return any(loc[0]-eps<=x<=loc[0]+size[0]+eps and loc[1]-eps<=y<=loc[1]+size[1]+eps
            and loc[2]-eps<=z<=loc[2]+size[2]+eps
            for loc,size in (*self.framing,*((p.start,p.size) for p in self.backing_parts)))

    def _wall_intervals(self, cut: BoardCut, station: float) -> list[tuple[float,float]]:
        """Remaining board material at a station, including cutouts and grade."""
        bottom=max(cut.bottom,self.ground_z(*self.xy(cut.wall,station))+self.ground_clearance)
        if cut.notched and self.rear_opening_min_x-self.end_gap<=station<=self.rear_opening_max_x+self.end_gap:
            bottom=max(bottom,self.rear_opening_top_z+self.end_gap)
        intervals=[(bottom,cut.top)] if bottom<cut.top else []
        openings=self.front_openings if cut.wall=="front" else self.right_openings if cut.wall=="right" else ()
        for o in openings:
            lo,hi=(o.min_x,o.max_x) if cut.wall=="front" else (o.min_y,o.max_y)
            if lo-0.125<=station<=hi+0.125:
                intervals=[piece for low,high in intervals for piece in
                           ((low,min(high,o.bottom_z-0.125)),(max(low,o.top_z+0.125),high))
                           if piece[1]>piece[0]]
        return intervals

    def _overlap_covers(self, cut: BoardCut, station: float, z: float) -> bool:
        radius=0.125
        return any(other.wall==cut.wall and other.course==cut.course+1
                   and other.start<=station-radius and station+radius<=other.end
                   and all(any(lo<=z-radius and z+radius<=hi
                               for lo,hi in self._wall_intervals(other,x))
                           for x in (station-radius,station,station+radius))
                   for other in self.cuts)

    def _trim_covers(self, wall: str, station: float, z: float) -> bool:
        # Project the complete head onto actual wall-facing US20 rectangles.
        axis=0 if wall in ("front","rear") else 1
        normal=1-axis
        face=self.xy(wall,station)[normal]
        for p in self.angle_parts:
            if abs(p.size[normal]-0.22)>1e-8: continue
            near=p.start[normal]+(p.size[normal] if wall in ("front","left") else 0)
            if abs(near-face)>1e-8: continue
            if not (p.start[axis]<=station-0.125 and station+0.125<=p.start[axis]+p.size[axis]
                    and p.start[2]<=z-0.125 and z+0.125<=p.start[2]+p.size[2]): continue
            if any(pos[axis]<station+0.125 and pos[axis]+size[axis]>station-0.125
                   and pos[2]<z+0.125 and pos[2]+size[2]>z-0.125 for pos,size in p.rebates): continue
            return True
        return False

    @cached_property
    def attachments(self) -> tuple[Attachment,...]:
        result=[]
        lap=self.board_width-self.course_pitch
        for cut in self.cuts:
            stations=[s for s in self.wall_stations(cut.wall) if cut.start<s<cut.end]
            openings=self.front_openings if cut.wall=="front" else self.right_openings if cut.wall=="right" else ()
            for opening in openings:
                if cut.bottom<opening.top_z and cut.top>opening.bottom_z:
                    lo,hi = (opening.min_x,opening.max_x) if cut.wall=="front" else (opening.min_y,opening.max_y)
                    stations.extend(s for s in (lo-0.5,hi+0.5) if cut.start<s<cut.end)
            midpoint=(cut.start+cut.end)/2
            stations.append(midpoint)
            candidates=[]
            for station in sorted(set(stations)):
                for bottom,top in self._wall_intervals(cut,station):
                    nominal=cut.bottom+lap/2
                    recessed=(lap>=0.25 and bottom+0.125<=nominal<=top-0.125)
                    z=nominal if recessed else bottom+min(0.75,(top-bottom)/2)
                    covered=recessed and self._overlap_covers(cut,station,z)
                    if not covered or not self._surface_supported(cut.wall,station,z):
                        # Prefer a supported trim-covered exception, including the header.
                        trim_rows=[bottom+0.125+i*0.125 for i in range(max(0,int((top-bottom-0.25)/0.125)+1))]
                        trim_rows=[v for v in trim_rows if self._trim_covers(cut.wall,station,v)
                                   and self._surface_supported(cut.wall,station,v)]
                        if trim_rows:
                            z=min(trim_rows,key=lambda v:abs(v-z))
                            recessed=cut.bottom+0.125<=z<=cut.bottom+lap-0.125
                    if not self._surface_supported(cut.wall,station,z):
                        z=top-min(0.75,(top-bottom)/2)
                        recessed=False
                        if not self._surface_supported(cut.wall,station,z): continue
                    covered=recessed and self._overlap_covers(cut,station,z)
                    concealment="overlap-concealed" if covered else "trim-concealed" if self._trim_covers(cut.wall,station,z) else "exposed"
                    reason=None if covered else "cutout, termination, scribe or missing support prevents concealed overlap fastening"
                    candidates.append(Attachment(cut.name,cut.wall,station,z,"face_screw",
                        concealment=concealment,exception_reason=reason,recessed=recessed))
            if not candidates:
                raise ValueError(f"{cut.name}: no supported face fastening")
            # Keep the notched physical board fixed at its header midpoint.
            fixed=min(candidates,key=lambda a:(abs(a.along-midpoint),-a.elevation))
            result.extend(replace(a,locked=a==fixed) for a in candidates)
        for part in self.board_parts:
            if "_top_" not in part.name: continue
            candidates=[]
            course=part.name.rsplit('_',1)[1]
            # Install from rear to front: the next frontward board covers
            # this recessed low-Y row. US20 covers the frontmost row.
            y=part.start[1]+lap/2
            strip=next(p for p in self.roof_strips
                       if p.name.startswith(f"{self.name}_roof_strip_{course}_")
                       and p.start[1]<=y<=p.start[1]+p.size[1])
            a=strip.start[0]+0.75; b=strip.start[0]+strip.size[0]-0.75
            midpoint=(self.min_x+self.max_x)/2
            stations=sorted(set((*self._stations(a,b,10),midpoint)))
            concealment="trim-concealed" if course=="1" else "overlap-concealed"
            candidates.extend(Attachment(part.name,"roof",x,y,"face_screw",
                length_in=0.875,concealment=concealment,recessed=True)
                for x in stations if a<=x<=b)
            if not candidates:
                raise ValueError(f"{part.name}: no roof attachment support")
            fixed=min(candidates,key=lambda a:abs(a.along-(self.min_x+self.max_x)/2))
            result.extend(replace(a,locked=a==fixed) for a in candidates)
        return tuple(result)

    def _roof_supported(self,x: float,y: float) -> bool:
        return any(p.start[0]<=x<=p.start[0]+p.size[0]
                   and p.start[1]<=y<=p.start[1]+p.size[1] for p in self.roof_strips)

    @cached_property
    def hardware_parts(self) -> tuple[SidingPart,...]:
        parts=[]
        # Schematic head envelopes; overlap head clearance remains a sample check.
        # Shanks and movement bores are not machining CAD.
        head=0.25; height=0.08
        for i,a in enumerate(self.attachments,1):
            if a.wall=="roof":
                head_z=self.roof_finished_top_z-(self.board_thickness/2 if a.recessed else 0)
                start=(a.along-head/2,a.elevation-head/2,head_z)
                size=(head,head,height)
            else:
                x,y=self.xy(a.wall,a.along)
                if a.recessed:
                    offset=self.board_thickness/2
                    x += offset if a.wall=="left" else -offset if a.wall=="right" else 0
                    y += offset if a.wall=="front" else -offset if a.wall=="rear" else 0
                start,size={
                    "front":((x-head/2,y-height,a.elevation-head/2),(head,height,head)),
                    "rear":((x-head/2,y,a.elevation-head/2),(head,height,head)),
                    "left":((x-height,y-head/2,a.elevation-head/2),(height,head,head)),
                    "right":((x,y-head/2,a.elevation-head/2),(height,head,head)),
                }[a.wall]
            parts.append(SidingPart(f"{a.board}_face_screw_{i}","face_screw",start,size,
                (0.85,0.62,0.12,1) if a.locked else (0.45,0.48,0.5,1)))
        for i,a in enumerate(self.roof_strip_anchors,1):
            # Recess anchor heads flush into plywood; siding remains free to slide.
            parts.append(SidingPart(f"{a.board}_anchor_{i}","strip_anchor",
                (a.along-head/2,a.elevation-head/2,self.roof_support_z-height),
                (head,head,height),(0.35,0.38,0.4,1)))
        return tuple(parts)

    @cached_property
    def angle_parts(self) -> tuple[SidingPart,...]:
        parts=[]; t=0.22; leg=40/25.4; cap=leg
        d=self.exterior_offset
        xl=self.min_x-d; xr=self.max_x+d; yf=self.min_y-d; yr=self.max_y+d
        roof_z=self.roof_finished_top_z
        trim_top=roof_z+t-cap-self.end_gap
        for name,x,y,sx,sy in (("fl",xl,yf,1,1),("fr",xr,yf,-1,1),
                               ("bl",xl,yr,1,-1),("br",xr,yr,-1,-1)):
            z=self.ground_z(x,y)+self.ground_clearance
            # Outer dimensions of both legs are 40 mm, including thickness.
            cx=x-sx*t; cy=y-sy*t
            for j,(pos,size) in enumerate((
                ((cx if sx==1 else cx-leg,cy if sy==1 else cy-t,z),(leg,t,trim_top-z)),
                ((cx if sx==1 else cx-t,cy if sy==1 else cy-leg,z),(t,leg,trim_top-z))),1):
                parts.append(SidingPart(f"{self.name}_US20_corner_{name}_{j}","US20",pos,size,self.decking_color,
                    cut_length=trim_top-z if j==1 else None))
        # US20 top faces are trapezoids meeting on 45 degree corner miters.
        for name,start,size,poly in (
            ("front",(xl-t,yf-t,roof_z),(xr-xl+2*t,cap,t),((0,0),(xr-xl+2*t,0),(xr-xl+2*t-cap,cap),(cap,cap))),
            ("rear",(xl-t,yr+t-cap,roof_z),(xr-xl+2*t,cap,t),((cap,0),(xr-xl+2*t-cap,0),(xr-xl+2*t,cap),(0,cap))),
            ("left",(xl-t,yf-t,roof_z),(cap,yr-yf+2*t,t),((0,0),(cap,cap),(cap,yr-yf+2*t-cap),(0,yr-yf+2*t))),
            ("right",(xr+t-cap,yf-t,roof_z),(cap,yr-yf+2*t,t),((0,cap),(cap,0),(cap,yr-yf+2*t),(0,yr-yf+2*t-cap))),
        ):
            # Small separation at miters allows trim movement.
            cx=sum(x for x,y in poly)/4; cy=sum(y for x,y in poly)/4
            poly=tuple((x+math.copysign(self.end_gap/2,cx-x),y+math.copysign(self.end_gap/2,cy-y)) for x,y in poly)
            length=size[0] if name in ("front","rear") else size[1]
            parts.append(SidingPart(f"{self.name}_US20_{name}_top","US20",start,size,self.decking_color,
                cut_length=length,polygon=poly))
            pos,dim={
                "front":((xl-t,yf-t,roof_z+t-cap),(xr-xl+2*t,t,cap)),
                "rear":((xl-t,yr,roof_z+t-cap),(xr-xl+2*t,t,cap)),
                "left":((xl-t,yf,roof_z+t-cap),(t,yr-yf,cap)),
                "right":((xr,yf,roof_z+t-cap),(t,yr-yf,cap)),
            }[name]
            relief=()
            if name=="front" and self.front_trim_relief:
                a,b,z=self.front_trim_relief
                relief=(((a,pos[1]-0.01,pos[2]-0.01),(b-a,dim[1]+0.02,max(0,z-pos[2])+0.01)),)
            parts.append(SidingPart(f"{self.name}_US20_{name}_face","US20",pos,dim,self.decking_color,rebates=relief))
        # Applied L-angles: face overlaps siding, return points into opening.
        for name,x in (("left",self.rear_opening_min_x),("right",self.rear_opening_max_x)):
            z=self.ground_z(x,self.max_y)+self.ground_clearance
            length=self.rear_opening_top_z-z-self.end_gap
            face_x=x-leg+t if name=="left" else x-t
            return_x=x if name=="left" else x-t
            for j,(pos,size) in enumerate((
                ((face_x,yr,z),(leg,t,length)),
                ((return_x,yr+t-leg,z),(t,leg,length))),1):
                parts.append(SidingPart(f"{self.name}_US20_opening_{name}_{j}","US20",pos,size,self.decking_color,
                    cut_length=length if j==1 else None))
        z=self.rear_opening_top_z
        length=self.rear_opening_max_x-self.rear_opening_min_x
        # Jamb ends stop below the header return with movement clearance.
        for name,pos,size in (
            ("face",(self.rear_opening_min_x,yr,z),(length,t,leg)),
            ("return",(self.rear_opening_min_x,yr+t-leg,z),(length,leg,t)),
        ):
            parts.append(SidingPart(f"{self.name}_US20_opening_header_{name}","US20",pos,size,self.decking_color,
                cut_length=length if name=="face" else None))
        return tuple(parts)

    @cached_property
    def mesh_segments(self) -> tuple[tuple[str, str, float, float, float], ...]:
        """Name, wall orientation, along start/end, and actual fixed XY coordinate."""
        segments = []
        for wall in ("front", "left", "right", "rear"):
            spans = [self.span(wall)]
            if wall == "rear":
                spans = [(self.span(wall)[0], self.rear_opening_min_x),
                         (self.rear_opening_max_x, self.span(wall)[1])]
            for j, (a, b) in enumerate(spans, 1):
                x, y = self._mesh_xy(wall, a)
                segments.append((f"{wall}_{j}", wall, a, b, y if wall in ("front", "rear") else x))
        if self.front_infill_back_y is not None:
            segments.extend((
                ("inner_front_1", "front", self.min_x+3.5, self.max_x-3.5, self.front_infill_back_y),
                ("inner_left_1", "left", self.min_y+3.5, self.max_y-3.5, self.min_x+3.5),
                ("inner_right_1", "right", self.min_y+3.5, self.max_y-3.5, self.max_x-3.5-.025),
            ))
        return tuple(segment for segment in segments if segment[3] > segment[2])

    @property
    def mesh_purchase_length_in(self) -> float:
        # Allow one two-inch overlapped termination/joint for each cut strip.
        return sum(b-a+2 for _, _, a, b, _ in self.mesh_segments)

    @cached_property
    def mesh_parts(self) -> tuple[SidingPart,...]:
        parts = []
        for name, wall, a, b, normal in self.mesh_segments:
            front = wall in ("front", "rear")
            samples = [min(b, a+k*.25) for k in range(math.ceil((b-a)/.25)+1)]
            xy = [(s, normal) if front else (normal, s) for s in samples]
            grade = [self.ground_z(x, y) for x, y in xy]
            for k, ((x, y), z) in enumerate(zip(xy, grade)):
                parts.append(SidingPart(f"{self.name}_mesh_{name}_wire_{k}", "mesh",
                    (x,y,z-.25), (.025,.025,2), (.35,.36,.37,1)))
            for k in range(8):
                elevations = [z-.25+k*.25 for z in grade]
                z0 = min(elevations)
                size = (b-a,.025,max(elevations)-z0+.025) if front else (.025,b-a,max(elevations)-z0+.025)
                lower = tuple((s-a,z-z0) for s,z in zip(samples,elevations))
                upper = tuple((s-a,z-z0+.025) for s,z in reversed(tuple(zip(samples,elevations))))
                parts.append(SidingPart(f"{self.name}_mesh_{name}_horizontal_{k}", "mesh",
                    (*xy[0],z0), size, (.35,.36,.37,1), polygon=lower+upper, plane="xz" if front else "yz"))
        return tuple(parts)

    def _mesh_xy(self,wall: str,s: float) -> tuple[float,float]:
        x,y=self.xy(wall,s,outside=False)
        return {"front":(x,y),"rear":(x,y-0.025),
                "left":(x,y),"right":(x-0.025,y)}[wall]

    @cached_property
    def parts(self) -> tuple[SidingPart,...]:
        return self.backing_parts+self.board_parts+self.hardware_parts+self.angle_parts+self.mesh_parts

    @property
    def cut_lengths(self) -> tuple[float,...]:
        return tuple(p.cut_length for p in self.board_parts if p.cut_length is not None)

    def fabrication_rows(self) -> list[dict[str,Any]]:
        cuts={c.name:c for c in self.cuts}
        rows=[]
        for p in self.board_parts:
            if p.cut_length is None: continue
            cut=next((c for name,c in cuts.items() if p.name==name or p.name.startswith(name+"_piece_")),None)
            rows.append(dict(name=cut.name if cut else p.name,material="US135",length_in=p.cut_length,
                blank_width_in=self.board_width,finished_width_in="scribe/profile",thickness_in=self.board_thickness,
                course=cut.course if cut else int(p.name.rsplit('_',1)[1]),
                wall=cut.wall if cut else "roof",bottom_edge=list(cut.bottom_edge) if cut else [],
                operation="rear opening notch" if cut and cut.notched else "scribe/rip bottom" if cut and any(z>cut.bottom+1e-8 for _,z in cut.bottom_edge) else "crosscut",
                kerf_allowance_in=self.kerf))
        for p in (*self.backing_parts,*self.angle_parts):
            if p.cut_length is not None:
                if p in self.infill_parts:
                    rows.append(dict(name=p.name,material=p.material,length_in=p.size[2],
                        blank_width_in=48,finished_width_in=p.size[0] if p.plane=="xz" else p.size[1],
                        thickness_in=.75,course="",wall=p.name.split("_infill_")[1].split("_")[0],
                        bottom_edge=list(p.polygon[:2]),operation="field fit between framing; scribe grade; predrill toe screws" + "".join(f"; snug bore {b.diameter:g} in at X={b.center_x:g}, Z={b.center_z:g}; seal residual seam" for b in p.front_bores),kerf_allowance_in=self.kerf))
                    continue
                if p.material==ROOF_STRIP_MATERIAL:
                    course=int(p.name.rsplit('_',2)[1])
                    rows.append(dict(name=p.name,material=p.material,length_in=p.cut_length,
                        blank_width_in=48,finished_width_in=p.size[1],thickness_in=p.size[2],
                        course=course,wall="roof",bottom_edge=[],
                        operation=f"rip strength axis along X; end cutouts for gussets; X={p.start[0]:.4f}..{p.start[0]+p.size[0]:.4f}; Y={p.start[1]:.4f}..{p.start[1]+p.size[1]:.4f}",
                        kerf_allowance_in=self.kerf))
                    continue
                width=p.size[0] if "backing_front" in p.name else p.size[1]
                rows.append(dict(name=p.name,material=p.material,length_in=p.cut_length,
                    blank_width_in=5.5 if p.material.startswith("PT_") else "",
                    finished_width_in=width if p.material=="PT_5/4x6_backing" else "profile",
                    thickness_in=1 if p.material=="PT_5/4x6_backing" else "profile",
                    course="",wall="",bottom_edge=[],operation="field fit / notch" if "backing" in p.material else "profile / miter",kerf_allowance_in=self.kerf))
        return rows

    def bom_rows(self) -> list[dict[str,Any]]:
        rows=[]
        groups={"US135":self.board_parts,"US20":self.angle_parts,
                "PT_5/4x6_backing":self.backing_parts}
        for material,parts in groups.items():
            lengths=tuple(p.cut_length for p in parts if p.material==material and p.cut_length is not None)
            if not lengths: continue
            stock=self.stock_length if material=="US135" else 96
            qty=minimum_stock_board_count(tuple(x+self.kerf for x in lengths),stock)
            rows.append(dict(category="siding",assembly=self.assembly,name=f"{self.name}_{material}",
                type=f"{material}; 1/8 in kerf per cut",qty=len(lengths),length_in=round(sum(lengths),4),
                total_linear_ft=round(sum(lengths)/12,4),stock_length_ft=stock/12,stock_board_qty=qty))
        for stock, count in self.plywood_layout["purchases"].items():
            if not count:
                continue
            rows.append(dict(category="sheet",assembly=self.assembly,
                name=f"{self.name}_{ROOF_STRIP_MATERIAL}" + ("_2x4" if stock=="2x4" else ""),
                type=f"3/4 in PT exterior structural plywood; {stock} ft panel; shared roof-strip and wall-infill cutting layout",
                qty=sum(1 for cut in self.plywood_layout["cuts"] if (self.plywood_layout["sheets"][cut["sheet"]-1]["width_in"]==48) == (stock=="2x4")),stock_board_qty=count))
        for name,description,qty in (
            ("infill_toe_screws","PT-compatible exterior screws; predrill angled panel-face entries into adjacent lumber; field-select length; allowance four per panel",4*len(self.infill_parts)),
            ("face_screws","#8 x 1-1/4 in SS304 composite face screw into lumber; one fixed point per board, other holes oversized and free to slide",sum(a.wall!="roof" for a in self.attachments)),
            ("roof_face_screws","Provisional #8 x 7/8 in stainless retaining-head screw into plywood only; through recessed overlap; nominal 5/8 in penetration; verify head clearance and sliding retention",sum(a.wall=="roof" for a in self.attachments)),
            ("roof_strip_anchors","Corrosion-resistant framing screws; recess heads flush in plywood; field-select length and substrate penetration",len(self.roof_strip_anchors)),
            ("trim_screws","#8 x 2 in SS304 trim screw through US20/board into lumber; predrill for independent board and trim movement",sum(2+math.ceil(p.cut_length/24) for p in self.angle_parts if p.cut_length and not p.name.endswith("_top"))),
            ("roof_trim_screws","#8 x 2-1/2 in stainless roof trim screw through US20/board/plywood into framing; allow independent movement",sum(2+math.ceil(p.cut_length/24) for p in self.angle_parts if p.cut_length and p.name.endswith("_top"))),
            ("backing_brackets","Stainless backing attachment angle, two at each end; field-select structural screws",4*sum(p.material=="PT_5/4x6_backing" for p in self.backing_parts)),
        ):
            rows.append(dict(category="hardware",assembly=self.assembly,name=f"{self.name}_{name}",type=description,qty=qty))
        rows.append(dict(category="siding",assembly=self.assembly,name=f"{self.name}_mesh",type="1/4 in corrosion-resistant hardware cloth; cut 2 in skirt, overlap joints 2 in; framing staples",qty=1,total_linear_ft=math.ceil(self.mesh_purchase_length_in/12)))
        # Keep the shared BOM CSV schema used by lumber and purchased parts.
        template=dict.fromkeys(CompositeSiding.bom_rows(self)[0], "")
        return [{**template,**row} for row in rows]

    def purchase_bom_rows(self) -> list[dict[str,Any]]:
        """Siding-only purchase snapshot, using the same quantities as the model."""
        notes={
            "US135":"Walls and roof cover; direct face fastening without clips or stand-off. Provisional 130 mm course pitch; sample-fit before cutting.",
            "US20":"Four outside corners, two rear jambs, one rear header and four roof edges. Applied L-angle; front fixture relief required.",
            "PT_5/4x6_backing":"Verified actual 1 in thickness; rip to 3-1/2 in and field-fit segments around existing framing.",
            ROOF_STRIP_MATERIAL:"Shared guillotine cut plan in plywood_layout.json/svg; 1/8 in kerf; reuse sheet remainder for fitted wall panels. Roof strips follow strength axis. Field-fit and treat cut edges.",
            ROOF_STRIP_MATERIAL+"_2x4":"Supplemental 2 x 4 ft panel; same grade/thickness/treatment as full sheet; see shared cut layout.",
            "infill_toe_screws":"Four per panel purchase allowance; predrill from accessible interior panel face toward neighboring timber. Field-select length/angle for contained tips and sound lumber engagement; do not screw into plywood edges.",
            "roof_face_screws":"Roof only. One recessed low-Y row, concealed rear-to-front; one midpoint fixed connection per board; all others slide. Tip stays within plywood; verify production stack and usable thread engagement. Custom unverified connection.",
            "roof_strip_anchors":"Two end anchors per strip at generated framing-supported locations; independent of siding screws. Countersink into plywood only, flush below siding.",
            "face_screws":"Walls only. One per generated wall attachment. One concealed overlap row on intact courses; local cut/termination exceptions; one fixed point per physical board and sliding holes elsewhere. Custom schedule, not load-verified.",
            "roof_trim_screws":"Roof horizontal legs only. Added 1/2 in length preserves former nominal framing penetration through the thicker stack. Verify framing landing and independent movement.",
            "trim_screws":"Wall and vertical trim allowance; verify backing, penetration and independent movement of trim and underlying siding.",
            "backing_brackets":"Four per backing segment; field-select hardware and structural screws for each actual joint.",
            "mesh":"Exterior skirt plus inner side-wall/front-cavity wrap; 2 in strips with 1/4 in openings and 2 in joint overlaps; staple independently to framing.",
        }
        rows=[]
        for row in self.bom_rows():
            item=row["name"].removeprefix(self.name+"_")
            stock=row.get("stock_board_qty")
            mesh=item=="mesh"
            note=notes[item]
            if stock and not item.startswith(ROOF_STRIP_MATERIAL):
                note+=" Calculated stock minimum includes 1/8 in kerf per cut and offcut reuse; no damage/contingency allowance."
            rows.append(dict(item=item,description=row["type"],
                quantity=stock if stock else row["total_linear_ft"] if mesh else row["qty"],
                unit="2 x 4 ft panels" if item==ROOF_STRIP_MATERIAL+"_2x4" else "4 x 8 ft sheets" if item==ROOF_STRIP_MATERIAL else "stock pieces" if stock else "linear ft of 2 in strip" if mesh else "each",
                stock_length_ft=row.get("stock_length_ft","") if stock else "",
                finished_cut_count=row["qty"] if stock else "",
                finished_total_linear_ft=row.get("total_linear_ft","") if stock or mesh else "",
                notes=note,source_commits=""))
        for item,description in (
            ("backing_structural_screws","Corrosion-resistant structural screws for backing angles"),
            ("mesh_staples","Corrosion-resistant framing staples for hardware cloth"),
        ):
            rows.append(dict(item=item,description=description,quantity="TBD",unit="each",
                stock_length_ft="",finished_cut_count="",finished_total_linear_ft="",
                notes="Required; field-select for actual attachment hardware and framing.",source_commits=""))
        return rows

    def write_artifacts(self, directory: Any) -> None:
        import csv
        import json
        from dataclasses import asdict
        from pathlib import Path
        directory=Path(directory)
        from lumber_model.plywood import write_layout
        write_layout(self.plywood_layout, directory)
        purchases=self.purchase_bom_rows()
        with (directory/"siding_bom.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(purchases[0]),lineterminator="\n")
            writer.writeheader()
            writer.writerows(purchases)
        rows=self.fabrication_rows()
        (directory/"siding_cut_list.json").write_text(json.dumps(rows,indent=2)+"\n")
        with (directory/"siding_cut_list.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({**r,"bottom_edge":json.dumps(r["bottom_edge"])} for r in rows)
        manifest={
            "product":"US135", "product_line":"All Weather Pro",
            "units":"inches", "wall_installation":"top downward; temporary framing-mounted padded supports",
            "physical_dry_fit_status":"NOT PERFORMED: verify inverted engagement, overlap material, head clearance, retention and sliding holes",
            "wall_orientation":"inverted; finished face outward",
            "wall_screw_row_offset_in":(self.board_width-self.course_pitch)/2,
            "wall_screw_row_status":"provisional overlap midpoint; not a drilling dimension",
            "head_clearance_status":"schematic head envelopes may intersect the simplified covering tongue; production clearance unverified; no machining relief specified",
            "wall_drainage_tradeoff":"small inverted-joint water-retention gap accepted for desert climate",
            "attachment_method":"custom direct face fastening to open lumber framing; inverted wall profiles, one concealed lower-overlap row with local exceptions; not a manufacturer-approved replacement for AW08",
            "trim_method":"applied US20 at four outside corners, rear opening and roof edges; corners stop below roof trim",
            "ventilation_status":"Side infill closes the inner wall cavities; front infill closes the rail rear plane below the header; upper strip stays forward for handle clearance; preserve screened drainage paths",
            "course_pitch_in":self.course_pitch, "course_pitch_status":"provisional 130 mm; verify two engaged samples before cutting",
            "board_profile_width_in":self.board_width, "board_thickness_in":self.board_thickness,
            "board_standoff_in":0.0, "ground_clearance_in":self.ground_clearance,
            "end_gap_in":self.end_gap, "gap_design_envelope":"32 F or warmer, components no longer than 8 ft; field-check guide table",
            "roof_strip_thickness_in":self.roof_strip_thickness,
            "roof_strip_width_in":self.roof_strip_width,
            "roof_support_z":self.roof_support_z,
            "roof_finished_top_z":self.roof_finished_top_z,
            "wall_infill":[dict(name=p.name,start_in=p.start,size_in=p.size,polygon=p.polygon,bores=[dict(name=b.name,center_x_in=b.center_x,center_z_in=b.center_z,diameter_in=b.diameter) for b in p.front_bores]) for p in self.infill_parts],
            "animal_infill_alignment":"Side panels flush with inside post faces; front animal panels below header rear-face flush with front_center_rail; upper strip stays at inside front-post plane",
            "front_infill_back_y_in":self.front_infill_back_y,
            "front_infill_header_top_z_in":self.front_infill_header_top_z,
            "mesh_segments":[dict(name=n,wall=w,start_in=a,end_in=b,normal_in=c) for n,w,a,b,c in self.mesh_segments],
            "mesh_purchase_length_in":self.mesh_purchase_length_in,
            "address_backing_exterior_setback_in":.25,
            "infill_toe_entries":self.infill_toe_entries,
            "infill_attachment":"Predrilled toe screws from panel face into bordering timber; four per panel allowance; field-select final positions, angle and length",
            "ceiling":"omitted entirely for future tambour access",
            "roof_strips":[dict(name=p.name,start_in=p.start,size_in=p.size,
                strength_axis="X",gusset_clearance_in=self.roof_hardware_clearance) for p in self.roof_strips],
            "roof_strip_anchors":[asdict(a) for a in self.roof_strip_anchors],
            "roof_drainage":"Open channels between continuous strips; clear tongue/groove rebates and gusset outlets. Final narrow course has one backer. No transverse cuts through load-bearing strips.",
            "roof_installation_order":[p.name for p in reversed(self.board_parts) if "_top_" in p.name],
            "roof_fastener_status":"Provisional #8 x 7/8 in through nominal 1/4 in recessed overlap; nominal 5/8 in plywood penetration; contained tip, thread engagement and head retention require production dry fit",
            "roof_status":"level cover allowing leakage; snow/wind/load capacity not established by siding or ceiling guide",
            "geometry_status":"simplified mating rebates and hardware/trim envelopes, not machining CAD",
            "attachments":[asdict(a) for a in self.attachments],
            "courses_top_down":[{"course":i,"bottom_z":b,"top_z":t} for i,(b,t) in enumerate(self.courses,1)],
        }
        (directory/"siding_installation.json").write_text(json.dumps(manifest,indent=2)+"\n")
        # Crop the actual roof framing, gussets and plywood strips.
        review=("// Roof support review. Render with openscad -D build_step=22.\n"
                "use <model.scad>\nintersection() {\n  render_model();\n"
                f"  translate([{self.min_x-1}, {self.min_y-1}, {self.frame_top_z-1.75}]) "
                f"cube([{self.max_x-self.min_x+2}, {self.max_y-self.min_y+2}, 4]);\n}}\n")
        (directory/"roof_support_review.scad").write_text(review)
        for name,x,y in (("front_left",self.min_x,self.min_y),("front_right",self.max_x,self.min_y),
                         ("rear_left",self.min_x,self.max_y),("rear_right",self.max_x,self.max_y)):
            text='// Inches. Custom trim junction; schematic profiles.\nuse <model.scad>\n'
            text+='intersection() {\n  union() {\n'
            for p in self.parts:
                if p.start[0]<=x+5 and p.start[0]+p.size[0]>=x-5 and p.start[1]<=y+5 and p.start[1]+p.size[1]>=y-5 and p.start[2]+p.size[2]>=self.frame_top_z-6:
                    text+=f"    render_siding_part({p.scad_record()});\n"
            for loc,size in self.framing:
                if loc[2]+size[2]>=self.frame_top_z-6:
                    text+=f"    color([0.44,0.26,0.11]) translate({list(loc)}) cube({list(size)});\n"
            text+='  }\n'
            text+=f"  translate([{x-5}, {y-5}, {self.frame_top_z-6}]) cube([10,10,9]);\n}}\n"
            (directory/f"siding_corner_{name}.scad").write_text(text)
