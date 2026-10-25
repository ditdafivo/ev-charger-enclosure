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
for future reference. The front guide uprights and their upper blocks are also
deferred; the permanent side receiver rails connect directly to the posts.

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
  - `build_step = 1..38`: show earlier objects normally, highlight objects from
    the selected step, and hide objects from later steps.
  - `build_step = 39`: show the completed model in its normal colors.
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
junction box installed in Step 12. The conduit boxes and fittings retain their
absolute modeled coordinates while their eventual mounting arrangement is
deferred.

Check both rails for level, square, and correct orientation before adding the
vertical member in Step 8.

New model objects:

```text
rail_fbu
rail_fbl
```

## 6. Add the side receiver rails (`upper-side-rails`)

Install the 15 7/8-inch `rail_lt` and `rail_rt` directly between the front and
back posts on their respective sides. Their lower and upper faces remain at
`z = 43 1/2` and `45` inches. Keep both wide faces horizontal.

Check both rails for level and aligned inside faces before installing `rail_ft`.
Their front post connections carry the header and charger loads; select the
connections for those loads and repeated cord-handling forces. Preserve the
full side-rail sections for the future tambour installation.

New model objects:

```text
rail_lt
rail_rt
```

## 7. Add the upper front cross rail (`upper-front-rail`)

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

## 8. Add the front center rail (`front-center-rail`)

Install `front_center_rail` between `rail_fbu` and `rail_ft`.

Check the rail for plumb. Its face orientation matters because it supports the
power junction box and EV charger.

New model objects:

```text
front_center_rail
```

## 9. Install the right center rail (`right-center-rail`)

Install `right_center_rail` vertically between `rail_rbu` and `rail_rt`, and
check that it is plumb. It supports the outlet backers installed next,
the Wi-Fi access point, and the low-voltage paths installed later.

New model objects:

```text
right_center_rail
```

## 10. Mount the EV charger with its cord and plug (`ev-charger-mounting`)

Mount the EV charger body and its inseparable flexible cord and plug on
`front_center_rail`, with the charger body shifted 2 inches downward from its
former modeled position while the cord holster remains fixed. Confirm and
record the physical location of its conduit
input; this installed position controls the field-fit conduit connection in
Step 11. Route the cord between the charger body, storage position, and
ground-level reach shown by the model.

Check the flexible cord for strain relief, minimum bend radius, storage
clearance, and absence of abrasion or pinch points. Repeat these checks after
making the power connection in Step 11.

New model objects:

```text
front_ev_charger_body
front_ev_charger_plug
front_ev_charger_cable
```

## 11. Connect the power junction to the EV charger (`ev-charger-power`)

Using the physical charger-input position recorded in Step 10, install the
Carlon E989NNJ nominal 4×4×2-inch junction box in place of the IPEX STB40S, with its removable cover
facing positive Y. Cut holes for a 1-inch top male fitting, a 3/4-inch back
male fitting toward the power junction, and the retained 1 1/4-inch bottom riser
male fitting. Clamp each entry with an exterior sealing washer and an interior
locknut; the box wall is not tapped. Keep the top fitting on the charger entry
axis and the bottom fitting on the existing riser axis.

The two-inch internal depth is centered at y = 12.5 inches on the riser.
The modeled cover and back add 0.155 and 0.160 inch, respectively, for a
2.315-inch overall depth. The narrower male stem enters the box; the larger
conduit socket stays below its bottom wall. The molded taper is approximated
with straight walls at the catalog minimum 3 5/8-inch opening.

The box center is z = 8.83 inches, with bottom and top at 6.83 and 10.83 inches.
Run the 3/4-inch branch from the back fitting to the planned rear-input position
of the 4×4×4-inch power junction box, leaving its end accessible for the final
connection after that box is mounted in Step 12. Run straight 1-inch conduit
from the top fitting to the charger; the old top reducer and box-adapter/coupling
pairs are removed. Fitting and clamp geometry is a planning envelope; lay out
hole sizes and seating depths from the selected hardware.

Check alignment at the riser, junction box, top fitting, and
charger entry. Route the unspliced #6 charger group through this conduit
according to the approved electrical design. Verify that the power path remains
clear of the cord-storage volume and adjacent framing. Check the flexible cord
for strain relief, minimum bend radius, storage clearance, and absence of
abrasion or pinch points. Verify the installed product markings and locally
required bend and fill calculations before construction.

New model objects:

```text
power_ev_charger_feed
power_ev_top_adapter
power_ev_top_adapter_sealing_washer
power_ev_top_adapter_locknut
power_ev_pull_box
power_ev_bottom_adapter
power_ev_bottom_adapter_sealing_washer
power_ev_bottom_adapter_locknut
power_ev_back_adapter
power_ev_back_adapter_sealing_washer
power_ev_back_adapter_locknut
power_pull_box_junction_feed
```

## 12. Preassemble and mount the power junction (`power-junction-assembly`)

Before mounting the Carlon E987N power junction box, fit its rear-facing
3/4-inch male input fitting for the shallow pull box and the right-side
FSW50Z-12.2-1 watertight UF cable connector for the receptacle. Prepare the
lighting connector port beside it; that connector is added in Step 20.
Cut the entry holes to suit the actual hardware and install its supplied
sealing and retention hardware according to the connector instructions.
The 3/4-inch conduit input retains its exterior sealing washer and interior
locknut. The light outlet is forward of
the receptacle outlet. Then mount the connected box on `front_center_rail`,
spanning x = 13 to 17 inches in the default model, and y = 3.1875 to 7.1875
inches. Its bottom face remains at the modeled elevation of approximately
z = 6.51 inches, supported along its lower edge by `rail_fbl`. Keep every
fitting axis aligned with its conduit or cable path and connect the rear fitting to the
3/4-inch branch left accessible in Step 11.

Check that the fittings and internal locknuts are clear of `front_center_rail`.
Keep the rear fitting aligned with the raised 3/4-inch feed from the shallow pull box.

The #6 charger group continues vertically through the 4×4×2-inch pull box and bypasses
the junction box. The #12 supply group branches through the 4×4×2-inch pull box's rear
port into the box, where its hot/hot/neutral conductors feed separate light and outlet
hot/neutral pairs and the equipment grounds are spliced. The lighting pair is
#14 UF-B and the outlet pair is #12 UF-B. The modeled junction-box calculation
is 17.50 in³ against an assumed 49.00 in³ marked capacity. Verify the
marking on the installed box and the locally required calculation before construction.

New model objects:

```text
power_junction_box
power_junction_input_adapter
power_junction_input_adapter_sealing_washer
power_junction_input_adapter_locknut
power_junction_outlet_uf_connector
```

## 13. Install the outlet box and backing (`outlet-rough-in`)

Install the two 6 11/16-inch 2x4 backers between `right_center_rail` and
`post_br`. Their modeled lower-face elevations are approximately 13 5/8 and
18 7/8 inches. Check that both backing faces are coplanar at x = 26.2625 inches;
this plane sets the rear of the 2.30-inch-deep FSE outlet box and its final
projection through the siding.

Immediately after securing the backing, mount the Carlon E980DFN FSE box.
Check that the box/cover mating plane will finish at x = 28.5625 inches, roughly
1/4 inch beyond the siding, and that the hub center is at x = 26.8285 inches.

New model objects:

```text
back_right_outlet_backer_lower
back_right_outlet_backer_upper
back_right_outlet
```

