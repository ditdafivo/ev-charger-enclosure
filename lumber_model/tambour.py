from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import math
from typing import overload

from lumber_model.coordinates import (
    AbsoluteCoord,
    Coordinate,
    CoordinateResolver,
    RelativeCoord,
    resolve_coordinate,
)
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3


TambourColor = tuple[float, float, float, float]
ResolvedTambourBend = tuple[int, float]
ResolvedTambourSlat = tuple[Vector3, Vector3, Vector3]

DEFAULT_TRACK_COLOR: TambourColor = (0.35, 0.37, 0.39, 1.0)
DEFAULT_SLAT_COLOR: TambourColor = (0.67, 0.42, 0.20, 1.0)
DEFAULT_BEND_SEGMENTS = 12


@dataclass(frozen=True)
class TambourInstalledDetails:
    """Installed hardware dimensions used by the enclosure visualization.

    All dimensions are inches.  A tambour without this record retains the
    original lightweight centerline-track rendering.
    """

    channel_internal_width: float
    channel_wall_thickness: float
    mounting_flange_thickness: float
    flange_extension: float
    slat_end_engagement: float
    segment_seams: tuple[float, ...] = ()
    joint_gap: float = 0.0
    loading_section_length: float = 0.0
    end_stop_length: float = 0.0
    webbing_count: int = 3
    webbing_width: float = 1.0
    webbing_thickness: float = 1 / 16
    pull_slat_indices: tuple[int, ...] = (0, 23)
    handle_width: float = 300 / 25.4
    handle_height: float = (0.75 * 25.4 - 1) / 25.4
    handle_projection: float = 0.625
    webbing_color: TambourColor = (0.08, 0.08, 0.08, 1.0)
    handle_color: TambourColor = (0.28, 0.30, 0.32, 1.0)

    def __post_init__(self) -> None:
        positive_fields = (
            "channel_internal_width",
            "channel_wall_thickness",
            "mounting_flange_thickness",
            "flange_extension",
            "slat_end_engagement",
            "webbing_width",
            "webbing_thickness",
            "handle_width",
            "handle_height",
            "handle_projection",
        )
        for field_name in positive_fields:
            value = getattr(self, field_name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field_name} must be finite and positive")
        if self.webbing_count < 1:
            raise ValueError("webbing_count must be at least one")
        if self.joint_gap < 0 or self.loading_section_length < 0:
            raise ValueError("joint gap and loading-section length cannot be negative")
        if self.end_stop_length < 0:
            raise ValueError("end_stop_length cannot be negative")
        if any(distance <= 0 for distance in self.segment_seams):
            raise ValueError("segment seams must be positive path distances")
        if tuple(sorted(set(self.segment_seams))) != self.segment_seams:
            raise ValueError("segment seams must be sorted and unique")
        if any(index < 0 for index in self.pull_slat_indices):
            raise ValueError("pull slat indices cannot be negative")
        if len(self.webbing_color) != 4 or len(self.handle_color) != 4:
            raise ValueError("installed-detail colors must be RGBA 4-tuples")


def _format_vector(values: Iterable[float]) -> str:
    return "[" + ", ".join(fmt_float(value) for value in values) + "]"


def _format_points(points: Iterable[Vector3]) -> str:
    return "[" + ", ".join(_format_vector(point) for point in points) + "]"


def _format_bends(bends: Iterable[ResolvedTambourBend]) -> str:
    return (
        "["
        + ", ".join(
            "[" + fmt_float(index) + ", " + fmt_float(radius) + "]"
            for index, radius in bends
        )
        + "]"
    )


def _format_slats(slats: Iterable[ResolvedTambourSlat]) -> str:
    return (
        "["
        + ", ".join(
            "["
            + ", ".join(_format_vector(vector) for vector in slat)
            + "]"
            for slat in slats
        )
        + "]"
    )


def _v_add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_scale(vector: Vector3, scale: float) -> Vector3:
    return (vector[0] * scale, vector[1] * scale, vector[2] * scale)


def _v_dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _v_cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _v_length(vector: Vector3) -> float:
    return math.sqrt(_v_dot(vector, vector))


def _v_unit(vector: Vector3) -> Vector3:
    length = _v_length(vector)
    if length == 0:
        raise ValueError("Cannot normalize a zero-length vector")
    return _v_scale(vector, 1 / length)


