"""Generic parameter descriptions; no vehicle registry is supplied."""

from dataclasses import dataclass
from enum import Enum

from .validation import ValidationError, boolean, finite, nonnegative, text


class OutOfRangePolicy(Enum):
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    parameter_id: str
    units: str
    lower_bound: float
    upper_bound: float
    maximum_step: float
    maximum_rate_per_second: float
    description: str
    persistence_eligible: bool
    out_of_range_policy: OutOfRangePolicy = OutOfRangePolicy.REJECT

    def __post_init__(self) -> None:
        text(self.parameter_id, "parameter_id")
        text(self.units, "units")
        text(self.description, "description")
        finite(self.lower_bound, "lower_bound")
        finite(self.upper_bound, "upper_bound")
        if self.lower_bound > self.upper_bound:
            raise ValidationError("inverted bounds")
        nonnegative(self.maximum_step, "maximum_step")
        nonnegative(self.maximum_rate_per_second, "maximum_rate_per_second")
        boolean(self.persistence_eligible, "persistence_eligible")
        if self.out_of_range_policy is not OutOfRangePolicy.REJECT:
            raise ValidationError("only REJECT is supported")
