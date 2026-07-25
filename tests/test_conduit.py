from __future__ import annotations

import unittest

from lumber_model import (
    AbsoluteCoord,
    CONDUIT_OD_BY_TRADE_SIZE,
    ComponentAnchor,
    ComponentCollection,
    ComponentType,
    ConduitBend,
    ConduitCollection,
    ConduitRun,
    LumberCollection,
    Model,
    RelativeCoord,
    cubic_bezier_conduit_points,
)


class ConduitTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_conduit_trade_size_ods(self) -> None:
        self.assertEqual(CONDUIT_OD_BY_TRADE_SIZE["1/2"], 0.840)
        self.assertEqual(CONDUIT_OD_BY_TRADE_SIZE["3/4"], 1.050)
        self.assertEqual(CONDUIT_OD_BY_TRADE_SIZE["1"], 1.315)
        self.assertEqual(CONDUIT_OD_BY_TRADE_SIZE["1-1/4"], 1.660)

    def test_rejects_unsupported_trade_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported conduit trade size"):
            ConduitRun(
                name="bad",
                trade_size="2",  # type: ignore[arg-type]
                points=(AbsoluteCoord(0, 0, 0), AbsoluteCoord(1, 0, 0)),
            )

    def test_model_rejects_duplicate_conduit_names(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        conduits = [
            ConduitRun("run", "1/2", (AbsoluteCoord(0, 0, 0), AbsoluteCoord(1, 0, 0))),
            ConduitRun("run", "3/4", (AbsoluteCoord(0, 1, 0), AbsoluteCoord(1, 1, 0))),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate conduit names"):
            Model(members, conduits=conduits).validate()

    def test_model_rejects_unknown_component_anchor(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        conduits = ConduitCollection()
        conduits.add(
            "run",
            trade_size="1/2",
            points=(ComponentAnchor("missing"), AbsoluteCoord(1, 0, 0)),
        )

        with self.assertRaisesRegex(KeyError, "unknown conduit component anchor"):
            Model(members, conduits=conduits).validate()

    def test_relative_conduit_point_resolves_from_component_anchor(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        component_type = ComponentType(
            name="box",
            size=(2, 2, 1),
            default_face="wide_pos",
        )
        components = ComponentCollection()
        components.add(
            "box",
            component_type=component_type,
            member="rail",
            at=5,
        )

        conduit = ConduitRun(
            "run",
            "1/2",
            (
                ComponentAnchor("box"),
                RelativeCoord("box", 1, 0, 2),
            ),
        )
        resolved = conduit.resolved(components.as_dict(), members.as_dict())

        self.assertVectorAlmostEqual(resolved.points[1], (6, 4, 2.75))

    def test_component_anchor_defaults_to_component_center_depth(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        component_type = ComponentType(
            name="box",
            size=(2, 2, 1),
            default_face="wide_pos",
        )
        components = ComponentCollection()
        components.add(
            "box",
            component_type=component_type,
            member="rail",
            at=5,
        )

        conduit = ConduitRun(
            "run",
            "1/2",
            (
                ComponentAnchor("box"),
                AbsoluteCoord(6, 4, 0.75),
            ),
        )
        resolved = conduit.resolved(components.as_dict(), members.as_dict())

        self.assertVectorAlmostEqual(resolved.points[0], (5, 4, 0.75))
        self.assertIn('"1/2"', resolved.scad_record())
        self.assertIn("0.84", resolved.scad_record())

    def test_component_anchor_supports_depth_offset_from_center(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        component_type = ComponentType(
            name="box",
            size=(2, 2, 1),
            default_face="wide_pos",
        )
        components = ComponentCollection()
        components.add(
            "box",
            component_type=component_type,
            member="rail",
            at=5,
        )

        conduit = ConduitRun(
            "run",
            "1/2",
            (
                ComponentAnchor("box", position=(1, 1), depth_offset=0.25),
                AbsoluteCoord(6, 4, 1),
            ),
        )
        resolved = conduit.resolved(components.as_dict(), members.as_dict())

        self.assertVectorAlmostEqual(resolved.points[0], (5, 4.25, 0.75))

    def test_bend_expands_corner_to_quarter_arc_points(self) -> None:
        conduit = ConduitRun(
            "run",
            "1/2",
            (
                AbsoluteCoord(0, 0, 0),
                AbsoluteCoord(0, 0, 10),
                AbsoluteCoord(10, 0, 10),
            ),
            bends=(ConduitBend(point_index=1, radius=4.0),),
        )
        resolved = conduit.resolved({}, {})

        self.assertEqual(resolved.bends, ((1, 4.0),))
        self.assertGreater(len(resolved.points), 3)
        self.assertVectorAlmostEqual(resolved.points[1], (0, 0, 6))
        self.assertVectorAlmostEqual(resolved.points[-2], (4, 0, 10))
        self.assertIn("[1, 4]", resolved.scad_record())

    def test_cubic_bezier_points_preserve_endpoints_and_tangency(self) -> None:
        points = cubic_bezier_conduit_points(
            (0, 0, 0),
            (0, 0, 4),
            (6, 8, 10),
            (10, 8, 10),
            segments=8,
        )
        resolved = tuple(point.resolve() for point in points)

        self.assertEqual(len(resolved), 9)
        self.assertVectorAlmostEqual(resolved[0], (0, 0, 0))
        self.assertVectorAlmostEqual(resolved[-1], (10, 8, 10))
        self.assertEqual(resolved[1][0], 0.265625)
        self.assertEqual(resolved[-2][1], 7.65625)

    def test_cubic_bezier_rejects_too_few_segments(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2"):
            cubic_bezier_conduit_points(
                (0, 0, 0),
                (0, 0, 1),
                (1, 1, 1),
                (1, 1, 2),
                segments=1,
            )


if __name__ == "__main__":
    unittest.main()
