"""Revalidate even frozen values at an untrusted runtime boundary."""

from dataclasses import replace

from cyberpilot_autotune.contracts import ObservationSnapshot, TuningProposal
from cyberpilot_autotune.contracts.validation import NonFiniteError, ValidationError

from .reasons import ReasonCode


def observation_error(value: ObservationSnapshot) -> ReasonCode | None:
    try:
        replace(value)
    except NonFiniteError:
        return ReasonCode.NON_FINITE
    except (ValidationError, TypeError, AttributeError):
        return ReasonCode.INVALID_OBSERVATION
    if not value.source_valid or any(
        signal is None
        for signal in (
            value.speed_mps,
            value.desired_curvature_inv_m,
            value.measured_curvature_inv_m,
            value.driver_override,
            value.controller_saturated,
        )
    ):
        return ReasonCode.INVALID_OBSERVATION
    return None


def proposal_error(value: object) -> ReasonCode | None:
    if type(value) is not TuningProposal:
        return ReasonCode.INVALID_PROPOSAL
    try:
        replace(value)
    except NonFiniteError:
        return ReasonCode.NON_FINITE
    except (ValidationError, TypeError, AttributeError):
        return ReasonCode.INVALID_PROPOSAL
    return None
