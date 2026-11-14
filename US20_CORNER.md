# ASA rounded slip-socket corner

For the separate measured-profile minimal rear-clip prototype, see
[US20_CORNER_CLIP.md](US20_CORNER_CLIP.md).

This standalone ASA elbow conceals a gapped 45° US20 roof-rim miter. Both trim
ends insert lengthwise into fully enclosed L-shaped sockets. The sleeve wraps
each trim's top, underside, inside and outside faces, and both free edges.
The cavities merge into an unobstructed corner chamber.

The rounded reference profile uses **conservative estimates from five ink
prints photographed on a 1 mm grid**. It is deliberately larger than the
apparent trim: 42 mm legs and 10 mm thickness, with 0.75 mm clearance per face.
These are not confirmed stock dimensions. Print a coupon before the full part.

There are **no clips, hooks, interference ribs, pads or insertion stops**.
The two installed trim pieces constrain the connector while remaining free to
slide. Do not rely on friction to secure it. Assemble both ends into the elbow
before fastening the trim; removal requires withdrawing a trim piece.

This replaces the earlier square-profile sleeve. The enclosure model, trim cuts and
BOM are unchanged. This sleeve needs space behind the trim that the existing
roof/siding arrangement does not provide automatically.

## Generate and inspect

```sh
uv run tools/generate_us20_corner.py
```

Outputs in `output/us20_corner/`:

- `us20_corner_cap.stl` / `.step`: the complete enclosed elbow. Existing filenames
  are preserved; the manifest identifies revision `rounded-slip-socket-v3`.
- `fit_coupon_0.50`, `fit_coupon_0.75`, `fit_coupon_1.00`: **20 mm long rounded
  sleeves**, with clearance in mm per mating surface.
- `miter_fixture_a` / `miter_fixture_b`: estimated rounded segments for bench checks.
  These are test tools, not replacement trim.
- `drawing.svg`: dimensioned plan and socket cross section showing every wall.
- `cap_exterior.svg`, `cap_underside.svg`, `socket_mouth.svg`,
  `fixture_assembly.svg`: projections from the actual CAD.
- `manifest.json`: dimensions, revision, part bounds, volumes and collision checks.

STLs have nonnegative coordinates and are already oriented **outer top face
down**. STEP files use installed axes: reference US20 outside corner at XY = 0,
trim top Z = 0, legs running along +X/+Y and down −Z. Rotate the same elbow
about Z for other corners; four-corner assembly is not integrated or verified.

Use `--leg`, `--thickness` and `--clearance` to regenerate from stock/coupon
measurements. Independent `--outside-bend-radius`, `--inside-bend-radius` and
`--end-radius` options control the reference curves. Defaults come from
`CornerSpec` in `lumber_model/us20_corner.py`. The reference uses tangent lines
and true circular arcs rather than tracing irregular ink edges. Production
texture and extrusion variation are not represented.

## Dimensions and movement

| Feature | Prototype dimension |
| --- | --- |
| Reference legs / thickness | 42 / 10 mm |
| Reference outside bend / inside bend radii | 2 / 4 mm |
| Reference free-end corner radii | 4 mm, with a 2 mm flat between them |
| Reach along each roof edge from reference outside corner | 68 mm |
| Shell walls | 2 mm |
| Running clearance per mating surface | 0.75 mm; coupon options 0.5 and 1 mm |
| Cavity thickness around each 10 mm reference leg | 11.5 mm |
| Outer offset beyond reference trim surfaces | 2.75 mm |
| Overall bounding box | 70.75 × 70.75 × 47.5 mm |
| Straight enclosed socket length beyond the elbow | 23.25 mm |
| Minimum full-profile engagement at maximum withdrawal | 18.56 mm |
| Bench travel target of each trim relative to elbow | ±3.2 mm |
| Dummy fixture gap, perpendicular to miter planes | 6 mm |

The reference uses the **smaller estimated convex outside radius** and the
**larger estimated concave inside radius** to leave more material in the
reference and therefore more space in its cavity. Simply making every radius
larger would tighten some corners. The 4 mm end corners also retain more space
than 5 mm semicircular tips.

