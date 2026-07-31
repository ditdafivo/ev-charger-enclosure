# EV Charger Enclosure Build Steps

This guide describes the modeled construction sequence for the fixed enclosure
design: 24-inch left-to-right post center spacing, 18 3/8-inch front-to-back post
center spacing, 47 inches above grade, and 32 inches of each post below grade.
Dimensions and cut lengths below apply to this design only.

The generated BOM and cut list remain the authoritative material references
for generated modeled materials. The custom tambour curtain, printed tracks,
webbing, pulls, and associated hardware remain prototype-controlled and are documented
separately in [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md); they are not yet included in
the generated material outputs.

The top-plane bracing decision, site load screen, and required connection
capacity are documented in [`TOP_BRACING.md`](TOP_BRACING.md).

Except for the modeled custom top-bracing detail, this guide does not define
fastener length, structural connection capacity, concrete work, or the means and
methods for excavation or underground work. It does require
the modeled underground conduit and site restoration to be completed before
the enclosure posts are installed. Have the structure, electrical design,
conductor ampacity, grounding and bonding, box fill, permits, and installation
verified for the site and applicable code. Electrical work should be performed
by a qualified installer.

## Naming and visualization contract

- `fl`, `fr`, `bl`, and `br` mean front-left, front-right, back-left, and
  back-right.
- The `New model objects` block in every step contains exact identifiers from
  the Python model. These blocks are intended to be machine-readable.
- Every modeled object is introduced in exactly one step. The ground plane is
  permanent context and is not assigned to a step.
- Temporary operations such as removing and protecting the tambour curtain
  after its trial fit are not separate model objects. From its introduction in
  Step 11, the visualization shows the completed tambour in its nominal open
  position.
- The OpenSCAD `build_step` parameter behaves as follows:
  - `build_step = 0`: show only permanent context, including the ground plane.
  - `build_step = 1..25`: show earlier objects normally, highlight objects from
    the selected step, and hide objects from later steps.
  - `build_step = 26`: show the completed model in its normal colors.
- An invalid positive step number should fail clearly during generation rather
  than silently display an incomplete or misleading model.

## 1. Complete the underground conduit risers and restore grade (`underground-risers`)

Before installing any posts, establish the enclosure layout from protected
reference points and mark all four 10-inch footing circles. Route both
underground conduit runs through the enclosure interior and clear of the full
footing excavations before sweeping them up to the risers. Bring the modeled
1 1/4-inch power riser out of the ground on the EV charger's conduit-port axis
(x = 16 inches and y = 11.3375 inches in the default model) and bring the
modeled 3/4-inch low-voltage riser out beneath the rear of its junction box.
Its default axis is approximately x = 13.17 inches and y = 5.44 inches, clear
of the post footings. Leave both upper ends positioned for the later equipment
connections.

Before covering the conduit, measure and photograph its centerline, depth, and
the complete envelope of every sweep from protected reference points. Establish
two parallel witness lines that bound a no-auger corridor along each run. Drive
the witness stakes outside the trench and excavation area at intervals of a few
feet, connect them with taut string or marking paint, and record enough offsets
to reconstruct the lines if they are disturbed. Do not place closely spaced
stakes beside the conduit or where they would interfere with compaction. Mark
the sweep envelopes separately; a surface riser axis alone does not locate the
underground bend. Install detectable warning tape and, where appropriate for a
nonmetallic raceway, an approved tracer wire above the conduit.

Complete the required underground inspection before covering the work. Place
clean selected material around and above the conduit so angular or oversized
backfill cannot bear directly against it. Backfill the remainder of the trench
at suitable moisture and mechanically compact it in thin lifts, keeping the
fill balanced around the conduit and the risers plumb. Restore a level local
grade, preserve or reconstruct the witness lines from the recorded references,
and correct and recompact any later settlement before excavating the posts. A
period of watering and observation may reveal settlement, but it does not
replace lift compaction.

Reconfirm both stub-up locations, keep them plumb, cap or otherwise protect
their open ends, and guard them against movement or damage during post
excavation and framing. Burial depth, trenching, conductor or cable
installation, separation, marking-system materials, and the underground supply
design remain outside the model and must follow the approved site design.

New model objects:

```text
power_ground_riser
low_voltage_ground_riser
```

## 2. Install the four posts (`posts`)

