# Rabbeted top-diagonal and consolidated side-brace proposal

## Status and purpose

This document records a candidate replacement for the unresolved butt-ended
top-diagonal connection described in [`TOP_BRACING.md`](TOP_BRACING.md). It is
a design-development proposal, not an approved construction detail.

Use this document to:

1. evaluate the selected catalog-metal candidate and the exterior-plywood
   fallback with their exact fasteners and supporting framing;
2. verify the geometry and load path with those exact components;
3. complete the member and connection calculations;
4. obtain project-specific structural and authority approval where required;
5. update the model only after the checks below pass.

The preferred connection-selection order is a cataloged metal connector, then
an engineered 3/4-inch exterior-plywood gusset if no catalog installation is
applicable. MDF, generic mending plates, field-modified connectors, and custom
machined steel are excluded. A connector or screw that merely fits must not be
assigned a published capacity from a different tested configuration.

## Design objective

Replace the current nominal 1x4 diagonal, which terminates at the inside
corners of the posts without a fabricated joint, with an extended nominal 1x4
that overlaps the two diagonal posts and adjacent framing in routed top seats.
The diagonal remains flush with the `z = 47.00` frame plane.

At the same time, replace the left and right top perimeter 2x4 braces with
top-flush 4x4 members. These deeper members provide usable screw penetration
beneath the diagonal and consolidate the functions of several existing side
rails without reducing the modeled clearance below the current framing.

A connector at each diagonal end distributes force between the diagonal and
the adjacent framing. Simpson Strong-Tie HTP37Z heavy tie plates are the first
catalog candidate. Engineered 3/4-inch exterior-plywood gussets are the fallback.
The previously considered MSTA18Z-and-blocking alternative is geometrically
inviable because its required blocking conflicts with the tambour envelope.
Neither remaining option is approved until the configuration-specific checks
below pass.

## Existing geometry

The default model uses a 27.5-by-21.875-inch outside post envelope and a
20.5-by-14.875-inch clear top opening. The current diagonal runs between the
inside corners of the back-left and front-right posts:

```text
start = (3.500, 18.375, 46.250)
end   = (24.000, 3.500, 46.250)

actual section = 0.75 x 3.50 inches
clear length   = 25.328 inches, nominal cut length 25 5/16 inches
plan angle     = 35.965 degrees from the x axis
top plane      = z 47.00 inches
bottom plane   = z 46.25 inches
```

The side framing currently occupies these vertical ranges:

| Current members | Vertical envelope |
|---|---:|
| `brace_fl_bl`, `brace_fr_br` | `z = 45.50` to `47.00` |
| `rail_l_tambour`, `rail_r_tambour` | `z = 43.75` to `45.25` |
| `rail_lt`, `rail_rt` | `z = 42.75` to `44.25` |
| Tambour ceiling panel | `z = 43.25` to `43.50` |
| `rail_ft` | `z = 41.00` to `42.50` |

## Proposed framing geometry

### Top side braces

Change these two members from flat 2x4s to 4x4s while retaining their current
plan spans and `z = 47.00` top plane:

| Member | Proposed actual section | Proposed vertical envelope |
|---|---:|---:|
| `brace_fl_bl` | 3.50 x 3.50 inches | `z = 43.50` to `47.00` |
| `brace_fr_br` | 3.50 x 3.50 inches | `z = 43.50` to `47.00` |

The proposed 4x4s have the same 3.5-inch plan width as the existing flat 2x4
members. Their undersides remain 0.75 inch above the lowest part of the
existing `rail_lt` and `rail_rt` envelope. The substitution therefore does not
consume any space that is not already occupied by modeled framing.

The left 4x4 interior face is its positive-x face at `x = 3.50`. The right 4x4
interior face is its negative-x face at `x = 24.00`.

### Consolidated rail functions

Subject to connection and service-load checks, use the two 4x4 side braces to
replace the following members:

