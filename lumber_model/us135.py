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
    CompositeSiding, SidingPart, _subtract_front_opening, _subtract_right_opening,
    minimum_stock_board_count,
)

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
    diagonal: tuple[tuple[float, float], ...] = ()
    front_trim_relief: tuple[float,float,float] | None = None  # x min/max, clear-above Z

    def __post_init__(self) -> None:
        super().__post_init__()
        for value in (self.course_pitch, self.ground_clearance,
                      self.end_gap, self.kerf):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("US135 layout dimensions must be finite and positive")
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
            rebates=(((x,inner,cut.bottom),(dx,t/2,lap)),
                     ((x,outer,cut.top-lap),(dx,t/2,lap)))
        else:
            outer=x if cut.wall=="left" else x+t/2
            inner=x+t/2 if cut.wall=="left" else x
            rebates=(((inner,y,cut.bottom),(t/2,dy,lap)),
                     ((outer,y,cut.top-lap),(t/2,dy,lap)))
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
        stations=list(self._stations(a+1.6875,b-1.6875,16))
        if wall=="right":
            stations.extend(s for o in self.right_openings for s in (o.min_y-0.5,o.max_y+0.5) if a<=s<=b)
        if wall=="front":
            stations.extend(s for o in self.front_openings for s in (o.min_x-0.5,o.max_x+0.5) if a<=s<=b)
        return tuple(sorted(set(stations)))

    @property
    def roof_stations(self) -> tuple[float,...]:
        return self._stations(self.min_x+1.75,self.max_x-1.75,10)

    @cached_property
    def backing_parts(self) -> tuple[SidingPart,...]:
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
            for j,s in enumerate(self.wall_stations(wall)[1:-1],1):
                wa,wb=(self.min_x,self.max_x) if wall=="front" else (self.min_y,self.max_y)
                if s <= wa+3.5 or s >= wb-3.5:
                    continue  # already backed by a corner post
                a=max(wa+3.5,s-1.75); b=min(wb-3.5,s+1.75)
                z = self.ground_z(*self.xy(wall,s))+self.ground_clearance
                start,size = {
                    "front": ((a,self.min_y,z),(b-a,1,self.frame_top_z-z)),
                    "left": ((self.min_x,a,z),(1,b-a,self.frame_top_z-z)),
                    "right": ((self.max_x-1,a,z),(1,b-a,self.frame_top_z-z)),
                }[wall]
                add_notched(f"backing_{wall}_{j}",start,size,2)
        for i,x in enumerate(self.roof_stations[1:-1],1):
            start=(x-1.75,self.min_y,self.roof_support_z-1)
            size=(3.5,self.max_y-self.min_y,1)
            slab=clip_polygon_to_box(self.diagonal,min_x=x-1.75,max_x=x+1.75,
                min_y=self.min_y,max_y=self.max_y) if self.diagonal else ()
            extra=()
            if slab:
                ya=min(y for _,y in slab); yb=max(y for _,y in slab)
                extra=(((x-1.75,ya,self.frame_top_z-0.75),(3.5,yb-ya,0.75)),)
            add_notched(f"backing_roof_{i}",start,size,1,extra)
        if self.diagonal:
            # Stop short of both gussets; the perimeter shims support the ends.
            poly=clip_polygon_to_box(self.diagonal,min_x=self.min_x+6.25,max_x=self.max_x-6.25,
                min_y=self.min_y+3.5,max_y=self.max_y-3.5)
            if len(poly)>=3:
                x0=min(x for x,y in poly); y0=min(y for x,y in poly)
                edge=max(((b[0]-a[0],b[1]-a[1]) for a,b in
                    zip(self.diagonal,self.diagonal[1:]+self.diagonal[:1])),key=lambda d:math.hypot(*d))
                norm=math.hypot(*edge)
                projected=[(x*edge[0]+y*edge[1])/norm for x,y in poly]
                parts.append(SidingPart(f"{self.name}_diagonal_shim","PT_roof_shim",
                    (x0,y0,self.frame_top_z),(max(x for x,y in poly)-x0,max(y for x,y in poly)-y0,
                     self.roof_support_z-self.frame_top_z),(0.44,0.26,0.11,1),
                    cut_length=max(projected)-min(projected),
                    polygon=tuple((x-x0,y-y0) for x,y in poly)))
        return tuple(parts)

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

    @cached_property
    def attachments(self) -> tuple[Attachment,...]:
        result=[]
        # Two face-screw rows retain both edges without relying on clip grooves.
        # Stay beyond the simplified tongue/rebate region. A scribed narrow
        # remainder gets a single centered row instead of an off-board screw.
        for cut in self.cuts:
            stations=[s for s in self.wall_stations(cut.wall) if cut.start<=s<=cut.end]
            midpoint=(cut.start+cut.end)/2
            stations.append(midpoint)
            candidates=[]
            for station in sorted(set(stations)):
                bottom=max(cut.bottom,self.ground_z(*self.xy(cut.wall,station))+self.ground_clearance)
                if cut.notched and self.rear_opening_min_x-self.end_gap<=station<=self.rear_opening_max_x+self.end_gap:
                    bottom=max(bottom,self.rear_opening_top_z+self.end_gap)
                height=cut.top-bottom
                if height<=0: continue
                elevations=(bottom+0.75,cut.top-0.75) if height>1.5 else ((bottom+cut.top)/2,)
                for z in sorted(set(elevations)):
                    openings=self.front_openings if cut.wall=="front" else self.right_openings if cut.wall=="right" else ()
                    if any((o.min_x if cut.wall=="front" else o.min_y)<=station<=
                           (o.max_x if cut.wall=="front" else o.max_y) and o.bottom_z<=z<=o.top_z
                           for o in openings):
                        continue
                    if self._surface_supported(cut.wall,station,z):
                        candidates.append(Attachment(cut.name,cut.wall,station,z,"face_screw"))
            if not candidates:
                raise ValueError(f"{cut.name}: no supported face fastening")
            # Header screw fixes the single notched rear board; its wings slide.
            fixed=min(candidates,key=lambda a:(abs(a.along-midpoint),-a.elevation))
            result.extend(replace(a,locked=a==fixed) for a in candidates)
        for part in self.board_parts:
            if "_top_" not in part.name: continue
            width=part.size[1]
            rows=(part.start[1]+0.75,part.start[1]+width-0.75) if width>1.5 else (part.start[1]+width/2,)
            candidates=[]
            for y in sorted(set(rows)):
                stations=list(self.roof_stations)
                shim=next((p for p in self.backing_parts if p.material=="PT_roof_shim"),None)
                if shim:
                    hits=[]
                    poly=[(x+shim.start[0],v+shim.start[1]) for x,v in shim.polygon]
                    for (x1,y1),(x2,y2) in zip(poly,poly[1:]+poly[:1]):
                        if min(y1,y2)<=y<=max(y1,y2) and abs(y2-y1)>1e-8:
                            hits.append(x1+(x2-x1)*(y-y1)/(y2-y1))
                    if len(hits)>=2:
                        stations.extend((min(hits)+0.375,(min(hits)+max(hits))/2,max(hits)-0.375))
                candidates.extend(Attachment(part.name,"roof",x,y,"face_screw")
                    for x in sorted(set(stations))
                    if part.start[0]+0.75<=x<=part.start[0]+part.size[0]-0.75 and self._roof_supported(x,y))
            if not candidates:
                raise ValueError(f"{part.name}: no roof attachment support")
            fixed=min(candidates,key=lambda a:abs(a.along-(self.min_x+self.max_x)/2))
            result.extend(replace(a,locked=a==fixed) for a in candidates)
        return tuple(result)

    def _roof_supported(self,x: float,y: float) -> bool:
        for loc,size in self.framing:
            if abs(loc[2]+size[2]-self.frame_top_z)<1e-6 and loc[0]<=x<=loc[0]+size[0] and loc[1]<=y<=loc[1]+size[1]:
                return True
        for p in self.backing_parts:
            if abs(p.start[2]+p.size[2]-self.roof_support_z)>1e-6: continue
            if p.start[0]<=x<=p.start[0]+p.size[0] and p.start[1]<=y<=p.start[1]+p.size[1]:
                if not p.polygon: return True
                poly=[(a+p.start[0],b+p.start[1]) for a,b in p.polygon]
                if all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=-1e-8 for a,b in zip(poly,poly[1:]+poly[:1])):
                    return True
        return False

    @cached_property
    def hardware_parts(self) -> tuple[SidingPart,...]:
        parts=[]
        # Schematic exposed screw heads; shanks and movement bores are not CAD.
        head=0.25; height=0.08
        for i,a in enumerate(self.attachments,1):
            if a.wall=="roof":
                start=(a.along-head/2,a.elevation-head/2,self.roof_finished_top_z)
                size=(head,head,height)
            else:
                x,y=self.xy(a.wall,a.along)
                start,size={
                    "front":((x-head/2,y-height,a.elevation-head/2),(head,height,head)),
                    "rear":((x-head/2,y,a.elevation-head/2),(head,height,head)),
                    "left":((x-height,y-head/2,a.elevation-head/2),(height,head,head)),
                    "right":((x,y-head/2,a.elevation-head/2),(height,head,head)),
                }[a.wall]
            parts.append(SidingPart(f"{a.board}_face_screw_{i}","face_screw",start,size,
                (0.85,0.62,0.12,1) if a.locked else (0.45,0.48,0.5,1)))
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
    def mesh_parts(self) -> tuple[SidingPart,...]:
        parts=[]
        for wall in ("front","left","right","rear"):
            spans=[self.span(wall)]
            if wall=="rear":
                spans=[(self.span(wall)[0],self.rear_opening_min_x),(self.rear_opening_max_x,self.span(wall)[1])]
            for j,(a,b) in enumerate(spans,1):
                # Render real 1/4-inch openings, not a ventilation-blocking slab.
                n=math.ceil((b-a)/0.25)
                for k in range(n+1):
                    s=min(b,a+k*0.25); z=self.ground_z(*self.xy(wall,s))
                    x,y=self._mesh_xy(wall,s)
                    parts.append(SidingPart(f"{self.name}_mesh_{wall}_{j}_wire_{k}","mesh",
                        (x,y,z-0.25),(0.025,0.025,2),(0.35,0.36,0.37,1)))
                for k in range(8):
                    edge=tuple((s,self.ground_z(*self.xy(wall,s))-0.25+k*0.25) for s in (a,b))
                    z0=min(z for s,z in edge)
                    x,y=self._mesh_xy(wall,a)
                    if wall in ("front","rear"):
                        size=(b-a,0.025,max(z for s,z in edge)-z0+0.025); plane="xz"
                    else:
                        size=(0.025,b-a,max(z for s,z in edge)-z0+0.025); plane="yz"
                    poly=((0,edge[0][1]-z0),(b-a,edge[1][1]-z0),(b-a,edge[1][1]-z0+0.025),(0,edge[0][1]-z0+0.025))
                    parts.append(SidingPart(f"{self.name}_mesh_{wall}_{j}_horizontal_{k}","mesh",(x,y,z0),size,(0.35,0.36,0.37,1),polygon=poly,plane=plane))
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
                width=p.size[0] if "backing_front" in p.name or "backing_roof" in p.name else p.size[1]
                rows.append(dict(name=p.name,material=p.material,length_in=p.cut_length,
                    blank_width_in=5.5 if p.material.startswith("PT_") else "",
                    finished_width_in=width if p.material=="PT_5/4x6_backing" else "profile",
                    thickness_in=1 if p.material=="PT_5/4x6_backing" else self.roof_support_z-self.frame_top_z if p.material=="PT_roof_shim" else "profile",
                    course="",wall="",bottom_edge=[],operation="field fit / notch" if "backing" in p.material else "profile / miter",kerf_allowance_in=self.kerf))
        return rows

    def bom_rows(self) -> list[dict[str,Any]]:
        rows=[]
        groups={"US135":self.board_parts,"US20":self.angle_parts,
                "PT_5/4x6_backing":self.backing_parts,"PT_roof_shim":self.backing_parts}
        for material,parts in groups.items():
            lengths=tuple(p.cut_length for p in parts if p.material==material and p.cut_length is not None)
            if not lengths: continue
            stock=self.stock_length if material=="US135" else 96
            qty=minimum_stock_board_count(tuple(x+self.kerf for x in lengths),stock)
            rows.append(dict(category="siding",assembly=self.assembly,name=f"{self.name}_{material}",
                type=f"{material}; 1/8 in kerf per cut",qty=len(lengths),length_in=round(sum(lengths),4),
                total_linear_ft=round(sum(lengths)/12,4),stock_length_ft=stock/12,stock_board_qty=qty))
        for name,description,qty in (
            ("face_screws","#8 x 1-1/4 in SS304 composite face screw into lumber; one fixed point per board, other holes oversized and free to slide",len(self.attachments)),
            ("trim_screws","#8 x 2 in SS304 trim screw through US20/board into lumber; predrill for independent board and trim movement",sum(2+math.ceil(p.cut_length/24) for p in self.angle_parts if p.cut_length)),
            ("backing_brackets","Stainless backing attachment angle, two at each end; field-select structural screws",4*sum(p.material=="PT_5/4x6_backing" for p in self.backing_parts)),
        ):
            rows.append(dict(category="hardware",assembly=self.assembly,name=f"{self.name}_{name}",type=description,qty=qty))
        perimeter=2*(self.max_x-self.min_x+self.max_y-self.min_y)-(self.rear_opening_max_x-self.rear_opening_min_x)
        rows.append(dict(category="siding",assembly=self.assembly,name=f"{self.name}_mesh",type="1/4 in corrosion-resistant hardware cloth; cut 2 in skirt, overlap joints 2 in; framing staples",qty=1,total_linear_ft=math.ceil((perimeter+10)/12)))
        # Keep the shared BOM CSV schema used by lumber and purchased parts.
        template=dict.fromkeys(CompositeSiding.bom_rows(self)[0], "")
        return [{**template,**row} for row in rows]

    def purchase_bom_rows(self) -> list[dict[str,Any]]:
        """Siding-only purchase snapshot, using the same quantities as the model."""
        notes={
            "US135":"Walls and roof cover; direct face fastening without clips or stand-off. Provisional 130 mm course pitch; sample-fit before cutting.",
            "US20":"Four outside corners, two rear jambs, one rear header and four roof edges. Applied L-angle; front fixture relief required.",
            "PT_5/4x6_backing":"Verified actual 1 in thickness; rip to 3-1/2 in and field-fit segments around existing framing.",
            "PT_roof_shim":"Added diagonal shim only, 1/4 in thick; existing perimeter shims excluded. Suitable offcut may replace dedicated stock.",
            "face_screws":"One per generated board attachment. Two rows where width permits; one fixed point per physical board and sliding holes elsewhere. Custom schedule, not load-verified.",
            "trim_screws":"Modeled allowance; verify backing, penetration and independent movement of trim and underlying siding.",
            "backing_brackets":"Four per backing segment; field-select hardware and structural screws for each actual joint.",
            "mesh":"2 in skirt with 1/4 in openings and 2 in joint overlaps; staple independently to framing.",
        }
        rows=[]
        for row in self.bom_rows():
            item=row["name"].removeprefix(self.name+"_")
            stock=row.get("stock_board_qty")
            mesh=item=="mesh"
            note=notes[item]
            if stock:
                note+=" Calculated stock minimum includes 1/8 in kerf per cut and offcut reuse; no damage/contingency allowance."
            rows.append(dict(item=item,description=row["type"],
                quantity=stock if stock else row["total_linear_ft"] if mesh else row["qty"],
                unit="stock pieces" if stock else "linear ft of 2 in strip" if mesh else "each",
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
            "physical_dry_fit_status":"NOT PERFORMED: verify direct seating, two-course engagement, face-screw retention and sliding holes",
            "attachment_method":"custom direct face fastening to open lumber framing; two rows where board width permits; not a manufacturer-approved replacement for AW08",
            "trim_method":"applied US20 at four outside corners, rear opening and roof edges; corners stop below roof trim",
            "ventilation_status":"verify unobstructed 1 inch net free airflow behind open framing; no clip-created stand-off",
            "course_pitch_in":self.course_pitch, "course_pitch_status":"provisional 130 mm; verify two engaged samples before cutting",
            "board_profile_width_in":self.board_width, "board_thickness_in":self.board_thickness,
            "board_standoff_in":0.0, "ground_clearance_in":self.ground_clearance,
            "end_gap_in":self.end_gap, "gap_design_envelope":"32 F or warmer, components no longer than 8 ft; field-check guide table",
            "roof_status":"level cover allowing leakage; snow/wind/load capacity not established by siding or ceiling guide",
            "geometry_status":"simplified mating rebates and hardware/trim envelopes, not machining CAD",
            "attachments":[asdict(a) for a in self.attachments],
            "courses_top_down":[{"course":i,"bottom_z":b,"top_z":t} for i,(b,t) in enumerate(self.courses,1)],
        }
        (directory/"siding_installation.json").write_text(json.dumps(manifest,indent=2)+"\n")
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
