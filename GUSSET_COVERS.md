# Printed gusset bearing covers

Two open ASA/ABS bearing covers support the roof siding where the 6-inch steel
gussets interrupt the plywood strips. Their top surfaces continue **only the
actual plywood runs**, at **3/4 inch above the framing**, matching the plywood
tops. The spaces between runs are open except for recessed connecting ribs.
Printed-part load capacity and long-term creep have not been tested.

Generate the parts with:

```sh
uv run tools/generate_gusset_covers.py
```

The normal `uv run build.py --no-deploy` also exports the parts and includes
them in the enclosure model, BOM and siding-preparation build step.

| File in `output/gusset_covers/` | Location | Quantity | Current size, X × Y × Z |
| --- | --- | --- | --- |
| `gusset_cover_1.stl` / `.step` | Back-left gusset | 1 | 163.4 × 175 × 19.05 mm |
| `gusset_cover_2.stl` / `.step` | Front-right gusset | 1 | 163.4 × 182.425 × 19.05 mm |

[Generated top-view preview](output/gusset_covers/preview.svg) shows both covers
alongside their plywood runs. Blue is the bearing surface, gray is recessed
framework, and tan is the adjacent plywood. Dashed outlines mark the steel and
screw heads; some are hidden beneath the bearing bands in the physical part.

STLs are in **millimetres**, with the roof-bearing faces down and the part
translated to nonnegative print coordinates. STEP and OpenSCAD copies use
installed orientation, with XY measured from the steel plate's minimum corner
and Z from the lumber top. The manifest records world origins in inches,
plate-relative Y bounds in millimetres, source strip names, and actual part
sizes. Keep the installed X/Y axes aligned with the enclosure; the bearing
bands run along X, parallel to the front. The covers are different parts.

## Bearing and fit

- Each cover has three bearing bands in the default layout. Their Y positions
  and widths exactly match the plywood runs shortened by that gusset, including
  the wider rear closure strip. No broad connecting sheet remains between them.
- The back-left cover extends **11.6 mm farther inward toward the front** than
  the former square cover, reaching Y = 15.9518 inches in the enclosure. The
  front-right cover extends **19.025 mm toward the rear**, reaching Y = 7.2156
  inches. These boundaries follow the inner edges of the interrupted runs.
  Dimensions recalculate when the roof layout changes.
- The original plate-locating skirt still reaches **5.5 mm (0.217 inch)** beyond
  each plate edge, leaving **0.85 mm (0.033 inch)** inside the verified 1/4-inch
  plate-to-frame margin. Its inner face clears the steel by **0.6 mm per side**.
  The added inward extensions occupy the open area beyond the plate.
- Internal **2.4 mm webs** bear on steel between the screw rows. Bearing bands
  begin at Z = 8 mm, leaving **3.33 mm overhead** above the modeled steel/head
  stack. Measure actual heads before printing: the model uses 8.89 mm diameter
  and 2.794 mm head height above the 1.880 mm plate.
- All connecting ribs stay at or below Z = 8 mm, **11.05 mm below the siding**.
  Longitudinal ribs continue into the extensions, with a transverse tie at the
  new inward edge. Extension feet reach the lumber only where the ribs overlap
  existing top-flush framing; no support is assumed beneath open areas.
- Original **6 × 3 mm drainage gates** remain in the skirt and web bottoms.
  Added feet have gates along their longer direction where space permits;
  short feet remain solid. Keep the framework and outlets clear.
- Plywood still stops **1/4 inch from the steel**, leaving **0.85 mm** between
  the cover and plywood ends. Strip lengths and fastener positions are unchanged
  by this revision. Both covers clear the siding's modeled mating profiles.

The load path is siding → bearing bands → webs/skirt/feet → steel/framing.
Keep siding and trim fasteners in their designated plywood or lumber. No gusset
screw is removed, loosened or lengthened. Roof boards capture the floating
covers vertically; the original skirts limit lateral movement.

## Printing

Use ASA or ABS with the filament manufacturer's enclosed-printer settings.
Start with a **0.4 or 0.6 mm nozzle, 0.2 mm layers, at least 6 perimeters,
6 top/bottom layers, and 40–50% infill**. Preserve solid webs and skirt in the
slicer. A brim may help keep the part flat. Confirm that layer quantization
preserves the 19.05 mm installed height. These are starting settings, not a
verified strength specification.

Print the supplied STL bearing faces down. Enable build-plate supports beneath
recessed connecting ribs that bridge the open gaps between bearing bands. Those
ribs begin 11.05 mm above the bed in this orientation. Inspect the slicer preview
for unsupported starts and check support access before printing. Remove all
supports and brim material, keeping bearing faces flat and drain gates open.
Do not apply generic shrink compensation without measuring a sample; the
0.6 mm plate clearance is already built into the CAD.

## Installation check

1. Seat cover 1 over the back-left plate, extending toward the front. Seat cover
   2 over the front-right plate, extending toward the rear. Both slide down from
   above with the ribs downward. Verify that the added feet bear on framing.
2. Check that each cover sits without rocking and clears every screw head.
   Use a straightedge across the bearing bands and adjacent plywood to confirm
   their tops align. No rib or foot projects below the framing top plane.
3. Dry-fit the roof courses. Check that each bearing band continues its plywood
   run, supports full-thickness board material, and clears the mating profiles.
   Regenerate the covers if the measured board pitch or strip layout changes.
4. Install the boards with their specified wood fasteners. Use temporary
   restraint for the floating covers during assembly if needed, then remove it.
   Check the open gaps and drainage gates before closing the roof.

Treat the first prints as fit prototypes. Geometry checks verify modeled
clearances, connection of the CAD solids and alignment; they do not establish
snow, uplift or thermal-creep capacity.
