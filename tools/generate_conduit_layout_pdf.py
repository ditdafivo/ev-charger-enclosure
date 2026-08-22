from __future__ import annotations

import argparse
from pathlib import Path
import sys

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build


PAGE_WIDTH, PAGE_HEIGHT = letter
SAFE_MARGIN = 0.35 * inch
CALIBRATION_LENGTH = 6 * inch


def _draw_crosshair(pdf: canvas.Canvas, x: float, y: float) -> None:
    arm = 0.16 * inch
    gap = 0.045 * inch
    pdf.setLineWidth(0.6)
    pdf.line(x-arm, y, x-gap, y)
    pdf.line(x+gap, y, x+arm, y)
    pdf.line(x, y-arm, x, y-gap)
    pdf.line(x, y+gap, x, y+arm)


def _draw_calibration_lines(pdf: canvas.Canvas) -> None:
    pdf.saveState()
    pdf.setLineWidth(0.8)

    horizontal_start = (1.25 * inch, 9.85 * inch)
    horizontal_end_x = horizontal_start[0] + CALIBRATION_LENGTH
    pdf.line(horizontal_start[0], horizontal_start[1], horizontal_end_x, horizontal_start[1])
    for index in range(7):
        x = horizontal_start[0] + index*inch
        pdf.line(x, horizontal_start[1]-0.07*inch, x, horizontal_start[1]+0.07*inch)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(
        (horizontal_start[0]+horizontal_end_x)/2,
        horizontal_start[1]+0.10*inch,
        "HORIZONTAL CALIBRATION: 6.000 in between end ticks; 1.000 in intervals",
    )

    vertical_x = 0.65 * inch
    vertical_start_y = 2.25 * inch
    vertical_end_y = vertical_start_y + CALIBRATION_LENGTH
    pdf.line(vertical_x, vertical_start_y, vertical_x, vertical_end_y)
    for index in range(7):
        y = vertical_start_y + index*inch
        pdf.line(vertical_x-0.07*inch, y, vertical_x+0.07*inch, y)
    pdf.translate(vertical_x-0.13*inch, (vertical_start_y+vertical_end_y)/2)
    pdf.rotate(90)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(
        0,
        0,
        "VERTICAL CALIBRATION: 6.000 in between end ticks; 1.000 in intervals",
    )
    pdf.restoreState()


def _draw_post_note(
    pdf: canvas.Canvas,
    *,
    x: float,
    y: float,
    align: str,
    post_name: str,
    power_offset: tuple[float, float],
    low_voltage_offset: tuple[float, float],
) -> None:
    draw = pdf.drawRightString if align == "right" else pdf.drawString
    pdf.setFont("Helvetica-Bold", 7)
    draw(x, y, f"{post_name} POST CENTER")
    pdf.setFont("Helvetica", 6.5)
    draw(
        x,
        y-0.11*inch,
        f"from POWER: DX {power_offset[0]:+0.4f}, DY {power_offset[1]:+0.4f} in",
    )
    draw(
        x,
        y-0.22*inch,
        f"from LOW-V: DX {low_voltage_offset[0]:+0.4f}, DY {low_voltage_offset[1]:+0.4f} in",
    )


def _draw_dimension_reference(
    pdf: canvas.Canvas,
    low_voltage_page: tuple[float, float],
    power_page: tuple[float, float],
    delta_x: float,
    delta_y: float,
) -> None:
    pdf.saveState()
    pdf.setDash(4, 3)
    pdf.setStrokeGray(0.35)
    pdf.setLineWidth(0.6)
    pdf.line(
        low_voltage_page[0],
        low_voltage_page[1],
        power_page[0],
        low_voltage_page[1],
    )
    pdf.line(
        power_page[0],
        low_voltage_page[1],
        power_page[0],
        power_page[1],
    )
    pdf.setDash()
    pdf.setFillGray(0.15)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(
        (low_voltage_page[0]+power_page[0])/2,
        low_voltage_page[1]+0.10*inch,
        f"DX = {delta_x:0.3f} in",
    )
    pdf.translate(power_page[0]-0.12*inch, (low_voltage_page[1]+power_page[1])/2)
    pdf.rotate(90)
    pdf.drawCentredString(0, 0, f"DY = {delta_y:0.3f} in")
    pdf.restoreState()


