# Printed gusset bearing covers

Two shallow ASA/ABS caps support the roof siding where the 6-inch gussets
interrupt the plywood strips. Each has bearing lands at **3/4 inch above the
framing**, matching the strip tops. The underside is a ribbed, open-bottom
cover over the plate and all 16 existing pan heads. These are prototype bearing
accessories; printed-part load capacity and long-term creep have not been tested.

Generate the parts with:

```sh
uv run tools/generate_gusset_covers.py
```

The normal `uv run build.py --no-deploy` also exports these parts and includes
them in the enclosure model, BOM and siding-preparation build step.

| File in `output/gusset_covers/` | Location | Quantity |
| --- | --- | --- |
| `gusset_cover_1.stl` / `.step` | Back-left gusset | 1 |
| `gusset_cover_2.stl` / `.step` | Front-right gusset | 1 |

STLs are in **millimetres**, already oriented with the roof-bearing face down.
STEP files use installed orientation, with XY measured from the steel plate's
minimum corner and Z from the lumber top. The manifest gives the corresponding
world origins in inches. Each part occupies **163.4 × 163.4 × 19.05 mm**
(6.433 × 6.433 × 0.750 inches). The two parts have different joint reliefs;
keep their installed X/Y axes aligned with the enclosure. In installed axes,
relief channels run along X, parallel to the front of the enclosure.

## Bearing and fit

- The skirt reaches **5.5 mm (0.217 inch)** beyond each plate edge. This leaves
  **0.85 mm (0.033 inch)** inside the verified 6.35 mm (1/4-inch) plate-to-frame
  margin. Its inner face clears the plate by **0.6 mm per side**. The skirt is
  4.9 mm thick and bears on the exposed framing wherever framing is present.
- Internal **2.4 mm webs** bear on the steel between the screw rows. They do
  not rest on the heads. The underside of the continuous 4 mm deck is at 8 mm;
  the modeled plate-plus-head stack is 4.674 mm, leaving **3.33 mm overhead**.
  Measure the actual screw heads before printing; the model uses 8.89 mm
  diameter and 2.794 mm height above the 1.880 mm plate.
- Raised lands reach the plywood support plane only beneath full-thickness
  roof-board material. Joint channels are **7.05 mm deep**, with 0.6 mm lateral
  allowance on either side of the modeled joint. The shallow deck continues
  beneath them to keep the cap connected. This follows the project's simplified
  US135 profile and provisional 130 mm pitch; verify against engaged boards.
- **6 mm wide × 3 mm high drainage gates** in the skirt and web bottoms connect
  the screw wells to the open perimeter. Keep these gates clear.
- Plywood strip ends now stop **1/4 inch from the steel**, leaving 0.85 mm
  between the printed cap and the strip wherever their extents overlap. Existing
  strip-anchor locations are recalculated against the shortened strips.

The load path is siding → raised lands → deck/webs/skirt → plate/framing.
The cap supports bearing only. Keep siding and trim fasteners in the designated
plywood or lumber; do not substitute printed plastic for their screw engagement.
No gusset screw is removed, loosened or lengthened to install the cap.

## Printing

Use ASA or ABS with the filament manufacturer's enclosed-printer settings.
Start with a **0.4 or 0.6 mm nozzle, 0.2 mm layers, at least 6 perimeters,
6 top/bottom layers, and 40–50% infill**. Preserve solid webs and skirt in the
slicer. A brim may help keep the wide part flat. Confirm that the slicer preserves
the exact 19.05 mm installed height; layer quantization must not lift the roof.
These are starting settings, not a verified strength specification.

Print the supplied STL bearing face down. Use build-plate supports under the
recessed joint channels and edge reliefs. The open screw wells and ribs then
build upward without buried support. Remove the channel supports completely;
do not fill the reliefs or drain gates with adhesive. Keep the bearing lands
flat, and avoid a brim or elephant foot that changes their contact plane.
Do not apply a generic shrink compensation without measuring a sample; the
0.6 mm side clearance is already built into the CAD.

## Installation check

1. Place cover 1 over the back-left plate and cover 2 over the front-right plate.
   Both slide on from above with the ribs downward. The surrounding skirt
   locates the cap; it is not a snap fit or a gasket.
2. Confirm all feet seat, the cap does not rock, and no screw head contacts a
   rib. Check deck flatness with a straightedge spanning adjacent plywood.
   Neither the skirt nor any web projects below the framing top plane.
3. Dry-fit the actual roof courses. Align each joint with its relieved channel;
   verify the board backs bear on the lands and the mating lips stay clear.
   Regenerate if the measured course pitch or board position changes.
4. Install the roof boards with their existing supported wood fasteners. They
   capture the floating caps vertically; the skirts limit lateral movement.
   Secure the caps temporarily during assembly if needed, then remove the
   temporary restraint. Check drainage paths before closing the roof.

Treat the first prints as fit prototypes before making production parts. The geometry
checks verify modeled clearances, single-solid CAD and alignment; they do not
establish snow, uplift or thermal-creep capacity.
