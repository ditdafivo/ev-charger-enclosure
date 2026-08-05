from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal, overload

from lumber_model.constants import AXIS_INDEX, Axis
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3, other_axis, replace_axis
from lumber_model.lumber import AngledLumber, Lumber, LumberPiece


FaceName = Literal["wide_pos", "wide_neg", "narrow_pos", "narrow_neg"]
ComponentShape = Literal["box", "mesh", "primitive_union"]
ComponentOrientation = Literal["up", "right", "down", "left", "inward"]
Color = tuple[float, float, float, float]
BoxPrimitive = tuple[Vector3, Vector3]
ComponentPrimitiveAxis = Literal["along", "across", "out"]
CylinderPrimitive = tuple[Vector3, ComponentPrimitiveAxis, float, float]
Matrix4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]

FACE_NAMES: tuple[FaceName, ...] = (
    "wide_pos",
    "wide_neg",
    "narrow_pos",
    "narrow_neg",
)
COMPONENT_ORIENTATIONS: tuple[ComponentOrientation, ...] = (
    "up",
    "right",
    "down",
    "left",
    "inward",
)


def _validate_vector3(name: str, value: Vector3) -> None:
    if len(value) != 3:
        raise ValueError(f"{name} must be a 3-tuple")


def _unit(axis: Axis, sign: int = 1) -> Vector3:
    values = [0.0, 0.0, 0.0]
    values[AXIS_INDEX[axis]] = float(sign)
    return tuple(values)  # type: ignore[return-value]


def _v_add(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    )


def _v_sub(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )


def _v_scale(v: Vector3, scale: float) -> Vector3:
    return (
        v[0] * scale,
        v[1] * scale,
        v[2] * scale,
    )


def _v_mul_add(origin: Vector3, direction: Vector3, distance: float) -> Vector3:
    return _v_add(origin, _v_scale(direction, distance))


def _format_vector(values: Iterable[float]) -> str:
    return "[" + ", ".join(fmt_float(value) for value in values) + "]"


def _format_color(color: Color) -> str:
    return _format_vector(color)


def _format_matrix(matrix: Matrix4) -> str:
    return "[" + ", ".join(_format_vector(row) for row in matrix) + "]"


def _format_box_primitives(primitives: Iterable[BoxPrimitive]) -> str:
    return (
        "["
        + ", ".join(
            "[" + _format_vector(box_min) + ", " + _format_vector(box_size) + "]"
            for box_min, box_size in primitives
        )
        + "]"
    )


def _format_cylinder_primitives(
    primitives: Iterable[CylinderPrimitive],
) -> str:
    return (
        "["
        + ", ".join(
            "["
            + _format_vector(origin)
            + ", "
            + scad_string(axis)
            + ", "
            + fmt_float(length)
            + ", "
            + fmt_float(diameter)
            + "]"
            for origin, axis, length, diameter in primitives
        )
        + "]"
    )


