"""Measured-profile, open-backed US20 seam cover. Dimensions are millimetres."""
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path

from .us20_corner import (CornerSpec, _box, _profile_prism, _profile_segments, _swap,
                          _intersection_volume, trim_fixture)


@dataclass(frozen=True)
class ClipSpec:
    leg: float = 39.6
    thickness: float = 8.2
    overlap: float = 10.0
    wall: float = 2.0
    clearance: float = 0.25
    outside_bend_radius: float = 2.0
    exterior_transition_radius: float = 1.0
    inside_bend_radius: float = 4.0
    end_radius: float = 4.0
    travel: float = 1.0
    miter_gap: float = 2.0
    tongue_length: float = 12.0
    tongue_width: float = 6.0
    tongue_thickness: float = 1.2
    capture: float = 0.8
    slot: float = 0.6

    @property
    def hook_offset(self):
        # Entire tongue stays beyond the moving miter cut, including clearance.
        return (self.miter_gap/math.sqrt(2)+self.travel+self.clearance
                +self.tongue_width/2+0.5)

    def __post_init__(self):
        if any(not math.isfinite(v) or v <= 0 for v in asdict(self).values()):
            raise ValueError('Dimensions must be finite and positive')
        self.reference()
        if self.exterior_transition_radius > self.outside_bend_radius+self.clearance+self.wall:
            raise ValueError('Exterior transition radius must not reduce the original shell thickness')
        if self.miter_gap <= math.sqrt(2)*self.travel:
            raise ValueError('Miter gap is too small for travel')
        if self.overlap <= self.travel/math.sqrt(2):
            raise ValueError('Travel exposes the seam')
        if not self.end_radius+self.capture < self.tongue_length < self.leg/2:
            raise ValueError('Tongue length must clear the rounded end and bend')
        if self.tongue_thickness > self.wall or self.capture >= self.thickness:
            raise ValueError('Invalid tongue thickness or capture')
        # Keep the diagonal upper tongue and its slots inside the seam band.
        if self.hook_offset+self.tongue_width/2+self.slot >= self.band_half_width:
            raise ValueError('Seam band is too narrow for hook slots')

    @property
    def band_half_width(self):
        return (self.overlap+self.miter_gap/2)*math.sqrt(2)

    def reference(self):
        return CornerSpec(leg=self.leg, thickness=self.thickness, length=80,
                          wall=self.wall, clearance=self.clearance,
                          outside_bend_radius=self.outside_bend_radius,
                          inside_bend_radius=self.inside_bend_radius,
                          end_radius=self.end_radius, travel=self.travel,
                          miter_gap=self.miter_gap)


def _flip(shape):
    """Exchange the horizontal and vertical legs of one L section."""
    from build123d import Plane
    return shape.mirror(Plane((0, 0, 0), (1, 0, 0), (0, 1, 1)))


def _exterior_prism(s):
    """Change only the outside bend, keeping the two exterior planes fixed."""
    from build123d import Edge, Face, Wire, extrude
    margin = s.clearance+s.wall
    segments = _profile_segments(s.reference(), margin)
    radius = s.exterior_transition_radius
    center = radius-margin
    top = (center, -margin)
    front = (-margin, center)
    midpoint = (center-radius/math.sqrt(2),)*2
    # The outline starts immediately after the outside bend and closes on it.
    _, _, end, _ = segments[0]
    segments[0] = (top, None, end, None)
    start, _, _, _ = segments[-2]
    segments[-2] = (start, None, front, None)
    segments[-1] = (front, midpoint, top, radius)

    def installed(point):
        return (-5, point[0], -point[1])

    edges = [Edge.make_line(installed(a), installed(b)) if mid is None else
             Edge.make_three_point_arc(installed(a), installed(mid), installed(b))
             for a, mid, b, _ in segments]
    return extrude(Face(Wire(edges)), amount=90, dir=(1, 0, 0))


def _upper_region(s, width, straight=False):
    from build123d import Plane, Polygon, extrude
    start = s.leg-s.tongue_length
    lo, hi = ((4-width/2, 4+width/2) if straight else
              (s.hook_offset-width/2, s.hook_offset+width/2))
    shift = 0 if straight else 1
    region = Plane.XY*Polygon((lo+shift*start, start),
        (hi+shift*start, start), (hi+shift*85, 85),
        (lo+shift*85, 85), align=None)
    return extrude(region, amount=90).translate((0, 0, -85))


