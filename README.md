# EV charger enclosure

This repository generates an OpenSCAD model, bill of materials, cut list, and
shopping list for a configurable outdoor EV charger enclosure.

## Generate and publish

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv run build.py
```

Outputs are written beneath `output/`. By default, the generated model is also
committed to the repository's generated `pages-source` branch and pushed to
GitHub. That push starts the Pages workflow, which rebuilds the browser-based
OpenSCAD Playground at:

<https://ditdafivo.github.io/ev-charger-enclosure/>

Publishing uses the authenticated `origin` Git remote. A network or GitHub
failure produces a warning without discarding local output. To generate files
without publishing, use:

```bash
uv run build.py --no-deploy
```

Automatic publishing is also skipped unless the working tree is clean and the
current commit exactly matches its freshly fetched upstream branch. This keeps
generated Pages deployments from getting ahead of the source code on GitHub.

The `--width`, `--depth`, and `--height` options customize the enclosure. Run
`uv run build.py --help` for their descriptions.

In the model parameters, deselect `siding` to hide the finish boards and trim.
Wall backing, plywood roof strips, siding screws, strip anchors, and pest mesh
remain visible, subject to the selected build step.

The default level finished post tops are at `z = 49.625` inches, with `z = 0`
at the outside corner of `post_fl`. The surveyed vertical ground-to-top heights
are 49 5/8 inches at front-left, 49 1/4 at front-right, 48 1/2 at back-left,
and 47 at back-right. Ground elevations at those outside corners are therefore
0, 3/8, 1 1/8, and 2 5/8 inches. A bilinear surface matches all four readings;
beyond the surveyed rectangle it holds the nearest edge elevation. Ground
references for conduit, cable clearance, and footing tops use that same surface.
The rendered surface is triangulated with less than 0.002-inch interpolation
error inside the surveyed rectangle.

`--height` changes the level post-top elevation above the front-left datum;
the surveyed ground stays fixed. The installed diagonal is friction-fitted
between the corner posts and secured by the two gussets. The diagonal and
perimeter bracing finish flush with the level post tops at `z = 49.625`.
The 3/4-inch PT plywood roof strips put roof support at `50.375` and the finished
US135 roof board at `50.875` (before US20 trim). Post bottoms remain at the assumed `z = -32` datum; the survey
does not establish their actual buried lengths.

## First deployment

GitHub Pages must use GitHub Actions as its publishing source. If the first
deployment reports that Pages is not enabled, open **Settings → Pages**, choose
**GitHub Actions** under **Build and deployment → Source**, and rerun
`uv run build.py`.

The build also writes `output/gusset_plate_6x6.dxf`, an inch-unit laser-cut
file for the custom G90 top-bracing gusset. To regenerate the committed
fabrication copy directly, run:

```bash
uv run python tools/generate_gusset_dxf.py
```

The build also exports two printable ASA/ABS gusset bearing covers in
`output/gusset_covers/`. They support the roof siding flush with the plywood
where the strips stop at the gussets. See [GUSSET_COVERS.md](GUSSET_COVERS.md)
for STL/STEP files, placement, printing and fit checks.

Tambour installation, including the front guide uprights and upper blocks, is
deferred indefinitely. The permanent side receiver rails attach directly to the
front and back posts and support the charger header independently. Printable ASA tracks, removable
keyed joint collars, clearance coupons,
end stops, loading sections, and the pull handle are generated as STEP and STL
files beneath `output/tambour/`. Generate the complete set, or one named part,
with:

```bash
uv run python tools/generate_tambour_parts.py
uv run python tools/generate_tambour_parts.py --part clearance_coupon_0.5mm
```

The geometry uses millimetres and targets a 350 mm printer bed with a 0.6 mm
nozzle. Print and condition the clearance coupons before committing to the
production tracks; the default 0.5 mm running clearance is only a starting
point. The 40 mm walls provide 35.2 mm usable depth with a 4.8 mm base and walls.
Provide at least 1 3/4-inch backing for the 39.7 mm footprint. Field-fit slats
to the minimum installed channel-bottom spacing minus 1/16-inch total end
clearance, following [the capture and prototype procedure](TAMBOUR_DOOR.md).
The generated CSV and JSON manifests give print quantities and finished
bounding dimensions. Print two common dovetail-collar shoes for every track
joint, plus two pull handles. `joint_fit_preview.step` shows two test tracks,
the expansion gap, and both collars in their installed positions.

The workflow builds directly from the pinned public OpenSCAD Playground
submodule. No NAS, container runtime, deployment key, personal access token, or
committed WASM output is required.

## Brook street light

The front fixture is the MOD Lighting Brook MOD119, 16-inch black, 3000K
variant 45573961023747. Its published overall dimensions are 16 x 2.4 x
3.9 inches. The supplied bracket sits on the front siding, fastened through
it into the low part of `brace_fl_fr`; default bracket center is z = 48.625
inches. Bracket geometry and fixture subdivisions are schematic.

Continuous 14/2 UF-B runs from the front power junction box, ahead of the
power ground riser pull box, along the former conduit path up `post_fr`,
then beneath the brace and through the nominal 1/2-inch siding bore into
the fixture's lower base. The existing 15 A maximum lighting-branch assumption
is retained. The round WRB550B transition box and its blank cover are removed.

A separate 12/2 UF-B run follows the former outlet conduit path along the lower
right rail into the outlet box. Three Commercial Electric FSW50Z-12.2-1
watertight UF connectors use the former light-box interface: two exits on the
front junction box and one entry at the outlet box. Cable lengths in the BOM
include 18 inches of termination/service allowance per run. The former
low-voltage light cable is removed.

Four separate silver numerals **4754**, each 5 inches high and 1 inch deep,
form a 12-inch-wide arrangement 3 inches below the light. One-inch standoffs
attach through the siding into 3/4-inch PT plywood across the upper front bays.
The plywood is recessed 1/4 inch behind the framing faces; use rigid local
spacers across that gap at numeral fasteners. The numeral font is Liberation Sans Regular.

This is a physical installation concept; the open-backed fixture connection
has not been verified against its certification. Measure the actual bracket,
cable, connector, and numeral hardware before drilling. See
[the build sequence](BUILD_STEPS.md#19-add-the-address-number-support-address-number-support)
for routing, sealing, grounding, access, and fabrication assumptions.

## Licensing

The original enclosure code, documentation, and owner-created 3D assets are
available under the [MIT license](LICENSE). The customized and compiled
OpenSCAD Playground remains GPL-covered. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the exact boundary and
third-party licensing information.

## Horizontal US135 siding

The shell uses US135 All Weather Pro tongue-and-groove siding with a
straight-grain face and V-groove joints. Full-height top boards and
ground-following bottom cuts keep the shell 3/4 inch above grade. A separate 1/4-inch mesh skirt
closes the lower gap. Wall installation proceeds **top downward**, using temporary
supports and inverted wall profiles, finished face outward. Screws into lumber
are concealed by the next lower overlap, with US20 covering edge exceptions
where possible and local exposed screws at remaining terminations. The build-step viewer
shows each course in that order. The rear access opening remains open.

The US135 top is a level cover that may leak. Paired 3/4-inch PT plywood strips
carry the boards and bear on the existing perimeter framing and diagonal;
US20 covers outside corners and the rear opening; vertical corners terminate
beneath mitered US20 roof-edge trim. See
[SIDING.md](SIDING.md) for the downward procedure, the required two-course
physical dry fit, provisional course pitch, custom face fastening, corner details,
fastener assumptions and the generated siding fabrication files.

## Fitted plywood wall infill

The roof strips and fitted 3/4-inch PT wall panels share one cutting plan.
Default dimensions need **one 4 x 8 ft sheet**, with no supplemental panel.
See `output/plywood_layout.svg` for the numbered layout and
`output/plywood_layout.json` for coordinates, kerfs and remaining offcuts.
Larger configurations compare additional full sheets with 2 x 4 ft panels,
using the stated approximate price ratio (0.49 per small panel).

Panels fit between permanent framing/backing rather than lining its interior
faces. Their interior faces finish flush with the inside post faces, leaving
the wall cavities between the siding and plywood. Predrilled toe screws attach
the panels to neighboring lumber. Separate upper-front numeral panels remain
1/4 inch behind the exterior framing faces for the eventual house-number
location. Keep the rear access opening and overhead space open; there is no ceiling or floor panel.
The mesh skirt closes the grade gap and tiny seams. The open rear access still
permits animal entry until it has a suitable closure.