Excavate and fill four 10-inch-diameter gravel footings from 36 inches below
the nominal ground datum to grade, centered on the post centerlines. Position
the four 79-inch 4x4 posts on the 24-by-18 3/8-inch centerline rectangle. The
model places each post 32 inches below grade and 47 inches above grade, leaving
4 inches of gravel beneath it.

**Before rental day:** Complete the required utility locate and compare each
entire footing circle with the preserved no-auger corridors and recorded
conduit and sweep locations. A marking system establishes location; it does not
make an inadequate clearance safe. Plan to use the auger only where the
complete 10-inch excavation, including a practical allowance for setup error,
bit drift, and soil breakout, remains outside the marked corridor. Plan to
hand- or vacuum-excavate where a sweep is too close, the recorded clearance is
insufficient, or the markings cannot be reliably reconstructed.

Obtain a sheet of structurally rated exterior plywood and prepare four
individual covers with generous bearing beyond the 10-inch holes. Size and
reinforce them to support at least twice the greatest person, equipment, or
material load that could be placed on them. Prepare a way to secure each cover
against wind and accidental displacement without driving an anchor into a
conduit corridor. Mark each cover conspicuously with `HOLE` or `COVER`, and
stage a barricade for the entire footing area. Individual covers are preferred
to one broad panel because one person can handle them, each can be inspected
and secured independently, and they do not have to pass over the conduit
risers.

**Auger day:** Using the 10-inch bit, excavate all four holes during the rental
period. Keep the auger and spoil loads off the restored conduit trench where
practical, and stop if unexpected fill, warning tape, or movement of a riser is
observed. Check every hole for center position, depth, bit drift, soil breakout,
loose material, and wall collapse. Verify that the witness markings and both
risers remain undisturbed. Install and secure each prepared cover as soon as
its inspection is complete, erect the barricade, and return the auger. Do not
leave an open hole unattended or rely on an unsecured sheet, tarp, or loose
boards as a cover.

**Post-installation day or days:** Inspect the covers and holes before resuming
work, particularly after rain, irrigation, freezing, or other changed site
conditions. Remove only the covers needed for active work. Place 4 inches of
compactable angular crushed aggregate beneath each post, then set and
temporarily brace all four posts so their spacing, diagonals, and plumb can be
adjusted together. Place the remaining aggregate evenly around all four sides
of each post in thin lifts, tamping each lift with a narrow tool before adding
the next. Complete every footing to grade and verify that the posts and both
conduit risers have not moved. Do not use rounded pea gravel.

Check the center spacing in both directions, compare the two plan diagonals,
and verify every post is plumb. Establish the front, back, left, and right
orientation now; all later part names depend on it. Maintain the temporary
external bracing until the permanent top bracing is installed and its frame
and connections are approved and stable. Continue to protect the two conduit
stub-ups throughout excavation, setting, and tamping.

New model objects:

```text
post_fl
post_fr
post_bl
post_br
footing_fl
footing_fr
footing_bl
footing_br
```

## 3. Add the complete top bracing (`top-bracing`)

Install 2x4 front and back perimeter braces and top-flush 4x4 left and right
braces. The back-left and front-right posts stop at `z = 46.25`; do not rabbet
them. Route only the four side-brace regions listed in
`output/fabrication.csv` to a uniform 3/4-inch depth. Dry-fit the approximately
35.133-inch-long rectangular blank cut from a stress-rated nominal 1x6; cut it
slightly long rather than rounding the minimum downward. Rip it slightly proud
of the calculated 4.907-inch minimum finished width, fit it on the modeled
post-center line, and jigsaw the end profiles listed in `output/fabrication.csv`.
Its full section must occupy `z = 46.25` to `47.00`, cover both complete post
tops, and stop at their exterior XY faces.

Install one laser-cut 6-by-6-by-0.074-inch G90 galvanized-steel gusset at each
involved corner. Orient each square from the two exterior post faces toward the
frame interior so it covers the post, both adjoining side braces, and the
diagonal. Install #9 pan-head screws in all sixteen modeled holes per plate.
Fastener length is intentionally not specified by this model; select it as part
of the approved structural connection detail. Seat every head without
overdriving and verify that every screw location has solid wood beneath it.

Before fastening the permanent bracing, reconfirm that every post is plumb and
compare the frame diagonals. Install the braces without pulling the posts out
of alignment, then repeat the plumb and square checks. Use the species and
grade specified against the 798-pound ASD brace demand in `TOP_BRACING.md`.
Reject split routed edges, stripped screws, raised plate edges, or rocking
hardware. Remove temporary external bracing only after the permanent frame and
both complete gusset assemblies are inspected and stable.

