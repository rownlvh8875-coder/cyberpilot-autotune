"""Exact comparisons for hard bounds and baseline-relative step budgets."""

from fractions import Fraction

from cyberpilot_autotune.contracts import ParameterSpec


def within_bounds(candidate: float, spec: ParameterSpec) -> bool:
    return spec.lower_bound <= candidate <= spec.upper_bound


def within_step(candidate: float, baseline: float, maximum_step: float) -> bool:
    return abs(Fraction(candidate) - Fraction(baseline)) <= Fraction(maximum_step)
