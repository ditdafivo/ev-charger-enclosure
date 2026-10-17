# EV Charger Enclosure Build Steps

This guide describes the modeled construction sequence for the fixed enclosure
design: 24-inch left-to-right post center spacing, 19 3/8-inch front-to-back post
center spacing, and level finished post tops 49 5/8 inches above the front-left
outside-corner ground datum. The other surveyed ground-to-top heights are
49 1/4 inches at front-right, 48 1/2 at back-left, and 47 at back-right.
All model Z elevations use that front-left ground datum.
Dimensions and cut lengths below apply to this design only.

The generated BOM and cut list remain the authoritative material references
for generated modeled materials. Tambour installation is deferred indefinitely;
its prototype and fabrication notes remain in [`TAMBOUR_DOOR.md`](TAMBOUR_DOOR.md)
for future reference.

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
- Every modeled construction object is introduced in exactly one step or is
  listed as a deferred reference object. The ground plane is permanent context
  and is not assigned to a step.
- Deferred objects are hidden by default. Set `show_deferred = true` to show
  them in the completed-model view; they do not appear in numbered steps.
- The OpenSCAD `build_step` parameter behaves as follows:
  - `build_step = 0`: show only permanent context, including the ground plane.
  - `build_step = 1..24`: show earlier objects normally, highlight objects from
    the selected step, and hide objects from later steps.
  - `build_step = 25`: show the completed model in its normal colors.
- An invalid positive step number should fail clearly during generation rather
  than silently display an incomplete or misleading model.

## 1. Complete the underground conduit risers and restore grade (`underground-risers`)