def _front_claw_limit(s):
    """Stop at 45 degrees around the front arc and never below the trim."""
    from build123d import Plane, Polygon, extrude
    region = Plane.YZ*Polygon((-5, -s.leg), (0, -s.leg),
        (s.leg+5, 5), (-5, 5), align=None)
    return extrude(region, amount=90, dir=(1, 0, 0)).translate((-5, 0, 0))


def _arm(s, straight=False):
    ref = s.reference()
    cavity = _profile_prism(ref, s.clearance, -10, 100)
    shell = _exterior_prism(s)-cavity
    # Keep the outside faces and their bend; all rear faces remain open.
    outside = _box(-5, -5, 0, 90, 90, 5)+_box(-5, -5, -85, 90, 5, 90)
    body = shell & outside
    # Stop the cosmetic faces at the free-end arc tangents. Continuing the
    # offset profile around those arcs creates tapered wings beside the hooks.
    # Only the flexible tongues below should wrap around the rounded ends.
    end_tangent = s.leg-s.end_radius
    body = body & _box(-5, -5, -end_tangent, 90,
                      end_tangent+5, end_tangent+5)
    thin = _profile_prism(ref, s.clearance+s.tongue_thickness, -5, 90)-cavity
    for vertical in (False, True):
        # One upper rear hook and one lower front claw on each incoming trim.
        center = 4 if straight else s.thickness/2+8
        start = s.leg-s.tongue_length
        removal = _box(center-s.tongue_width/2-s.slot, start, -85,
                       s.tongue_width+2*s.slot, 90, 90)
        tongue_area = _box(center-s.tongue_width/2, start, -85,
                           s.tongue_width, 90, 90)
        if not vertical:
            removal = _upper_region(s, s.tongue_width+2*s.slot, straight)
            tongue_area = _upper_region(s, s.tongue_width, straight)
        rear_limit = s.leg-s.end_radius-s.capture
        keep = (_box(-5, -5, 0, 90, 90, 5)
                +_box(-5, rear_limit, -s.thickness-s.clearance-s.tongue_thickness,
                      90, 90, s.thickness+s.clearance+s.tongue_thickness+5))
        if vertical:
            removal, tongue_area, keep = map(_flip, (removal, tongue_area, keep))
        tongue = thin & tongue_area & keep
        if vertical:
            tongue = tongue & _front_claw_limit(s)
        body = (body-removal)+tongue
    return body


def cap(s=ClipSpec()):
    from build123d import Plane, Polygon, extrude
    d = s.band_half_width
    # Trim the X arm at the miter plane and the parallel edge of the seam band.
    region = Plane.XY*Polygon((-5, -5), (-5+d, -5), (85, 85-d),
                              (85, 85), align=None)
    region = extrude(region, amount=100).translate((0, 0, -85))
    arm = _arm(s) & region
    return arm+_swap(arm)


def coupon(s=ClipSpec()):
    """One complete L section with the same flexible hooks; straight offcut fit."""
    # Straight coupons preserve the sections; the full corner's upper tongues
    # follow the diagonal seam so each return engages only its own trim.
    return _arm(s, straight=True) & _box(0, -5, -85, 8, 90, 90)


def validation(s, cover=None):
    cover = cap(s) if cover is None else cover
    a = trim_fixture(s.reference())
    b = _swap(a)
    maximum = 0.0
    for dx in (-s.travel, 0, s.travel):
        for dy in (-s.travel, 0, s.travel):
            ta, tb = a.translate((dx, 0, 0)), b.translate((0, dy, 0))
            for left, right in ((cover, ta), (cover, tb), (ta, tb)):
                maximum = max(maximum, _intersection_volume(left, right))
    if maximum > 1e-5:
        raise ValueError(f'Seated collision: {maximum:g} mm³')
    return dict(travel_positions_checked=9, maximum_intersection_mm3=maximum,
                minimum_miter_gap_mm=s.miter_gap-math.sqrt(2)*s.travel,
                minimum_normal_overlap_mm=s.overlap-s.travel/math.sqrt(2),
                rear_hook_clearance_mm=s.clearance+s.tongue_thickness,
                lower_rear_return=False, lower_front_claw_angle_deg=45,
                upper_hook_minimum_miter_margin_mm=
                    s.hook_offset-s.tongue_width/2-s.miter_gap/math.sqrt(2)-s.travel,
                snap_entry='Rounded end arcs provide lead-ins; elastic deflection and retention require offcut tests')


