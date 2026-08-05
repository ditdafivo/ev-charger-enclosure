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

    def test_lumber_toggle_identifiers_must_remain_unique(self) -> None:
        members = LumberCollection()
        for name, x in (("same-name", 0), ("same name", 2)):
            members.add(
                name,
                assembly="frame",
                type="2x4",
                axis="z",
                start=AbsoluteCoord(x, 0, 0),
                length=10,
            )

        with self.assertRaisesRegex(
            ValueError,
            "duplicate individual OpenSCAD toggles",
        ):
            Model(members).validate()

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

        self.assertEqual(len(model.build_steps), 27)
        self.assertEqual(len(assigned), 143)
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
        self.assertNotIn("rail_l_tambour", step_by_object)
        self.assertEqual(step_by_object["tambour_ceiling_panel"], 13)
        self.assertEqual(step_by_object["enclosure_tambour_track"], 11)
        self.assertEqual(step_by_object["enclosure_tambour_door"], 12)
        self.assertEqual(step_by_object["front_street_light_backer_lower"], 14)
        self.assertEqual(step_by_object["front_street_light_backer_bottom"], 14)
        self.assertEqual(step_by_object["brace_fl_fr"], 3)
        self.assertEqual(step_by_object["brace_bl_fr"], 3)
        self.assertEqual(step_by_object["gusset_back_left"], 3)
        self.assertNotIn("brace_br_fl", step_by_object)
        self.assertEqual(step_by_object["front_ev_charger_body"], 15)
        self.assertEqual(step_by_object["front_ev_charger_plug"], 15)
        self.assertEqual(step_by_object["front_ev_charger_cable"], 15)
        self.assertEqual(step_by_object["power_junction_box"], 16)
        self.assertEqual(step_by_object["power_ground_riser"], 1)
        self.assertEqual(step_by_object["low_voltage_ground_riser"], 1)
        self.assertEqual(step_by_object["power_ev_charger_feed"], 17)
        self.assertEqual(step_by_object["power_ev_t_body"], 17)
        self.assertEqual(step_by_object["power_t_junction_feed"], 17)
        self.assertEqual(step_by_object["power_ev_reducer"], 17)
        self.assertEqual(step_by_object["rail_ltam"], 6)
        self.assertEqual(step_by_object["rail_rtam"], 6)
        self.assertEqual(step_by_object["left_tambour_bend_backer"], 10)
        self.assertEqual(step_by_object["right_tambour_bend_backer"], 10)
        self.assertEqual(step_by_object["rail_lt"], 7)
        self.assertEqual(step_by_object["rail_rt"], 7)
        self.assertEqual(step_by_object["rail_ft"], 8)
        self.assertEqual(step_by_object["front_center_rail"], 9)
        self.assertEqual(step_by_object["right_center_rail"], 9)
        self.assertEqual(step_by_object["roof_shim_brace_fl_fr"], 24)
        self.assertEqual(step_by_object["back_right_outlet_backer_lower"], 19)
        self.assertEqual(step_by_object["back_right_outlet"], 19)

    def test_generated_scad_contains_step_controls_and_routing(self) -> None:
        scad = build.model.to_scad()

        self.assertIn("build_step = 28;", scad)
        self.assertIn("build_step_count = 27;", scad)
        self.assertIn('["power_ground_riser", 1]', scad)
        self.assertIn('["low_voltage_ground_riser", 1]', scad)
        self.assertIn('["post_fl", 2]', scad)
        self.assertIn('["footing_fl", 2]', scad)
        self.assertIn('["brace_fl_fr", 3]', scad)
        self.assertIn('["gusset_back_left", 3]', scad)
        self.assertIn('["enclosure_tambour_track", 11]', scad)
        self.assertIn('["enclosure_tambour_door", 12]', scad)
        self.assertIn('["front_ev_charger_body", 15]', scad)
        self.assertIn('["front_ev_charger_cable", 15]', scad)
        self.assertIn('["power_junction_box", 16]', scad)
        self.assertIn('["power_ev_charger_feed", 17]', scad)
        self.assertIn('["power_ev_t_body", 17]', scad)
        self.assertIn('["power_t_junction_feed", 17]', scad)
        self.assertIn('["tambour_ceiling_panel", 13]', scad)
        self.assertIn('["roof_shim_brace_fl_fr", 24]', scad)
        self.assertIn('["back_right_outlet_backer_lower", 19]', scad)
        self.assertIn('["back_right_outlet", 19]', scad)
        self.assertIn('["back_right_outlet_cover", 27]', scad)
        self.assertIn("build_step == floor(build_step)", scad)
        self.assertIn("function object_is_visible(name)", scad)
        self.assertIn("function object_is_highlighted(name)", scad)
        self.assertIn("[1.0, 0.82, 0.0, 1.0]", scad)
        self.assertIn("labels = false;", scad)
        self.assertNotIn("lumber_labels", scad)
        self.assertNotIn("component_labels", scad)
        self.assertIn("/* [Individual Lumber] */", scad)
        self.assertIn("/* [Individual Components] */", scad)
        self.assertIn("// rail ft\nshow_lumber_rail_ft = true;", scad)
        self.assertIn(
            "// tambour ceiling panel\n"
            "show_component_tambour_ceiling_panel = true;",
            scad,
        )
        self.assertIn("show_lumber_rail_ft = true;", scad)
        self.assertIn("show_component_tambour_ceiling_panel = true;", scad)
        self.assertIn("function lumber_object_is_enabled(name)", scad)
        self.assertIn("function component_object_is_enabled(name)", scad)
        self.assertIn("&& lumber_object_is_enabled(l_name(p))", scad)
        self.assertIn("&& component_object_is_enabled(c_name(c))", scad)
        self.assertEqual(scad.count("if (labels && highlighted)"), 2)
        self.assertIn(
            "render_lumber(p, object_is_highlighted(l_name(p)))",
            scad,
        )
        self.assertIn(
            "render_siding_part(s, object_is_highlighted(s_name(s)))",
            scad,
        )

    def test_generic_and_parameterized_models_keep_normal_rendering(self) -> None:
        generic_scad = Model(self.sample_members()).to_scad()
        custom_scad = build.build_enclosure(width=30).model.to_scad()

        self.assertNotIn("build_step = 28;", generic_scad)
        self.assertNotIn("build_step = 28;", custom_scad)
        self.assertIn("function object_is_visible(name) = true;", generic_scad)


if __name__ == "__main__":
    unittest.main()
