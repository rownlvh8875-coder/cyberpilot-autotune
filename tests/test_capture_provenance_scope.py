"""Closed successor;frozen and live tamper checks remain independent."""

import importlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "7422a868a5802ab49b496429448795e88c4de074"
PROFILE_END = "0ac6e3519ad7191b036eb777b4317174121851bb"
PROFILE_BASE = "4b77b31dd23010f2d2b394466d88b04a4a2720e2"
REPAIR_START = "209edaa83b398e6204af1097fda4b651807cc815"
REPAIR_END = "db91591637f9e73ecbbb009b6e122443636390a8"
ADDITIONS = frozenset(
    (
        "tests/audit_capture_provenance/__init__.py",
        "tests/audit_capture_provenance/contracts.py",
        "tests/audit_capture_provenance/validation.py",
        "tests/fixtures/capture_provenance.py",
        "tests/test_capture_provenance.py",
        "tests/test_capture_provenance_architecture.py",
        "tests/test_capture_provenance_scope.py",
        "docs/evidence/audit_compatibility/capture-provenance-v1/registration.json",
        "docs/superpowers/specs/2026-11-04-capture-provenance.md",
        "docs/superpowers/plans/2026-11-04-capture-provenance.md",
    )
)
MODIFICATIONS = frozenset(
    (
        "tests/test_audit_compatibility_history_architecture.py",
        "tests/test_preflight_profile_mapping_architecture.py",
    )
)

MAPPING_ADDITIONS = {
    "tests/audit_preflight_profile_mapping/__init__.py",
    "tests/audit_preflight_profile_mapping/contracts.py",
    "tests/audit_preflight_profile_mapping/mapping.py",
    "tests/fixtures/preflight_profile_mapping.py",
    "tests/test_preflight_profile_mapping.py",
    "tests/test_preflight_profile_mapping_architecture.py",
    "tests/test_preflight_profile_mapping_scope.py",
    "docs/evidence/audit_compatibility/preflight-profile-mapping-v1/registration.json",
    "docs/superpowers/specs/2026-11-04-preflight-profile-mapping.md",
    "docs/superpowers/plans/2026-11-04-preflight-profile-mapping.md",
}

MAPPING_MODIFICATIONS = {
    "tests/test_audit_compatibility_history_architecture.py",
    "tests/test_preparation_profile_architecture.py",
}

PROFILE_ADDITIONS = frozenset(
    (
        "tests/audit_preparation_profile/__init__.py",
        "tests/audit_preparation_profile/contracts.py",
        "tests/audit_preparation_profile/wire.py",
        "tests/audit_preparation_profile/validation.py",
        "tests/fixtures/preparation_profile.py",
        "tests/test_preparation_profile_values.py",
        "tests/test_preparation_profile_wire.py",
        "tests/test_preparation_profile_validation.py",
        "tests/test_preparation_profile_adversarial.py",
        "tests/test_preparation_profile_architecture.py",
        "tests/test_preparation_profile_scope.py",
        "docs/evidence/audit_compatibility/preparation-profile-v1/registration.json",
        "docs/superpowers/specs/2026-11-04-preparation-profile-contract.md",
        "docs/superpowers/plans/2026-11-04-preparation-profile-contract.md",
    )
)

PROFILE_MODIFICATIONS = frozenset(
    (
        "tests/test_audit_compatibility_history_architecture.py",
        "tests/test_h1_cancellation_cleanup.py",
    )
)

REPAIR_ADDITIONS = frozenset(
    (
        "docs/superpowers/specs/2026-11-03-h1-cancellation-cleanup-design.md",
        "docs/superpowers/plans/2026-11-03-h1-cancellation-cleanup.md",
        "tests/test_h1_cancellation_cleanup.py",
        "docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json",
    )
)

REPAIR_MODIFICATIONS = frozenset(
    (
        "tests/audit_compatibility_executor/runner.py",
        "tests/audit_compatibility_executor/supervision.py",
        "tests/test_audit_compatibility_history_architecture.py",
        "tests/test_h1_outcome_consistency.py",
        "tests/test_actions_preflight_registration.py",
    )
)


def _closed(rows, additions, modifications, *, exact=False):
    assert type(rows) is list
    seen = set()
    for row in rows:
        assert type(row) is str
        fields = row.split("\t")
        assert len(fields) == 2
        status, path = fields
        assert path not in seen
        seen.add(path)
        assert (status == "A" and path in additions) or (status == "M" and path in modifications)
    if exact:
        assert set(rows) == {"A\t" + p for p in additions} | {"M\t" + p for p in modifications}


def assert_capture_scope(rows: list[str], *, exact: bool = False) -> None:
    _closed(rows, ADDITIONS, MODIFICATIONS, exact=exact)


def _compose(first, *groups):
    result = {row.split("\t")[1]: row.split("\t")[0] for row in first}
    for group in groups:
        for row in group:
            status, path = row.split("\t")
            if status == "A":
                assert path not in result
                result[path] = status
            else:
                assert path in result
    return {status + "\t" + path for path, status in result.items()}


