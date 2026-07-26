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
| Distance between left and right track centerlines | 26 1/2 in | Verify against the built frame |
| Rear lower track endpoint | `y = 29`, `z = 3` in | Fixed enclosure interface |
| Front lower track endpoint | `y = 5 1/2`, `z = 16` in | Fixed enclosure interface |
| Top track centerline | `z = 44 1/2` in | Fixed enclosure interface |
| Bend centerline radius | 3 in | Prototype-controlled |
| Curtain length | 44 in | Prototype-controlled |
| Slat pitch | 1 in | Prototype-controlled |
| Slat travel-direction width | 0.9 in | Prototype-controlled |
| Slat face depth | 3/4 in modeled; 1 1/2 in maximum envelope | Prototype-controlled |
| Rendered track diameter | 1/2 in | Visualization only |

The model places 44 slats on the 44-inch curtain. It models the two tracks as
round centerlines; it does not define a groove, liner cross-section, running
clearance, fastener pattern, or loading opening. Derive those details from the
prototype rather than treating the rendered cylinders as stock material.

The top track centerline is 1 inch below the perimeter braces. This permits an
approved curtain and pull-slat envelope up to 1 1/2 inches deep while retaining
1/4 inch of clearance below the braces: `44.5 + 1.5 / 2 = 45.25` inches. No
handle, fastener, backing reinforcement, or track fixing may project beyond
that approved envelope in this region. A thinner production profile increases
the clearance but does not permit the track centerline to be raised.

## Provisional construction

Use the following construction family for the prototypes:

- Straight, dimensionally stable exterior hardwood for the slats. Reject
  twisted, cupped, checked, or irregular stock.
- An exterior-rated flexible backing and compatible flexible adhesive on the
  concealed face. Confirm adhesion to both the wood and its chosen finish with
  coupons before committing the full curtain.
- UV-stable UHMW-PE for the low-friction guide liners, mechanically attached to
  the lumber supports. Do not rely on adhesive alone to retain UHMW.
- Corrosion-resistant mechanical fasteners located outside the running
  surface. Use slotted holes, suitable washers, and end gaps so the polymer can
  expand without buckling.
- Replaceable end stops and paired removable loading sections at the lower rear
  ends of the tracks. The curtain must remain removable after siding, trim, and
  electrical equipment are installed.

Make both guide paths from the same full-size master template. Mark every
liner, spacer, loading section, and end stop left/right and front/rear so that
matched pieces return to their proven positions. Keep the running surfaces
smooth and free of exposed screw heads, abrupt joints, adhesive squeeze-out,
and pockets that retain grit or water. Provide cleanout and drainage at both
low endpoints.

