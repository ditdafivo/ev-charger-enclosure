> Historical plan: the active siding product is now **US135 All Weather Pro**.
> The US09 product references, prices and takeoff below describe the earlier
> proposal. Use `SIDING.md` and generated BOM/cut lists for the current design.

# NewTechWood Cladding and Matching Deck Roof

## Summary

Replace the wall decking with Indian Ebony NewTechWood US09 siding and retain a distinct roof surface using matching US07 Cortes Plus decking. Preserve the current enclosure dimensions, horizontal wall-board orientation, openings, and existing tambour assembly without redesigning its door or slats.

The base mounting arrangement uses the existing open framing, with flush backing added only where a board, clip, or trim needs support. A continuous exterior layer of furring is optional, rather than a base BOM item. Keep the AW02/AW08 attachment system, supported board ends and opening edges, and support spacing no greater than 16 inches. This open-frame arrangement is a project design choice; it is not a claim that the manufacturer's complete wall assembly has been reproduced. Use the user-selected 50°F installation-gap assumptions. [US09 specifications](https://www.newtechwood.com/siding/all-weather/), [US09 installation guide](https://www.newtechwood.com/pdf/ALL_WEATHER_Siding_Horizontal_Installation_Guide.pdf), [US07 product](https://www.homedepot.com/p/332886282), [decking guide](https://www.newtechwood.com/pdf/Decking-Installation.pdf).

## Implementation Changes

- Refactor `CompositeSiding` so wall cladding and roof decking have separate product specifications, dimensions, stock lengths, course gaps, colors, materials, and BOM optimization.
  - Walls: **9 US09-8-EB boards**, 142 mm overall profile width × 13 mm × 96 inches, Indian Ebony. Use the installed course coverage, not the overall profile width, for the horizontal course count. The takeoff below reserves ten courses.
  - Roof: **1 US07-16-G9-EB board**, 138 mm × 22.5 mm × 192 inches. The mutually exclusive 8-foot-stock alternative is **2 US07-8-G9-EB boards**. Retain 3/16-inch lateral drainage gaps in the base layout and 1/16-inch clearances at restrained ends.
  - Preserve the existing bottom elevation, street-light and outlet openings, and tambour opening; recompute course cuts and ripped terminal boards from the new profiles. Leave the tambour door and slats unchanged.

- Implement the complete US09 attachment system.
  - Reuse framing as the attachment substrate and add the flush backing scheduled below. Do not add a blanket 1-inch exterior furring layer to the base design. Keep a full furring option separate because it changes the wall planes, board runs, electrical projections, and BOM.
  - Model and list AW02 starters, AW08 clips at every backing/course intersection, one locked AW08 clip per board, T-7 final-course supports, and the manufacturer-specified stainless clip/locking screws.
  - Replace generic black angles with matching Indian Ebony US46 outside-corner and US44 edge/opening trims; omit US45 because every enclosure run fits within one 8-foot board.
  - Recalculate electrical-box projections, trim planes, enclosure bounds, and existing tambour clearances from the actual clip-and-board profile on the framing. Include furring thickness only when that option is selected.
  - Add all boards, backing, trims, clips, fasteners, and stock quantities to the existing BOM schema, identifying products and SKUs in the `type` field.

- Update the roof support and BOM.
  - Keep the perimeter roof shims and add a centered front-to-rear support/shim so the 27.5-inch board run has no span greater than 16 inches.
  - Maintain the existing roof footprint and drainage gaps using the five balanced roof courses below. Face-fasten US07 at each support with stainless composite screws, keeping screw centers at least 1.5 inches from board ends and side edges. Do not retain the very narrow terminal strip from the generic decking layout.
  - Verify the added center support clears the existing tambour envelope and does not conflict with gussets or removable ceiling access.
  - Allocate the roof cuts from one 16-foot board, separately from the US09 wall stock. Also export the two-board 8-foot alternative without adding both alternatives to the shopping list.

## Procurement BOM and cut allocation

This takeoff is for the default 24 × 19 3/8-inch post-centerline enclosure, not arbitrary `--width`, `--depth`, or `--height` values. It is a procurement schedule for the proposed refactor, not output already implemented in `build.py`. Dimensions below are inches unless stated otherwise. Board and trim cuts listed as **blanks** include material for final fitting; their stock quantities are proven by the allocations below. Final trim stops, miters, profile lips, and end clearances must fit inside those blanks.