## 14. Install the outlet UF-B run (`outlet-conduit`)

Run continuous 12/2 UF-B with equipment ground from the front power junction
box to the outlet, following the former conduit path along `rail_rbl` and
up into the outlet's bottom hub. Use the same Commercial Electric
FSW50Z-12.2-1 watertight UF connector at both ends: one at the junction-box
exit and one at the outlet entry. Confirm the actual outlet hub and connector
interface before assembly.

The modeled cable retains the former conduit centerline at z = 7.17 inches
in the default enclosure, giving its 0.45-inch circular envelope about
0.195 inch of clearance above the rail. Retain the two 4-inch-radius sweeps. Support
the UF-B along the route and near both boxes, keeping loads off the connections.
Terminate the outlet branch under the approved wiring design.

New model objects:

```text
back_right_outlet_uf_connector
power_back_right_outlet_uf_b
```

## 15. Add the low-voltage termination (`low-voltage-termination`)

Mount the low-voltage junction box with its bottom adapter centered at the
upper 45-degree elbow outlet (nominally x = 10.657, y = 6.25, z = 9.912
inches). The male fitting meets that outlet directly; insert its thread through a cut
hole with an exterior sealing washer and an interior locknut. The box spans approximately
x = 8.657 to 12.657 and y = 3.1875 to 7.1875 inches, with its center at
z = 13.382 inches. Its back is flush with the front face of `rail_fbu`; the
bottom entry is offset toward the back at y = 6.25 inches to meet the elbow.
The power junction spans x = 13 to 17 inches. Future backing lumber may be
added but is not included. Field-locate the bottom opening from the as-built
elbow position. Then add the two cable glands and a weatherproof closure for the unused
street-light gland opening in the remaining bottom-panel area; reposition their nominal front-row layout as necessary to
preserve fitting clearances.

Keep each fitting center at least 3/4 inch from the panel sides. Confirm that
the riser remains plumb and clear of the 10-inch footing and that the existing
cables have room to leave the forward glands in negative Z before sweeping
toward the center framing. Route the blue Cat 6 feeds beside the 3/4-inch
riser, retaining the modeled clearance. Use
the modeled 0.625-inch upward turn beneath the glands, remain on the negative-Y
side of `rail_fbu` until above it. The former dark-brown street-light service cable is omitted.

New model objects:

```text
low_voltage_termination_box
low_voltage_input_adapter
low_voltage_input_adapter_sealing_washer
low_voltage_input_adapter_locknut
low_voltage_unused_port_closure
low_voltage_cable_gland_2
low_voltage_cable_gland_3
```

## 16. Mount and cable the Wi-Fi access point (`wifi-and-feed`)

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

## 17. Route the charger low-voltage feed (`charger-low-voltage-feed`)

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

## 18. Install the wood power-cord bumper (`power-cord-guard`)

Cut two 11 1/4-inch 2x4 uprights and one 7 1/2-by-11 1/4-inch panel from
1/4-inch exterior plywood. Rip the upright depth to approximately 2 7/8 inches;
the exact modeled depth places the panel's rear face 1/4 inch beyond the
pull box's positive-Y cover face. Install the uprights on edge with their rear faces
against the positive-Y faces of both `rail_fbl` and `rail_fbu`. In the default
model, the left upright occupies x = 11.6 to 13.1 inches and the right
upright x = 17.6 to 19.1 inches. Both start at z = 3/4 inch and end at
z = 12 inches, about 1 inch above the 4×4×2-inch pull box. Their inner edges have a
nominal 1/4-inch clearance from the 4×4×2-inch pull box.

Fasten each upright into each rail with one 4-inch exterior structural wood
screw, using pilot holes and the screw maker's installation guidance. Recess
the heads below the upright front faces so the plywood seats flat. Check
the screw locations against all installed electrical runs before drilling; the
screws must stop inside the wood rails. No guard fastener enters a conduit,
fitting, junction box, or the soil.

Fasten the plywood to the positive-Y ends of the uprights with four removable
1 1/2-inch #10 exterior truss-head screws per side, spaced along the height
and clear of the rail fasteners. The panel's modeled rear face is at
y = 13.5375 inches. Seal its faces and edges and smooth every cord-contact
edge; keep screw heads low and smooth.

Before fastening, trial-fit the wood and panel around the actual pull box,
threaded fittings, branch, riser, and charger feed. Remove the panel and confirm
the pull-box cover can
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

## 19. Add the address-number support (`address-number-support`)

Install the front vertical siding backing first, then fit 3/4-inch PT plywood across both upper front bays, from the half-height
line to the underside of the front brace. The posts and vertical siding backing
fill the interruptions. Set the exterior plywood faces 1/4 inch behind the
post/backing faces, leaving a gap behind the siding. These panels replace the
narrow 5/4x6 numeral support and allow the numeral position to be decided later.

Predrill angled entries from the accessible interior panel face into adjacent
lumber; use toe screws rather than surface-mounted cleats. Field-select screw
length and angle for sound timber engagement with contained tips. Do not drive
into plywood edges. The BOM allows four screws per panel; confirm the final
pattern on the fitted parts. Field-fit panel edges with a small installation gap.
Seal numeral penetrations and use rigid local spacers across the siding-to-panel
gap so tightening standoffs does not pull the siding inward. Confirm actual
numeral mounting screw engagement in 3/4-inch plywood before drilling.

New model objects:

```text
enclosure_siding_backing_front_1_1
enclosure_siding_infill_front_address_3
enclosure_siding_infill_front_address_4
```

## 20. Prepare the direct lighting cable route (`light-transition-box`)

The round Commercial Electric WRB550B transition box and WBC300G cover are
removed. The front power junction box, immediately ahead of the power ground
riser pull box, is now the lighting cable's only junction-box origin.

Keep the former conduit corridor from its right-side lighting port to the
inside of `post_fr`, including the 2 1/2-inch rising sweep and gentle offset.
Continue directly beneath `brace_fl_fr` to the light; no splice or intermediate
box is modeled on the post. Check the route and cable supports before siding.
Install the lighting UF connector in the front junction-box port prepared in
Step 12.

New model objects:

```text
power_junction_light_uf_connector
```

## 21. Route the UF-B lighting cable (`light-uf-b-cable`)

Run continuous 14/2 copper UF-B with equipment ground from the front power
junction box to the Brook light, retaining the existing **15 A maximum branch
protection** assumption. Make the supply-to-lighting-cable splice inside the
accessible front junction box. Use its Commercial Electric FSW50Z-12.2-1
watertight connector, the same interface formerly used at the round fixture
box and now used for the outlet branch. Keep the jacket intact through the
connector and tighten it according to its instructions.

Follow the former conduit path up `post_fr`, then sweep toward negative X
beneath `brace_fl_fr`. At the light centerline turn toward negative Y through
the siding into the lower fixture base, beneath the bracket. The nominal bore
is 1/2 inch diameter at x = 13.75 and z = 47.75 inches in the default enclosure.
Protect the penetration from abrasion and seal around the jacket independently
of the fixture perimeter. Secure UF-B along the route and near the box.

Both UF-B runs use a schematic 0.45-inch circular envelope; the lighting route
uses 2-inch bends below the brace. Actual UF-B is flat: confirm jacket dimensions,
bend requirements, penetration clearance, and connector fit before drilling.
The gray routes represent line-voltage UF-B. The former low-voltage street-light
service run is removed and its gland opening is closed.