| Remove | Replacement function |
|---|---|
| `rail_l_tambour` | Left 4x4 interior face and underside support the tambour assembly. |
| `rail_r_tambour` | Right 4x4 interior face and underside support the tambour assembly. |
| `rail_lt` | Left 4x4 and extended vertical framing receive its dependent members. |
| `rail_rt` | Right 4x4 and extended vertical framing receive its dependent members. |

The tambour ceiling top is already at `z = 43.50`, coincident with the proposed
4x4 undersides. Detail the ceiling-edge attachment to the 4x4 interior faces or
undersides without reducing the required curtain clearance.

Keep `rail_ft` at its current `z = 41.00` to `42.50` envelope unless a later
tambour analysis supports moving it. Extend `rail_ft_left_support` and
`rail_ft_right_support` upward to the 4x4 undersides at `z = 43.50`; this is the
preferred preliminary support path for `rail_ft`. Also extend or reconnect
`front_center_rail`, `right_center_rail`, `right_tambour_rail`, and
`left_tambour_rail` as necessary after removing `rail_lt` and `rail_rt`.

### Extended diagonal and routed seats

Continue the existing diagonal centerline across the back-left and front-right
post tops to the outside x faces of the frame. This produces a preliminary
overall length of approximately:

```text
25.328 x (27.5 / 20.5) = 33.977 inches
```

Use approximately 34 inches only for early component and stock planning. The
model and fabrication detail must determine the final endpoints, end cuts, and
routed-seat limits.

Route 0.75-inch-deep seats in the necessary portions of:

- `post_bl` and `post_fr`;
- `brace_fl_bl` and `brace_fr_br`; and
- any intersected portions of `brace_bl_br` and `brace_fl_fr` required by the
  final diagonal footprint.

The routed seats receive the full 0.75-inch diagonal thickness so that the
diagonal top remains at `z = 47.00`. Do not reduce the diagonal itself to make
the lap. The 4x4 posts and side braces retain 2.75 inches of depth beneath a
full-depth seat.

The extended board is approximately 34 inches overall, but its unsupported
compression length need not automatically increase from the existing
25.328-inch clear opening. If the routed end regions provide verified bearing,
lateral restraint, and force transfer, the clear opening may continue to govern
the effective length. The structural calculation must establish the actual
effective length rather than assuming either overall board length or clear
opening length.

## Connection alternatives and selection order

Use direct wood bearing in the routed seats as the compression load path. Use
Option A at each end as the reversible tension load path if it passes the
structural, geometric, corrosion, and approval gates; otherwise use Option B.
The rejected alternative remains documented to prevent it from being
reintroduced without resolving its geometric conflict.

### Option A: HTP37Z heavy tie plate

First ask Simpson Strong-Tie to confirm in writing whether an HTP37Z can be used
in the actual layered, skewed geometry. The HTP37Z is a 3-by-7-inch, 16-gauge
ZMAX plate. The connector catalog lists DF/SP and SPF/HF allowable tension
loads of 1,850 and 1,600 pounds, respectively, with twenty specified
0.148-by-1.5-inch nails. ICC-ES ESR-3096 lists 2,735 pounds with twenty SD9112
screws. These values apply to their stated fastener schedules and include the
wind/seismic load-duration increase; do not mix the schedules or apply another
increase.

The plate is a promising geometric candidate because each half of its 7-inch
length can fit within a nominal 3.5-inch connection region. The published value
must not be used unless the manufacturer or project engineer accepts all of the
following departures from a simple coplanar splice:

- the diagonal is routed flush into, and overlaps, the supporting framing;
- any fastener assigned to the lower framing passes through the 0.75-inch
  diagonal before entering that framing;
- some available framing beneath the plate includes post end grain;
- the load and plate axes follow the 35.965-degree diagonal rather than a
  conventional lumber splice; and
- only holes with solid wood and compliant edge/end distances beneath them may
  be counted.

