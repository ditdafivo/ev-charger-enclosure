# NewTechWood Cladding, Matching Deck Roof, and HDPE Tambour

## Summary

Replace the wall decking with Indian Ebony NewTechWood US09 siding, retain a distinct roof surface using matching US07 Cortes Plus decking, and change the 56 tambour slats to 1/2-inch black HDPE. Preserve the current enclosure dimensions, horizontal wall-board orientation, openings, and tambour geometry.

Follow the manufacturer systems: US09 uses AW02/AW08 hardware over ventilated furring, while US07 is face-fastened over supports no more than 16 inches on center. Use the user-selected 50°F installation-gap assumptions. [US09 specifications](https://www.newtechwood.com/siding/all-weather/), [US07 product](https://www.homedepot.com/p/332886377), [decking guide](https://www.newtechwood.com/wp-content/uploads/2021/09/Decking-Installation.pdf.pdf).

## Implementation Changes

- Refactor `CompositeSiding` so wall cladding and roof decking have separate product specifications, dimensions, stock lengths, course gaps, colors, materials, and BOM optimization.
  - Walls: US09-8-EB, 142 mm × 13 mm × 96 inches, horizontal courses, Indian Ebony, interlocking courses without the current 3/16-inch course gap.
  - Roof: US07-8-G9-EB, 138 mm × 22.5 mm × 96 inches, retain the existing 3/16-inch lateral drainage gap and use 1/16-inch end clearances for the selected 50°F installation condition.
  - Preserve the existing bottom elevation and all street-light, outlet, and tambour openings; recompute course cuts and ripped terminal boards from the new profiles.

- Implement the complete US09 attachment system.
  - Add actual 1-inch-thick pressure-treated vertical furring at no more than 16 inches on center, including independent support at every board end and opening edge.
  - Model and list AW02 starters, AW08 clips at every furring/course intersection, one locked AW08 clip per board, T-7 final-course supports, and the manufacturer-specified stainless clip/locking screws.
  - Replace generic black angles with matching Indian Ebony US46 outside-corner and US44 edge/opening trims; omit US45 because every enclosure run fits within one 8-foot board.
  - Recalculate electrical-box projections, trim planes, enclosure bounds, and tambour clearances from the new furring-plus-board finished wall plane.
  - Add all boards, furring, trims, clips, fasteners, and stock quantities to the existing BOM schema, identifying products and SKUs in the `type` field.

- Update the roof support and BOM.
  - Keep the perimeter roof shims and add a centered front-to-rear support/shim so the 27.5-inch board run has no span greater than 16 inches.
  - Maintain the existing roof footprint and drainage gaps, face-fasten US07 at each support with manufacturer-approved stainless composite screws, and keep fasteners 1.5 inches from board ends.
  - Verify the added center support retains the modeled 1/4-inch tambour swept-envelope clearance and does not conflict with gussets or removable ceiling access.
  - Allocate the calculated roof cuts from 8-foot stock separately from the US09 wall stock.

- Convert the tambour design to HDPE.
  - Keep 56 finished slats at 20 1/2 × 3/4 × 1/2 inches, the 25/32-inch pitch, black appearance, 44-inch curtain length, track spacing, and existing clearance-coupon process.
  - Add a kerf-aware sheet cut plan for one 24 × 48-inch and one 12 × 24-inch black HDPE sheet. With a 0.110-inch kerf, the primary sheet yields 55 slats; cut the remaining production slat and spares/coupons from the second sheet.
  - Document supported panel handling, a narrow-rip jig/push blocks, moderate feed, minimal blade exposure, dust collection, and inspection for melted or burred edges. Ease and deburr the moving edges without reducing required track engagement.
  - Retain the Freud LU94M010, but move the operation to a different table saw with a manufacturer-approved riving knife thicker than the blade’s 0.087-inch plate and thinner than its 0.110-inch kerf. Explicitly prohibit these through-rips on the DWE7491RS stock 0.087-inch riving knife configuration. [Freud blade data](https://www.freudtools.com/public/catalog/freud-catalog/docs/Freud_GPCatalog_2020_LOWRES.pdf), [DWE7491RS manual](https://www.dewalt.com/GLOBALBOM/QU/DWE7491RS/10/Instruction_Manual/EN/N531890_DWE7491rs.pdf).

- Redesign HDPE attachments.
  - Route three 1/16-inch-deep webbing seats into each concealed face so the existing 1-inch polyester strips remain within the inward envelope.
  - Use corrosion-resistant M3 flush countersunk through-fasteners: a round fixed hole at the center webbing and span-direction expansion slots at the two outer strips. Replace every wood-screw assumption.
  - Revise the printed pull handle for M4 flush countersunk through-fasteners, with one centered locating hole and span-direction slots at the remaining positions. Both faces must remain flush or within the existing 1/16-inch inward projection.
  - Parameterize hole, slot, counterbore, and fastener-stack dimensions in `TambourFabricationConfig`; update generated STEP/STL parts, manifests, fabrication guidance, BOM rows, and the production build record.

## Public Interfaces and Outputs

- Add explicit wall-cladding and roof-decking product-spec types while keeping the existing CSV/JSON column schemas stable.
- Extend tambour fabrication configuration with slat span/material, sheet-stock dimensions, saw kerf, webbing recess, and M3/M4 attachment geometry.
- Generate distinct BOM lines for US09 wall boards, US07 roof boards, system trims/hardware, furring, HDPE sheets, webbing fasteners, and pull-handle fasteners.
- Update `BUILD_STEPS.md` and `TAMBOUR_DOOR.md` so product links, quantities, installation sequence, safety gates, and acceptance tests match the model.

## Test Plan

- Assert exact US09/US07 dimensions, colors, SKUs, 96-inch stock lengths, course layout, opening cuts, stock allocation, and separate roof/wall BOM rows.
- Verify every wall board is supported at no more than 16-inch centers, every clip/trim is counted, wall openings retain their required clearances, and electrical fixtures terminate at the new finished plane.
- Verify roof board gaps, center support, maximum span, fastener locations, tambour clearance, gusset clearance, and configurable enclosure sizes.
- Assert 56 HDPE slats, kerf-aware 55-plus-1 sheet yield, correct finished dimensions, and allowance for spare/coupon pieces.
- Validate webbing/handle slots, countersinks, thermal-movement direction, swept-envelope limits, printable-part validity, and full open/closed tambour collision checks.
- Run the complete test suite and a non-deploying build; inspect generated OpenSCAD, BOM, cut lists, shopping lists, and tambour manifests for internal consistency.

## Assumptions

- Wall boards remain horizontal; the roof boards retain their current front-to-rear course arrangement.
- Installation temperature is 50°F; short enclosure boards use at least 1/16-inch clearance at restrained ends.
- US09 trim is matching Indian Ebony.
- The roof decking is a ventilated/draining cover, not a waterproof roof membrane.
- The LU94M010 is retained only with a different guarded saw/riving-knife configuration; the DWE7491RS is excluded from the production rip operation.