New model objects:

```text
brace_fl_fr
brace_fl_bl
brace_bl_br
brace_fr_br
brace_bl_fr
gusset_back_left
gusset_front_right
```

## 4. Add the lower side rails (`lower-side-rails`)

Install the left and right 14 7/8-inch 2x4 rails between the front and back
posts. Their modeled bottom elevation is 6 1/4 inches above the nominal ground
datum and their wide faces are horizontal.

Check that the rails are level with one another, that the clear spacing between
posts remains 14 7/8 inches, and that all four posts remain plumb. Adjust the
temporary bracing rather than using these rails to pull the posts into place.

New model objects:

```text
rail_lb
rail_rb
```

## 5. Add the lower front cross rail (`lower-front-rail`)

Install the 20 1/2-inch `rail_fb` between the two lower side rails. Its modeled
front face is offset toward the enclosure interior to support the front center
rail and the power-junction assembly.

Check that it is level, square to the side rails, and correctly oriented before
adding the vertical member in Step 8.

New model objects:

```text
rail_fb
```

## 6. Add the upper side rails (`upper-side-rails`)

Install the right intermediate receiver rail. Keep its modeled wide face horizontal.

Check `rail_rbu` at its
modeled lower-face elevation of 11 1/4 inches; it receives the right-side
vertical rails in Step 8 and Step 9. Reconfirm post plumbness and the frame
diagonals as these rails are fastened.

New model objects:

```text
rail_rbu
```

## 7. Add the upper front cross rail (`upper-front-rail`)

Install the 20 1/2-inch 2x4 `rail_ft` with its lower and upper faces at
z = 41 and 42 1/2 inches. Install the two 1 3/4-inch vertical 2x4 support
blocks between its ends and the undersides of the top side 4x4s.

Check the header for level and square, obtain full bearing from the support
blocks, and verify that the assembly is positioned to receive
`front_center_rail`. Use connections designed for the charger dead load and
the repeated lateral and torsional loads produced while handling its cord.

New model objects:

```text
rail_ft
rail_ft_left_support
rail_ft_right_support
```

## 8. Add the main vertical rails (`main-vertical-rails`)

Install `front_center_rail` between the lower and upper front cross rails.
Install `right_center_rail` between `rail_rbu` and the right top side 4x4.

Check both rails for plumb. Their face orientation matters: the front center
rail supports the power junction box and EV charger, while the right center
rail supports the outlet backers, Wi-Fi access point, and low-voltage paths.

New model objects:

```text
front_center_rail
right_center_rail
```

## 9. Add the tambour vertical supports (`tambour-vertical-rails`)

Install `left_tambour_rail` between `rail_lb` and the left top side 4x4 and
`right_tambour_rail` between `rail_rbu` and the right top side 4x4.