New model objects:

```text
power_street_light_uf_b
```

## 22. Prepare siding backing and ventilation (`siding-preparation`)

Fit the remaining 3/4-inch PT wall infill within the framing depth with the
same 1/4-inch exterior setback as the upper front panels. Fit around permanent
lumber, siding backing and the outlet opening. Predrill toe screws into adjacent
lumber, with four per panel allowed. Tiny seams below 1/4 inch high use hardware
cloth rather than fragile plywood slivers. Scribe the lower panels to the same
3/4-inch grade clearance as the siding and close the remaining gap with mesh.
The rear service/future door opening stays open. This is a wall barrier, not a
sealed animal-proof enclosure while that opening remains open.

Use the shared `output/plywood_layout.svg` and `.json`: roof strips and infill
come from the same purchased sheet stock. Follow the numbered layout with
1/8-inch kerfs, then field-fit the blanks. No ceiling panel is installed or
included in future purchase quantities. Keep the entire overhead space open for
future tambour installation; wall infill can be unscrewed if future guides need
access. No floor panel is added.

Install the actual 1-inch wall backing segments with their existing specified
connections. Keep the space below the top diagonal clear for the prototype
tambour door; no local roof-support blocks or their toe screws are installed.
The plywood roof strips bear on the existing perimeter framing and diagonal.

Limit the extra outlet-side backing to the full heights of the courses cut by
the outlet. Keep the regular wall supports above and below this local backing.

Install the 3/4-inch PT exterior plywood roof strips in place of all roof shims
and intermediate roof backing. Rip with the panel strength axis along X.
Full courses use paired provisional 1.5-inch strips; the narrow closure uses
one backer. Shorten strip ends around gussets with 1/4-inch clearance and
anchor independently at generated framing-supported locations. Recess anchor
heads flush in plywood. Preserve open channels and joint outlets; do not cut
transversely through a strip for drainage. Field-treat cut edges as required.
The recessed panels leave only a 1/4-inch nominal wall cavity. Keep its drainage
paths and screened lower edges open; the former open-frame ventilation assumption
no longer applies.

Seat the two printed ASA/ABS gusset bearing covers before the roof boards:
cover 1 at back-left and cover 2 at front-right. Their bearing lands align with
the plywood tops; their relieved channels align with the roof joints. Check
that each sits without rocking and clears every gusset screw head. The roof
boards capture these floating covers; keep all fasteners in the specified wood
backing. See GUSSET_COVERS.md for printing and fit checks.

Dry-fit two US135 courses directly against representative lumber before cutting
production pieces. Verify the provisional 130 mm installed pitch, rear-profile
seating, inverted engagement, overlap material, head clearance and movement-hole retention. This is a custom
face-fastened adaptation; the manufacturer's US135 detail uses AW08 clips.
The model does not establish approval or connection load capacity.

New model objects:

```text
enclosure_siding_backing_left_1_1
enclosure_siding_backing_left_1_2
enclosure_siding_backing_left_1_3
enclosure_siding_backing_left_1_4
enclosure_siding_backing_right_1_1
enclosure_siding_backing_right_1_2
enclosure_siding_backing_right_1_3
enclosure_siding_backing_right_opening_1_1
enclosure_siding_infill_front_animal_1
enclosure_siding_infill_front_animal_2
enclosure_siding_infill_left_animal_5
enclosure_siding_infill_left_animal_6
enclosure_siding_infill_left_animal_7
enclosure_siding_infill_left_animal_8
enclosure_siding_infill_left_animal_9
enclosure_siding_infill_left_animal_10
enclosure_siding_infill_left_animal_11
enclosure_siding_infill_left_animal_12
enclosure_siding_infill_right_animal_13
enclosure_siding_infill_right_animal_14
enclosure_siding_infill_right_animal_15
enclosure_siding_infill_right_animal_16
enclosure_siding_infill_right_animal_17
enclosure_siding_infill_right_animal_18
enclosure_siding_infill_right_animal_19
enclosure_siding_infill_right_animal_20
enclosure_siding_infill_right_animal_21
enclosure_siding_infill_right_animal_22
enclosure_siding_infill_right_animal_23
enclosure_siding_infill_right_animal_24
enclosure_siding_infill_rear_animal_25
enclosure_siding_roof_strip_1_1
enclosure_siding_roof_strip_1_2
enclosure_siding_roof_strip_2_1
enclosure_siding_roof_strip_2_2
enclosure_siding_roof_strip_3_1
enclosure_siding_roof_strip_3_2
enclosure_siding_roof_strip_4_1
enclosure_siding_roof_strip_4_2
enclosure_siding_roof_strip_5_1
gusset_cover_1
gusset_cover_2
enclosure_siding_roof_strip_1_1_anchor_1
enclosure_siding_roof_strip_1_1_anchor_2
enclosure_siding_roof_strip_1_2_anchor_3
enclosure_siding_roof_strip_1_2_anchor_4
enclosure_siding_roof_strip_2_1_anchor_5
enclosure_siding_roof_strip_2_1_anchor_6
enclosure_siding_roof_strip_2_2_anchor_7
enclosure_siding_roof_strip_2_2_anchor_8
enclosure_siding_roof_strip_3_1_anchor_9
enclosure_siding_roof_strip_3_1_anchor_10
enclosure_siding_roof_strip_3_2_anchor_11
enclosure_siding_roof_strip_3_2_anchor_12
enclosure_siding_roof_strip_4_1_anchor_13
enclosure_siding_roof_strip_4_1_anchor_14
enclosure_siding_roof_strip_4_2_anchor_15
enclosure_siding_roof_strip_4_2_anchor_16
enclosure_siding_roof_strip_5_1_anchor_17
enclosure_siding_roof_strip_5_1_anchor_18
```

## 23. Install the hardware-cloth skirt (`siding-skirt`)

Install the 1/4-inch hardware cloth behind the future siding, overlap joints
2 inches, and staple it independently to framing. Extend it to grade while
keeping siding and US20 at least 3/4 inch above grade. Preserve drainage and
ventilation. The rear access opening remains open.

New model objects:

