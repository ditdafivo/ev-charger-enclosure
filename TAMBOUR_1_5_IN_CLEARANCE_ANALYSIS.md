# Tambour 1.5-Inch Slat Clearance Analysis

## Question

Confirm clearance along the complete tambour-door path if the slat depth is
increased to `TAMBOUR_MAX_SLAT_DEPTH = 1.5` inches.

## Conclusion

Clearance is **not confirmed**. A 1.5-inch-deep slat intersects existing
framing along the current resolved path. The definite full-width conflicts are
the front transverse top rail (`rail_ft`) and the three front street-light
backers. Two electrical services also have negligible clearance, and the rear
trim/end-guide relationship cannot be approved from the current model because
the production track and slat-end profiles are intentionally unspecified.

The top perimeter bracing does clear the proposed envelope by the intended
1/4 inch, but the existing assertion checks only that local condition and does
not establish clearance along the rest of the path.

## Verification method

The check used the current default enclosure geometry and the resolved
tambour centerline, including both modeled 3-inch-radius bends. The resolved
path is approximately 85.04 inches long.

A single slat was swept over the complete path because every slat traverses
the same path during operation. The evaluated slat envelope was:

- 1.5 inches in the face-depth direction;
- 0.9 inch in the travel direction; and
- the complete modeled span between the left and right track centerlines.

At each position, the slat was oriented using the local path tangent, matching
the orientation used by `render_tambour_slat` in the generated OpenSCAD model.
The swept envelope was checked against framing, component bounding boxes,
siding and trim solids, conduit centerlines with their modeled outside
diameters, and cable centerlines with their modeled diameters.

This is a model-geometry check. It does not replace the required full-size
prototype and installed full-travel test.

## Results by path region

| Path region or object | Result |
| --- | ---: |
| Perimeter top braces | Passes with 0.25-inch clearance |
| Shallow top diagonal | Passes with approximately 1.0-inch clearance |
| Top/front bend at `rail_ft` | Collision: 0.50-inch overlap on the straight top run and approximately 0.56 inch at the bend |
| Front bend and vertical run through the street-light backers | Collision: approximately 0.80 to 0.85 inch |
| EV-charger cord near the top run | Approximately 0.003-inch clearance; effectively no construction tolerance |
| Charger-feed conduit near the lower front endpoint | Approximately 0.025-inch clearance |
| Rear trim and slat ends | Modeled overlap; actual result depends on the unspecified track groove and slat-end clearance |

### Top perimeter bracing

The top track centerline is at `z = 44.5` inches. A centered 1.5-inch envelope
therefore reaches:

```text
44.5 + 1.5 / 2 = 45.25 inches
```

The perimeter braces begin at `z = 45.5` inches, leaving the intended gap:

```text
45.5 - 45.25 = 0.25 inch
```

This is the condition currently covered by
`test_tambour_top_support_and_maximum_curtain_clear_bracing`.

### Front transverse top rail

`rail_ft` occupies approximately:

```text
y = 6.1875 to 9.6875 inches
z = 42.75 to 44.25 inches
```

On the horizontal top run, the 1.5-inch slat occupies:

```text
z = 43.75 to 45.25 inches
```

The resulting direct overlap is:

```text
44.25 - 43.75 = 0.50 inch
```

The locally rotated envelope reaches approximately 0.56 inch of penetration
while entering the front bend. This is a full-width framing conflict rather
than a track-end-detail ambiguity.

The currently rendered 0.75-inch slat also overlaps this rail:

```text
44.25 - (44.5 - 0.75 / 2) = 0.125 inch
```

### Front street-light backers

The three street-light backers span the door width and occupy:

```text
y = 2.30 to 3.80 inches
z = 33.0 to 43.5 inches
```

The current front vertical track centerline is `y = 3.75` inches. A 1.5-inch
slat centered on that line occupies:

```text
y = 3.00 to 4.50 inches
```

The straight-run overlap is therefore:

```text
3.80 - 3.00 = 0.80 inch
```

The rotated envelope reaches approximately 0.85 inch of penetration while
leaving the front bend. The three contiguous backers keep the path obstructed
from roughly `z = 43.5` down to `z = 32.6` as the slat travels.

The currently rendered 0.75-inch slat also overlaps these backers:

