from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import math
from typing import overload

from lumber_model.components import ResolvedComponent
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3, rounded_polyline_points
from lumber_model.ground import ResolvedGroundPlane


CableColor = tuple[float, float, float, float]
DEFAULT_CABLE_COLOR: CableColor = (0.055, 0.055, 0.06, 1.0)
DEFAULT_CURVE_SEGMENTS = 24
MINIMUM_BEND_RADIUS_MULTIPLIER = 5.0


def rounded_cable_points(
    points: Iterable[Vector3],
    bends: Mapping[int, float],
    *,
    segments: int = 12,
) -> tuple[Vector3, ...]:
    """Build a cable centerline with circular arcs at selected 90-degree turns."""
    return rounded_polyline_points(points, bends, segments=segments)


def _format_vector(values: Iterable[float]) -> str:
    return "[" + ", ".join(fmt_float(value) for value in values) + "]"


def _format_points(points: Iterable[Vector3]) -> str:
    return "[" + ", ".join(_format_vector(point) for point in points) + "]"


def _v_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_scale(v: Vector3, scale: float) -> Vector3:
    return (v[0] * scale, v[1] * scale, v[2] * scale)


def _distance(a: Vector3, b: Vector3) -> float:
    delta = _v_sub(b, a)
    return math.sqrt(delta[0] ** 2 + delta[1] ** 2 + delta[2] ** 2)


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _length(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def cable_centerline_length(points: Iterable[Vector3]) -> float:
    points = tuple(points)
    return sum(_distance(a, b) for a, b in zip(points, points[1:]))


def minimum_cable_bend_radius(points: Iterable[Vector3]) -> float:
    """Estimate minimum centerline radius from circumcircles of sampled points."""
    points = tuple(points)
    minimum = math.inf

    for a, b, c in zip(points, points[1:], points[2:]):
        ab = _distance(a, b)
        bc = _distance(b, c)
        ac = _distance(a, c)
        twice_area = _length(_cross(_v_sub(b, a), _v_sub(c, a)))
        if twice_area <= 1e-9 * ab * bc:
            continue

        minimum = min(minimum, ab * bc * ac / (2 * twice_area))

    return minimum


@dataclass(frozen=True)
class CableRun:
    name: str
    diameter: float
    points: tuple[Vector3, ...]
    assembly: str = "ev_charger_cable"
    color: CableColor = DEFAULT_CABLE_COLOR

    def __post_init__(self) -> None:
        if self.diameter <= 0:
            raise ValueError(f"{self.name}: cable diameter must be positive")

        if len(self.points) < 2:
            raise ValueError(f"{self.name}: cable run must have at least two points")

        if len(self.color) != 4:
            raise ValueError(f"{self.name}: cable color must be an RGBA tuple")

        for index, point in enumerate(self.points):
            if len(point) != 3:
                raise ValueError(f"{self.name}: points[{index}] must be a 3-tuple")

    @property
    def centerline_length(self) -> float:
        return cable_centerline_length(self.points)

    def resolved(self) -> ResolvedCableRun:
        return ResolvedCableRun(
            name=self.name,
            assembly=self.assembly,
            diameter=self.diameter,
            color=self.color,
            points=self.points,
            centerline_length=self.centerline_length,
        )


@dataclass(frozen=True)
class ResolvedCableRun:
    name: str
    assembly: str
    diameter: float
    color: CableColor
    points: tuple[Vector3, ...]
    centerline_length: float

    def scad_record(self) -> str:
        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{fmt_float(self.diameter)}, "
            f"{_format_vector(self.color)}, "
            f"{_format_points(self.points)}, "
            f"{fmt_float(self.centerline_length)}"
            "]"
        )


CableRef = str | CableRun


