"""Synthetic host-transaction invariants, not vehicle performance evidence."""

from dataclasses import replace
from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.application.contracts import ApplicationReason as R
from cyberpilot_autotune.application.contracts import ApplicationState as S
from cyberpilot_autotune.application.coordinator import BoundedSteeringApplicator
from tests.fixtures.steering_application import (
    Authority,
    Clock,
    MemoryTarget,
    baseline,
    policy,
    request,
)


@given(st.floats(allow_nan=False, allow_infinity=False, width=64))
@settings(max_examples=150)
def test_every_verified_host_commit_obeys_bounds_step_and_actual_rate(value):
    p, clock = policy(), Clock()
    target = MemoryTarget(clock, baseline(p))
    app = BoundedSteeringApplicator(p, baseline(p), target, Authority(), clock)
    result = app.process(request(p, value=value))
    if result.reason is R.VERIFIED:
        spec = p.parameters[0]
        actual = target.current.values[spec.parameter_id]
        delta = abs(Fraction(actual) - Fraction(baseline(p).values[spec.parameter_id]))
        assert spec.lower_bound <= actual <= spec.upper_bound
        assert delta <= Fraction(spec.maximum_step)
        assert delta <= Fraction(spec.maximum_rate_per_second) * Fraction(clock.time)
        assert result.effective_parameters == target.current.values
        assert result.state is S.ACTIVE
    else:
        assert target.current.values == baseline(p).values and not target.writes


@given(
    st.lists(
        st.sampled_from(["healthy", "override", "saturated", "invalid"]), min_size=1, max_size=20
    )
)
def test_identical_synthetic_streams_produce_identical_receipts(events):
    def run():
        p, clock = policy(), Clock()
        target = MemoryTarget(clock, baseline(p))
        app = BoundedSteeringApplicator(p, baseline(p), target, Authority(), clock)
        results = []
        for seq, event in enumerate(events):
            clock.time = 1.0 + seq * 0.1
            item = request(
                p, sequence=seq, now=clock.time, revision=target.current.revision, value=10.0
            )
            obs = replace(
                item.observation,
                driver_override=event == "override",
                controller_saturated=event == "saturated",
                source_valid=event != "invalid",
            )
            results.append(app.process(replace(item, observation=obs)))
        return results, target.writes

    assert run() == run()