def _identity_matrix() -> Matrix4:
    return (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def _validate_matrix4(name: str, value: Matrix4) -> None:
    if len(value) != 4 or any(len(row) != 4 for row in value):
        raise ValueError(f"{name} must be a 4x4 matrix")


def _validate_box_primitives(name: str, value: tuple[BoxPrimitive, ...]) -> None:
    for index, (box_min, box_size) in enumerate(value):
        _validate_vector3(f"{name}: box_primitives[{index}] min", box_min)
        _validate_vector3(f"{name}: box_primitives[{index}] size", box_size)

        for dimension in box_size:
            if dimension <= 0:
                raise ValueError(
                    f"{name}: box_primitives[{index}] dimensions must be positive, "
                    f"got {box_size}"
                )


def _validate_cylinder_primitives(
    name: str,
    value: tuple[CylinderPrimitive, ...],
) -> None:
    for index, (origin, axis, length, diameter) in enumerate(value):
        _validate_vector3(f"{name}: cylinder_primitives[{index}] origin", origin)
        if axis not in ("along", "across", "out"):
            raise ValueError(
                f"{name}: cylinder_primitives[{index}] axis must be 'along', "
                f"'across', or 'out', got {axis!r}"
            )
        if length <= 0 or diameter <= 0:
            raise ValueError(
                f"{name}: cylinder_primitives[{index}] length and diameter must "
                f"be positive, got length={length}, diameter={diameter}"
            )


def _scad_path(path: str, scad_dir: str | Path | None) -> str:
    if scad_dir is None:
        return path

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.as_posix()

    return Path(os.path.relpath(candidate, start=Path(scad_dir))).as_posix()


def _lumber_cross_axes(member: Lumber) -> tuple[Axis, Axis]:
    """
    Return the coordinate axes occupied by the member's wide and narrow faces.
    """
    if member.axis == "x":
        return ("y", "z") if member.rotated else ("z", "y")

    if member.axis == "y":
        return ("x", "z") if member.rotated else ("z", "x")

    if member.axis == "z":
        return ("x", "y") if member.rotated else ("y", "x")

    raise ValueError(f"{member.name}: invalid axis {member.axis!r}")


def _face_axis_and_sign(member: Lumber, face: FaceName) -> tuple[Axis, int]:
    if face not in FACE_NAMES:
        raise ValueError(
            f"{member.name}: invalid component mount face {face!r}; "
            f"expected one of {FACE_NAMES}"
        )

    wide_axis, narrow_axis = _lumber_cross_axes(member)
    face_axis = wide_axis if face.startswith("wide_") else narrow_axis
    sign = 1 if face.endswith("_pos") else -1
    return face_axis, sign


def _oriented_axes(
    orientation: ComponentOrientation,
    along_vec: Vector3,
    across_vec: Vector3,
    out_vec: Vector3,
) -> tuple[Vector3, Vector3, Vector3]:
    if orientation == "up":
        return along_vec, across_vec, out_vec

    if orientation == "right":
        return _v_scale(across_vec, -1.0), along_vec, out_vec

    if orientation == "down":
        return (
            _v_scale(along_vec, -1.0),
            _v_scale(across_vec, -1.0),
            out_vec,
        )

    if orientation == "left":
        return across_vec, _v_scale(along_vec, -1.0), out_vec

    if orientation == "inward":
        return _v_scale(out_vec, -1.0), across_vec, along_vec

    raise ValueError(f"Invalid component orientation {orientation!r}")


@dataclass(frozen=True)
class ComponentType:
    """
    Reusable component shape and mount definition.

    size is expressed in component-local axes:
      - along: parallel to the attached lumber's primary axis
      - across: centered on the selected lumber face
      - out: normal to and away from the selected lumber face

    mount_point is measured from the component-local minimum corner using the
    same axes.  The default is the center of the back face.
    """

    name: str
    size: Vector3
    color: Color = (0.74, 0.78, 0.80, 1.0)
    default_face: FaceName = "wide_pos"
    mount_point: Vector3 | None = None
    shape: ComponentShape = "box"
    mesh_path: str | None = None
    mesh_matrix: Matrix4 | None = None
    box_primitives: tuple[BoxPrimitive, ...] = ()
    cylinder_primitives: tuple[CylinderPrimitive, ...] = ()
    include_primitive_envelope: bool = False

    def __post_init__(self) -> None:
        _validate_vector3(f"{self.name}: size", self.size)

        for value in self.size:
            if value <= 0:
                raise ValueError(
                    f"{self.name}: component dimensions must be positive, got "
                    f"{self.size}"
                )

        if len(self.color) != 4:
            raise ValueError(f"{self.name}: color must be an RGBA 4-tuple")

        if self.default_face not in FACE_NAMES:
            raise ValueError(
                f"{self.name}: invalid default_face {self.default_face!r}; "
                f"expected one of {FACE_NAMES}"
            )

        if self.shape not in ("box", "mesh", "primitive_union"):
            raise ValueError(
                f"{self.name}: invalid shape {self.shape!r}; expected 'box' or "
                "'mesh' or 'primitive_union'"
            )

        if self.shape == "mesh" and not self.mesh_path:
            raise ValueError(f"{self.name}: mesh_path is required for mesh components")

        if self.shape == "primitive_union":
            if not self.box_primitives and not self.cylinder_primitives:
                raise ValueError(
                    f"{self.name}: primitive_union must contain at least one "
                    "primitive"
                )
            _validate_box_primitives(self.name, self.box_primitives)
            _validate_cylinder_primitives(self.name, self.cylinder_primitives)

        if self.mesh_matrix is not None:
            _validate_matrix4(f"{self.name}: mesh_matrix", self.mesh_matrix)

        if self.mount_point is None:
            object.__setattr__(
                self,
                "mount_point",
                (self.size[0] / 2, self.size[1] / 2, 0.0),
            )
        else:
            _validate_vector3(f"{self.name}: mount_point", self.mount_point)

        if self.shape == "mesh" and self.mesh_matrix is None:
            object.__setattr__(self, "mesh_matrix", _identity_matrix())


@dataclass(frozen=True)
class ComponentInstance:
    name: str
    component_type: ComponentType
    member: str
    at: float
    assembly: str = "components"
    face: FaceName | None = None
    offset: Vector3 = (0.0, 0.0, 0.0)
    orientation: ComponentOrientation = "up"

    def __post_init__(self) -> None:
        if self.at < 0:
            raise ValueError(f"{self.name}: at must be non-negative, got {self.at}")

        _validate_vector3(f"{self.name}: offset", self.offset)

        if self.face is not None and self.face not in FACE_NAMES:
            raise ValueError(
                f"{self.name}: invalid face {self.face!r}; expected one of "
                f"{FACE_NAMES}"
            )

        if self.orientation not in COMPONENT_ORIENTATIONS:
            raise ValueError(
                f"{self.name}: invalid orientation {self.orientation!r}; expected "
                f"one of {COMPONENT_ORIENTATIONS}"
            )

    def resolved(self, member: LumberPiece) -> ResolvedComponent:
        if self.at > member.length:
            raise ValueError(
                f"{self.name}: at={self.at} is outside member {member.name!r} "
                f"length {member.length}"
            )

        face = self.face if self.face is not None else self.component_type.default_face
        if isinstance(member, AngledLumber):
            dx = member.end[0] - member.start[0]
            dy = member.end[1] - member.start[1]
            along_vec = (dx / member.length, dy / member.length, 0.0)
            lateral_vec = (-along_vec[1], along_vec[0], 0.0)
            vertical_vec = (0.0, 0.0, 1.0)
            sign = 1 if face.endswith("_pos") else -1
            if face.startswith("wide_"):
                across_vec = lateral_vec
                out_vec = _v_scale(vertical_vec, sign)
                face_offset = member.thickness / 2
            else:
                across_vec = vertical_vec
                out_vec = _v_scale(lateral_vec, sign)
                face_offset = member.width / 2
            anchor = _v_mul_add(member.start, along_vec, self.at)
            anchor = _v_mul_add(anchor, out_vec, face_offset)
        else:
            face_axis, sign = _face_axis_and_sign(member, face)
            across_axis = other_axis(member.axis, face_axis)

            anchor = (0.0, 0.0, 0.0)
            anchor = replace_axis(
                anchor, member.axis, member.min_on(member.axis) + self.at
            )
            anchor = replace_axis(anchor, across_axis, member.center_on(across_axis))
            anchor = replace_axis(
                anchor,
                face_axis,
                member.max_on(face_axis) if sign > 0 else member.min_on(face_axis),
            )

            along_vec = _unit(member.axis)
            across_vec = _unit(across_axis)
            out_vec = _unit(face_axis, sign)
        along_vec, across_vec, out_vec = _oriented_axes(
            self.orientation,
            along_vec,
            across_vec,
            out_vec,
        )

        anchor = _v_mul_add(anchor, along_vec, self.offset[0])
        anchor = _v_mul_add(anchor, across_vec, self.offset[1])
        anchor = _v_mul_add(anchor, out_vec, self.offset[2])

        mount_point = self.component_type.mount_point
        if mount_point is None:
            raise ValueError(f"{self.component_type.name}: mount_point was not set")

        origin = anchor
        origin = _v_sub(origin, _v_scale(along_vec, mount_point[0]))
        origin = _v_sub(origin, _v_scale(across_vec, mount_point[1]))
        origin = _v_sub(origin, _v_scale(out_vec, mount_point[2]))

        size = self.component_type.size
        local_min = [0.0, 0.0, 0.0]
        local_max = [size[0], size[1], size[2]]
        if (
            self.component_type.shape == "primitive_union"
            and self.component_type.include_primitive_envelope
        ):
            for primitive_min, primitive_size in self.component_type.box_primitives:
                for index in range(3):
                    local_min[index] = min(local_min[index], primitive_min[index])
                    local_max[index] = max(
                        local_max[index], primitive_min[index] + primitive_size[index]
                    )
            local_axis_index = {"along": 0, "across": 1, "out": 2}
            for primitive_origin, primitive_axis, length, diameter in (
                self.component_type.cylinder_primitives
            ):
                axis_index = local_axis_index[primitive_axis]
                radius = diameter / 2
                for index in range(3):
                    padding = 0 if index == axis_index else radius
                    local_min[index] = min(
                        local_min[index], primitive_origin[index] - padding
                    )
                    local_max[index] = max(
                        local_max[index],
                        primitive_origin[index]
                        + (length if index == axis_index else 0)
                        + padding,
                    )
        corners = [
            _v_add(
                origin,
                _v_add(
                    _v_add(_v_scale(along_vec, along), _v_scale(across_vec, across)),
                    _v_scale(out_vec, out),
                ),
            )
            for along in (local_min[0], local_max[0])
            for across in (local_min[1], local_max[1])
            for out in (local_min[2], local_max[2])
        ]

        box_min = tuple(min(corner[i] for corner in corners) for i in range(3))
        box_max = tuple(max(corner[i] for corner in corners) for i in range(3))
        box_size = tuple(box_max[i] - box_min[i] for i in range(3))

        return ResolvedComponent(
            name=self.name,
            assembly=self.assembly,
            type_name=self.component_type.name,
            member=member.name,
            face=face,
            at=self.at,
            box_min=box_min,  # type: ignore[arg-type]
            box_size=box_size,  # type: ignore[arg-type]
            color=self.component_type.color,
            origin=origin,
            along_vec=along_vec,
            across_vec=across_vec,
            out_vec=out_vec,
            shape=self.component_type.shape,
            mesh_path=self.component_type.mesh_path,
            mesh_matrix=self.component_type.mesh_matrix,
            box_primitives=self.component_type.box_primitives,
            cylinder_primitives=self.component_type.cylinder_primitives,
        )


@dataclass(frozen=True)
class ResolvedComponent:
    name: str
    assembly: str
    type_name: str
    member: str
    face: FaceName
    at: float
    box_min: Vector3
    box_size: Vector3
    color: Color
    origin: Vector3
    along_vec: Vector3
    across_vec: Vector3
    out_vec: Vector3
    shape: ComponentShape
    mesh_path: str | None
    mesh_matrix: Matrix4 | None
    box_primitives: tuple[BoxPrimitive, ...]
    cylinder_primitives: tuple[CylinderPrimitive, ...]

    def scad_record(self, scad_dir: str | Path | None = None) -> str:
        mesh_path = (
            "" if self.mesh_path is None else _scad_path(self.mesh_path, scad_dir)
        )
        mesh_matrix = (
            self.mesh_matrix if self.mesh_matrix is not None else _identity_matrix()
        )

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{scad_string(self.type_name)}, "
            f"{scad_string(self.member)}, "
            f"{scad_string(self.face)}, "
            f"{fmt_float(self.at)}, "
            f"{_format_vector(self.box_min)}, "
            f"{_format_vector(self.box_size)}, "
            f"{_format_color(self.color)}, "
            f"{scad_string(self.shape)}, "
            f"{_format_vector(self.origin)}, "
            f"{_format_vector(self.along_vec)}, "
            f"{_format_vector(self.across_vec)}, "
            f"{_format_vector(self.out_vec)}, "
            f"{scad_string(mesh_path)}, "
            f"{_format_matrix(mesh_matrix)}, "
            f"{_format_box_primitives(self.box_primitives)}, "
            f"{_format_cylinder_primitives(self.cylinder_primitives)}"
            "]"
        )


