from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import math
from typing import Literal, overload

from lumber_model.components import ComponentInstance
from lumber_model.coordinates import (
    AbsoluteCoord,
    Coordinate,
    RelativeCoord,
    resolve_coordinate,
)
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3, cubic_bezier_points
from lumber_model.lumber import Lumber


ConduitTradeSize = Literal["1/2", "3/4", "1", "1-1/4"]
ComponentAnchorPosition = tuple[float, float]
ConduitColor = tuple[float, float, float, float]
ResolvedBend = tuple[int, float]

CONDUIT_OD_BY_TRADE_SIZE: dict[ConduitTradeSize, float] = {
    "1/2": 0.840,
    "3/4": 1.050,
    "1": 1.315,
    "1-1/4": 1.660,
}

DEFAULT_CONDUIT_COLOR: ConduitColor = (0.78, 0.80, 0.78, 1.0)
DEFAULT_BEND_SEGMENTS = 12
DEFAULT_CURVE_SEGMENTS = 24


def _validate_vector2(name: str, value: ComponentAnchorPosition) -> None:
    if len(value) != 2:
        raise ValueError(f"{name} must be a 2-tuple")


def _format_vector(values: Iterable[float]) -> str:
    return "[" + ", ".join(fmt_float(value) for value in values) + "]"


def _format_points(points: Iterable[Vector3]) -> str:
    return "[" + ", ".join(_format_vector(point) for point in points) + "]"


def _format_bends(bends: Iterable[ResolvedBend]) -> str:
    return (
        "["
        + ", ".join(
            "[" + fmt_float(index) + ", " + fmt_float(radius) + "]"
            for index, radius in bends
        )
        + "]"
    )


def _v_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_scale(v: Vector3, scale: float) -> Vector3:
    return (v[0] * scale, v[1] * scale, v[2] * scale)


def _v_dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _v_length(v: Vector3) -> float:
    return math.sqrt(_v_dot(v, v))


def _v_unit(v: Vector3) -> Vector3:
    length = _v_length(v)
    if length == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return _v_scale(v, 1 / length)


def cubic_bezier_conduit_points(
    start: Vector3,
    control_a: Vector3,
    control_b: Vector3,
    end: Vector3,
    *,
    segments: int = DEFAULT_CURVE_SEGMENTS,
) -> tuple[AbsoluteCoord, ...]:
    """Sample a smooth cubic Bezier centerline for a conduit offset."""
    for name, point in (
        ("start", start),
        ("control_a", control_a),
        ("control_b", control_b),
        ("end", end),
    ):
        if len(point) != 3 or not all(math.isfinite(value) for value in point):
            raise ValueError(f"{name} must be a finite 3-vector")

    if segments < 2:
        raise ValueError("Bezier conduit segments must be at least 2")

    return tuple(
        AbsoluteCoord(*point)
        for point in cubic_bezier_points(
            start,
            control_a,
            control_b,
            end,
            segments=segments,
        )
    )


def _anchor_point(
    component: ComponentInstance,
    member: Lumber,
    anchor: ComponentAnchor,
) -> Vector3:
    resolved = component.resolved(member)
    size = component.component_type.size
    position = anchor.position
    local_point = (
        size[0] / 2 if position is None else position[0],
        size[1] / 2 if position is None else position[1],
        size[2] / 2 + anchor.depth_offset,
    )

    return _v_add(
        resolved.origin,
        _v_add(
            _v_add(
                _v_scale(resolved.along_vec, local_point[0]),
                _v_scale(resolved.across_vec, local_point[1]),
            ),
            _v_scale(resolved.out_vec, local_point[2]),
        ),
    )