The cavity is a 0.75 mm outward offset of the reference. Its convex outside
bend radius is 2.75 mm, inside radius 3.25 mm, and end radii 4.75 mm. The
exterior offsets those curves by another 2 mm: respectively 4.75, 1.25 and
6.75 mm. Arc centres remain fixed, preserving the wall thickness. Both the
fixtures and section drawing use this same analytic profile. The two rounded
sweeps meet on a 45° plane, avoiding bulges from overlapping curved ends. Their
cavities join on that same plane without an internal partition.

At simultaneous 3.2 mm inward travel of both pieces, the miter gap reduces by
`sqrt(2) × 3.2`, leaving about **1.47 mm**. This is a geometric travel test, not
a temperature-derived US20 gap requirement. Check the required thermal travel
before final cuts. Trim fasteners must permit independent sliding.

The enclosed sockets occupy **2.75 mm behind both reference faces**: 0.75 mm
clearance plus 2 mm ASA. Smaller actual stock may need more allowance relative
to its inner faces; this is not a confirmed installation dimension. This
includes the wall under the horizontal trim leg, between it
and the roof, and the wall behind the vertical leg, against the siding. Local
roof/siding relief or revised trim positioning needs a separate design. The
old clip-specific US46 gap and extended apron no longer apply. The bottom
return extends 2.75 mm below the reference profile and must also clear US46. Do not assume the
part can slide onto trim that is already tight against the existing boards.

## Printing and fitting

1. Print the three enclosed coupons in the intended ASA first. Start with a
   0.4 mm nozzle, 0.2 mm layers, at least five perimeters, six top/bottom layers
   and 30% infill, using the filament manufacturer's enclosed-printer settings.
   Do not apply generic shrink compensation before measuring a sample.
2. Print top face down as exported. The enclosed pocket ceilings need support
   or a verified bridge strategy. Paint removable supports under these ceilings
   and inspect their access from the open mouths. Avoid support contact on the
   sliding faces where possible. The full elbow's corner chamber is harder to
   reach than the short coupons: verify removal with pliers and a blunt scraper
   through both mouths. If supports cannot be completely removed without
   damaging the sleeve, revise the support strategy before using the part.
3. Deburr the mouths and remove all support residue. Slide each coupon onto
   an actual US20 offcut **axially**, without flexing or snapping it over an edge.
   Choose a clearance that inserts and slides freely by hand. Some looseness
   is intentional; do not select for gripping force. Record the selected
   clearance, filament, printer and settings.
4. Regenerate the full elbow with `--clearance`, then print it and the optional
   estimated rounded fixtures. Insert the first fixture through one mouth and the second
   through the perpendicular mouth. There are no stops to set their depth;
   position the miter ends using the intended gap and the drawings.
5. Check each trim independently through ±3.2 mm, then both together toward and
   away from the corner. Confirm no binding, miter collision or exposed seam,
   and at least 17 mm full-profile overlap at maximum withdrawal. Perform 100
   sliding cycles and reject cracking, distortion or increasing resistance.
6. Repeat with real offcuts and a mock roof, wall and US46 interface allowing
   the full sleeve thickness. Verify insertion access, available movement and
   the exterior appearance. Before any installed four-corner use, establish an
   assembly sequence that does not require inserting the last rigid trim between
   two immovable sockets. This is outside the standalone prototype's validation.
7. Check the fit again after warm outdoor exposure. To disassemble, release the
   trim's fastening as necessary and withdraw at least one trim piece axially.
   Do not pry the sleeve open. No added drain holes are included; the mouths
   remain open, and drainage must be checked in the actual installation.

## Checks and limits

```sh
uv run python -m unittest discover -s tests -p 'test_us20_corner.py'
```

The generator verifies clearance at nine combinations of independent travel
and two continuous axial insertion sweeps with the neighboring trim present.
It checks valid single solids before export and records minimum engagement.
Tests check all six surfaces of each L-profile sleeve, unobstructed mouths,
concealed seams, curved-wall thickness, collision detection and printable export
orientation. Containment checks cover all 24 valid endpoint combinations of
40–42 mm legs, 8–10 mm thickness, 2–4 mm outside/inside bend radii and 4–5 mm
end radii. These bounds come from approximate photo measurements; they do not
replace an actual stock fit test.

Geometry checks do not establish stock fit, support removability, ASA creep,
service life, drainage or wind retention. This is a loose cosmetic connector,
not a roof attachment or a water seal. Actual enclosure integration remains
separate from this prototype.
