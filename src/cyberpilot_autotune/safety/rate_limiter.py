"""Conservative shadow budget; no applied-value history or vehicle policy."""

from fractions import Fraction


def within_rate(
    candidate: float,
    baseline: float,
    maximum_rate: float,
    timestamp_s: float,
    previous_timestamp_s: float | None,
) -> bool:
    delta = abs(Fraction(candidate) - Fraction(baseline))
    if previous_timestamp_s is None:
        return delta == 0
    elapsed = Fraction(timestamp_s) - Fraction(previous_timestamp_s)
    return elapsed > 0 and delta <= Fraction(maximum_rate) * elapsed