ComponentRef = str | ComponentInstance
LumberRef = str | LumberPiece


class ComponentCollection(Mapping[str, ComponentInstance]):
    def __init__(
        self,
        components: Mapping[str, ComponentInstance]
        | Iterable[ComponentInstance]
        | None = None,
    ):
        self._components: dict[str, ComponentInstance] = {}

        if components is None:
            return

        if isinstance(components, Mapping):
            for name, component in components.items():
                if name != component.name:
                    raise ValueError(
                        f"Component key {name!r} does not match component name "
                        f"{component.name!r}"
                    )
                self._store(component)
            return

        for component in components:
            self._store(component)

    def add(
        self,
        name: str,
        *,
        component_type: ComponentType,
        member: LumberRef,
        at: float,
        assembly: str = "components",
        face: FaceName | None = None,
        offset: Vector3 = (0.0, 0.0, 0.0),
        orientation: ComponentOrientation = "up",
    ) -> ComponentInstance:
        member_name = member.name if isinstance(member, (Lumber, AngledLumber)) else member

        return self._store(
            ComponentInstance(
                name=name,
                component_type=component_type,
                member=member_name,
                at=at,
                assembly=assembly,
                face=face,
                offset=offset,
                orientation=orientation,
            )
        )

    @overload
    def get(self, name: str) -> ComponentInstance | None: ...

    @overload
    def get(
        self,
        name: str,
        default: ComponentInstance,
    ) -> ComponentInstance: ...

    def get(
        self,
        name: str,
        default: ComponentInstance | None = None,
    ) -> ComponentInstance | None:
        return self._components.get(name, default)

    def resolve(self, ref: ComponentRef) -> ComponentInstance:
        if isinstance(ref, ComponentInstance):
            return ref

        try:
            return self._components[ref]
        except KeyError as exc:
            raise KeyError(f"Unknown component {ref!r}") from exc

    def as_dict(self) -> dict[str, ComponentInstance]:
        return dict(self._components)

    def _store(self, component: ComponentInstance) -> ComponentInstance:
        if component.name in self._components:
            raise ValueError(f"Duplicate component name: {component.name}")

        self._components[component.name] = component
        return component

    def __getitem__(self, name: str) -> ComponentInstance:
        return self._components[name]

    def __contains__(self, name: object) -> bool:
        return name in self._components

    def __iter__(self) -> Iterator[str]:
        return iter(self._components)

    def __len__(self) -> int:
        return len(self._components)


