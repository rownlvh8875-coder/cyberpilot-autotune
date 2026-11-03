"""A mapping successor cannot enlarge a frozen profile or erase live tamper checks."""

import importlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "0ac6e3519ad7191b036eb777b4317174121851bb"
PROFILE_BASE = "4b77b31dd23010f2d2b394466d88b04a4a2720e2"
REPAIR_START = "209edaa83b398e6204af1097fda4b651807cc815"
REPAIR_END = "db91591637f9e73ecbbb009b6e122443636390a8"
ADDITIONS = {
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
MODIFICATIONS = {
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
        parts = row.split("\t")
        assert len(parts) == 2
        status, path = parts
        assert path not in seen
        seen.add(path)
        assert (status == "A" and path in additions) or (status == "M" and path in modifications)
    if exact:
        assert set(rows) == {"A\t" + p for p in additions} | {"M\t" + p for p in modifications}


def assert_mapping_scope(rows: list[str]) -> None:
    _closed(rows, ADDITIONS, MODIFICATIONS)


def _compose(first, second):
    result = {row.split("\t")[1]: row.split("\t")[0] for row in first}
    for row in second:
        status, path = row.split("\t")
        if status == "M":
            assert path in result
        else:
            assert path not in result
            result[path] = status
    return [status + "\t" + path for path, status in result.items()]


def _same_rows(actual, expected):
    assert len(actual) == len(expected) and set(actual) == set(expected)


def assert_mapping_composition(
    frozen_repair: list[str],
    frozen_profile: list[str],
    new_rows: list[str],
    profile_current: list[str],
    all_current: list[str],
) -> None:
    _closed(frozen_repair, REPAIR_ADDITIONS, REPAIR_MODIFICATIONS, exact=True)
    _closed(frozen_profile, PROFILE_ADDITIONS, PROFILE_MODIFICATIONS, exact=True)
    assert_mapping_scope(new_rows)
    _same_rows(profile_current, _compose(frozen_profile, new_rows))
    _same_rows(all_current, _compose(_compose(frozen_repair, frozen_profile), new_rows))


def checks():
    one = globals().get("assert_mapping_scope")
    composed = globals().get("assert_mapping_composition")
    assert callable(one) and callable(composed), "closed mapping successor missing"
    return one, composed


def git_rows(start, end):
    return (
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-status", start, end], cwd=ROOT
        )
        .decode()
        .splitlines()
    )


def test_closed_mapping_scope_rejects_unknown_status_alias_and_manifest_expansion():
    one, _ = checks()
    one(["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS])
    one([])
    for rows in (
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttests/audit_preparation_profile/contracts.py"],
        ["M\ttests/audit_compatibility_executor/runner.py"],
        ["A\tUNREGISTERED.py"],
        ["D\ttests/test_preflight_profile_mapping.py"],
        ["R100\ta.py\ttests/test_preflight_profile_mapping.py"],
        ["A\t../tests/test_preflight_profile_mapping.py"],
        ["A\ttests//test_preflight_profile_mapping.py"],
        ["A\ttests/test_preflight_profile_mapping.py"] * 2,
        ["M\ttests/test_preflight_profile_mapping.py"],
        ["M tests/test_preparation_profile_architecture.py"],
    ):
        with pytest.raises(AssertionError):
            one(rows)


def test_composition_keeps_frozen_addition_after_modification_and_every_current_row():
    _, composed = checks()
    repair = git_rows(REPAIR_START, REPAIR_END)
    profile = git_rows(PROFILE_BASE, BASE)
    all_old = git_rows(REPAIR_START, BASE)
    assert (len(repair), len(profile), len(all_old)) == (9, 16, 23)
    addition = "A\ttests/test_preflight_profile_mapping_scope.py"
    new = [addition, "M\ttests/test_preparation_profile_architecture.py"]
    composed(repair, profile, new, profile + [addition], all_old + [addition])
    for r, p, n, pc, ac in (
        (repair[:-1], profile, new, profile + [addition], all_old + [addition]),
        (repair, profile[:-1], new, profile + [addition], all_old + [addition]),
        (repair, profile, new, profile, all_old + [addition]),
        (repair, profile, new, profile + [addition], all_old),
        (repair, profile, new, profile + [addition] * 2, all_old + [addition]),
        (repair, profile, ["M\ttools/actions_runner_preflight.py"], profile, all_old),
    ):
        with pytest.raises(AssertionError):
            composed(r, p, n, pc, ac)


@pytest.mark.parametrize(
    "tamper", ["repair", "profile", "new", "profile_current", "all_current", "untracked", "tree"]
)
def test_real_consumer_keeps_every_old_and_new_tamper_hook(monkeypatch, tamper):
    checks()
    module = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    real = module.subprocess.check_output

    def changed(args, **kwargs):
        suffix = args[1:]
        ranges = {
            "repair": [REPAIR_START, REPAIR_END],
            "profile": [PROFILE_BASE, BASE],
            "new": [BASE],
            "profile_current": [PROFILE_BASE],
            "all_current": [REPAIR_START],
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
            raw += b"UNREGISTERED.py\n"
        return raw

    monkeypatch.setattr(module.subprocess, "check_output", changed)
    with pytest.raises(AssertionError):
        module.test_all_earlier_files_and_guard_bytes_are_preserved()
