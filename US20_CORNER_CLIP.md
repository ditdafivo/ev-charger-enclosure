# Minimal US20 rear-clip prototype

This separate ASA prototype conceals the miter with a narrow cover and flexible
rear hooks. The existing slip-socket generator and files remain available.
The enclosure model and BOM are unchanged.

Revision `small-radius-v4` reduces the exterior transition between the
horizontal and vertical faces from 4.25 mm to **1 mm radius**. It adds material
outside the existing rounded cavity, preserving the trim clearance. The
smaller rounded overhang is intended to reduce support near the bed; check
the slicer and a coupon print before printing the full corner.

The two primary retaining hooks sit
behind the horizontal, upward-facing trim legs. Each upper tongue follows
the diagonal seam, keeping its entire retaining return on its own trim even
at maximum withdrawal. The lower tongues end as shallow claws around only
the first 45° of the lower front rounding. They do not reach the flat rear
face or extend below the trim's bottom plane, leaving the lower rear clear
for the adjoining trim. The tapered cosmetic wings remain removed.

The measured US20 profile has **39.6 mm outside legs and 8.2 mm thickness**.
Outside bend, inside bend and free-end radii remain estimates of 2, 4 and 4 mm.
These describe the reference trim, independently of the 1 mm exterior
transition radius of the printed cover.
The cover overlaps each trim by **10 mm perpendicular to its cut edge** at
nominal position. With a 2 mm miter gap, the band is 22 mm wide normal to the
seam; it follows the entire L profile, rather than stopping 10 mm from the
outside corner vertex.

The 2 mm shell has 0.25 mm running clearance. Local tongues have a 12 mm
sweep toward the free edge, 6 mm axial width, 1.2 mm thickness and 0.6 mm
relief slots. On the full corner the upper tongue follows a diagonal path;
its path length is therefore longer than the 12 mm transverse sweep.
Upper rear capture extends 0.8 mm past the rounded-end tangent onto the
underside. The nearest upper retaining contact remains 0.75 mm beyond the
moving miter cut at maximum withdrawal. The rounded reference ends provide
lead-ins; this is a prototype flexure, not a validated snap fit.
The straight coupons reproduce the upper-hook and lower-claw sections;
always test the full corner as well to check its diagonal tongue behavior.

## Generate

```sh
uv run python tools/generate_us20_corner_clip.py
uv run python -m unittest discover -s tests -p 'test_us20_corner_clip.py'
```

Outputs in `output/us20_corner_clip/` include the corner STL/STEP, coupons at
0.15, 0.25 and 0.40 mm clearance, actual CAD exterior/rear/assembly/section
views, an annotated section drawing and a dimension/validation manifest.
All specification fields are exposed as CLI options, including `--clearance`,
`--capture`, `--tongue-length`, `--tongue-thickness` and
`--exterior-transition-radius`. The latter controls only the printed outside
bend; `--outside-bend-radius` still describes the reference trim.
STEP uses installed axes: XY outside corner at zero, top Z=0, legs along +X/+Y
and down −Z. STLs are outer top down with nonnegative coordinates.

## Fit and installation

1. Print coupons in the intended ASA, starting at 0.25 mm clearance. Start with
   0.2 mm layers and a 0.4 mm nozzle. Inspect the slicer for continuous tongue
   paths and support access; keep support residue off mating faces and slots.
2. Use a real offcut to check that the hooks can flex over its rounded free
   ends without cracking or permanent set. Engage the upper return beneath
   the horizontal leg, then seat the lower front claw. Do not force a reluctant fit. Tune the exposed clip
   parameters and print another coupon if needed.
3. Position two offcuts with a 2 mm gap perpendicular to the miter. Fit the full
   corner by engaging both upper hooks beneath the horizontal legs, then
   easing the lower front claws onto the rounding. Check both upper returns
   engage their own trim and all relief slots stay free.
4. Check each trim independently through ±1 mm and both together. CAD predicts
   at least 9.29 mm normal overlap and a 0.59 mm remaining miter gap. The hooks
   should retain the cover while permitting sliding. Cycle the assembly 100
   times and reject cracking, increasing resistance or loose retention.
5. Repeat against a mock roof, siding and the adjoining lower trim. Upper
   hooks need **1.45 mm** beneath the horizontal legs locally. Check their
   free-edge projection, roof and fastener clearance. Confirm the adjoining
   trim can butt against the lower rear without contacting a return. Release
   the lower claws and then upper hooks for removal; confirm access before
   installation. Recheck after warm exposure.

Seated collision tests cover nine travel combinations and tests verify open
rear areas, seam concealment, upper-hook contact on each incoming trim,
45° lower claw limits, bottom clearance, hook returns and relief slots. Rigid CAD does
not simulate snap insertion: the rounded return must flex around the end
radius as well as its capture, so the required opening can exceed 0.8 mm.
Neither ASA strain limits nor wind retention, creep, service life or water
sealing have been established. Actual enclosure integration remains separate.
