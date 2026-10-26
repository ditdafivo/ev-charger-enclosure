"""Deterministic guillotine layouts for shared roof-strip and wall-infill stock."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape


def _pack(cuts, sizes, kerf):
    free = [(i, 0., 0., w, h) for i, (w, h) in enumerate(sizes)]
    placed = []
    # Roof rips first, preserving full-length remainder for wall panels.
    ordered = sorted(cuts, key=lambda c: (c[3], -max(c[1:3]), -c[1]*c[2], c[0]))
    for name, width, height, rotate in ordered:
        options = []
        for index, (sheet, x, y, fw, fh) in enumerate(free):
            for turned, (w, h) in enumerate(((width, height), (height, width)) if rotate else ((width, height),)):
                if w <= fw+1e-8 and h <= fh+1e-8:
                    options.append(((fw*fh-w*h, min(fw-w, fh-h), sheet, index, turned), w, h))
        if not options:
            return None
        score, w, h = min(options)
        _, _, sheet, index, turned = score
        _, x, y, fw, fh = free.pop(index)
        placed.append(dict(name=name, sheet=sheet+1, x_in=x, y_in=y,
                           width_in=w, height_in=h, rotated=bool(turned)))
        # Each pair of cuts partitions its parent rectangle with saw kerf.
        if fw-w > fh-h:
            new = [(sheet, x+w+kerf, y, fw-w-kerf, fh),
                   (sheet, x, y+h+kerf, w, fh-h-kerf)]
        else:
            new = [(sheet, x+w+kerf, y, fw-w-kerf, h),
                   (sheet, x, y+h+kerf, fw, fh-h-kerf)]
        free.extend(r for r in new if r[3] > 1e-8 and r[4] > 1e-8)
    return placed, free


def plan_plywood(cuts, kerf):
    if kerf <= 0 or not cuts:
        raise ValueError("Plywood planning needs cuts and a positive kerf")
    if any(w <= 0 or h <= 0 or not ((w <= 96 and h <= 48) or (rotate and h <= 96 and w <= 48)) for _,w,h,rotate in cuts):
        raise ValueError("Plywood cut does not fit 4 x 8 ft stock")
    candidates = []
    for full in range(1, len(cuts)+1):
        for small in range(3):
            # User price relationship: a small panel costs slightly under half.
            cost = full + .49*small
            sizes = [(96., 48.)]*full + [(48., 24.)]*small
            result = _pack(cuts, sizes, kerf)
            if result:
                candidates.append((cost, full, small, sizes, result))
        if candidates and full+1 > min(c[0] for c in candidates):
            break
    _, full, small, sizes, (placed, free) = min(candidates, key=lambda c: c[:3])
    return dict(units="inches", kerf_in=kerf,
                method="Deterministic guillotine nesting; feasible layout, not a proof of optimal stock use. Roof strips unrotated along 96-inch strength axis; wall panels may rotate.",
                price_assumption="2x4 panel = 0.49 of 4x8 sheet cost; no live prices used",
                purchases={"4x8":full, "2x4":small},
                sheets=[dict(sheet=i+1, width_in=w, height_in=h) for i,(w,h) in enumerate(sizes)],
                cuts=placed,
                offcuts=[dict(sheet=i+1,x_in=x,y_in=y,width_in=w,height_in=h) for i,x,y,w,h in free])


def write_layout(layout, directory):
    directory = Path(directory)
    (directory / "plywood_layout.json").write_text(json.dumps(layout, indent=2)+"\n")
    height = sum(s["height_in"]+8 for s in layout["sheets"])
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 104 {height}">',
           '<rect width="100%" height="100%" fill="white"/>']
    offset = 0
    for sheet in layout["sheets"]:
        svg.append(f'<text x="4" y="{offset+3}" font-size="2">Sheet {sheet["sheet"]}: {sheet["width_in"]:g} x {sheet["height_in"]:g} inches; 1/8-inch kerf</text>')
        svg.append(f'<rect x="4" y="{offset+5}" width="{sheet["width_in"]}" height="{sheet["height_in"]}" fill="#eee" stroke="#333" stroke-width=".15"/>')
        for i, cut in enumerate(layout["cuts"],1):
            if cut["sheet"] != sheet["sheet"]:
                continue
            x,y = cut["x_in"]+4,cut["y_in"]+offset+5
            label = f'{i}: {cut["name"]} ({cut["width_in"]:g} x {cut["height_in"]:g})'
            svg.append(f'<rect x="{x}" y="{y}" width="{cut["width_in"]}" height="{cut["height_in"]}" fill="#c5a87b" stroke="#333" stroke-width=".1"><title>{escape(label)}</title></rect>')
            svg.append(f'<text x="{x+.2}" y="{y+min(1.5,cut["height_in"]*.8)}" font-size="1.2">{i}</text>')
        offset += sheet["height_in"]+8
    svg.append('</svg>')
    (directory / "plywood_layout.svg").write_text('\n'.join(svg)+'\n')
