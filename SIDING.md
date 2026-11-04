# US135 enclosure siding and roof cover

Walls use horizontal NewTechWood US135 in the manufacturer's orientation,
finished face outward, installed **bottom upward on AW08 clips**. Layout is
calculated from the full top board downward so all walls share seam elevations.
The ripped bottom starter preserves its upper engagement edge and is installed
first. US20 remains the applied corner, opening and roof-edge trim.
Generate with `uv run build.py --no-deploy`. Dimensions are inches.

## References and sample checks

The supplied [horizontal guide](ALL_WEATHER_Siding_Horizontal_Installation_Guide.pdf)
(09.16.25 US) governs reference installation and movement details. The
[US135 drawing](https://www.newtechwood.com/pdf/US135_Architect_DWG_US.pdf)
shows AW08 at every support, one locked clip per board, 142 mm overall width
and nominal 13 mm thickness. It says not to scale the drawing.

The model retains 1/2-inch stock thickness and **provisional 130 mm installed
pitch**. The triangular V-groove envelope is provisionally 3 mm wide by 1.5 mm
deep. The modeled wall stand-off is 8 mm, matching nominal T-7 height; verify
production clip seating and the actual profile. These are adjustable fields
on `US135Siding`: `course_pitch`, `wall_standoff`, `groove_width`, `groove_depth`.
No texture or exact clip machining is represented. Geometry shows real recessed
joint relief rather than painted seam lines.

Dry-fit production boards, AW08 and T-7 before cutting. Measure engaged pitch,
visible groove, stand-off, screw clearance and starter engagement. The ripped
bottom starter is a **custom adaptation**, not the guide's normal AW02 start.
The unchanged roof cover is also custom. Manufacturer acceptance and connection
capacity of these adaptations remain unverified.

## Field layout and bottom-up installation

`output/siding_field_layout.pdf` gives nominal dimensions below **level post
tops**, a common course table, top trim overlap, and four wall elevations.
JSON and CSV companions retain unrounded dimensions. Negative offsets mean
above the datum. Course IDs count from the top; installation order counts from
the bottom. The field sheet is a nominal layout, not an as-built survey.

1. Verify the post-top datum with a level. If the actual tops differ, transfer
   one common level datum rather than following each post independently.
2. Dry-fit production boards and measure pitch. Update the model and regenerate
   if needed; do not distribute cumulative pitch error through the courses.
3. Mark the starter upper edge and all visible seams around the enclosure.
   Use the same marks across corners and the rear opening.
4. Scribe the starter bottom to local grade plus 3/4 inch, checking high spots.
   Preserve the upper engagement profile. Face-fix its lower edge over T-7
   spacers into wood backing; attach AW08 at supported upper-edge stations.
   Stoppers space the board; screws obtain retention from the backing.
   The high-grade rear starter wing is very narrow below the engagement lip:
   verify usable material and screw edge distances before drilling. Schematic
   centers do not establish an adequate connection.
5. Engage subsequent courses upward. Attach AW08 at every supported upper-edge
   station, with support spacing no more than 16 inches. Lock one midpoint clip
   per physical board using the guide's locking screw; leave other clips free
   for movement. Each rear wing is a separate physical board.
6. At cutout exceptions and the full top board, face-fix over T-7 into backed
   locations. One fixed connection per board; other face holes allow movement.
   The notched rear top board remains one physical board. Gold hardware marks
   fixed connections. Head and spacer envelopes are schematic.
7. Apply US20 after boards. Verify screw-head coverage: the 40 mm top angle
   does not necessarily conceal face screws below the upper engagement lip.
   Exposed exceptions remain visible in the model and installation manifest.

## Top board, trim and interfaces

The full physical top profile remains at the existing wall-top elevation;
US20 obscures part of it. The field sheet distinguishes physical width,
exposed face height and trim overlap away from the front fixture relief.
Review `siding_review_top.scad`, `siding_review_top_section.scad`,
`siding_review_joint.scad`, `siding_review_starter.scad` and the four
`siding_corner_*.scad` views. These preserve actual cutouts and trim relief.

Clip stand-off moves wall faces outward; fixture and outlet placement follow
that face. Roof support height and board thickness remain unchanged. Roof-edge
US20 spans the revised wall perimeter and existing roof edge. Check actual
trim bearing and fastening reach before cutting. Retain 1/8-inch end allowances,
corner-to-roof trim clearance, independent trim movement and drainage paths.
The gap envelope remains pieces up to 8 feet at 32 F or warmer; check the guide
for actual installation conditions. Keep existing backing, animal infill and
mesh, with the rear service opening accessible.

## Roof cover and review files

Roof boards run along X and courses progress along Y. Each full-width board
rests on two continuous **3/4-inch PT exterior structural plywood strips**,
provisionally 1.5 inches wide. Rip with the panel strength axis along X. Place
the low-Y strip directly beneath the recessed fastening lip and keep the
high-Y strip clear of the underside rebate. The narrow
rear course uses one backer instead of overlapping strips. Verify these bearing
zones against the production profile before ripping plywood.

The strips replace the intermediate roof backing, perimeter shims and diagonal
shim. Their bottoms bear on the common framing/diagonal top plane, z = 49.625.
Open channels between strips leave the middle of each full board exposed below;
keep joint outlets and perimeter drainage open. Do not sever strips transversely
for drainage. This arrangement does not establish manufacturer acceptance of the
ventilation or exposed-roof adaptation. Treat cut plywood edges as required by
the selected preservative system; verify exterior bond, grade and actual thickness.

Shorten strip ends around the steel gusset envelopes with 1/4-inch clearance,
leaving room for the [printed gusset bearing covers](GUSSET_COVERS.md). The
covers support the roof siding at these interrupted edges, flush with the
plywood. Their bearing bands continue only the interrupted plywood runs, with
open gaps and recessed ribs between bands. Each extends inward in Y to the
inner edge of its interrupted runs. The covers are floating
bearing pieces, captured by the installed roof boards. Keep siding and trim
fasteners in their specified wood backing. The
strips bear on the existing perimeter framing and diagonal, without local
support blocks below the diagonal. This preserves the 1-inch modeled clearance
between the diagonal underside and the prototype tambour hardware envelope.
The strip anchors retain their existing supported locations. Remaining strip
bearing and roof load capacity are unverified.

Anchor each plywood strip independently near its two ends at the generated
framing/diagonal-supported locations. Recess anchor heads flush in plywood so
they do not clamp the siding. Field-select anchor screw length and penetration.

Roof screws are separately counted: provisional **#8 x 7/8-inch stainless
retaining-head screws**, nominally 5/8-inch penetration through the recessed
1/4-inch overlap into 3/4-inch plywood. The default layout uses **21 screws**,
replacing the former 39 screws in two face rows. This is a geometric candidate,
not a verified fastener product or connection capacity. Check the actual stack, contained tip, usable
thread engagement, head retention and sliding-hole behavior.

Install roof courses **from rear (+Y) toward front (-Y)**, beginning with the
ripped rear course. Each board receives one straight-down screw row at the
midpoint of its recessed low-Y overlap, provisionally 6 mm from the profile
edge. The next frontward board covers that row; front US20 covers the final
frontmost row. Retain both bearing strips on full boards even though only the
low-Y strip carries siding screws. Keep screw stations at no more than 10-inch
spacing, with one midpoint fixed connection per physical board and sliding
connections elsewhere. Independently anchor both strips before laying boards.

Dry-fit the production joint before drilling: verify lip retention, head
clearance, joint engagement without clamping the neighboring board, and actual
screw penetration. Do not angle screws through the tongue. The simplified model
shows heads on a half-thickness recess; it does not establish usable machining
or connection capacity. Roof uplift retention remains unverified.

Use 2-1/2-inch roof trim screws through horizontal US20/board/plywood into
framing, preserving the former nominal framing penetration. Wall trim retains
2-inch screws. Verify actual landing and penetration; trim carries no roof load.
This level cover permits leakage; snow, uplift, ponding and exposed-roof capacity
remain unverified. The [ceiling guide](https://www.newtechwood.com/pdf/All_Weather_Siding_Ceiling_Installation_Guide.pdf)
informs movement guidance without establishing this support arrangement's capacity.

Plywood purchasing uses a shared guillotine cutting layout for roof strips and
fitted 3/4-inch wall infill, including 1/8-inch saw kerfs. The default cuts fit
one 4 x 8 ft PT sheet. Larger builds compare additional sheets with 2 x 4 ft
panels at an assumed 0.49 of a full sheet's cost. This is a feasible layout,
not a proof of the optimal stock count. Roof strips retain the sheet strength
axis along their length; wall infill blanks may rotate.

Side-wall animal infill sits within the framing thickness, flush with the
inside post faces. Front animal infill sits farther back, with its rear face
flush with the rear face of front_center_rail. Separate panels close the bays
on both sides of that rail, between the two lower horizontal rails, below the
lowest rail. The strip above the header stays at the inside front-post
plane, up to the front brace, to clear the future tambour handle. Fit around the
permanent timber and outlet. Bore the front between-rails panel snugly around
the existing power_ev_back_adapter barrel (nominal 1.35 inches) and seal any
residual seam; toe-screw from the interior panel face into adjacent
lumber. Separate upper-front numeral panels cover both bays near the exterior,
set back 1/4 inch from the post and siding-backing faces, replacing the narrow
support board. Use rigid spacers across the setback at numeral attachments and confirm
mounting screw engagement. Retain the exterior mesh skirt and add a continuous inner ground-gap wrap
along both side-wall infills and the new front plane. Join the front corners,
terminate the side runs against the posts, and overlap mesh joints 2 inches.
Sample grade at the installed panel and mesh coordinates. Screen tiny seams, keep the
rear opening accessible, and omit all ceiling panels for future tambour access.
See BUILD_STEPS.md steps 19 and 22 for fitting and attachment details.

Generated files include:

- `output/plywood_layout.svg` and `.json`: shared sheet layout and usable offcuts.
- `output/model.scad`: enclosure, schematic recessed/face screw heads and bottom-up wall build steps.
- `output/roof_support_review.scad`: cropped roof framing, gussets and strips; render with `openscad -D build_step=22`.
- `output/gusset_covers/`: two ASA/ABS bearing covers as millimetre STL/STEP files and a placement manifest.
- `output/siding_corner_*.scad`: four cropped roof/wall corner views.
- `output/siding_cut_list.csv` and `.json`: physical board, backing and trim cuts.
- `output/siding_installation.json`: supported attachment locations, fixed
  points, concealment classifications, exception reasons, course order and prototype assumptions.
- `output/siding_bom.csv`: siding purchase quantities and installation notes;
  the repository-root `siding_bom.csv` is the current default-build snapshot.
- Shared BOM, cut and shopping lists include the revised materials/hardware.