WEATHERPROOF_120V_OUTLET_BOX = ComponentType(
    name="weatherproof_120v_outlet_box",
    size=(3.0, 4.75, 1.0),
    color=(0.74, 0.78, 0.80, 1.0),
    default_face="wide_neg",
)

_CARLON_E980DFN_OVERALL_HEIGHT = 5.70
_CARLON_E980DFN_BODY_HEIGHT = 4.54
_CARLON_E980DFN_WIDTH = 2.80
_CARLON_E980DFN_DEPTH = 2.30
CARLON_E980DFN_HUB_DEPTH = 0.566
_CARLON_E980DFN_END_HEIGHT = (
    _CARLON_E980DFN_OVERALL_HEIGHT - _CARLON_E980DFN_BODY_HEIGHT
) / 2
_CARLON_E980DFN_HUB_DIAMETER = 1.15

CARLON_E980DFN_OUTLET_BOX = ComponentType(
    name="carlon_e980dfn_outlet_box",
    size=(
        _CARLON_E980DFN_OVERALL_HEIGHT,
        _CARLON_E980DFN_WIDTH,
        _CARLON_E980DFN_DEPTH,
    ),
    color=(0.55, 0.57, 0.58, 1.0),
    default_face="narrow_pos",
    shape="primitive_union",
    box_primitives=(
        (
            (_CARLON_E980DFN_END_HEIGHT, 0.0, 0.0),
            (
                _CARLON_E980DFN_BODY_HEIGHT,
                _CARLON_E980DFN_WIDTH,
                _CARLON_E980DFN_DEPTH,
            ),
        ),
        ((0.0, 0.95, 0.0), (_CARLON_E980DFN_END_HEIGHT, 0.90, 0.30)),
        (
            (
                _CARLON_E980DFN_OVERALL_HEIGHT - _CARLON_E980DFN_END_HEIGHT,
                0.95,
                0.0,
            ),
            (_CARLON_E980DFN_END_HEIGHT, 0.90, 0.30),
        ),
    ),
    cylinder_primitives=(
        (
            (0.0, _CARLON_E980DFN_WIDTH / 2, CARLON_E980DFN_HUB_DEPTH),
            "along",
            _CARLON_E980DFN_END_HEIGHT,
            _CARLON_E980DFN_HUB_DIAMETER,
        ),
    ),
)