### Geometry and coverage basis

- Existing frame faces: 27 1/2 across the front/rear and 22 7/8 along each side. US46 corners replace the old overlapping decking returns; side blanks do not gain another two board thicknesses. No external furring offset is included.
- Wall visible bottom: `z = 2`. Wall top takeoff datum: `49.625 + 13 / 25.4 = 50.136811`; exposed wall height is therefore 48.136811. Keep roof support at `z = 49.875` and roof top at `49.875 + 22.5 / 25.4 = 50.760827`.
- NewTechWood's current [calculator data](https://www.newtechwood.com/wp-content/themes/newtechwood/js/project-calculator.js), linked from its [calculator page](https://www.newtechwood.com/calculator/), assigns US09 **6.9166667 square feet of installed coverage per 16-foot board**, versus 7.42 square feet at overall width. This implies a **5 3/16-inch installed pitch**: `6.9166667 / 16 × 12 ≈ 5.1875`. Do not use the 142 mm overall dimension as exposed course height.
- Reserve **10 courses**: `ceil(48.136811 / 5.1875) = 10`. The exposed course grid starts at `z = 2`, with seams at 7.1875, 12.375, 17.5625, 22.75, 27.9375, 33.125, 38.3125, 43.5, and 48.6875. The final course has 1.449311 of exposed height; determine its physical rip from the actual interlocking profile, retaining the mating lower edge.
- Rear tambour opening: `x = 3.5..24`, top `z = 47`. Rear course 9 is a full-width blank notched around the opening; course 10 is another full-width header blank. Courses 1–8 use two short wing blanks each. Counting only one full-width rear header would understate this takeoff.
- Front light cutout: `x = 11.55..15.95`, `z = 40.425..44.825`; notch front courses 8 and 9 from their full-width blanks. Right outlet cutout: `y = 16.475..19.275`, `z = 15.15..20.85`; notch right courses 3 and 4. Do not count the removed cutouts as reusable full-profile board stock.
- Verify the installed pitch with an engaged US09/AW08 sample before making terminal rips. The order below reserves ten courses and does not depend on salvaging narrow longitudinal rips.

### US09 wall boards: order 9 × US09-8-EB

| Blank ID | Application | Quantity | Blank length | Total length |
| --- | --- | ---: | ---: | ---: |
| A | Ten front courses plus rear courses 9 and 10 | 12 | 27.5 | 330 |
| B | Ten left and ten right courses | 20 | 22.875 | 457.5 |
| C | Rear left/right wings, courses 1–8 | 16 | 3.5 | 56 |
| **Total** | Full-profile blanks before notching/ripping | **48** | | **843.5 = 70.291667 ft** |

Reserve **1/8 inch at each stock end**, including the end-trimming cuts, leaving **95.75 inches usable per 96-inch board**. Charge another **1/8 inch per released blank** for crosscut kerf, including the final blank in each pattern.

| Stock boards | Cut pattern per board | Blank length + crosscut kerf | Usable remainder per board |
| --- | --- | ---: | ---: |
| S1–S4: 4 boards | 3 A + 3 C | 93.75 | 2 |
| S5–S8: 4 boards | 4 B + 1 C | 95.625 | 0.125 |
| S9: 1 board | 4 B | 92 | 3.75 |

This produces exactly 12 A, 20 B, and 16 C blanks. Nine stock boards supply 864 inches: 843.5 in blanks + 6 in crosscut kerf + 2.25 in stock-end allowance + 12.25 in remaining offcuts. **Eight boards provide only 768 inches and cannot supply this blank schedule even with zero kerf.** Nine is the minimum for this defined schedule; a tenth board is an optional damage/mistake spare, not a required installed-material item. Do not substitute an area-only board count for this allocation.

### US07 roof: order 1 × US07-16-G9-EB

The roof footprint is 27.5 × 22.875. The base layout keeps the planned **3/16-inch gaps**, with **five equal-width courses**, rather than four full-width boards followed by a narrow strip:

`course width = (22.875 - 4 × 0.1875) / 5 = 4.425 inches`.

Crosscut **five 27.5-inch blanks** from the single 192-inch board, then rip each to 4.425 inches. Where both ends are restrained, finish the length to **27.375 inches**, leaving 1/16 inch at each end within the 27.5-inch footprint. Starting Y coordinates are 0, 4.6125, 9.225, 13.8375, and 18.45. Each course is wide enough for two screw lines inset 1.5 inches from its side edges.