Commercial tambour instructions emphasize consistent, aligned tracks and
keeping debris out of the slats. UHMW installation guidance also requires room
for substantially greater thermal movement than the supporting wood. See the
[Tambour Doors installation guidance](https://tambourdoors.eu/installation-guides/),
[Tambortech installation instructions](https://www.tambortech.com.au/fileadmin/user_upload/downloads/2013_Tambour_Door_Install_Sheet.pdf),
and [UHMW expansion guidance](https://www.dotmar.com.au/insights/educational/plastics-designing-for-thermal-expansion).

## Pull slats

Make two special pull slats as part of the curtain:

1. The lowest slat is the normal opening pull. When the door is open, this slat
   travels onto the upper run and also serves as the closing pull.
2. Place a second pull approximately 18 inches above the lower curtain edge.
   At the modeled 1-inch pitch this is nominally the nineteenth slat when the
   lowest slat is counted as the first. Set its final position from the actual
   production pitch, not merely the nominal slat count.

Rear elevation, door closed (not to scale):

```text
                    top track centerline z = 45
       left track  |==========================|  right track
                   |                          |
                   |  upper recessed pull     |  about 18 in above lower edge
                   |  <-------------------->  |
                   |                          |
                   |  lowest recessed pull    |  normal opening pull
                   |  <-------------------->  |
                   +--------------------------+  lower edge about z = 3
```

Side path and handle orientation (not to scale):

```text
 rear opening                                      enclosure front
 y = 29                                                   y = 5.5
    |        top brace underside z = 45.5                    |
    |        ----------------------------------               |
    |        1/4-in minimum clearance                         |
    |      / recessed pull rotates onto top run \             |
    |     /======================================\ z = 44.5   |
    |     |                                      |            |
    |     |                                      |            |
 z = 3 --+                                      +-- z = 16

 Any proud handle reduces the required 1/4-in clearance.
 The recessed pull must remain inside the approved 1 1/2-in envelope.
```

Machine a continuous recessed finger channel across most of the usable span of
each pull slat. Stop the channel before the end regions engaged by the tracks.
The channel should permit a centered one-hand grip or a wide two-hand grip; it
must not require separate handles near the tracks.

The approved pull profile must meet all of these conditions:

- Nothing projects beyond the ordinary slat envelope in any direction.
- The groove and its edges are smooth, radiused, drainable, and sealed on every
  machined surface.
- Enough wood remains behind the deepest part of the groove to keep the pull
  slat straight under the proof load.
- The backing connection at each pull slat is reinforced within the approved
  curtain envelope. Force on the upper pull must not depend only on a narrow
  adhesive line at that slat.
- The grip cannot trap a finger against the next slat or either track while the
  curtain enters a bend.

A surface-mounted bail, folding handle, knob, proud screw, or webbing loop is
not acceptable: every slat-mounted feature travels through both bends and
under the top bracing. Prototype the recessed profile before making the full
curtain.

## Prototype sequence

Do not fabricate the final curtain and tracks in one pass.

### 1. Material and pull coupons

Mill several short slats at the modeled profile. Round the moving edges and
make at least one candidate recessed pull. Apply the proposed finish and bond
backing across the samples using the proposed surface preparation and
adhesive. After cure, check flexibility, adhesion, drainage, grip comfort, and
whether the pull remains straight under the 15-pound proof load described
below.

### 2. Full-size path template

Lay out the complete side path at full scale, including both 3-inch-radius
bends and both lower endpoints. Use a fair curve with tangent transitions; do
not approximate the bend with a sharp miter. Make a rigid master template and
use it for both mirrored track assemblies.

### 3. Short-curtain track test

Machine one prototype liner and run a short backed group of ordinary and pull
slats through both bends. Adjust slat edge radii, groove clearance, liner
profile, bend radius, and backing thickness until the sample moves without
pinching, chatter, or visible skew. Reproduce the accepted profile in a second
mirrored liner.

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
   track backing as needed; do not pull a crooked liner straight with screws.
3. Allow the specified UHMW expansion clearance and keep every fixing outside
   the running surface.
4. Load the completed curtain and cycle it fully. Confirm the recessed pulls
   clear both bends and all installed framing, including at least 1/4 inch of
   clearance below the already installed top braces throughout their travel.
5. Mark all matched parts, then remove the curtain, loading sections, and end
   stops. Cover the fixed liners against dust, cuttings, paint, finish, and
   adhesive during the remaining work.
6. After siding and trim, uncover and clean the tracks. Confirm that no
   fastener or trim movement changed their spacing.
7. Reinstall the curtain, loading sections, and stops, then repeat the full
   acceptance test, including clearance from the already completed conduit,
   cable routes, and charger cord.

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
2. Free any ice bond without levering against a slat or guide liner.
3. Use a wide or two-handed grip on the upper recessed pull and apply smooth,
   even force until the bottom pull is exposed.
4. Transfer to the bottom pull for normal operation.
5. Stop if the door racks, binds, or requires more than its normal operating
   effort. Clear the obstruction rather than forcing the curtain.

## Acceptance tests

Approve the production design only after it passes all of the following on the
full-width test frame and again in the enclosure:

- Complete at least 100 full open-close cycles without binding, derailment,
  backing separation, handle damage, or visible track wear.
- Measure no more than 5 pounds peak normal operating force anywhere in the
  travel, using the center and the left and right thirds of both pulls.
- Apply a 15-pound static load to each recessed pull for one minute without
  cracking, permanent deformation, or backing separation.
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
| Recessed pull profile and remaining wall thickness | |
| Upper pull position from lower curtain edge | |
| Backing and reinforcement | |
| Adhesive and surface preparation | |
| Finish and maintenance interval | |
| UHMW grade, liner profile, and expansion allowance | |
| Fasteners and slot dimensions | |
| Loading-section and end-stop details | |
| Measured peak operating force | |
| Prototype cycle count and date | |

Until this record is complete, the tambour materials are provisional and are
not included in the generated BOM or shopping list. After approval, follow up
by splitting guide tracks, ordinary slats, and pull slats into distinct modeled
objects and adding their approved materials to the generated BOM and shopping
list.