INTERMATIC_WP5100BL_IN_USE_COVER = ComponentType(
    name="intermatic_wp5100bl_in_use_cover",
    size=(6.33, 4.66, 2.75),
    color=(0.03, 0.03, 0.03, 1.0),
    default_face="narrow_pos",
    shape="primitive_union",
    box_primitives=(
        ((0.0, 0.0, 0.0), (6.33, 4.66, 0.18)),
        ((0.22, 0.18, 0.18), (5.89, 4.30, 2.57)),
        ((0.0, 2.00, 2.45), (0.32, 0.66, 0.30)),
    ),
    cylinder_primitives=(
        ((0.20, 0.14, 0.35), "along", 5.93, 0.28),
    ),
)

_COMMERCIAL_ELECTRIC_WRB550B_WIDTH = 4.20
_COMMERCIAL_ELECTRIC_WRB550B_HEIGHT = 5.40
_COMMERCIAL_ELECTRIC_WRB550B_DEPTH = 1.60
_COMMERCIAL_ELECTRIC_WRB550B_BODY_DIAMETER = 4.00
_COMMERCIAL_ELECTRIC_WRB550B_HUB_DIAMETER = 1.15
_COMMERCIAL_ELECTRIC_WRB550B_CAP_DIAMETER = 1.30
_COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS = 0.10
_COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG = (
    _COMMERCIAL_ELECTRIC_WRB550B_WIDTH / 2
)
_COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS = (
    _COMMERCIAL_ELECTRIC_WRB550B_HEIGHT / 2
)
_COMMERCIAL_ELECTRIC_WRB550B_SIDE_HUB_LENGTH = 0.70
_COMMERCIAL_ELECTRIC_WRB550B_END_HUB_LENGTH = 0.70

COMMERCIAL_ELECTRIC_WRB550B_OUTLET_BOX = ComponentType(
    name="commercial_electric_wrb550b_outlet_box",
    size=(
        _COMMERCIAL_ELECTRIC_WRB550B_WIDTH,
        _COMMERCIAL_ELECTRIC_WRB550B_HEIGHT,
        _COMMERCIAL_ELECTRIC_WRB550B_DEPTH,
    ),
    color=(0.30, 0.16, 0.07, 1.0),
    default_face="narrow_neg",
    mount_point=(
        _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
        _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
        0.0,
    ),
    shape="primitive_union",
    cylinder_primitives=(
        # Round body.
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                0.0,
            ),
            "out",
            _COMMERCIAL_ELECTRIC_WRB550B_DEPTH,
            _COMMERCIAL_ELECTRIC_WRB550B_BODY_DIAMETER,
        ),
        # Bottom, top, left, and right 1/2-inch hubs.
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
                0.0,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRB550B_END_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRB550B_HUB_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
                _COMMERCIAL_ELECTRIC_WRB550B_HEIGHT
                - _COMMERCIAL_ELECTRIC_WRB550B_END_HUB_LENGTH,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRB550B_END_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRB550B_HUB_DIAMETER,
        ),
        (
            (
                0.0,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRB550B_SIDE_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRB550B_HUB_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_WIDTH
                - _COMMERCIAL_ELECTRIC_WRB550B_SIDE_HUB_LENGTH,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRB550B_SIDE_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRB550B_HUB_DIAMETER,
        ),
        # Closure caps for the top, left, right, and rear ports. The bottom
        # hub remains uncapped for the future 1/2-inch conduit run.
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
                _COMMERCIAL_ELECTRIC_WRB550B_HEIGHT
                - _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_DIAMETER,
        ),
        (
            (
                0.0,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_WIDTH
                - _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                _COMMERCIAL_ELECTRIC_WRB550B_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ALONG,
                _COMMERCIAL_ELECTRIC_WRB550B_CENTER_ACROSS,
                0.0,
            ),
            "out",
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRB550B_CAP_DIAMETER,
        ),
    ),
)

