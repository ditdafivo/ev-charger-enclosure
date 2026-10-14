# Retarget the Tambour Fabrication Parts for a Bambu Lab X2D

## Objective

Update the printable tambour track and pull-handle design so every generated
part fits the Bambu Lab X2D, while preserving the installed door path and the
existing rail profile. The X2D replaces the Voron 2.4 with a 350 mm build area
as the target printer for the generated parts.

This is a CAD-generation and documentation change. The door's enclosure
interfaces, slat dimensions, bend geometry, running clearances, material, and
track mounting concept remain the design baseline.

## Printer envelope

Bambu Lab specifies a 256 x 256 x 260 mm build volume for the X2D main hotend.
The auxiliary hotend has a 235.5 x 256 x 256 mm printable area. Use the main
hotend for the single-material ASA track and handle parts and validate against
the main-hotend envelope. Do not rely on the auxiliary hotend's smaller region
for a part's primary geometry. See the [X2D user manual](https://csm.bblcdn.com/hub/7c58718aaa2e40edab56efb87419a96a.pdf)
and [Bambu Lab X2D specifications](https://blog.bambulab.com/xcellence-made-simple-bambu-lab-presents-the-x2d/).
Bambu Lab lists ASA among materials supported in heated mode, so retain ASA as
the track material.

Set the maximum straight-track segment length to **250 mm**. This leaves
clearance within the X2D's 256 mm horizontal limit for placement and a modest
bed-edge margin. Keep parts in their intended print orientation: track
mounting flange on the build plate, as described in `TAMBOUR_DOOR.md`. Do not
scale exported parts in the slicer.

## Current design and expected resegmentation

The fabrication defaults currently use a 300 mm straight-track limit and a
300 mm-wide pull handle in `lumber_model/tambour_fabrication.py`. The installed
path dimensions are derived in `build.py`. With the present path, the fixed
straight runs are approximately:

| Run | Fixed track length | Existing segmentation at 300 mm | Segmentation at 250 mm |
| --- | ---: | ---: | ---: |
| Rear | 864.25 mm | 3 x 288.08 mm | 4 x 216.06 mm |
| Top | 258.45 mm | 1 x 258.45 mm | 2 x 129.23 mm |
| Front | 634.05 mm | 3 x 211.35 mm | 3 x 211.35 mm |

The current layout therefore has seven straight sections per side; the X2D
layout will have nine per side. Including the loading section and two bends,
that changes from ten to twelve track pieces per side. The design uses two
collar shoes at each joint, so the expected common-collar quantity increases
from 36 to 44. Keep this quantity derived from the part and joint counts rather
than hard-coding it.

The bend part's plan-view bounding dimensions are approximately 113.4 x
113.4 mm. Keep its current 2 5/8-inch centerline radius and tangent stubs. Keep
the channel, flange, expansion slot, drainage, dovetail pads, collar, and
fastener geometry unchanged unless a fit check exposes a specific X2D issue.
The added straight-track seam locations must continue to be calculated from
the same segment-splitting configuration used to generate the parts, so the
visualized/modelled seams and fabrication exports stay aligned.

## Pull-handle size

The single-piece pull handle is currently 300 mm wide, which exceeds the X2D
build volume in every orientation because its longest dimension is greater
than the 260 mm Z limit as well. Set `handle_width` to **250 mm** for the
X2D-targeted design. Update the fabrication guide, design plan, model-derived
display dimensions, and related tests to use the configured value. Retain the
centered grip, attachment pattern where it fits, 5/8-inch maximum projection,
one-slat attachment, and the existing swept-depth constraint. The 15-pound
proof-load and bend-clearance requirements still apply to the revised handle.

## Implementation work

1. In `lumber_model/tambour_fabrication.py`, set the default maximum straight
   segment length to 250 mm and the handle width to 250 mm. Preserve the
   existing equal-segment division behavior. Replace fixed 350 mm constructor
   guards with checks against the selected printer envelope. If retaining
   multiple printer targets, represent their envelopes explicitly.
2. Replace the scalar 350 mm bed-fit assumption with an axis-aware build-volume
   check for 256 x 256 x 260 mm. Make the checked dimensions explicit and keep
   error messages tied to the X2D envelope. Ensure the validation reflects the
   exported print orientation.
3. Keep `build.py`'s path and seam calculations derived from the fabrication
   configuration. Confirm the new mid-top seam and additional rear seam per
   side are reflected wherever the tambour track seams are modelled or shown.
4. Review generated part bounding boxes, including bends, loading sections,
   end stops, collars, coupons, and handles. All parts must fit without
   scaling. Keep the ASA channel and flange dimensions and mounting interfaces
   consistent with the enclosure.
5. Update references to the 350 mm printer, 300 mm maximum track length, and
   300 mm handle width in `README.md`, `TAMBOUR_DOOR.md`,
   `TAMBOUR_ASA_TRACK_PLAN.md`, code comments, and tests. State the X2D print
   orientation and 250 mm limit clearly in the fabrication instructions.
6. Update the fabrication tests to cover the X2D dimensions, the revised
   segment counts and collar quantity, handle fit, and part validity. The
   printed mesh/STEP generator should continue to emit its manifest and named
   part exports.

## Acceptance criteria

- The default generated track sections are no longer than 250 mm.
- The current modeled route produces four rear, two top, and three front
  straight sections per side, with lengths summing to the corresponding fixed
  run lengths.
- The generated assembly has the new seams in the corresponding positions
  and a derived collar-shoe quantity of 44 for the current enclosure geometry.
- The pull handle is 250 mm wide, fits the X2D main-hotend envelope, remains
  centered on one slat, and meets the existing projection and swept-envelope
  limits.
- Every generated part fits within 256 x 256 x 260 mm in its intended print
  orientation. Track bends, loading pieces, hardware, and coupons retain their
  existing geometry and remain valid solids.
- The track remains compatible with the existing full-size path, support
  spacing, mounting faces, 2.4 mm minimum wall design, joint hardware, and ASA
  material specification. Confirm the intended X2D nozzle diameter in the
  printer profile and preserve the existing 0.6 mm nozzle-based geometry when
  that nozzle is supported.
- Project docs and tests consistently describe the X2D target, its build
  envelope, the 250 mm segment limit, and the configured handle width.
- The fabrication generator can export the full set and individual named
  parts without a printer-envelope rejection.

## Suggested verification for the implementation task

Run the tambour fabrication and model-build test suites, then generate the
fabrication set and inspect its manifest for part dimensions and quantities.
Open the generated track assembly/preview and confirm every added seam matches
the modelled path. In Bambu Studio, verify the exported parts fit the X2D plate
in the documented orientation without automatic scaling.
