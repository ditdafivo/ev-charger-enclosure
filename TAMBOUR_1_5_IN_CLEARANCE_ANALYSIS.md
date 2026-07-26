# Tambour 1.5-Inch Slat Clearance Analysis

## Conclusion

The modeled 1.5-inch tambour envelope clears the fixed front framing,
street-light backers, revised charger-feed conduit, and removable plywood
ceiling by at least the intended 1/4 inch. The model now renders the actual
1.5-inch slat depth and regression-tests the front straight run and bend.

The production groove, liner, slat-end clearance, fasteners, and loading
section remain prototype-controlled. The rendered charger cord is illustrative
and is not treated as a hard clearance envelope; the plywood ceiling guards the
overhead curtain from hands and the cord.

## Resolved geometry

| Region or object | Result |
| --- | ---: |
| Perimeter top braces | 0.25-inch clearance |
| Shallow top diagonal | Approximately 1-inch clearance |
| Lowered `rail_ft` and front bend | At least 0.25-inch modeled clearance |
| Front street-light backers | 0.45-inch planar clearance |
| Junction-riser charger feed | Clears below or behind the front curtain |
| Plywood ceiling | 0.25 inch below the horizontal curtain envelope |
| Rear trim and lateral slat ends | Prototype-controlled guide detail |

### Front guide and street-light backers

The front guide centerline moved from `y = 3.75` to `y = 5.0`. A centered
1.5-inch envelope reaches forward to `y = 4.25`; the backers end at `y = 3.80`:

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

The swept-envelope regression follows the resolved piecewise track, orients a
1.5-by-0.9-inch slat to every sampled segment, and checks the lowest curtain
surface over the header's Y interval. The resulting clearance exceeds the
required 1/4 inch, including through the front bend.

This is a geometry result, not a structural rating. The header, blocks, center
rail, fasteners, and connections must be selected for the charger dead load
and repeated lateral and torsional loading from wrapping the cord and handling
the plug.

### Charger-feed conduit

The former direct spline rose through the relocated front curtain envelope.
It has been replaced by the junction-riser arrangement: a 1 1/4-inch rearward
feed leaves the junction box, enters an LB conduit body, reduces to 1 inch, and
rises near the charger's Y coordinate. The LB feed remains below the lower
front curtain endpoint, and the 1-inch rise remains behind the vertical
curtain with construction-tolerant clearance.

The junction box retains its 37-cubic-inch fill calculation with 12 cubic
inches of margin. The LB conduit body requires 20 cubic inches against its
modeled 32-cubic-inch marking, also leaving 12 cubic inches.

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
slat will instead terminate with running clearance inside a defined lined
groove, with the trim concealing the interface.

Because the groove cross-section, liner thickness, end clearance, and
fasteners are intentionally unspecified, this contact is excluded from the
solid-envelope assertion. It must be approved on the full-width prototype.

## Acceptance requirements

1. Build the guide paths from one full-size template using the modeled
   `y = 5.0`, `z = 44.5`, and 3-inch-radius datums.
2. Verify the header load path and connections for the charger and holster's
   dead and dynamic loads.
3. Prototype the groove, liner, slat ends, pulls, fasteners, loading section,
   and removable ceiling retainers.
4. Cycle the curtain through full travel before and after installing the
   ceiling, conduit, fixed cables, siding, and trim.
5. Record the production dimensions and revise the model if the approved
   prototype differs from the modeled maximum envelope.
