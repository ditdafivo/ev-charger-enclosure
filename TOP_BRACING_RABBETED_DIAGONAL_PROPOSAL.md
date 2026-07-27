# Rabbeted top-diagonal and consolidated side-brace proposal

## Status and purpose

This document records a candidate replacement for the unresolved butt-ended
top-diagonal connection described in [`TOP_BRACING.md`](TOP_BRACING.md). It is
a design-development proposal, not an approved construction detail.

Use this document to:

1. select candidate lumber, tie plates, fasteners, shims, and subsidiary
   connectors;
2. verify the geometry and load path with those exact components;
3. complete the member and connection calculations;
4. obtain project-specific structural and authority approval where required;
5. update the model only after the checks below pass.

The proposal deliberately separates fixed geometric requirements from
unresolved product selections. A generic tie plate or a screw that merely fits
must not be assigned a published capacity from a different tested connector
configuration.

## Design objective

Replace the current nominal 1x4 diagonal, which terminates at the inside
corners of the posts without a fabricated joint, with an extended nominal 1x4
that overlaps the two diagonal posts and adjacent framing in routed top seats.
The diagonal remains flush with the `z = 47.00` frame plane.

At the same time, replace the left and right top perimeter 2x4 braces with
top-flush 4x4 members. These deeper members provide usable screw penetration
beneath the diagonal and consolidate the functions of several existing side
rails without reducing the modeled clearance below the current framing.

A tie plate at each diagonal end distributes force between the diagonal, the
underlying post, and the underlying 4x4 side brace. Exact plates, screws, hole
patterns, and connection capacities remain to be selected and checked.

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

## Preliminary connection concept

Install one tie plate over each supported end region of the diagonal. Each
plate should engage the diagonal and framing on both sides of the force-transfer
interface. The preliminary primary load path is:

```text
diagonal
  -> tie plate and primary screw group
  -> underlying 4x4 post and 4x4 side brace
  -> perimeter frame/post joints
  -> posts and foundation system
```

The front or back 2x4 and its fasteners may supplement this path, but the
connection should not require short screws through the 0.75-inch diagonal to
develop the full design force in only 0.75 inch of remaining 2x4 depth.

A nominal 3-inch screw installed from the top through the plate and 0.75-inch
diagonal has approximately 2.25 inches of penetration available in an
underlying post or 4x4 before deductions for the plate thickness and any
manufacturer-defined point or effective-thread provisions. It should terminate
approximately 0.5 inch above the underside of a top-flush 4x4. Use exact
dimensions from the selected screw and plate rather than these nominal values
in the final check.

Fasteners driven vertically into the post tops enter end grain. The final
design must:

- check the applicable lateral end-grain adjustment;
- prevent a load component that relies on prohibited or unverified end-grain
  withdrawal;
- include plate eccentricity, bending, prying, and fastener-head effects;
- satisfy fastener spacing, end distance, edge distance, and group-action
  requirements within the available post and brace footprints;
- account for wet service, treated lumber, load duration, and corrosion;
- verify that the plate transfers both tension and compression load directions,
  or that direct wood bearing provides the compression path while the plate
  provides the reversible tension path.

Published connector values apply only to the manufacturer's specified plate,
fasteners, quantities, holes, lumber, orientation, and loading direction. Do
not assign the capacity of a listed connector to a generic mending plate or a
custom skewed installation without an applicable calculation, test basis, or
manufacturer/engineer approval.

## Roof shims and finished height

The tie plates and screw heads project above `z = 47.00`. Accept that projection
as an increase in finished structure height rather than cutting a plate recess
into the 0.75-inch diagonal.

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

Record exact products here before relying on published values.

| Item | Candidate | Required information | Status |
|---|---|---|---|
| Diagonal lumber | TBD | Stress-rated nominal 1x4; species, grade, treatment, moisture condition | Open |
| Side braces | TBD | Stress-rated nominal 4x4; species, grade, treatment | Open |
| End tie plate | TBD | Manufacturer/model or custom material, dimensions, gauge, coating, hole pattern, load directions | Open |
| Primary post screws | TBD | Manufacturer/model, diameter, total length, effective penetration, coating, end-grain basis | Open |
| Primary 4x4-brace screws | TBD | Manufacturer/model, diameter, total length, effective penetration, coating | Open |
| Supplemental 2x4 screws | TBD | Exact listed use and whether installed through diagonal or directly into framing | Open |
| `rail_ft` support connection | TBD | Extended support-stud joint or listed connector and fasteners | Open |
| Tambour ceiling attachment | TBD | Cleat/angle/fasteners that preserve clearances | Open |
| Roof shims | TBD | Material, thickness, width, spacing, treatment, fastening | Open |
| Roof fasteners | TBD | Added shim thickness, required penetration, corrosion compatibility | Open |
| Isolation/drainage material | TBD | Compatibility and water-management detail | Open |

Useful selection sources include:

- [Simpson Strong-Tie connector fastener requirements](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/connector-holes-fastener-types)
- [Simpson Strong-Tie SDS Heavy-Duty Connector screws](https://www.strongtie.com/strongdrive_exteriorwoodscrews/sds_screw/p/strong-drive-sds-heavy-duty-connector-screw)
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

### Plates and fasteners

- Check plate gross and net tension, shear, bending, buckling, tear-out, block
  shear, and bearing at holes as applicable.
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
- tie plates, screw heads, and shims have an explicit modeled envelope;
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
7. Add selected plates, screws, and their exact installed envelopes.
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

## Approval gate

The proposal may advance to the final model only when the selected products and
calculations establish all of the following:

- at least 826 pounds ASD axial capacity in both directions at each diagonal
  end and through the complete frame/post load path;
- acceptable 1x4 compression, tension, net-section, and stability capacity;
- acceptable routed post and 4x4 residual-section capacity;
- compliant plate and fastener installation with explicit treatment of
  end-grain and any withdrawal/prying effects;
- acceptable connection deformation and frame racking;
- acceptable gravity support by the revised 4x4 perimeter members;
- complete support for all framing formerly dependent on the removed rails;
- verified tambour operation and clearance;
- verified roof support, drainage, corrosion compatibility, and revised
  finished-height detailing;
- project-specific structural and authority approval required by the governing
  code and project circumstances.