These lumber members support the custom ASA tracks; they are not themselves
the finished tracks. Check both for plumb and verify their inside spacing and
front-to-back position against the full-size track template in
[`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md) before fixing them permanently.
Their modeled Y range is 4 3/4 to 6 1/4 inches, supporting the guide
centerline at y = 5 3/8 inches.

New model objects:

```text
left_tambour_rail
right_tambour_rail
```

## 10. Verify the consolidated tambour top supports (`tambour-top-rails`)

Verify that the inside faces and undersides of the two top side 4x4s provide
continuous, level attachment surfaces for the printed tracks and removable
ceiling retainers. Preserve the modeled rear and front bend clearances and
confirm the support geometry against the prototype alignment gauges.

Trial-fit the removable ceiling panel against its independent retainers, then
remove it until the services and tambour have passed their later clearance
checks.

New model objects:

```text
tambour_ceiling_panel
```

## 11. Install and set the tracks; trial-fit the tambour (`tambour-door`)

Follow [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md) to complete the full-size prototype
and approve the 1/2-by-3/4-inch slat profile, printed pulls, mechanical webbing,
track profile,
loading sections, and end stops before installing production parts. Mount the
mirrored ASA track segments along the modeled paths before installing any nearby
electrical equipment or conduit. Their final position is the controlling
clearance datum for the power-junction assembly, its 1 1/4-inch conduit, and
all outgoing conduit runs; do not use those later assemblies to force or shift
a guide. The track datums' rear lower endpoint is at `y = 21`, `z = 3` inches;
their front lower endpoint is at `y = 5 3/8`, `z = 16` inches; their top
centerline is at `z = 44 1/8` inches; and both turns begin from a modeled
2 5/8-inch centerline radius. The slat center remains offset 3/8 inch from the
datum; the wood is rendered at its actual 1/2-inch depth while the complete
hardware assembly must remain inside the 1 1/2-inch clearance envelope.

Load the completed curtain and cycle it fully using both the lowest pull slat
and the printed pull approximately 18 inches above it. Verify equal tracking,
the approved operating force, clearance from every installed framing member,
and at least 1/4-inch clearance from the installed top bracing using the
approved curtain and pull-slat envelope. Mark all matched track parts, then
remove the curtain, removable loading sections, and end stops. Protect the
fixed tracks from debris, finish, and damage during the remaining work. Before
proceeding, lock the fixed guide geometry, record its critical spacing, and use
the installed guides and those measurements when checking every nearby box and
conduit clearance.

The build-step visualization shows the completed door in its nominal open
position from this step onward; it does not depict this temporary removal.

New model objects:

```text
enclosure_tambour_door
```

## 12. Add the street-light backing (`street-light-backing`)

Install the three 20 1/2-inch front backing 2x4s. The bottom backer starts at a
modeled elevation of 33 inches, the middle backer at 36 1/2 inches, and the
upper backer at 40 inches. Their rearward face position locates the outlet-box
stack relative to the siding, and the bottom backer supports the horizontal
street-light conduit run.

Check that the backers are level, form a continuous field from z = 33 through
43 1/2 inches, and share the modeled street-light centerline at
x = 13 3/4 inches. The outlet box remains centered at z = 40 inches.

New model objects:

```text
front_street_light_backer_bottom
front_street_light_backer_lower
front_street_light_backer_upper
```

## 13. Mount the EV charger with its cord and plug (`ev-charger-mounting`)

Mount the EV charger body and its inseparable flexible cord and plug on
`front_center_rail`, with the charger body shifted 2 inches downward from its
former modeled position while the cord holster remains fixed. Confirm and
record the physical location of its conduit
input; this installed position controls the field-fit conduit connection in
Step 15. Route the cord between the charger body, storage position, and
ground-level reach shown by the model.

Check the flexible cord for strain relief, minimum bend radius, storage
clearance, tambour-door clearance, and absence of abrasion or pinch points.
Cycle the tambour fully from both printed pulls and confirm that neither the
door nor either pull contacts the charger, cord, or plug. Repeat these checks
after making the power connection in Step 15 and after reloading the curtain in
Step 23.

New model objects:

```text
front_ev_charger_body
front_ev_charger_plug
front_ev_charger_cable
```

## 14. Preassemble and mount the power junction (`power-junction-assembly`)

Before mounting the Carlon E987N power junction box, fit its rear-facing
1 1/4-inch input adapter and coupling for the T-body branch and the two
right-side 1/2-inch light and receptacle outlets.
The light outlet is forward of the receptacle outlet. Then mount the connected
box on `front_center_rail`, spanning x = 15 to 19 inches in the default model,
and y = 2.1875 to 6.1875 inches. Its bottom face remains at the modeled
elevation of approximately z = 6.50 inches. Keep every fitting axis aligned
with its conduit path.

Check that the fittings are fully seated and clear of `front_center_rail`.
Keep the rear fitting aligned with the raised 1 1/4-inch feed from the T body.

The #6 charger group continues vertically through the T body and bypasses the
junction box. The #12 supply group branches through the T into the box, where
its hot/hot/neutral conductors feed separate light and outlet hot/neutral pairs
and the #12 equipment grounds are spliced. The modeled junction-box calculation
is 18.00 in³ against an assumed 49.00 in³ marked capacity. Verify the marking
on the installed box and the locally required calculation before construction.

New model objects:

```text
power_junction_box
power_junction_input_adapter
power_junction_input_coupling
power_junction_light_adapter
power_junction_light_coupling
power_junction_outlet_adapter
power_junction_outlet_coupling
```

## 15. Connect the power junction to the EV charger (`ev-charger-power`)

Using the physical charger-input position recorded in Step 13, align the
1 1/4-inch ground riser and T body with the charger's conduit-port X coordinate.
Set the T-body branch high enough that the complete conduit envelope passes
above `rail_fb`, then run the full horizontal branch to the rear coupling on
the junction box. Fit the reducer at the T body's upward outlet and run the
straight 1-inch conduit to the bottom of the charger.

Check alignment at the riser, junction box, top adapter and coupling, and
charger entry. Route the unspliced #6 charger group through this conduit
according to the approved electrical design. Verify that the power path remains
clear of the cord-storage volume. Check the flexible cord for strain relief,
minimum bend radius, storage clearance, tambour-door clearance, and absence of
abrasion or pinch points. Cycle the tambour fully from both printed pulls and
confirm that neither the door nor either pull contacts the completed power
connection, charger, cord, or plug. Verify the installed product markings and
locally required bend and fill calculations before construction. Repeat the
clearance check after the curtain is reloaded in Step 23.

New model objects:

```text
power_ev_charger_feed
power_ev_reducer
power_ev_t_body
power_t_junction_feed
```

## 16. Rough in the street light (`street-light-rough-in`)

Mount the Commercial Electric WRB550B base box on the street-light backers.
Install the 1/2-inch feed from the forward fitting on the positive-X side of
the power junction box. Run toward positive X and make the first modeled
2 1/2-inch-radius sweep upward against the negative-X face of `post_fr`. Make the
required Y transition gradually on this long rising leg. At z = 34 inches,
make the second 3-inch-radius sweep toward negative X, support the horizontal
run on the bottom backer, and make the third 3-inch-radius sweep toward
positive Z into the bottom port of the WRB550B base box at x = 13.75,
y = 1.5, and z = 37.3 inches. The junction-box fitting center is at
y = 3.1875 inches, leaving approximately 0.14 inch between the conduit
envelope and the closed tambour plane.

Check that the box is centered at x = 13 3/4 inches and z = 40 inches, the
unused side and top ports are plugged, the horizontal run is securely strapped
to its backing, and the conduit stays forward of the open tambour door at
y = 5 inches. Pull and terminate the light branch's #12 conductors only
under the approved wiring design.

New model objects:

```text
front_street_light_base_box
power_street_light_feed
```

## 17. Add the backing and rough in the right-side outlet (`outlet-rough-in`)

Install the two 6 11/16-inch 2x4 backers between `right_center_rail` and
`post_br`. Their modeled lower-face elevations are approximately 13 5/8 and
18 7/8 inches. Check that both backing faces are coplanar at x = 26.45 inches;
this plane sets the rear of the 2.30-inch-deep FSE outlet box and its final
projection through the siding.

Immediately after securing the backing, mount the Carlon E980DFN FSE box and
install the 1/2-inch feed from the junction box, including both modeled
4-inch-radius sweeps into the bottom hub.

Check that the box/cover mating plane will finish at x = 28.75 inches, roughly
1/4 inch beyond the siding, and that the hub center is at x = 27.016 inches.
Confirm conduit clearances before covering the framing. Pull and terminate the
outlet branch's #12 conductors only under the approved wiring design.

New model objects:

```text
back_right_outlet_backer_lower
back_right_outlet_backer_upper
back_right_outlet
power_back_right_outlet_feed
```

## 18. Add the low-voltage termination (`low-voltage-termination`)

Mount the low-voltage junction box in its shifted position, spanning x = 10
to 14 inches and y = 2.1875 to 6.1875 inches, centered at z = 13 inches. The
power junction spans x = 15 to 19 inches, so both boxes share the same
positive-Y face and retain a one-inch X gap. Future backing lumber may be
added but is not included. Connect
the rear portion of the bottom panel to the 3/4-inch riser installed in Step 1,
then add the three cable glands across the front portion of the bottom panel.

Keep each fitting center at least 3/4 inch from the panel sides. Confirm that
the riser remains plumb and clear of the 10-inch footing and that the existing
cables have room to leave the forward glands in negative Z before sweeping
toward the center framing. Route the blue Cat 6 feeds beside the 3/4-inch
riser, retaining the modeled clearance. Use
the modeled 0.625-inch upward turn beneath the glands, remain on the negative-Y
side of `rail_fb` until above it. Use the gentle departure spline modeled for
the dark-brown street-light cable; it bottoms at z = 8.25 inches without a flat
horizontal run.

New model objects:

```text
low_voltage_termination_box
low_voltage_input_adapter
low_voltage_cable_gland_1
low_voltage_cable_gland_2
low_voltage_cable_gland_3
```

## 19. Mount and cable the Wi-Fi access point (`wifi-and-feed`)

Mount the Wi-Fi access point near the top of `right_center_rail`. Route the
highest-X low-voltage gland's cable through the modeled droop, then sweep it
gradually in positive X as it rises toward `front_center_rail`. Reach the
positive-X face near z = 10.25 inches, hold that X coordinate while sweeping to
the rail's center Y coordinate near z = 15 inches, carry it straight upward,
and bend around
the positive-Y face of the rail near the top, cross in positive X along the
positive-Y face of `rail_ft`, and descend the negative-X face of
`right_center_rail`. Just below the access point, bend around the rail's
positive-Y face and sweep upward into the existing bottom entry.
Identify this run as blue Cat 6 cable in accordance with the model.

Check that the cable retains at least the modeled 0.625-inch minimum bend
radius and remains clear throughout the tambour door's travel.

New model objects:

```text
front_wifi_access_point
low_voltage_wifi_feed
```

## 20. Route the street-light service cable (`light-service-cable`)

Route the front low-voltage gland's cable downward before sweeping toward and
up the positive-X face of `post_fl`. Continue beneath `brace_fl_fr` and
approach the mirrored service loop above the street-light box stack from the
negative-X direction. The loop returns in that direction before terminating
at the existing conduit entry.
The model renders this low-voltage cable dark brown.

Check attachment clearances, the 1 1/4-inch service-loop radius, the overall
0.625-inch minimum bend radius, clearance from the street-light backing, and
separation required by the approved wiring design.

New model objects:

```text
low_voltage_street_light_service
```

## 21. Route the charger low-voltage feed (`charger-low-voltage-feed`)

Route the center low-voltage gland's cable down from the gland and up the
negative-X face of `front_center_rail`. Hold the gland's X coordinate through
the droop and ascending return until z = 10 inches, then sweep toward the rail.
As it approaches
the elevation of the EV charger's bottom plane, bend in positive Y to clear the
positive-Y face of the rail, then sweep upward into the charger's unchanged
bottom entry.
Identify this run as blue Cat 6 cable in accordance with the model.

Check its direct entry sweep, the 0.625-inch minimum bend radius, and clearance
from the tambour door, power conduit, and siding through the door's full
travel.

New model objects:

```text
low_voltage_ev_charger_feed
```

## 22. Install the composite siding (`composite-siding`)

Before placing the top boards, install 1/4-inch ripped pressure-treated shims
on the exposed portions of all four perimeter members and across both
non-gusseted corner posts. Keep the shims level and terminate them at the custom
gusset envelopes so no shim rests on a plate or pan head. Let the decking span
these short interruptions, and leave drainage paths at the plate edges. Use
roof fasteners long enough to
retain the originally required penetration after passing through the shims.

Install the composite boards only after the framing, tambour guides, interior
equipment, conduit, and cable routes are installed, inspected, and proven clear
through the door's full travel. Only siding trim, tambour reloading, and the
fixtures or covers that mount outside the siding follow this step.

The model represents 48 physical cuts as 57 rendered pieces because
boards interrupted by the street-light and outlet openings, and the top rear
board surrounding the tambour opening, are split into multiple solids.

Maintain the modeled bottom elevation of 2 inches and the front-light,
right-outlet, and rear-tambour openings. Dry-fit opening courses before cutting
and confirm the electrical boxes' finish projections. The current BOM totals
870 3/4 inches of composite decking and allocates five 16-foot stock boards.

New model objects:

```text
roof_shim_brace_fl_fr
roof_shim_brace_fl_bl
roof_shim_brace_bl_br
roof_shim_brace_fr_br
enclosure_siding_top_1
enclosure_siding_top_2
enclosure_siding_top_3
enclosure_siding_top_4
enclosure_siding_front_1
enclosure_siding_left_1
enclosure_siding_right_1
enclosure_siding_rear_top_left
enclosure_siding_rear_top_header
enclosure_siding_rear_top_right
enclosure_siding_front_2_1
enclosure_siding_front_2_2
enclosure_siding_front_2_3
enclosure_siding_front_2_4
enclosure_siding_left_2
enclosure_siding_right_2
enclosure_siding_rear_left_2
enclosure_siding_rear_right_2
enclosure_siding_front_3
enclosure_siding_left_3
enclosure_siding_right_3
enclosure_siding_rear_left_3
enclosure_siding_rear_right_3
enclosure_siding_front_4
enclosure_siding_left_4
enclosure_siding_right_4
enclosure_siding_rear_left_4
enclosure_siding_rear_right_4
enclosure_siding_front_5
enclosure_siding_left_5
enclosure_siding_right_5_1
enclosure_siding_right_5_2
enclosure_siding_right_5_3
enclosure_siding_rear_left_5
enclosure_siding_rear_right_5
enclosure_siding_front_6
enclosure_siding_left_6
enclosure_siding_right_6_1
enclosure_siding_right_6_2
enclosure_siding_right_6_3
enclosure_siding_rear_left_6
enclosure_siding_rear_right_6
enclosure_siding_front_7
enclosure_siding_left_7
enclosure_siding_right_7
enclosure_siding_rear_left_7
enclosure_siding_rear_right_7
enclosure_siding_front_8
enclosure_siding_left_8
enclosure_siding_right_8
enclosure_siding_rear_left_8
enclosure_siding_rear_right_8
enclosure_siding_front_9
enclosure_siding_left_9
enclosure_siding_right_9
enclosure_siding_rear_left_9
enclosure_siding_rear_right_9
```

## 23. Install the siding trim and reload the tambour (`siding-trim`)

Install the paired black-aluminum angle legs at all four enclosure corners and
both sides of the tambour opening, then install the paired header legs. The
vertical trim pieces are modeled at 46 inches; the rear opening header is
20 1/2 inches.

Check the trim for plumb, straight edges, safe cut edges, and interference-free
clearance around the tambour opening. Uncover and clean the fixed ASA tracks,
then recheck their spacing and joints in case the siding or trim moved them.
Reload the curtain through the removable lower-rear sections and reinstall the
end stops. Cycle the door fully from both printed pulls and repeat the
operating-force, tracking, endpoint-retention, and framing/trim clearance tests
from [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md). Repeat the full-travel clearance
check against every completed conduit and fixed cable route. Install the
removable 20 1/2-by-8 7/8-inch, 1/4-inch plywood ceiling panel on independent
retainers at z = 43 1/4 to 43 1/2 inches beneath the overhead curtain, then
repeat the full-travel test before placing the enclosure in service.

New model objects:

```text
enclosure_siding_angle_front_left_a
enclosure_siding_angle_front_left_b
enclosure_siding_angle_front_right_a
enclosure_siding_angle_front_right_b
enclosure_siding_angle_rear_left_a
enclosure_siding_angle_rear_left_b
enclosure_siding_angle_rear_right_a
enclosure_siding_angle_rear_right_b
enclosure_siding_angle_tambour_left_a
enclosure_siding_angle_tambour_left_b
enclosure_siding_angle_tambour_right_a
enclosure_siding_angle_tambour_right_b
enclosure_siding_angle_tambour_header_face
enclosure_siding_angle_tambour_header_bottom
```

## 24. Finish the street-light assembly (`street-light-finish`)

Install the WRE450G extension ring through the siding opening, with its front
face flush with the siding exterior plane, then attach the downward-facing
street-light fixture.

Check the gasketed/weatherproof assembly, unused-port plugs, fixture alignment,
and siding clearance. Complete conductor termination and testing under the
approved electrical design.

New model objects:

```text
front_street_light_extension_ring
front_street_light
```

## 25. Finish the right-side outlet (`outlet-finish`)

Install the Intermatic WP5100BL in-use cover on the FSE box after the siding is
complete.

Check the cover gasket, weatherproof mating surface, full opening range, and
finished projection. Complete receptacle installation, conductor termination,
and testing under the approved electrical design; the receptacle itself is not
modeled.

New model objects:

```text
back_right_outlet_cover
```

## Model coverage checklist

The 25 steps above assign all modeled construction objects exactly once:

| Category | Modeled count | Assigned steps |
| --- | ---: | --- |
| Lumber members | 29 | 2-9, 11-12, 17 |
| Components and fittings | 25 | 13-19, 23-25 |
| Conduit runs | 6 | 1, 15-17 |
| Cable paths | 4 | 13, 19-21 |
| Tambour assemblies | 1 | 10 |
| Composite siding render parts | 58 | 22 |
| Siding trim render parts | 14 | 23 |

The `ground` object is visualization context rather than an installed enclosure
component, so it intentionally remains outside the numbered sequence.
