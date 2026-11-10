"""Standalone enclosed US20 slip-socket elbow. All dimensions are millimetres.

Conservative ink-print estimates, not manufacturing CAD. Fit requires offcut tests;
the travel target is not a thermal expansion specification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class CornerSpec:
    leg: float = 42.0
    thickness: float = 10.0
    length: float = 68.0
    wall: float = 2.0
    clearance: float = 0.75
    outside_bend_radius: float = 2.0
    inside_bend_radius: float = 4.0
    end_radius: float = 4.0
    travel: float = 3.2
    miter_gap: float = 6.0  # Perpendicular distance between the two cut planes.

    def __post_init__(self):
        if any(not math.isfinite(v) or v <= 0 for v in asdict(self).values()):
            raise ValueError('All dimensions must be finite and positive')
        if self.thickness+2*self.outer >= self.leg:
            raise ValueError('Profile thickness and shell consume the inside leg')
        if 2*self.end_radius > self.thickness:
            raise ValueError('Free-end radii exceed the reference thickness')
        if self.outside_bend_radius > self.thickness:
            raise ValueError('Outside bend radius exceeds the reference thickness')
        if self.thickness+self.inside_bend_radius+self.end_radius >= self.leg:
            raise ValueError('Bend and end radii consume the straight inside leg')
        if self.miter_gap <= math.sqrt(2)*self.travel:
            raise ValueError('Miter ends collide at the simultaneous travel limit')
        if self.minimum_engagement < 17:
            raise ValueError('At least 17 mm of full-profile engagement is required')

    @property
    def outer(self):
        """Space occupied beyond each nominal trim surface, including clearance."""
        return self.clearance+self.wall

    @property
    def minimum_engagement(self):
        start = max(self.leg+self.outer,
                    self.leg+self.miter_gap/math.sqrt(2)+self.travel)
        return self.length-start


def _box(x, y, z, dx, dy, dz):
    from build123d import Align, Box, Location
    return Location((x, y, z))*Box(dx, dy, dz, align=(Align.MIN,)*3)


def _swap(shape):
    from build123d import Plane
    return shape.mirror(Plane((0, 0, 0), (1, 1, 0), (1, -1, 0)))


def _profile_segments(s: CornerSpec, margin: float = 0):
    """Exact tangent lines/arcs of an outward-offset rounded L in local XY.

    Convex radii grow and the concave radius shrinks with the offset. Centres
    remain fixed until a concave arc disappears; it then becomes a sharp inside
    corner. Entries are (start, midpoint-or-None, end, radius-or-None).
    """
    if not math.isfinite(margin) or margin < 0:
        raise ValueError('Profile offset must be finite and nonnegative')
    w, t = s.leg+2*margin, s.thickness+2*margin
    ro, re = s.outside_bend_radius+margin, s.end_radius+margin
    ri = max(0, s.inside_bend_radius-margin)
    cursor = (ro, 0)
    segments = []

    def shifted(point):
        return tuple(v-margin for v in point)

    def line(end):
        nonlocal cursor
        if math.dist(cursor, end) > 1e-8:
            segments.append((shifted(cursor), None, shifted(end), None))
        cursor = end

    def arc(center, radius, angle, end):
        nonlocal cursor
        middle = (center[0]+radius*math.cos(math.radians(angle)),
                  center[1]+radius*math.sin(math.radians(angle)))
        segments.append((shifted(cursor), shifted(middle), shifted(end), radius))
        cursor = end

    line((w-re, 0))
    arc((w-re, re), re, -45, (w, re))
    line((w, t-re))
    arc((w-re, t-re), re, 45, (w-re, t))
    line((t+ri, t))
    if ri:
        arc((t+ri, t+ri), ri, -135, (t, t+ri))
    line((t, w-re))
    arc((t-re, w-re), re, 45, (t-re, w))
    line((re, w))
    arc((re, w-re), re, 135, (0, w-re))
    line((0, ro))
    arc((ro, ro), ro, 225, (ro, 0))
    return segments


def _profile_prism(s: CornerSpec, margin: float, start: float, length: float):
    """Rounded offset profile along +X; mirror X/Y for the other socket."""
    from build123d import Edge, Face, Wire, extrude

    def installed(p):
        return (start, p[0], -p[1])

    edges = [Edge.make_line(installed(a), installed(b)) if mid is None else
             Edge.make_three_point_arc(installed(a), installed(mid), installed(b))
             for a, mid, b, _ in _profile_segments(s, margin)]
    return extrude(Face(Wire(edges)), amount=length, dir=(1, 0, 0))


def _elbow_prism(s: CornerSpec, margin: float, overrun: float = 0):
    """Join matching rounded sweeps on X=Y, without overlapping end bulges."""
    from build123d import Plane, Polygon, extrude
    sweep = _profile_prism(s, margin, -margin, s.length+margin+overrun)
    lo, hi = -margin-1, s.length+overrun+1
    half_plane = Plane.XY*Polygon((lo, lo), (hi, lo), (hi, hi), align=None)
    clip = extrude(half_plane, amount=s.leg+2*margin+2).translate(
        (0, 0, -s.leg-margin-1))
    mitered = sweep & clip
    return mitered+_swap(mitered)


def cap(s: CornerSpec = CornerSpec()):
    """Closed outer elbow minus both connected through-socket cavities."""
    body = _elbow_prism(s, s.outer)
    # Match the cavities on the same plane and subtract the connected volume:
    # this leaves no web or stop and preserves the profile around the corner.
    return body-_elbow_prism(s, s.clearance, overrun=1)


def coupon(s: CornerSpec):
    """20 mm axial sample of the fully enclosed L-profile slip sleeve."""
    outer = _profile_prism(s, s.outer, 0, 20)
    inner = _profile_prism(s, s.clearance, -1, 22)
    return outer-inner


def trim_fixture(s: CornerSpec = CornerSpec(), length: float = 95):
    """One estimated rounded angle, mitered to give s.miter_gap with its mirror."""
    from build123d import Plane, Polygon, extrude
    angle = _profile_prism(s, 0, 0, length)
    offset = s.miter_gap/math.sqrt(2)
    # Retain x >= y+offset. Mirror in x=y to make the perpendicular segment.
    area = Plane.XY*Polygon((offset, 0), (length, 0),
                             (length, length-offset), align=None)
    keep = extrude(area, amount=s.leg+2).translate((0, 0, -s.leg-1))
    return angle & keep


def insertion_sweep(s: CornerSpec):
    """Exact axial sweep of the reference miter fixture from outside to -travel.

    At each Y/Z section the trim occupies an X interval. Translating that
    interval continuously fills the longer interval represented by this prism.
    """
    fixture_length = max(95, s.length+30)
    outside_shift = s.length+s.outer
    return trim_fixture(s, fixture_length+outside_shift+s.travel).translate(
        (-s.travel, 0, 0))


def _intersection_volume(a, b):
    intersection = a & b
    return intersection.volume if intersection else 0.0


def validation(s: CornerSpec, cover=None):
    """Actual solid clearance for travel extrema and continuous insertion paths."""
    cover = cap(s) if cover is None else cover
    a = trim_fixture(s, max(95, s.length+30))
    b = _swap(a)
    maximum = 0.0
    for dx in (-s.travel, 0, s.travel):
        for dy in (-s.travel, 0, s.travel):
            ta, tb = a.translate((dx, 0, 0)), b.translate((0, dy, 0))
            for left, right in ((cover, ta), (cover, tb), (ta, tb)):
                maximum = max(maximum, _intersection_volume(left, right))
    sweep = insertion_sweep(s)
    for path, neighbor, axis in ((sweep, b, (0, 1, 0)),
                                 (_swap(sweep), a, (1, 0, 0))):
        maximum = max(maximum, _intersection_volume(cover, path))
        for shift in (-s.travel, 0, s.travel):
            maximum = max(maximum, _intersection_volume(
                path, neighbor.translate(tuple(v*shift for v in axis))))
    if maximum > 1e-5:
        raise ValueError(f'Prototype collision: {maximum:g} mm³')
    return dict(travel_positions_checked=9, insertion_sweeps_checked=2,
                insertion_neighbor_positions_checked=6,
                maximum_intersection_mm3=maximum,
                minimum_miter_gap_mm=s.miter_gap-math.sqrt(2)*s.travel,
                minimum_full_profile_engagement_mm=s.minimum_engagement,
                required_space_behind_trim_mm=s.outer)


def _drawing(s: CornerSpec, path: Path):
    """Dimensioned plan and section showing every wall of the sleeve."""
    o, c, w, t = s.outer, s.clearance, s.leg, s.thickness
    # SVG Y points down; the section uses -Z for clarity.
    def profile(m):
        segments = _profile_segments(s, m)
        commands = [f'M {segments[0][0][0]:g} {segments[0][0][1]:g}']
        for a, mid, b, radius in segments:
            if mid is None:
                commands.append(f'L {b[0]:g} {b[1]:g}')
            else:
                cross = ((mid[0]-a[0])*(b[1]-mid[1])
                         - (mid[1]-a[1])*(b[0]-mid[0]))
                commands.append(f'A {radius:g} {radius:g} 0 0 {int(cross > 0)} '
                                f'{b[0]:g} {b[1]:g}')
        return ' '.join([*commands, 'Z'])
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 680">
<rect width="1120" height="680" fill="#f5f6f7"/>
<g font-family="sans-serif" fill="#24323d">
<text x="30" y="35" font-size="24">US20 ASA corner — rounded slip-socket prototype / mm</text>
<text x="30" y="65">Two axial insertion mouths. No clips, interference ribs, pads or stops.</text>
<g transform="translate(65 110) scale(3)">
<path d="M {-o} {-o} H {s.length} V {w+o} H {w+o} V {s.length} H {-o} Z"
 fill="#556774" stroke="#24323d" stroke-width="0.4"/>
<path d="M 0 0 H {s.length} M 0 0 V {s.length} M 0 0 L {w} {w}"
 fill="none" stroke="#eacb8b" stroke-width="0.5" stroke-dasharray="2 1"/>
<path d="M {s.length+10} 20 H {s.length+1} M 20 {s.length+10} V {s.length+1}"
 fill="none" stroke="#248e88" stroke-width="1"/>
</g>
<text x="40" y="345">PLAN: reach {s.length:g} mm along each edge from nominal corner</text>
<text x="40" y="370">Reference {w:g} mm legs; exterior offset {o:g} mm</text>
<text x="40" y="395">Minimum full-profile engagement: {s.minimum_engagement:.2f} mm</text>
<g transform="translate(635 110) scale(4)">
<path d="{profile(o)}" fill="#556774"/>
<path d="{profile(c)}" fill="#f5f6f7"/>
<path d="{profile(0)}" fill="#c6a570"/>
</g>
<text x="550" y="345">SOCKET SECTION: gold = estimated trim; dark = ASA</text>
<text x="550" y="370">Walls {s.wall:g} mm; running clearance {c:g} mm per face</text>
<text x="550" y="395">Reference thickness {t:g} mm; leg width {w:g} mm</text>
<text x="550" y="420">Inner walls require {o:g} mm behind trim, against roof/siding</text>
<text x="40" y="445">Reference radii: outside bend {s.outside_bend_radius:g}; inside bend {s.inside_bend_radius:g}; free ends {s.end_radius:g} mm</text>
<text x="40" y="470">Fixture seam: {s.miter_gap:g} mm measured PERPENDICULAR to the 45° cuts</text>
<text x="40" y="500">Independent travel: ±{s.travel:g} mm each; no thermal capacity claim</text>
<text x="40" y="530">Assemble by inserting both trim ends before fastening. Withdraw a trim piece to remove.</text>
<text x="40" y="560">Print top down; remove internal ceiling supports through the socket mouths.</text>
<text x="40" y="600">Enclosure is unchanged. Roof/siding relief or trim repositioning requires separate design.</text>
<text x="40" y="640">Rounded section from CAD profile. Conservative photo estimates; verify on actual stock.</text>
</g></svg>\n''')


def generate(directory: Path, s: CornerSpec = CornerSpec()):
    from build123d import Axis, Compound, ExportSVG, export_step, export_stl
    directory.mkdir(parents=True, exist_ok=True)
    cover = cap(s)
    checks = validation(s, cover)
    pieces = [('us20_corner_cap', cover, 'top down')]
    for c in (0.5, 0.75, 1.0):
        pieces.append((f'fit_coupon_{c:.2f}', coupon(replace(s, clearance=c)), 'top down'))
    fixture = trim_fixture(s, max(95, s.length+30))
    pieces.extend([('miter_fixture_a', fixture, 'outer top down'),
                   ('miter_fixture_b', _swap(fixture), 'outer top down')])
    records, paths = [], []
    for name, shape, orientation in pieces:
        if not shape.is_valid or len(shape.solids()) != 1:
            raise ValueError(f'{name}: expected one valid solid')
        step, stl = directory/f'{name}.step', directory/f'{name}.stl'
        export_step(shape, step)
        printable = shape.rotate(Axis.X, 180)
        bounds = printable.bounding_box()
        printable = printable.translate(tuple(-v for v in bounds.min))
        export_stl(printable, stl, tolerance=0.03, angular_tolerance=0.1)
        paths.extend((step, stl))
        record = dict(name=name, size_mm=list(shape.bounding_box().size),
                      volume_mm3=shape.volume, print_orientation=orientation)
        if name.startswith('fit_coupon_'):
            record['clearance_per_face_mm'] = float(name.rsplit('_', 1)[1])
        records.append(record)
    drawing, manifest = directory/'drawing.svg', directory/'manifest.json'
    _drawing(s, drawing)
    for name, shape, eye in (
        ('cap_exterior', cover, (-150, -180, 130)),
        ('cap_underside', cover, (150, 180, -140)),
        ('fixture_assembly', Compound(children=[cover, fixture, _swap(fixture)]),
         (-150, -180, 130)),
        ('socket_mouth', cover, (180, 0, -20)),
    ):
        visible, _ = shape.project_to_viewport(eye, look_at=(25, 25, -20))
        svg = ExportSVG(scale=3, margin=5, line_weight=0.25)
        svg.add_shape(visible)
        preview = directory/f'{name}.svg'
        svg.write(preview)
        paths.append(preview)
    manifest.write_text(json.dumps(dict(units='mm', material='ASA', prototype=True,
        design_revision='rounded-slip-socket-v3',
        dimension_basis='Conservative estimates from five ink prints photographed on a 1 mm grid; not confirmed stock measurements.',
        dimensions=asdict(s), outer_offset_mm=s.outer, validation=checks, parts=records,
        coordinates='US20 outside corner at XY=0; top Z=0; legs extend in +X/+Y and down -Z',
        warning='Estimated rounded fixtures only. Print a coupon to check stock fit, support removal and space behind trim; enclosure unchanged.'),
        indent=2)+'\n')
    return [*paths, drawing, manifest]