def generate(output_path: Path) -> None:
    enclosure = build.default_build
    power_center = (enclosure.POWER_T_AXIS_X, enclosure.POWER_T_AXIS_Y)
    low_voltage_center = (
        enclosure.LOW_VOLTAGE_INPUT_X,
        enclosure.LOW_VOLTAGE_INPUT_Y,
    )
    power_diameter = build.CONDUIT_OD_BY_TRADE_SIZE["1-1/4"]
    low_voltage_diameter = build.CONDUIT_OD_BY_TRADE_SIZE["3/4"]
    delta_x = power_center[0]-low_voltage_center[0]
    delta_y = power_center[1]-low_voltage_center[1]

    cross_section_width = (
        delta_x + power_diameter/2 + low_voltage_diameter/2
    )
    cross_section_height = (
        delta_y + power_diameter/2 + low_voltage_diameter/2
    )
    if cross_section_width*inch > PAGE_WIDTH-2*SAFE_MARGIN:
        raise ValueError("conduit cross section does not fit letter paper in X at 1:1")
    if cross_section_height*inch > PAGE_HEIGHT-2*SAFE_MARGIN:
        raise ValueError("conduit cross section does not fit letter paper in Y at 1:1")

    low_voltage_page = (2.30*inch, 1.50*inch)
    power_page = (
        low_voltage_page[0]+delta_x*inch,
        low_voltage_page[1]+delta_y*inch,
    )
    envelopes = (
        (*low_voltage_page, low_voltage_diameter*inch/2),
        (*power_page, power_diameter*inch/2),
    )
    for x, y, radius in envelopes:
        if not (
            SAFE_MARGIN <= x-radius
            and x+radius <= PAGE_WIDTH-SAFE_MARGIN
            and SAFE_MARGIN <= y-radius
            and y+radius <= PAGE_HEIGHT-SAFE_MARGIN
        ):
            raise ValueError("a conduit envelope falls outside the printable safe area")

    post_centers = {
        name.removeprefix("post_").upper(): (
            enclosure.members[name].center_on("x"),
            enclosure.members[name].center_on("y"),
        )
        for name in ("post_fl", "post_fr", "post_bl", "post_br")
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(output_path),
        pagesize=letter,
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle("EV charger enclosure conduit layout template")
    pdf.setAuthor("ev-charger-enclosure model")
    pdf.setSubject("Actual-size conduit cross section and post-center offsets")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(PAGE_WIDTH/2, 10.72*inch, "CONDUIT LAYOUT TEMPLATE - US LETTER - SCALE 1:1")
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(
        PAGE_WIDTH/2,
        10.12*inch,
        "Print at Actual size / 100%. Disable Fit, Shrink, and Scale to printable area.",
    )

    for post_name, x, y, align in (
        ("BL", 0.35*inch, 10.52*inch, "left"),
        ("BR", 8.15*inch, 10.52*inch, "right"),
        ("FL", 0.35*inch, 0.72*inch, "left"),
        ("FR", 8.15*inch, 0.72*inch, "right"),
    ):
        post_center = post_centers[post_name]
        _draw_post_note(
            pdf,
            x=x,
            y=y,
            align=align,
            post_name=post_name,
            power_offset=(
                post_center[0]-power_center[0],
                post_center[1]-power_center[1],
            ),
            low_voltage_offset=(
                post_center[0]-low_voltage_center[0],
                post_center[1]-low_voltage_center[1],
            ),
        )

    _draw_calibration_lines(pdf)
    _draw_dimension_reference(
        pdf,
        low_voltage_page,
        power_page,
        delta_x,
        delta_y,
    )

    pdf.setLineWidth(1.0)
    pdf.setFillGray(0.93)
    pdf.circle(
        power_page[0],
        power_page[1],
        power_diameter*inch/2,
        stroke=1,
        fill=1,
    )
    pdf.setFillGray(1)
    pdf.circle(
        low_voltage_page[0],
        low_voltage_page[1],
        low_voltage_diameter*inch/2,
        stroke=1,
        fill=1,
    )
    pdf.setFillGray(0)
    _draw_crosshair(pdf, power_page[0], power_page[1])
    _draw_crosshair(pdf, low_voltage_page[0], low_voltage_page[1])

    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(
        power_page[0],
        power_page[1]-0.25*inch,
        "POWER",
    )
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(
        power_page[0],
        power_page[1]-0.37*inch,
        f'1-1/4 in trade; modeled OD {power_diameter:0.3f} in',
    )
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(
        low_voltage_page[0],
        low_voltage_page[1]-0.25*inch,
        "LOW VOLTAGE",
    )
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(
        low_voltage_page[0],
        low_voltage_page[1]-0.37*inch,
        f'3/4 in trade; modeled OD {low_voltage_diameter:0.3f} in',
    )
    pdf.setFont("Helvetica", 6.5)
    pdf.drawCentredString(
        PAGE_WIDTH/2,
        0.30*inch,
        "+X is right; +Y is toward the back/top of this sheet. DX/DY notes run from conduit center to post center.",
    )
    pdf.showPage()
    pdf.save()

    reader = PdfReader(str(output_path))
    if len(reader.pages) != 1:
        raise ValueError("generated template must contain exactly one page")
    media_box = reader.pages[0].mediabox
    if float(media_box.width) != PAGE_WIDTH or float(media_box.height) != PAGE_HEIGHT:
        raise ValueError(
            f"generated page is {float(media_box.width)} x {float(media_box.height)} points, not letter"
        )

    print(
        f"wrote {output_path}: letter 8.5 x 11 in, scale 1:1; "
        f"conduit envelope {cross_section_width:.3f} x {cross_section_height:.3f} in"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the actual-size letter-paper conduit layout template."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("fabrication/conduit_cross_section_letter.pdf"),
    )
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
