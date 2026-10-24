# US09 enclosure siding and roof cover

The enclosure uses horizontal NewTechWood US09, installed **from the top
downward**. Layout, cut blanks, hardware and corner views are generated with
`uv run build.py --no-deploy`. Dimensions are inches.

The controlling wall reference is the supplied
[horizontal installation guide](ALL_WEATHER_Siding_Horizontal_Installation_Guide.pdf)
(09.16.25 US). Supporting references are the manufacturer's
[US09 drawing](https://www.newtechwood.com/pdf/5467-014.pdf),
[US46 drawing](https://www.newtechwood.com/pdf/5467-017.pdf),
[product dimensions](https://www.newtechwood.com/siding/all-weather/), and
[ceiling guide](https://www.newtechwood.com/pdf/All_Weather_Siding_Ceiling_Installation_Guide.pdf).
The ceiling guide informs the 12-inch maximum roof support spacing; it does
not establish suitability or load capacity for an exposed roof.

## Dimensions and fabrication status

US09 is modeled at 142 mm overall width and 1/2-inch thickness. These are
separate from the **provisional 130 mm installed course pitch** and the
**provisional 5/16-inch clip stand-off**. Measure two engaged production boards
and actual clips before cutting; change `course_pitch` and `clip_standoff` in
`US09Siding` if the samples differ. The model uses simplified mating edge
rebates, clip envelopes and trim envelopes, rather than machining profiles.
In particular, the top and bottom rebates illustrate engagement without
claiming an exact groove or clip cross-section.
The preview leaves 0.002 inch between mating rebate faces and extends rebate
cutters beyond the board edges to prevent flickering at highlighted course
borders. This visualization clearance does not change stock dimensions,
course pitch, or fabrication allowances.

The defaults give ten wall courses. Solid-wall top boards retain their full
profile height. The rear top board is one physical board with an access notch;
lower rear wings are separate physical offcuts. Openings split rendered solids
without multiplying the stock-board count.

The wall top is z = 50.125. Existing perimeter shims and the added diagonal
shim put the roof support plane at z = 49.875. Including clip stand-off and
US09 thickness, the finished roof board top is z = 50.6875; US20 adds its
schematic 0.22-inch thickness above that. The finished wall face is 13/16 inch
outside framing, so the front face is y = -0.8125. Fixture, numeral and outlet
positions follow that face; US09 thickness alone is not the mounting offset.

The 1/8-inch end and trim gaps are a conservative modeled allowance for pieces
up to 8 feet, installed at 32 F or warmer. Check page 11 of the supplied guide
against actual installation temperature and stock lengths. The model rejects
layouts beyond this length envelope. Use one fixed point per physical board
or trim piece; additional face fasteners use predrilled sliding holes. Page 5
specifies hole diameter relative to screw thread and head diameters. Do not
clamp a sliding hole tightly enough to prevent movement.

## Downward wall installation

This is a custom sequence, distinct from the guide's illustrated upward
sequence. The physical dry fit has **not been performed**.

1. Install the framing and interior systems, including fixture backing. Add
   the flush front/left backing, right-side extensions, opening backing,
   roof backing and shims. Existing rails and posts fill the interruptions
   between new backing segments. Attach each segment positively to framing
   using suitable stainless angles/plates and structural screws; field-fit
   the small blocks and their hardware. Preserve gusset and screw-head gaps.
2. Pre-position any US46/US44 profile that cannot be inserted afterward.
   Keep the rear access opening available. Install mesh behind the lower
   siding before that space becomes inaccessible.
3. Make a two-course sample on representative backing. Keep the boards in
   their intended exterior orientation. Test offering the AW08 supporting
   clips from below with the flange accessible in the unfilled course space.
   Confirm full groove engagement, screw-driver access, midpoint locking,
   fit of the next lower board, and removal of the temporary supports.
   Do not invert the boards to obtain screw access. The reverse-access AW08
   envelopes in the model are an installation hypothesis, not proof of fit.
   If the sample cannot be assembled this way, revise the clip/support detail
   before installation; the documented direction remains downward.
4. Hold the full-height top board level with padded props or clamps attached
   to framing. Use enough support to prevent sag or rotation. Engage and
   fasten its supporting AW08s from the open space below. Secure its free
   top edge over T-7 spacers. Lock only one point near the board midpoint;
   keep other clips unlocked and other face holes free to slide.
5. Engage the next board with the installed course, support it temporarily,
   then fasten its supporting clips from below. Remove temporary supports
   only after the permanent connections retain the board. Continue downward.
   The build-step viewer follows the same order, one wall course per step.
6. At the rear top notch, the single fixed point is the header face screw
   into the rear brace; the wing clips remain unlocked. Each separate lower
   rear wing gets its own single fixed point. Do not lock rendering fragments
   as though they were separate physical boards.
7. Scribe the bottom profile to surveyed grade plus 3/4 inch. Check actual
   grade along the full wall, including intervening high spots. Use T-7-backed
   face screws where the rip removes the clip groove; fix one point and
   provide sliding holes elsewhere. Do not reverse the board or the tongue
   orientation at the bottom. No AW02 starter is counted: this termination
   uses backed face fastening instead of an intact starter groove.

Supports are at most 16 inches apart on the walls. Additional backing near the
outlet supports the notched courses. The substrate remains open framing;
there is no added layer of furring or sheathing. Keep the open spaces behind
and between framing unobstructed so ventilation and drainage remain available.
The mesh skirt does not turn the rear access opening into an animal-proof door.

## Roof and upper corners

Roof boards run along X and courses progress along Y. They sit above the
existing perimeter supports, added actual 1-inch backing strips, and a
1/4-inch shim on the diagonal. Added strips stop at the diagonal rather than
intersecting it. This is intermittent lumber support, with spans no greater
than 12 inches along the boards. Fasten the first free edge over T-7 spacers,
use AW08s on intact grooves and face fastening over T-7 at the ripped final
edge. Keep one fixed point per roof board and accommodate movement elsewhere.
The trim carries no roof weight. This level cover allows leakage; snow, uplift,
ponding and exposed-roof load capacity remain unverified.

Vertical US46 corner trims stop beneath the US20 roof-edge faces. US20's
horizontal legs cover the roof edges and meet in 45-degree plan miters with
movement gaps. Its vertical legs overlap the wall tops. This staggered
junction avoids a three-way compound miter and uses no unsupported corner cap.
The vertical corner trims retain 3/4-inch grade clearance at their own corners.
US44 frames the rear access opening; each jamb follows its local ground height.

The front US20 face needs a local relief around the Brook's mounting body:
6 1/4 inches wide, to 1/8 inch above its modeled top. Check the physical fixture
before cutting. Fasten the remaining vertical leg on either side into the
front brace; do not put a screw in the relieved zone. Use #8 x 2-1/2-inch trim
screws where passing through trim, board and stand-off into framing, subject
to field verification of penetration. #8 x 1-1/4-inch face screws are for the
board/T-7 connection, not this thicker trim stack. Seal fixture penetrations
without sealing shut the board/trim movement gaps or drainage paths.

## Generated review files

- `output/model.scad`: full enclosure and downward installation steps.
- `output/siding_corner_front_left.scad`, `siding_corner_front_right.scad`,
  `siding_corner_rear_left.scad`, `siding_corner_rear_right.scad`: cropped,
  enlarged-ready views of each custom roof/wall junction.
- `output/siding_cut_list.csv` and `.json`: one row per physical board blank,
  backing cut and trim cut; scribe coordinates are world along-wall/Z pairs.
- `output/siding_installation.json`: attachment positions, fixed points,
  course order and explicit prototype assumptions.
- Shared BOM, cut and shopping lists include the new materials and hardware.
  Stock quantities include a 1/8-inch kerf allowance per cut. They are calculated
  minimums with offcut reuse, without a damage/contingency allowance. Kerf is
  included in the allowance even for the last cut on a stock piece.

The hardware cloth has 1/4-inch openings, a 2-inch cut height and 2-inch joint
overlaps. Fix it to framing independently of the boards. The nominal 3/4-inch
grade gap remains under both the siding and the trim.
