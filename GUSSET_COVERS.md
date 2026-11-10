# Printed gusset bearing and fastening covers

Two ASA/ABS covers bridge the plywood runs interrupted by the 6-inch steel
gussets. Bearing surfaces sit **19.05 mm (3/4 inch) above framing**, flush with
plywood tops. Full-height outer lands provide a US20 fastening base on each
corner side. Two recessed inward tabs per cover accept long wood screws into
the perimeter braces. All holes are **field-drilled**.

## Generate and customize

```sh
uv run tools/generate_gusset_covers.py
uv run tools/generate_gusset_covers.py --outward-x-mm 6.35 --outward-y-mm 8 --inward-x-mm 30 --inward-y-mm 25 --tab-width-x-mm 25 --tab-width-y-mm 25 --tab-recess-x-mm 6 --tab-recess-y-mm 6
```

All dimensions below are **millimetres**. X runs parallel to the front/back
braces; Y runs parallel to the side braces. Each axis is independently adjustable
and the same base specification is mirrored for both covers. Each cover also
has the additional outward X/Y offsets listed below.

| Parameter / CLI option | Default | Reference |
| --- | --- | --- |
| `outward_x_mm` / `--outward-x-mm` | 6.35 | Beyond the outside left/right framing edge |
| `outward_y_mm` / `--outward-y-mm` | 6.35 | Beyond the outside front/rear framing edge |
| `back_left_outward_x_extra_mm` / `--back-left-outward-x-extra-mm` | 5.5 | Additional negative-X reach on back-left cover |
| `back_left_outward_y_extra_mm` / `--back-left-outward-y-extra-mm` | 4.7625 | Additional positive-Y reach on back-left cover |
| `front_right_outward_x_extra_mm` / `--front-right-outward-x-extra-mm` | 3.175 | Additional positive-X reach on front-right cover |
| `front_right_outward_y_extra_mm` / `--front-right-outward-y-extra-mm` | 4.7625 | Additional negative-Y reach on front-right cover |
| `inward_x_mm` / `--inward-x-mm` | 25 | Along the front/back brace beyond the existing cover edge |
| `inward_y_mm` / `--inward-y-mm` | 25 | Along the side brace beyond the existing cover edge |
| `tab_width_x_mm` / `--tab-width-x-mm` | 25 | Across the X-running tab, centered over its brace |
| `tab_width_y_mm` / `--tab-width-y-mm` | 25 | Across the Y-running tab, centered over its brace |
| `tab_recess_x_mm` / `--tab-recess-x-mm` | 6 | X-tab top below siding underside |
| `tab_recess_y_mm` / `--tab-recess-y-mm` | 6 | Y-tab top below siding underside |

Reaches must be finite and nonnegative; zero inward reach omits that tab. Widths
must be positive and fit within the supporting brace. Recesses must be positive
and less than 19.05 mm. Defaults leave **13.05 mm thick tabs**, with 6 mm for
screw-head clearance. Confirm actual #10 flange-head dimensions during fitting.

Python callers can pass `spec=GussetCoverSpec(...)` to `covers_for_siding` or
`generate_gusset_covers`. The enclosure model and normal
`uv run build.py --no-deploy` use the same defaults. Custom standalone exports do
not change the enclosure configuration.

| File in `output/gusset_covers/` | Location | Quantity | Default X × Y × Z |
| --- | --- | --- | --- |
| `gusset_cover_bl.stl` / `.step` | Back-left | 1 | 201.1 × 223.9625 × 19.05 mm |
| `gusset_covet_fr.stl` / `.step` | Front-right | 1 | 198.775 × 207.3875 × 19.05 mm |

The [top-view preview](output/gusset_covers/preview.svg) shows blue bearing/trim
lands, orange recessed anchor tabs, gray framework and tan adjacent plywood.
STLs are in millimetres, bearing faces down, translated to nonnegative print
coordinates. STEP and SCAD use installed axes relative to the steel plate's
minimum corner, with Z from the framing top. The manifest records effective
parameters, world origins in inches, original bearing-band and framework bounds,
new land/tab boxes, actual total sizes and solid volumes. The covers differ.

