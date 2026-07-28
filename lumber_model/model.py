from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import json
import math

from jinja2 import Environment, FileSystemLoader, select_autoescape

from lumber_model.build_steps import BuildStep
from lumber_model.cable import CableRun
from lumber_model.components import ComponentInstance
from lumber_model.conduit import ConduitRun
from lumber_model.constants import LumberType
from lumber_model.formatting import (
    fmt_float,
    inches_to_fraction_text,
    round_to_increment,
    sanitize_scad_identifier,
)
from lumber_model.geometry import Vector3
from lumber_model.footing import Footing
from lumber_model.fabrication import PurchasedItem, RoutedSeat
from lumber_model.ground import GroundPlane
from lumber_model.lumber import AngledLumber, LumberPiece
from lumber_model.siding import CompositeSiding
from lumber_model.tambour import TambourDoor


XYBounds = tuple[float, float, float, float]
XYOrigin = tuple[float, float]


def _include_xy_box(
    bounds: list[float],
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> None:
    bounds[0] = min(bounds[0], min_x)
    bounds[1] = max(bounds[1], max_x)
    bounds[2] = min(bounds[2], min_y)
    bounds[3] = max(bounds[3], max_y)


def _include_centerline_segments(
    bounds: list[float],
    points: tuple[Vector3, ...],
    diameter: float,
) -> None:
    radius = diameter / 2
    for start, end in zip(points, points[1:]):
        delta = tuple(end[index] - start[index] for index in range(3))
        length = math.sqrt(sum(value * value for value in delta))
        if length == 0:
            continue
        x_radius = radius * math.sqrt(max(0, 1 - (delta[0] / length) ** 2))
        y_radius = radius * math.sqrt(max(0, 1 - (delta[1] / length) ** 2))
        _include_xy_box(
            bounds,
            min(start[0], end[0]) - x_radius,
            max(start[0], end[0]) + x_radius,
            min(start[1], end[1]) - y_radius,
            max(start[1], end[1]) + y_radius,
        )


@dataclass(init=False)
class Model:
    pieces: list[LumberPiece]
    components: list[ComponentInstance]
    conduits: list[ConduitRun]
    cables: list[CableRun]
    grounds: list[GroundPlane]
    footings: list[Footing]
    tambours: list[TambourDoor]
    sidings: list[CompositeSiding]
    routed_seats: list[RoutedSeat]
    purchased_items: list[PurchasedItem]
    build_steps: tuple[BuildStep, ...]
    xygrid_origin: XYOrigin

    def __init__(
        self,
        pieces: Mapping[str, LumberPiece] | Iterable[LumberPiece],
        components: Mapping[str, ComponentInstance]
        | Iterable[ComponentInstance]
        | None = None,
        conduits: Mapping[str, ConduitRun] | Iterable[ConduitRun] | None = None,
        cables: Mapping[str, CableRun] | Iterable[CableRun] | None = None,
        grounds: Mapping[str, GroundPlane] | Iterable[GroundPlane] | None = None,
        footings: Mapping[str, Footing] | Iterable[Footing] | None = None,
        tambours: Mapping[str, TambourDoor] | Iterable[TambourDoor] | None = None,
        sidings: Mapping[str, CompositeSiding]
        | Iterable[CompositeSiding]
        | None = None,
        routed_seats: Iterable[RoutedSeat] | None = None,
        purchased_items: Iterable[PurchasedItem] | None = None,
        build_steps: Iterable[BuildStep] | None = None,
        xygrid_origin: XYOrigin = (0, 0),
    ):
        if isinstance(pieces, Mapping):
            self.pieces = list(pieces.values())
        else:
            self.pieces = list(pieces)

        if components is None:
            self.components = []
        elif isinstance(components, Mapping):
            self.components = list(components.values())
        else:
            self.components = list(components)

        if conduits is None:
            self.conduits = []
        elif isinstance(conduits, Mapping):
            self.conduits = list(conduits.values())
        else:
            self.conduits = list(conduits)

        if cables is None:
            self.cables = []
        elif isinstance(cables, Mapping):
            self.cables = list(cables.values())
        else:
            self.cables = list(cables)

        if grounds is None:
            self.grounds = []
        elif isinstance(grounds, Mapping):
            self.grounds = list(grounds.values())
        else:
            self.grounds = list(grounds)

        if footings is None:
            self.footings = []
        elif isinstance(footings, Mapping):
            self.footings = list(footings.values())
        else:
            self.footings = list(footings)

        if tambours is None:
            self.tambours = []
        elif isinstance(tambours, Mapping):
            self.tambours = list(tambours.values())
        else:
            self.tambours = list(tambours)

        if sidings is None:
            self.sidings = []
        elif isinstance(sidings, Mapping):
            self.sidings = list(sidings.values())
        else:
            self.sidings = list(sidings)

        self.routed_seats = list(routed_seats or ())
        self.purchased_items = list(purchased_items or ())

        self.build_steps = tuple(build_steps or ())
        self.xygrid_origin = xygrid_origin

    @classmethod
    def from_members(
        cls,
        members: Mapping[str, LumberPiece] | Iterable[LumberPiece],
    ) -> Model:
        return cls(members)

    def assemblies(self) -> list[str]:
        return sorted({piece.assembly for piece in self.pieces})

    def pieces_in(self, assembly: str) -> list[LumberPiece]:
        return [piece for piece in self.pieces if piece.assembly == assembly]

    def validate(self) -> None:
        names = [piece.name for piece in self.pieces]
        duplicates = sorted({name for name in names if names.count(name) > 1})

        if duplicates:
            raise ValueError(f"Duplicate lumber names: {duplicates}")

        assembly_vars = [sanitize_scad_identifier(a) for a in self.assemblies()]
        duplicate_vars = sorted(
            {name for name in assembly_vars if assembly_vars.count(name) > 1}
        )

        if duplicate_vars:
            raise ValueError(
                "Assembly names produce duplicate OpenSCAD identifiers after "
                f"sanitization: {duplicate_vars}"
            )

        member_by_name = {piece.name: piece for piece in self.pieces}

        component_names = [component.name for component in self.components]
        duplicate_components = sorted(
            {
                name
                for name in component_names
                if component_names.count(name) > 1
            }
        )

        if duplicate_components:
            raise ValueError(f"Duplicate component names: {duplicate_components}")

        component_assembly_vars = [
            "component_" + sanitize_scad_identifier(a)
            for a in self.component_assemblies()
        ]
        duplicate_component_vars = sorted(
            {
                name
                for name in component_assembly_vars
                if component_assembly_vars.count(name) > 1
            }
        )

        if duplicate_component_vars:
            raise ValueError(
                "Component assembly names produce duplicate OpenSCAD identifiers "
                f"after sanitization: {duplicate_component_vars}"
            )

        for component in self.components:
            try:
                member = member_by_name[component.member]
            except KeyError as exc:
                raise KeyError(
                    f"{component.name}: unknown lumber member "
                    f"{component.member!r}"
                ) from exc

            component.resolved(member)

        routed_seat_names = [seat.name for seat in self.routed_seats]
        if len(routed_seat_names) != len(set(routed_seat_names)):
            raise ValueError("Duplicate routed-seat names")
        for seat in self.routed_seats:
            if seat.member not in member_by_name:
                raise KeyError(f"{seat.name}: unknown lumber member {seat.member!r}")

        conduit_names = [conduit.name for conduit in self.conduits]
        duplicate_conduits = sorted(
            {
                name
                for name in conduit_names
                if conduit_names.count(name) > 1
            }
        )

        if duplicate_conduits:
            raise ValueError(f"Duplicate conduit names: {duplicate_conduits}")

        conduit_assembly_vars = [
            "conduit_" + sanitize_scad_identifier(a)
            for a in self.conduit_assemblies()
        ]
        duplicate_conduit_vars = sorted(
            {
                name
                for name in conduit_assembly_vars
                if conduit_assembly_vars.count(name) > 1
            }
        )

        if duplicate_conduit_vars:
            raise ValueError(
                "Conduit assembly names produce duplicate OpenSCAD identifiers "
                f"after sanitization: {duplicate_conduit_vars}"
            )

        component_by_name = {
            component.name: component for component in self.components
        }

        for conduit in self.conduits:
            conduit.resolved(component_by_name, member_by_name)

        cable_names = [cable.name for cable in self.cables]
        duplicate_cables = sorted(
            {name for name in cable_names if cable_names.count(name) > 1}
        )

        if duplicate_cables:
            raise ValueError(f"Duplicate cable names: {duplicate_cables}")

        cable_assembly_vars = [
            "cable_" + sanitize_scad_identifier(a) for a in self.cable_assemblies()
        ]
        duplicate_cable_vars = sorted(
            {
                name
                for name in cable_assembly_vars
                if cable_assembly_vars.count(name) > 1
            }
        )

        if duplicate_cable_vars:
            raise ValueError(
                "Cable assembly names produce duplicate OpenSCAD identifiers after "
                f"sanitization: {duplicate_cable_vars}"
            )

        for cable in self.cables:
            cable.resolved()

        ground_names = [ground.name for ground in self.grounds]
        duplicate_grounds = sorted(
            {name for name in ground_names if ground_names.count(name) > 1}
        )

        if duplicate_grounds:
            raise ValueError(f"Duplicate ground names: {duplicate_grounds}")

        for ground in self.grounds:
            ground.resolved(self)

        footing_names = [footing.name for footing in self.footings]
        duplicate_footings = sorted(
            {name for name in footing_names if footing_names.count(name) > 1}
        )

        if duplicate_footings:
            raise ValueError(f"Duplicate footing names: {duplicate_footings}")

        for footing in self.footings:
            footing.resolved(self)

        tambour_names = [tambour.name for tambour in self.tambours]
        duplicate_tambours = sorted(
            {name for name in tambour_names if tambour_names.count(name) > 1}
        )

        if duplicate_tambours:
            raise ValueError(f"Duplicate tambour names: {duplicate_tambours}")

        tambour_assembly_vars = [
            "tambour_" + sanitize_scad_identifier(a)
            for a in self.tambour_assemblies()
        ]
        duplicate_tambour_vars = sorted(
            {
                name
                for name in tambour_assembly_vars
                if tambour_assembly_vars.count(name) > 1
            }
        )

        if duplicate_tambour_vars:
            raise ValueError(
                "Tambour assembly names produce duplicate OpenSCAD identifiers "
                f"after sanitization: {duplicate_tambour_vars}"
            )

        for tambour in self.tambours:
            tambour.resolved(self)

        siding_names = [siding.name for siding in self.sidings]
        duplicate_sidings = sorted(
            {name for name in siding_names if siding_names.count(name) > 1}
        )

        if duplicate_sidings:
            raise ValueError(f"Duplicate siding names: {duplicate_sidings}")

        self._validate_build_steps()

    def renderable_object_names(self) -> list[str]:
        return (
            [piece.name for piece in self.pieces]
            + [component.name for component in self.components]
            + [conduit.name for conduit in self.conduits]
            + [cable.name for cable in self.cables]
            + [footing.name for footing in self.footings]
            + [tambour.name for tambour in self.tambours]
            + [part.name for siding in self.sidings for part in siding.parts]
        )

    def _validate_build_steps(self) -> None:
        if not self.build_steps:
            return

        numbers = [step.number for step in self.build_steps]
        expected_numbers = list(range(1, len(self.build_steps) + 1))
        if numbers != expected_numbers:
            raise ValueError(
                "Build step numbers must be sequential starting at 1: "
                f"{numbers}"
            )

        model_names = self.renderable_object_names()
        duplicate_model_names = sorted(
            {name for name in model_names if model_names.count(name) > 1}
        )
        if duplicate_model_names:
            raise ValueError(
                "Build-step object names must be unique across model categories: "
                f"{duplicate_model_names}"
            )

        assigned_names = [
            name for step in self.build_steps for name in step.object_names
        ]
        duplicate_assignments = sorted(
            {name for name in assigned_names if assigned_names.count(name) > 1}
        )
        if duplicate_assignments:
            raise ValueError(
                "Model objects are assigned to multiple build steps: "
                f"{duplicate_assignments}"
            )

        missing = sorted(set(model_names) - set(assigned_names))
        unknown = sorted(set(assigned_names) - set(model_names))
        if missing or unknown:
            details = []
            if missing:
                details.append(f"missing model objects: {missing}")
            if unknown:
                details.append(f"unknown model objects: {unknown}")
            raise ValueError("Invalid build-step mapping; " + "; ".join(details))

    def bom_rows(self) -> list[dict[str, Any]]:
        self.validate()
        rows = [
            {
                "category": "lumber",
                **piece.bom_row(),
                "qty": 1,
                "total_linear_ft": "",
                "stock_length_ft": "",
                "stock_board_qty": "",
            }
            for piece in self.pieces
        ]
        for siding in self.sidings:
            rows.extend(siding.bom_rows())
        rows.extend(item.bom_row() for item in self.purchased_items)
        return rows

    def fabrication_rows(self) -> list[dict[str, Any]]:
        self.validate()
        return [seat.fabrication_row() for seat in self.routed_seats]

    def write_fabrication_csv(self, path: str | Path) -> None:
        self._write_csv(path, self.fabrication_rows())

    def write_fabrication_json(self, path: str | Path) -> None:
        self._write_json(path, self.fabrication_rows())

    def cut_list_rows(
        self,
        rounding_increment: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Group identical cuts by assembly, type, and length.

        rounding_increment:
          - None keeps exact modeled length.
          - 1/16 can be passed as 0.0625.
          - 1/8 can be passed as 0.125.
        """
        self.validate()

        grouped: dict[
            tuple[str, str, float, object, object],
            list[LumberPiece],
        ] = defaultdict(list)

        for piece in self.pieces:
            length = piece.length

            if rounding_increment is not None:
                length = round_to_increment(length, rounding_increment)

            key = (
                piece.assembly,
                piece.type,
                round(length, 4),
                round(piece.cut_angle_deg, 2)
                if isinstance(piece, AngledLumber)
                else "",
                round(piece.cut_angle_deg, 2)
                if isinstance(piece, AngledLumber)
                else "",
            )

            grouped[key].append(piece)

        rows: list[dict[str, Any]] = []

        for (
            assembly,
            lumber_type,
            length,
            start_cut_angle,
            end_cut_angle,
        ), pieces in sorted(grouped.items()):
            rows.append(
                {
                    "assembly": assembly,
                    "type": lumber_type,
                    "length_in": length,
                    "length_display": inches_to_fraction_text(length),
                    "start_cut_angle_deg": start_cut_angle,
                    "end_cut_angle_deg": end_cut_angle,
                    "qty": len(pieces),
                    "members": ", ".join(piece.name for piece in pieces),
                }
            )

        return rows

    def shopping_list_rows(
        self,
        stock_lengths: dict[LumberType, list[float]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Basic shopping-list estimate.

        Conservative strategy:
          - Each member is assigned to the shortest listed stock length
            that can contain it.
          - This does not optimize multiple cuts per board.
        """
        self.validate()

        if stock_lengths is None:
            stock_lengths = {
                "1x4": [72, 96, 120, 144, 168, 192],
                "2x4": [96, 120, 144, 168, 192],
                "4x4": [96, 120, 144, 168, 192],
            }

        counts: dict[tuple[str, float], int] = defaultdict(int)

        for piece in self.pieces:
            options = sorted(stock_lengths[piece.type])
            selected = None

            for stock_length in options:
                if piece.length <= stock_length:
                    selected = stock_length
                    break

            if selected is None:
                raise ValueError(
                    f"{piece.name}: length {piece.length} exceeds available "
                    f"stock lengths for {piece.type}: {options}"
                )

            counts[(piece.type, selected)] += 1

        rows: list[dict[str, Any]] = []

        for (lumber_type, stock_length), qty in sorted(counts.items()):
            rows.append(
                {
                    "type": lumber_type,
                    "stock_length_in": stock_length,
                    "stock_length_display": inches_to_fraction_text(stock_length),
                    "qty": qty,
                }
            )

        return rows

    def write_bom_csv(self, path: str | Path) -> None:
        self._write_csv(path, self.bom_rows())

    def write_bom_json(self, path: str | Path) -> None:
        self._write_json(path, self.bom_rows())

    def write_cut_list_csv(
        self,
        path: str | Path,
        rounding_increment: float | None = 1 / 16,
    ) -> None:
        self._write_csv(path, self.cut_list_rows(rounding_increment=rounding_increment))

    def write_cut_list_json(
        self,
        path: str | Path,
        rounding_increment: float | None = 1 / 16,
    ) -> None:
        self._write_json(path, self.cut_list_rows(rounding_increment=rounding_increment))

    def write_shopping_list_csv(
        self,
        path: str | Path,
        stock_lengths: dict[LumberType, list[float]] | None = None,
    ) -> None:
        self._write_csv(path, self.shopping_list_rows(stock_lengths=stock_lengths))

    def write_shopping_list_json(
        self,
        path: str | Path,
        stock_lengths: dict[LumberType, list[float]] | None = None,
    ) -> None:
        self._write_json(path, self.shopping_list_rows(stock_lengths=stock_lengths))

    @staticmethod
    def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not rows:
            path.write_text("")
            return

        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_json(path: str | Path, rows: list[dict[str, Any]]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows, indent=2))

    def scad_piece_records(self) -> list[str]:
        return [piece.scad_record() for piece in self.pieces]

    def scad_routed_seat_records(self) -> list[str]:
        return [seat.scad_record() for seat in self.routed_seats]

    def scad_assemblies(self) -> list[dict[str, str]]:
        return [
            {
                "name": assembly,
                "toggle": sanitize_scad_identifier(assembly),
            }
            for assembly in self.assemblies()
        ]

    def component_assemblies(self) -> list[str]:
        return sorted({component.assembly for component in self.components})

    def scad_component_assemblies(self) -> list[dict[str, str]]:
        return [
            {
                "name": assembly,
                "toggle": "component_" + sanitize_scad_identifier(assembly),
            }
            for assembly in self.component_assemblies()
        ]

    def scad_component_records(self, scad_dir: str | Path | None = None) -> list[str]:
        member_by_name = {piece.name: piece for piece in self.pieces}
        return [
            component.resolved(member_by_name[component.member]).scad_record(scad_dir)
            for component in self.components
        ]

    def conduit_assemblies(self) -> list[str]:
        return sorted({conduit.assembly for conduit in self.conduits})

    def scad_conduit_assemblies(self) -> list[dict[str, str]]:
        return [
            {
                "name": assembly,
                "toggle": "conduit_" + sanitize_scad_identifier(assembly),
            }
            for assembly in self.conduit_assemblies()
        ]

    def scad_conduit_records(self) -> list[str]:
        member_by_name = {piece.name: piece for piece in self.pieces}
        component_by_name = {component.name: component for component in self.components}
        return [
            conduit.resolved(component_by_name, member_by_name).scad_record()
            for conduit in self.conduits
        ]

    def cable_assemblies(self) -> list[str]:
        return sorted({cable.assembly for cable in self.cables})

    def scad_cable_assemblies(self) -> list[dict[str, str]]:
        return [
            {
                "name": assembly,
                "toggle": "cable_" + sanitize_scad_identifier(assembly),
            }
            for assembly in self.cable_assemblies()
        ]

    def scad_cable_records(self) -> list[str]:
        return [cable.resolved().scad_record() for cable in self.cables]

    def resolve_coordinate_reference(self, name: str) -> Vector3:
        member_by_name = {piece.name: piece for piece in self.pieces}

        try:
            return member_by_name[name].start
        except KeyError as exc:
            raise KeyError(f"Unknown coordinate reference {name!r}") from exc

    def scad_ground_records(self) -> list[str]:
        return [ground.resolved(self).scad_record() for ground in self.grounds]

    def scad_footing_records(self) -> list[str]:
        return [footing.resolved(self).scad_record() for footing in self.footings]

    def tambour_assemblies(self) -> list[str]:
        return sorted({tambour.assembly for tambour in self.tambours})

    def scad_tambour_assemblies(self) -> list[dict[str, str]]:
        return [
            {
                "name": assembly,
                "toggle": "tambour_" + sanitize_scad_identifier(assembly),
            }
            for assembly in self.tambour_assemblies()
        ]

    def scad_tambour_records(self) -> list[str]:
        return [tambour.resolved(self).scad_record() for tambour in self.tambours]

    def scad_siding_records(self) -> list[str]:
        return [part.scad_record() for siding in self.sidings for part in siding.parts]

    def scad_build_step_records(self) -> list[str]:
        return [
            f'[{json.dumps(name)}, {step.number}]'
            for step in self.build_steps
            for name in step.object_names
        ]

    def _xygrid_bounds(self) -> XYBounds | None:
        """Return non-ground XY geometry bounds with a one-inch margin."""
        bounds = [math.inf, -math.inf, math.inf, -math.inf]
        member_by_name = {piece.name: piece for piece in self.pieces}
        component_by_name = {
            component.name: component for component in self.components
        }

        for piece in self.pieces:
            if isinstance(piece, AngledLumber):
                dx = piece.end[0] - piece.start[0]
                dy = piece.end[1] - piece.start[1]
                perpendicular_x = -dy / piece.length
                perpendicular_y = dx / piece.length
                x_radius = abs(perpendicular_x) * piece.width / 2
                y_radius = abs(perpendicular_y) * piece.width / 2
                _include_xy_box(
                    bounds,
                    min(piece.start[0], piece.end[0]) - x_radius,
                    max(piece.start[0], piece.end[0]) + x_radius,
                    min(piece.start[1], piece.end[1]) - y_radius,
                    max(piece.start[1], piece.end[1]) + y_radius,
                )
            else:
                _include_xy_box(
                    bounds,
                    piece.min[0],
                    piece.max[0],
                    piece.min[1],
                    piece.max[1],
                )

        for component in self.components:
            resolved = component.resolved(member_by_name[component.member])
            _include_xy_box(
                bounds,
                resolved.box_min[0],
                resolved.box_min[0] + resolved.box_size[0],
                resolved.box_min[1],
                resolved.box_min[1] + resolved.box_size[1],
            )

        for conduit in self.conduits:
            resolved = conduit.resolved(component_by_name, member_by_name)
            _include_centerline_segments(bounds, resolved.points, resolved.od)

        for cable in self.cables:
            radius = cable.diameter / 2
            for point in cable.points:
                _include_xy_box(
                    bounds,
                    point[0] - radius,
                    point[0] + radius,
                    point[1] - radius,
                    point[1] + radius,
                )

        for tambour in self.tambours:
            resolved = tambour.resolved(self)
            _include_centerline_segments(
                bounds,
                resolved.left_points,
                resolved.track_diameter,
            )
            _include_centerline_segments(
                bounds,
                resolved.right_points,
                resolved.track_diameter,
            )

            for slats in (resolved.slats, resolved.closed_slats):
                for left, right, tangent in slats:
                    span = tuple(right[index] - left[index] for index in range(3))
                    span_length = math.sqrt(sum(value * value for value in span))
                    span_dir = tuple(value / span_length for value in span)
                    tangent_length = math.sqrt(sum(value * value for value in tangent))
                    travel_dir = tuple(value / tangent_length for value in tangent)
                    depth_dir = (
                        span_dir[1] * travel_dir[2]
                        - span_dir[2] * travel_dir[1],
                        span_dir[2] * travel_dir[0]
                        - span_dir[0] * travel_dir[2],
                        span_dir[0] * travel_dir[1]
                        - span_dir[1] * travel_dir[0],
                    )
                    depth_length = math.sqrt(
                        sum(value * value for value in depth_dir)
                    )
                    depth_dir = tuple(value / depth_length for value in depth_dir)
                    center = tuple(
                        (left[index] + right[index]) / 2 for index in range(3)
                    )
                    half_extent = tuple(
                        (
                            abs(span_dir[index]) * span_length
                            + abs(travel_dir[index]) * resolved.slat_thickness
                            + abs(depth_dir[index]) * resolved.slat_depth
                        )
                        / 2
                        for index in range(3)
                    )
                    _include_xy_box(
                        bounds,
                        center[0] - half_extent[0],
                        center[0] + half_extent[0],
                        center[1] - half_extent[1],
                        center[1] + half_extent[1],
                    )

        for siding in self.sidings:
            for part in siding.parts:
                _include_xy_box(
                    bounds,
                    part.start[0],
                    part.start[0] + part.size[0],
                    part.start[1],
                    part.start[1] + part.size[1],
                )

        if math.isinf(bounds[0]):
            return None
        return (bounds[0] - 1, bounds[1] + 1, bounds[2] - 1, bounds[3] + 1)

    def _scad_xygrid_bounds(self) -> str:
        bounds = self._xygrid_bounds()
        if bounds is None:
            return "[]"
        return "[" + ", ".join(fmt_float(value) for value in bounds) + "]"

    def _scad_xygrid_origin(self) -> str:
        values = ", ".join(fmt_float(value) for value in self.xygrid_origin)
        return f"[{values}]"

    def to_scad(
        self,
        template_dir: str | Path = "templates",
        template_name: str = "model.scad.j2",
        scad_path: str | Path | None = None,
    ) -> str:
        self.validate()

        template_dir = Path(template_dir)
        scad_dir = Path(scad_path).parent if scad_path is not None else None

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(enabled_extensions=()),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        template = env.get_template(template_name)

        return template.render(
            assemblies=self.scad_assemblies(),
            piece_records=self.scad_piece_records(),
            routed_seat_records=self.scad_routed_seat_records(),
            component_assemblies=self.scad_component_assemblies(),
            component_records=self.scad_component_records(scad_dir),
            conduit_assemblies=self.scad_conduit_assemblies(),
            conduit_records=self.scad_conduit_records(),
            cable_assemblies=self.scad_cable_assemblies(),
            cable_records=self.scad_cable_records(),
            ground_records=self.scad_ground_records(),
            footing_records=self.scad_footing_records(),
            tambour_assemblies=self.scad_tambour_assemblies(),
            tambour_records=self.scad_tambour_records(),
            siding_records=self.scad_siding_records(),
            xygrid_bounds=self._scad_xygrid_bounds(),
            xygrid_origin=self._scad_xygrid_origin(),
            build_step_records=self.scad_build_step_records(),
            build_step_count=len(self.build_steps),
        )

    def write_scad(
        self,
        path: str | Path,
        template_dir: str | Path = "templates",
        template_name: str = "model.scad.j2",
    ) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.to_scad(
                template_dir=template_dir,
                template_name=template_name,
                scad_path=path,
            )
        )