def assert_capture_composition(
    repair: list[str],
    profile: list[str],
    mapping: list[str],
    new: list[str],
    profile_current: list[str],
    repair_current: list[str],
    mapping_current: list[str],
) -> None:
    _closed(repair, REPAIR_ADDITIONS, REPAIR_MODIFICATIONS, exact=True)
    _closed(profile, PROFILE_ADDITIONS, PROFILE_MODIFICATIONS, exact=True)
    _closed(mapping, MAPPING_ADDITIONS, MAPPING_MODIFICATIONS, exact=True)
    assert_capture_scope(new)
    for actual, expected in (
        (profile_current, _compose(profile, mapping, new)),
        (repair_current, _compose(repair, profile, mapping, new)),
        (mapping_current, _compose(mapping, new)),
    ):
        assert len(actual) == len(expected) and set(actual) == expected


def git_rows(start, end):
    return (
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-status", start, end], cwd=ROOT
        )
        .decode()
        .splitlines()
    )


def checks():
    one = globals().get("assert_capture_scope")
    composed = globals().get("assert_capture_composition")
    assert callable(one) and callable(composed), "closed capture successor missing"
    return one, composed


def test_capture_scope_is_closed():
    one, _ = checks()
    one(["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS], exact=True)
    one([])
    for rows in (
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttests/audit_preparation_profile/contracts.py"],
        ["M\ttests/audit_preflight_profile_mapping/contracts.py"],
        ["M\ttests/audit_compatibility_executor/runner.py"],
        ["A\tUNKNOWN.py"],
        ["D\ttests/test_capture_provenance.py"],
        ["R100\tx\ttests/test_capture_provenance.py"],
        ["A\t../tests/test_capture_provenance.py"],
        ["A\ttests//test_capture_provenance.py"],
        ["A\ttests/test_capture_provenance.py"] * 2,
        ["M\ttests/test_capture_provenance.py"],
        ["A tests/test_capture_provenance.py"],
    ):
        with pytest.raises(AssertionError):
            one(rows)
    with pytest.raises(AssertionError):
        one([], exact=True)


def test_composition_preserves_all_prior_rows():
    _, composed = checks()
    repair = git_rows(REPAIR_START, REPAIR_END)
    profile = git_rows(PROFILE_BASE, PROFILE_END)
    mapping = git_rows(PROFILE_END, BASE)
    pc = git_rows(PROFILE_BASE, BASE)
    rc = git_rows(REPAIR_START, BASE)
    assert list(map(len, (repair, profile, mapping, pc, rc))) == [9, 16, 12, 26, 33]
    addition = "A\ttests/fixtures/capture_provenance.py"
    new = [
        addition,
        "M\ttests/test_preflight_profile_mapping_architecture.py",
        "M\ttests/test_audit_compatibility_history_architecture.py",
    ]
    arguments = [
        repair,
        profile,
        mapping,
        new,
        pc + [addition],
        rc + [addition],
        mapping + [addition],
    ]
    composed(*arguments)
    for index in range(7):
        changed = [list(rows) for rows in arguments]
        changed[index] = changed[index][1:]
        with pytest.raises(AssertionError):
            composed(*changed)
        changed[index] = arguments[index] + [arguments[index][0]]
        with pytest.raises(AssertionError):
            composed(*changed)


@pytest.mark.parametrize(
    "tamper",
    [
        "repair",
        "profile",
        "mapping",
        "profile_current",
        "repair_current",
        "mapping_current",
        "new",
        "untracked",
        "tree",
    ],
)
def test_current_and_frozen_tamper_hooks_are_live(monkeypatch, tamper):
    checks()
    module = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    real = module.subprocess.check_output

    def altered(args, **kwargs):
        suffix = args[1:]
        ranges = {
            "repair": [REPAIR_START, REPAIR_END],
            "profile": [PROFILE_BASE, PROFILE_END],
            "mapping": [PROFILE_END, BASE],
            "profile_current": [PROFILE_BASE],
            "repair_current": [REPAIR_START],
            "mapping_current": [PROFILE_END],
            "new": [BASE],
        }
        if tamper in ranges and suffix == [
            "diff",
            "--no-renames",
            "--name-status",
            *ranges[tamper],
        ]:
            return b"M\tsrc/cyberpilot_autotune/__init__.py\n"
        if tamper == "tree" and suffix == ["rev-parse", BASE + "^{tree}"]:
            return b"0" * 40 + b"\n"
        raw = real(args, **kwargs)
        if tamper == "untracked" and suffix == ["ls-files", "--others", "--exclude-standard"]:
            raw += b"UNKNOWN.py\n"
        return raw

    monkeypatch.setattr(module.subprocess, "check_output", altered)
    with pytest.raises(AssertionError):
        module.test_all_earlier_files_and_guard_bytes_are_preserved()
