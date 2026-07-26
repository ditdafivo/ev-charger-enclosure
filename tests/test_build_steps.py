from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import build
from lumber_model import AbsoluteCoord, BuildStep, LumberCollection, Model
from lumber_model.build_steps import parse_build_steps


class BuildStepParserTests(unittest.TestCase):
    def parse(self, text: str) -> tuple[BuildStep, ...]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "BUILD_STEPS.md"
            path.write_text(text)
            return parse_build_steps(path)

    def test_parses_sequential_object_blocks(self) -> None:
        steps = self.parse(
            """# Steps

## 1. First

New model objects:

```text
one
two
```

## 2. Second

New model objects:

```text
three
```
"""
        )

        self.assertEqual(
            steps,
            (
                BuildStep(1, ("one", "two")),
                BuildStep(2, ("three",)),
            ),
        )

    def test_rejects_nonsequential_steps(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected build step 2"):
            self.parse(
                """## 1. First
New model objects:
```text
one
```
## 3. Third
New model objects:
```text
three
```
"""
            )

    def test_rejects_duplicate_object_assignments(self) -> None:
        with self.assertRaisesRegex(ValueError, "assigned to both build steps"):
            self.parse(
                """## 1. First
New model objects:
```text
same
```
## 2. Second
New model objects:
```text
same
```
"""
            )


class BuildStepModelTests(unittest.TestCase):
    def sample_members(self) -> LumberCollection:
        members = LumberCollection()
        members.add(
            "post",
            assembly="frame",
            type="2x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )
        return members

    def test_mapping_must_match_every_renderable_object(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing model objects.*post"):
            Model(
                self.sample_members(),
                build_steps=(BuildStep(1, ("unknown",)),),
            ).validate()

    def test_enclosure_document_assigns_every_object_once(self) -> None:
        model = build.model
        assigned = [
            name for step in model.build_steps for name in step.object_names
        ]

        step_by_object = {
            name: step.number
            for step in model.build_steps
            for name in step.object_names
        }

        self.assertEqual(len(model.build_steps), 25)
        self.assertEqual(len(assigned), 134)
        self.assertEqual(set(assigned), set(model.renderable_object_names()))
        self.assertEqual(
            model.build_steps[0].object_names,
            ("power_ground_riser", "low_voltage_ground_riser"),
        )
        self.assertEqual(
            model.build_steps[-1].object_names,
            ("back_right_outlet_cover",),
        )
        self.assertEqual(step_by_object["post_fl"], 2)
        self.assertEqual(step_by_object["footing_fl"], 2)
        self.assertEqual(step_by_object["front_street_light_backer_lower"], 11)
        self.assertEqual(step_by_object["brace_fl_fr"], 12)
        self.assertEqual(step_by_object["brace_br_fl"], 12)
        self.assertEqual(step_by_object["front_ev_charger_body"], 13)
        self.assertEqual(step_by_object["front_ev_charger_plug"], 13)
        self.assertEqual(step_by_object["front_ev_charger_cable"], 13)
        self.assertEqual(step_by_object["power_junction_box"], 14)
        self.assertEqual(step_by_object["power_ground_riser"], 1)
        self.assertEqual(step_by_object["low_voltage_ground_riser"], 1)
        self.assertEqual(step_by_object["power_junction_ev_adapter"], 14)
        self.assertEqual(step_by_object["power_junction_ev_coupling"], 14)
        self.assertEqual(step_by_object["power_ev_charger_feed"], 15)
        self.assertEqual(step_by_object["back_right_outlet_backer_lower"], 17)
        self.assertEqual(step_by_object["back_right_outlet"], 17)

    def test_generated_scad_contains_step_controls_and_routing(self) -> None:
        scad = build.model.to_scad()

        self.assertIn("build_step = 26;", scad)
        self.assertIn("build_step_count = 25;", scad)
        self.assertIn('["power_ground_riser", 1]', scad)
        self.assertIn('["low_voltage_ground_riser", 1]', scad)
        self.assertIn('["post_fl", 2]', scad)
        self.assertIn('["footing_fl", 2]', scad)
        self.assertIn('["brace_fl_fr", 12]', scad)
        self.assertIn('["front_ev_charger_body", 13]', scad)
        self.assertIn('["front_ev_charger_cable", 13]', scad)
        self.assertIn('["power_junction_box", 14]', scad)
        self.assertIn('["power_junction_ev_adapter", 14]', scad)
        self.assertIn('["power_junction_ev_coupling", 14]', scad)
        self.assertIn('["power_ev_charger_feed", 15]', scad)
        self.assertIn('["back_right_outlet_backer_lower", 17]', scad)
        self.assertIn('["back_right_outlet", 17]', scad)
        self.assertIn('["back_right_outlet_cover", 25]', scad)
        self.assertIn("build_step == floor(build_step)", scad)
        self.assertIn("function object_is_visible(name)", scad)
        self.assertIn("function object_is_highlighted(name)", scad)
        self.assertIn("[1.0, 0.82, 0.0, 1.0]", scad)
        self.assertIn(
            "render_lumber(p, object_is_highlighted(l_name(p)))",
            scad,
        )
        self.assertIn(
            "render_siding_part(s, object_is_highlighted(s_name(s)))",
            scad,
        )

    def test_alternate_layout_objects_keep_their_installation_steps(self) -> None:
        expected_step_15 = {
            "charger-riser": {
                "power_ev_t_body",
                "power_ev_reducer",
                "power_t_junction_feed",
                "power_ev_charger_feed",
            },
            "junction-riser": {
                "power_ev_lb_body",
                "power_ev_reducer",
                "power_ev_lb_feed",
                "power_ev_charger_feed",
            },
        }
        for layout, expected in expected_step_15.items():
            with self.subTest(layout=layout):
                enclosure = build.build_enclosure(power_conduit_layout=layout)
                enclosure.model.validate()
                step_by_object = {
                    name: step.number
                    for step in enclosure.model.build_steps
                    for name in step.object_names
                }
                self.assertTrue(all(step_by_object[name] == 15 for name in expected))

                if layout == "junction-riser":
                    self.assertEqual(step_by_object["power_junction_ev_adapter"], 14)
                    self.assertEqual(step_by_object["power_junction_ev_coupling"], 14)

    def test_generic_and_parameterized_models_keep_normal_rendering(self) -> None:
        generic_scad = Model(self.sample_members()).to_scad()
        custom_scad = build.build_enclosure(width=30).model.to_scad()

        self.assertNotIn("build_step = 26;", generic_scad)
        self.assertNotIn("build_step = 26;", custom_scad)
        self.assertIn("function object_is_visible(name) = true;", generic_scad)


if __name__ == "__main__":
    unittest.main()
