# HDPE tambour

## Summary

## Implementation Changes

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

- Extend tambour fabrication configuration with slat span/material, sheet-stock dimensions, saw kerf, webbing recess, and M3/M4 attachment geometry.
- Generate distinct BOM lines for furring, HDPE sheets, webbing fasteners, and pull-handle fasteners.
- Update `BUILD_STEPS.md` and `TAMBOUR_DOOR.md` so product links, quantities, installation sequence, and acceptance tests match the model.

## Test Plan

- Assert 56 HDPE slats, kerf-aware 55-plus-1 sheet yield, correct finished dimensions, and allowance for spare/coupon pieces.
- Validate webbing/handle slots, countersinks, swept-envelope limits, printable-part validity, and full open/closed tambour collision checks.
- Run the complete test suite and a non-deploying build; inspect generated OpenSCAD, BOM, cut lists, shopping lists, and tambour manifests for internal consistency.

## Assumptions

- The LU94M010 is retained only with a different guarded saw/riving-knife configuration; the DWE7491RS is excluded from the production rip operation.