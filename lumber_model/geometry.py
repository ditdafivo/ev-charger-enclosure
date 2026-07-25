from __future__ import annotations

from collections.abc import Iterable, Mapping
import math

from lumber_model.constants import AXES, AXIS_INDEX, Axis


Vector3 = tuple[float, float, float]


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


def v_add(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    )


def v_mid(a: Vector3, b: Vector3) -> Vector3:
    return (
        (a[0] + b[0]) / 2,
        (a[1] + b[1]) / 2,
        (a[2] + b[2]) / 2,
    )


def cubic_bezier_points(
    start: Vector3,
    control_a: Vector3,
    control_b: Vector3,
    end: Vector3,
    *,
    segments: int = 24,
) -> tuple[Vector3, ...]:
    """Sample a cubic Bezier centerline while preserving its exact endpoints."""
    for name, point in (
        ("start", start),
        ("control_a", control_a),
        ("control_b", control_b),
        ("end", end),
    ):
        if len(point) != 3 or not all(math.isfinite(value) for value in point):
            raise ValueError(f"{name} must be a finite 3-vector")

    if segments < 2:
        raise ValueError("Bezier segments must be at least 2")

    sampled: list[Vector3] = []
    for index in range(segments + 1):
        t = index / segments
        one_minus_t = 1 - t
        weights = (
            one_minus_t**3,
            3 * one_minus_t**2 * t,
            3 * one_minus_t * t**2,
            t**3,
        )
        sampled.append(
            tuple(
                weights[0] * start[axis]
                + weights[1] * control_a[axis]
                + weights[2] * control_b[axis]
                + weights[3] * end[axis]
                for axis in range(3)
            )
        )

    deduplicated: list[Vector3] = []
    for point in sampled:
        if not deduplicated or point != deduplicated[-1]:
            deduplicated.append(point)
    return tuple(deduplicated)


def rounded_polyline_points(
    points: Iterable[Vector3],
    bends: Mapping[int, float],
    *,
    segments: int = 12,
) -> tuple[Vector3, ...]:
    """Replace selected orthogonal polyline corners with circular quarter arcs."""
    points = tuple(points)
    if len(points) < 2:
        raise ValueError("Rounded polyline requires at least two points")
    if segments < 2:
        raise ValueError("Rounded polyline segments must be at least 2")

    sampled: list[Vector3] = []
    for index, point in enumerate(points):
        radius = bends.get(index)
        if radius is None:
            sampled.append(point)
            continue
        if index == 0 or index == len(points) - 1:
            raise ValueError("Rounded corners require previous and next points")
        if radius <= 0:
            raise ValueError("Rounded corner radius must be positive")

        previous = points[index - 1]
        next_point = points[index + 1]
        incoming = _v_unit(_v_sub(point, previous))
        outgoing = _v_unit(_v_sub(next_point, point))
        if abs(_v_dot(incoming, outgoing)) > 1e-6:
            raise ValueError("Rounded corners must be 90-degree corners")
        if _v_length(_v_sub(point, previous)) <= radius:
            raise ValueError("Rounded corner radius exceeds incoming segment")
        if _v_length(_v_sub(next_point, point)) <= radius:
            raise ValueError("Rounded corner radius exceeds outgoing segment")

        center = v_add(
            _v_sub(point, _v_scale(incoming, radius)),
            _v_scale(outgoing, radius),
        )
        start_axis = _v_scale(outgoing, -1)
        end_axis = incoming
        sampled.extend(
            v_add(
                center,
                _v_scale(
                    v_add(
                        _v_scale(start_axis, math.cos(theta)),
                        _v_scale(end_axis, math.sin(theta)),
                    ),
                    radius,
                ),
            )
            for theta in (
                (math.pi / 2) * arc_index / segments
                for arc_index in range(segments + 1)
            )
        )

    deduplicated: list[Vector3] = []
    for point in sampled:
        if not deduplicated or point != deduplicated[-1]:
            deduplicated.append(point)
    return tuple(deduplicated)


def replace_axis(v: Vector3, axis: Axis, value: float) -> Vector3:
    out = list(v)
    out[AXIS_INDEX[axis]] = value
    return tuple(out)  # type: ignore[return-value]


def other_axis(axis_a: Axis, axis_b: Axis) -> Axis:
    if axis_a == axis_b:
        raise ValueError(f"Axes must be different, got {axis_a!r} twice")

    for axis in AXES:
        if axis != axis_a and axis != axis_b:
            return axis

    raise ValueError(f"Could not determine remaining axis from {axis_a=} and {axis_b=}")


def inferred_position_axis(span_axis: Axis) -> Axis:
    """
    Default placement convention:

    - Members spanning X or Y are positioned vertically with Z.
    - Members spanning Z are positioned horizontally with X.

    This can be overridden in Lumber.between().
    """
    return "z" if span_axis in ("x", "y") else "x"