def _bend_arc_points(
    previous: Vector3,
    corner: Vector3,
    next_point: Vector3,
    radius: float,
    segments: int,
) -> tuple[Vector3, ...]:
    incoming = _v_unit(_v_sub(corner, previous))
    outgoing = _v_unit(_v_sub(next_point, corner))
    dot = _v_dot(incoming, outgoing)

    if abs(dot) > 1e-6:
        raise ValueError("Conduit bends must be 90-degree corners")

    if _v_length(_v_sub(corner, previous)) <= radius:
        raise ValueError("Conduit bend radius exceeds incoming straight segment")

    if _v_length(_v_sub(next_point, corner)) <= radius:
        raise ValueError("Conduit bend radius exceeds outgoing straight segment")

    center = _v_add(
        _v_sub(corner, _v_scale(incoming, radius)),
        _v_scale(outgoing, radius),
    )
    start_axis = _v_scale(outgoing, -1)
    end_axis = incoming

    return tuple(
        _v_add(
            center,
            _v_scale(
                _v_add(
                    _v_scale(start_axis, math.cos(theta)),
                    _v_scale(end_axis, math.sin(theta)),
                ),
                radius,
            ),
        )
        for theta in (
            (math.pi / 2) * index / segments
            for index in range(segments + 1)
        )
    )


@dataclass(frozen=True)
class ComponentAnchor:
    component: str
    position: ComponentAnchorPosition | None = None
    depth_offset: float = 0.0

    def __post_init__(self) -> None:
        if self.position is not None:
            _validate_vector2(
                f"{self.component}: conduit anchor position",
                self.position,
            )


ConduitPointRef = Coordinate | ComponentAnchor


@dataclass(frozen=True)
class ConduitBend:
    point_index: int
    radius: float = 4.0
    segments: int = DEFAULT_BEND_SEGMENTS

    def __post_init__(self) -> None:
        if self.point_index < 1:
            raise ValueError("Conduit bend point_index must be at least 1")

        if self.radius <= 0:
            raise ValueError("Conduit bend radius must be positive")

        if self.segments < 2:
            raise ValueError("Conduit bend segments must be at least 2")


@dataclass(frozen=True)
class ConduitRun:
    name: str
    trade_size: ConduitTradeSize
    points: tuple[ConduitPointRef, ...]
    assembly: str = "electrical_conduit"
    color: ConduitColor = DEFAULT_CONDUIT_COLOR
    bends: tuple[ConduitBend, ...] = ()

    def __post_init__(self) -> None:
        if self.trade_size not in CONDUIT_OD_BY_TRADE_SIZE:
            raise ValueError(
                f"{self.name}: unsupported conduit trade size {self.trade_size!r}"
            )

        if len(self.points) < 2:
            raise ValueError(f"{self.name}: conduit run must have at least two points")

        if len(self.color) != 4:
            raise ValueError(f"{self.name}: color must be an RGBA 4-tuple")

        for index, point in enumerate(self.points):
            if not isinstance(point, (ComponentAnchor, AbsoluteCoord, RelativeCoord)):
                raise TypeError(
                    f"{self.name}: points[{index}] must be an AbsoluteCoord, "
                    "RelativeCoord, or ComponentAnchor"
                )

        for bend in self.bends:
            if bend.point_index >= len(self.points) - 1:
                raise ValueError(
                    f"{self.name}: bend point_index {bend.point_index} must have "
                    "both previous and next points"
                )

    @property
    def od(self) -> float:
        return CONDUIT_OD_BY_TRADE_SIZE[self.trade_size]

    def resolved(
        self,
        components_by_name: Mapping[str, ComponentInstance],
        members_by_name: Mapping[str, Lumber],
    ) -> ResolvedConduitRun:
        resolver = _ConduitCoordinateResolver(components_by_name, members_by_name)
        resolved_points: list[Vector3] = []

        for index, point in enumerate(self.points):
            if isinstance(point, ComponentAnchor):
                try:
                    component = components_by_name[point.component]
                except KeyError as exc:
                    raise KeyError(
                        f"{self.name}: unknown conduit component anchor "
                        f"{point.component!r}"
                    ) from exc

                member = members_by_name[component.member]
                resolved_points.append(_anchor_point(component, member, point))
            else:
                resolved_points.append(
                    resolve_coordinate(f"{self.name}: points[{index}]", point, resolver)
                )

        bends_by_index = {bend.point_index: bend for bend in self.bends}
        render_points: list[Vector3] = []

        for index, point in enumerate(resolved_points):
            bend = bends_by_index.get(index)
            if bend is None:
                render_points.append(point)
                continue

            arc_points = _bend_arc_points(
                resolved_points[index - 1],
                point,
                resolved_points[index + 1],
                bend.radius,
                bend.segments,
            )
            render_points.extend(arc_points)

        return ResolvedConduitRun(
            name=self.name,
            assembly=self.assembly,
            trade_size=self.trade_size,
            od=self.od,
            color=self.color,
            points=tuple(render_points),
            bends=tuple((bend.point_index, bend.radius) for bend in self.bends),
        )


