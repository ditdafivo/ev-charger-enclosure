"""Generate roof gusset bearing covers for the current enclosure layout."""
from pathlib import Path
import argparse
from dataclasses import asdict
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import default_build
from lumber_model.gusset_cover import DEFAULT_SPEC, GussetCoverSpec, generate_gusset_covers

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/gusset_covers'))
    for name, default in asdict(DEFAULT_SPEC).items():
        parser.add_argument('--'+name.replace('_', '-'), type=float, default=default,
                            help=f'Field-fit dimension in mm (default: {default:g})')
    args = parser.parse_args()
    try:
        spec = GussetCoverSpec(**{name: getattr(args, name) for name in asdict(DEFAULT_SPEC)})
    except ValueError as error:
        parser.error(str(error))
    for path in generate_gusset_covers(default_build.siding, args.output_dir, spec=spec):
        print(path)
