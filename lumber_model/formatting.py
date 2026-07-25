from __future__ import annotations

import math


def fmt_float(value: float) -> str:
    text = f"{value:.4f}"
    text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def scad_bool(value: bool) -> str:
    return "true" if value else "false"


def scad_string(value: str) -> str:
    """
    Minimal OpenSCAD string escaping.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def sanitize_scad_identifier(value: str) -> str:
    """
    Convert a user-facing assembly name into a valid OpenSCAD variable name.

    Examples:
      "front_frame" -> "front_frame"
      "front frame" -> "front_frame"
      "2nd frame"   -> "_2nd_frame"
    """
    out = []

    for ch in value:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")

    result = "".join(out)

    if not result:
        result = "assembly"

    if result[0].isdigit():
        result = "_" + result

    return result


def round_to_increment(value: float, increment: float) -> float:
    if increment <= 0:
        raise ValueError("increment must be positive")

    return round(value / increment) * increment


def inches_to_fraction_text(value: float, denominator: int = 16) -> str:
    """
    Convert decimal inches to a simple inch string.

    Examples:
      56.5    -> 56 1/2"
      48.0    -> 48"
      10.0625 -> 10 1/16"
    """
    if denominator <= 0:
        raise ValueError("denominator must be positive")

    whole = math.floor(value)
    frac = value - whole
    numerator = round(frac * denominator)

    if numerator == 0:
        return f'{whole}"'

    if numerator == denominator:
        return f'{whole + 1}"'

    gcd = math.gcd(numerator, denominator)
    numerator //= gcd
    denominator //= gcd

    if whole == 0:
        return f'{numerator}/{denominator}"'

    return f'{whole} {numerator}/{denominator}"'
