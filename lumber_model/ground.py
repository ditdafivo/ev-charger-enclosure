from __future__ import annotations

from dataclasses import dataclass
import math

from lumber_model.coordinates import Coordinate, CoordinateResolver, resolve_coordinate
from lumber_model.formatting import fmt_float, scad_string
from lumber_model.geometry import Vector3


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )


def _length(v: Vector3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _unit(v: Vector3) -> Vector3:
    length = _length(v)

    if length == 0:
        raise ValueError("Cannot normalize zero-length vector")

    return (v[0] / length, v[1] / length, v[2] / length)


@dataclass(frozen=True)
class ResolvedGroundPlane:
    name: str
    origin: Vector3
    point_a: Vector3
    point_b: Vector3
    center: Vector3
    radius: float
    color: tuple[float, float, float, float]
    thickness: float

    @property
    def normal(self) -> Vector3:
        normal = _unit(
            _cross(
                _sub(self.point_a, self.origin),
                _sub(self.point_b, self.origin),
            )
        )

        if normal[2] < 0:
            return (-normal[0], -normal[1], -normal[2])

        return normal

    def z_at(self, x: float, y: float) -> float:
        normal = self.normal
        if abs(normal[2]) < 1e-9:
            raise ValueError("Cannot calculate elevation on a vertical ground plane")
        return self.origin[2] - (
            normal[0] * (x - self.origin[0])
            + normal[1] * (y - self.origin[1])
        ) / normal[2]

    def scad_record(self) -> str:
        def vector(values: tuple[float, ...]) -> str:
            return "[" + ", ".join(fmt_float(value) for value in values) + "]"

        return (
            "["
            f"{scad_string(self.name)}, "
            f"{vector(self.center)}, "
            f"{vector(self.normal)}, "
            f"{fmt_float(self.radius)}, "
            f"{vector(self.color)}, "
            f"{fmt_float(self.thickness)}"
            "]"
        )


@dataclass(frozen=True)
class GroundPlane:
    """
    A circular visual representation of the ground plane.

    The plane is fixed to z=0 at the named origin reference's x/y position,
    normally ``post_fl``. Two additional model coordinates define the
    tilt. The rendered circle is centered at ``center``.
    """

    name: str
    point_a: Coordinate
    point_b: Coordinate
    center: Coordinate
    radius: float
    origin_reference: str = "post_fl"
    color: tuple[float, float, float, float] = (0.24, 0.42, 0.24, 0.35)
    thickness: float = 0.05

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"{self.name}: radius must be positive")

        if self.thickness <= 0:
            raise ValueError(f"{self.name}: thickness must be positive")

        if len(self.color) != 4:
            raise ValueError(f"{self.name}: color must be an RGBA tuple")

    def resolved(self, resolver: CoordinateResolver) -> ResolvedGroundPlane:
        reference = resolver.resolve_coordinate_reference(self.origin_reference)
        origin = (reference[0], reference[1], 0.0)
        point_a = resolve_coordinate(f"{self.name}: point_a", self.point_a, resolver)
        point_b = resolve_coordinate(f"{self.name}: point_b", self.point_b, resolver)
        center = resolve_coordinate(f"{self.name}: center", self.center, resolver)

        try:
            resolved = ResolvedGroundPlane(
                name=self.name,
                origin=origin,
                point_a=point_a,
                point_b=point_b,
                center=center,
                radius=self.radius,
                color=self.color,
                thickness=self.thickness,
            )
            resolved.normal
        except ValueError as exc:
            raise ValueError(
                f"{self.name}: ground plane points must not be coincident or collinear"
            ) from exc

        return resolved


