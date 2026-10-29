"""Gusset bearing caps. Dimensions are mm; installed origin is the plate minimum."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from lumber_model.gusset import GUSSET_HOLE_CENTERS_IN, GUSSET_SIZE_IN, GUSSET_THICKNESS_IN

MM = 25.4
PLATE = GUSSET_SIZE_IN * MM
HEIGHT = 0.75 * MM
OVERHANG = 5.5  # Fits inside the verified 6.35 mm plate-to-frame margin.
# Field print overhung the rear framing by 1/4 inch. Restore the nominal
# plate-to-frame inset as well, without changing the enclosure model.
BACK_LEFT_REAR_TRIM_MM = 0.25 * MM + (0.25 * MM - OVERHANG)
FIT = 0.6
WEB = 2.4
DECK_BOTTOM = 8.0
DRAIN_WIDTH = 6.0
DRAIN_HEIGHT = 3.0
Box = tuple[tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True)
class GussetCover:
    name: str
    origin_in: tuple[float, float, float]
    bearing_bands_mm: tuple[tuple[float, float], ...]
    y_bounds_mm: tuple[float, float]
    source_strips: tuple[str, ...]

    @property
    def boxes(self) -> tuple[Box, ...]:
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


def covers_for_siding(siding, *, fabrication: bool = False) -> tuple[GussetCover, ...]:
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
        result.append(GussetCover(f'gusset_cover_{index}', origin, bands,
                                  y_bounds, source_strips))
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
                   f'{"Back-left" if index == 0 else "Front-right"} (cover {index+1})</text>')
        svg.append(f'<g transform="translate({center-163.4+2*OVERHANG} '
                   f'{510+2*cover.y_bounds_mm[0]}) scale(2 -2)">')
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
        svg.append(f'<rect width="{PLATE}" height="{PLATE}" fill="none" '
                   'stroke="#273b47" stroke-width="0.6" stroke-dasharray="3 2"/>')
        for x,y in GUSSET_HOLE_CENTERS_IN:
            svg.append(f'<circle cx="{x*MM}" cy="{y*MM}" r="4.445" fill="none" '
                       'stroke="#273b47" stroke-width="0.45" stroke-dasharray="1 1"/>')
        svg.append('</g>')
        length = cover.y_bounds_mm[1]-cover.y_bounds_mm[0]
        svg.append(f'<text x="{center}" y="547" font-size="16">'
                   f'163.4 × {length:g} mm; bearing height 19.05 mm</text>')
    svg.extend(['<text x="560" y="590" font-size="15">Blue: siding bearing  ·  Gray: recessed ribs  ·  Dashed: steel and screw-head outlines</text>',
                '</g></svg>'])
    path.write_text('\n'.join(svg)+'\n')


def generate_gusset_covers(siding, directory: Path) -> list[Path]:
    """Export two individually relieved caps in mm, with STEP in installed axes."""
    from build123d import Align, Axis, Box as CadBox, Location, Part, export_step, export_stl

    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    records = []
    covers = covers_for_siding(siding, fabrication=True)
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
                            size_mm=list(bounds.size),
                            volume_mm3=solid.volume))
    manifest = directory/'manifest.json'
    manifest.write_text(json.dumps(dict(units='mm', material='ASA or ABS',
        skirt_margin_mm=6.35-OVERHANG, plate_side_clearance_mm=FIT,
        parts=records), indent=2)+'\n')
    paths.append(manifest)
    preview = directory/'preview.svg'
    _write_preview(covers, preview)
    paths.append(preview)
    return paths
