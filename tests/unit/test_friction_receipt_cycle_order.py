"""Serial controller cycles cannot replay context/callback time across publications."""

from dataclasses import fields, replace

import pytest

from cyberpilot_autotune.observability import contracts as c
from cyberpilot_autotune.observability.types import (
    ClockDomain,
    ScalarOrigin,
    Signal,
    SourceOrigin,
    Stage,
)
from tests.fixtures.friction_receipt import complete, scalar
from tests.unit.test_friction_receipt import reasons


def retime(receipt, **changes):
    """Retag consistent synthetic records; no old cycle binding is left behind."""
    cycle = replace(receipt.cycle, **changes)

    def scalars(record):
        return replace(
            record,
            **{
                f.name: replace(
                    value,
                    cycle_digest=cycle.digest,
                    captured_mono_time_ns=cycle.callback_exit_mono_time_ns
                    if value.stage in {Stage.CALLBACK_INPUT, Stage.HELPER_Q, Stage.RAW_CALLBACK}
                    else value.captured_mono_time_ns,
                )
                for f in fields(record)
                if isinstance(value := getattr(record, f.name), c.ScalarObservation)
            },
        )

    return replace(
        receipt,
        cycle=cycle,
        signals=scalars(receipt.signals),
        stages=replace(
            scalars(receipt.stages),
            downstream_cycle_id=cycle.digest,
            downstream_identities=tuple(
                replace(i, controller_cycle_digest=cycle.digest)
                for i in receipt.stages.downstream_identities
            ),
        ),
        context=replace(
            receipt.context,
            cycle_digest=cycle.digest,
            snapshot_time_ns=cycle.context_capture_mono_time_ns,
            gains=replace(receipt.context.gains, cycle_digest=cycle.digest),
        ),
        sources=tuple(
            replace(
                s,
                controller_cycle_digest=cycle.digest
                if s.origin == SourceOrigin.LOCAL_CYCLE_OBJECT
                else s.controller_cycle_digest,
                source_time_ns=min(s.source_time_ns, cycle.context_capture_mono_time_ns - 1),
            )
            for s in receipt.sources
        ),
    )


@pytest.mark.parametrize("start", [20000, 20010, 20025])
def test_next_cycle_context_and_callback_cannot_replay_or_overlap_previous_publication(start):
    previous = complete(10)
    current = retime(
        complete(11),
        context_capture_mono_time_ns=start,
        callback_enter_mono_time_ns=start + 10,
        callback_exit_mono_time_ns=start + 20,
    )
    assert reasons(current) == set()
    assert "TIME_ORDER_INVALID" in reasons(current, previous)


@pytest.mark.parametrize("requested_value_available", [False, True])
def test_next_context_must_follow_previous_command_event_when_identity_is_available(
    requested_value_available,
):
    previous = retime(complete(10), receipt_complete_mono_time_ns=21500)
    later = 21400
    previous = replace(
        previous,
        stages=replace(
            previous.stages,
            requested_torque=replace(previous.stages.requested_torque, captured_mono_time_ns=later)
            if requested_value_available
            else None,
            downstream_identities=(
                replace(previous.stages.downstream_identities[0], source_time_ns=later),
            ),
        ),
    )
    assert reasons(previous) == set()
    assert "TIME_ORDER_INVALID" in reasons(complete(11), previous)


def test_exact_previous_publication_boundary_is_allowed_without_inventing_an_interval_cutoff():
    previous = complete(10)
    start = previous.cycle.control_event_mono_time_ns
    current = retime(
        complete(11),
        context_capture_mono_time_ns=start,
        callback_enter_mono_time_ns=start + 10,
        callback_exit_mono_time_ns=start + 20,
    )
    assert reasons(current, previous) == set()


def test_absent_previous_command_identity_uses_known_control_publication_not_fabricated_time():
    previous = complete(10)
    previous = replace(
        previous,
        stages=replace(previous.stages, requested_torque=None, downstream_identities=()),
    )
    assert reasons(complete(11), previous) == set()


def test_late_downstream_companion_does_not_force_next_controller_cycle_to_wait():
    previous = retime(complete(10), receipt_complete_mono_time_ns=30000)
    late = 26000
    applied = scalar(
        previous.cycle,
        Signal.APPLIED_TORQUE,
        -0.3,
        Stage.APPLIED_TORQUE,
        ScalarOrigin.DOWNSTREAM,
        captured_mono_time_ns=late,
    )
    identity = c.DownstreamStageIdentity(
        stage=Stage.APPLIED_TORQUE,
        source_event_id="e" * 64,
        source_command_event_id=previous.stages.downstream_identities[0].source_event_id,
        source_time_ns=late,
        clock_domain=ClockDomain.MONOTONIC,
        controller_cycle_digest=previous.cycle.digest,
        exact_source_command_reference=True,
        source_valid=True,
        source_transport_healthy=True,
    )
    previous = replace(
        previous,
        stages=replace(
            previous.stages,
            applied_torque=applied,
            downstream_identities=(*previous.stages.downstream_identities, identity),
        ),
    )
    assert reasons(previous) == set()
    assert complete(11).cycle.context_capture_mono_time_ns < late
    assert reasons(complete(11), previous) == set()


@pytest.mark.parametrize(
    "change", [{"session_id": "9" * 64}, {"controller_instance_generation": 2}]
)
def test_new_session_or_controller_instance_starts_a_distinct_epoch_not_a_replayed_cycle(change):
    previous = complete(10)
    current = retime(
        complete(11),
        context_capture_mono_time_ns=20000,
        callback_enter_mono_time_ns=20010,
        callback_exit_mono_time_ns=20020,
        **change,
    )
    assert reasons(current) == set()
    observed = reasons(current, previous)
    assert "TIME_ORDER_INVALID" not in observed
    assert "EPOCH_CONTEXT_CHANGED" in observed
