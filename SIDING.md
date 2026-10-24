# US135 enclosure siding and roof cover

The enclosure uses horizontal NewTechWood US135, installed **from the top
downward**, with exposed face screws directly into open lumber framing.
US20 L-angle covers all four outside corners, the rear access opening and the
roof perimeter. There are no AW08 clips, T-7 spacers, US46 or US44 profiles.
Generate the model and fabrication files with `uv run build.py --no-deploy`.
Dimensions are inches.

This is a **custom face-fastened adaptation**, not the manufacturer's illustrated
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
Existing perimeter shims and the added diagonal shim put roof support at
z = 49.875; the roof board top is z = 50.375. Schematic US20 thickness adds
0.22 inch above that.

The defaults give ten wall courses. Solid-wall top boards retain their full
profile height. The rear top board is one physical board with an access notch;
each lower rear wing is a separate physical offcut. Rendered opening fragments
do not multiply the stock-board count or fixed-point count.

Before cutting production pieces, dry-fit two courses on representative lumber.
Check rear-profile seating, engagement in the intended orientation, installed
pitch, access for face screws, head retention and movement-hole behavior.
**This physical dry fit has not been performed.**

## Face fastening and downward installation

1. Install the framing, fixture backing, added wall and roof backing, and shims.
   Existing rails and posts fill interruptions between new backing segments.
   Attach each segment positively to framing with suitable stainless angles
   and structural screws. Field-fit small blocks and keep gusset/head gaps.
2. Install the hardware-cloth skirt independently of the boards. Keep paths
   behind and between framing members unobstructed for drainage and the guide's
   minimum 1-inch continuous net free ventilation area. The open frame must
   provide this airflow; there is no clip-created space behind the boards.
3. Hold each top board level with padded temporary supports fixed to framing.
   Seat it against the lumber and install exposed #8 x 1-1/4-inch stainless
   composite face screws at the generated supported locations. Check actual
   penetration and head selection against the production profile and lumber.
4. Engage the next course with the course above and continue downward. Each
   course has two screw rows where its remaining width permits, nominally
   3/4 inch from its upper and lower edges. Narrow scribed remainders use a
   centered row. These locations are a custom retention proposal, not tested
   load capacities. Do not screw through unsupported groove lips.
5. Use **one fixed point per physical board**. All remaining face connections
   need oversized holes and heads free to slide. Page 5 of the supplied guide
   gives thread/hole/head size relationships. Do not clamp or countersink the
   sliding connections tightly into the composite. The preview shows screw
   heads; it does not machine the holes. Gold heads mark the fixed points.
6. The notched rear top board fixes at the backed header near its midpoint;
   all wing connections slide. Each separate lower wing has its own fixed
   point. Do not treat display fragments as separate physical boards.
7. Scribe the final course to surveyed grade plus 3/4 inch and check intervening
   high spots. Retain supported face fastening and movement clearance without
   lowering the courses above. Remove props after permanent fasteners retain
   each board.

Wall support spacing remains at most 16 inches. Backing near the outlet retains
the notched courses. Removing the clips does not remove the backing requirement.
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
Use #8 x 2-inch stainless trim screws through US20/board into lumber, checking
actual penetration. The trim-screw BOM is an allowance, not a drilled layout.

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

Roof boards run along X and courses progress along Y. Boards bear directly on
the existing perimeter shims, added actual 1-inch backing strips, and the
1/4-inch diagonal shim. Added strips stop at the diagonal. Support spans remain
no greater than 12 inches along the boards. Face screws retain both edges where
width permits, with one fixed point per physical roof board. The trim carries
no roof weight. This level cover permits leakage; snow, uplift, ponding and
exposed-roof capacity remain unverified. The [ceiling guide](https://www.newtechwood.com/pdf/All_Weather_Siding_Ceiling_Installation_Guide.pdf)
informs support spacing without establishing exposed-roof suitability.

Generated files include:

- `output/model.scad`: enclosure, exposed screw heads and downward build steps.
- `output/siding_corner_*.scad`: four cropped roof/wall corner views.
- `output/siding_cut_list.csv` and `.json`: physical board, backing and trim cuts.
- `output/siding_installation.json`: supported attachment locations, fixed
  points, course order and prototype assumptions.
- `output/siding_bom.csv`: siding purchase quantities and installation notes;
  the repository-root `siding_bom.csv` is the current default-build snapshot.
- Shared BOM, cut and shopping lists include the revised materials/hardware.
