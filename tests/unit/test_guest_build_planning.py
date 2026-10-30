"""Automatic continuation prepares requirements, never prepares runnable commands."""

import importlib
import json
import runpy
from dataclasses import FrozenInstanceError, asdict, replace

import pytest


def planning():
    assert importlib.util.find_spec("compatibility.guest_build_receipt.planning") is not None
    return importlib.import_module("compatibility.guest_build_receipt.planning")


def test_current_reference_is_not_current_observed_or_qualified_input():
    d = planning().current_reference_plan()
    assert d.inputs.reference_revision == "bbec08f84d0d08b17075663643ddeba6db46d977"
    assert (
        d.inputs.reference_snapshot_digest
        == "6f854b3c1e6bb1f216092c87f983c553a7ff5419897415f56a007d74e06b5eb7"
    )
    assert d.evidence_origin == "REFERENCE_ONLY"
    assert d.overall_status == "BLOCKED"
    assert d.missing_registrations == ("executor", "producer", "input_seal", "promotion")
    assert d.unverified_registrations == ()
    assert d.current_observation is None and d.prepared_command is None
    with pytest.raises(FrozenInstanceError):
        d.inputs.executor_registration = "a" * 64


def test_all_digest_shaped_registrations_are_references_not_trust_or_authority():
    p = planning()
    inputs = replace(
        p.current_reference_plan().inputs,
        **{
            name + "_registration": "a" * 64
            for name in ("executor", "producer", "input_seal", "promotion")
        },
    )
    d = p.assess_preparation(inputs)
    assert d.missing_registrations == ()
    assert d.unverified_registrations == ("executor", "producer", "input_seal", "promotion")
    assert d.overall_status == "BLOCKED" and "QUALIFIED_EVIDENCE_UNAVAILABLE" in d.blockers
    for name in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert asdict(d)[name] is False
    assert d.successful_prohibited_handles is None and d.successful_prohibited_effects is None
    with pytest.raises(ValueError):
        replace(d, build_execution_allowed=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_revision", "main"),
        ("reference_revision", "A" * 40),
        ("reference_snapshot_digest", False),
        ("executor_registration", "approved"),
        ("producer_registration", 0),
        ("input_seal_registration", ""),
        ("promotion_registration", "file:///seal"),
    ],
)
def test_preparation_references_require_exact_digest_types_without_coercion(field, value):
    with pytest.raises(ValueError):
        replace(planning().current_reference_plan().inputs, **{field: value})


def test_planning_rejects_arbitrary_objects_not_a_typed_registration_context():
    with pytest.raises(ValueError):
        planning().assess_preparation({})


def test_cli_is_closed_default_and_explicit_describe_only(capsys, monkeypatch):
    planning()
    assert importlib.util.find_spec("compatibility.guest_build_receipt.host_main") is not None
    cli = importlib.import_module("compatibility.guest_build_receipt.host_main")
    for args in ([], ["--execute"], ["--describe-plan", "--run"], ["/bin/cc"]):
        assert cli.main(args) == 2
        assert capsys.readouterr().out == ""
    monkeypatch.setattr("sys.argv", ["guest-receipt", "--describe-plan"])
    assert cli.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["evidence_origin"] == "REFERENCE_ONLY" and report["overall_status"] == "BLOCKED"
    assert report["prepared_command"] is None


def test_planning_and_default_cli_do_not_probe_files_environment_or_execute(monkeypatch):
    p = planning()
    cli = importlib.import_module("compatibility.guest_build_receipt.host_main")

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected IO or execution")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr("os.getenv", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    assert p.current_reference_plan().overall_status == "BLOCKED"
    assert cli.main([]) == 2


@pytest.mark.filterwarnings("ignore:.*found in sys.modules.*:RuntimeWarning")
def test_module_entrypoint_is_also_closed_default(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["guest-receipt"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("compatibility.guest_build_receipt.host_main", run_name="__main__")
    assert error.value.code == 2 and capsys.readouterr().out == ""
