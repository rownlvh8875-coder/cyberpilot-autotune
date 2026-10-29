"""H5 source/history/report evidence rejects changed bindings and false readiness."""

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def artifacts():
    return tuple(
        json.loads((ROOT / "docs/evidence" / name).read_text(encoding="utf-8"))
        for name in (
            "torque_identification_scientific_sources.json",
            "torque_identification_policy.json",
        )
    )


def test_scientific_sources_and_frozen_policy_have_complete_bindings():
    from tests.audit.validate_torque_science import validate

    sources, policy = artifacts()
    result = validate(sources, policy)
    assert result["files"] >= 20 and result["ranges"] >= 30
    assert result["source_bytes_verified"] is False
    assert result["application_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "source_pin",
        "policy",
        "range",
        "blob",
        "missing_file",
        "duplicate_file",
        "escape_path",
        "authority",
        "preserved",
    ],
)
def test_altered_source_or_policy_binding_never_validates(mutation):
    from tests.audit.validate_torque_science import validate

    sources, policy = copy.deepcopy(artifacts())
    if mutation == "source_pin":
        sources["pins"]["runtime"] = "0" * 40
    elif mutation == "policy":
        policy["route_stability_acceptance_threshold"] = 0.05
    elif mutation == "range":
        sources["files"][0]["ranges"][0]["end"] = 10**9
    elif mutation == "blob":
        sources["files"][0]["git_blob"] = "malformed"
    elif mutation == "missing_file":
        sources["files"].pop()
    elif mutation == "duplicate_file":
        sources["files"].append(sources["files"][0])
    elif mutation == "escape_path":
        sources["files"][0]["path"] = "../private"
    elif mutation == "authority":
        sources["application_authorized"] = True
    else:
        sources["preserved_files"]["src/cyberpilot_autotune/owner_protocol/reference_owner.py"] = (
            "0" * 64
        )
    with pytest.raises(ValueError):
        validate(sources, policy)


def test_final_results_preserve_unavailable_development_statistics_and_false_authority():
    from tests.audit.validate_torque_science import validate_results

    sources, policy = artifacts()
    results = json.loads((ROOT / "docs/evidence/torque_identification_results.json").read_text())
    assert validate_results(results, sources, policy)["development_fit_executed"] is False
    changed = copy.deepcopy(results)
    changed["report"]["candidate_generation_allowed"] = True
    with pytest.raises(ValueError):
        validate_results(changed, sources, policy)


def test_git_history_proves_frozen_policy_existed_before_result_introduction():
    from tests.audit.validate_torque_science import verify_history

    # Explicit integration check of actual commit graph, not a text assertion.
    result = verify_history(require_results=False)
    assert result["freeze_ancestor"] is True
    assert result["results_absent_at_freeze"] is True


@pytest.mark.parametrize("mutation", ["scope", "preservation_set"])
def test_source_scope_or_protected_owner_file_cannot_be_removed(mutation):
    from tests.audit.validate_torque_science import validate

    sources, policy = artifacts()
    if mutation == "scope":
        sources["scope"] = "VEHICLE_APPLICATION_READY"
    else:
        sources["preserved_files"].pop("src/cyberpilot_autotune/owner_protocol/reference_owner.py")
    with pytest.raises(ValueError):
        validate(sources, policy)


@pytest.mark.parametrize(
    "mutation", ["truth", "estimate", "scenario", "missing_case", "factor_verdict"]
)
def test_stale_or_altered_synthetic_execution_results_are_not_accepted(mutation):
    from tests.audit.validate_torque_science import validate_results

    sources, policy = artifacts()
    result = json.loads((ROOT / "docs/evidence/torque_identification_results.json").read_text())
    case = result["report"]["synthetic_recovery_summary"][0]
    if mutation == "truth":
        case["true_factor"] = 99.0
    elif mutation == "estimate":
        case["numerical"]["fit"]["linear_mode_tls_lat_accel_slope"] = 99.0
    elif mutation == "scenario":
        case["scenario_digest"] = "0" * 64
    elif mutation == "missing_case":
        result["report"]["synthetic_recovery_summary"].pop()
    else:
        result["report"]["factor_verdict"] = "FACTOR_IDENTIFICATION_QUALIFIED_LINEAR_MODE"
    with pytest.raises(ValueError):
        validate_results(result, sources, policy)


@pytest.mark.parametrize(
    "lines,branches,accepted",
    [(98, 95, True), (97, 100, False), (100, 94, False), (100, 100, True)],
)
def test_research_statement_and_branch_coverage_are_separate_gates(lines, branches, accepted):
    from tests.audit.validate_torque_science import check_coverage

    totals = {
        "num_statements": 100,
        "covered_lines": lines,
        "num_branches": 100,
        "covered_branches": branches,
    }
    if accepted:
        assert check_coverage({"totals": totals})["statements_percent"] == lines
    else:
        with pytest.raises(ValueError):
            check_coverage({"totals": totals})
