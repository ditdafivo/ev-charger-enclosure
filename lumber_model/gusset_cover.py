"""Gusset bearing caps. Dimensions are mm; installed origin is the plate minimum."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

from lumber_model.gusset import GUSSET_HOLE_CENTERS_IN, GUSSET_SIZE_IN, GUSSET_THICKNESS_IN

MM = 25.4
PLATE = GUSSET_SIZE_IN * MM
HEIGHT = 0.75 * MM
OVERHANG = 5.5  # Fits inside the verified 6.35 mm plate-to-frame margin.
# Trim the rear skirt flush with the default layout's rear bearing band.
# Nominal rear: 157.9 mm; bearing-band rear: 155.575 mm.
BACK_LEFT_REAR_TRIM_MM = 2.325
FIT = 0.6
WEB = 2.4
DECK_BOTTOM = 8.0
DRAIN_WIDTH = 6.0
DRAIN_HEIGHT = 3.0
Box = tuple[tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True)
class GussetCoverSpec:
    """Field-fit dimensions in mm; outward reaches start at framing edges."""
    outward_x_mm: float = 6.35
    outward_y_mm: float = 6.35
    # Together with the base offsets, add 1/2 in -X and 9/16 in +Y
    # relative to the original field-trimmed back-left fabrication cover.
    back_left_outward_x_extra_mm: float = 5.5
    back_left_outward_y_extra_mm: float = 4.7625
    front_right_outward_x_extra_mm: float = 3.175
    front_right_outward_y_extra_mm: float = 4.7625
    inward_x_mm: float = 25.0
    inward_y_mm: float = 25.0
    tab_width_x_mm: float = 25.0
    tab_width_y_mm: float = 25.0
    tab_recess_x_mm: float = 6.0
    tab_recess_y_mm: float = 6.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'{name} must be finite and nonnegative')
            if 'width' in name and value == 0:
                raise ValueError(f'{name} must be positive')
            if 'recess' in name and not 0 < value < HEIGHT:
                raise ValueError(f'{name} must be between zero and {HEIGHT:g} mm')


DEFAULT_SPEC = GussetCoverSpec()


@dataclass(frozen=True)
class GussetCover:
    name: str
    origin_in: tuple[float, float, float]
    bearing_bands_mm: tuple[tuple[float, float], ...]
    y_bounds_mm: tuple[float, float]
    source_strips: tuple[str, ...]
    trim_lands: tuple[Box, ...] = ()
    anchor_tabs: tuple[Box, ...] = ()

    @property
    def boxes(self) -> tuple[Box, ...]:
        return self.base_boxes + self.trim_lands + self.anchor_tabs

    @property
    def bounds_mm(self) -> Box:
        boxes = self.boxes
        lo = tuple(min(p[i] for p, _ in boxes) for i in range(3))
        hi = tuple(max(p[i]+s[i] for p, s in boxes) for i in range(3))
        return lo, tuple(hi[i]-lo[i] for i in range(3))

    @property
    def base_boxes(self) -> tuple[Box, ...]:
        """A connected solid, including open-bottom screw wells and drain gates."""
        boxes: list[Box] = []
        lo, hi = -OVERHANG, PLATE + OVERHANG
        span = hi-lo
        for a, b in self.bearing_bands_mm:
            boxes.append(((lo, a, DECK_BOTTOM), (span, b-a, HEIGHT-DECK_BOTTOM)))

        def rib(axis: int, across: float, width: float, bottom: float) -> None:
            # The upper part is continuous; lower gates connect every screw well
            # to the open perimeter. Internal webs bear on steel, skirts on wood.
            gate_top = bottom + DRAIN_HEIGHT
            pos = [lo, across, gate_top]
            size = [span, width, DECK_BOTTOM-gate_top]
            if axis == 1:
                pos[0], pos[1] = pos[1], pos[0]
                size[0], size[1] = size[1], size[0]
            boxes.append((tuple(pos), tuple(size)))
            cuts = [lo, *(v*MM-DRAIN_WIDTH/2 for v in (0.75,2.25,3.75,5.25)), hi]
            ends = [*(v*MM+DRAIN_WIDTH/2 for v in (0.75,2.25,3.75,5.25)), hi]
            for a, b in zip([lo, *ends[:-1]], cuts[1:]):
                pos = [a, across, bottom]
                size = [b-a, width, DRAIN_HEIGHT]
                if axis == 1:
                    pos[0], pos[1] = pos[1], pos[0]
                    size[0], size[1] = size[1], size[0]
                boxes.append((tuple(pos), tuple(size)))

        for axis in (0, 1):
            rib(axis, lo, OVERHANG-FIT, 0)
            rib(axis, PLATE+FIT, OVERHANG-FIT, 0)
            for center in (WEB/2, 1.5*MM, 3*MM, 4.5*MM, PLATE-WEB/2):
                rib(axis, center-WEB/2, WEB, GUSSET_THICKNESS_IN*MM)
        # Continue the longitudinal webs inward without extending the skirt's
        # plate-locating faces. Cross-ties and feet stay below the bearing bands.
        extension_rails = []
        for ya, yb in ((self.y_bounds_mm[0], lo), (hi, self.y_bounds_mm[1])):
            if yb-ya < 1e-7:
                continue
            rail_x = [(lo, OVERHANG-FIT), (PLATE+FIT, OVERHANG-FIT)]
            rail_x += [(c-WEB/2, WEB) for c in
                       (WEB/2, 1.5*MM, 3*MM, 4.5*MM, PLATE-WEB/2)]
            for x, width in rail_x:
                extension_rails.append(((x, ya, DECK_BOTTOM-WEB), (width, yb-ya, WEB)))
            edge_y = ya if ya < lo else yb-WEB
            extension_rails.append(((lo, edge_y, DECK_BOTTOM-WEB), (span, WEB, WEB)))

        boxes.extend(extension_rails)
        for pos, size in extension_rails:
            # Extend every rail to the framing plane. Clipping feet to the
            # modeled framing left an unnecessary raised corner in the print.
            # These extensions are entirely outside the steel plate footprint.
            xa, ya = pos[:2]
            xb, yb = xa+size[0], ya+size[1]
            boxes.append(((xa, ya, DRAIN_HEIGHT),
                          (xb-xa, yb-ya, DECK_BOTTOM-WEB-DRAIN_HEIGHT)))
            along = 0 if xb-xa > yb-ya else 1
            start, end = (xa, xb) if along == 0 else (ya, yb)
            mid = (start+end)/2
            segments = ((start, end),) if end-start <= DRAIN_WIDTH else (
                (start, mid-DRAIN_WIDTH/2), (mid+DRAIN_WIDTH/2, end))
            for a, b in segments:
                foot_pos = [xa, ya, 0]
                foot_size = [xb-xa, yb-ya, DRAIN_HEIGHT]
                foot_pos[along], foot_size[along] = a, b-a
                boxes.append((tuple(foot_pos), tuple(foot_size)))
        # The fabrication-only rear trim cuts through every layer, including
        # the nominal skirt and webs that were built around the full plate.
        clipped = []
        for pos, size in boxes:
            if (pos[1] >= self.y_bounds_mm[0]-1e-7 and
                    pos[1]+size[1] <= self.y_bounds_mm[1]+1e-7):
                clipped.append((pos, size))
                continue
            a = max(pos[1], self.y_bounds_mm[0])
            b = min(pos[1]+size[1], self.y_bounds_mm[1])
            if b-a > 1e-7:
                clipped.append(((pos[0], a, pos[2]), (size[0], b-a, size[2])))
        return tuple(clipped)


def covers_for_siding(siding, *, fabrication: bool = False,
                      spec: GussetCoverSpec = DEFAULT_SPEC) -> tuple[GussetCover, ...]:
    """Continue interrupted plywood runs; optionally apply field-fit trimming."""
    result = []
    for index, (origin, size) in enumerate(siding.roof_gussets, 1):
        if any(abs(v-GUSSET_SIZE_IN)>1e-6 for v in size[:2]):
            raise ValueError('Gusset covers require the 6 x 6 inch plates')
        left = origin[0]+size[0]/2 < (siding.min_x+siding.max_x)/2
        rear = origin[1]+size[1]/2 > (siding.min_y+siding.max_y)/2
        clearance = siding.roof_hardware_clearance
        interrupted = []
        for strip in siding.roof_strips:
            end = strip.start[0] if left else strip.start[0]+strip.size[0]
            cutoff = origin[0]+size[0]+clearance if left else origin[0]-clearance
            if (abs(end-cutoff)<1e-7 and
                    strip.start[1]<origin[1]+size[1]+clearance and
                    strip.start[1]+strip.size[1]>origin[1]-clearance):
                interrupted.append(strip)
        if not interrupted:
            raise ValueError(f'Gusset {index}: no interrupted plywood runs')
        lo, hi = -OVERHANG, PLATE+OVERHANG
        raw_bands = [((s.start[1]-origin[1])*MM,
                      (s.start[1]+s.size[1]-origin[1])*MM) for s in interrupted]
        y_bounds = (min(lo, min(a for a, _ in raw_bands)), hi) if rear else (
            lo, max(hi, max(b for _, b in raw_bands)))
        if fabrication and left and rear:
            y_bounds = (y_bounds[0], y_bounds[1]-BACK_LEFT_REAR_TRIM_MM)
        trimmed_bands = [(max(a,y_bounds[0]), min(b,y_bounds[1])) for a,b in raw_bands]
        bands = tuple((a,b) for a,b in trimmed_bands if b-a > 1e-7)
        source_strips = tuple(s.name for s,(a,b) in zip(interrupted, trimmed_bands)
                              if b-a > 1e-7)
        # Frame-relative limits; preserve the original plate-locating skirt.
        back_left = left and rear
        front_right = not left and not rear
        extra_x = (spec.back_left_outward_x_extra_mm if back_left else
                   spec.front_right_outward_x_extra_mm if front_right else 0)
        extra_y = (spec.back_left_outward_y_extra_mm if back_left else
                   spec.front_right_outward_y_extra_mm if front_right else 0)
        outward_x = spec.outward_x_mm + extra_x
        outward_y = spec.outward_y_mm + extra_y
        outer_x = siding.min_x-outward_x/MM if left else siding.max_x+outward_x/MM
        outer_y = siding.max_y+outward_y/MM if rear else siding.min_y-outward_y/MM
        ox, oy = (outer_x-origin[0])*MM, (outer_y-origin[1])*MM
        xlo, xhi = (min(lo, ox), hi) if left else (lo, max(hi, ox))
        lands = []
        xa, xb = (xlo, lo) if left else (hi, xhi)
        if xb > xa:
            lands.extend(((xa, a, DECK_BOTTOM), (xb-xa, b-a, HEIGHT-DECK_BOTTOM))
                         for a, b in bands)
        ya, yb = (bands[-1][1], oy) if rear else (oy, bands[0][0])
        if yb > ya:
            lands.append(((xlo, ya, DECK_BOTTOM), (xhi-xlo, yb-ya, HEIGHT-DECK_BOTTOM)))

        def brace_center(axis: int) -> float:
            transverse = 1-axis
            edge = ((siding.max_y if rear else siding.min_y) if axis == 0 else
                    (siding.min_x if left else siding.max_x))
            candidates = [(p, z) for p, z in siding.framing
                          if abs(p[2]+z[2]-origin[2]) < 1e-6
                          and z[axis] > GUSSET_SIZE_IN
                          and p[transverse]-1e-7 <= edge <= p[transverse]+z[transverse]+1e-7]
            if len(candidates) != 1:
                raise ValueError(f'Gusset {index}: cannot identify axis {axis} supporting brace')
            p, z = candidates[0]
            width = spec.tab_width_x_mm if axis == 0 else spec.tab_width_y_mm
            if width > z[transverse]*MM:
                raise ValueError(f'Gusset {index}: axis {axis} tab width exceeds brace width')
            return (p[transverse]+z[transverse]/2-origin[transverse])*MM

        tabs = []
        for axis, reach, width, recess, direction, start in (
            (0, spec.inward_x_mm, spec.tab_width_x_mm, spec.tab_recess_x_mm,
             1 if left else -1, hi if left else lo),
            (1, spec.inward_y_mm, spec.tab_width_y_mm, spec.tab_recess_y_mm,
             -1 if rear else 1, y_bounds[0] if rear else y_bounds[1]),
        ):
            if reach == 0:
                continue
            center = brace_center(axis)
            pos = [0., 0., 0.]
            size = [0., 0., HEIGHT-recess]
            pos[axis] = start if direction > 0 else start-reach
            pos[1-axis] = center-width/2
            size[axis], size[1-axis] = reach, width
            tabs.append((tuple(pos), tuple(size)))
        name = ('gusset_cover_bl' if left and rear else
                'gusset_covet_fr' if not left and not rear else
                f'gusset_cover_{index}')
        result.append(GussetCover(name, origin, bands,
                                  y_bounds, source_strips, tuple(lands), tuple(tabs)))
    return tuple(result)


def _write_preview(covers: tuple[GussetCover, ...], path: Path) -> None:
    """A top view showing bearing bands, open framework, and adjacent plywood."""
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 620">',
           '<rect width="1120" height="620" fill="#f5f6f7"/>',
           '<g font-family="sans-serif" fill="#21313b" text-anchor="middle">',
           '<text x="560" y="45" font-size="25">Gusset covers: plywood-aligned bearing bands</text>',
           '<text x="560" y="77" font-size="15">Top view; rear (+Y) is up. Tan stubs show the adjacent plywood runs.</text>']
    for index, cover in enumerate(covers):
        center = 300+520*index
        svg.append(f'<text x="{center}" y="119" font-size="20">'
                   f'{"Back-left" if index == 0 else "Front-right"} ({cover.name})</text>')
        lower, extent = cover.bounds_mm
        scale = min(1.7, 440/extent[0], 360/extent[1])
        svg.append(f'<g transform="translate({center-scale*(lower[0]+extent[0]/2)} '
                   f'{505+scale*lower[1]}) scale({scale} {-scale})">')
        for pos, size in cover.boxes:
            if pos[2]+size[2] <= DECK_BOTTOM+1e-7:
                svg.append(f'<rect x="{pos[0]}" y="{pos[1]}" width="{size[0]}" '
                           f'height="{size[1]}" fill="#a5aeb4"/>')
        for a,b in cover.bearing_bands_mm:
            svg.append(f'<rect x="{-OVERHANG}" y="{a}" width="{PLATE+2*OVERHANG}" '
                       f'height="{b-a}" fill="#377e96"/>')
            stub_x = PLATE+0.25*MM if index == 0 else -0.25*MM-30
            svg.append(f'<rect x="{stub_x}" y="{a}" width="30" height="{b-a}" '
                       'fill="#c6a570"/>')
        for boxes, color in ((cover.trim_lands, '#377e96'), (cover.anchor_tabs, '#c47738')):
            for pos, land_size in boxes:
                svg.append(f'<rect x="{pos[0]}" y="{pos[1]}" width="{land_size[0]}" '
                           f'height="{land_size[1]}" fill="{color}"/>')
        svg.append(f'<rect width="{PLATE}" height="{PLATE}" fill="none" '
                   'stroke="#273b47" stroke-width="0.6" stroke-dasharray="3 2"/>')
        for x,y in GUSSET_HOLE_CENTERS_IN:
            svg.append(f'<circle cx="{x*MM}" cy="{y*MM}" r="4.445" fill="none" '
                       'stroke="#273b47" stroke-width="0.45" stroke-dasharray="1 1"/>')
        svg.append('</g>')
        svg.append(f'<text x="{center}" y="547" font-size="16">'
                   f'{extent[0]:g} × {extent[1]:g} mm; bearing height 19.05 mm</text>')
    svg.extend(['<text x="560" y="590" font-size="15">Blue: bearing / trim lands · Orange: recessed anchor tabs · Gray: ribs · Dashed: steel / heads</text>',
                '</g></svg>'])
    path.write_text('\n'.join(svg)+'\n')


def generate_gusset_covers(siding, directory: Path, *,
                           spec: GussetCoverSpec = DEFAULT_SPEC) -> list[Path]:
    """Export two individually relieved caps in mm, with STEP in installed axes."""
    from build123d import Align, Axis, Box as CadBox, Location, Part, export_step, export_stl

    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    records = []
    covers = covers_for_siding(siding, fabrication=True, spec=spec)
    for cover in covers:
        solids = [Location(pos)*CadBox(*size, align=(Align.MIN,)*3)
                  for pos, size in cover.boxes]
        solid = Part() + solids
        if len(solid.solids()) != 1 or not solid.is_valid:
            raise ValueError(f'{cover.name}: cover must be one valid solid')
        step_path = directory/f'{cover.name}.step'
        stl_path = directory/f'{cover.name}.stl'
        scad_path = directory/f'{cover.name}.scad'
        export_step(solid, step_path)
        # Use actual bounds: the two Y extensions have different lengths and
        # directions. Bearing faces touch the bed; the ribs then build upward.
        bounds = solid.bounding_box()
        printable = solid.rotate(Axis.X, 180).translate(
            (-bounds.min.X, bounds.max.Y, bounds.max.Z))
        export_stl(printable, stl_path, tolerance=0.05, angular_tolerance=0.1)
        scad_path.write_text(
            '// Millimetres. Installed orientation; STL is bearing face down.\n'
            'color([0.22,0.30,0.36]) union() {\n'
            + ''.join(f'  translate({list(pos)}) cube({list(size)});\n'
                      for pos, size in cover.boxes) + '}\n'
        )
        paths.extend((step_path, stl_path, scad_path))
        records.append(dict(name=cover.name, quantity=1, origin_in=cover.origin_in,
                            bearing_bands_mm=cover.bearing_bands_mm,
                            y_bounds_mm=cover.y_bounds_mm,
                            source_strips=cover.source_strips,
                            trim_lands_mm=cover.trim_lands,
                            anchor_tabs_mm=cover.anchor_tabs,
                            plywood_relief_required=True,
                            bounds_mm=cover.bounds_mm,
                            size_mm=list(bounds.size),
                            volume_mm3=solid.volume))
    manifest = directory/'manifest.json'
    manifest.write_text(json.dumps(dict(units='mm', material='ASA or ABS',
        skirt_margin_mm=6.35-OVERHANG, plate_side_clearance_mm=FIT,
        parameters=asdict(spec), parts=records), indent=2)+'\n')
    paths.append(manifest)
    preview = directory/'preview.svg'
    _write_preview(covers, preview)
    paths.append(preview)
    return paths