Before installing any posts, establish the enclosure layout from protected
reference points and mark all four 10-inch footing circles. Route both
underground conduit runs through the enclosure interior and clear of the full
footing excavations before sweeping them up to the risers. Bring the modeled
1 1/4-inch power riser out of the ground at its fixed modeled axis
(x = 15.055 inches and y = 12.5 inches in the default model) and bring the
modeled 3/4-inch low-voltage riser out at its fixed ground-entry axis
(x = 14 inches and y = 6.25 inches). At grade, use two matching Carlon
45-degree belled elbows to offset the low-voltage run toward negative X, then
continue vertically from the second elbow. These ground-entry positions remain
fixed while the center-rail assembly and its equipment move rearward. Leave
both upper ends positioned for the later equipment connections.

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
low_voltage_ground_riser_inlet
low_voltage_ground_sweep_elbow_1
low_voltage_ground_sweep_elbow_2
```

## 2. Install the four posts (`posts`)

Excavate and fill four 10-inch-diameter gravel footings from 36 inches below
the front-left ground datum to local grade, centered on the post centerlines.
Position four 4x4 posts on the 24-by-19 3/8-inch centerline rectangle with all
finished tops level at `z = 49.625`. The model assumes bottoms at `z = -32`,
so each modeled post is 81 5/8 inches long, with 4 inches of gravel beneath it.
Actual buried lengths were not measured. The uneven ground matches the four
outside-corner readings; footing tops follow grade at their centerlines.

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

The installed diagonal was cut to friction fit between the back-left and
front-right posts and secured with gussets. Keep the four finished post tops,
2x4 front/back perimeter braces, and 4x4 left/right braces flush at
`z = 49.625`. The flat 1x6 diagonal occupies `z = 48.875` to `49.625` and ends
against the posts' opposing front/back faces. It does not cover their tops.

The modeled full-width 5.5-inch board needs a rectangular blank at least
31.369 inches long. Use the generated end profile as a layout reference and
preserve the actual friction fit against both posts. The modeled 3/4-inch
seats in `output/fabrication.csv` occur only in the left and right side braces.

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

Install the 15 7/8-inch upper `rail_lbu` and `rail_rbu` 2x4 rails between their
front and back posts. Their modeled bottom elevation is 12 1/4 inches above
the nominal ground datum. Install the matching lower `rail_lbl` and `rail_rbl`
between the same posts, with modeled bottoms at 5 1/4 inches. This places the
lower pair one inch below the former right lower rail position. Keep all four
wide faces horizontal.

Check that each left/right pair is level, that the clear spacing between posts
remains 15 7/8 inches, and that all four posts remain plumb. Adjust the
temporary bracing rather than using these rails to pull the posts into place.

New model objects:

```text
rail_lbu
rail_rbu
rail_lbl
rail_rbl
```

## 5. Add the lower front cross rail (`lower-front-rail`)

Install the 20 1/2-inch upper `rail_fbu` between `rail_lbu` and `rail_rbu`, and
the matching lower `rail_fbl` between `rail_lbl` and `rail_rbl`. Their modeled
Y center coordinates are the same, and their front faces are offset toward the
enclosure interior. `rail_fbl` provides a lower support edge for the power
junction box installed in Step 11. The conduit boxes and fittings retain their
absolute modeled coordinates while their eventual mounting arrangement is
deferred.

Check both rails for level, square, and correct orientation before adding the
vertical member in Step 9.

New model objects:

```text
rail_fbu
rail_fbl
```

## 6. Add the front support rails (`front-support-rails`)

Install `rail_ltam` and `rail_rtam` vertically between `rail_lbu`/`rail_rbu` and
the undersides of the top side 4x4s. Their modeled Y range is 4 1/4 to
5 3/4 inches. Keep them plumb, parallel, and directly opposite one another.
Leave their inner faces accessible for possible future tambour fittings.

New model objects:

```text
rail_ltam
rail_rtam
```

## 7. Add the side receiver rails (`upper-side-rails`)

Install `rail_lt` and `rail_rt` from the corresponding front support rail to
the back post; their modeled lower and upper faces are at `z = 43 1/2` and
`45` inches. Keep both wide faces horizontal.

Check the receiver rails for level and confirm that the two upper rails remain
opposite one another. Their front ends depend on the plumb support rails
installed in Step 6, and their aligned inside faces receive `rail_ft` in
Step 8.

New model objects:

```text
rail_lt
rail_rt
```

## 8. Add the upper front cross rail (`upper-front-rail`)

Install the 20 1/2-inch 2x4 `rail_ft` between `rail_lt` and `rail_rt`, with its
lower and upper faces at `z = 43 1/2` and `45` inches. Its modeled Y range
is `7 3/16` to `10 11/16` inches. Fasten its complete end faces to the side
rails; the former separate vertical header-support blocks are not used.

Check the header for level and square and verify its position before adding
`front_center_rail`. Use connections designed for the charger dead load and
the repeated lateral and torsional loads produced while handling its cord.

New model objects:

```text
rail_ft
```

## 9. Add the front center rail (`front-center-rail`)

Install `front_center_rail` between `rail_fbu` and `rail_ft`.

Check the rail for plumb. Its face orientation matters because it supports the
power junction box and EV charger.

New model objects:

```text
front_center_rail
```

## 10. Mount the EV charger with its cord and plug (`ev-charger-mounting`)

Mount the EV charger body and its inseparable flexible cord and plug on
`front_center_rail`, with the charger body shifted 2 inches downward from its
former modeled position while the cord holster remains fixed. Confirm and
record the physical location of its conduit
input; this installed position controls the field-fit conduit connection in
Step 12. Route the cord between the charger body, storage position, and
ground-level reach shown by the model.

Check the flexible cord for strain relief, minimum bend radius, storage
clearance, and absence of abrasion or pinch points. Repeat these checks after
making the power connection in Step 12.

New model objects:

```text
front_ev_charger_body
front_ev_charger_plug
front_ev_charger_cable
```

## 11. Preassemble and mount the power junction (`power-junction-assembly`)

Before mounting the Carlon E987N power junction box, fit its rear-facing
1 1/4-inch input adapter and coupling for the rear port of the Type TB body and
the two right-side 1/2-inch light and receptacle outlets.
The light outlet is forward of the receptacle outlet. Then mount the connected
box on `front_center_rail`, spanning x = 13 to 17 inches in the default model,
and y = 3.1875 to 7.1875 inches. Its bottom face remains at the modeled
elevation of approximately z = 6.51 inches, supported along its lower edge by
`rail_fbl`. Keep every fitting axis aligned with its conduit path.

Check that the fittings are fully seated and clear of `front_center_rail`.
Keep the rear fitting aligned with the raised 1 1/4-inch feed from the Type TB body.

The #6 charger group continues vertically through the Type TB body and bypasses
the junction box. The #12 supply group branches through the Type TB body's rear
port into the box, where
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

## 12. Connect the power junction to the EV charger (`ev-charger-power`)

Using the physical charger-input position recorded in Step 10, align the
1 1/4-inch ground riser and Type TB body with the charger's conduit-port X coordinate.
Set the TB-body rear port high enough that the complete conduit envelope passes
above `rail_fbu`, then run the full horizontal branch to the rear coupling on
the junction box. Fit the reducer at the Type TB body's upward outlet and run the
straight 1-inch conduit to the bottom of the charger.

Check alignment at the riser, junction box, top adapter and coupling, and
charger entry. Route the unspliced #6 charger group through this conduit
according to the approved electrical design. Verify that the power path remains
clear of the cord-storage volume and adjacent framing. Check the flexible cord
for strain relief, minimum bend radius, storage clearance, and absence of
abrasion or pinch points. Verify the installed product markings and locally
required bend and fill calculations before construction.

New model objects:

```text
power_ev_charger_feed
power_ev_reducer
power_ev_tb_body
power_tb_junction_feed
```

## 13. Add the street-light backing (`street-light-backing`)

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

## 14. Rough in the street light (`street-light-rough-in`)

Mount the Commercial Electric WRB550B base box on the street-light backers.
Install the 1/2-inch feed from the forward fitting on the positive-X side of
the power junction box. Run toward positive X and make the first modeled
2 1/2-inch-radius sweep upward against the negative-X face of `post_fr`. Make the
required Y transition gradually on this long rising leg. At z = 34 inches,
make the second 3-inch-radius sweep toward negative X, support the horizontal
run on the bottom backer, and make the third 3-inch-radius sweep toward
positive Z into the bottom port of the WRB550B base box at x = 13.75,
y = 1.5, and z = 37.3 inches. The junction-box fitting center is at
y = 4.1875 inches.

Check that the box is centered at x = 13 3/4 inches and z = 40 inches, the
unused side and top ports are plugged, the horizontal run is securely strapped
to its backing and clear of adjacent framing and equipment. Pull and terminate
the light branch's #12 conductors only under the approved wiring design.

New model objects:

```text
front_street_light_base_box
power_street_light_feed
```

## 15. Install the right-side framing, backing, and outlet (`outlet-rough-in`)

Install `right_center_rail` vertically between `rail_rbu` and `rail_rt`, and
check that it is plumb. It supports the outlet backers installed in this step,
the Wi-Fi access point, and the low-voltage paths installed later.

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
right_center_rail
back_right_outlet_backer_lower
back_right_outlet_backer_upper
back_right_outlet
power_back_right_outlet_feed
```

