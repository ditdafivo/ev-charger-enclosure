from __future__ import annotations


GUSSET_SIZE_IN = 6.0
GUSSET_THICKNESS_IN = 0.074
GUSSET_MATERIAL = "G90 galvanized steel"
GUSSET_HOLE_DIAMETER_IN = 13 / 64
GUSSET_HOLE_GRID_IN = (0.75, 2.25, 3.75, 5.25)
GUSSET_HOLE_CENTERS_IN = tuple(
    (x, y) for x in GUSSET_HOLE_GRID_IN for y in GUSSET_HOLE_GRID_IN
)
GUSSET_FASTENER_SIZE = "#9"
GUSSET_FASTENER_HEAD = "pan head"
GUSSET_FASTENER_COUNT = len(GUSSET_HOLE_CENTERS_IN)

# Only the head is modeled: fastener length is intentionally unspecified.
GUSSET_SCREW_HEAD_DIAMETER_IN = 0.35
GUSSET_SCREW_HEAD_HEIGHT_IN = 0.11


def pan_head_cylinder_primitives() -> tuple[
    tuple[tuple[float, float, float], str, float, float], ...
]:
    """Return stepped cylinders that approximate each domed pan-head profile."""

    layers = (
        (0.0, 0.045, 1.0),
        (0.045, 0.035, 0.90),
        (0.080, 0.025, 0.72),
        (0.105, 0.005, 0.42),
    )
    return tuple(
        (
            (x, y, GUSSET_THICKNESS_IN + z),
            "out",
            height,
            GUSSET_SCREW_HEAD_DIAMETER_IN * diameter_scale,
        )
        for x, y in GUSSET_HOLE_CENTERS_IN
        for z, height, diameter_scale in layers
    )