## Bearing, clearances and field relief

The original bearing bands follow the interrupted plywood runs, including the
rear closure strip. Only the outermost band continues outward in Y; X extensions
continue the individual bands. Spaces between runs retain recessed framework.
Outer lands reach **1/4 inch beyond the brace edges** by default, independently
of the original plate-locating skirt. The front-right land adds **1/8 inch in
positive X** and **3/16 inch in negative Y**, for total reaches of **3/8 inch
positive X** and **7/16 inch negative Y**. Plywood, siding boards and US20
geometry are not extended by this generator; coordinate their field fitting
with the new lands.

The back-left offsets instead give **11.85 mm beyond the left framing edge**
and **11.1125 mm (7/16 inch) beyond the rear framing edge**. These put the outer
edges **1/2 inch farther in negative X** and **9/16 inch farther in positive Y**
than the original field-trimmed fabrication cover before fastening extensions
were added. In structure coordinates, that original left edge was X = +0.85 mm;
the new edge is X = -11.85 mm. The original rear edge was Y = 22.75 inches;
the new edge is Y = 23.3125 inches in the default enclosure. Plate seating and
the inward tabs retain their existing positions.

The original skirt extends 5.5 mm beyond the plate, with 0.6 mm plate clearance.
Fabrication exports retain the **2.325 mm back-left rear skirt trim**, ending the
original framework at plate-relative Y = 155.575 mm. The enclosure model retains
its nominal rear framework edge at 157.9 mm. This trim never clips the new outer
fastening land. The inward framework edges still follow the interrupted plywood
runs; new tabs extend from those edges along each brace.

Internal 2.4 mm webs bear on steel between screw rows. Original bearing bands
start at Z = 8 mm, leaving 3.33 mm above the modeled steel/head stack. The model
uses 8.89 mm diameter heads, 2.794 mm high above 1.880 mm steel. Preserve existing
gusset screws. Original 6 × 3 mm drainage gates and extension feet remain;
keep their outlets clear.

**Field-cut plywood relief is required wherever the new inward tabs overlap a
plywood strip.** The tabs are solid down to the framing plane; reducing their
height clears siding and anchor heads, but does not clear plywood. Cut relief
for the actual tab footprint and verify screw access before closing the roof.
Do not drill anchors into steel or rely on a tab over an open framing bay.

## Printing and installation

Use ASA or ABS with enclosed-printer settings. Start with a 0.4 or 0.6 mm nozzle,
0.2 mm layers, at least 6 perimeters, 6 top/bottom layers and 40–50% infill.
Preserve solid webs, tabs and lands. Print bearing faces down with supports
beneath recessed ribs and tabs; check the slicer for unsupported starts and
support access. Remove supports without damaging bearing surfaces or drains.
Do not apply generic shrink compensation without measuring a sample.

1. Seat `gusset_cover_bl` at back-left, extending toward the front, and
   `gusset_covet_fr` at front-right, extending toward the rear. Check framing
   contact, plate/head clearance and absence of rocking.
2. Check the outer lands against the actual brace edges and proposed trim
   position. Adjust X/Y parameters independently and regenerate as needed.
3. Mark and cut plywood relief for the inward tabs. Verify the tabs sit on
   lumber, their tops are recessed and the remaining bearing bands align with
   adjacent plywood.
4. Field-drill each tab and positively fasten it into its brace with a long wood
   screw. Select length and position for actual lumber engagement. Confirm the
   head clears the siding underside and avoid obstructing drains.
5. Dry-fit roof boards and their profiles, including the intended extended
   spacers beneath trim. Fasten the boards, then fit US20 with one trim screw
   into the cover's full-height land on each corner side.

Treat the defaults as fit-prototype dimensions. Geometry checks establish modeled
clearances and connected solids; printed screw retention, snow/uplift capacity
and long-term creep have not been established.
