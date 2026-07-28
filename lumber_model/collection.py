from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
import math
from typing import overload

from lumber_model.constants import ACTUAL_DIMS, Axis, LumberType
from lumber_model.coordinates import Coordinate, resolve_coordinate
from lumber_model.fabrication import clip_polygon_to_box
from lumber_model.geometry import Vector3
from lumber_model.lumber import AngledLumber, Lumber, LumberPiece


LumberRef = str | LumberPiece


class LumberCollection(Mapping[str, LumberPiece]):
    """
    Dict-backed builder for lumber members keyed by member name.

    The add methods return the created Lumber when a caller wants to keep a local
    reference, but normal model construction can consume the collection directly.
    """

    def __init__(
        self,
        members: Mapping[str, LumberPiece] | Iterable[LumberPiece] | None = None,
    ):
        self._members: dict[str, LumberPiece] = {}

        if members is None:
            return

        if isinstance(members, Mapping):
            for name, member in members.items():
                if name != member.name:
                    raise ValueError(
                        f"Member key {name!r} does not match lumber name "
                        f"{member.name!r}"
                    )
                self._store(member)
            return

        for member in members:
            self._store(member)

    def add(
        self,
        name: str,
        *,
        assembly: str,
        type: LumberType,
        axis: Axis,
        start: Coordinate,
        length: float,
        rotated: bool = True,
    ) -> Lumber:
        return self._store(
            Lumber(
                name=name,
                assembly=assembly,
                type=type,
                axis=axis,
                start=resolve_coordinate(f"{name}: start", start, self),
                length=length,
                rotated=rotated,
            )
        )

    def between(
        self,
        name: str,
        *,
        assembly: str,
        type: LumberType,
        support_a: LumberRef,
        support_b: LumberRef,
        position: float,
        cross_offset: float = 0,
        inset: float = 0,
        rotated: bool = True,
        span_axis: Axis | None = None,
        position_axis: Axis | None = None,
    ) -> Lumber:
        return self._store(
            Lumber.between(
                name=name,
                assembly=assembly,
                type=type,
                support_a=self.resolve(support_a),
                support_b=self.resolve(support_b),
                position=position,
                cross_offset=cross_offset,
                inset=inset,
                rotated=rotated,
                span_axis=span_axis,
                position_axis=position_axis,
            )
        )

    def diagonal_between(
        self,
        name: str,
        *,
        assembly: str,
        type: LumberType,
        support_a: LumberRef,
        support_b: LumberRef,
        position: float,
        rotated: bool = True,
        extend_within_support_xy: bool = False,
        cover_supports_xy: bool = False,
    ) -> AngledLumber:
        """
        Create a horizontal diagonal member between the inside corners of posts.

        The endpoint on each support is chosen from the support corner facing
        the opposite support, so the member butts into the clear top-frame
        opening rather than running post-center to post-center. With
        cover_supports_xy, the member instead follows the support-center line,
        is ripped to their maximum projected width, extends across both support
        profiles, and is clipped to their combined exterior XY bounds.
        """
        a = self.resolve(support_a)
        b = self.resolve(support_b)

        if isinstance(a, AngledLumber) or isinstance(b, AngledLumber):
            raise ValueError(f"{name}: diagonal supports must be axis-aligned lumber")

        if extend_within_support_xy and cover_supports_xy:
            raise ValueError(
                f"{name}: extension modes extend_within_support_xy and "
                "cover_supports_xy are mutually exclusive"
            )

        a_center = a.center
        b_center = b.center

        a_x = a.max_on("x") if b_center[0] >= a_center[0] else a.min_on("x")
        a_y = a.max_on("y") if b_center[1] >= a_center[1] else a.min_on("y")
        b_x = b.max_on("x") if a_center[0] >= b_center[0] else b.min_on("x")
        b_y = b.max_on("y") if a_center[1] >= b_center[1] else b.min_on("y")

        finished_width: float | None = None
        footprint: tuple[tuple[float, float], ...] | None = None

        if cover_supports_xy:
            dx = b_center[0] - a_center[0]
            dy = b_center[1] - a_center[1]
            center_length = math.hypot(dx, dy)
            if math.isclose(center_length, 0):
                raise ValueError(f"{name}: cannot cover coincident supports")

            along = (dx / center_length, dy / center_length)
            normal = (-along[1], along[0])

            def projected_extent(support: Lumber, direction: tuple[float, float]) -> float:
                return (
                    abs(direction[0]) * (support.max_on("x") - support.min_on("x"))
                    + abs(direction[1]) * (support.max_on("y") - support.min_on("y"))
                )

            finished_width = max(
                projected_extent(a, normal),
                projected_extent(b, normal),
            )
            stock_width = ACTUAL_DIMS[type][1 if rotated else 0]
            if finished_width > stock_width:
                raise ValueError(
                    f"{name}: required finished width {finished_width} exceeds "
                    f"{type} stock width {stock_width}"
                )

            a_extension = projected_extent(a, along) / 2
            b_extension = projected_extent(b, along) / 2
            a_x = a_center[0] - along[0] * a_extension
            a_y = a_center[1] - along[1] * a_extension
            b_x = b_center[0] + along[0] * b_extension
            b_y = b_center[1] + along[1] * b_extension

            half_width = finished_width / 2
            raw_footprint = (
                (a_x - normal[0] * half_width, a_y - normal[1] * half_width),
                (b_x - normal[0] * half_width, b_y - normal[1] * half_width),
                (b_x + normal[0] * half_width, b_y + normal[1] * half_width),
                (a_x + normal[0] * half_width, a_y + normal[1] * half_width),
            )
            footprint = clip_polygon_to_box(
                raw_footprint,
                min_x=min(a.min_on("x"), b.min_on("x")),
                max_x=max(a.max_on("x"), b.max_on("x")),
                min_y=min(a.min_on("y"), b.min_on("y")),
                max_y=max(a.max_on("y"), b.max_on("y")),
            )
        elif extend_within_support_xy:
            dx = b_x - a_x
            dy = b_y - a_y
            clear_length = math.hypot(dx, dy)
            if math.isclose(clear_length, 0):
                raise ValueError(f"{name}: cannot extend a zero-length diagonal")

            along = (dx / clear_length, dy / clear_length)
            normal = (-along[1], along[0])
            half_width = ACTUAL_DIMS[type][1] / 2

            def extended_endpoint(
                point: tuple[float, float],
                support: Lumber,
                direction: tuple[float, float],
            ) -> tuple[float, float]:
                """Extend a square-cut end without crossing outward support faces."""

                limits: list[float] = []
                for axis, axis_name in enumerate(("x", "y")):
                    padding = abs(normal[axis]) * half_width
                    rate = direction[axis]
                    if math.isclose(rate, 0):
                        continue
                    if rate < 0:
                        limit = (
                            point[axis] - support.min_on(axis_name) - padding
                        ) / -rate
                    else:
                        limit = (
                            support.max_on(axis_name) - padding - point[axis]
                        ) / rate
                    limits.append(limit)

                distance = min(limits)
                if distance < 0:
                    raise ValueError(
                        f"{name}: diagonal width does not fit on {support.name}"
                    )
                return (
                    point[0] + direction[0] * distance,
                    point[1] + direction[1] * distance,
                )

            a_x, a_y = extended_endpoint((a_x, a_y), a, (-along[0], -along[1]))
            b_x, b_y = extended_endpoint((b_x, b_y), b, along)

        return self._store(
            AngledLumber(
                name=name,
                assembly=assembly,
                type=type,
                start=(a_x, a_y, position),
                end=(b_x, b_y, position),
                rotated=rotated,
                finished_width=finished_width,
                footprint=footprint,
            )
        )

    @overload
    def get(self, name: str) -> LumberPiece | None: ...

    @overload
    def get(self, name: str, default: LumberPiece) -> LumberPiece: ...

    def get(
        self,
        name: str,
        default: LumberPiece | None = None,
    ) -> LumberPiece | None:
        return self._members.get(name, default)

    def resolve(self, ref: LumberRef) -> LumberPiece:
        if isinstance(ref, (Lumber, AngledLumber)):
            return ref

        try:
            return self._members[ref]
        except KeyError as exc:
            raise KeyError(f"Unknown lumber member {ref!r}") from exc

    def resolve_coordinate_reference(self, name: str) -> Vector3:
        return self.resolve(name).start

    def as_dict(self) -> dict[str, LumberPiece]:
        return dict(self._members)

    def _store(self, member: LumberPiece) -> LumberPiece:
        if member.name in self._members:
            raise ValueError(f"Duplicate lumber name: {member.name}")

        self._members[member.name] = member
        return member

    def __getitem__(self, name: str) -> LumberPiece:
        return self._members[name]

    def __contains__(self, name: object) -> bool:
        return name in self._members

    def __iter__(self) -> Iterator[str]:
        return iter(self._members)

    def __len__(self) -> int:
        return len(self._members)
