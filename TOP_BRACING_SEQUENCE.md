# Top-bracing build-sequence evaluation

## Question

Record why the accepted rabbeted top bracing is installed immediately after
the posts rather than after the intermediate framing.

## Conclusion

Install the accepted rabbeted top bracing directly after the posts using the
detail in [`TOP_BRACING.md`](TOP_BRACING.md). Keep temporary external bracing
until the routed seats, custom gusset plates, complete #9 screw grids, and frame
have been inspected.

## Consolidated geometry

The left and right top perimeter members are now 4x4s spanning `z = 43.50` to
`47.00`. Their inside faces and undersides replace `rail_l_tambour`,
`rail_r_tambour`, `rail_lt`, and `rail_rt`. The removable ceiling remains at
`z = 43.25` to `43.50`, directly against the 4x4 undersides, while the curtain
and guides remain inside the clear opening.

The full-section diagonal remains at `z = 46.25` to `47.00`. The two involved
posts stop at its underside, and only the four intersected side braces are
routed. Custom 0.074-inch gusset plates and modeled screw heads project 0.184
inch above the frame. The 1/4-inch shims cover the exposed perimeter framing
and both non-gusseted corner posts, stop at the gusset envelopes, and establish
the roof support plane at `z = 47.25`.

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

### Improved access from the shallow diagonal

The rabbeted, ripped nominal 1x6 diagonal has an underside at `z = 46.25` inches.
The maximum approved tambour envelope reaches `z = 45.25` inches on its top
run, leaving approximately:

```text
46.25 - 45.25 = 1.00 inch
```

This 1-inch minimum clearance beneath the diagonal is substantially greater
than under the former 2x4 diagonals. It makes early installation less likely
to obstruct later tambour work.

The side 4x4s occupy the former side-support footprint rather than crossing the
clear curtain opening. Verify the production tracks, curtain, recessed pulls,
fasteners, and ceiling retainers against their actual inside faces.

## Temporary-bracing limitation

Early installation of the top-plane bracing is not by itself a reason to
remove all temporary external bracing. It controls distortion of the top
rectangle, but it does not necessarily prevent all four posts from leaning or
swaying together in a vertical plane.

The build guide should continue to require temporary support until the
installed rails and other permanent framing provide adequate stability in
every direction and the permanent top-brace connections have been approved.

## Structural-connection installation

Route and dry-fit the four side-brace seats before installing hardware. Place
each 6-by-6 gusset against the two exterior faces of its post and fill its
sixteen-hole grid with #9 pan-head screws. The model intentionally leaves screw
length unspecified. Inspect plate seating, wood splitting, screw clearance,
and the post/perimeter load path before removing temporary support.

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
