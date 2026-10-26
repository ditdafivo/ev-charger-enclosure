"""Generate roof gusset bearing covers for the current enclosure layout."""
from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import default_build
from lumber_model.gusset_cover import generate_gusset_covers

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('output/gusset_covers'))
    args = parser.parse_args()
    for path in generate_gusset_covers(default_build.siding, args.output_dir):
        print(path)
