from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class BuildStep:
    number: int
    object_names: tuple[str, ...]


_HEADING_RE = re.compile(r"^## (\d+)\. .+$", re.MULTILINE)
_OBJECT_BLOCK_RE = re.compile(
    r"^New model objects:\s*\n+```text\n(.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
_OBJECT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_build_steps(path: str | Path) -> tuple[BuildStep, ...]:
    """Parse numbered object assignments from a BUILD_STEPS-style document."""
    path = Path(path)
    text = path.read_text()
    headings = list(_HEADING_RE.finditer(text))
    if not headings:
        raise ValueError(f"{path}: no numbered build steps found")

    steps: list[BuildStep] = []
    assigned: dict[str, int] = {}
    for index, heading in enumerate(headings):
        number = int(heading.group(1))
        expected = index + 1
        if number != expected:
            raise ValueError(
                f"{path}: expected build step {expected}, found step {number}"
            )

        section_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(text)
        )
        section = text[heading.end() : section_end]
        blocks = list(_OBJECT_BLOCK_RE.finditer(section))
        if len(blocks) != 1:
            raise ValueError(
                f"{path}: build step {number} must contain exactly one "
                "New model objects block"
            )

        names = tuple(
            line.strip()
            for line in blocks[0].group(1).splitlines()
            if line.strip()
        )
        if not names:
            raise ValueError(f"{path}: build step {number} has no model objects")

        for name in names:
            if not _OBJECT_NAME_RE.fullmatch(name):
                raise ValueError(
                    f"{path}: invalid model object identifier {name!r} "
                    f"in build step {number}"
                )
            if name in assigned:
                raise ValueError(
                    f"{path}: model object {name!r} is assigned to both "
                    f"build steps {assigned[name]} and {number}"
                )
            assigned[name] = number

        steps.append(BuildStep(number=number, object_names=names))

    return tuple(steps)
