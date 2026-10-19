# Tambour 1.5-Inch Slat Clearance Analysis

## Conclusion

The modeled tambour clears the fixed framing, siding, street-light backers,
revised charger-feed conduit, and removable plywood ceiling throughout a dense
sweep of the complete track. The check uses the actual asymmetric envelope:
7/8 inch outward from the track centerline for the slat and handle, and
5/16 inch inward for the slat, webbing, reinforcement, and fastener heads. The
1 3/16-inch actual stack remains inside the 1 1/2-inch maximum envelope.

The production channel clearance, printed-track fasteners, slat-end clearance,
joint clips, loading section, and exact inward fastener stack remain
prototype-controlled. The rendered
charger cord is illustrative
and is not treated as a hard clearance envelope; the plywood ceiling guards the
overhead curtain from hands and the cord.

## Resolved geometry

| Region or object | Result |
| --- | ---: |
| Perimeter top braces | 0.25-inch clearance |
| Shallow top diagonal | Approximately 1-inch clearance |
| Lowered `rail_ft` and front bend | At least 0.25-inch modeled clearance |
| Front street-light backers | 0.325-inch planar clearance |
| Charger-riser feed | Clears below or behind the front curtain |
| Plywood ceiling | 0.25 inch below the horizontal curtain envelope |
| Rear trim and lateral slat ends | Prototype-controlled guide detail |

### Front guide and street-light backers

The slat and guide share the groove centerline at `y = 5.0`. The minimum safe
datum from the fixed street-light backers is `y = 4.925`; it is rounded
rearward to the next 1/8 inch for construction. The outward handle envelope
therefore reaches forward to `y = 4.125`, while the backers end at `y = 3.80`:

```text
4.125 - 3.80 = 0.325 inch
```

The deferred left and right vertical support rails move with the guide and occupy
`y = 4.25` to `y = 5.75`, with flush recessed 1 3/4-inch plywood
facings extending from `y = 4.125` to `y = 5.875`. The 3/4-inch plywood bend
backers extend from `y = 5.625` rearward to `y = 7.375` and occupy `z = 45` to `z = 46.125`, above `rail_lt` and
`rail_rt`, so the complete printed flange remains supported without overlapping
the receiver rails.

### Structural front header

`rail_ft` remains a 2x4 at `z = 43.5` through `z = 45`.
The front center rail bears against its underside. The header spans directly
between `rail_lt` and `rail_rt`, which provide its full-depth end attachment
faces; the former vertical header-support blocks are not used. The side receiver
rails now connect directly between the front and back posts. The deferred
front guide uprights terminate beneath these rails, with separate blocks above
them. Split, flush plywood facings preserve the track datum without notching
the structural receiver rails. See `TAMBOUR_DOOR.md` for the future support detail.

The regression follows the resolved piecewise track and checks both the full
7/8-inch outward handle envelope and the full 5/16-inch inward slat/hardware
envelope over the header's Y interval and through both bends. Separate dense
samples of the complete printed-track cross section prove backing support and
absence of lumber penetration through the 2 5/8-inch-radius front bend.

This is a geometry result, not a structural rating. The header, blocks, center
rail, fasteners, and connections must be selected for the charger dead load
and repeated lateral and torsional loading from wrapping the cord and handling
the plug.

### Charger-feed conduit

The charger-riser arrangement uses a 4×4×2-inch pull box in place of the
IPEX STB40S. A 1 1/4-inch bottom male fitting retains the ground riser, a
1-inch top male fitting feeds the charger, and a 3/4-inch back male fitting
feeds the 4×4×4-inch power junction. All conduit entries through these boxes
use cut holes, exterior sealing washers, and interior locknuts. Both feeds
remain below or behind the front curtain envelope.

The #6 charger group bypasses the power junction through the shallow pull box.
The power junction's remaining #12 groups require 18 cubic inches against its
modeled 49-cubic-inch marking, leaving 31 cubic inches.

### Removable plywood ceiling

The modeled exterior-plywood panel occupies:

```text
x = 3.5 to 24.0 inches
y = 10.6875 to 18.625 inches
z = 43.25 to 43.50 inches
```

Its top is 9/16 inch below the inward horizontal curtain envelope at
`44.375 - 0.3125 = 44.0625` inches.
Its rear edge is inset 3/4 inch from the rear bend tangency; its front edge
aligns with the positive-Y face of `rail_ft`. Mount it on independent removable
retainers so track inspection, cleaning, and curtain removal remain possible.

## Rear trim and slat ends

“Rear trim and slat ends” refers to the left and right ends of each slat where
the curtain passes through the rear opening, not the trailing end of the
curtain. The model now shortens each slat to the nominal channel-bottom spacing minus
1/16-inch total end clearance. Production slats use the minimum measured
channel-bottom spacing after the backing and tracks are installed. The 40 mm
walls give 35.2 mm usable depth and require at least 1 3/4-inch-wide backing
for the 39.7 mm footprint. See `TAMBOUR_DOOR.md` for the 1-inch variation and
full sideways capture check.

Because the accepted printed clearance, end engagement, and installed track
spacing remain prototype-controlled, this interface must be approved on the
full-width test frame.

## Acceptance requirements

1. Build the guide paths from one full-size template using the modeled
   front `y = 5.0`, top `z = 44.375`, rear `y = 22.0`, and 2 5/8-inch-radius
   track datums.
2. Verify the header load path and connections for the charger and holster's
   dead and dynamic loads.
3. Prototype the printed channel, clearance coupons, slat ends, pulls,
   fasteners, loading section,
   and removable ceiling retainers.
4. Cycle the curtain through full travel before and after installing the
   ceiling, conduit, fixed cables, siding, and trim.
5. Record the production dimensions and revise the model if the approved
   prototype differs from the modeled maximum envelope.
