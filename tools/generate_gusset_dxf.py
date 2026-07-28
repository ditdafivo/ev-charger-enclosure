from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lumber_model.gusset_dxf import generate_gusset_dxf


DEFAULT_OUTPUT = Path("fabrication/gusset_plate_6x6.dxf")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"DXF output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    generate_gusset_dxf(args.output)


if __name__ == "__main__":
    main()
