"""Reference CAD model from ipex_077454.pdf; all design dimensions below are inches.

Run: .venv/bin/python tools/generate_ipex_stb40s.py
The exported STEP uses millimeters and contains separate body, cover and screws.
Undimensioned details are estimates; see assets/components/ipex_stb40s/README.md.
"""
from pathlib import Path
import argparse

from build123d import (
    Align, Axis, Box, Color, Compound, Cylinder, SlotOverall,
    export_step, extrude,
)

INCH = 25.4
DEFAULT_OUTPUT = Path("output/ipex_stb40s/ipex_stb40s_077454.step")


def capsule(width, length, front, back):
    """Capsule in XZ, extruded from back toward front along -Y."""
    face = SlotOverall(length * INCH, width * INCH, rotation=90)
    return extrude(face, amount=(back - front) * INCH).rotate(
        axis=Axis.X, angle=90
    ).translate((0, back * INCH, 0))


def cylinder_z(radius, bottom, top, x=0, y=0):
    return Cylinder(radius * INCH, (top - bottom) * INCH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(
                        (x * INCH, y * INCH, bottom * INCH))


def cylinder_y(radius, front, back, z=0):
    return Cylinder(radius * INCH, (back - front) * INCH,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(
                        Axis.X, 90).translate((0, back * INCH, z * INCH))


def make_model():
    # Dimensions explicitly called out: 7.91, 2.30, 3.92, 1.00, 1.11,
    # 2.85 and socket ID 1.68. Chained vertical dimensions total 7.92;
    # overall 7.91 takes precedence, hence stop positions +/-2.845.
    half_length = 7.91 / 2
    stop_z = half_length - 1.11
    body = capsule(2.30, 7.41, -1.66, 1.00)
    body += cylinder_z(1.01, 2.55, half_length)
    body += cylinder_z(1.01, -half_length, -2.55)
    body += cylinder_y(1.01, 0.75, 2.00)

    # Main chamber plus the taller, shallower front access recess.
    body -= capsule(1.94, 5.55, -1.68, 0.82)
    body -= capsule(1.98, 7.05, -1.68, -1.02)

    # Solvent sockets with shoulders and smaller passages to the chamber.
    body -= cylinder_z(0.84, stop_z, half_length + .01)
    body -= cylinder_z(0.77, 2.40, stop_z + .01)
    body -= cylinder_z(0.84, -half_length - .01, -stop_z)
    body -= cylinder_z(0.77, -stop_z - .01, -2.40)
    body -= cylinder_y(0.84, 1.00, 2.01)
    body -= cylinder_y(0.77, 0.70, 1.01)

    # Cover screw bosses, located from the section view proportions.
    screw_positions = (-2.98, 2.98)
    for z in screw_positions:
        body += cylinder_y(.18, -1.66, -1.00, z)
        body -= cylinder_y(.065, -1.67, -1.05, z)
    body.label = "STB40S PVC body"
    body.color = Color(.42, .43, .44)

    cover = capsule(2.30, 7.41, -1.80, -1.66)
    screws = []
    for z in screw_positions:
        cover -= cylinder_y(.080, -1.81, -1.65, z)
        screw = cylinder_y(.070, -1.82, -1.19, z)
        screw += cylinder_y(.15, -1.92, -1.80, z)
        # Plain slot head; actual thread and drive profile are not specified.
        slot = Box(.24 * INCH, .045 * INCH, .040 * INCH).translate(
            (0, -1.9075 * INCH, z * INCH))
        screw -= slot
        screw.label = f"Cover screw {'upper' if z > 0 else 'lower'}"
        screw.color = Color(.65, .66, .68)
        screws.append(screw)
    cover.label = "Removable PVC access cover"
    cover.color = Color(.49, .50, .51)
    return Compound(label="IPEX Scepter STB40S 077454", children=[body, cover, *screws])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    model = make_model()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not export_step(model, args.output):
        raise RuntimeError("STEP export failed")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