class CableCollection(Mapping[str, CableRun]):
    def __init__(
        self,
        cables: Mapping[str, CableRun] | Iterable[CableRun] | None = None,
    ):
        self._cables: dict[str, CableRun] = {}

        if cables is None:
            return

        if isinstance(cables, Mapping):
            for name, cable in cables.items():
                if name != cable.name:
                    raise ValueError(
                        f"Cable key {name!r} does not match cable name {cable.name!r}"
                    )
                self._store(cable)
            return

        for cable in cables:
            self._store(cable)

    def add(
        self,
        name: str,
        *,
        diameter: float,
        points: Iterable[Vector3],
        assembly: str = "ev_charger_cable",
        color: CableColor = DEFAULT_CABLE_COLOR,
    ) -> CableRun:
        return self._store(
            CableRun(
                name=name,
                diameter=diameter,
                points=tuple(points),
                assembly=assembly,
                color=color,
            )
        )

    @overload
    def get(self, name: str) -> CableRun | None: ...

    @overload
    def get(self, name: str, default: CableRun) -> CableRun: ...

    def get(self, name: str, default: CableRun | None = None) -> CableRun | None:
        return self._cables.get(name, default)

    def resolve(self, ref: CableRef) -> CableRun:
        if isinstance(ref, CableRun):
            return ref

        try:
            return self._cables[ref]
        except KeyError as exc:
            raise KeyError(f"Unknown cable {ref!r}") from exc

    def as_dict(self) -> dict[str, CableRun]:
        return dict(self._cables)

    def _store(self, cable: CableRun) -> CableRun:
        if cable.name in self._cables:
            raise ValueError(f"Duplicate cable name: {cable.name}")

        self._cables[cable.name] = cable
        return cable

    def __getitem__(self, name: str) -> CableRun:
        return self._cables[name]

    def __contains__(self, name: object) -> bool:
        return name in self._cables

    def __iter__(self) -> Iterator[str]:
        return iter(self._cables)

    def __len__(self) -> int:
        return len(self._cables)


def _component_local_point(
    component: ResolvedComponent,
    along: float,
    across: float,
    out: float,
) -> Vector3:
    return _v_add(
        component.origin,
        _v_add(
            _v_add(
                _v_scale(component.along_vec, along),
                _v_scale(component.across_vec, across),
            ),
            _v_scale(component.out_vec, out),
        ),
    )


def _ground_z(ground: ResolvedGroundPlane, x: float, y: float) -> float:
    normal = ground.normal
    if abs(normal[2]) < 1e-9:
        raise ValueError("Cable clearance requires a non-vertical ground plane")

    return ground.origin[2] - (
        normal[0] * (x - ground.origin[0])
        + normal[1] * (y - ground.origin[1])
    ) / normal[2]


def _append_point(points: list[Vector3], point: Vector3) -> None:
    if not points or _distance(points[-1], point) > 1e-9:
        points.append(point)


def _append_bottom_arc(
    points: list[Vector3],
    *,
    start_x: float,
    end_x: float,
    y: float,
    low_z: float,
    segments: int,
) -> None:
    radius = abs(end_x - start_x) / 2
    center_x = (start_x + end_x) / 2
    tangent_z = low_z + radius
    direction = 1 if end_x > start_x else -1

    for index in range(segments + 1):
        theta = math.pi * index / segments
        _append_point(
            points,
            (
                center_x - direction * radius * math.cos(theta),
                y,
                tangent_z - radius * math.sin(theta),
            ),
        )


def _spiral_point(
    phase: float,
    *,
    revolution: int,
    spacing: float,
    base_left: float,
    base_right: float,
    base_y: float,
    base_low_z: float,
    base_top_z: float,
) -> Vector3:
    # Each visible pass holds a constant X/Z outline and depth. The bottom arc
    # transitions smoothly to the next pass, which is one cable width farther
    # out in X/Z and toward the viewer.
    transition = 0.0 if phase <= 0.75 else (phase - 0.75) / 0.25
    pass_progress = transition**2 * (3 - 2 * transition)
    offset = spacing * (revolution + pass_progress)
    left = base_left - offset
    right = base_right + offset
    y = base_y + offset
    radius = (right - left) / 2
    center_x = (right + left) / 2
    bottom_tangent = base_low_z + (base_right - base_left) / 2
    top_tangent = base_top_z - (base_right - base_left) / 2

    if phase <= 0.25:
        fraction = phase / 0.25
        z = bottom_tangent + fraction * (top_tangent - bottom_tangent)
        return (right, y, z)

    if phase <= 0.5:
        fraction = (phase - 0.25) / 0.25
        theta = math.pi * fraction
        return (
            center_x + radius * math.cos(theta),
            y,
            top_tangent + radius * math.sin(theta),
        )

    if phase <= 0.75:
        fraction = (phase - 0.5) / 0.25
        z = top_tangent + fraction * (bottom_tangent - top_tangent)
        return (left, y, z)

    fraction = (phase - 0.75) / 0.25
    theta = math.pi * fraction
    return (
        center_x - radius * math.cos(theta),
        y,
        bottom_tangent - radius * math.sin(theta),
    )


