# Custom Tambour Door Prototype and Build Guide

This guide defines how to develop, prove, fabricate, install, and maintain the
custom tambour door shown in the enclosure model. It supplements
[`BUILD_STEPS.md`](BUILD_STEPS.md); it is not a claim that the current modeled
slat and track dimensions are a proven shop drawing.

The door is intended to be an attractive visual barrier that is easy to open,
close, clean, and service. It is not a security barrier or a weather seal. Do
not add locks, gaskets, springs, or counterweights without revisiting the path,
clearances, operating force, and maintenance requirements.

## Modeled starting geometry

Use these values to lay out the first full-size prototype. Values marked
"prototype-controlled" may change before production and must be recorded in
the build record at the end of this guide.

| Feature | Modeled value | Status |
| --- | ---: | --- |
| Distance between left and right track centerlines | 20 1/2 in | Verify against the built frame |
| Rear lower track endpoint | `y = 21`, `z = 3` in | Fixed enclosure interface |
| Front lower track endpoint | `y = 5 1/2`, `z = 16` in | Fixed enclosure interface |
| Top track centerline | `z = 44 1/2` in | Fixed enclosure interface |
| Track offset into slat | 0 in; path is groove center | Fixed enclosure interface |
| Bend centerline radius | 2 5/8 in | Prototype-controlled |
| Curtain length | 44 in | Prototype-controlled |
| Slat pitch | 25/32 in | Prototype-controlled |
| Slat travel-direction height | 3/4 in | Prototype-controlled |
| Wooden slat face depth | 1/2 in | Prototype-controlled |
| Complete swept depth envelope | 1 1/2 in | Fixed clearance limit |
| Rendered track diameter | 1/2 in | Visualization only |
| Removable ceiling panel | 20 1/2 by 8 3/4 by 1/4 in | Fixed enclosure interface |

The model places 56 slats on the 44-inch curtain. The 1/32-inch difference
between the 3/4-inch slat height and 25/32-inch attachment pitch is a setup
allowance, not a promise of a permanently visible gap. The lower stop supports
the closed curtain, adjacent slats may settle together, and the webbing can bow
locally. The detailed model draws the channel and its mounting flange; printable
track solids and test coupons are generated separately with build123d.

The track datum and wooden slat center now share the running-groove centerline.
In the X direction, that datum is also the lumber mounting face: the printed
flange and channel project from it into the door opening rather than into the
supporting lumber.
The actual 1/2-inch slat is rendered at `z = 44.5` on the top run, while
clearance checks retain the complete 1 1/2-inch swept envelope. The envelope
retains 1/4 inch below the braces: `44.5 + 1.5 / 2 = 45.25` inches. No handle,
screw head, webbing,
reinforcement, or track fixing may extend beyond it.

## Provisional construction

Use the following construction family for the prototypes:

- Dry, straight pressure-treated stock surfaced to 1/2 inch for the slats.
  Reject twisted, cupped, checked, severely incised, or irregular stock. Use a
  planer, purchased surfaced stock, or outsourced milling rather than resawing
  a wide board on edge with only a table saw. Field-treat and seal cut faces.
- At least three exterior-rated polyester webbing strips on the concealed face,
  mechanically fastened to every slat without pre-tension. Keep fasteners clear
  of the captured ends and handle screws.
- ASA track segments with integral mounting flanges as the replaceable running
  surface. Print the clearance coupons before production parts; a separate
  UHMW liner is not part of the initial design.
- Corrosion-resistant fasteners outside the running surface. Fix each track
  segment at its center and use slotted outer holes so it can expand without
  buckling.
- Replaceable end stops and paired removable loading sections at the lower rear
  ends of the tracks. The curtain must remain removable after siding, trim, and
  electrical equipment are installed.

Make both guide paths from the same full-size master template. Mark every
track segment, keyed collar, spacer, loading section, and end stop
left/right and front/rear so that matched pieces return to their proven
positions. Keep the running surfaces
smooth and free of exposed screw heads, abrupt joints, plastic strings,
and pockets that retain grit or water. Provide cleanout and drainage at both
low endpoints.