_COMMERCIAL_ELECTRIC_WRE450G_DIAMETER = 4.40
_COMMERCIAL_ELECTRIC_WRE450G_DEPTH = 1.70
_COMMERCIAL_ELECTRIC_WRE450G_BODY_DIAMETER = 4.00
_COMMERCIAL_ELECTRIC_WRE450G_HUB_DIAMETER = 1.15
_COMMERCIAL_ELECTRIC_WRE450G_CAP_DIAMETER = 1.30
_COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS = 0.10
_COMMERCIAL_ELECTRIC_WRE450G_CENTER = _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER / 2
_COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH = 0.70

COMMERCIAL_ELECTRIC_WRE450G_EXTENSION_RING = ComponentType(
    name="commercial_electric_wre450g_extension_ring",
    size=(
        _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER,
        _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER,
        _COMMERCIAL_ELECTRIC_WRE450G_DEPTH,
    ),
    color=(0.55, 0.57, 0.58, 1.0),
    default_face="narrow_neg",
    mount_point=(
        _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
        _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
        0.0,
    ),
    shape="primitive_union",
    cylinder_primitives=(
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                0.0,
            ),
            "out",
            _COMMERCIAL_ELECTRIC_WRE450G_DEPTH,
            _COMMERCIAL_ELECTRIC_WRE450G_BODY_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                0.0,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER
                - _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_DIAMETER,
        ),
        (
            (
                0.0,
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER
                - _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_LENGTH,
            _COMMERCIAL_ELECTRIC_WRE450G_HUB_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                0.0,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER
                - _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "across",
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_DIAMETER,
        ),
        (
            (
                0.0,
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_DIAMETER,
        ),
        (
            (
                _COMMERCIAL_ELECTRIC_WRE450G_DIAMETER
                - _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
                _COMMERCIAL_ELECTRIC_WRE450G_CENTER,
                _COMMERCIAL_ELECTRIC_WRE450G_DEPTH / 2,
            ),
            "along",
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_THICKNESS,
            _COMMERCIAL_ELECTRIC_WRE450G_CAP_DIAMETER,
        ),
    ),
)

GENERIC_DOWNWARD_STREET_LIGHT = ComponentType(
    name="generic_downward_street_light",
    size=(18.0, 4.0, 4.0),
    color=(0.08, 0.09, 0.10, 1.0),
    default_face="narrow_neg",
)

WIFI_ACCESS_POINT = ComponentType(
    name="wifi_access_point",
    size=(5.4, 3.3, 1.34),
    color=(0.74, 0.78, 0.80, 1.0),
    default_face="wide_neg",
    mount_point=(5.4, 1.65, 0.0),
)

EV_CHARGER_BODY = ComponentType(
    name="ev_charger_body",
    size=(7.9, 7.8, 3.9),
    color=(0.055, 0.055, 0.060, 1.0),
    default_face="wide_neg",
    mount_point=(7.9, 3.9, 0.0),
    shape="mesh",
    mesh_path=(
        "assets/components/wallbox_pulsar_plus/"
        "wallbox_pulsar_plus_body.stl"
    ),
)

CARLON_E989NNJ_JUNCTION_BOX = ComponentType(
    name="carlon_e989nnj_junction_box",
    size=(4.0, 4.0, 2.0),
    color=(0.55, 0.57, 0.58, 1.0),
    default_face="wide_neg",
)


_CARLON_GRAY = (0.55, 0.57, 0.58, 1.0)

CARLON_E987N_JUNCTION_BOX = ComponentType(
    name="carlon_e987n_junction_box",
    size=(4.0, 4.0, 4.0),
    color=_CARLON_GRAY,
    default_face="wide_neg",
    shape="primitive_union",
    box_primitives=(
        ((0.0, 0.0, 0.0), (4.0, 4.0, 3.875)),
        # Gasketed cover, represented by the outermost eighth inch.
        ((0.0, 0.0, 3.875), (4.0, 4.0, 0.125)),
    ),
)


