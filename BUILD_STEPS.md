# EV Charger Enclosure Build Steps

This guide describes the modeled construction sequence for the fixed enclosure
design: 24-inch left-to-right post center spacing, 18 3/8-inch front-to-back post
center spacing, 47 inches above grade, and 32 inches of each post below grade.
Dimensions and cut lengths below apply to this design only.

The generated BOM and cut list remain the authoritative material references
for generated modeled materials. The custom tambour curtain, guide liners,
backing, pulls, and associated hardware remain provisional and are documented
separately in [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md); they are not yet included in
the generated material outputs.

The top-plane bracing decision, site load screen, and required connection
capacity are documented in [`TOP_BRACING.md`](TOP_BRACING.md).

This guide does not define fasteners, structural connections, concrete work,
or the means and methods for excavation or underground work. It does require
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
1 1/4-inch power riser out of the ground beneath the back-left corner of the
power junction box (x = 14.975 inches and y = 4.2125 inches in the default
model) and bring the modeled 3/4-inch low-voltage riser out beneath the rear of
its junction box.
Its default axis is approximately x = 12.17 inches and y = 5.44 inches, clear
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

Install the four top perimeter 2x4 braces, followed by the single stress-rated
nominal 1x4 diagonal. The perimeter cuts are two at 20 1/2 inches and two at
14 7/8 inches. The diagonal cut is 25 5/16 inches in the model. Its top remains
flush with the 47-inch frame top, placing its underside at 46 1/4 inches and
recovering 3/4 inch of interior clearance relative to the former 2x4
diagonals.

Before fastening the permanent bracing, reconfirm that every post is plumb and
compare the frame diagonals. Install the braces without pulling the posts out
of alignment, then repeat the plumb and square checks. Use only the
species/grade and positive two-way connection approved against the 826-pound
ASD brace demand in `TOP_BRACING.md`; ordinary deck screws, end-grain screws,
and unverified toe-screw patterns are not acceptable. Remove temporary
external bracing only after the permanent frame and its connections are
approved and stable.

New model objects:

```text
brace_fl_fr
brace_fl_bl
brace_bl_br
brace_fr_br
brace_bl_fr
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

Install the three 14 7/8-inch rails: the right intermediate receiver rail and
the upper left and right rails. Keep their modeled wide faces horizontal.

Check that `rail_lt` and `rail_rt` are level with each other and 42 3/4 inches
above the nominal ground datum at their lower faces. Check `rail_rbu` at its
modeled lower-face elevation of 11 1/4 inches; it receives the right-side
vertical rails in Step 8 and Step 9. Reconfirm post plumbness and the frame
diagonals as these rails are fastened.

New model objects:

```text
rail_rbu
rail_lt
rail_rt
```

## 7. Add the upper front cross rail (`upper-front-rail`)

Install the 20 1/2-inch 2x4 `rail_ft` with its lower and upper faces at
z = 41 and 42 1/2 inches. Install the two 1 3/4-inch vertical 2x4 support
blocks between its ends and the undersides of `rail_lt` and `rail_rt`.

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

Install the 33 1/4-inch `front_center_rail` between the lower and upper front cross
rails. Install the 30-inch `right_center_rail` between `rail_rbu` and `rail_rt`.

Check both rails for plumb. Their face orientation matters: the front center
rail supports the power junction box and EV charger, while the right center
rail supports the outlet backers, Wi-Fi access point, and low-voltage paths.

New model objects:

```text
front_center_rail
right_center_rail
```

## 9. Add the tambour vertical supports (`tambour-vertical-rails`)

Install the 39-inch `left_tambour_rail` between `rail_lb` and `rail_lt` and the
30-inch `right_tambour_rail` between `rail_rbu` and `rail_rt`.

These lumber members support the custom guide liners; they are not themselves
the finished tracks. Check both for plumb and verify their inside spacing and
front-to-back position against the full-size track template in
[`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md) before fixing them permanently.
Their modeled Y range is 4 3/4 to 6 1/4 inches, supporting the guide
centerline at y = 5 inches.

New model objects:

```text
left_tambour_rail
right_tambour_rail
```

## 10. Add the tambour top supports (`tambour-top-rails`)

Install the left and right 14 7/8-inch top rails at the modeled lower-face
elevation of 43 3/4 inches. Their upper faces are at 45 1/4 inches, leaving
1/4 inch below the perimeter braces. These lumber members support the guide
liners that define the upper path of the door.

Check that the two rails are level, parallel, and aligned with the vertical
tambour supports. Preserve the modeled rear and front bend clearances and
verify the completed support geometry against the prototype alignment gauges
before fabricating or mounting the production liners.

New model objects:

```text
rail_l_tambour
rail_r_tambour
```

## 11. Install and set the tracks; trial-fit the tambour (`tambour-door`)

Follow [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md) to complete the full-size prototype
and approve the slat profile, recessed pulls, flexible backing, track profile,
loading sections, and end stops before installing production parts. Mount the
mirrored guide liners along the modeled paths before installing any nearby
electrical equipment or conduit. Their final position is the controlling
clearance datum for the power-junction assembly, its 1 1/4-inch conduit, and
all outgoing conduit runs; do not use those later assemblies to force or shift
a guide. The guide liners' rear lower endpoint is at z = 3 inches, their front
lower endpoint is at z = 16 inches, their top centerline is at z = 44 1/2 inches,
and both turns begin from a modeled 3-inch centerline radius.