```text
3.80 - (3.75 - 0.75 / 2) = 0.425 inch
```

### Electrical services

The modeled EV-charger cord comes within approximately 0.003 inch of the
1.5-inch swept envelope near the top run. Although the sampled model does not
show a finite overlap, this is effectively zero clearance after accounting
for fabrication, installation, cable movement, or path tolerances.

The `power_ev_charger_feed` conduit comes within approximately 0.025 inch of
the envelope near the lower front endpoint. This likewise provides no useful
construction tolerance and must not be treated as confirmed clearance.

### Rear trim and guide ends

The rear siding-angle solids overlap the modeled slat at its lateral ends.
The model draws each slat all the way to the two track centerlines, while the
prototype guide explicitly leaves the groove cross-section, liner thickness,
slat-end clearance, and fastener detail undefined. Consequently, this
relationship cannot be approved or rejected solely from the rendered slat
solid. It must be resolved in the production track cross-section and verified
on the full-width prototype.

## Modeling inconsistencies

### The maximum-depth constant does not set the modeled slat depth

`TAMBOUR_MAX_SLAT_DEPTH` is currently used to lower the top support and track
assembly. The `tambours.add(...)` call does not pass `slat_depth`, so the door
continues to use the `TambourDoor` default of 0.75 inch.

Changing or retaining only:

```python
TAMBOUR_MAX_SLAT_DEPTH = 1.5
```

does not render or validate a 1.5-inch slat. The tambour instance would also
need to receive the intended depth, and a full-path clearance assertion would
need to evaluate its swept envelope.

### Documented and resolved path coordinates disagree

`TAMBOUR_DOOR.md` documents these endpoints:

```text
rear:  y = 29
front: y = 5.5
```

The current default build resolves them to approximately:

```text
rear:  y = 21.375
front: y = 3.75
```

The front discrepancy is particularly important because a centerline at
`y = 5.5` would place a 1.5-inch slat much farther from the street-light
backers than the current `y = 3.75` path. The intended construction datum must
be reconciled before a final clearance design is selected.

## Minimum geometric requirements

These values describe the minimum modeled movements needed to obtain a
1/4-inch nominal gap; they are not a complete redesign recommendation.

### Clearance below `rail_ft`

For a top centerline at `z = 44.5`, a 1.5-inch slat, and 1/4-inch clearance,
the top of `rail_ft` must be no higher than:

```text
44.5 - 1.5 / 2 - 0.25 = 43.5 inches
```

Its current top is `z = 44.25`, so it would need to move down by at least
0.75 inch or be reconfigured outside the swept path.

### Clearance from the street-light backers

With the current front centerline at `y = 3.75`, the backers must end no farther
rearward than:

```text
3.75 - 1.5 / 2 - 0.25 = 2.75 inches
```

Their current rear face is `y = 3.80`, requiring at least 1.05 inches of
separation through a backer change, a guide-path move, or a combination of
both.

Alternatively, retaining the current backer face at `y = 3.80` requires the
front guide centerline to be at least:

```text
3.80 + 1.5 / 2 + 0.25 = 4.80 inches
```

The documented `y = 5.5` centerline would satisfy this particular planar
condition with approximately 0.95 inch of clearance, but the bend, top rail,
services, trim, and track details would still require a complete recheck.

## Required follow-up before approval

1. Reconcile the documented and modeled rear/front track coordinates.
2. Decide whether the 1.5-inch value is a physical production slat depth or
   only a maximum envelope including pulls, backing, and reinforcement.
3. Reconfigure `rail_ft` or the guide path so their solids do not intersect.
4. Reconfigure the street-light backers or move the front guide path.
5. Increase clearance to the charger cord and charger-feed conduit to an
   approved construction-tolerant value.
6. Define and prototype the track groove, liner, slat-end clearance, trim
   interface, fasteners, and loading section.
7. Model the approved slat depth explicitly and add a swept full-path
   regression test covering framing, trim, components, conduit, and cables.
8. Repeat the installed full-travel acceptance test required by
   `TAMBOUR_DOOR.md` and `BUILD_STEPS.md`.

Until these conflicts and inconsistencies are resolved, a 1.5-inch tambour
slat or pull-slat envelope should not be approved for the current path.
