# US135 enclosure siding and roof cover

The enclosure uses horizontal NewTechWood US135, installed **from the top
downward**, with the wall profiles **upside down and finished face outward**.
Screws into open lumber framing are normally concealed by the next lower board’s
overlap; US20 conceals edge exceptions where its actual coverage permits.
US20 L-angle covers all four outside corners, the rear access opening and the
roof perimeter. There are no AW08 clips, T-7 spacers, US46 or US44 profiles.
Generate the model and fabrication files with `uv run build.py --no-deploy`.
Dimensions are inches.

This is a **custom concealed face-fastened adaptation**, not the manufacturer's illustrated
US135 attachment system. The supplied [horizontal installation guide](ALL_WEATHER_Siding_Horizontal_Installation_Guide.pdf)
(09.16.25 US) controls the reference material and movement guidance; its face
fastening details do not establish an approved all-face-fastened connection
schedule. The [US135 drawing](https://www.newtechwood.com/pdf/US135_Architect_DWG_US.pdf)
shows AW08 at every support. Connection capacity and manufacturer acceptance
of this adaptation remain unverified.

## Dimensions and fabrication status

US135 All Weather Pro has a straight-grain face and V-groove course joints.
The model uses 142 mm overall width, 1/2-inch thickness and a **provisional
130 mm installed course pitch**. Measure two engaged production boards before
cutting. The simplified mating rebates and seam markings do not reproduce the
machining profile or grain texture. The 0.002-inch preview clearance between
rebate faces prevents flicker without changing stock dimensions or pitch.

Boards seat directly on framing, with **zero added stand-off**. The finished
wall face is 1/2 inch outside the framing; the front face is y = -0.5. Fixture,
numeral and outlet positions follow that face. The wall top remains z = 50.125.
The 3/4-inch PT plywood strips replace the roof shims and intermediate roof
backing, putting roof support at z = 50.375 and the roof board top at z = 50.875.
Schematic US20 thickness adds 0.22 inch above that.

The defaults give ten wall courses. Solid-wall top boards retain their full
profile height. The rear top board is one physical board with an access notch;
each lower rear wing is a separate physical offcut. Rendered opening fragments
do not multiply the stock-board count or fixed-point count.

Before cutting production pieces, dry-fit two courses on representative lumber.
Check rear-profile seating, engagement in the inverted orientation, installed
pitch, usable overlap material, screw access, head clearance and retention, and
movement-hole behavior. The modeled row is at the overlap midpoint, provisionally
6 mm (0.236 inch) from the original lower profile edge; it is not a drilling
dimension. Schematic heads sit on the recessed fastening surface and may intersect
the simplified covering tongue. No head cavity or machining relief is specified;
the physical profile must provide clearance without clamping the adjacent board.
**This physical dry fit has not been performed.**

The small inverted-joint gap can retain water. This tradeoff is accepted for this
desert installation; keep the existing drainage paths open.

## Concealed fastening and downward installation

1. Install the framing, fixture backing, added wall backing and plywood roof strips.
   Existing rails and posts fill interruptions between new backing segments.
   Attach wall backing segments positively to framing with suitable stainless
   angles and structural screws. Roof strips bear on the existing perimeter
   framing and diagonal; keep the space below the diagonal clear.
2. Install the hardware-cloth skirt independently of the boards. Keep paths
   behind and between framing members unobstructed for drainage and the guide's
   minimum 1-inch continuous net free ventilation area. The open frame must
   provide this airflow; there is no clip-created space behind the boards.
3. Install the US135 roof cover while the sides remain open for access to the
   support strips and fasteners. Leave US20 roof-edge trim until after the wall
   siding is installed.
4. Hold each inverted top board level with padded temporary supports fixed to
   framing. Seat it against the lumber and install #8 x 1-1/4-inch stainless
   composite screws through the recessed lower overlap at supported stations.
   Verify usable material, penetration and head clearance on production boards.
5. Engage the next inverted course below, concealing the preceding fastening
   row, and continue downward. Intact courses use one lower-overlap row, with
   their upper edges engaged in the preceding course. At cutouts, the rear header
   and scribed terminations, use supported local face screws where the overlap
   is unavailable. US20 is the preferred concealment at corners and opening
   edges; exposed screws remain only where neither overlap nor trim covers them.
   The generated manifest classifies full-head coverage using actual modeled
   trim extents, including the front fixture relief. Retention remains untested;
   do not assume an unsupported lip can carry a fastener.
6. Use **one fixed point per physical board**. All remaining face connections
   need oversized holes and heads free to slide. Page 5 of the supplied guide
   gives thread/hole/head size relationships. Do not clamp or countersink the
   sliding connections tightly into the composite. The preview shows schematic screw
   head envelopes; it does not machine the holes. Gold heads mark the fixed points.
7. The notched rear top board fixes at the backed header near its midpoint;
   all wing connections slide. Each separate lower wing has its own fixed
   point. Do not treat display fragments as separate physical boards.
8. Scribe the final course to surveyed grade plus 3/4 inch and check intervening
   high spots. Retain supported local fastening and movement clearance without
   lowering the courses above. Remove props after permanent fasteners retain
   each board.

Wall support spacing remains at most 16 inches. Extra backing beside the outlet
extends only over the full heights of the courses intersected by the cutout;
the extra screw stations apply only to those courses. Regular wall backing and
screw stations continue independently above and below it. Existing framing fills
interruptions in the local backing. Removing the clips does not remove the backing requirement.
The hardware cloth has 1/4-inch openings, a 2-inch cut height and 2-inch joint
overlaps. The nominal 3/4-inch grade gap remains under siding and trim. The rear
access opening remains open.

## US20 corners, opening and roof edges

[US20](https://www.newtechwood.com/pdf/Wall-Cladding-US20US20_P12_Line_Dwg_20221219.pdf)
is a nominal 40 x 40 mm L-angle. Apply it after the boards, covering square-cut
ends. It is narrower than US46, so verify actual overlap, clearance and backing
before drilling. It covers edges; it does not support the boards.

At all four outside corners, vertical US20 stops beneath the roof-edge US20
faces with 1/8-inch modeled clearance. Each vertical trim retains 3/4-inch
clearance above its own local grade. Rear-opening jamb returns face inward;
the jamb tops stop below the header return with movement clearance. Check the
full return against actual opening backing and service access.

Roof-edge US20 has horizontal legs over the roof and vertical legs over the
wall tops. Its horizontal legs meet at 45-degree plan miters with movement
gaps. The staggered vertical-corner/roof junction avoids a three-way compound
miter and uses no unsupported corner cap.

The front roof-edge face needs relief around the Brook mounting body:
6 1/4 inches wide, to 1/8 inch above its modeled top. Check the actual fixture
before cutting. Fasten on either side of the relief into the front brace.
Use #8 x 2-inch stainless wall trim screws into lumber. Horizontal roof trim
uses 2-1/2-inch screws through the thicker roof stack; check actual penetration. The trim-screw BOM is an allowance, not a drilled layout.

Fix each trim piece once and allow its other connections to slide. Screws
passing through siding must allow independent movement of that board too.
Do not clamp a long angle tightly against several courses. Leave movement
and drainage gaps open; seal fixture penetrations independently.

The 1/8-inch modeled end/trim allowance is for pieces up to 8 feet installed
at 32 F or warmer. Check page 11 of the supplied guide against actual conditions.
The model rejects layouts beyond that length envelope. Stock minimums include
1/8-inch kerf per cut and offcut reuse, with no damage/contingency allowance.
Default purchase stock is 8 feet for both US135 and US20.

## Roof cover and review files

Roof boards run along X and courses progress along Y. Each full-width board
rests on two continuous **3/4-inch PT exterior structural plywood strips**,
provisionally 1.5 inches wide. Rip with the panel strength axis along X. Place
strips within the full-thickness underside, clear of mating rebates. The narrow
final course uses one backer instead of overlapping strips. Verify these bearing
zones against the production profile before ripping plywood.

The strips replace the intermediate roof backing, perimeter shims and diagonal
shim. Their bottoms bear on the common framing/diagonal top plane, z = 49.625.
Open channels between strips leave the middle of each full board exposed below;
keep joint outlets and perimeter drainage open. Do not sever strips transversely
for drainage. This arrangement does not establish manufacturer acceptance of the
ventilation or exposed-roof adaptation. Treat cut plywood edges as required by
the selected preservative system; verify exterior bond, grade and actual thickness.

Shorten strip ends around the gusset envelopes with 1/8-inch clearance. The
strips bear on the existing perimeter framing and diagonal, without local
support blocks below the diagonal. This preserves the 1-inch modeled clearance
between the diagonal underside and the prototype tambour hardware envelope.
The strip anchors retain their existing supported locations. Remaining strip
bearing and roof load capacity are unverified.

Anchor each plywood strip independently near its two ends at the generated
framing/diagonal-supported locations. Recess anchor heads flush in plywood so
they do not clamp the siding. Field-select anchor screw length and penetration.

Roof face screws are separately counted: provisional **#8 x 1-1/8-inch stainless
retaining-head screws**, nominally 5/8-inch penetration through 1/2-inch siding
into 3/4-inch plywood. This is a geometric candidate, not a verified fastener
product or connection capacity. Check the actual stack, contained tip, usable
thread engagement, head retention and sliding-hole behavior. A #8 x 1-1/4-inch
screw through the nominal 1/2-inch siding and 3/4-inch plywood reaches only
the framing surface; it provides no penetration into the diagonal. Attach along strip
centerlines at no more than 10-inch spacing, with exactly one midpoint fixed
connection per physical board and sliding connections elsewhere.

Use 2-1/2-inch roof trim screws through horizontal US20/board/plywood into
framing, preserving the former nominal framing penetration. Wall trim retains
2-inch screws. Verify actual landing and penetration; trim carries no roof load.
This level cover permits leakage; snow, uplift, ponding and exposed-roof capacity
remain unverified. The [ceiling guide](https://www.newtechwood.com/pdf/All_Weather_Siding_Ceiling_Installation_Guide.pdf)
informs movement guidance without establishing this support arrangement's capacity.

Plywood purchasing uses a conservative 4 x 8 ft sheet allowance: one longitudinal
rip lane per strip including kerf, without optimized offcut reuse. Sheet quantities
are separate from linear lumber stock. The installation JSON records strip
coordinates, independent anchors, short siding screws and toe-screw entry axes.

Generated files include:

- `output/model.scad`: enclosure, schematic recessed/face screw heads and downward build steps.
- `output/roof_support_review.scad`: cropped roof framing, gussets and strips; render with `openscad -D build_step=22`.
- `output/siding_corner_*.scad`: four cropped roof/wall corner views.
- `output/siding_cut_list.csv` and `.json`: physical board, backing and trim cuts.
- `output/siding_installation.json`: supported attachment locations, fixed
  points, concealment classifications, exception reasons, course order and prototype assumptions.
- `output/siding_bom.csv`: siding purchase quantities and installation notes;
  the repository-root `siding_bom.csv` is the current default-build snapshot.
- Shared BOM, cut and shopping lists include the revised materials/hardware.
