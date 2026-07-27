# Top-bracing build-sequence evaluation

## Question

Evaluate whether the simplified top bracing currently assigned to Build Step
12 can and should be moved to immediately after Build Step 2.

## Conclusion

Install the permanent top bracing directly after the posts, subject to approval
of the structural member and connection design described in
[`TOP_BRACING.md`](TOP_BRACING.md). The former conflict has been resolved by
lowering the tambour top supports and track centerline by 1/2 inch.

## Resolved geometry conflict

The modeled left and right top perimeter 2x4 braces occupy the following
vertical range:

```text
z = 45.50 to 47.00 inches
```

The former left and right tambour top-support 2x4 rails occupied:

```text
z = 44.25 to 45.75 inches
```

Each perimeter brace and corresponding tambour support spans between the same
two posts and occupies the same plan footprint. Their former vertical ranges
overlapped by 1/4 inch:

```text
45.75 - 45.50 = 0.25 inch
```

The tambour top supports now occupy `z = 43.75` to `45.25` inches. The slat
center path remains at `z = 44.50` inches, while the track centerline is offset
3/8 inch inward at `z = 44.125` inches. This leaves 1/4 inch between the support
rails and perimeter braces and accommodates a curtain and recessed-pull
envelope up to 1 1/2 inches deep while retaining the same clearance:

```text
45.50 - (44.125 + 0.375 + 1.50 / 2) = 0.25 inch
```

Handles, finger pulls, fasteners, and reinforcement must remain within that
envelope. The perimeter brace geometry and structural connections are
unchanged.

## Reasons for moving the bracing after Step 2

### No modeled dependency on intermediate framing

All four perimeter members and the single diagonal connect only to the four
posts. They do not depend geometrically on the lower rails, upper rails,
vertical rails, tambour supports, door, or street-light backing introduced in
Steps 4 through 12.

The reorder is therefore feasible from the model's dependency standpoint.

### Earlier control of frame squareness

Installing the top perimeter and diagonal while the posts are being aligned
would establish the final top rectangle earlier. This reduces the period in
which plan squareness depends entirely on temporary external bracing and makes
it less likely that later installation of the permanent diagonal will disturb
already positioned framing or guide tracks.

The posts should be checked for plumb, spacing, and equal plan diagonals before
the permanent members are fastened. Those measurements should be repeated
after fastening so the bracing does not lock an error into the frame.

### Better tambour alignment and acceptance testing

The former sequence trial-fitted the tambour before installing the permanent
top bracing and checked the curtain against the bracing's modeled envelope.
With the bracing installed earlier, the production tracks and curtain are
aligned and tested against the actual completed framing.

This is preferable because the installed braces, connections, and permitted
construction tolerances—not their idealized model envelopes—control the real
clearance.

### Improved access from the simplified diagonal

The simplified nominal 1x4 diagonal has an underside at `z = 46.25` inches.
The maximum approved tambour envelope reaches `z = 45.25` inches on its top
run, leaving approximately:

```text
46.25 - 45.25 = 1.00 inch
```

This 1-inch minimum clearance beneath the diagonal is substantially greater
than under the former 2x4 diagonals. It makes early installation less likely
to obstruct later tambour work.

The four perimeter 2x4 braces begin at `z = 45.50`, leaving 1/4 inch above the
maximum curtain envelope. Verify this minimum with the production tracks,
curtain, recessed pulls, fasteners, and approved support detail.

## Temporary-bracing limitation

Early installation of the top-plane bracing is not by itself a reason to
remove all temporary external bracing. It controls distortion of the top
rectangle, but it does not necessarily prevent all four posts from leaning or
swaying together in a vertical plane.

The build guide should continue to require temporary support until the
installed rails and other permanent framing provide adequate stability in
every direction and the permanent top-brace connections have been approved.

## Structural-connection limitation

Reordering the work does not resolve the unspecified structural connections.
The approved detail must still provide the member and connection capacity
required by [`TOP_BRACING.md`](TOP_BRACING.md), including positive load
transfer through the diagonal, perimeter frame, and posts in both loading
directions.

Ordinary deck screws, end-grain screws, or an unverified toe-screw pattern
must not be substituted for the approved connection. Applicable NDS connection
provisions or the [American Wood Council Connection
Calculator](https://awc.org/resources/connection-calculator/) can support the
connection design, but the final detail remains subject to the project-specific
engineering and authority approval already required by the bracing evaluation.

## Revised sequence

The revised sequence is:

1. Complete the underground conduit risers and restore grade.
2. Install the four posts with temporary external bracing.
3. Install the complete top perimeter and diagonal bracing while checking post
   plumb, spacing, plan diagonals, and the approved connection details.
4. Continue with the former Steps 3 through 11, renumbered as Steps 4 through
   12.
5. Continue with the existing Steps 13 through 25 without changing their
   numbers.

This move keeps the total at 25 build steps, so `build_step = 26` continues to
represent the completed model.

## Implemented project updates

The model, tambour prototype guide, build sequence, and build-step assertions
use the resolved geometry and early-bracing sequence. The tambour trial fit is
performed against the installed bracing, and temporary external bracing remains
required until the permanent frame and connections are approved and stable.
