# Custom-gusset top-diagonal detail

## Status and purpose

This document records the implemented replacement for the catalog-plate joint
in the previous top-bracing commit. The structural screening load and member
checks remain in [`TOP_BRACING.md`](TOP_BRACING.md).

## Implemented framing

- `brace_fl_bl` and `brace_fr_br` remain top-flush 4x4 side members from
  `z = 43.50` through `z = 47.00`.
- The front and rear perimeter members remain top-flush 2x4s.
- `post_bl` and `post_fr` are 3/4 inch shorter than the other posts and stop at
  `z = 46.25`. They are not rabbeted.
- The diagonal is ripped from nominal 1x6 stock to a calculated 4.907-inch
  default finished width and occupies `z = 46.25` through `z = 47.00`. Its
  35.133-inch rectangular blank follows the post-center line at 37.44 degrees.
  Both ends are jigsawed to the modeled six-sided footprint, fully covering
  both post tops without crossing their exterior XY faces.
- The diagonal's footprint is routed 3/4 inch into the four intersected side
  braces. There are no routed post seats.

The angled board fills both shortened posts' complete top footprints. Its
minimum width is recalculated from post spacing as the square-post projection
normal to the center-to-center brace axis.

## Custom gusset

Each involved corner receives one flat 6-by-6-inch laser-cut plate. The plate
is positioned against the corner's two exterior post faces and extends inward,
covering the post, both adjoining side braces, and the diagonal.

Fabrication specification:

| Property | Value |
|---|---:|
| Material | G90 galvanized steel |
| Thickness | 0.074 inch |
| Overall outline | 6.000 by 6.000 inches |
| Hole pattern | 4 by 4 square grid |
| Hole center coordinates on each axis | 0.750, 2.250, 3.750, 5.250 inches |
| Hole diameter | 13/64 inch (0.203125 inch) |
| Quantity | 2 identical plates |

The DXF uses inches and contains one closed outline plus sixteen circle
entities on the `CUT` layer. Generate it with:

```text
uv run python tools/generate_gusset_dxf.py
```

The committed result is `fabrication/gusset_plate_6x6.dxf`; a normal model
build also writes `output/gusset_plate_6x6.dxf`.

## Fasteners

Model sixteen #9 pan-head screws per plate, thirty-two total. The OpenSCAD
geometry represents only each pan head above the plate. Neither the model,
DXF, BOM, nor instructions model or specify screw length.

The uniform grid is positioned so its centers lie over the post, side braces,
or diagonal in the default geometry. Final screw type, length, coating,
penetration, edge distances, and group capacity require an approved structural
connection design. The custom plate must not be assigned a catalog connector's
published capacity.

## Roof interface

The plate plus modeled screw head projects 0.184 inch above `z = 47.00`.
The 1/4-inch ripped pressure-treated shims cover the exposed perimeter framing
and both non-gusseted corner posts, stop at the gusset envelopes, and retain the
roof support plane at `z = 47.25`. The decking spans the short interruptions and
finishes at `z = 48.25`.

## Acceptance checks

Before removing temporary bracing, verify:

- the shortened posts terminate at the diagonal underside and have no routed
  top seats;
- no diagonal geometry extends past the exterior XY faces of either involved
  post;
- all four side-brace rabbets are flat, full depth, and free of splits;
- both gussets sit flat across the modeled intersection;
- every screw location has solid wood below it;
- the selected fasteners and custom plate have an approved capacity for the
  798-pound ASD diagonal demand documented in `TOP_BRACING.md`;
- roof shims stop clear of the plates and heads while preserving drainage; and
- tambour, wiring, siding, and service clearances remain unobstructed.

## Decision log

| Date | Decision | Result |
|---|---|---|
| 2026-07-27 | Fully cover both shortened post tops with the diagonal. | The brace now follows the post-center line, is ripped from 1x6 stock to the calculated minimum width, and has jigsaw-profiled ends. |
| 2026-07-27 | Remove the former diagonal extensions beyond the posts. | Superseded by the full-post, jigsaw-profiled detail above. |
| 2026-07-27 | Shorten the involved posts instead of rabbeting them. | `post_bl` and `post_fr` stop 3/4 inch below the frame top. |
| 2026-07-27 | Retain rabbets only at intersected side braces. | Four routed seats remain. |
| 2026-07-27 | Replace HTP37Z hardware with custom gussets. | Two identical 6-by-6-by-0.074-inch G90 plates with sixteen-hole grids are modeled. |
| 2026-07-27 | Leave #9 pan-head screw length open. | Heads and quantities are modeled; length is absent from all specifications. |