Commercial tambour instructions emphasize consistent, aligned tracks and
keeping debris out of the slats. Printed ASA also requires expansion gaps and
independently aligned segments rather than a long rigid run. See the
[Tambour Doors installation guidance](https://tambourdoors.eu/installation-guides/),
[Tambortech installation instructions](https://www.tambortech.com.au/fileadmin/user_upload/downloads/2013_Tambour_Door_Install_Sheet.pdf),
and the printable-part instructions below.

## Printable ASA parts

Run `uv run python tools/generate_tambour_parts.py` to write the complete STEP,
STL, and quantity manifests beneath `output/tambour/`. Use `--part NAME` while
developing a coupon or replacement. Do not scale meshes in the slicer; change
the Python configuration and regenerate them so track and collar clearances stay
coordinated.

The baseline assumes a 0.6 mm nozzle, 0.3 mm or finer layers, at least four
perimeters, and an enclosed ASA-capable printer. Put each track's mounting
flange on the build plate; both handed exports are already oriented this way.
Use enough top and bottom layers and infill to make screw counterbores and the
handle ribs solid in practice. Follow the filament manufacturer's temperature,
drying, ventilation, and fume-control instructions. Do not anneal production
parts unless identically treated coupons demonstrate that dimensional change
does not consume the accepted running clearance.

The fixed straight runs are divided into equal segments below 300 mm. The rear
loading section replaces the lowest 100 mm of fixed track; it is not added to
the path length. Keep the configured 0.6 mm expansion seam between track ends.
At every joint, slide one external dovetail-collar shoe down each channel wall,
then retain each shoe with a recessed M3 stainless screw in its heat-set insert.
The shoes index both channel walls while leaving the running channel empty and
allowing limited longitudinal thermal movement. Remove both screws and lift the
shoes outward before lifting an individual segment. The collars align the
tracks but do not replace the segment mounting screws. Print the two joint-test
tracks first and inspect `joint_fit_preview.step` for the installed orientation.
Keep the open drain notch in each lower stop unobstructed.

## Pull slats

Make two special pull slats as part of the curtain:

1. The lowest slat is the normal opening pull. When the door is open, this slat
   travels onto the upper run and also serves as the closing pull.
2. Place a second pull approximately 18 inches above the lower curtain edge.
   At the modeled 25/32-inch pitch this is nominally the twenty-fourth slat when
   the lowest slat is counted as the first. Set its final position from the
   actual production pitch, not merely the nominal slat count.

Rear elevation, door closed (not to scale):

```text
                  top track centerline z = 44.5
       left track  |==========================|  right track
                   |                          |
                   |  upper printed lift ledge|  about 18 in above lower edge
                   |  <-------------------->  |
                   |                          |
                   |  lowest printed lift ledge| normal opening pull
                   |  <-------------------->  |
                   +--------------------------+  lower edge about z = 3
```

Side path and handle orientation (not to scale):

```text
 rear opening                                      enclosure front
 y = 21                                                   y = 5.5
    |        top brace underside z = 45.5                    |
    |        ----------------------------------               |
    |        1/4-in minimum clearance                         |
    |      / printed ledge rotates onto top run \              |
    |     /======================================\ z = 44.5   |
    |     |                                      |            |
    |     |                                      |            |
 z = 3 --+                                      +-- z = 16

 Any proud handle reduces the required 1/4-in clearance.
 The printed ledge must remain inside the approved 1 1/2-in envelope.
```

The model includes a removable 1/4-inch exterior-plywood ceiling from
`y = 8.875` to `y = 17.625` and `z = 43.25` to `z = 43.5`. It shields the
overhead curtain from hands and the charger cord while retaining 1/4 inch
below the maximum curtain envelope. Support it on independent removable
retainers; do not fasten through a printed track or obstruct track inspection.

Attach one centered printed ASA lift ledge to each pull slat. The nominal ledge
is 300 mm wide, no more than 5/8 inch proud of the wood face, and secured with
multiple short corrosion-resistant wood screws in recessed counterbores. It
must remain entirely on one slat and permit a centered one-hand grip or a wide
two-hand grip.

The approved pull profile must meet all of these conditions:

- Nothing projects beyond the ordinary slat envelope in any direction.
- The printed grip and its edges are smooth, rounded, drainable, and free of
  layer separation or sharp support scars.
- Screw pilot holes retain enough wood to keep the 1/2-inch pull slat straight
  under the proof load without penetrating the concealed face.
- The webbing connection at each pull slat is reinforced within the approved
  curtain envelope. Force on the upper pull must not depend only on one screw
  or one webbing strip.
- The grip cannot trap a finger against the next slat or either track while the
  curtain enters a bend.

A bail, folding handle, knob, proud screw, or webbing loop is not acceptable:
every slat-mounted feature travels through both bends and under the top
bracing. Prototype the printed ledge and complete fastener stack before making
the full curtain.

## Prototype sequence

Do not fabricate the final curtain and tracks in one pass.

### 1. Material and pull coupons

Mill several short 1/2- and 3/8-inch-deep slats at the modeled 3/4-inch height.
Ease the moving edges, fasten actual webbing, and mount one printed handle.
Apply the proposed field treatment and finish. Check articulation, screw
holding, drainage, grip comfort, and whether the pull remains straight under
the 15-pound proof load described below. Keep 1/2 inch as the production depth
unless the thinner coupon passes every wind and durability test.

### 2. Full-size path template

Lay out the complete side path at full scale, including both 2 5/8-inch-radius
bends and both lower endpoints. Use a fair curve with tangent transitions; do
not approximate the bend with a sharp miter. Make a rigid master template and
use it for both mirrored track assemblies.

### 3. Short-curtain track test

Print the 0.3, 0.5, and 0.7 mm-per-face clearance coupons, then one complete
bend and its tangent stubs. Run a short webbing-linked group of ordinary and
pull slats through it. Select the tightest conditioned coupon that runs freely,
then adjust only slat edge easing and setup gap until the sample moves without
pinching, chatter, or visible skew. Generate both track hands with that
accepted clearance.

### 4. Full-width test frame

Build a rigid test frame at the measured production track spacing. Use fixed
spacers or an alignment gauge at the rear vertical, both bends, top run, and
front vertical. Install the removable loading sections and end stops exactly
as they will be installed in the enclosure.

### 5. Full-curtain test

Fabricate the 44-inch curtain using the two pull slats. Load it through the
service sections, fit the stops, and perform the acceptance tests below. Test
the bottom pull from the center and with hands spread toward both tracks. Test
the upper pull the same way.

If the completed door exceeds the operating-force limit, first reduce the slat
mass and repeat the short-curtain and full-curtain tests. Adjust the model after
the production profile is approved. Do not mask an excessively heavy curtain
with extra track friction, and do not add a spring or counterweight as part of
this design.

## Enclosure installation

Install the approved tracks after the four tambour-supporting lumber members
are fixed and before electrical backing, conduit, siding, or trim restricts
access.

1. Measure the actual frame and compare it with the prototype test frame.
2. Use the prototype alignment gauges to position both guide paths. Shim the
   mounting flanges as needed; do not pull a crooked segment straight with
   screws.
3. Fix each ASA segment at its center, use its slotted outer holes, preserve
   the accepted joint gaps, and keep every fixing outside the running surface.
4. Load the completed curtain and cycle it fully. Confirm the printed pulls
   clear both bends and all installed framing, including at least 1/4 inch of
   clearance below the already installed top braces throughout their travel.
5. Mark all matched parts, then remove the curtain, loading sections, and end
   stops. Cover the fixed tracks against dust, cuttings, paint, and finish
   during the remaining work.
6. After siding and trim, uncover and clean the tracks. Confirm that no
   fastener or trim movement changed their spacing.
7. Reinstall the curtain, loading sections, and stops, then repeat the full
   acceptance test, including clearance from the already completed conduit
   and fixed cable routes. Install the removable ceiling and repeat the test.

The rendered charger cord is illustrative rather than an accurate operating
envelope. Do not use its modeled path as a hard tambour-clearance datum; the
ceiling panel provides the physical guard beneath the overhead curtain.

The OpenSCAD build-step view shows the completed tambour assembly beginning at
its trial-fit step. It does not attempt to depict the curtain's temporary
removal during the intervening construction work.

## Snow operation

The modeled lower curtain edge is only about 3 inches above nominal grade, so
drifting, shoveled, or plowed snow can cover the lowest pull even though the
door is not intended as a weather barrier. The upper pull provides a reachable
grip; it is not a pry point for breaking a frozen door loose.

After snowfall:

1. Clear snow away from the face of the curtain, both track edges, and the rear
   lower track endpoints.
2. Free any ice bond without levering against a slat or printed track.
3. Use a wide or two-handed grip on the upper printed pull and apply smooth,
   even force until the bottom pull is exposed.
4. Transfer to the bottom pull for normal operation.
5. Stop if the door racks, binds, or requires more than its normal operating
   effort. Clear the obstruction rather than forcing the curtain.

## Acceptance tests

Approve the production design only after it passes all of the following on the
full-width test frame and again in the enclosure:

- Complete at least 100 full open-close cycles without binding, derailment,
  webbing separation, handle damage, or visible track wear.
- Measure no more than 5 pounds peak normal operating force anywhere in the
  travel, using the center and the left and right thirds of both pulls.
- Apply a 15-pound static load to each printed pull for one minute without
  cracking, permanent deformation, screw withdrawal, or webbing separation.
- Apply approximately 4.7 pounds uniformly to a conditioned full-span slat and
  screen the complete closed door and supports for the project's approximately
  260-pound distributed ultimate wind load.
- Confirm that center operation does not rack the curtain and that a deliberate
  modest left/right imbalance does not cause derailment.
- Confirm that the curtain cannot run away, leave either endpoint, or create an
  accessible pinch point during ordinary operation.
- Sweep the complete handle and reinforcement envelope through both bends and
  the top run without contact.
- Remove and reinstall the curtain without removing siding, trim, electrical
  equipment, or a permanent track section.
- Repeat the functional and clearance checks after track installation, after
  siding and trim, and after the final cable routes are installed.

## Production build record

Complete this record before final fabrication and use the approved values to
update the model and generated material outputs in a later change.

| Item | Approved value or product |
| --- | --- |
| Actual installed track spacing | |
| Bend radius | |
| Slat species and moisture condition | |
| Slat pitch, travel width, depth, and end clearance | |
| Ordinary edge profile | |
| Printed pull revision, projection, and screw pattern | |
| Upper pull position from lower curtain edge | |
| Webbing product, strip count, and screw pattern | |
| Field treatment and surface preparation | |
| Finish and maintenance interval | |
| ASA product, clearance coupon, and expansion allowance | |
| Fasteners and slot dimensions | |
| Loading-section and end-stop details | |
| Measured peak operating force | |
| Prototype cycle count and date | |

Until this record is complete, the tambour materials are provisional and are
not included in the generated BOM or shopping list. After approval, follow up
by splitting guide tracks, ordinary slats, and pull slats into distinct modeled
objects and adding their approved materials to the generated BOM and shopping
list.