def _bend_arc_points(
    previous: Vector3,
    corner: Vector3,
    next_point: Vector3,
    radius: float,
    segments: int,
) -> tuple[Vector3, ...]:
    incoming = _v_unit(_v_sub(corner, previous))
    outgoing = _v_unit(_v_sub(next_point, corner))

    if abs(_v_dot(incoming, outgoing)) > 1e-6:
        raise ValueError("Tambour bends must be 90-degree corners")

    if _v_length(_v_sub(corner, previous)) <= radius:
        raise ValueError("Tambour bend radius exceeds incoming straight segment")

    if _v_length(_v_sub(next_point, corner)) <= radius:
        raise ValueError("Tambour bend radius exceeds outgoing straight segment")

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
            (math.pi / 2) * index / segments for index in range(segments + 1)
        )
    )


def _path_lengths(points: tuple[Vector3, ...]) -> tuple[tuple[float, ...], float]:
    cumulative = [0.0]
    for start, end in zip(points, points[1:]):
        segment_length = _v_length(_v_sub(end, start))
        if segment_length == 0:
            raise ValueError("Tambour tracks cannot contain zero-length segments")
        cumulative.append(cumulative[-1] + segment_length)
    return tuple(cumulative), cumulative[-1]


def _sample_path(
    points: tuple[Vector3, ...],
    cumulative: tuple[float, ...],
    distance: float,
) -> tuple[Vector3, Vector3]:
    for index, segment_end in enumerate(cumulative[1:]):
        if distance <= segment_end or index == len(points) - 2:
            start = points[index]
            end = points[index + 1]
            tangent = _v_unit(_v_sub(end, start))
            segment_start = cumulative[index]
            return _v_add(start, _v_scale(tangent, distance - segment_start)), tangent

    raise ValueError("Tambour path sampling exceeded the track length")


@dataclass(frozen=True)
class TambourBend:
    point_index: int
    radius: float = 3.0
    segments: int = DEFAULT_BEND_SEGMENTS

    def __post_init__(self) -> None:
        if self.point_index < 1:
            raise ValueError("Tambour bend point_index must be at least 1")
        if self.radius <= 0:
            raise ValueError("Tambour bend radius must be positive")
        if self.segments < 2:
            raise ValueError("Tambour bend segments must be at least 2")


