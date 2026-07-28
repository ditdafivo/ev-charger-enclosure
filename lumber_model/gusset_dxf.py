from __future__ import annotations

from pathlib import Path

import ezdxf

from lumber_model.gusset import (
    GUSSET_HOLE_CENTERS_IN,
    GUSSET_HOLE_DIAMETER_IN,
    GUSSET_SIZE_IN,
)


def generate_gusset_dxf(output_path: Path) -> None:
    """Write the laser-cut 6 x 6 gusset outline and #9 clearance-hole grid."""

    fixed_metadata = ezdxf.options.write_fixed_meta_data_for_testing
    ezdxf.options.write_fixed_meta_data_for_testing = True
    try:
        document = ezdxf.new("R2013")
        document.units = ezdxf.units.IN
        document.header["$INSUNITS"] = ezdxf.units.IN
        document.header["$MEASUREMENT"] = 0
        document.header["$PROJECTNAME"] = "EV charger enclosure 6 x 6 gusset plate"

        document.layers.add("CUT", color=7)
        modelspace = document.modelspace()
        modelspace.add_lwpolyline(
            (
                (0.0, 0.0),
                (GUSSET_SIZE_IN, 0.0),
                (GUSSET_SIZE_IN, GUSSET_SIZE_IN),
                (0.0, GUSSET_SIZE_IN),
            ),
            close=True,
            dxfattribs={"layer": "CUT"},
        )
        for center in GUSSET_HOLE_CENTERS_IN:
            modelspace.add_circle(
                center,
                radius=GUSSET_HOLE_DIAMETER_IN / 2,
                dxfattribs={"layer": "CUT"},
            )

        # ezdxf's required-class source is a set; sort once before export so
        # independently generated copies are byte-for-byte reproducible.
        document.classes.add_required_classes(document.dxfversion)
        document.classes.classes = dict(sorted(document.classes.classes.items()))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.saveas(output_path)
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = fixed_metadata
