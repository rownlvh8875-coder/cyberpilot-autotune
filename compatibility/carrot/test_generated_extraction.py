"""Real pycapnp reader tests; run only with the explicitly pinned checkout."""

from dataclasses import replace

import pytest
from openpilot.cereal import car, log

from compatibility.carrot.builders import car_control, car_output, car_state, sample
from cyberpilot_autotune.adapters.carrot_receipt_contract import evaluate
from cyberpilot_autotune.integrations.carrot.availability import require_schema
from cyberpilot_autotune.integrations.carrot.cache import ExactCache
from cyberpilot_autotune.integrations.carrot.extraction import (
    extract_car_control,
    extract_car_output,
    extract_car_state,
)
from tests.audit.test_observation_v2_cases import CASES, from_case, projection
from tests.fixtures.carrot_adapter import healthy
from tests.fixtures.carrot_v2 import BASELINE, complete


def test_actual_generated_binding_is_qualified_not_a_double():
    binding = require_schema()
    assert binding.reader_version == "2.1.0"
    assert binding.reader_type is type(car.CarControl.new_message().as_reader())
    assert car.ObservationFloat64.new_message().which() == "unavailable"
    value = car.ObservationFloat64.new_message()
    value.value = 0.0
    assert value.which() == "value" and value.value == 0.0


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: c["id"])
def test_all_literal_contracts_through_real_readers_and_exact_caches(case):
    attempt, policy = from_case(case)
    binding = require_schema()
    commands = ExactCache(2)
    states = ExactCache(2)
    source = attempt.source_command
    if source is not None:
        event = car_control(log, source)
        extracted = extract_car_control(
            sample(event), binding, static_context_digest=source.static_context_digest
        )
        commands.put(source.event_time.value_ns, extracted, healthy())
        if not attempt.exact_lookup_unambiguous:
            commands.put(
                source.event_time.value_ns,
                replace(extracted, desired_target_curvature_inv_m=0.5),
                healthy(),
            )
    cs = attempt.source_car_state
    if cs is not None:
        event = car_state(log, cs)
        # Scalar Bool has no unavailable encoding. Carry this synthetic case's
        # missing capability outside the wire, never reinterpret default False.
        extracted = extract_car_state(
            sample(event),
            binding,
            steering_pressed_supported=cs.steering_pressed_supported
            and cs.steering_pressed is not None,
        )
        states.put(cs.event_time.value_ns, extracted, healthy())
    output = car_output(log, attempt.receipt, event_valid=attempt.outer_car_output_valid)
    receipt = extract_car_output(sample(output), binding)
    entry = commands.lookup(receipt.source_command_time.value_ns)
    source = entry.evidence if entry else None
    state_entry = states.lookup(source.measurement.car_state_time.value_ns) if source else None
    result = evaluate(
        replace(
            attempt,
            receipt=receipt,
            source_command=source,
            source_car_state=state_entry.evidence if state_entry else None,
        ),
        policy,
        BASELINE,
    )
    assert projection(result, True) == case["expected"]


def test_reader_lifetime_and_mutation_do_not_change_copied_evidence():
    attempt, _ = complete()
    binding = require_schema()
    event = car_control(log, attempt.source_command)
    data = event.to_bytes()
    with log.Event.from_bytes(data) as reader:
        copied = extract_car_control(
            sample(reader.as_builder()),
            binding,
            static_context_digest=attempt.static_context.digest,
        )
    event.carControl.lateralControlObservation.desiredTargetCurvatureInvM.value = 9
    assert copied.desired_target_curvature_inv_m == 0.0
    assert copied.measurement.input_speed_mps == 2.0