Use the complete current HTP37Z fastener schedule if this configuration is
accepted. Candidate fasteners are hot-dip-galvanized 0.148-by-1.5-inch connector
nails or SD9112 Strong-Drive SD connector screws. Either fastener reaches only
about 0.75 inch into lower framing after passing through the 0.75-inch diagonal;
the catalog values therefore cannot be assigned to that layered installation
without written acceptance. Do not substitute longer nails, the earlier 3-inch
SDS screw, or ordinary deck screws.

#### Why a longer screw is not a catalog substitution

A longer screw may be part of an engineered connection, but it does not retain
the HTP37Z catalog value automatically. ESR-3096 assigns the 2,735-pound value
to exactly twenty SD9112 screws, with half installed directly into each member
of a coplanar splice. Simpson requires the specified fastener type, size,
quantity, finish, and holes for a published connector load.

A longer #9 SD connector screw may fit the prepunched holes, but the routed lap
is no longer the rated two-member splice. The plate remains on top of the
diagonal, so a framing-side screw bears first in the 0.75-inch diagonal and then
in the lower framing. This creates a layered multiple-member yield mechanism and
changes screw bending, wood bearing, slip, group stiffness, force distribution,
and splitting behavior. Added penetration does not remove the interposed loaded
diagonal or restore the catalog geometry.

Simpson's general longer-fastener provision for a strap installed over wood
structural-panel sheathing is limited to sheathing no thicker than 5/8 inch.
The 0.75-inch diagonal is thicker and is a loaded brace rather than incidental
sheathing. A 1/4-inch SDS screw is also a different fastener family and is too
large for the HTP37Z's approximately 5/32-inch holes; enlarging those holes is
prohibited. Other structural, ledger, or deck screws have no HTP37Z rating.

Accordingly, use a longer screw only if Simpson approves the exact screw and
layered configuration in writing or a project-specific calculation treats the
HTP37Z as a steel side plate without claiming its catalog value.

### Rejected alternative: MSTA18Z strap with blocking

An MSTA18Z requires substantially more side-grain anchorage length than the
existing post and side-brace footprint provides. The considered solution added
a diagonal-aligned 4x4 block beneath the framing half of the strap, with its top
flush at `z = 47.00` and underside at `z = 43.50`.

That block would project from the perimeter into the clear top opening. The
horizontal 1.5-inch curtain envelope begins at `z = 43.75`, while the removable
ceiling occupies `z = 43.25` to `43.50`. The block would therefore overlap
approximately 3.25 inches of the curtain's vertical envelope wherever their
plan footprints intersect, occupy the space immediately above the ceiling, and
obstruct ceiling attachment and removal. Restricting the block to the already
occupied perimeter footprint does not provide the required strap anchorage
length. The MSTA18Z-and-blocking option is rejected and must not be modeled or
procured for this proposal.

### Option B: exterior-plywood gusset

If no HTP37Z configuration is approved, use an engineered gusset cut from
23/32- or 3/4-inch APA-trademarked Structural I plywood with an Exterior bond
classification. Do not use Exposure 1/CDX, OSB, MDF, particleboard, or an
unmarked project panel. Unlike MSTA blocking, the gusset adds material only
above `z = 47.00` and therefore preserves the interior tambour envelope.

Shape the gusset to engage the diagonal, side 4x4, adjacent perimeter member,
and usable post footprint while avoiding reliance on end-grain withdrawal.
Select exterior-rated structural wood screws from published lateral-load data
for a 3/4-inch plywood side member and treated Douglas fir. The earlier 3-inch
SDS screw is not presumed adequate: the plywood and diagonal together consume
approximately 1.5 inches before the screw reaches the framing.

Check both plywood strength axes, panel shear, tension, net section, fastener
bearing, tear-out, group action, splitting, wet service, edge and end distances,
and deformation. Seal all cut edges and holes after fabrication; field-applied
sealer does not upgrade an Exposure 1 panel to Exterior.

