from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lumber_model.tambour_fabrication import generate_tambour_fabrication


DEFAULT_OUTPUT = Path("output/tambour")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the printable ASA tambour track and hardware parts."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--part",
        help="generate one named part instead of the complete fabrication set",
    )
    args = parser.parse_args()
    paths = generate_tambour_fabrication(args.output_dir, part_name=args.part)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