- One 16-foot stock board: `5 × (27.5 + 0.125) = 138.125` inches of the 191.75 usable after stock-end trimming; 53.625 inches remain before any further offcut use.
- Alternative eight-foot stock: buy **two**, cut three blanks from the first and two from the second. Their usable remainders are 12.875 and 40.5 inches respectively. These replace the one 16-foot item.
- Alternative four-course layout discussed in chat: retain four full 138 mm widths and set the three gaps to `(22.875 - 4 × 138 / 25.4) / 3 = 0.380906 inches`, approximately 3/8 inch. Exact 3/8-inch gaps apply to the rounded 5 7/16-inch width. This option still requires one 16-foot board or two 8-foot boards. It is an alternative to the base 3/16-inch-gap layout, not an additional purchase.
- Reserve **30 roof face screws**: five courses × three support lines × two screws. Resolve individual screw locations around the existing gusset plates and shim interruptions; do not drill through plate hardware or place a fastener over an unsupported gap.

### Mounting, backing, and trim allocation

The following defines the attachment provision used for the accessory order. It is not a full exterior furring grid. Coordinates refer to the existing frame faces; new backing is flush with those faces and fitted around existing members and equipment.

| Face | Clip/support axes along that face | Allocation |
| --- | --- | --- |
| Front | X = 1.75, 10.8, 13.75, 16.7, 25.75 | Existing end posts; two light-opening jamb supports and split center backing. Omit the center clip at the course-8 seam inside the light cutout. |
| Left | Y = 1.75, 11.4375, 21.125 | Existing end posts and added center backing between rails. |
| Right | Y = 1.75, 11.9375, 15.725, 21.125 | Existing posts/center rail, center extensions, and backing beside the outlet opening. |
| Rear | X = 1.75, 25.75 on wings; X = 13.75 on headers | Existing posts support the complete short wings. Add header backing above the opening. |

Nine inter-course clip rows give front `9 × 5 - 1 = 44`, left `9 × 3 = 27`, right `9 × 4 = 36`, and rear `8 × 2 + 3 = 19`: **126 AW08 clips**. One lock per physical lower-course board gives `9 + 9 + 9 + (8 × 2 + 1) = 44` locking screws. The top course has **15 T-7/face-fixing stations** (`5 + 3 + 4 + 3`). The starter courses have **14 attachment stations** (`5 + 3 + 4 + 2`). Where an opening prevents a center lock, use the nearest supported intact clip on that same physical board; retain only one fixed point.

The added wood blank schedule is below. Use dry pressure-treated nominal 2×4 stock, actual 1.5 × 3.5. Segment or notch the new backing to fit the existing rails; do not move the wall face outward to avoid a conflict.

| New wood use | Quantity × blank length | Detail |
| --- | --- | --- |
| Front bottom rail | 1 × 20.5 | Between posts, Z = 2..3.5; supports the front backing and starter. |
| Front light jamb backing | 2 × 44.625 | Z = 3.5..48.125; use the 1.5-inch face beside the opening. |
| Front split center backing | 1 × 36.925; 1 × 3.3 | Z = 3.5..40.425 and 44.825..48.125, avoiding the box opening. |
| Front light horizontal backing | 2 × 4.4 | Header/sill support between jambs; fit around existing backers. |
| Left center backing | 1 each × 3.25, 5.5, 29.75, 1.125 | Fill Z gaps 2..5.25, 6.75..12.25, 13.75..43.5, and 45..46.125. |
| Right center extensions | 1 each × 3.25, 5.5, 1.125 | Reuse the existing middle center rail. |
| Right outlet-side backing | 1 each × 3.25, 5.5, 29.75, 1.125 | At Y = 15.725, outside the cutout. |
| Right outlet horizontal backing | 2 × 2.9 | Fit between the jamb and rear post beside the 2.8-inch opening. |
| Rear header filler | 1 × 20.5 | Rip to 1.125-inch height, Z = 47..48.125, below the existing rear top brace. |
| Roof center support | 1 × 15.875 | Flat 2×4 between front/rear top braces, X = 12..15.5. House its top 0.75 inch where it crosses the existing 1×6 diagonal, leaving that diagonal intact. |
| Roof center shim donor | 1 × 15.875 | Resaw to 0.25 × 3.5; reuse the four existing perimeter shims. |

