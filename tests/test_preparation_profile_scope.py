"""A successor cannot erase a frozen change or self-authorize new paths."""

import importlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "4b77b31dd23010f2d2b394466d88b04a4a2720e2"
CHECKPOINT = "db91591637f9e73ecbbb009b6e122443636390a8"
START = "209edaa83b398e6204af1097fda4b651807cc815"
ADDITIONS = {
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
}
MODIFICATIONS = {
    "tests/test_audit_compatibility_history_architecture.py",
    "tests/test_h1_cancellation_cleanup.py",
}


def checks():
    module = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    single = getattr(module, "_preparation_profile_changes", None)
    composed = getattr(module, "_preparation_profile_composed_changes", None)
    assert callable(single) and callable(composed), "closed preparation successor missing"
    return module, single, composed


def test_closed_successor_rejects_unknown_status_alias_duplicate_and_manifest_expansion():
    _, single, _ = checks()
    rows = ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    single(rows)
    single([])  # Construction subsets are allowed; final inventory is checked separately.
    for bad in (
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttests/audit_compatibility_executor/runner.py"],
        ["A\tdocs/UNKNOWN.md"],
        ["D\ttests/test_preparation_profile_scope.py"],
        ["R100\ta.py\ttests/test_preparation_profile_scope.py"],
        ["A\t../tests/test_preparation_profile_scope.py"],
        ["A\ttests//test_preparation_profile_scope.py"],
        ["A\ttests/test_preparation_profile_scope.py"] * 2,
        ["M\ttests/test_preparation_profile_scope.py"],
    ):
        with pytest.raises(AssertionError):
            single(bad)


def test_composition_preserves_frozen_status_and_requires_every_current_row():
    _, _, composed = checks()
    frozen = (
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-status", START, CHECKPOINT], cwd=ROOT
        )
        .decode()
        .splitlines()
    )
    new = ["M\ttests/test_h1_cancellation_cleanup.py", "A\ttests/test_preparation_profile_scope.py"]
    combined = frozen + new[1:]
    composed(frozen, new, combined)  # Old A followed by M is still A.
    for old, fresh, current in (
        (frozen[:-1], new, combined),
        (frozen, new, combined[:-1]),
        (frozen, new, combined + [combined[0]]),
        (frozen, new, combined + ["A\tUNKNOWN.py"]),
        (frozen, ["M\ttests/audit_compatibility_executor/runner.py"], combined),
        (frozen, new, [r.replace("A\ttests/test_h1", "M\ttests/test_h1") for r in combined]),
    ):
        with pytest.raises(AssertionError):
            composed(old, fresh, current)


@pytest.mark.parametrize("tamper", ["frozen", "new", "current", "untracked", "tree"])
def test_frozen_new_current_untracked_tampering_all_fail(monkeypatch, tamper):
    module, _, _ = checks()
    real = module.subprocess.check_output

    def changed(args, **kwargs):
        suffix = args[1:]
        if tamper == "frozen" and suffix == [
            "diff",
            "--no-renames",
            "--name-status",
            START,
            CHECKPOINT,
        ]:
            return b""
        if tamper == "new" and suffix == ["diff", "--no-renames", "--name-status", BASE]:
            return b"M\ttests/audit_compatibility_executor/runner.py\n"
        if tamper == "current" and suffix == ["diff", "--no-renames", "--name-status", START]:
            return b""
        if tamper == "tree" and suffix == ["rev-parse", BASE + "^{tree}"]:
            return b"0" * 40 + b"\n"
        raw = real(args, **kwargs)
        if tamper == "untracked" and suffix == ["ls-files", "--others", "--exclude-standard"]:
            raw += b"UNREGISTERED.py\n"
        return raw

    monkeypatch.setattr(module.subprocess, "check_output", changed)
    with pytest.raises(AssertionError):
        module.test_all_earlier_files_and_guard_bytes_are_preserved()
