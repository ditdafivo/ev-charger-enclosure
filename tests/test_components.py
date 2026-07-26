from __future__ import annotations

import unittest

from lumber_model import (
    AbsoluteCoord,
    AngledLumber,
    CARLON_E980DFN_HUB_DEPTH,
    CARLON_E980DFN_OUTLET_BOX,
    CARLON_E983G_CONDUIT_T_BODY,
    CARLON_E986G_LB_CONDUIT_BODY,
    CARLON_E989NNJ_JUNCTION_BOX,
    CARLON_E940D_COUPLING,
    CARLON_E940F_COUPLING,
    CARLON_E940G_COUPLING,
    CARLON_E943E_MALE_TERMINAL_ADAPTER,
    CARLON_E950GF_REDUCER_BUSHING,
    CARLON_E987N_JUNCTION_BOX,
    CARLON_E996D_BOX_ADAPTER,
    CARLON_E996F_BOX_ADAPTER,
    CARLON_E996G_BOX_ADAPTER,
    COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX,
    COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING,
    EV_CHARGER_BODY,
    EV_CHARGER_PLUG,
    GENERIC_DOWNWARD_STREET_LIGHT,
    INTERMATIC_WP5100BL_IN_USE_COVER,
    ONE_INCH_CABLE_GLAND,
    WEATHERPROOF_120V_OUTLET_BOX,
    ComponentCollection,
    ComponentInstance,
    ComponentType,
    Lumber,
    LumberCollection,
    Model,
    RelativeCoord,
    WIFI_ACCESS_POINT,
)


