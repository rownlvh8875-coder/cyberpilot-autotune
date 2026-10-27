"""Fuzz untrusted proposal shapes without network or wall time."""

from hypothesis import given, settings
from hypothesis import strategies as st

from cyberpilot_autotune.runtime.mode import RuntimeMode
from tests.fixtures.synthetic import ScriptedLearner
from tests.integration.test_runtime import engine
from tests.unit.test_contracts import observation, proposal
from tests.unit.test_gate import BASELINE


@settings(derandomize=True, deadline=None)
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(),
        st.text(),
        st.lists(st.integers(), max_size=8),
        st.dictionaries(st.text(), st.floats(), max_size=4),
    )
)
def test_arbitrary_malformed_proposals_never_escape_boundary(value):
    result = engine(learner=ScriptedLearner(output=value)).step(observation())
    assert result.effective_parameters == BASELINE


@settings(derandomize=True, deadline=None)
@given(st.floats(allow_nan=True, allow_infinity=True), st.sampled_from(list(RuntimeMode)))
def test_any_candidate_retains_baseline(value, mode):
    candidate = proposal()
    object.__setattr__(candidate, "proposed_value", value)
    result = engine(mode=mode, learner=ScriptedLearner((candidate,))).step(observation())
    assert result.effective_parameters == result.baseline_parameters == BASELINE