### Common load path

The preliminary primary load path is:

```text
diagonal
  -> selected connector and fastener groups
  -> adjacent 4x4 and perimeter framing
  -> perimeter frame/post joints
  -> posts and foundation system
```

The front or back 2x4 and its fasteners may supplement this path, but the
connection should not require short screws through the 0.75-inch diagonal to
develop the full design force in only 0.75 inch of remaining 2x4 depth.

Fasteners driven vertically into the post tops enter end grain. The final
design must:

- check the applicable lateral end-grain adjustment;
- prevent a load component that relies on prohibited or unverified end-grain
  withdrawal;
- include connector eccentricity, bending, prying, and fastener-head effects;
- satisfy fastener spacing, end distance, edge distance, and group-action
  requirements within the available post and brace footprints;
- account for wet service, treated lumber, load duration, and corrosion;
- verify direct wood bearing as the compression path and the selected connector
  as the reversible tension path.

Published connector values apply only to the manufacturer's specified connector,
fasteners, quantities, holes, lumber, orientation, and loading direction. Do
not assign the capacity of a listed connector to a generic mending plate or a
custom skewed installation without an applicable calculation, test basis, or
manufacturer/engineer approval.

## Roof shims and finished height

The selected connector and fastener heads project above `z = 47.00`. Accept
that projection as an increase in finished structure height rather than cutting
a connector recess into the 0.75-inch diagonal. A plywood gusset adds almost
3/4 inch more projection than the HTP37Z candidate.

Let `h_hardware` be the maximum installed projection above the diagonal,
including plate thickness, screw-head projection, tolerances, and any required
isolation material. Provide a shim/support system beneath the composite top
boards with a finished thickness of at least `h_hardware`.

Preliminary resulting elevations are:

```text
composite top-board bottom = 47.00 + h_hardware
finished composite top     = 48.00 + h_hardware
```

The shim design must:

- keep all top boards level and adequately supported between framing members;
- provide suitable fastening locations and preserve required fastener
  penetration;
- avoid point support or rocking over connector heads;
- tolerate outdoor moisture and remain compatible with treated lumber,
  connector coatings, and composite decking;
- preserve drainage and avoid water traps around the plates;
- coordinate the wall-board top edges and aluminum edge trim with the raised
  roof plane.

The current `CompositeSiding` model uses one frame-top elevation to derive both
top-board placement and finished wall height. The model may need separate roof
support and wall-top elevations rather than raising every siding component by
`h_hardware`.

## Component-selection worksheet

These candidates are readily procurable in the Boulder, Colorado 80301 area.
Home Depot Boulder #1546 is at 1600 29th Street; Lowe's Boulder is at 6379
Valmont Road. Web inventory is a snapshot, so confirm the exact model and pickup
quantity before travel. Lumber must be accepted from its physical grade and
treatment stamps rather than the retail listing alone.