## 16. Add the low-voltage termination (`low-voltage-termination`)

Mount the low-voltage junction box with its bottom adapter centered at the
upper 45-degree elbow outlet (nominally x = 10.657, y = 6.25, z = 9.912
inches). The adapter meets that outlet directly. The box spans approximately
x = 8.657 to 12.657 and y = 3.1875 to 7.1875 inches, with its center at
z = 13.382 inches. Its back is flush with the front face of `rail_fbu`; the
bottom entry is offset toward the back at y = 6.25 inches to meet the elbow.
The power junction spans x = 13 to 17 inches. Future backing lumber may be
added but is not included. Field-locate the bottom opening from the as-built
elbow position. Then add the three cable glands in
the remaining bottom-panel area; reposition their nominal front-row layout as necessary to
preserve fitting clearances.

Keep each fitting center at least 3/4 inch from the panel sides. Confirm that
the riser remains plumb and clear of the 10-inch footing and that the existing
cables have room to leave the forward glands in negative Z before sweeping
toward the center framing. Route the blue Cat 6 feeds beside the 3/4-inch
riser, retaining the modeled clearance. Use
the modeled 0.625-inch upward turn beneath the glands, remain on the negative-Y
side of `rail_fbu` until above it. Use the gentle departure spline modeled for
the dark-brown street-light cable; it bottoms at z = 8.63 inches without a flat
horizontal run.

New model objects:

```text
low_voltage_termination_box
low_voltage_input_adapter
low_voltage_cable_gland_1
low_voltage_cable_gland_2
low_voltage_cable_gland_3
```

## 17. Mount and cable the Wi-Fi access point (`wifi-and-feed`)

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
radius and remains clear of adjacent framing and equipment.

New model objects:

```text
front_wifi_access_point
low_voltage_wifi_feed
```

## 18. Route the street-light service cable (`light-service-cable`)

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

## 19. Route the charger low-voltage feed (`charger-low-voltage-feed`)

Route the center low-voltage gland's cable down from the gland and up the
negative-X face of `front_center_rail`. Sweep it in positive X through the
droop and ascending return to bypass the centered 3/4-inch riser, then continue
toward the rail. As it approaches
the elevation of the EV charger's bottom plane, bend in positive Y to clear the
positive-Y face of the rail, then sweep upward into the charger's unchanged
bottom entry.
Identify this run as blue Cat 6 cable in accordance with the model.

Check its direct entry sweep, the 0.625-inch minimum bend radius, and clearance
from the power conduit, framing, and siding.

