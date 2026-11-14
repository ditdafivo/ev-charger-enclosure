"""Generate the minimal US20 rear-clip prototype and fit coupons."""
import argparse
from dataclasses import fields
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lumber_model.us20_corner_clip import ClipSpec, generate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/us20_corner_clip'))
    for field in fields(ClipSpec):
        parser.add_argument('--'+field.name.replace('_', '-'), type=float, default=field.default)
    args = vars(parser.parse_args())
    directory = args.pop('output_dir')
    for path in generate(directory, ClipSpec(**args)):
        print(path)