@dataclass(frozen=True)
class TambourDoor:
    name: str
    left_points: tuple[Coordinate, ...]
    right_points: tuple[Coordinate, ...]
    assembly: str = "tambour"
    bends: tuple[TambourBend, ...] = ()
    track_diameter: float = 0.5
    slat_pitch: float = 1.0
    slat_thickness: float = 0.9
    slat_depth: float = 0.75
    slat_track_offset: float = 0.0
    slat_envelope_depth: float | None = None
    installed_details: TambourInstalledDetails | None = None
    door_length: float = 14.0
    track_color: TambourColor = DEFAULT_TRACK_COLOR
    slat_color: TambourColor = DEFAULT_SLAT_COLOR

    def __post_init__(self) -> None:
        if len(self.left_points) < 2 or len(self.right_points) < 2:
            raise ValueError(f"{self.name}: tambour tracks need at least two points")
        if len(self.left_points) != len(self.right_points):
            raise ValueError(f"{self.name}: left and right tracks must align")

        for side, points in (("left", self.left_points), ("right", self.right_points)):
            for index, point in enumerate(points):
                if not isinstance(point, (AbsoluteCoord, RelativeCoord)):
                    raise TypeError(
                        f"{self.name}: {side}_points[{index}] must be an "
                        "AbsoluteCoord or RelativeCoord"
                    )

        bend_indices = [bend.point_index for bend in self.bends]
        if len(set(bend_indices)) != len(bend_indices):
            raise ValueError(f"{self.name}: duplicate tambour bend point indexes")
        for bend in self.bends:
            if bend.point_index >= len(self.left_points) - 1:
                raise ValueError(
                    f"{self.name}: bend point_index {bend.point_index} must have "
                    "both previous and next points"
                )

        for field_name in (
            "track_diameter",
            "slat_pitch",
            "slat_thickness",
            "slat_depth",
            "door_length",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{self.name}: {field_name} must be positive")
        if self.slat_thickness >= self.slat_pitch:
            raise ValueError(
                f"{self.name}: slat_thickness must be less than slat_pitch"
            )
        if self.slat_track_offset < 0:
            raise ValueError(f"{self.name}: slat_track_offset cannot be negative")
        envelope_depth = (
            self.slat_depth
            if self.slat_envelope_depth is None
            else self.slat_envelope_depth
        )
        if not math.isfinite(envelope_depth) or envelope_depth <= 0:
            raise ValueError(
                f"{self.name}: slat_envelope_depth must be finite and positive"
            )
        if envelope_depth < self.slat_depth:
            raise ValueError(
                f"{self.name}: slat_envelope_depth cannot be less than slat_depth"
            )
        if self.slat_track_offset > envelope_depth / 2:
            raise ValueError(
                f"{self.name}: slat_track_offset must remain within the envelope"
            )
        if len(self.track_color) != 4 or len(self.slat_color) != 4:
            raise ValueError(f"{self.name}: tambour colors must be RGBA 4-tuples")

    def resolved(
        self, resolver: CoordinateResolver | None = None
    ) -> ResolvedTambourDoor:
        envelope_depth = (
            self.slat_depth
            if self.slat_envelope_depth is None
            else self.slat_envelope_depth
        )
        left = tuple(
            resolve_coordinate(f"{self.name}: left_points[{index}]", point, resolver)
            for index, point in enumerate(self.left_points)
        )
        right = tuple(
            resolve_coordinate(f"{self.name}: right_points[{index}]", point, resolver)
            for index, point in enumerate(self.right_points)
        )
        bends_by_index = {bend.point_index: bend for bend in self.bends}

        def expand(points: tuple[Vector3, ...]) -> tuple[Vector3, ...]:
            render_points: list[Vector3] = []
            for index, point in enumerate(points):
                bend = bends_by_index.get(index)
                if bend is None:
                    render_points.append(point)
                else:
                    render_points.extend(
                        _bend_arc_points(
                            points[index - 1],
                            point,
                            points[index + 1],
                            bend.radius,
                            bend.segments,
                        )
                    )
            return tuple(render_points)

        resolved_left = expand(left)
        resolved_right = expand(right)
        left_lengths, left_total = _path_lengths(resolved_left)
        right_lengths, right_total = _path_lengths(resolved_right)

        if not math.isclose(left_total, right_total, abs_tol=1e-6):
            raise ValueError(f"{self.name}: left and right track lengths must match")
        if self.door_length > left_total:
            raise ValueError(f"{self.name}: door_length exceeds the track length")

        slat_count = max(1, math.floor(self.door_length / self.slat_pitch))
        if self.installed_details is not None:
            details = self.installed_details
            if details.segment_seams and details.segment_seams[-1] >= left_total:
                raise ValueError(f"{self.name}: segment seam exceeds the track length")
            if details.loading_section_length >= left_total:
                raise ValueError(
                    f"{self.name}: loading section exceeds the track length"
                )
            if details.handle_width > _v_length(_v_sub(right[0], left[0])):
                raise ValueError(f"{self.name}: handle width exceeds the slat span")
            if any(index >= slat_count for index in details.pull_slat_indices):
                raise ValueError(f"{self.name}: pull slat index exceeds the curtain")

        def resolve_slats(
            distances: Iterable[float],
        ) -> tuple[ResolvedTambourSlat, ...]:
            slats: list[ResolvedTambourSlat] = []
            for distance in distances:
                left_point, left_tangent = _sample_path(
                    resolved_left, left_lengths, distance
                )
                right_point, right_tangent = _sample_path(
                    resolved_right, right_lengths, distance
                )
                tangent = _v_unit(_v_add(left_tangent, right_tangent))
                span = _v_unit(_v_sub(right_point, left_point))
                inward = _v_unit(_v_cross(span, tangent))
                center_offset = _v_scale(inward, -self.slat_track_offset)
                slats.append(
                    (
                        _v_add(left_point, center_offset),
                        _v_add(right_point, center_offset),
                        tangent,
                    )
                )
            return tuple(slats)

        def resolve_track_samples(
            distances: Iterable[float],
        ) -> tuple[ResolvedTambourSlat, ...]:
            samples: list[ResolvedTambourSlat] = []
            for distance in distances:
                left_point, left_tangent = _sample_path(
                    resolved_left, left_lengths, distance
                )
                right_point, right_tangent = _sample_path(
                    resolved_right, right_lengths, distance
                )
                samples.append(
                    (
                        left_point,
                        right_point,
                        _v_unit(_v_add(left_tangent, right_tangent)),
                    )
                )
            return tuple(samples)

        open_slats = resolve_slats(
            left_total - (index + 0.5) * self.slat_pitch
            for index in reversed(range(slat_count))
        )
        closed_slats = resolve_slats(
            (index + 0.5) * self.slat_pitch for index in range(slat_count)
        )
        installed_seams = (
            resolve_track_samples(self.installed_details.segment_seams)
            if self.installed_details is not None
            else ()
        )

        return ResolvedTambourDoor(
            name=self.name,
            assembly=self.assembly,
            track_color=self.track_color,
            slat_color=self.slat_color,
            track_diameter=self.track_diameter,
            slat_pitch=self.slat_pitch,
            slat_thickness=self.slat_thickness,
            slat_depth=self.slat_depth,
            slat_track_offset=self.slat_track_offset,
            slat_envelope_depth=envelope_depth,
            installed_details=self.installed_details,
            installed_seams=installed_seams,
            left_points=resolved_left,
            right_points=resolved_right,
            bends=tuple((bend.point_index, bend.radius) for bend in self.bends),
            slats=open_slats,
            closed_slats=closed_slats,
        )


@dataclass(frozen=True)
class ResolvedTambourDoor:
    name: str
    assembly: str
    track_color: TambourColor
    slat_color: TambourColor
    track_diameter: float
    slat_pitch: float
    slat_thickness: float
    slat_depth: float
    slat_track_offset: float
    slat_envelope_depth: float
    installed_details: TambourInstalledDetails | None
    installed_seams: tuple[ResolvedTambourSlat, ...]
    left_points: tuple[Vector3, ...]
    right_points: tuple[Vector3, ...]
    bends: tuple[ResolvedTambourBend, ...]
    slats: tuple[ResolvedTambourSlat, ...]
    closed_slats: tuple[ResolvedTambourSlat, ...]

    def track_samples(
        self, subdivisions: int = 1
    ) -> tuple[ResolvedTambourSlat, ...]:
        """Sample both track centerlines for support/clearance checks.

        Resolved bend arcs are already faceted according to ``TambourBend``.
        Additional subdivisions sample the interior of every straight or arc
        facet. Shared endpoints are returned for both adjacent facets because
        each rendered channel segment has its own cross-section orientation.
        """
        if subdivisions < 1:
            raise ValueError("track sample subdivisions must be at least one")

        samples: list[ResolvedTambourSlat] = []
        for left_start, left_end, right_start, right_end in zip(
            self.left_points,
            self.left_points[1:],
            self.right_points,
            self.right_points[1:],
        ):
            left_delta = _v_sub(left_end, left_start)
            right_delta = _v_sub(right_end, right_start)
            tangent = _v_unit(
                _v_add(_v_unit(left_delta), _v_unit(right_delta))
            )
            for step in range(subdivisions + 1):
                fraction = step / subdivisions
                samples.append(
                    (
                        _v_add(left_start, _v_scale(left_delta, fraction)),
                        _v_add(right_start, _v_scale(right_delta, fraction)),
                        tangent,
                    )
                )
        return tuple(samples)

    def scad_record(self) -> str:
        details = self.installed_details
        installed_record = (
            "[]"
            if details is None
            else "["
            + ", ".join(
                (
                    fmt_float(details.channel_internal_width),
                    fmt_float(details.channel_wall_thickness),
                    fmt_float(details.mounting_flange_thickness),
                    fmt_float(details.flange_extension),
                    fmt_float(details.slat_end_engagement),
                    _format_slats(self.installed_seams),
                    fmt_float(details.joint_gap),
                    fmt_float(details.loading_section_length),
                    fmt_float(details.end_stop_length),
                    fmt_float(details.webbing_count),
                    fmt_float(details.webbing_width),
                    fmt_float(details.webbing_thickness),
                    _format_vector(details.pull_slat_indices),
                    fmt_float(details.handle_width),
                    fmt_float(details.handle_height),
                    fmt_float(details.handle_projection),
                    _format_vector(details.webbing_color),
                    _format_vector(details.handle_color),
                )
            )
            + "]"
        )
        return (
            "["
            f"{scad_string(self.name)}, "
            f"{scad_string(self.assembly)}, "
            f"{_format_vector(self.track_color)}, "
            f"{_format_vector(self.slat_color)}, "
            f"{fmt_float(self.track_diameter)}, "
            f"{fmt_float(self.slat_pitch)}, "
            f"{fmt_float(self.slat_thickness)}, "
            f"{fmt_float(self.slat_depth)}, "
            f"{fmt_float(self.slat_track_offset)}, "
            f"{_format_points(self.left_points)}, "
            f"{_format_points(self.right_points)}, "
            f"{_format_bends(self.bends)}, "
            f"{_format_slats(self.slats)}, "
            f"{_format_slats(self.closed_slats)}, "
            f"{installed_record}"
            "]"
        )


TambourRef = str | TambourDoor


class TambourCollection(Mapping[str, TambourDoor]):
    def __init__(
        self,
        tambours: Mapping[str, TambourDoor] | Iterable[TambourDoor] | None = None,
    ):
        self._tambours: dict[str, TambourDoor] = {}
        if tambours is None:
            return
        if isinstance(tambours, Mapping):
            for name, tambour in tambours.items():
                if name != tambour.name:
                    raise ValueError(
                        f"Tambour key {name!r} does not match tambour name "
                        f"{tambour.name!r}"
                    )
                self._store(tambour)
            return
        for tambour in tambours:
            self._store(tambour)

    def add(
        self,
        name: str,
        *,
        left_points: Iterable[Coordinate],
        right_points: Iterable[Coordinate],
        assembly: str = "tambour",
        bends: Iterable[TambourBend] = (),
        track_diameter: float = 0.5,
        slat_pitch: float = 1.0,
        slat_thickness: float = 0.9,
        slat_depth: float = 0.75,
        slat_track_offset: float = 0.0,
        slat_envelope_depth: float | None = None,
        installed_details: TambourInstalledDetails | None = None,
        door_length: float = 14.0,
        track_color: TambourColor = DEFAULT_TRACK_COLOR,
        slat_color: TambourColor = DEFAULT_SLAT_COLOR,
    ) -> TambourDoor:
        return self._store(
            TambourDoor(
                name=name,
                left_points=tuple(left_points),
                right_points=tuple(right_points),
                assembly=assembly,
                bends=tuple(bends),
                track_diameter=track_diameter,
                slat_pitch=slat_pitch,
                slat_thickness=slat_thickness,
                slat_depth=slat_depth,
                slat_track_offset=slat_track_offset,
                slat_envelope_depth=slat_envelope_depth,
                installed_details=installed_details,
                door_length=door_length,
                track_color=track_color,
                slat_color=slat_color,
            )
        )

    @overload
    def get(self, name: str) -> TambourDoor | None: ...

    @overload
    def get(self, name: str, default: TambourDoor) -> TambourDoor: ...

    def get(
        self, name: str, default: TambourDoor | None = None
    ) -> TambourDoor | None:
        return self._tambours.get(name, default)

    def resolve(self, ref: TambourRef) -> TambourDoor:
        if isinstance(ref, TambourDoor):
            return ref
        try:
            return self._tambours[ref]
        except KeyError as exc:
            raise KeyError(f"Unknown tambour {ref!r}") from exc

    def as_dict(self) -> dict[str, TambourDoor]:
        return dict(self._tambours)

    def _store(self, tambour: TambourDoor) -> TambourDoor:
        if tambour.name in self._tambours:
            raise ValueError(f"Duplicate tambour name: {tambour.name}")
        self._tambours[tambour.name] = tambour
        return tambour

    def __getitem__(self, name: str) -> TambourDoor:
        return self._tambours[name]

    def __contains__(self, name: object) -> bool:
        return name in self._tambours

    def __iter__(self) -> Iterator[str]:
        return iter(self._tambours)

    def __len__(self) -> int:
        return len(self._tambours)
