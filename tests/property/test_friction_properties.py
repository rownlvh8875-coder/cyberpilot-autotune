"""Ideal algebraic symmetries do not grant scientific or application authority."""

from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.research.friction_model.candidates import fit
from cyberpilot_autotune.research.friction_model.experiments import toy_context
from cyberpilot_autotune.research.friction_model.synthetic import Scenario, generate


@settings(max_examples=30, deadline=None)
@given(
    factor=st.floats(min_value=0.8, max_value=5, allow_nan=False),
    offset=st.floats(min_value=-0.2, max_value=0.2, allow_nan=False),
)
def test_zero_friction_ideal_model_never_systematically_manufactures_C(factor, offset):
    result = fit(
        generate(Scenario(factor=factor, friction=0, offset=offset), toy_context()), "controller"
    )
    assert result.estimate == pytest.approx(0, abs=1e-10)
    assert not result.application_authorized


@settings(max_examples=25, deadline=None)
@given(friction=st.floats(min_value=0, max_value=0.4, allow_nan=False))
def test_joint_model_preserves_sign_symmetry(friction):
    rows = generate(Scenario(friction=friction), toy_context())
    mirrored = tuple(
        replace(
            r,
            acceleration=-r.acceleration,
            callback_output=-r.callback_output,
            q=-r.q,
            explicit_term=-r.explicit_term,
            pid=-r.pid,
            total=-r.total,
        )
        for r in rows
    )
    before = fit(rows, "controller")
    after = fit(mirrored, "controller")
    assert after.factor == pytest.approx(before.factor)
    assert after.estimate == pytest.approx(before.estimate)
    assert after.intercept == pytest.approx(-before.intercept)
