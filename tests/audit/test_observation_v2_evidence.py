"""Evidence pin/range/case mutations must invalidate the audit."""

from copy import deepcopy

import pytest

from tests.audit.validate_observation_v2 import load_evidence, validate


def test_pinned_sources_and_literal_cases_validate_offline():
    sources, cases = load_evidence()
    summary = validate(sources, cases)
    assert summary["changed_files"] == 26 and summary["cases"] >= 40
    assert sources["decision"] == "CONTRACT_READY_FOR_PHASE_8B"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s, c: s.update(observation_v2_head="0" * 40),
        lambda s, c: s["changed_files"].pop(),
        lambda s, c: s["changed_files"][0]["head"].update(sha256="broken"),
        lambda s, c: s["changed_files"][0].update(path="../outside"),
        lambda s, c: s["evidence_ranges"][0].update(end_line=10**9),
        lambda s, c: s["mandatory_gates"].update(control_active="UNRESOLVED"),
        lambda s, c: c["cases"][0]["expected"].update(source_valid=False),
        lambda s, c: c["cases"].append(deepcopy(c["cases"][0])),
    ],
)
def test_mutated_evidence_is_rejected(mutation):
    sources, cases = load_evidence()
    mutation(sources, cases)
    with pytest.raises(ValueError):
        validate(sources, cases)