def _carlon_box_adapter(
    catalog: str,
    *,
    length: float,
    conduit_od: float,
    flange_od: float,
) -> ComponentType:
    stem_length = length * 0.72
    return ComponentType(
        name=f"carlon_{catalog.lower()}_box_adapter",
        size=(length, flange_od, flange_od),
        color=_CARLON_GRAY,
        mount_point=(0.0, flange_od / 2, flange_od / 2),
        shape="primitive_union",
        cylinder_primitives=(
            ((0.0, flange_od / 2, flange_od / 2), "along", length, conduit_od),
            (
                (stem_length, flange_od / 2, flange_od / 2),
                "along",
                length - stem_length,
                flange_od,
            ),
        ),
    )


def _carlon_coupling(
    catalog: str,
    *,
    length: float,
    outside_diameter: float,
) -> ComponentType:
    return ComponentType(
        name=f"carlon_{catalog.lower()}_coupling",
        size=(length, outside_diameter, outside_diameter),
        color=_CARLON_GRAY,
        mount_point=(0.0, outside_diameter / 2, outside_diameter / 2),
        shape="primitive_union",
        cylinder_primitives=(
            (
                (0.0, outside_diameter / 2, outside_diameter / 2),
                "along",
                length,
                outside_diameter,
            ),
        ),
    )


# Box-adapter stem diameters match the outside diameter of their conduit.
# Flange diameters not published in the catalog are conservative visual values.
CARLON_E996D_BOX_ADAPTER = _carlon_box_adapter(
    "E996D",
    length=0.85,
    conduit_od=0.840,
    flange_od=1.11,
)
CARLON_E996F_BOX_ADAPTER = _carlon_box_adapter(
    "E996F",
    length=1 + 3 / 32,
    conduit_od=1.315,
    flange_od=1.60,
)
CARLON_E996G_BOX_ADAPTER = _carlon_box_adapter(
    "E996G",
    length=1.25,
    conduit_od=1.660,
    flange_od=1.95,
)

# E943E dimensions follow the manufacturer's 3/4-inch male terminal-adapter
# drawing: 1.470-inch overall length and 1.290-inch maximum thread diameter.
CARLON_E943E_MALE_TERMINAL_ADAPTER = ComponentType(
    name="carlon_e943e_male_terminal_adapter",
    size=(1.470, 1.290, 1.290),
    color=_CARLON_GRAY,
    mount_point=(0.0, 1.290 / 2, 1.290 / 2),
    shape="primitive_union",
    cylinder_primitives=(
        ((0.0, 1.290 / 2, 1.290 / 2), "along", 0.553, 1.290),
        ((0.553, 1.290 / 2, 1.290 / 2), "along", 1.470 - 0.553, 1.064),
    ),
)

ONE_INCH_CABLE_GLAND = ComponentType(
    name="one_inch_cable_gland",
    size=(0.75, 1.0, 1.0),
    color=(0.10, 0.10, 0.11, 1.0),
    mount_point=(0.0, 0.5, 0.5),
    shape="primitive_union",
    cylinder_primitives=(
        ((0.0, 0.5, 0.5), "along", 0.75, 1.0),
    ),
)

CARLON_E940D_COUPLING = _carlon_coupling(
    "E940D",
    length=1.5,
    outside_diameter=1 + 7 / 64,
)
CARLON_E940F_COUPLING = _carlon_coupling(
    "E940F",
    length=2.0,
    outside_diameter=1 + 5 / 8,
)
CARLON_E940G_COUPLING = _carlon_coupling(
    "E940G",
    length=2 + 1 / 8,
    outside_diameter=1 + 63 / 64,
)

# The E950GF is a bell-by-spigot reducer. The published overall length is
# represented conservatively; its 1-1/4-inch end overlaps the LB outlet hub.
CARLON_E950GF_REDUCER_BUSHING = ComponentType(
    name="carlon_e950gf_reducer_bushing",
    size=(1 + 9 / 64, 1.660, 1.660),
    color=_CARLON_GRAY,
    mount_point=(0.0, 0.830, 0.830),
    shape="primitive_union",
    cylinder_primitives=(
        ((0.0, 0.830, 0.830), "along", 0.75, 1.660),
        ((0.75, 0.830, 0.830), "along", 25 / 64, 1.315),
    ),
)

_TINKERCAD_CM_TO_INCH = 1 / 2.54
_EV_CHARGER_PLUG_RAW_SIZE = (10.16, 21.844, 25.8193)