These 23 blanks total **305.95 inches**. Order **4 nominal 2×4×8-foot pieces**. A feasible allocation, with the same 95.75-inch usable stock and 1/8-inch-per-blank kerf, is:

| Stock | Blank lengths | Length including crosscut kerf |
| --- | --- | ---: |
| W1 | 44.625, 44.625, 5.5 | 95.125 |
| W2 | 36.925, 29.75, 20.5, 5.5, 1.125, 1.125 | 95.675 |
| W3 | 29.75, 20.5, 15.875, 5.5, 4.4, 4.4, 3.3, 3.25, 3.25, 3.25 | 94.725 |
| W4 | 15.875, 2.9, 2.9, 1.125 | 23.3 |

Order **2 US46-8-EB corner trims** for four 47.625-inch blanks. Each stock yields two (`2 × 47.625 + 2 × 0.125 = 95.5`, within 95.75 usable). They run from Z = 2 to the post top at 49.625; the top US44 caps overlap their upper ends. Do not extend all four corner blanks to the siding's higher top datum, which would require four 8-foot sticks instead of two.

Order **4 US44-8-EB F-trims** using the following deliberately oversized miter/fitting blanks. Finish miters from the actual corner/edge profiles; preserve the clear light, outlet, and tambour openings. The larger blanks accommodate trim coverage and do not imply widening those openings.

| Stock | Application / blank cuts | Length including crosscut kerf |
| --- | --- | ---: |
| F1 | Two tambour jamb blanks, 47 + 47 | 94.25 |
| F2 | Front/rear top caps, 31.5 + 31.5; tambour head, 24.5 | 87.875 |
| F3 | Side top caps, 26.875 + 26.875; four light trim blanks, 4 × 8.4 | 88.1 |
| F4 | Outlet trim blanks, 2 × 9.7 + 2 × 6.8 | 33.5 |

The 15 F-trim blanks total 301.85 inches before kerf, so three 96-inch sticks cannot supply this allocation. The 47-inch jamb blanks and 24.5-inch head blank include miter allowances; they are not a reduction of the 45-inch-high, 20.5-inch-wide clear tambour opening. Check that the rear corner and opening trim profiles fit on the 3.5-inch wings without obstructing the tracks.

### Wall and roof purchase BOM

