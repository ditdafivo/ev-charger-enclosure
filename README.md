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

Printable ASA tambour tracks, removable keyed joint collars, clearance coupons,
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
point. The generated CSV and JSON manifests give print quantities and finished
bounding dimensions. Print two common dovetail-collar shoes for every track
joint, plus two pull handles. `joint_fit_preview.step` shows two test tracks,
the expansion gap, and both collars in their installed positions.

The workflow builds directly from the pinned public OpenSCAD Playground
submodule. No NAS, container runtime, deployment key, personal access token, or
committed WASM output is required.

## Licensing

The original enclosure code, documentation, and owner-created 3D assets are
available under the [MIT license](LICENSE). The customized and compiled
OpenSCAD Playground remains GPL-covered. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the exact boundary and
third-party licensing information.
