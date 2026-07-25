# OpenSCAD Playground Pages build

This directory contains the pinned OpenSCAD Playground source, the GPL-covered
customization patches, and the static GitHub Pages build helper.

Initialize the submodule and generate a local-only enclosure model:

```bash
git submodule update --init
uv run build.py --no-deploy
```

Prepare the model path expected by the Playground, then build with:

```bash
sed 's#../assets/components/ev_charger_plug/ev_charger_plug\.stl#ev_charger_plug.stl#' \
  output/model.scad > /tmp/model.scad
./openscad_playground_container/scripts/build-pages.sh \
  /tmp/model.scad openscad_playground_container/dist local
```

Normal publication does not require this manual step. `uv run build.py` pushes
the prepared model to `pages-source`, and `.github/workflows/deploy-pages.yml`
runs the helper and publishes its output.

The build copies the upstream license bundle and an exact corresponding-source
revision notice into the deployed site. See the repository's
`THIRD_PARTY_NOTICES.md` for licensing details.