EV_CHARGER_PLUG = ComponentType(
    name="ev_charger_plug",
    size=(
        _EV_CHARGER_PLUG_RAW_SIZE[2] * _TINKERCAD_CM_TO_INCH,
        _EV_CHARGER_PLUG_RAW_SIZE[0] * _TINKERCAD_CM_TO_INCH,
        _EV_CHARGER_PLUG_RAW_SIZE[1] * _TINKERCAD_CM_TO_INCH,
    ),
    color=(0.9137254901960784, 0.11372549019607843, 0.17647058823529413, 1.0),
    default_face="wide_neg",
    mount_point=(
        _EV_CHARGER_PLUG_RAW_SIZE[2] * _TINKERCAD_CM_TO_INCH,
        _EV_CHARGER_PLUG_RAW_SIZE[0] * _TINKERCAD_CM_TO_INCH / 2,
        0.0,
    ),
    shape="mesh",
    mesh_path="assets/components/ev_charger_plug/ev_charger_plug.stl",
)


_CARLON_E983G_L1 = 8 + 21 / 32
_CARLON_E983G_H = 2 + 5 / 16
_CARLON_E983G_Q = 2 + 1 / 2
_CARLON_E983G_W = 2 + 3 / 4
_CARLON_E983G_SIDE_CHANNEL_WIDTH = _CARLON_E983G_W
_CARLON_E983G_SIDE_PROTRUSION = _CARLON_E983G_H - 0.5 * _CARLON_E983G_Q
_CARLON_E983G_FULL_WIDTH = _CARLON_E983G_H + _CARLON_E983G_SIDE_PROTRUSION

CARLON_E983G_CONDUIT_T_BODY = ComponentType(
    name="carlon_e983g_conduit_t_body",
    size=(_CARLON_E983G_L1, _CARLON_E983G_FULL_WIDTH, _CARLON_E983G_W),
    color=(0.55, 0.57, 0.58, 1.0),
    default_face="wide_neg",
    mount_point=(
        _CARLON_E983G_L1 / 2,
        _CARLON_E983G_FULL_WIDTH / 2,
        0.0,
    ),
    shape="primitive_union",
    box_primitives=(
        (
            (0.0, 0.0, 0.0),
            (_CARLON_E983G_L1, _CARLON_E983G_H, _CARLON_E983G_W),
        ),
        (
            (
                (_CARLON_E983G_L1 - _CARLON_E983G_SIDE_CHANNEL_WIDTH) / 2,
                _CARLON_E983G_H,
                0.0,
            ),
            (
                _CARLON_E983G_SIDE_CHANNEL_WIDTH,
                _CARLON_E983G_SIDE_PROTRUSION,
                _CARLON_E983G_W,
            ),
        ),
    ),
)


# E986G Type LB catalog dimensions, in inches. Local ``along`` is the rear
# projection, ``across`` is the body width, and ``out`` is the vertical axis
# when the component is mounted with the inward orientation.
_CARLON_E986G_C = 1 + 13 / 32
_CARLON_E986G_L1 = 7 + 31 / 32
_CARLON_E986G_L2 = 6 + 13 / 32
_CARLON_E986G_L3 = 6.0
_CARLON_E986G_H = 2 + 5 / 16
_CARLON_E986G_Q = 2 + 1 / 2
_CARLON_E986G_W = 2 + 3 / 4
_CARLON_E986G_HUB_OD = 1 + 63 / 64
_CARLON_E986G_OUTLET_CENTER = _CARLON_E986G_W - _CARLON_E986G_HUB_OD / 2

CARLON_E986G_LB_CONDUIT_BODY = ComponentType(
    name="carlon_e986g_lb_conduit_body",
    size=(_CARLON_E986G_W, _CARLON_E986G_Q, _CARLON_E986G_L1),
    color=_CARLON_GRAY,
    default_face="wide_neg",
    mount_point=(
        0.0,
        _CARLON_E986G_Q / 2,
        _CARLON_E986G_L1 - _CARLON_E986G_L3,
    ),
    shape="primitive_union",
    box_primitives=(
        (
            (_CARLON_E986G_C, 0.0, 0.0),
            (
                _CARLON_E986G_W - _CARLON_E986G_C,
                _CARLON_E986G_Q,
                _CARLON_E986G_L2,
            ),
        ),
        (
            (_CARLON_E986G_W - 0.125, 0.125, 0.25),
            (0.125, _CARLON_E986G_Q - 0.25, _CARLON_E986G_L2 - 0.5),
        ),
    ),
    cylinder_primitives=(
        (
            (
                0.0,
                _CARLON_E986G_Q / 2,
                _CARLON_E986G_L1 - _CARLON_E986G_L3,
            ),
            "along",
            _CARLON_E986G_H,
            _CARLON_E986G_HUB_OD,
        ),
        (
            (
                _CARLON_E986G_OUTLET_CENTER,
                _CARLON_E986G_Q / 2,
                _CARLON_E986G_L2,
            ),
            "out",
            _CARLON_E986G_L1 - _CARLON_E986G_L2,
            _CARLON_E986G_HUB_OD,
        ),
    ),
)
