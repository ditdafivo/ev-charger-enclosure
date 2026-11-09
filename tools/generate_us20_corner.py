"""Generate the rounded US20 ASA slip-socket elbow, coupons and fixtures."""
import argparse
from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lumber_model.us20_corner import CornerSpec, generate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/us20_corner'))
    defaults = CornerSpec()
    parser.add_argument('--leg', type=float, default=defaults.leg, help='Reference outside leg width, mm')
    parser.add_argument('--thickness', type=float, default=defaults.thickness, help='Reference thickness, mm')
    parser.add_argument('--clearance', type=float, default=defaults.clearance, help='Socket clearance per mating surface, mm')
    parser.add_argument('--outside-bend-radius', type=float, default=defaults.outside_bend_radius)
    parser.add_argument('--inside-bend-radius', type=float, default=defaults.inside_bend_radius)
    parser.add_argument('--end-radius', type=float, default=defaults.end_radius)
    args = parser.parse_args()
    spec = replace(defaults, leg=args.leg, thickness=args.thickness, clearance=args.clearance,
                   outside_bend_radius=args.outside_bend_radius,
                   inside_bend_radius=args.inside_bend_radius, end_radius=args.end_radius)
    for path in generate(args.output_dir, spec):
        print(path)
