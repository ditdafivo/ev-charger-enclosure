from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import ezdxf

from lumber_model.gusset import (
    GUSSET_HOLE_CENTERS_IN,
    GUSSET_HOLE_DIAMETER_IN,
    GUSSET_SIZE_IN,
)
from lumber_model.gusset_dxf import generate_gusset_dxf


class GussetDxfTests(unittest.TestCase):
    def test_generated_dxf_has_inch_units_outline_and_hole_grid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "gusset.dxf"
            generate_gusset_dxf(path)
            document = ezdxf.readfile(path)

        self.assertEqual(document.units, ezdxf.units.IN)
        entities = list(document.modelspace())
        outlines = [entity for entity in entities if entity.dxftype() == "LWPOLYLINE"]
        holes = [entity for entity in entities if entity.dxftype() == "CIRCLE"]
        self.assertEqual(len(outlines), 1)
        self.assertTrue(outlines[0].closed)
        self.assertEqual(
            [(point[0], point[1]) for point in outlines[0].get_points()],
            [
                (0, 0),
                (GUSSET_SIZE_IN, 0),
                (GUSSET_SIZE_IN, GUSSET_SIZE_IN),
                (0, GUSSET_SIZE_IN),
            ],
        )
        self.assertEqual(len(holes), 16)
        self.assertEqual(
            {(circle.dxf.center.x, circle.dxf.center.y) for circle in holes},
            set(GUSSET_HOLE_CENTERS_IN),
        )
        self.assertEqual(
            {circle.dxf.radius for circle in holes},
            {GUSSET_HOLE_DIAMETER_IN / 2},
        )
        self.assertEqual({entity.dxf.layer for entity in entities}, {"CUT"})

    def test_generated_dxf_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            first = Path(temporary_directory) / "first.dxf"
            second = Path(temporary_directory) / "second.dxf"
            generate_gusset_dxf(first)
            generate_gusset_dxf(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