def _append_spiral_revolution(
    points: list[Vector3],
    *,
    revolution: int,
    spacing: float,
    base_left: float,
    base_right: float,
    base_y: float,
    base_low_z: float,
    base_top_z: float,
    segments: int,
) -> None:
    phases = [0.0, 0.25]
    phases.extend(
        0.25 + 0.25 * index / segments for index in range(1, segments + 1)
    )
    phases.append(0.75)
    phases.extend(
        0.75 + 0.25 * index / segments for index in range(1, segments + 1)
    )

    for phase in phases:
        _append_point(
            points,
            _spiral_point(
                phase,
                revolution=revolution,
                spacing=spacing,
                base_left=base_left,
                base_right=base_right,
                base_y=base_y,
                base_low_z=base_low_z,
                base_top_z=base_top_z,
            ),
        )


def _terminal_route(
    candidate: Vector3,
    end: Vector3,
    *,
    tangent_z: float,
    segments: int,
) -> tuple[Vector3, ...]:
    horizontal = (end[0] - candidate[0], end[1] - candidate[1], 0.0)
    separation = _length(horizontal)
    if separation == 0:
        raise ValueError("Terminal cable plane requires distinct XY points")

    horizontal_unit = _v_scale(horizontal, 1 / separation)
    radius = separation / 2
    route: list[Vector3] = [candidate]
    _append_point(route, (candidate[0], candidate[1], tangent_z))

    for index in range(1, segments + 1):
        fraction = index / segments
        theta = math.pi * fraction
        horizontal_distance = radius * (1 - math.cos(theta))
        _append_point(
            route,
            (
                candidate[0] + horizontal_unit[0] * horizontal_distance,
                candidate[1] + horizontal_unit[1] * horizontal_distance,
                tangent_z - radius * math.sin(theta),
            ),
        )
    _append_point(route, end)
    return tuple(route)


def _trim_to_length_and_terminate(
    path: list[Vector3],
    end: Vector3,
    target_length: float,
    *,
    base_left: float,
    minimum_radius: float,
    segments: int,
) -> tuple[Vector3, ...]:
    prefix = 0.0
    candidates: list[tuple[float, tuple[Vector3, ...]]] = []

    for index, (a, b) in enumerate(zip(path, path[1:])):
        segment_length = _distance(a, b)
        is_left_descent = (
            abs(a[0] - b[0]) < 1e-9
            and abs(a[1] - b[1]) < 1e-9
            and b[2] < a[2]
            and a[0] <= base_left + 1e-9
        )

        if is_left_descent:
            separation = math.hypot(end[0] - b[0], end[1] - b[1])
            radius = separation / 2
            if radius >= minimum_radius:
                arc_length = (
                    2 * segments * radius * math.sin(math.pi / (2 * segments))
                )
                prefix_at_b = prefix + segment_length
                tangent_z = (
                    prefix_at_b + b[2] + arc_length + end[2] - target_length
                ) / 2

                if tangent_z <= min(a[2], end[2]):
                    cutoff_z = max(b[2], tangent_z)
                    cutoff = (b[0], b[1], cutoff_z)
                    prefix_at_cutoff = prefix_at_b - (cutoff_z - b[2])
                    terminal = _terminal_route(
                        cutoff,
                        end,
                        tangent_z=tangent_z,
                        segments=segments,
                    )
                    result = path[: index + 1]
                    _append_point(result, cutoff)
                    consumed_loop_low_z = min(point[2] for point in result)
                    for point in terminal[1:]:
                        _append_point(result, point)

                    total = prefix_at_cutoff + cable_centerline_length(terminal)
                    if math.isclose(total, target_length, abs_tol=1e-7):
                        return_low_z = tangent_z - radius
                        candidates.append(
                            (abs(return_low_z - consumed_loop_low_z), tuple(result))
                        )

        prefix += segment_length

    if not candidates:
        raise ValueError(
            "Cable path has no exact-length terminal return satisfying the minimum "
            "bend radius"
        )

    candidates.sort(key=lambda candidate: candidate[0])
    return candidates[0][1]