@dataclass(frozen=True)
class _ConduitCoordinateResolver:
    components_by_name: Mapping[str, ComponentInstance]
    members_by_name: Mapping[str, Lumber]

    def resolve_coordinate_reference(self, name: str) -> Vector3:
        component = self.components_by_name.get(name)
        if component is not None:
            member = self.members_by_name[component.member]
            return _anchor_point(component, member, ComponentAnchor(name))

        member = self.members_by_name.get(name)
        if member is not None:
            return member.start

        raise KeyError(f"Unknown coordinate reference {name!r}")


@dataclass(frozen=True)
class ResolvedConduitRun:
    name: str
    assembly: str
    trade_size: ConduitTradeSize
    od: float
    color: ConduitColor
    points: tuple[Vector3, ...]
    bends: tuple[ResolvedBend, ...]

    def scad_record(self) -> str:
        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{scad_string(self.trade_size)}, "
            f"{fmt_float(self.od)}, "
            f"{_format_vector(self.color)}, "
            f"{_format_points(self.points)}, "
            f"{_format_bends(self.bends)}"
            "]"
        )


ConduitRef = str | ConduitRun


class ConduitCollection(Mapping[str, ConduitRun]):
    def __init__(
        self,
        conduits: Mapping[str, ConduitRun] | Iterable[ConduitRun] | None = None,
    ):
        self._conduits: dict[str, ConduitRun] = {}

        if conduits is None:
            return

        if isinstance(conduits, Mapping):
            for name, conduit in conduits.items():
                if name != conduit.name:
                    raise ValueError(
                        f"Conduit key {name!r} does not match conduit name "
                        f"{conduit.name!r}"
                    )
                self._store(conduit)
            return

        for conduit in conduits:
            self._store(conduit)

    def add(
        self,
        name: str,
        *,
        trade_size: ConduitTradeSize,
        points: Iterable[ConduitPointRef],
        assembly: str = "electrical_conduit",
        color: ConduitColor = DEFAULT_CONDUIT_COLOR,
        bends: Iterable[ConduitBend] = (),
    ) -> ConduitRun:
        return self._store(
            ConduitRun(
                name=name,
                trade_size=trade_size,
                points=tuple(points),
                assembly=assembly,
                color=color,
                bends=tuple(bends),
            )
        )

    @overload
    def get(self, name: str) -> ConduitRun | None: ...

    @overload
    def get(self, name: str, default: ConduitRun) -> ConduitRun: ...

    def get(self, name: str, default: ConduitRun | None = None) -> ConduitRun | None:
        return self._conduits.get(name, default)

    def resolve(self, ref: ConduitRef) -> ConduitRun:
        if isinstance(ref, ConduitRun):
            return ref

        try:
            return self._conduits[ref]
        except KeyError as exc:
            raise KeyError(f"Unknown conduit {ref!r}") from exc

    def as_dict(self) -> dict[str, ConduitRun]:
        return dict(self._conduits)

    def _store(self, conduit: ConduitRun) -> ConduitRun:
        if conduit.name in self._conduits:
            raise ValueError(f"Duplicate conduit name: {conduit.name}")

        self._conduits[conduit.name] = conduit
        return conduit

    def __getitem__(self, name: str) -> ConduitRun:
        return self._conduits[name]

    def __contains__(self, name: object) -> bool:
        return name in self._conduits

    def __iter__(self) -> Iterator[str]:
        return iter(self._conduits)

    def __len__(self) -> int:
        return len(self._conduits)