```text
enclosure_siding_mesh_front_1_wire_0
enclosure_siding_mesh_front_1_wire_1
enclosure_siding_mesh_front_1_wire_2
enclosure_siding_mesh_front_1_wire_3
enclosure_siding_mesh_front_1_wire_4
enclosure_siding_mesh_front_1_wire_5
enclosure_siding_mesh_front_1_wire_6
enclosure_siding_mesh_front_1_wire_7
enclosure_siding_mesh_front_1_wire_8
enclosure_siding_mesh_front_1_wire_9
enclosure_siding_mesh_front_1_wire_10
enclosure_siding_mesh_front_1_wire_11
enclosure_siding_mesh_front_1_wire_12
enclosure_siding_mesh_front_1_wire_13
enclosure_siding_mesh_front_1_wire_14
enclosure_siding_mesh_front_1_wire_15
enclosure_siding_mesh_front_1_wire_16
enclosure_siding_mesh_front_1_wire_17
enclosure_siding_mesh_front_1_wire_18
enclosure_siding_mesh_front_1_wire_19
enclosure_siding_mesh_front_1_wire_20
enclosure_siding_mesh_front_1_wire_21
enclosure_siding_mesh_front_1_wire_22
enclosure_siding_mesh_front_1_wire_23
enclosure_siding_mesh_front_1_wire_24
enclosure_siding_mesh_front_1_wire_25
enclosure_siding_mesh_front_1_wire_26
enclosure_siding_mesh_front_1_wire_27
enclosure_siding_mesh_front_1_wire_28
enclosure_siding_mesh_front_1_wire_29
enclosure_siding_mesh_front_1_wire_30
enclosure_siding_mesh_front_1_wire_31
enclosure_siding_mesh_front_1_wire_32
enclosure_siding_mesh_front_1_wire_33
enclosure_siding_mesh_front_1_wire_34
enclosure_siding_mesh_front_1_wire_35
enclosure_siding_mesh_front_1_wire_36
enclosure_siding_mesh_front_1_wire_37
enclosure_siding_mesh_front_1_wire_38
enclosure_siding_mesh_front_1_wire_39
enclosure_siding_mesh_front_1_wire_40
enclosure_siding_mesh_front_1_wire_41
enclosure_siding_mesh_front_1_wire_42
enclosure_siding_mesh_front_1_wire_43
enclosure_siding_mesh_front_1_wire_44
enclosure_siding_mesh_front_1_wire_45
enclosure_siding_mesh_front_1_wire_46
enclosure_siding_mesh_front_1_wire_47
enclosure_siding_mesh_front_1_wire_48
enclosure_siding_mesh_front_1_wire_49
enclosure_siding_mesh_front_1_wire_50
enclosure_siding_mesh_front_1_wire_51
enclosure_siding_mesh_front_1_wire_52
enclosure_siding_mesh_front_1_wire_53
enclosure_siding_mesh_front_1_wire_54
enclosure_siding_mesh_front_1_wire_55
enclosure_siding_mesh_front_1_wire_56
enclosure_siding_mesh_front_1_wire_57
enclosure_siding_mesh_front_1_wire_58
enclosure_siding_mesh_front_1_wire_59
enclosure_siding_mesh_front_1_wire_60
enclosure_siding_mesh_front_1_wire_61
enclosure_siding_mesh_front_1_wire_62
enclosure_siding_mesh_front_1_wire_63
enclosure_siding_mesh_front_1_wire_64
enclosure_siding_mesh_front_1_wire_65
enclosure_siding_mesh_front_1_wire_66
enclosure_siding_mesh_front_1_wire_67
enclosure_siding_mesh_front_1_wire_68
enclosure_siding_mesh_front_1_wire_69
enclosure_siding_mesh_front_1_wire_70
enclosure_siding_mesh_front_1_wire_71
enclosure_siding_mesh_front_1_wire_72
enclosure_siding_mesh_front_1_wire_73
enclosure_siding_mesh_front_1_wire_74
enclosure_siding_mesh_front_1_wire_75
enclosure_siding_mesh_front_1_wire_76
enclosure_siding_mesh_front_1_wire_77
enclosure_siding_mesh_front_1_wire_78
enclosure_siding_mesh_front_1_wire_79
enclosure_siding_mesh_front_1_wire_80
enclosure_siding_mesh_front_1_wire_81
enclosure_siding_mesh_front_1_wire_82
enclosure_siding_mesh_front_1_wire_83
enclosure_siding_mesh_front_1_wire_84
enclosure_siding_mesh_front_1_wire_85
enclosure_siding_mesh_front_1_wire_86
enclosure_siding_mesh_front_1_wire_87
enclosure_siding_mesh_front_1_wire_88
enclosure_siding_mesh_front_1_wire_89
enclosure_siding_mesh_front_1_wire_90
enclosure_siding_mesh_front_1_wire_91
enclosure_siding_mesh_front_1_wire_92
enclosure_siding_mesh_front_1_wire_93
enclosure_siding_mesh_front_1_wire_94
enclosure_siding_mesh_front_1_wire_95
enclosure_siding_mesh_front_1_wire_96
enclosure_siding_mesh_front_1_wire_97
enclosure_siding_mesh_front_1_wire_98
enclosure_siding_mesh_front_1_wire_99
enclosure_siding_mesh_front_1_wire_100
enclosure_siding_mesh_front_1_wire_101
enclosure_siding_mesh_front_1_wire_102
enclosure_siding_mesh_front_1_wire_103
enclosure_siding_mesh_front_1_wire_104
enclosure_siding_mesh_front_1_wire_105
enclosure_siding_mesh_front_1_wire_106
enclosure_siding_mesh_front_1_wire_107
enclosure_siding_mesh_front_1_wire_108
enclosure_siding_mesh_front_1_wire_109
enclosure_siding_mesh_front_1_horizontal_0
enclosure_siding_mesh_front_1_horizontal_1
enclosure_siding_mesh_front_1_horizontal_2
enclosure_siding_mesh_front_1_horizontal_3
enclosure_siding_mesh_front_1_horizontal_4
enclosure_siding_mesh_front_1_horizontal_5
enclosure_siding_mesh_front_1_horizontal_6
enclosure_siding_mesh_front_1_horizontal_7
enclosure_siding_mesh_left_1_wire_0
enclosure_siding_mesh_left_1_wire_1
enclosure_siding_mesh_left_1_wire_2
enclosure_siding_mesh_left_1_wire_3
enclosure_siding_mesh_left_1_wire_4
enclosure_siding_mesh_left_1_wire_5
enclosure_siding_mesh_left_1_wire_6
enclosure_siding_mesh_left_1_wire_7
enclosure_siding_mesh_left_1_wire_8
enclosure_siding_mesh_left_1_wire_9
enclosure_siding_mesh_left_1_wire_10
enclosure_siding_mesh_left_1_wire_11
enclosure_siding_mesh_left_1_wire_12
enclosure_siding_mesh_left_1_wire_13
enclosure_siding_mesh_left_1_wire_14
enclosure_siding_mesh_left_1_wire_15
enclosure_siding_mesh_left_1_wire_16
enclosure_siding_mesh_left_1_wire_17
enclosure_siding_mesh_left_1_wire_18
enclosure_siding_mesh_left_1_wire_19
enclosure_siding_mesh_left_1_wire_20
enclosure_siding_mesh_left_1_wire_21
enclosure_siding_mesh_left_1_wire_22
enclosure_siding_mesh_left_1_wire_23
enclosure_siding_mesh_left_1_wire_24
enclosure_siding_mesh_left_1_wire_25
enclosure_siding_mesh_left_1_wire_26
enclosure_siding_mesh_left_1_wire_27
enclosure_siding_mesh_left_1_wire_28
enclosure_siding_mesh_left_1_wire_29
enclosure_siding_mesh_left_1_wire_30
enclosure_siding_mesh_left_1_wire_31
enclosure_siding_mesh_left_1_wire_32
enclosure_siding_mesh_left_1_wire_33
enclosure_siding_mesh_left_1_wire_34
enclosure_siding_mesh_left_1_wire_35
enclosure_siding_mesh_left_1_wire_36
enclosure_siding_mesh_left_1_wire_37
enclosure_siding_mesh_left_1_wire_38
enclosure_siding_mesh_left_1_wire_39
enclosure_siding_mesh_left_1_wire_40
enclosure_siding_mesh_left_1_wire_41
enclosure_siding_mesh_left_1_wire_42
enclosure_siding_mesh_left_1_wire_43
enclosure_siding_mesh_left_1_wire_44
enclosure_siding_mesh_left_1_wire_45
enclosure_siding_mesh_left_1_wire_46
enclosure_siding_mesh_left_1_wire_47
enclosure_siding_mesh_left_1_wire_48
enclosure_siding_mesh_left_1_wire_49
enclosure_siding_mesh_left_1_wire_50
enclosure_siding_mesh_left_1_wire_51
enclosure_siding_mesh_left_1_wire_52
enclosure_siding_mesh_left_1_wire_53
enclosure_siding_mesh_left_1_wire_54
enclosure_siding_mesh_left_1_wire_55
enclosure_siding_mesh_left_1_wire_56
enclosure_siding_mesh_left_1_wire_57
enclosure_siding_mesh_left_1_wire_58
enclosure_siding_mesh_left_1_wire_59
enclosure_siding_mesh_left_1_wire_60
enclosure_siding_mesh_left_1_wire_61
enclosure_siding_mesh_left_1_wire_62
enclosure_siding_mesh_left_1_wire_63
enclosure_siding_mesh_left_1_wire_64
enclosure_siding_mesh_left_1_wire_65
enclosure_siding_mesh_left_1_wire_66
enclosure_siding_mesh_left_1_wire_67
enclosure_siding_mesh_left_1_wire_68
enclosure_siding_mesh_left_1_wire_69
enclosure_siding_mesh_left_1_wire_70
enclosure_siding_mesh_left_1_wire_71
enclosure_siding_mesh_left_1_wire_72
enclosure_siding_mesh_left_1_wire_73
enclosure_siding_mesh_left_1_wire_74
enclosure_siding_mesh_left_1_wire_75
enclosure_siding_mesh_left_1_wire_76
enclosure_siding_mesh_left_1_wire_77
enclosure_siding_mesh_left_1_wire_78
enclosure_siding_mesh_left_1_wire_79
enclosure_siding_mesh_left_1_wire_80
enclosure_siding_mesh_left_1_wire_81
enclosure_siding_mesh_left_1_wire_82
enclosure_siding_mesh_left_1_wire_83
enclosure_siding_mesh_left_1_wire_84
enclosure_siding_mesh_left_1_wire_85
enclosure_siding_mesh_left_1_wire_86
enclosure_siding_mesh_left_1_wire_87
enclosure_siding_mesh_left_1_wire_88
enclosure_siding_mesh_left_1_wire_89
enclosure_siding_mesh_left_1_wire_90
enclosure_siding_mesh_left_1_wire_91
enclosure_siding_mesh_left_1_horizontal_0
enclosure_siding_mesh_left_1_horizontal_1
enclosure_siding_mesh_left_1_horizontal_2
enclosure_siding_mesh_left_1_horizontal_3
enclosure_siding_mesh_left_1_horizontal_4
enclosure_siding_mesh_left_1_horizontal_5
enclosure_siding_mesh_left_1_horizontal_6
enclosure_siding_mesh_left_1_horizontal_7
enclosure_siding_mesh_right_1_wire_0
enclosure_siding_mesh_right_1_wire_1
enclosure_siding_mesh_right_1_wire_2
enclosure_siding_mesh_right_1_wire_3
enclosure_siding_mesh_right_1_wire_4
enclosure_siding_mesh_right_1_wire_5
enclosure_siding_mesh_right_1_wire_6
enclosure_siding_mesh_right_1_wire_7
enclosure_siding_mesh_right_1_wire_8
enclosure_siding_mesh_right_1_wire_9
enclosure_siding_mesh_right_1_wire_10
enclosure_siding_mesh_right_1_wire_11
enclosure_siding_mesh_right_1_wire_12
enclosure_siding_mesh_right_1_wire_13
enclosure_siding_mesh_right_1_wire_14
enclosure_siding_mesh_right_1_wire_15
enclosure_siding_mesh_right_1_wire_16
enclosure_siding_mesh_right_1_wire_17
enclosure_siding_mesh_right_1_wire_18
enclosure_siding_mesh_right_1_wire_19
enclosure_siding_mesh_right_1_wire_20
enclosure_siding_mesh_right_1_wire_21
enclosure_siding_mesh_right_1_wire_22
enclosure_siding_mesh_right_1_wire_23
enclosure_siding_mesh_right_1_wire_24
enclosure_siding_mesh_right_1_wire_25
enclosure_siding_mesh_right_1_wire_26
enclosure_siding_mesh_right_1_wire_27
enclosure_siding_mesh_right_1_wire_28
enclosure_siding_mesh_right_1_wire_29
enclosure_siding_mesh_right_1_wire_30
enclosure_siding_mesh_right_1_wire_31
enclosure_siding_mesh_right_1_wire_32
enclosure_siding_mesh_right_1_wire_33
enclosure_siding_mesh_right_1_wire_34
enclosure_siding_mesh_right_1_wire_35
enclosure_siding_mesh_right_1_wire_36
enclosure_siding_mesh_right_1_wire_37
enclosure_siding_mesh_right_1_wire_38
enclosure_siding_mesh_right_1_wire_39
enclosure_siding_mesh_right_1_wire_40
enclosure_siding_mesh_right_1_wire_41
enclosure_siding_mesh_right_1_wire_42
enclosure_siding_mesh_right_1_wire_43
enclosure_siding_mesh_right_1_wire_44
enclosure_siding_mesh_right_1_wire_45
enclosure_siding_mesh_right_1_wire_46
enclosure_siding_mesh_right_1_wire_47
enclosure_siding_mesh_right_1_wire_48
enclosure_siding_mesh_right_1_wire_49
enclosure_siding_mesh_right_1_wire_50
enclosure_siding_mesh_right_1_wire_51
enclosure_siding_mesh_right_1_wire_52
enclosure_siding_mesh_right_1_wire_53
enclosure_siding_mesh_right_1_wire_54
enclosure_siding_mesh_right_1_wire_55
enclosure_siding_mesh_right_1_wire_56
enclosure_siding_mesh_right_1_wire_57
enclosure_siding_mesh_right_1_wire_58
enclosure_siding_mesh_right_1_wire_59
enclosure_siding_mesh_right_1_wire_60
enclosure_siding_mesh_right_1_wire_61
enclosure_siding_mesh_right_1_wire_62
enclosure_siding_mesh_right_1_wire_63
enclosure_siding_mesh_right_1_wire_64
enclosure_siding_mesh_right_1_wire_65
enclosure_siding_mesh_right_1_wire_66
enclosure_siding_mesh_right_1_wire_67
enclosure_siding_mesh_right_1_wire_68
enclosure_siding_mesh_right_1_wire_69
enclosure_siding_mesh_right_1_wire_70
enclosure_siding_mesh_right_1_wire_71
enclosure_siding_mesh_right_1_wire_72
enclosure_siding_mesh_right_1_wire_73
enclosure_siding_mesh_right_1_wire_74
enclosure_siding_mesh_right_1_wire_75
enclosure_siding_mesh_right_1_wire_76
enclosure_siding_mesh_right_1_wire_77
enclosure_siding_mesh_right_1_wire_78
enclosure_siding_mesh_right_1_wire_79
enclosure_siding_mesh_right_1_wire_80
enclosure_siding_mesh_right_1_wire_81
enclosure_siding_mesh_right_1_wire_82
enclosure_siding_mesh_right_1_wire_83
enclosure_siding_mesh_right_1_wire_84
enclosure_siding_mesh_right_1_wire_85
enclosure_siding_mesh_right_1_wire_86
enclosure_siding_mesh_right_1_wire_87
enclosure_siding_mesh_right_1_wire_88
enclosure_siding_mesh_right_1_wire_89
enclosure_siding_mesh_right_1_wire_90
enclosure_siding_mesh_right_1_wire_91
enclosure_siding_mesh_right_1_horizontal_0
enclosure_siding_mesh_right_1_horizontal_1
enclosure_siding_mesh_right_1_horizontal_2
enclosure_siding_mesh_right_1_horizontal_3
enclosure_siding_mesh_right_1_horizontal_4
enclosure_siding_mesh_right_1_horizontal_5
enclosure_siding_mesh_right_1_horizontal_6
enclosure_siding_mesh_right_1_horizontal_7
enclosure_siding_mesh_rear_1_wire_0
enclosure_siding_mesh_rear_1_wire_1
enclosure_siding_mesh_rear_1_wire_2
enclosure_siding_mesh_rear_1_wire_3
enclosure_siding_mesh_rear_1_wire_4
enclosure_siding_mesh_rear_1_wire_5
enclosure_siding_mesh_rear_1_wire_6
enclosure_siding_mesh_rear_1_wire_7
enclosure_siding_mesh_rear_1_wire_8
enclosure_siding_mesh_rear_1_wire_9
enclosure_siding_mesh_rear_1_wire_10
enclosure_siding_mesh_rear_1_wire_11
enclosure_siding_mesh_rear_1_wire_12
enclosure_siding_mesh_rear_1_wire_13
enclosure_siding_mesh_rear_1_wire_14
enclosure_siding_mesh_rear_1_horizontal_0
enclosure_siding_mesh_rear_1_horizontal_1
enclosure_siding_mesh_rear_1_horizontal_2
enclosure_siding_mesh_rear_1_horizontal_3
enclosure_siding_mesh_rear_1_horizontal_4
enclosure_siding_mesh_rear_1_horizontal_5
enclosure_siding_mesh_rear_1_horizontal_6
enclosure_siding_mesh_rear_1_horizontal_7
enclosure_siding_mesh_rear_2_wire_0
enclosure_siding_mesh_rear_2_wire_1
enclosure_siding_mesh_rear_2_wire_2
enclosure_siding_mesh_rear_2_wire_3
enclosure_siding_mesh_rear_2_wire_4
enclosure_siding_mesh_rear_2_wire_5
enclosure_siding_mesh_rear_2_wire_6
enclosure_siding_mesh_rear_2_wire_7
enclosure_siding_mesh_rear_2_wire_8
enclosure_siding_mesh_rear_2_wire_9
enclosure_siding_mesh_rear_2_wire_10
enclosure_siding_mesh_rear_2_wire_11
enclosure_siding_mesh_rear_2_wire_12
enclosure_siding_mesh_rear_2_wire_13
enclosure_siding_mesh_rear_2_wire_14
enclosure_siding_mesh_rear_2_horizontal_0
enclosure_siding_mesh_rear_2_horizontal_1
enclosure_siding_mesh_rear_2_horizontal_2
enclosure_siding_mesh_rear_2_horizontal_3
enclosure_siding_mesh_rear_2_horizontal_4
enclosure_siding_mesh_rear_2_horizontal_5
enclosure_siding_mesh_rear_2_horizontal_6
enclosure_siding_mesh_rear_2_horizontal_7
```