Load the completed curtain and cycle it fully using both the lowest pull slat
and the recessed pull approximately 18 inches above it. Verify equal tracking,
the approved operating force, clearance from every installed framing member,
and at least 1/4-inch clearance from the installed top bracing using the
approved curtain and pull-slat envelope. Mark all matched track parts, then
remove the curtain, removable loading sections, and end stops. Protect the
fixed liners from debris, finish, and damage during the remaining work. Before
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
`front_center_rail`. Confirm and record the physical location of its conduit
input; this installed position controls the field-fit conduit connection in
Step 15. Route the cord between the charger body, storage position, and
ground-level reach shown by the model.

Check the flexible cord for strain relief, minimum bend radius, storage
clearance, tambour-door clearance, and absence of abrasion or pinch points.
Cycle the tambour fully from both recessed pulls and confirm that neither the
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

Before mounting the Carlon E987N power junction box, fit its bottom-facing
1 1/4-inch input adapter and coupling at the back-left corner, rear-facing
1 1/4-inch charger outlet, and the two right-side 1/2-inch light and receptacle
outlets.
The light outlet is forward of the receptacle outlet. Then mount the connected
box on `front_center_rail`, spanning x = 14 to 18 inches in the default model,
and y = 1.1875 to 5.1875 inches. Its bottom face remains at the modeled
elevation of approximately z = 6.50 inches. Keep every fitting axis aligned
with its conduit path.

Check that the fittings are fully seated and clear of `front_center_rail`.
Keep the charger fitting aligned with the short 1 1/4-inch feed to the LB body.

The incoming #6 and #12 groups enter through the bottom riser. The #12
hot/hot/neutral conductors feed separate light and outlet hot/neutral pairs,
the #12 equipment grounds are spliced, and the #6 charger conductors continue
unspliced to the charger. The conservative junction-box calculation is 37.00
in³ against an assumed 49.00 in³ marked capacity. Verify the marking on the
installed box and the locally required calculation before construction.

New model objects:

```text
power_junction_box
power_junction_input_adapter
power_junction_input_coupling
power_junction_ev_adapter
power_junction_ev_coupling
power_junction_light_adapter
power_junction_light_coupling
power_junction_outlet_adapter
power_junction_outlet_coupling
```

## 15. Connect the power junction to the EV charger (`ev-charger-power`)

Using the physical charger-input position recorded in Step 13, run the short
1 1/4-inch feed rearward from the junction coupling into the LB conduit body.
Fit the reducer at its upward outlet, then form the modeled 1-inch spline from
the reducer to the bottom of the charger.

Check alignment at the riser, junction box, top adapter and coupling, and
charger entry. Route the unspliced #6 charger group through this conduit
according to the approved electrical design. Verify that the power path remains
clear of the cord-storage volume. Check the flexible cord for strain relief,
minimum bend radius, storage clearance, tambour-door clearance, and absence of
abrasion or pinch points. Cycle the tambour fully from both recessed pulls and
confirm that neither the door nor either pull contacts the completed power
connection, charger, cord, or plug. Verify the installed product markings and
locally required bend and fill calculations before construction. Repeat the
clearance check after the curtain is reloaded in Step 23.

New model objects:

```text
power_ev_charger_feed
power_ev_lb_body
power_ev_lb_feed
power_ev_reducer
```

## 16. Rough in the street light (`street-light-rough-in`)

Mount the Commercial Electric WRB550B base box on the street-light backers.
Install the 1/2-inch feed from the forward fitting on the positive-X side of
the power junction box. Run toward positive X and make the first modeled
3-inch-radius sweep upward against the negative-X face of `post_fr`. Make the
required Y transition gradually on this long rising leg. At z = 34 inches,
make the second 3-inch-radius sweep toward negative X, support the horizontal
run on the bottom backer, and make the third 3-inch-radius sweep toward
positive Z into the bottom port of the WRB550B base box at x = 13.75,
y = 1.5, and z = 37.3 inches. The junction-box fitting center is at
y = 2.1875 inches, leaving approximately 1.14 inches between the conduit
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

Mount the low-voltage junction box in its unchanged position, spanning x = 9
to 13 inches and y = 2.1875 to 6.1875 inches, centered at z = 13 inches. The
power junction spans x = 14 to 18 inches and sits one inch farther forward in
negative Y. The boxes retain a one-inch X gap. Future backing lumber may be
added but is not included. Connect
the rear portion of the bottom panel to the 3/4-inch riser installed in Step 1,
then add the three cable glands across the front portion of the bottom panel.

Keep each fitting center at least 3/4 inch from the panel sides. Confirm that
the riser remains plumb and clear of the 10-inch footing and that the existing
cables have room to leave the forward glands in negative Z before sweeping
toward the negative-X side of the framing. Route the blue Cat 6 feeds around
opposite X sides of the 3/4-inch riser, retaining the modeled clearance. Use
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
center low-voltage gland's cable down from the gland, sweep it toward the
negative-X face of `front_center_rail`, and carry it up that face. Bend around
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

Route the rear low-voltage gland's cable parallel to the Wi-Fi feed: down from
the gland and up the negative-X face of `front_center_rail`. As it approaches
the elevation of the EV charger's bottom plane, bend in positive Y to clear the
positive-Y face of the rail, then sweep upward into the charger's unchanged
bottom entry. Maintain the modeled one-cable-diameter separation between the
two low-voltage lanes until the charger feed branches.
Identify this run as blue Cat 6 cable in accordance with the model.

Check its direct entry sweep, the 0.625-inch minimum bend radius, and clearance
from the tambour door, power conduit, and siding through the door's full
travel.

New model objects:

```text
low_voltage_ev_charger_feed
```

## 22. Install the composite siding (`composite-siding`)

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
clearance around the tambour opening. Uncover and clean the fixed guide liners,
then recheck their spacing and joints in case the siding or trim moved them.
Reload the curtain through the removable lower-rear sections and reinstall the
end stops. Cycle the door fully from both recessed pulls and repeat the
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
tambour_ceiling_panel
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