New model objects:

```text
low_voltage_ev_charger_feed
```

## 20. Install the composite siding (`composite-siding`)

Before placing the top boards, install 1/4-inch ripped pressure-treated shims
on the exposed portions of all four perimeter members and across both
non-gusseted corner posts. Keep the shims level and terminate them at the custom
gusset envelopes so no shim rests on a plate or pan head. Let the decking span
these short interruptions, and leave drainage paths at the plate edges. Use
roof fasteners long enough to
retain the originally required penetration after passing through the shims.

Install the composite boards after the framing, interior equipment, conduit,
and cable routes are installed and inspected. Only siding trim and the fixtures
or covers that mount outside the siding follow this step.

The generated siding cut list accounts for boards interrupted by the
street-light and outlet openings and the top rear board surrounding the tambour
opening. Those boards are split into multiple rendered solids.

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
enclosure_siding_top_5
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
enclosure_siding_right_5
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
enclosure_siding_right_7_1
enclosure_siding_right_7_2
enclosure_siding_right_7_3
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

## 21. Install the siding trim (`siding-trim`)

Install the paired black-aluminum angle legs at all four enclosure corners and
both sides of the tambour opening, then install the paired header legs. The
vertical trim pieces are modeled at 46 inches; the rear opening header is
20 1/2 inches.

Check the trim for plumb, straight edges, safe cut edges, and clear openings
around the enclosure. The rear opening remains available for a possible future
tambour installation.

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

## 22. Finish the street-light assembly (`street-light-finish`)

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

## 23. Finish the right-side outlet (`outlet-finish`)

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

## 24. Install the wood power-cord bumper (`power-cord-guard`)

Cut two 13 1/2-inch 2x4 uprights and one 6 1/4-by-13 1/2-inch panel from
1/4-inch exterior plywood. Rip the upright depth to approximately 3 inches;
the exact modeled depth places the panel's rear face 1/4 inch beyond the Type TB
body's positive-Y cover face. Install the uprights on edge with their rear faces
against the positive-Y faces of both `rail_fbl` and `rail_fbu`. In the default
model, the left upright occupies x = 12.225 to 13.725 inches and the right
upright x = 16.975 to 18.475 inches. Both start at z = 3/4 inch and end at
z = 14 1/4 inches, about 1 inch above the Type TB body. Their inner edges have a
nominal 1/4-inch clearance from the Type TB body.

Fasten each upright into each rail with one 4-inch exterior structural wood
screw, using pilot holes and the screw maker's installation guidance. Recess
the heads below the upright front faces so the plywood seats flat. Check
the screw locations against all installed electrical runs before drilling; the
screws must stop inside the wood rails. No guard fastener enters a conduit,
fitting, junction box, or the soil.

Fasten the plywood to the positive-Y ends of the uprights with four removable
1 1/2-inch #10 exterior truss-head screws per side, spaced along the height
and clear of the rail fasteners. The panel's modeled rear face is at
y = 13.6937 inches. Seal its faces and edges and smooth every cord-contact
edge; keep screw heads low and smooth.

Before fastening, trial-fit the wood and panel around the actual T, reducer,
branch, riser, and charger feed. Remove the panel and confirm the T cover can
be opened and removed between the uprights. Place and remove the actual
charging cord repeatedly. Its loops should rest outside the bumper, and cord
contact must not flex the plywood or uprights into any conduit or fitting. If
the actual clearance or stiffness is inadequate, adjust the cut and fit before
installation. The modeled flexible-cord path remains schematic and is not a
placement template for the real cord.

New model objects:

```text
power_guard_left_upright
power_guard_right_upright
power_guard_removable_panel
```

## Model coverage checklist

The 24 steps above assign all active construction objects exactly once.
Seven deferred tambour objects remain available in the model for future
reference and are hidden unless `show_deferred` is enabled in the completed
view.

| Category | Modeled count | Assigned steps |
| --- | ---: | --- |
| Lumber members | 27 | 2-9, 10, 15, 24 |
| Components and fittings | 29 | 3, 11-17, 20, 22-24 |
| Footings | 4 | 2 |
| Conduit runs | 6 | 1, 13-15 |
| Cable paths | 4 | 11, 17-19 |
| Composite siding render parts | 58 | 20 |
| Siding trim render parts | 14 | 21 |
| Deferred tambour reference objects | 7 | Completed view with `show_deferred` |

The `ground` object is visualization context rather than an installed enclosure
component, so it intentionally remains outside the numbered sequence.