## 24. Install the US135 roof cover (`siding-roof`)

Install the roof cover before the wall siding so the open sides preserve
access to the roof support strips and fasteners. Leave roof-edge trim until
after the wall siding is installed.

Run boards along X and progress across Y. Seat boards directly on the
3/4-inch plywood support strips. Use provisional #8 x 1-1/8-inch stainless
retaining-head screws into plywood only, nominally 5/8-inch penetration.
Verify production profile thickness, actual plywood thickness, usable thread
engagement and contained tips before installation. Face-fasten along the strip
centerlines at generated locations, no more than 10 inches apart. Use one fixed point per
physical board and sliding holes elsewhere, including the ripped final board.
Horizontal roof trim uses 2-1/2-inch screws through the increased stack, with
framing landing and movement checked separately. US20 trim carries no roof
weight. This level cover may leak; snow, uplift,
ponding and exposed-roof capacity remain unverified.

New model objects:

```text
enclosure_siding_top_1
enclosure_siding_top_2
enclosure_siding_top_3
enclosure_siding_top_4
enclosure_siding_top_5
enclosure_siding_top_1_face_screw_134
enclosure_siding_top_1_face_screw_135
enclosure_siding_top_1_face_screw_136
enclosure_siding_top_1_face_screw_137
enclosure_siding_top_1_face_screw_138
enclosure_siding_top_1_face_screw_139
enclosure_siding_top_1_face_screw_140
enclosure_siding_top_1_face_screw_141
enclosure_siding_top_2_face_screw_142
enclosure_siding_top_2_face_screw_143
enclosure_siding_top_2_face_screw_144
enclosure_siding_top_2_face_screw_145
enclosure_siding_top_2_face_screw_146
enclosure_siding_top_2_face_screw_147
enclosure_siding_top_2_face_screw_148
enclosure_siding_top_2_face_screw_149
enclosure_siding_top_2_face_screw_150
enclosure_siding_top_3_face_screw_151
enclosure_siding_top_3_face_screw_152
enclosure_siding_top_3_face_screw_153
enclosure_siding_top_3_face_screw_154
enclosure_siding_top_3_face_screw_155
enclosure_siding_top_3_face_screw_156
enclosure_siding_top_3_face_screw_157
enclosure_siding_top_3_face_screw_158
enclosure_siding_top_3_face_screw_159
enclosure_siding_top_3_face_screw_160
enclosure_siding_top_4_face_screw_161
enclosure_siding_top_4_face_screw_162
enclosure_siding_top_4_face_screw_163
enclosure_siding_top_4_face_screw_164
enclosure_siding_top_4_face_screw_165
enclosure_siding_top_4_face_screw_166
enclosure_siding_top_4_face_screw_167
enclosure_siding_top_4_face_screw_168
enclosure_siding_top_5_face_screw_169
enclosure_siding_top_5_face_screw_170
enclosure_siding_top_5_face_screw_171
enclosure_siding_top_5_face_screw_172
```