@dataclass(frozen=True)
class ResolvedGroundSurface:
    """Bilinear surveyed grade, held at the nearest edge outside the survey."""

    name: str
    corners: tuple[Vector3, Vector3, Vector3, Vector3]  # FL, FR, BR, BL
    center: Vector3
    radius: float
    color: tuple[float, float, float, float]
    thickness: float

    @property
    def normal(self) -> Vector3:
        # The mesh uses world XY coordinates rather than a rotated disk.
        return (0.0, 0.0, 1.0)

    def z_at(self, x: float, y: float) -> float:
        fl, fr, br, bl = self.corners
        u = min(1.0, max(0.0, (x - fl[0]) / (fr[0] - fl[0])))
        v = min(1.0, max(0.0, (y - fl[1]) / (bl[1] - fl[1])))
        return (
            (1-u)*(1-v)*fl[2] + u*(1-v)*fr[2]
            + u*v*br[2] + (1-u)*v*bl[2]
        )

    @property
    def z_bounds(self) -> tuple[float, float]:
        return (
            min(p[2] for p in self.corners) - self.thickness,
            max(p[2] for p in self.corners),
        )

    def mesh(self) -> tuple[list[Vector3], list[tuple[int, ...]]]:
        fl, fr, _, bl = self.corners
        # Include the surveyed edges exactly and subdivide the gently curved
        # interior. The same z_at function drives equipment ground references.
        xs = sorted({self.center[0]-self.radius, self.center[0]+self.radius,
                     *(fl[0] + (fr[0]-fl[0])*i/16 for i in range(17))})
        ys = sorted({self.center[1]-self.radius, self.center[1]+self.radius,
                     *(fl[1] + (bl[1]-fl[1])*i/16 for i in range(17))})
        nx, ny = len(xs), len(ys)
        top = [(x, y, self.z_at(x, y)) for y in ys for x in xs]
        count = len(top)
        vertices = top + [(x, y, z-self.thickness) for x, y, z in top]
        faces: list[tuple[int, ...]] = []
        for j in range(ny-1):
            for i in range(nx-1):
                a = j*nx+i
                b, c, d = a+1, a+nx+1, a+nx
                faces.extend(((a, b, c), (a, c, d),
                              (a+count, c+count, b+count),
                              (a+count, d+count, c+count)))
        boundary = (
            list(range(nx))
            + [j*nx+nx-1 for j in range(1, ny)]
            + list(range(count-2, count-nx-1, -1))
            + [j*nx for j in range(ny-2, 0, -1)]
        )
        for a, b in zip(boundary, boundary[1:]+boundary[:1]):
            faces.append((a, a+count, b+count, b))
        return vertices, faces

    def scad_record(self) -> str:
        vertices, faces = self.mesh()

        def vector(values: tuple[float, ...]) -> str:
            return "[" + ", ".join(fmt_float(v) for v in values) + "]"

        return (
            f"[{scad_string(self.name)}, {vector(self.center)}, [0, 0, 1], "
            f"{fmt_float(self.radius)}, {vector(self.color)}, "
            f"{fmt_float(self.thickness)}, "
            "[" + ", ".join(vector(v) for v in vertices) + "], "
            "[" + ", ".join(vector(f) for f in faces) + "]]"
        )


@dataclass(frozen=True)
class GroundSurface:
    """Circular grade visualization through four rectangular survey corners."""

    name: str
    corners: tuple[Coordinate, Coordinate, Coordinate, Coordinate]
    center: Coordinate
    radius: float
    color: tuple[float, float, float, float] = (0.24, 0.42, 0.24, 0.35)
    thickness: float = 0.05

    def __post_init__(self) -> None:
        if not math.isfinite(self.radius) or self.radius <= 0:
            raise ValueError(f"{self.name}: radius must be finite and positive")
        if not math.isfinite(self.thickness) or self.thickness <= 0:
            raise ValueError(f"{self.name}: thickness must be finite and positive")
        if len(self.color) != 4 or len(self.corners) != 4:
            raise ValueError(f"{self.name}: expected RGBA color and four corners")

    def resolved(self, resolver: CoordinateResolver) -> ResolvedGroundSurface:
        corners = tuple(resolve_coordinate(self.name, p, resolver) for p in self.corners)
        fl, fr, br, bl = corners
        if not (
            fl[0] == bl[0] < fr[0] == br[0]
            and fl[1] == fr[1] < bl[1] == br[1]
        ):
            raise ValueError(f"{self.name}: corners must form an XY rectangle in FL, FR, BR, BL order")
        center = resolve_coordinate(self.name, self.center, resolver)
        return ResolvedGroundSurface(
            self.name, corners, center, self.radius, self.color, self.thickness,
        )