def ev_charger_cable_points(
    body: ResolvedComponent,
    plug: ResolvedComponent,
    ground: ResolvedGroundPlane,
    *,
    length: float = 25 * 12,
    diameter: float = 0.8,
    spacing: float = 0.8,
    ground_clearance: float = 3.0,
    curve_segments: int = DEFAULT_CURVE_SEGMENTS,
) -> tuple[Vector3, ...]:
    """Build the expanding, depth-stacked cable centerline for the front charger."""
    if length <= 0:
        raise ValueError("Cable length must be positive")
    if diameter <= 0 or spacing < diameter:
        raise ValueError("Cable spacing must be at least its positive diameter")
    if curve_segments < 4:
        raise ValueError("Cable curves require at least four segments")

    expected_axes = ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    for component in (body, plug):
        axes = (component.along_vec, component.across_vec, component.out_vec)
        if axes != expected_axes:
            raise ValueError("EV charger cable requires upright front-mounted components")

    body_size = body.box_size
    plug_size = plug.box_size
    radius = diameter / 2
    minimum_bend_radius = MINIMUM_BEND_RADIUS_MULTIPLIER * diameter
    start = _component_local_point(body, 0.0, 2.0, body_size[1] / 2)
    end = _component_local_point(plug, 0.0, plug_size[0] / 2, plug_size[1])

    body_left = body.box_min[0]
    body_right = body.box_min[0] + body.box_size[0]
    plug_top = plug.box_min[2] + plug.box_size[2]
    base_y = start[1]
    required_terminal_separation = 2 * minimum_bend_radius
    terminal_plane_left_limit = (
        end[0]
        + (end[1] - base_y)
        - required_terminal_separation * math.sqrt(2)
    )
    base_left = min(body_left - radius, terminal_plane_left_limit)
    base_right = max(body_right + radius, start[0] + 2 * minimum_bend_radius)
    base_loop_radius = (base_right - base_left) / 2
    loop_center_x = (base_left + base_right) / 2
    plug_left = plug.box_min[0]
    plug_right = plug.box_min[0] + plug.box_size[0]
    farthest_plug_edge = max(
        abs(plug_left - loop_center_x),
        abs(plug_right - loop_center_x),
    )
    if farthest_plug_edge >= base_loop_radius:
        raise ValueError("EV charger plug is too wide for the cable's top loop")
    corner_rise = math.sqrt(base_loop_radius**2 - farthest_plug_edge**2)
    base_top_z = plug_top + radius + base_loop_radius - corner_rise
    if base_loop_radius < minimum_bend_radius:
        raise ValueError(
            "EV charger loop cannot satisfy the cable's minimum bend radius"
        )
    lead_radius = (base_right - start[0]) / 2
    lead_low_x = (start[0] + base_right) / 2
    base_low_z = (
        _ground_z(ground, lead_low_x, base_y) + ground_clearance + radius
    )
    lead_tangent_z = base_low_z + lead_radius
    bottom_tangent_z = base_low_z + base_loop_radius

    path: list[Vector3] = [start]
    _append_point(path, (start[0], base_y, lead_tangent_z))
    _append_bottom_arc(
        path,
        start_x=start[0],
        end_x=base_right,
        y=base_y,
        low_z=base_low_z,
        segments=curve_segments,
    )
    _append_point(path, (base_right, base_y, bottom_tangent_z))

    revolution = 0
    while cable_centerline_length(path) < length + 100:
        _append_spiral_revolution(
            path,
            revolution=revolution,
            spacing=spacing,
            base_left=base_left,
            base_right=base_right,
            base_y=base_y,
            base_low_z=base_low_z,
            base_top_z=base_top_z,
            segments=curve_segments,
        )
        revolution += 1

    result = _trim_to_length_and_terminate(
        path,
        end,
        length,
        base_left=base_left,
        minimum_radius=minimum_bend_radius,
        segments=curve_segments,
    )
    if not math.isclose(cable_centerline_length(result), length, abs_tol=1e-7):
        raise AssertionError("Generated cable centerline did not match target length")
    measured_radius = minimum_cable_bend_radius(result)
    if measured_radius < minimum_bend_radius - 1e-6:
        raise AssertionError(
            "Generated cable centerline violates its minimum bend radius: "
            f"{measured_radius:.4f} < {minimum_bend_radius:.4f}"
        )
    return result