## 25. Wrap the front, left and right with wall siding course 1 (`siding-course-1`)

Hold the full-height top boards level with padded framing-mounted supports.
Seat the boards directly against the lumber and face-fasten at the generated
supported locations. Use one fixed point per physical board; predrill all other
holes for movement and leave their heads free to slide. Install profiles upside
down, finished face outward. One recessed lower-overlap row is concealed by the
next course. Schematic heads require a production-profile clearance check.
Keep the ends clear for the applied US20 corner covers installed in step 36.
Remove temporary supports after permanent fasteners retain each board.

New model objects:

```text
enclosure_siding_front_1
enclosure_siding_left_1
enclosure_siding_right_1
enclosure_siding_front_1_face_screw_1
enclosure_siding_front_1_face_screw_2
enclosure_siding_front_1_face_screw_3
enclosure_siding_left_1_face_screw_4
enclosure_siding_left_1_face_screw_5
enclosure_siding_left_1_face_screw_6
enclosure_siding_right_1_face_screw_7
enclosure_siding_right_1_face_screw_8
enclosure_siding_right_1_face_screw_9
```

## 26. Install the notched rear top siding board (`siding-course-1-rear`)

Cut one physical rear board with an access notch; the three displayed solids
are portions of this same board. Support it temporarily and face-fasten into
the rear posts and header. Its one fixed point is the supported header screw
near the midpoint. All wing and other header connections must permit movement.
Keep clearance around the opening and beneath the future US20 covers.