| Material / product | Required or allocated use | Quantity to obtain |
| --- | --- | --- |
| US09-8-EB siding, 96-inch stock | 48 full-profile blanks in S1–S9 | **9 boards** |
| US07-16-G9-EB decking, 192-inch stock | Five roof blanks, five balanced rip courses | **1 board** |
| US07-8-G9-EB alternative | Replaces the 16-foot board | **2 boards instead of 1 × 16-foot** |
| US46-8-EB corner trim | Four corner blanks | **2 sticks** |
| US44-8-EB F-trim | Fifteen cap/opening blanks | **4 sticks** |
| AW02 aluminum starter, 1 m / approximately 39.37 inches | Front 27.5; left/right 22.875 each; rear 3.5 each | **3 strips**; put both rear pieces with the front cut |
| AW08 siding clips | 126 allocated; [manufacturer chart](https://www.newtechwood.com/pdf/US09-All-Weather-Siding-Calc-v20230607.pdf) specifies 90 per bag | **2 bags / 180 clips**, leaving 54 |
| T-7 rubber stoppers | 15 top-course stations; same chart specifies 50 per bag | **1 bag / 50**, leaving 35 |
| SS304 #8 × 1-inch pan-head screws | 126 clips + 14 starter stations + 15 T-7 supports + 4 new shim fixings = 159 | **175 screws** (7 × 25-packs) |
| NewTechWood AW08-SCREW-100 set | 15 top-board fixings + 56 trim-fixing allowance = 71 #8 × 1 1/4-inch screws; includes 10 #6 locking screws | **1 set / 100 #8 screws + 10 #6 screws** |
| SS304 #6 × 1 1/4-inch locking screws | 44 board locks, less 10 supplied in the AW08 screw set | **1 × 100-pack** |
| Stainless composite decking screws, approximately #10 × 2 1/2 inches, black heads | 30 roof face screws; use a product intended for composite, such as the guide's recommended Cap-Tor xd family | **1 box of 100** |
| PT nominal 2×4×8-foot stock | W1–W4 backing, roof support, shim donor | **4 pieces** |
| Corrosion-resistant structural wood screws, 2 1/2 inches | **100-screw connection allowance**, not a calculated joint schedule | **100 screws** |
| Corrosion-resistant structural wood screws, 5 inches | Roof support end-connection provision: two per end | **4 screws** (buy a 12-pack) |
| Full exterior furring grid, wall sheathing, insulation, weather barrier | Not selected for this open-frame base arrangement | **0** |
| Existing perimeter roof shims, main frame, gussets, electrical equipment | Reuse; do not repurchase in this refactor BOM | **Existing items** |

The trim-fixing allowance is 24 corner-trim screws (three per leg per corner), 6 screws total across the two existing tambour jambs, 2 at its head, 8 top-cap screws, and 16 light/outlet trim screws. These fasteners support siding trim around the existing opening; the tambour door and slats are unchanged. Composite face holes must allow movement. The backing connection allowance is deliberately identified as an allowance: final joint attachment and gusset/track clearance must be resolved in the model before issuing construction drawings. Do not present these allowances as verified structural connection counts or assume that the smallest blocks accept four screws each.

The allocated clip, stopper, and screw counts follow the explicit support/course schedule above. Suppress intersections inside openings, rather than adding a fastener through a hole; reconcile the final model's hardware against this schedule. Supplier packaging of loose screws can vary: the quantities above are the planned purchase amounts, not unverified retailer pack SKUs.

### Cost basis

Prices below are current online examples checked 2026-10-19, before tax and delivery. Home Depot notes that local prices can vary. The siding and roof **board-only subtotal is $490.12**: `9 × $43.39 + 1 × $99.61`. The complete siding-and-roof material takeoff is **about $1,203.01**, using the purchase packs and example fasteners below. This includes siding, roof, trims, siding accessories, backing stock, and roof support fasteners. It excludes the reused enclosure/frame/electrical equipment, labor, tax, delivery, optional furring, and a damage spare. The structural screw counts are allowances, pending final connection details. The tambour door and slats remain existing parts and are not included.

| Purchase group | Price basis | Subtotal |
| --- | --- | ---: |
| US09 wall boards | 9 × $43.39 ([Home Depot](https://www.homedepot.com/p/332417145)) | $390.51 |
| US07 roof board | 1 × $99.61 ([Lowe's listing](https://www.lowes.com/pd/NewTechWood-Cortes-PLUS-0-88-in-x-5-43-in-x-16-ft-Rustic-and-Wood-Grain-Indian-Ebony-Composite-Decking-Board/5016446863); user-provided Home Depot price is the same) | $99.61 |
| US46 corner trim | 2 × $51.69 ([Home Depot listing](https://www.homedepot.com/b/Building-Materials-Siding-Siding-Trim/NewTechWood/Indian-Ebony/Outside-Corner-Trim/N-5yc1vZaq0nZbzgZ1z1ykuoZ1z25gvn)) | $103.38 |
| US44 F-trim | 4 × $51.69 ([Home Depot listing](https://www.homedepot.com/b/Building-Materials-Siding-Siding-Trim/NewTechWood/Indian-Ebony/N-5yc1vZaq0nZbzgZ1z1ykuo)) | $206.76 |
| AW02 starter strips | 3 × $15.09 ([Home Depot](https://www.homedepot.com/p/341585085)) | $45.27 |
| AW08 clips | 2 × $64.40 ([Home Depot listing](https://www.homedepot.com/b/Building-Materials-Siding/NewTechWood/Fastener/N-5yc1vZaripZbzgZ1z1tnvx)) | $128.80 |
| T-7 stoppers | 1 × $14.61 ([Home Depot listing](https://www.homedepot.com/b/Building-Materials-Siding/NewTechWood/Fastener/N-5yc1vZaripZbzgZ1z1tnvx)) | $14.61 |
| #8 × 1-inch stainless pan-head screws | 7 × 25 at $6.87; 175 purchased for 159 allocated ([Home Depot](https://www.homedepot.com/p/317479208)) | $48.09 |
| AW08-SCREW-100 siding screw set | 1 set of 100 #8 × 1 1/4-inch plus 10 #6 × 1 1/4-inch screws ([Home Depot](https://www.homedepot.com/p/340751785)) | $40.50 |
| Additional #6 × 1 1/4-inch stainless locking screws | 1 × 100 at $15.95 ([McFeely's](https://www.mcfeelys.com/6-x-1-1-4-in-bugle-head-self-drilling-305-ss-square.html)); together with the set above, more than the 44 allocated locks | $15.95 |
| Roof composite screws | 1 × 100 black stainless NewTechWood screws, $40.31 ([Home Depot listing](https://www.homedepot.com/b/Hardware-Fasteners-Screws-Deck-Screws-Composite-Deck-Screws/Black/10/2-1-2-in/N-5yc1vZ2fkpe6aZ1z0sg0yZ1z0sg11Z1z1ymgp)) | $40.31 |
| PT nominal 2×4×8 stock | 4 × $4.88 ([Home Depot listing](https://www.homedepot.com/b/Lumber-Composites-Pressure-Treated-Lumber/2-in-x-4-in/N-5yc1vZc3srZ1z1c7kp)) | $19.52 |
| 2 1/2-inch structural screw allowance | 1 × 100-pack at $22.78 ([Home Depot listing](https://www.homedepot.com/b/Hardware-Fasteners-Screws/Exterior/100/2-1-2-in/N-5yc1vZc2b0Z1z0sg0yZ1z1415qZ1z17e31)) | $22.78 |
| 5-inch structural screws | 1 × 12-pack at $26.92; four allocated ([Home Depot listing](https://www.homedepot.com/b/Hardware-Fasteners-Screws/Exterior/5-in/N-5yc1vZc2b0Z1z0sg05Z1z17e31)) | $26.92 |
| **Total siding-and-roof takeoff** |  | **$1,203.01** |

The 8-foot roof-board alternative costs `2 × $64.22 = $128.44`, which is $28.83 above the single 16-foot board. An optional tenth US09 damage spare adds $43.39. These alternatives are not included in the $1,203.01 total.

## Public Interfaces and Outputs

- Add explicit wall-cladding and roof-decking product-spec types while keeping the existing CSV/JSON column schemas stable.
- Generate distinct BOM lines for US09 wall boards, US07 roof boards, system trims/hardware, flush backing, and optional furring. Record installed counts, purchase quantities, optional spares, and connection allowances separately.
- Update `BUILD_STEPS.md` so product links, quantities, and installation sequence match the cladding and roof model. Leave `TAMBOUR_DOOR.md` and the existing tambour assembly unchanged.

## Test Plan

- Assert US09's overall profile and installed pitch separately, ten wall courses, both rear header blanks, 48 wall blanks, and the nine-board S1–S9 allocation including kerf/end trimming. Correct the stale 870 3/4-inch baseline in `BUILD_STEPS.md`; the existing unrefactored default model currently reports 916 1/4 inches combined, including roof boards.
- Assert exact product dimensions, colors, SKUs, 96-inch US09 stock, 192-inch primary US07 stock, and the mutually exclusive two-board 96-inch roof alternative. Check every stock pattern above against its usable length.
- Verify every wall board is supported at no more than 16-inch centers, the base layout has zero blanket exterior furring, every clip/trim is counted, wall openings retain their required clearances, and electrical fixtures terminate at the new finished plane.
- Reconcile the 126 AW08 clips, 44 locks, 15 top fixing stations, 14 starter stations, 30 roof screws, wood blank schedule, and trim cap overlap against the implemented geometry. Resolve backing joints before declaring the full cladding and roof construction BOM final.
- Verify roof board gaps, center support, maximum span, fastener locations, clearance to the existing tambour, gusset clearance, and configurable enclosure sizes.
- Run the complete test suite and a non-deploying build; inspect generated OpenSCAD, BOM, cut lists, shopping lists, and tambour manifests for internal consistency.

## Assumptions

- Wall boards remain horizontal. Roof boards keep the 27.5-inch run along X, with courses distributed across the 22.875-inch Y dimension; the earlier phrase "front-to-rear" did not accurately describe the model axes.
- Base procurement is nine US09-8-EB boards and one US07-16-G9-EB board. Optional spares and the two-board US07-8 alternative are separate choices.
- The base roof uses five balanced 4.425-inch rip widths at 3/16-inch gaps. Four full-width courses at approximately 3/8-inch gaps remain an alternative.
- Installation temperature is 50°F; short enclosure boards use at least 1/16-inch clearance at restrained ends.
- US09 trim is matching Indian Ebony.
- The roof decking is a ventilated/draining cover, not a waterproof roof membrane.
