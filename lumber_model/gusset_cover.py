"""Gusset bearing caps. Dimensions are mm; installed origin is the plate minimum."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from lumber_model.gusset import GUSSET_SIZE_IN, GUSSET_THICKNESS_IN

MM = 25.4
PLATE = GUSSET_SIZE_IN * MM
HEIGHT = 0.75 * MM
OVERHANG = 5.5  # Fits inside the verified 6.35 mm plate-to-frame margin.
FIT = 0.6
WEB = 2.4
DECK_BOTTOM = 8.0
DECK_TOP = 12.0  # Recessed joint channels are 7.05 mm below the bearing plane.
DRAIN_WIDTH = 6.0
DRAIN_HEIGHT = 3.0
Box = tuple[tuple[float, float, float], tuple[float, float, float]]


@dataclass(frozen=True)
class GussetCover:
    name: str
    origin_in: tuple[float, float, float]
    bearing_bands_mm: tuple[tuple[float, float], ...]

    @property
    def boxes(self) -> tuple[Box, ...]:
        """A connected solid, including open-bottom screw wells and drain gates."""
        boxes: list[Box] = []
        lo, hi = -OVERHANG, PLATE + OVERHANG
        span = hi-lo
        boxes.append(((lo, lo, DECK_BOTTOM), (span, span, DECK_TOP-DECK_BOTTOM)))
        for a, b in self.bearing_bands_mm:
            boxes.append(((lo, a, DECK_TOP), (span, b-a, HEIGHT-DECK_TOP)))

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
        return tuple(boxes)


def covers_for_siding(siding) -> tuple[GussetCover, ...]:
    """Relieve each cap at the actual roof-board joints, keeping laps unobstructed."""
    result = []
    for index, (origin, size) in enumerate(siding.roof_gussets, 1):
        if any(abs(v-GUSSET_SIZE_IN)>1e-6 for v in size[:2]):
            raise ValueError('Gusset covers require the 6 x 6 inch plates')
        bands = []
        for board in siding.board_parts:
            if '_top_' not in board.name:
                continue
            # Same full-thickness bearing envelope as the plywood strips, plus
            # 0.6 mm clearance at either side of the joint/board-end relief.
            lap = siding.board_width-siding.course_pitch
            a = max(-OVERHANG, (board.start[1]+lap-origin[1])*MM+FIT)
            b = min(PLATE+OVERHANG,
                    (min(board.start[1]+board.size[1], board.start[1]+siding.course_pitch)-origin[1])*MM-FIT)
            if b>a:
                bands.append((a,b))
        result.append(GussetCover(f'gusset_cover_{index}', origin, tuple(bands)))
    return tuple(result)


def generate_gusset_covers(siding, directory: Path) -> list[Path]:
    """Export two individually relieved caps in mm, with STEP in installed axes."""
    from build123d import Align, Axis, Box as CadBox, Location, Part, export_step, export_stl

    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    records = []
    for cover in covers_for_siding(siding):
        solids = [Location(pos)*CadBox(*size, align=(Align.MIN,)*3)
                  for pos, size in cover.boxes]
        solid = Part() + solids
        if len(solid.solids()) != 1 or not solid.is_valid:
            raise ValueError(f'{cover.name}: cover must be one valid solid')
        step_path = directory/f'{cover.name}.step'
        stl_path = directory/f'{cover.name}.stl'
        scad_path = directory/f'{cover.name}.scad'
        export_step(solid, step_path)
        # Bearing face down; only the shallow joint relief needs bed support.
        printable = solid.rotate(Axis.X, 180).translate((OVERHANG, PLATE+OVERHANG, HEIGHT))
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
                            size_mm=[PLATE+2*OVERHANG]*2+[HEIGHT],
                            volume_mm3=solid.volume))
    manifest = directory/'manifest.json'
    manifest.write_text(json.dumps(dict(units='mm', material='ASA or ABS',
        skirt_margin_mm=6.35-OVERHANG, plate_side_clearance_mm=FIT,
        parts=records), indent=2)+'\n')
    paths.append(manifest)
    return paths
