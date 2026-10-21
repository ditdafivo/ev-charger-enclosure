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
The existing 1/4-inch roof shims put roof support at `49.875` and the finished
roof at `50.875`. Post bottoms remain at the assumed `z = -32` datum; the survey
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

The front fixture is the MOD Lighting Brook MOD119, [16-inch black, 3000K
variant](https://www.mod-lighting.com/products/brook?variant=45573961023747).
The model uses its published 16 x 2.4 x 3.9-inch overall dimensions and
approximate bar/backplate geometry. A provisional 4 x 2 x 3.3-inch recessed
junction-box envelope replaces the round box and extension ring, keeping the
existing backing and tambour positions. The supplied bracket attaches at the
siding exterior; no exterior adapter plate is modeled.

This mount is conceptual: the manufacturer does not publish bracket dimensions.
Measure the actual bracket/backplate and select a compatible, accessible
junction box before fabrication or cutting the siding opening. The placeholder
box is labeled as provisional in the model and inventories. See
[steps 19–24](BUILD_STEPS.md#19-add-the-street-light-backing-street-light-backing)
for geometry assumptions and the manufacturer references.

## Licensing

The original enclosure code, documentation, and owner-created 3D assets are
available under the [MIT license](LICENSE). The customized and compiled
OpenSCAD Playground remains GPL-covered. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the exact boundary and
third-party licensing information.