New model objects:

```text
enclosure_siding_rear_1_piece_1
enclosure_siding_rear_1_piece_2
enclosure_siding_rear_1_piece_3
enclosure_siding_rear_1_face_screw_10
enclosure_siding_rear_1_face_screw_11
enclosure_siding_rear_1_face_screw_12
```

## 27. Install wall siding course 2, top down (`siding-course-2`)

Install wall course 2, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_2
enclosure_siding_left_2
enclosure_siding_right_2
enclosure_siding_rear_2_1
enclosure_siding_rear_2_2
enclosure_siding_front_2_face_screw_13
enclosure_siding_front_2_face_screw_14
enclosure_siding_front_2_face_screw_15
enclosure_siding_left_2_face_screw_16
enclosure_siding_left_2_face_screw_17
enclosure_siding_left_2_face_screw_18
enclosure_siding_right_2_face_screw_19
enclosure_siding_right_2_face_screw_20
enclosure_siding_right_2_face_screw_21
enclosure_siding_rear_2_1_face_screw_22
enclosure_siding_rear_2_1_face_screw_23
enclosure_siding_rear_2_2_face_screw_24
enclosure_siding_rear_2_2_face_screw_25
```

## 28. Install wall siding course 3, top down (`siding-course-3`)

Install wall course 3, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_3
enclosure_siding_left_3
enclosure_siding_right_3
enclosure_siding_rear_3_1
enclosure_siding_rear_3_2
enclosure_siding_front_3_face_screw_26
enclosure_siding_front_3_face_screw_27
enclosure_siding_front_3_face_screw_28
enclosure_siding_left_3_face_screw_29
enclosure_siding_left_3_face_screw_30
enclosure_siding_left_3_face_screw_31
enclosure_siding_right_3_face_screw_32
enclosure_siding_right_3_face_screw_33
enclosure_siding_right_3_face_screw_34
enclosure_siding_rear_3_1_face_screw_35
enclosure_siding_rear_3_1_face_screw_36
enclosure_siding_rear_3_2_face_screw_37
enclosure_siding_rear_3_2_face_screw_38
```

## 29. Install wall siding course 4, top down (`siding-course-4`)

Install wall course 4, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_4
enclosure_siding_left_4
enclosure_siding_right_4
enclosure_siding_rear_4_1
enclosure_siding_rear_4_2
enclosure_siding_front_4_face_screw_39
enclosure_siding_front_4_face_screw_40
enclosure_siding_front_4_face_screw_41
enclosure_siding_left_4_face_screw_42
enclosure_siding_left_4_face_screw_43
enclosure_siding_left_4_face_screw_44
enclosure_siding_right_4_face_screw_45
enclosure_siding_right_4_face_screw_46
enclosure_siding_right_4_face_screw_47
enclosure_siding_rear_4_1_face_screw_48
enclosure_siding_rear_4_1_face_screw_49
enclosure_siding_rear_4_2_face_screw_50
enclosure_siding_rear_4_2_face_screw_51
```

## 30. Install wall siding course 5, top down (`siding-course-5`)

Install wall course 5, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_5
enclosure_siding_left_5
enclosure_siding_right_5
enclosure_siding_rear_5_1
enclosure_siding_rear_5_2
enclosure_siding_front_5_face_screw_52
enclosure_siding_front_5_face_screw_53
enclosure_siding_front_5_face_screw_54
enclosure_siding_left_5_face_screw_55
enclosure_siding_left_5_face_screw_56
enclosure_siding_left_5_face_screw_57
enclosure_siding_right_5_face_screw_58
enclosure_siding_right_5_face_screw_59
enclosure_siding_right_5_face_screw_60
enclosure_siding_rear_5_1_face_screw_61
enclosure_siding_rear_5_1_face_screw_62
enclosure_siding_rear_5_2_face_screw_63
enclosure_siding_rear_5_2_face_screw_64
```

## 31. Install wall siding course 6, top down (`siding-course-6`)

Install wall course 6, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_6
enclosure_siding_left_6
enclosure_siding_right_6_piece_1
enclosure_siding_right_6_piece_2
enclosure_siding_right_6_piece_3
enclosure_siding_rear_6_1
enclosure_siding_rear_6_2
enclosure_siding_front_6_face_screw_65
enclosure_siding_front_6_face_screw_66
enclosure_siding_front_6_face_screw_67
enclosure_siding_left_6_face_screw_68
enclosure_siding_left_6_face_screw_69
enclosure_siding_left_6_face_screw_70
enclosure_siding_right_6_face_screw_71
enclosure_siding_right_6_face_screw_72
enclosure_siding_right_6_face_screw_73
enclosure_siding_right_6_face_screw_74
enclosure_siding_right_6_face_screw_75
enclosure_siding_rear_6_1_face_screw_76
enclosure_siding_rear_6_1_face_screw_77
enclosure_siding_rear_6_2_face_screw_78
enclosure_siding_rear_6_2_face_screw_79
```

## 32. Install wall siding course 7, top down (`siding-course-7`)

Install wall course 7, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_7
enclosure_siding_left_7
enclosure_siding_right_7_piece_1
enclosure_siding_right_7_piece_2
enclosure_siding_right_7_piece_3
enclosure_siding_rear_7_1
enclosure_siding_rear_7_2
enclosure_siding_front_7_face_screw_80
enclosure_siding_front_7_face_screw_81
enclosure_siding_front_7_face_screw_82
enclosure_siding_left_7_face_screw_83
enclosure_siding_left_7_face_screw_84
enclosure_siding_left_7_face_screw_85
enclosure_siding_right_7_face_screw_86
enclosure_siding_right_7_face_screw_87
enclosure_siding_right_7_face_screw_88
enclosure_siding_right_7_face_screw_89
enclosure_siding_right_7_face_screw_90
enclosure_siding_rear_7_1_face_screw_91
enclosure_siding_rear_7_1_face_screw_92
enclosure_siding_rear_7_2_face_screw_93
enclosure_siding_rear_7_2_face_screw_94
```

## 33. Install wall siding course 8, top down (`siding-course-8`)