def generate(directory: Path, s=ClipSpec()):
    from build123d import Axis, Compound, ExportSVG, export_step, export_stl
    directory.mkdir(parents=True, exist_ok=True)
    cover = cap(s)
    checks = validation(s, cover)
    pieces = [('us20_corner_clip', cover)]
    pieces += [(f'clip_coupon_{c:.2f}', coupon(replace(s, clearance=c)))
               for c in (0.15, 0.25, 0.40)]
    records, paths = [], []
    for name, shape in pieces:
        if not shape.is_valid or len(shape.solids()) != 1:
            raise ValueError(f'{name}: expected one valid solid')
        step, stl = directory/f'{name}.step', directory/f'{name}.stl'
        export_step(shape, step)
        printable = shape.rotate(Axis.X, 180)
        printable = printable.translate(tuple(-v for v in printable.bounding_box().min))
        export_stl(printable, stl, tolerance=0.03, angular_tolerance=0.1)
        paths.extend((step, stl))
        records.append(dict(name=name, size_mm=list(shape.bounding_box().size),
                            volume_mm3=shape.volume, print_orientation='outer top down'))
    fixture = trim_fixture(s.reference())
    for name, shape, eye in (
        ('assembly', Compound(children=[cover, fixture, _swap(fixture)]), (-120, -160, 110)),
        ('rear', cover, (120, 150, -110)),
        ('exterior', cover, (-120, -160, 110)),
        ('coupon_section', coupon(s), (120, 4, -20)),
    ):
        visible, _ = shape.project_to_viewport(eye, look_at=(4, 4, -20) if name == 'coupon_section' else (20, 20, -20))
        svg = ExportSVG(scale=4, margin=5, line_weight=0.25)
        svg.add_shape(visible)
        path = directory/f'{name}.svg'
        svg.write(path)
        paths.append(path)
    # Embed the actual CAD section projection; annotations remain in millimetres.
    import xml.etree.ElementTree as ET
    drawing = directory/'drawing.svg'
    root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg',
                      viewBox='0 0 900 650')
    section = ET.fromstring((directory/'coupon_section.svg').read_text())
    section.set('x', '30'); section.set('y', '80')
    section.set('width', '430'); section.set('height', '430')
    root.append(section)
    labels = [
        (25, 35, 'US20 rear-clip prototype — mm'),
        (25, 65, 'Actual CAD coupon section; estimated radii, measured leg widths and thickness'),
        (480, 130, f'Outside legs: {s.leg:g} × {s.leg:g}'),
        (480, 165, f'Trim thickness: {s.thickness:g}'),
        (480, 200, f'Face clearance: {s.clearance:g}'),
        (480, 235, f'Shell / tongue: {s.wall:g} / {s.tongue_thickness:g}'),
        (480, 270, f'Tongue sweep × axial width: {s.tongue_length:g} × {s.tongue_width:g}'),
        (480, 305, f'Rear capture past end tangent: {s.capture:g}'),
        (480, 340, f'Upper rear space: {s.clearance+s.tongue_thickness:g}'),
        (480, 375, 'Lower front claw: 45°; rear clear'),
        (480, 410, f'Outside transition radius: {s.exterior_transition_radius:g}'),
        (25, 540, f'Seam band: {2*s.overlap+s.miter_gap:g} normal width = {s.overlap:g} overlap + {s.miter_gap:g} gap + {s.overlap:g} overlap'),
        (25, 575, f'Independent travel: ±{s.travel:g}; minimum overlap: {checks["minimum_normal_overlap_mm"]:.2f}'),
        (25, 610, 'Upper rear hooks; lower front claws stop at 45°. Lower rear stays open.'),
    ]
    for x, y, label in labels:
        ET.SubElement(root, 'text', x=str(x), y=str(y),
                      **{'font-family': 'sans-serif', 'font-size': '17'}).text = label
    ET.ElementTree(root).write(drawing, encoding='unicode')
    paths.append(drawing)
    manifest = directory/'manifest.json'
    manifest.write_text(json.dumps(dict(design_revision='small-radius-v4', units='mm',
        material='ASA', prototype=True, dimensions=asdict(s), validation=checks,
        dimension_basis='Caliper leg widths and thickness; radii remain photographic estimates',
        parts=records), indent=2)+'\n')
    return [*paths, manifest]
