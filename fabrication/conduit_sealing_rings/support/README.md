# Supporting scripts

Run from the ev-charger-enclosure repository root:

```bash
.venv/bin/python fabrication/conduit_sealing_rings/generate_rings.py
.venv/bin/python fabrication/conduit_sealing_rings/support/render_preview.py
```

The ring generator requires build123d 0.10.0, already pinned by the repository.
The optional preview renderer additionally requires matplotlib (tested with 3.11.1).

`extract_specs.py` is the script used to extract washer dimensions and locations
from the enclosure model, adapted to resolve this repository relative to its path.
It refreshes `design_inputs.json` from the current model while retaining the
researched Carlon/NPT constants in the script. Run it only when intentionally
refreshing those inputs; it replaces manual bore overrides.

```bash
.venv/bin/python fabrication/conduit_sealing_rings/support/extract_specs.py
```

The two PDFs in `../references/` are the manufacturer's drawing and catalog
extract inspected during dimension research. Provenance and source links are
recorded in `../PRINT_INSTRUCTIONS.md`.