Install wall course 8, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_8
enclosure_siding_left_8
enclosure_siding_right_8
enclosure_siding_rear_8_1
enclosure_siding_rear_8_2
enclosure_siding_front_8_face_screw_95
enclosure_siding_front_8_face_screw_96
enclosure_siding_front_8_face_screw_97
enclosure_siding_left_8_face_screw_98
enclosure_siding_left_8_face_screw_99
enclosure_siding_left_8_face_screw_100
enclosure_siding_right_8_face_screw_101
enclosure_siding_right_8_face_screw_102
enclosure_siding_right_8_face_screw_103
enclosure_siding_rear_8_1_face_screw_104
enclosure_siding_rear_8_1_face_screw_105
enclosure_siding_rear_8_2_face_screw_106
enclosure_siding_rear_8_2_face_screw_107
```

## 34. Install wall siding course 9, top down (`siding-course-9`)

Install wall course 9, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

New model objects:

```text
enclosure_siding_front_9
enclosure_siding_left_9
enclosure_siding_right_9
enclosure_siding_rear_9_1
enclosure_siding_rear_9_2
enclosure_siding_front_9_face_screw_108
enclosure_siding_front_9_face_screw_109
enclosure_siding_front_9_face_screw_110
enclosure_siding_left_9_face_screw_111
enclosure_siding_left_9_face_screw_112
enclosure_siding_left_9_face_screw_113
enclosure_siding_right_9_face_screw_114
enclosure_siding_right_9_face_screw_115
enclosure_siding_right_9_face_screw_116
enclosure_siding_rear_9_1_face_screw_117
enclosure_siding_rear_9_1_face_screw_118
enclosure_siding_rear_9_2_face_screw_119
enclosure_siding_rear_9_2_face_screw_120
```

## 35. Install wall siding course 10, top down (`siding-course-10`)

Install wall course 10, proceeding downward. Engage it with the course
above, support it temporarily, and face-fasten directly into lumber at the
generated locations in the inverted lower overlap, concealed by the next course.
Use supported local exceptions at cutouts and terminations; prefer US20 coverage.
Fix each physical board once; keep all other holes oversized and free to slide.
Each separate rear wing has its own fixed point. Keep screws clear of openings
and keep the board ends clear beneath the future US20 covers.

Scribe the final course to actual grade plus 3/4 inch, checking intervening
high spots. Narrow remainders use a centered screw row. Preserve movement
clearance without lowering the courses above.

New model objects:

```text
enclosure_siding_front_10
enclosure_siding_left_10
enclosure_siding_right_10
enclosure_siding_rear_10_1
enclosure_siding_rear_10_2
enclosure_siding_front_10_face_screw_121
enclosure_siding_front_10_face_screw_122
enclosure_siding_front_10_face_screw_123
enclosure_siding_left_10_face_screw_124
enclosure_siding_left_10_face_screw_125
enclosure_siding_left_10_face_screw_126
enclosure_siding_right_10_face_screw_127
enclosure_siding_right_10_face_screw_128
enclosure_siding_right_10_face_screw_129
enclosure_siding_rear_10_1_face_screw_130
enclosure_siding_rear_10_1_face_screw_131
enclosure_siding_rear_10_2_face_screw_132
enclosure_siding_rear_10_2_face_screw_133
```

## 36. Fit US20 corners, rear-access and roof-edge trim (`siding-trim`)

Apply US20 L-angle at all four outside wall corners and both rear jambs and
the rear header. Its face covers the board ends; the opening returns face
inward. Jambs stop below the header return with movement clearance. Maintain
3/4-inch grade clearance at each trim's location. Verify actual overlap and
backing before drilling, since US20 is narrower than the former US46.

Stop the vertical corner covers beneath the roof-edge US20 faces with a
movement gap. Fit roof-edge angles with 45-degree plan miters. Relieve the
front vertical leg around the Brook body: 6 1/4 inches wide, to 1/8 inch above
its modeled top. Field-check the fixture; fasten on either side into the brace.
The four generated siding_corner_*.scad files show these custom junctions.

Use #8 x 2-inch stainless trim screws where the stack is US20 plus siding into
lumber; verify actual penetration. Use one fixed point per trim and sliding
holes elsewhere. Screws passing through siding must also allow that board to
move independently. Do not clamp the angles tightly against multiple courses.
Leave movement and drainage gaps open. The 1/8-inch modeled allowance assumes
installation at 32 F or warmer and pieces no longer than 8 feet; check the
manufacturer's temperature/length table against field conditions.

New model objects:

```text
enclosure_siding_US20_corner_fl_1
enclosure_siding_US20_corner_fl_2
enclosure_siding_US20_corner_fr_1
enclosure_siding_US20_corner_fr_2
enclosure_siding_US20_corner_bl_1
enclosure_siding_US20_corner_bl_2
enclosure_siding_US20_corner_br_1
enclosure_siding_US20_corner_br_2
enclosure_siding_US20_front_top
enclosure_siding_US20_front_face
enclosure_siding_US20_rear_top
enclosure_siding_US20_rear_face
enclosure_siding_US20_left_top
enclosure_siding_US20_left_face
enclosure_siding_US20_right_top
enclosure_siding_US20_right_face
enclosure_siding_US20_opening_left_1
enclosure_siding_US20_opening_left_2
enclosure_siding_US20_opening_right_1
enclosure_siding_US20_opening_right_2
enclosure_siding_US20_opening_header_face
enclosure_siding_US20_opening_header_return
```

## 37. Finish the Brook and address numbers (`street-light-finish`)

Install the MOD Lighting Brook MOD119, 16-inch black, 3000K variant
45573961023747. Published dimensions are 16 inches long, 2.4 inches high,
and 3.9 inches projecting from the wall. Center the supplied bracket at
x = 13.75 and z = 48.625 inches in the default enclosure: 1/2 inch above the
underside of `brace_fl_fr`. Set the bracket against the siding exterior at
y = -0.5 inch and fasten through the siding into the low part of the brace.
The cable enters the lower base below the bracket, through the small bore
specified in step 21. There is no large box opening in the siding.

Bracket dimensions and fixture subdivisions are visual approximations.
Field-locate screws and the penetration from the actual bracket and fixture;
confirm screw penetration, edge distances, cable clearance, and fixture removal
access. Connect with power off, bond the fixture using its ground provision,
and secure it using its retaining screws. Follow the guide's caulking detail:
seal the top and sides against the siding and leave the bottom open to drain.
The open-backed termination arrangement is the selected physical installation
concept; compliance with the fixture's certification has not been established.

Replace the plaque with four separate silver numerals **4754**, each 5 inches
high and 1 inch deep, modeled in Liberation Sans Regular. The centered
arrangement is 12 inches wide: four 2 1/4-inch digit envelopes with 1-inch
spacing. Keep a 3-inch vertical gap below the Brook. Default numeral bounds
span x = 7.75 to 19.75, z = 39.425 to 44.425 inches. Each digit has two
1-inch standoffs, leaving 1 inch from siding to its back; its front is at
y = -2.5 inches. Fasten the standoffs through the siding into the actual
1-inch-thick support installed in step 19. Standoff diameter and mounting
positions are schematic and must follow the selected numeral hardware.

References:

- [Brook specification sheet](https://cdn.sanity.io/files/lrx9w99n/production/9d39bfc360a3fc010ca203d22dd87101716f5845.pdf)
- [Brook installation guide](https://www.mod-lighting.com/installation/brook)
- [Selected UF connector](https://www.homedepot.com/p/316096859)
- [Round blank cover](https://www.homedepot.com/p/300848519)

New model objects:

```text
front_street_light
front_street_light_bracket
front_address_number_1
front_address_number_1_standoff_1
front_address_number_1_standoff_2
front_address_number_2
front_address_number_2_standoff_1
front_address_number_2_standoff_2
front_address_number_3
front_address_number_3_standoff_1
front_address_number_3_standoff_2
front_address_number_4
front_address_number_4_standoff_1
front_address_number_4_standoff_2
```

## 38. Finish the right-side outlet (`outlet-finish`)

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

The 36 steps assign every active construction object exactly once.
Thirteen deferred tambour reference objects remain hidden unless `show_deferred`
is enabled in the completed view. Ground is visualization context outside the
numbered installation sequence. Wall course steps descend from top to bottom.