| Item | Candidate | Required information | Status |
|---|---|---|---|
| Diagonal lumber | Home Depot Internet #202083125, model 767150, PT Douglas-fir 1x4x8 | Physical No. 2-or-better grade stamp, 0.75-by-3.5-inch actual section, treatment, moisture, incising | Candidate; reject ungraded, undersized, incised without recalculation, checked, split, waned, or crooked stock |
| Side braces | PT Douglas-fir 4x4x8, No. 2 or better | Physical species/grade/treatment stamps and 3.5-inch actual section | Candidate; one 8-foot timber supplies the two side braces |
| Primary catalog plate | Simpson Strong-Tie HTP37Z, Home Depot Internet #202329565 / Lowe's item #312976 | Written applicability to layered routed geometry, current load table, full fastener schedule | Preferred candidate; not yet configuration-approved |
| Rejected catalog strap | Simpson Strong-Tie MSTA18Z, Home Depot Internet #100375194 | Required side-grain anchorage would need blocking inside the clear opening | Rejected; block overlaps the tambour envelope and ceiling-service space |
| Wood gusset | 23/32- or 3/4-inch APA Structural I plywood, Exterior bond classification | APA stamp, species/group, panel design values, exterior durability | Immediate fallback if HTP37Z is not approved; engineer sizes outline and fastener groups |
| HTP fasteners | Manufacturer-specified hot-dip-galvanized 0.148-by-1.5-inch nails or SD9112 screws | Exact coating, count, penetration, and written applicability to layered geometry | Open pending connector confirmation; longer screws are not a catalog substitution |
| Primary plywood-gusset screws | Exterior-rated structural wood screw, length TBD | Published plywood-side-member lateral value, effective penetration, wet service, coating | Open pending gusset design; 3-inch SDS not presumed adequate |
| `rail_ft` support connection | Simpson Strong-Tie A35Z with SD9112 screws, or calculated direct joint | Current connector table, load direction, screw count, clearance | Candidate |
| Tambour ceiling attachment | Simpson Strong-Tie A21Z with SD9112 screws, or exterior-rated continuous aluminum cleat | Ceiling load, spacing, galvanic isolation, curtain clearance | Candidate |
| Roof shims | Continuous ripped PT-lumber strips | Finished `h_hardware`, width, spacing, treatment, fastening | Candidate; do not use stacked plastic wedges |
| Roof fasteners | Existing approved composite fastener increased for final shim thickness | Required penetration, coating, tip clearance | Open pending `h_hardware` |
| Isolation/drainage material | YellaWood Joist Shield YW113W094, 4-inch butyl tape | Compatibility, drainage terminations, locations outside connector interfaces unless approved | Candidate |

Useful selection sources include:

