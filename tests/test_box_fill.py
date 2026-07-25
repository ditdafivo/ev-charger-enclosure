from __future__ import annotations

import unittest

from lumber_model import (
    BoxFillCalculation,
    conductor_fill_volume,
    equipment_grounding_fill_volume,
)


class BoxFillTests(unittest.TestCase):
    def test_task_three_fill_calculation(self) -> None:
        calculation = BoxFillCalculation(
            marked_volume=49,
            conductor_groups=((6, 3), (12, 7)),
            equipment_grounding_awgs=(6, 6, 12, 12, 12),
        )

        self.assertEqual(conductor_fill_volume(awg=6, count=3), 15)
        self.assertEqual(conductor_fill_volume(awg=12, count=7), 15.75)
        self.assertEqual(
            equipment_grounding_fill_volume(6, 6, 12, 12, 12),
            6.25,
        )
        self.assertEqual(calculation.required_volume, 37)
        self.assertEqual(calculation.remaining_volume, 12)
        calculation.validate()

    def test_spliced_six_awg_configuration_exceeds_box(self) -> None:
        calculation = BoxFillCalculation(
            marked_volume=49,
            conductor_groups=((6, 6), (12, 7)),
            equipment_grounding_awgs=(6, 6, 12, 12, 12),
        )

        with self.assertRaisesRegex(ValueError, "exceeds marked volume"):
            calculation.validate()

    def test_rejects_unsupported_wire_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            conductor_fill_volume(awg=4, count=1)


if __name__ == "__main__":
    unittest.main()
