# Tambour 1.5-Inch Slat Clearance Analysis

## Conclusion

The modeled 1.5-inch tambour envelope clears the fixed front framing,
street-light backers, revised charger-feed conduit, and removable plywood
ceiling by at least the intended 1/4 inch. The model renders the actual
1/2-inch wooden slat and independently regression-tests the 1 1/2-inch complete
hardware envelope through the front straight run and bend.

The production channel clearance, printed-track fasteners, slat-end clearance,
joint clips, and loading section remain prototype-controlled. The rendered
charger cord is illustrative
and is not treated as a hard clearance envelope; the plywood ceiling guards the
overhead curtain from hands and the cord.

## Resolved geometry

| Region or object | Result |
| --- | ---: |
| Perimeter top braces | 0.25-inch clearance |
| Shallow top diagonal | Approximately 1-inch clearance |
| Lowered `rail_ft` and front bend | At least 0.25-inch modeled clearance |
| Front street-light backers | 0.45-inch planar clearance |
| Charger-riser feed | Clears below or behind the front curtain |
| Plywood ceiling | 0.25 inch below the horizontal curtain envelope |
| Rear trim and lateral slat ends | Prototype-controlled guide detail |

### Front guide and street-light backers

The slat center path remains at `y = 5.0`, while the guide centerline is
modeled 3/8 inch inward at `y = 5.375`. The 1.5-inch envelope still reaches
forward to `y = 4.25`; the backers end at `y = 3.80`:

```text
4.25 - 3.80 = 0.45 inch
```

The left and right vertical support rails moved with the guide and now occupy
`y = 4.75` to `y = 6.25`.

### Structural front header

`rail_ft` remains a 2x4 but moved down to `z = 41.0` through `z = 42.5`.
The front center rail bears against its underside. Two short vertical 2x4
blocks provide full-depth attachment faces at the header ends and bear against
the undersides of the upper side rails.

The swept-envelope regression follows the resolved piecewise track, offsets
the center of the 3/4-inch-high slat path 3/8 inch outward, and checks an
independent 1 1/2-inch complete hardware envelope over the header's Y interval.
The resulting clearance exceeds
the required 1/4 inch, including through the 2 5/8-inch-radius front bend.

This is a geometry result, not a structural rating. The header, blocks, center
rail, fasteners, and connections must be selected for the charger dead load
and repeated lateral and torsional loading from wrapping the cord and handling
the plug.

### Charger-feed conduit

The charger-riser arrangement aligns the 1 1/4-inch ground riser and T body
with the charger's conduit-port X coordinate. Its complete horizontal branch
runs 1/4 inch above `rail_fb` to the rear of the junction box, while the
reduced 1-inch feed rises directly from the T body to the charger. Both feeds
remain below or behind the front curtain envelope.

The #6 charger group bypasses the junction box through the T body. The box's
remaining #12 groups require 18 cubic inches against its modeled 49-cubic-inch
marking, leaving 31 cubic inches.

### Removable plywood ceiling

The modeled exterior-plywood panel occupies:

```text
x = 3.5 to 24.0 inches
y = 8.75 to 17.625 inches
z = 43.25 to 43.50 inches
```

Its top is 1/4 inch below the horizontal curtain envelope at `z = 43.75`.
Its Y ends are inset 3/4 inch from both bend tangencies. Mount it on independent
removable retainers so track inspection, cleaning, and curtain removal remain
possible.

## Rear trim and slat ends

“Rear trim and slat ends” refers to the left and right ends of each slat where
the curtain passes through the rear opening, not the trailing end of the
curtain. The simplified model draws each slat to both track centerlines, while
the rear opening angles reach those same lateral boundaries. A production
slat instead terminates with running clearance inside the printed side-opening
channel, with the trim concealing the interface.

Because the accepted printed clearance, end engagement, and installed track
spacing remain prototype-controlled, this interface must be approved on the
full-width test frame.

## Acceptance requirements

1. Build the guide paths from one full-size template using the modeled
   front `y = 5.375`, top `z = 44.125`, rear `y = 21.0`, and 2 5/8-inch-radius
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
