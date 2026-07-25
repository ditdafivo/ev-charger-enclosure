from __future__ import annotations

from dataclasses import dataclass


CONDUCTOR_VOLUME_BY_AWG: dict[int, float] = {
    18: 1.50,
    16: 1.75,
    14: 2.00,
    12: 2.25,
    10: 2.50,
    8: 3.00,
    6: 5.00,
}


def conductor_fill_volume(*, awg: int, count: int) -> float:
    if count < 0:
        raise ValueError("conductor count must be non-negative")
    try:
        allowance = CONDUCTOR_VOLUME_BY_AWG[awg]
    except KeyError as exc:
        raise ValueError(f"unsupported box-fill conductor size: {awg} AWG") from exc
    return allowance * count


def equipment_grounding_fill_volume(*awgs: int) -> float:
    if not awgs:
        return 0.0
    try:
        largest_allowance = max(CONDUCTOR_VOLUME_BY_AWG[awg] for awg in awgs)
    except KeyError as exc:
        raise ValueError(
            f"unsupported box-fill grounding conductor size: {exc.args[0]} AWG"
        ) from exc

    additional_quarters = max(0, len(awgs) - 4)
    return largest_allowance * (1 + additional_quarters / 4)


@dataclass(frozen=True)
class BoxFillCalculation:
    marked_volume: float
    conductor_groups: tuple[tuple[int, int], ...]
    equipment_grounding_awgs: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.marked_volume <= 0:
            raise ValueError("marked box volume must be positive")

    @property
    def required_volume(self) -> float:
        return sum(
            conductor_fill_volume(awg=awg, count=count)
            for awg, count in self.conductor_groups
        ) + equipment_grounding_fill_volume(*self.equipment_grounding_awgs)

    @property
    def remaining_volume(self) -> float:
        return self.marked_volume - self.required_volume

    def validate(self) -> None:
        if self.remaining_volume < 0:
            raise ValueError(
                f"required box fill {self.required_volume:.2f} cu in exceeds "
                f"marked volume {self.marked_volume:.2f} cu in"
            )