- [Simpson HTP37Z retail listing and specified fasteners](https://www.homedepot.com/p/202329565)
- [Simpson MSTA18Z ZMAX retail listing](https://www.homedepot.com/p/100375194)
- [Simpson SD-connector code report ESR-3096](https://www.icc-es.org/wp-content/uploads/report-directory/ESR-3096.pdf)
- [Simpson strap and plate code report ESR-2105](https://icc-es.org/wp-content/uploads/report-directory/ESR-2105.pdf)
- [Simpson Strong-Tie connector fastener requirements](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/connector-holes-fastener-types)
- [Simpson corrosion-compatible material and coating guidance](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/corrosion-info/materials-and-coatings)
- [APA exterior-panel and bond-classification guidance](https://www.apawood.org/help)
- [American Wood Council Connection Calculator](https://awc.org/resources/connection-calculator/)
- the current NDS and selected manufacturers' current code reports and load
  tables.

## Required structural checks

### Design demand

Retain the conservative screening demand from [`TOP_BRACING.md`](TOP_BRACING.md)
unless a revised wind/load-path analysis supersedes it:

```text
top-plane design shear = 485 pounds ASD
diagonal axial demand  = 826 pounds ASD
```

Each diagonal end and the complete downstream load path must resist at least
826 pounds ASD in both load directions. Do not apply another wind-duration
increase to a published allowable load that already includes it.

### Diagonal member

- Confirm the selected 1x4 species and grade meet or exceed the assumed
  Douglas fir-larch No. 2 values.
- Recalculate compression using the justified effective length and actual end
  restraint.
- Confirm tension capacity at every hole, defect, and minimum net section.
- Confirm weak-axis stability where the board crosses the clear opening.
- Reject checks, splits, wane, or slope-of-grain defects in both connection
  regions.

### Routed posts and 4x4 side braces

- Check the 2.75-inch residual depth beneath each routed seat.
- Check local bearing from the diagonal in both force directions.
- Check net-section tension, shear, bending, splitting, and cross-grain effects
  around each routed boundary and screw group.
- Check the 4x4 side braces over their 14.875-inch clear span for roof gravity
  load and all forces introduced by the diagonal and dependent framing.
- Check the post-to-perimeter and 4x4-to-post corner connections as part of the
  same load path.

### Connectors and fasteners

- Check connector or gusset gross and net tension, shear, bending, buckling,
  tear-out, block shear, and bearing at holes as applicable.
- Check each screw for lateral capacity in its actual grain orientation and
  effective penetration.
- Check any withdrawal component, head pull-through, group action, row
  interaction, spacing, edge distance, and end distance.
- Check load direction relative to the plate's published axes.
- Verify that all required holes fit inside solid underlying wood after routing.
- Verify screw tips and connector projections do not violate tambour or wiring
  clearances.
- Check combined connection deformation so frame racking remains acceptable,
  not merely below ultimate connection capacity.
- For HTP37Z, obtain written acceptance of the layered routed installation or
  use a project-specific calculation; the catalog load alone is insufficient,
  and greater screw length alone does not restore the catalog geometry.
- Do not advance MSTA18Z blocking: its required side-grain anchorage conflicts
  with the curtain envelope and removable-ceiling service space.
- For plywood, check both panel axes, panel and fastener failure modes, exterior
  durability, and the longer screw schedule.

### Consolidated framing and tambour support

- Verify all members that formerly terminated at `rail_lt` or `rail_rt` have a
  defined replacement support and fastening detail.
- Verify the tambour ceiling and track attachment to the 4x4 faces/undersides.
- Repeat the full tambour travel and 1.5-inch curtain-envelope clearance check.
- Confirm that removal of the four rails does not eliminate required siding,
  electrical-backing, conduit, cable, or trim attachment points.

### Roof support and weathering

- Check shim bearing, spacing, crushing, screw bending, and roof fastener
  penetration.
- Check composite manufacturer requirements for support spacing and fastening.
- Detail drainage around plates and penetrations.
- Verify corrosion compatibility between treated wood, steel plates, screws,
  aluminum trim, and environmental exposure.

## Geometry acceptance criteria

The proposal passes the geometric gate only if the updated model demonstrates
all of the following:

- frame top remains `z = 47.00` before plates, heads, and roof shims;
- proposed side 4x4 undersides remain `z = 43.50`;
- diagonal section remains a full 0.75 by 3.50 inches through the clear span;
- routed seats place the diagonal top flush at `z = 47.00`;
- the selected connectors, fastener heads, gusset, and shims have explicit
  modeled envelopes;
- the tambour ceiling remains at or below `z = 43.50` and has a buildable
  attachment;
- the complete 1.5-inch curtain envelope retains its required clearances;
- `rail_ft` and all dependent vertical rails have defined supports;
- screw tips do not protrude into the tambour, electrical, or service spaces;
- composite roof boards have continuous or manufacturer-compliant support at
  the raised elevation;
- exterior trim and wall-to-roof closure accommodate the revised finished
  height.

## Model-update plan after structural acceptance

Do not implement the proposal as final construction geometry until the load
checks pass. When accepted, update the model in this order:

1. Change `brace_fl_bl` and `brace_fr_br` to top-flush 4x4 members.
2. Remove `rail_l_tambour`, `rail_r_tambour`, `rail_lt`, and `rail_rt`.
3. Rebind the tambour ceiling and other dependent components to the new 4x4
   members or explicit absolute geometry.
4. Extend the vertical members and the two `rail_ft` support studs to the new
   4x4 undersides.
5. Replace the inside-corner diagonal geometry with explicit extended
   endpoints and preserve its full section.
6. Add a representation for routed seats. If the lumber model cannot represent
   fabrication cuts, add explicit routed-volume geometry and fabrication notes
   rather than silently overlapping solid members.
7. Add the selected HTP37Z or plywood gusset, its fasteners, and the exact
   installed envelopes. Do not add MSTA18Z blocking.
8. Add roof shims and separate roof-support elevation from wall-top elevation
   if required.
9. Update BOM and cut/fabrication outputs with 4x4 stock, the longer 1x4,
   routed-seat dimensions, hardware, shims, and removed rails.
10. Update `BUILD_STEPS.md`, `TOP_BRACING.md`, and
    `TOP_BRACING_SEQUENCE.md` to describe the approved detail and sequence.
11. Update tests for member types, endpoints, vertical envelopes, removed
    objects, dependencies, tambour clearance, roof elevation, BOM, cut list,
    and build-step assignments.
12. Regenerate all outputs and inspect the complete model visually for
    collisions and missing supports.

Likely code areas include the top-brace and rail definitions in `build.py`, the
inside-corner behavior of `LumberCollection.diagonal_between`, fabrication/BOM
support in `lumber_model`, `CompositeSiding` roof elevation handling, and the
corresponding tests.

## Decision log

Record iterations here so superseded hardware assumptions do not remain
implicit.

| Date | Decision or candidate | Result/reason |
|---|---|---|
| 2026-07-27 | Replace left/right top 2x4 braces with top-flush 4x4s. | Proposed; consolidates side rails and provides deeper diagonal anchorage without lowering the occupied framing envelope. |
| 2026-07-27 | Extend the 1x4 across the diagonal post tops in full-depth routed seats. | Proposed; resolves the unconnected butt-end geometry while retaining the `z = 47.00` frame plane. |
| 2026-07-27 | Accept plate/head projection above `z = 47.00` and shim the composite roof. | Proposed; avoids weakening the 1x4 with a plate recess. Exact hardware projection and finished height remain open. |
| 2026-07-27 | Prefer cataloged metal over an engineered plywood gusset; exclude MDF and custom-machined steel. | Selected evaluation order; minimizes added roof height and avoids moisture-sensitive nonstructural panels. |
| 2026-07-27 | Evaluate HTP37Z first. | Readily procurable, ZMAX, load-rated catalog plate; its 1,850-pound DF/SP value cannot be assigned to the layered routed geometry without manufacturer or engineer acceptance. |
| 2026-07-27 | Reject MSTA18Z with diagonal-aligned 4x4 blocking. | The block would occupy `z = 43.50` to `47.00`, overlap about 3.25 inches of the horizontal curtain envelope, and obstruct the removable ceiling; perimeter-only blocking cannot provide the strap's anchorage length. |
| 2026-07-27 | Do not treat a longer HTP37Z screw as a catalog substitution. | ESR-3096 rates twenty SD9112 screws in a direct coplanar splice. A longer screw through the 0.75-inch loaded diagonal creates an unrated layered connection; a 1/4-inch SDS also does not fit the specified holes without prohibited enlargement. |
| 2026-07-27 | Use 3/4-inch APA Structural I Exterior plywood if HTP37Z is not approved. | Engineer the gusset and longer fasteners as a new connection; its added material remains above `z = 47.00`. Reject MDF, OSB, Exposure 1/CDX, and unmarked panels. |

## Approval gate

The proposal may advance to the final model only when the selected products and
calculations establish all of the following:

- at least 826 pounds ASD axial capacity in both directions at each diagonal
  end and through the complete frame/post load path;
- acceptable 1x4 compression, tension, net-section, and stability capacity;
- acceptable routed post and 4x4 residual-section capacity;
- compliant catalog-connector installation or a complete engineered-plywood
  gusset calculation, with explicit treatment of end grain and any
  withdrawal/prying effects;
- acceptable connection deformation and frame racking;
- acceptable gravity support by the revised 4x4 perimeter members;
- complete support for all framing formerly dependent on the removed rails;
- verified tambour operation and clearance;
- verified roof support, drainage, corrosion compatibility, and revised
  finished-height detailing;
- project-specific structural and authority approval required by the governing
  code and project circumstances.