class ComponentResolutionTests(unittest.TestCase):
    def assertVectorAlmostEqual(
        self,
        actual: tuple[float, float, float],
        expected: tuple[float, float, float],
    ) -> None:
        for a, e in zip(actual, expected, strict=True):
            self.assertAlmostEqual(a, e)

    def test_lumber_collection_resolves_relative_start_from_existing_member(self) -> None:
        members = LumberCollection()
        members.add(
            "origin_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(-1.75, -1.75, 0),
            length=48,
        )

        member = members.add(
            "offset_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=RelativeCoord("origin_post", 10, 20, 0),
            length=48,
        )

        self.assertVectorAlmostEqual(member.start, (8.25, 18.25, 0))

    def test_between_aligns_cross_axis_to_support_overlap_by_default(self) -> None:
        members = LumberCollection()
        members.add(
            "left_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )
        members.add(
            "right_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=RelativeCoord("left_post", 24, 0, 0),
            length=48,
        )

        rail = members.between(
            "top_rail",
            assembly="frame",
            type="2x4",
            support_a="left_post",
            support_b="right_post",
            position=44,
        )

        self.assertVectorAlmostEqual(rail.start, (3.5, 0, 43.25))

    def test_between_cross_offset_moves_from_aligned_support_center(self) -> None:
        members = LumberCollection()
        members.add(
            "left_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )
        members.add(
            "right_post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=RelativeCoord("left_post", 24, 0, 0),
            length=48,
        )

        rail = members.between(
            "top_rail",
            assembly="frame",
            type="2x4",
            support_a="left_post",
            support_b="right_post",
            position=44,
            cross_offset=1,
        )

        self.assertVectorAlmostEqual(rail.start, (3.5, 1, 43.25))

    def test_between_uses_actual_perpendicular_dims_for_z_rotated_false(self) -> None:
        members = LumberCollection()
        members.add(
            "bottom_rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(3.5, 0, 5.25),
            length=20.5,
        )
        members.add(
            "top_rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(3.5, 0, 45.5),
            length=20.5,
        )

        rail = members.between(
            "center_rail",
            assembly="frame",
            type="2x4",
            support_a="bottom_rail",
            support_b="top_rail",
            position=13.75,
            rotated=False,
        )

        self.assertVectorAlmostEqual(rail.start, (13.0, 0, 6.75))
        self.assertVectorAlmostEqual(rail.size, (1.5, 3.5, 38.75))

    def test_diagonal_between_uses_inside_post_corners(self) -> None:
        members = LumberCollection()
        members.add(
            "post_fl",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )
        members.add(
            "post_fr",
            assembly="frame",
            type="4x4",
            axis="z",
            start=RelativeCoord("post_fl", 24, 0, 0),
            length=48,
        )
        members.add(
            "post_bl",
            assembly="frame",
            type="4x4",
            axis="z",
            start=RelativeCoord("post_fl", 0, 20, 0),
            length=48,
        )

        brace = members.diagonal_between(
            "brace",
            assembly="frame",
            type="2x4",
            support_a="post_bl",
            support_b="post_fr",
            position=46.25,
        )

        self.assertVectorAlmostEqual(brace.start, (3.5, 20, 46.25))
        self.assertVectorAlmostEqual(brace.end, (24, 3.5, 46.25))
        self.assertAlmostEqual(brace.length, 26.315395, places=5)
        self.assertAlmostEqual(brace.cut_angle_deg, 38.829824, places=5)
        self.assertEqual(brace.width, 3.5)
        self.assertEqual(brace.thickness, 1.5)

    def test_nominal_one_by_four_has_shallow_actual_thickness(self) -> None:
        brace = AngledLumber(
            name="brace",
            assembly="frame",
            type="1x4",
            start=(3.5, 20, 46.625),
            end=(24, 3.5, 46.625),
        )

        self.assertEqual(brace.width, 3.5)
        self.assertEqual(brace.thickness, 0.75)
        self.assertEqual(brace.bom_row()["size_z"], 0.75)

    def test_angled_lumber_bom_row_includes_cut_angles(self) -> None:
        brace = AngledLumber(
            name="brace",
            assembly="frame",
            type="2x4",
            start=(3.5, 20, 46.25),
            end=(24, 3.5, 46.25),
        )

        row = brace.bom_row()

        self.assertEqual(row["axis"], "angled")
        self.assertEqual(row["start_cut_angle_deg"], 38.83)
        self.assertEqual(row["end_cut_angle_deg"], 38.83)

    def test_resolves_wide_negative_face_on_x_running_lumber(self) -> None:
        member = Lumber(
            name="rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(10, 20, 30),
            length=100,
        )
        component_type = ComponentType(
            name="box",
            size=(4, 2, 1),
            default_face="wide_neg",
        )
        component = ComponentInstance(
            name="mounted_box",
            component_type=component_type,
            member="rail",
            at=25,
        )

        resolved = component.resolved(member)

        self.assertVectorAlmostEqual(resolved.box_min, (33, 19, 29.75))
        self.assertVectorAlmostEqual(resolved.box_size, (4, 1, 2))

    def test_resolves_narrow_positive_face_on_y_running_rotated_lumber(self) -> None:
        member = Lumber(
            name="rail",
            assembly="frame",
            type="2x4",
            axis="y",
            start=AbsoluteCoord(0, 0, 0),
            length=20,
            rotated=False,
        )
        component_type = ComponentType(
            name="box",
            size=(2, 4, 3),
            default_face="narrow_pos",
        )
        component = ComponentInstance(
            name="mounted_box",
            component_type=component_type,
            member="rail",
            at=5,
        )

        resolved = component.resolved(member)

        self.assertVectorAlmostEqual(resolved.box_min, (1.5, 4, -0.25))
        self.assertVectorAlmostEqual(resolved.box_size, (3, 2, 4))

    def test_instance_face_override_controls_post_side(self) -> None:
        member = Lumber(
            name="post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(-1.75, -1.75, 0),
            length=48,
        )
        component = ComponentInstance(
            name="outlet",
            component_type=WEATHERPROOF_120V_OUTLET_BOX,
            member="post",
            at=10,
            face="narrow_neg",
        )

        resolved = component.resolved(member)

        self.assertVectorAlmostEqual(resolved.box_min, (-2.375, -2.75, 8.5))
        self.assertVectorAlmostEqual(resolved.box_size, (4.75, 1, 3))

    def test_instance_orientation_rotates_about_mount_point(self) -> None:
        member = Lumber(
            name="rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=20,
        )
        component_type = ComponentType(
            name="marker",
            size=(4, 2, 1),
            default_face="wide_pos",
            mount_point=(2, 1, 0),
        )

        expected = {
            "up": ((8, 3.5, -0.25), (4, 1, 2)),
            "right": ((9, 3.5, -1.25), (2, 1, 4)),
            "down": ((8, 3.5, -0.25), (4, 1, 2)),
            "left": ((9, 3.5, -1.25), (2, 1, 4)),
            "inward": ((10, 1.5, -0.25), (1, 4, 2)),
        }

        for orientation, (box_min, box_size) in expected.items():
            with self.subTest(orientation=orientation):
                component = ComponentInstance(
                    name=f"mounted_box_{orientation}",
                    component_type=component_type,
                    member="rail",
                    at=10,
                    orientation=orientation,  # type: ignore[arg-type]
                )

                resolved = component.resolved(member)

                self.assertVectorAlmostEqual(resolved.box_min, box_min)
                self.assertVectorAlmostEqual(resolved.box_size, box_size)


class ComponentValidationTests(unittest.TestCase):
    def test_model_rejects_unknown_lumber_reference(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        components = ComponentCollection()
        components.add(
            "outlet",
            component_type=WEATHERPROOF_120V_OUTLET_BOX,
            member="missing",
            at=1,
        )

        with self.assertRaisesRegex(KeyError, "unknown lumber member"):
            Model(members, components=components).validate()

    def test_model_rejects_out_of_range_position(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )

        components = ComponentCollection()
        components.add(
            "outlet",
            component_type=WEATHERPROOF_120V_OUTLET_BOX,
            member="rail",
            at=11,
        )

        with self.assertRaisesRegex(ValueError, "outside member"):
            Model(members, components=components).validate()

    def test_model_rejects_component_on_angled_lumber(self) -> None:
        members = LumberCollection()
        members.diagonal_between(
            "brace",
            assembly="frame",
            type="2x4",
            support_a=members.add(
                "post_a",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(0, 0, 0),
                length=48,
            ),
            support_b=members.add(
                "post_b",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(24, 20, 0),
                length=48,
            ),
            position=46.25,
        )
        components = ComponentCollection()
        components.add(
            "outlet",
            component_type=WEATHERPROOF_120V_OUTLET_BOX,
            member="brace",
            at=1,
        )

        with self.assertRaisesRegex(ValueError, "cannot mount to angled lumber"):
            Model(members, components=components).validate()

    def test_component_type_rejects_invalid_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            ComponentType(name="bad", size=(1, 0, 1))

    def test_component_instance_rejects_invalid_face(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid face"):
            ComponentInstance(
                name="bad",
                component_type=WEATHERPROOF_120V_OUTLET_BOX,
                member="rail",
                at=1,
                face="front",  # type: ignore[arg-type]
            )

    def test_component_instance_rejects_invalid_orientation(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid orientation"):
            ComponentInstance(
                name="bad",
                component_type=WEATHERPROOF_120V_OUTLET_BOX,
                member="rail",
                at=1,
                orientation="diagonal",  # type: ignore[arg-type]
            )

    def test_primitive_union_rejects_empty_primitives(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            ComponentType(
                name="bad",
                size=(1, 1, 1),
                shape="primitive_union",
            )

    def test_primitive_union_rejects_invalid_primitive_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            ComponentType(
                name="bad",
                size=(1, 1, 1),
                shape="primitive_union",
                box_primitives=(
                    ((0, 0, 0), (1, 0, 1)),
                ),
            )

    def test_primitive_union_rejects_invalid_cylinder_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "axis must be"):
            ComponentType(
                name="bad",
                size=(1, 1, 1),
                shape="primitive_union",
                cylinder_primitives=(
                    ((0, 0, 0), "diagonal", 1, 1),  # type: ignore[arg-type]
                ),
            )

    def test_primitive_union_rejects_invalid_cylinder_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            ComponentType(
                name="bad",
                size=(1, 1, 1),
                shape="primitive_union",
                cylinder_primitives=(
                    ((0, 0, 0), "along", 0, 1),
                ),
            )

    def test_wifi_access_point_geometry(self) -> None:
        self.assertEqual(WIFI_ACCESS_POINT.name, "wifi_access_point")
        self.assertEqual(WIFI_ACCESS_POINT.size, (5.4, 3.3, 1.34))
        self.assertEqual(WIFI_ACCESS_POINT.default_face, "wide_neg")
        self.assertEqual(WIFI_ACCESS_POINT.mount_point, (5.4, 1.65, 0.0))

    def test_ev_charger_body_geometry(self) -> None:
        self.assertEqual(EV_CHARGER_BODY.name, "ev_charger_body")
        self.assertEqual(EV_CHARGER_BODY.size, (6.6, 6.6, 3.3))
        self.assertEqual(EV_CHARGER_BODY.default_face, "wide_neg")
        self.assertEqual(EV_CHARGER_BODY.mount_point, (6.6, 3.3, 0.0))

    def test_carlon_e989nnj_junction_box_geometry(self) -> None:
        self.assertEqual(CARLON_E989NNJ_JUNCTION_BOX.name, "carlon_e989nnj_junction_box")
        self.assertEqual(CARLON_E989NNJ_JUNCTION_BOX.size, (4.0, 4.0, 2.0))
        self.assertEqual(CARLON_E989NNJ_JUNCTION_BOX.shape, "box")
        self.assertEqual(CARLON_E989NNJ_JUNCTION_BOX.default_face, "wide_neg")
        self.assertEqual(CARLON_E989NNJ_JUNCTION_BOX.mount_point, (2.0, 2.0, 0.0))

    def test_carlon_e987n_junction_box_geometry(self) -> None:
        box = CARLON_E987N_JUNCTION_BOX

        self.assertEqual(box.name, "carlon_e987n_junction_box")
        self.assertEqual(box.size, (4.0, 4.0, 4.0))
        self.assertEqual(box.shape, "primitive_union")
        self.assertEqual(box.mount_point, (2.0, 2.0, 0.0))
        self.assertEqual(len(box.box_primitives), 2)

    def test_carlon_box_adapters_and_couplings(self) -> None:
        expected = (
            (CARLON_E996D_BOX_ADAPTER, 0.85, 1.11),
            (CARLON_E996F_BOX_ADAPTER, 1 + 3 / 32, 1.60),
            (CARLON_E996G_BOX_ADAPTER, 1.25, 1.95),
            (CARLON_E940D_COUPLING, 1.5, 1 + 7 / 64),
            (CARLON_E940F_COUPLING, 2.0, 1 + 5 / 8),
            (CARLON_E940G_COUPLING, 2 + 1 / 8, 1 + 63 / 64),
        )

        for component, length, diameter in expected:
            with self.subTest(component=component.name):
                self.assertEqual(component.size, (length, diameter, diameter))
                self.assertEqual(component.shape, "primitive_union")
                self.assertTrue(component.cylinder_primitives)
                self.assertEqual(component.mount_point, (0, diameter / 2, diameter / 2))

    def test_carlon_e950gf_reducer_geometry(self) -> None:
        reducer = CARLON_E950GF_REDUCER_BUSHING

        self.assertEqual(reducer.name, "carlon_e950gf_reducer_bushing")
        self.assertEqual(reducer.size, (1 + 9 / 64, 1.660, 1.660))
        self.assertEqual(reducer.mount_point, (0.0, 0.830, 0.830))
        self.assertEqual(
            reducer.cylinder_primitives,
            (
                ((0.0, 0.830, 0.830), "along", 0.75, 1.660),
                ((0.75, 0.830, 0.830), "along", 25 / 64, 1.315),
            ),
        )

    def test_low_voltage_entry_fittings(self) -> None:
        adapter = CARLON_E943E_MALE_TERMINAL_ADAPTER
        self.assertEqual(adapter.name, "carlon_e943e_male_terminal_adapter")
        self.assertEqual(adapter.size, (1.470, 1.290, 1.290))
        self.assertEqual(adapter.mount_point, (0, 1.290 / 2, 1.290 / 2))
        self.assertEqual(len(adapter.cylinder_primitives), 2)

        self.assertEqual(ONE_INCH_CABLE_GLAND.name, "one_inch_cable_gland")
        self.assertEqual(ONE_INCH_CABLE_GLAND.size, (0.75, 1.0, 1.0))
        self.assertEqual(ONE_INCH_CABLE_GLAND.mount_point, (0, 0.5, 0.5))

    def test_carlon_e980dfn_outlet_box_geometry(self) -> None:
        self.assertEqual(
            CARLON_E980DFN_OUTLET_BOX.name,
            "carlon_e980dfn_outlet_box",
        )
        self.assertEqual(CARLON_E980DFN_OUTLET_BOX.size, (5.7, 2.8, 2.3))
        self.assertEqual(CARLON_E980DFN_OUTLET_BOX.shape, "primitive_union")
        self.assertEqual(CARLON_E980DFN_OUTLET_BOX.default_face, "narrow_pos")
        self.assertEqual(CARLON_E980DFN_OUTLET_BOX.mount_point, (2.85, 1.4, 0.0))
        self.assertEqual(len(CARLON_E980DFN_OUTLET_BOX.box_primitives), 3)
        hub = CARLON_E980DFN_OUTLET_BOX.cylinder_primitives[0]
        self.assertEqual(CARLON_E980DFN_HUB_DEPTH, 0.566)
        self.assertEqual(hub[:2], ((0.0, 1.4, 0.566), "along"))
        self.assertAlmostEqual(hub[2], 0.58)
        self.assertEqual(hub[3], 1.15)

    def test_intermatic_wp5100bl_cover_geometry(self) -> None:
        self.assertEqual(
            INTERMATIC_WP5100BL_IN_USE_COVER.name,
            "intermatic_wp5100bl_in_use_cover",
        )
        self.assertEqual(INTERMATIC_WP5100BL_IN_USE_COVER.size, (6.33, 4.66, 2.75))
        self.assertEqual(INTERMATIC_WP5100BL_IN_USE_COVER.shape, "primitive_union")
        self.assertEqual(
            INTERMATIC_WP5100BL_IN_USE_COVER.mount_point,
            (3.165, 2.33, 0.0),
        )
        self.assertEqual(
            INTERMATIC_WP5100BL_IN_USE_COVER.cylinder_primitives,
            (((0.2, 0.14, 0.35), "along", 5.93, 0.28),),
        )

    def test_commercial_electric_wrb550b_geometry(self) -> None:
        box = COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX

        self.assertEqual(box.name, "commercial_electric_wrb550b_outlet_box")
        self.assertEqual(box.size, (4.2, 5.4, 1.6))
        self.assertEqual(box.color, (0.30, 0.16, 0.07, 1.0))
        self.assertEqual(box.shape, "primitive_union")
        self.assertEqual(box.default_face, "narrow_neg")
        self.assertEqual(box.mount_point, (2.1, 2.7, 0.0))
        self.assertEqual(len(box.cylinder_primitives), 9)
        self.assertEqual(
            box.cylinder_primitives[0],
            ((2.1, 2.7, 0.0), "out", 1.6, 4.0),
        )
        self.assertEqual(box.cylinder_primitives[1][0], (2.1, 0.0, 0.8))
        self.assertNotIn(
            ((2.1, 0.0, 0.8), "across", 0.1, 1.3),
            box.cylinder_primitives,
        )

    def test_commercial_electric_wre450g_geometry(self) -> None:
        ring = COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING

        self.assertEqual(ring.name, "commercial_electric_wre450g_extension_ring")
        self.assertEqual(ring.size, (4.4, 4.4, 1.7))
        self.assertEqual(ring.color, (0.55, 0.57, 0.58, 1.0))
        self.assertEqual(ring.shape, "primitive_union")
        self.assertEqual(ring.default_face, "narrow_neg")
        self.assertEqual(ring.mount_point, (2.2, 2.2, 0.0))
        self.assertEqual(len(ring.cylinder_primitives), 9)
        self.assertEqual(
            ring.cylinder_primitives[0],
            ((2.2, 2.2, 0.0), "out", 1.7, 4.0),
        )
        for cap in ring.cylinder_primitives[5:]:
            self.assertEqual(cap[2:], (0.1, 1.3))

    def test_generic_downward_street_light_geometry(self) -> None:
        self.assertEqual(
            GENERIC_DOWNWARD_STREET_LIGHT.name,
            "generic_downward_street_light",
        )
        self.assertEqual(GENERIC_DOWNWARD_STREET_LIGHT.size, (18.0, 4.0, 4.0))
        self.assertEqual(GENERIC_DOWNWARD_STREET_LIGHT.shape, "box")
        self.assertEqual(GENERIC_DOWNWARD_STREET_LIGHT.default_face, "narrow_neg")

    def test_ev_charger_plug_geometry(self) -> None:
        expected_size = (10.16507874015748, 4.0, 8.6)
        expected_mount_point = (10.16507874015748, 2.0, 0.0)

        self.assertEqual(EV_CHARGER_PLUG.name, "ev_charger_plug")
        self.assertEqual(EV_CHARGER_PLUG.shape, "mesh")
        self.assertEqual(
            EV_CHARGER_PLUG.mesh_path,
            "assets/components/ev_charger_plug/ev_charger_plug.stl",
        )
        self.assertEqual(EV_CHARGER_PLUG.default_face, "wide_neg")
        for actual, expected in zip(EV_CHARGER_PLUG.size, expected_size, strict=True):
            self.assertAlmostEqual(actual, expected)
        mount_point = EV_CHARGER_PLUG.mount_point
        self.assertIsNotNone(mount_point)
        assert mount_point is not None
        for actual, expected in zip(mount_point, expected_mount_point, strict=True):
            self.assertAlmostEqual(actual, expected)

    def test_carlon_e983g_geometry(self) -> None:
        expected_size = (8.65625, 3.375, 2.75)
        expected_mount_point = (4.328125, 1.6875, 0.0)
        expected_primitives = (
            ((0.0, 0.0, 0.0), (8.65625, 2.3125, 2.75)),
            ((2.953125, 2.3125, 0.0), (2.75, 1.0625, 2.75)),
        )

        self.assertEqual(CARLON_E983G_CONDUIT_T_BODY.name, "carlon_e983g_conduit_t_body")
        self.assertEqual(CARLON_E983G_CONDUIT_T_BODY.shape, "primitive_union")
        self.assertEqual(CARLON_E983G_CONDUIT_T_BODY.default_face, "wide_neg")
        self.assertEqual(CARLON_E983G_CONDUIT_T_BODY.size, expected_size)
        self.assertEqual(CARLON_E983G_CONDUIT_T_BODY.mount_point, expected_mount_point)
        self.assertEqual(
            CARLON_E983G_CONDUIT_T_BODY.box_primitives,
            expected_primitives,
        )

    def test_carlon_e986g_lb_geometry(self) -> None:
        lb = CARLON_E986G_LB_CONDUIT_BODY

        self.assertEqual(lb.name, "carlon_e986g_lb_conduit_body")
        self.assertEqual(lb.shape, "primitive_union")
        self.assertEqual(lb.size, (2.75, 2.5, 7 + 31 / 32))
        self.assertEqual(lb.mount_point, (0.0, 1.25, 1 + 31 / 32))
        self.assertEqual(len(lb.box_primitives), 2)
        self.assertEqual(len(lb.cylinder_primitives), 2)
        self.assertEqual(lb.cylinder_primitives[0][1], "along")
        self.assertEqual(lb.cylinder_primitives[1][1], "out")
        outlet = lb.cylinder_primitives[1]
        self.assertAlmostEqual(
            outlet[0][0]+outlet[3]/2,
            lb.size[0],
        )

    def test_mesh_component_scad_import_is_rendered(self) -> None:
        members = LumberCollection()
        members.add(
            "post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )

        components = ComponentCollection()
        components.add(
            "plug",
            component_type=EV_CHARGER_PLUG,
            member="post",
            at=20,
        )

        scad = Model(members, components=components).to_scad(
            scad_path="output/model.scad"
        )

        self.assertIn('"mesh"', scad)
        self.assertIn(
            '"../assets/components/ev_charger_plug/ev_charger_plug.stl"',
            scad,
        )
        self.assertIn("import(file = c_mesh_path(c), convexity = 10);", scad)

    def test_primitive_union_component_scad_is_rendered(self) -> None:
        members = LumberCollection()
        members.add(
            "post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )

        components = ComponentCollection()
        components.add(
            "conduit_t",
            component_type=CARLON_E983G_CONDUIT_T_BODY,
            member="post",
            at=20,
            orientation="left",
        )

        scad = Model(members, components=components).to_scad()

        self.assertIn('"primitive_union"', scad)
        self.assertIn("[[0, 0, 0], [8.6562, 2.3125, 2.75]]", scad)
        self.assertIn("[[2.9531, 2.3125, 0], [2.75, 1.0625, 2.75]]", scad)
        self.assertIn("function c_box_primitives(c) = c[16];", scad)
        self.assertIn("for (p = c_box_primitives(c))", scad)
        self.assertIn("cube(p_size(p));", scad)

    def test_primitive_union_scad_record_includes_primitives(self) -> None:
        member = Lumber(
            name="post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )
        component = ComponentInstance(
            name="conduit_t",
            component_type=CARLON_E983G_CONDUIT_T_BODY,
            member="post",
            at=20,
        )

        record = component.resolved(member).scad_record()

        self.assertIn('"primitive_union"', record)
        self.assertIn("[[0, 0, 0], [8.6562, 2.3125, 2.75]]", record)
        self.assertIn("[[2.9531, 2.3125, 0], [2.75, 1.0625, 2.75]]", record)

    def test_cylinder_primitive_scad_is_rendered(self) -> None:
        members = LumberCollection()
        members.add(
            "post",
            assembly="frame",
            type="4x4",
            axis="z",
            start=AbsoluteCoord(0, 0, 0),
            length=48,
        )
        component_type = ComponentType(
            name="cylinder",
            size=(2, 1, 1),
            shape="primitive_union",
            cylinder_primitives=(
                ((0, 0.5, 0.5), "along", 2, 1),
            ),
        )
        components = ComponentCollection()
        components.add(
            "cylinder",
            component_type=component_type,
            member="post",
            at=20,
        )

        scad = Model(members, components=components).to_scad()

        self.assertIn('[[0, 0.5, 0.5], "along", 2, 1]', scad)
        self.assertIn("function c_cylinder_primitives(c) = c[17];", scad)
        self.assertIn("module render_component_cylinder(p)", scad)
        self.assertIn("for (p = c_cylinder_primitives(c))", scad)

    def test_cut_list_rows_include_angled_cut_angles(self) -> None:
        members = LumberCollection()
        members.add(
            "rail",
            assembly="frame",
            type="2x4",
            axis="x",
            start=AbsoluteCoord(0, 0, 0),
            length=10,
        )
        members.diagonal_between(
            "brace",
            assembly="frame",
            type="2x4",
            support_a=members.add(
                "post_a",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(0, 0, 0),
                length=48,
            ),
            support_b=members.add(
                "post_b",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(24, 20, 0),
                length=48,
            ),
            position=46.25,
        )

        rows = Model(members).cut_list_rows(rounding_increment=None)
        brace_row = next(row for row in rows if row["members"] == "brace")
        rail_row = next(row for row in rows if row["members"] == "rail")

        self.assertEqual(brace_row["start_cut_angle_deg"], 38.83)
        self.assertEqual(brace_row["end_cut_angle_deg"], 38.83)
        self.assertEqual(rail_row["start_cut_angle_deg"], "")
        self.assertEqual(rail_row["end_cut_angle_deg"], "")

    def test_shopping_list_supports_nominal_one_by_four(self) -> None:
        members = LumberCollection()
        members.diagonal_between(
            "brace",
            assembly="frame",
            type="1x4",
            support_a=members.add(
                "post_a",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(0, 0, 0),
                length=48,
            ),
            support_b=members.add(
                "post_b",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(24, 20, 0),
                length=48,
            ),
            position=46.625,
        )

        rows = Model(members).shopping_list_rows()

        self.assertIn(
            {
                "type": "1x4",
                "stock_length_in": 72,
                "stock_length_display": '72"',
                "qty": 1,
            },
            rows,
        )

    def test_angled_lumber_scad_is_rendered_with_transform(self) -> None:
        members = LumberCollection()
        members.diagonal_between(
            "brace",
            assembly="frame",
            type="2x4",
            support_a=members.add(
                "post_a",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(0, 0, 0),
                length=48,
            ),
            support_b=members.add(
                "post_b",
                assembly="frame",
                type="4x4",
                axis="z",
                start=AbsoluteCoord(24, 20, 0),
                length=48,
            ),
            position=46.25,
        )

        scad = Model(members).to_scad()

        self.assertIn('"angled"', scad)
        self.assertIn("function l_end(l) = len(l) > 7 ? l[7] : l_start(l);", scad)
        self.assertIn("rotate([0, 0, l_angle(l)])", scad)
        self.assertIn("cube([l_len(l), l_width(l), l_thickness(l)]);", scad)


if __name__ == "__main__":
    unittest.main()
