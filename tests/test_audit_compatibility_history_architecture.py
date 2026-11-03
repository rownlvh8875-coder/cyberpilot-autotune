"""HR021/025/026:matching claims cannot acquire I/O or remove old admission blocks."""

import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.audit_compatibility_history import api, complete


def test_fresh_import_is_inert_and_does_not_load_old_core_or_runtime(tmp_path):
    script = """
import sys,os,importlib
sys.dont_write_bytecode=True
def guard(event,args):
 if (event.startswith(('socket.','subprocess.','os.fork','os.exec','ctypes.'))
     or event in {'os.mkdir','os.remove','os.rename'}):
  raise AssertionError(event)
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  raise AssertionError(event)
sys.addaudithook(guard)
for name in ('contracts','validation'):
 importlib.import_module('tests.audit_compatibility_history.'+name)
for n in sys.modules:
 assert not n.startswith(('cyberpilot_autotune','tests.audit_compatibility.',
                          'tests.audit_compatibility_capture'))
print('INERT_PURE_IMPORT')
"""
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "INERT_PURE_IMPORT" and list(tmp_path.iterdir()) == []


def test_package_uses_only_pure_stdlib_and_sibling_imports():
    root = Path(__file__).resolve().parents[1] / "tests/audit_compatibility_history"
    allowed = {"json", "dataclasses", "hashlib", "typing"}
    for path in root.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert (node.level == 1 and node.module == "contracts") or (
                    node.level == 0 and node.module in allowed
                )


def test_h_record_cannot_override_bad_current_C_or_supply_old_IO():
    from tests.audit_compatibility.contracts import IO_UNAVAILABLE, PERMISSIONS
    from tests.audit_compatibility.validation import assess_compatibility
    from tests.fixtures.audit_compatibility_core import complete as core_vector

    h, policy = complete()
    assert api("validation").assess_record(h, policy).consistency == "STRUCTURAL_RECORD_MATCH"
    v = core_vector(candidate_extra={"unregistered.py": b"not approved"})
    current = assess_compatibility(v.bundle, v.manifest)
    assert current.decision == "REJECTED" and set(IO_UNAVAILABLE) <= set(current.unavailable_checks)
    assert current.permissions == h.permissions == PERMISSIONS
    clean = core_vector()
    assert assess_compatibility(clean.bundle, clean.manifest).decision == "UNAVAILABLE"


def _phase_changes(rows, additions, *, modifications=frozenset(), exact=False):
    seen = set()
    for row in rows:
        parts = row.split("\t")
        assert len(parts) == 2
        status, path = parts
        assert path not in seen
        seen.add(path)
        assert (status == "A" and path in additions) or (status == "M" and path in modifications)
    if exact:
        assert seen == additions


def _registered_preflight_changes(rows):
    # A successor phase,not an enlargement of the frozen synthetic allowlist.
    # Current manifest data cannot grant another path or mutation permission.
    _phase_changes(
        rows,
        {
            ".github/workflows/runner-preflight.yml",
            "tools/actions_runner_preflight.py",
            "tests/test_actions_runner_preflight.py",
            "tests/test_actions_preflight_registration.py",
            "docs/actions_runner_preflight.md",
            "docs/evidence/audit_compatibility/actions-runner-preflight-v1/registration.json",
        },
        modifications={
            ".gitattributes",
            "tests/test_audit_compatibility_history_architecture.py",
        },
    )


def _ci_portability_changes(rows):
    # Separate successor,never a wider allowance for either frozen older range.
    _phase_changes(
        rows,
        {
            "docs/superpowers/specs/2026-11-03-ci-portability-design.md",
            "docs/superpowers/plans/2026-11-03-ci-portability.md",
            "tests/test_audit_compatibility_capture_portability.py",
            "docs/evidence/audit_compatibility/ci-portability-v1/registration.json",
        },
        modifications={
            ".gitattributes",
            "tests/test_audit_compatibility_capture_cohort.py",
            "tests/test_audit_compatibility_capture_git.py",
            "tests/test_audit_compatibility_capture_worktree.py",
            "tests/fixtures/audit_compatibility_capture.py",
            "tests/test_audit_compatibility_capture_architecture.py",
            "tests/test_audit_compatibility_history_architecture.py",
            "tests/test_actions_preflight_registration.py",
        },
    )


def _h1_outcome_changes(rows):
    # A distinct repair ceiling;never broaden a frozen earlier phase.
    _phase_changes(
        rows,
        {
            "docs/superpowers/specs/2026-11-03-h1-outcome-consistency-design.md",
            "docs/superpowers/plans/2026-11-03-h1-outcome-consistency.md",
            "tests/test_h1_outcome_consistency.py",
            "docs/evidence/audit_compatibility/h1-outcome-consistency-v1/registration.json",
        },
        modifications={
            "tests/audit_compatibility_history/validation.py",
            "tests/test_audit_compatibility_history_architecture.py",
            "tests/test_audit_compatibility_capture_portability.py",
            "tests/test_actions_preflight_registration.py",
        },
    )


def _h1_cancellation_changes(rows):
    # New repair boundary; none of the earlier phase ceilings are enlarged.
    _phase_changes(
        rows,
        {
            "docs/superpowers/specs/2026-11-03-h1-cancellation-cleanup-design.md",
            "docs/superpowers/plans/2026-11-03-h1-cancellation-cleanup.md",
            "tests/test_h1_cancellation_cleanup.py",
            "docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json",
        },
        modifications={
            "tests/audit_compatibility_executor/runner.py",
            "tests/audit_compatibility_executor/supervision.py",
            "tests/test_audit_compatibility_history_architecture.py",
            "tests/test_h1_outcome_consistency.py",
            "tests/test_actions_preflight_registration.py",
        },
    )


def test_all_earlier_files_and_guard_bytes_are_preserved():
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"}

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, env=env).decode()

    original = "fa33fbf970adfdcb6b23d35489364158740cc6d9"
    h1 = "61245f6bbf3fdbc3d14ce8c93ff7349234da46f7"
    design = "ac6adf32ab163fa1fe9eaeb635644037c0de8cde"
    synthetic_end = "33d358fdac148fccc7f02c19e24bb35c4b09e417"
    original_paths = set(
        json.loads(
            git(
                "show",
                original + ":docs/evidence/audit_compatibility/historical-design-v1/semantics.json",
            )
        )["future_pure_preparation_paths"]
    )
    profile = json.loads(
        git(
            "show", design + ":docs/evidence/audit_compatibility/executor-profile-v1/semantics.json"
        )
    )
    assert len(original_paths) == 8
    assert len(set(profile["design_paths"])) == 5
    assert len(set(profile["future_synthetic_paths"])) == 10
    _phase_changes(
        git("diff", "--no-renames", "--name-status", original, h1).splitlines(),
        original_paths,
        exact=True,
    )
    _phase_changes(
        git("diff", "--no-renames", "--name-status", h1, design).splitlines(),
        set(profile["design_paths"]),
        exact=True,
    )
    changed = git("diff", "--no-renames", "--name-status", design, synthetic_end).splitlines()
    _phase_changes(
        changed,
        set(profile["future_synthetic_paths"]),
        modifications={"tests/test_audit_compatibility_history_architecture.py"},
    )
    assert {row.split("\t")[1] for row in changed} == set(profile["future_synthetic_paths"]) | {
        "tests/test_audit_compatibility_history_architecture.py"
    }
    registration_end = "ce138c503ff320a2a6956ceff3d8735418b72bcc"
    _registered_preflight_changes(
        git("diff", "--no-renames", "--name-status", synthetic_end, registration_end).splitlines()
    )
    portability_end = "a8b2bf1e6f27a4157212298928a50c8e970babf5"
    _ci_portability_changes(
        git("diff", "--no-renames", "--name-status", registration_end, portability_end).splitlines()
    )
    outcome_end = "209edaa83b398e6204af1097fda4b651807cc815"
    _h1_outcome_changes(
        git("diff", "--no-renames", "--name-status", portability_end, outcome_end).splitlines()
    )
    checkpoint = "db91591637f9e73ecbbb009b6e122443636390a8"
    base = "4b77b31dd23010f2d2b394466d88b04a4a2720e2"
    tree = "c8534fed7baa56ec3754b64774aba2dbbeab85de"
    assert git("rev-parse", base + "^{tree}").strip() == tree
    assert git("rev-parse", checkpoint + "^{tree}").strip() == tree
    frozen = git("diff", "--no-renames", "--name-status", outcome_end, checkpoint).splitlines()
    _h1_cancellation_changes(frozen)
    untracked = [
        "A\t" + path for path in git("ls-files", "--others", "--exclude-standard").splitlines()
    ]
    profile_end = "0ac6e3519ad7191b036eb777b4317174121851bb"
    assert git("rev-parse", profile_end + "^{tree}").strip() == (
        "974837bb773c5e18b90f01e9ce7491769a3d4b2a"
    )
    profile = git("diff", "--no-renames", "--name-status", base, profile_end).splitlines()
    old_combined = git(
        "diff", "--no-renames", "--name-status", outcome_end, profile_end
    ).splitlines()
    _preparation_profile_composed_changes(frozen, profile, old_combined)
    profile_current = git("diff", "--no-renames", "--name-status", base).splitlines() + untracked
    successor = git("diff", "--no-renames", "--name-status", outcome_end).splitlines() + untracked
    new = git("diff", "--no-renames", "--name-status", profile_end).splitlines() + untracked
    mapping_scope = importlib.import_module("tests.test_preflight_profile_mapping_scope")
    mapping_scope.assert_mapping_composition(frozen, profile, new, profile_current, successor)
    module = importlib.import_module("tests.audit_compatibility.contracts")
    assert module.IO_UNAVAILABLE == (
        "CURRENT_INDEX_WORKTREE",
        "EFFECTIVE_ATTRIBUTES",
        "HISTORICAL_REPLAY",
        "SOURCE_CAPTURE_ATOMICITY",
    )


@pytest.mark.parametrize(
    "rows",
    [
        ["M\ta.py"],
        ["D\ta.py"],
        ["A\tunknown.py"],
        ["A\ta.py", "A\ta.py"],
        ["R100\ta.py\tb.py"],
        ["A\t../a.py"],
        ["A\tdir/a.py"],
        ["A a.py"],
    ],
)
def test_phase_guard_rejects_edits_deletions_aliases_and_unknown_additions(rows):
    check = globals().get("_phase_changes")
    assert callable(check), "phase-specific path guard not implemented"
    with pytest.raises(AssertionError):
        check(rows, {"a.py"})


def test_phase_guard_requires_exact_historical_sets_without_widening_current_scope():
    check = globals().get("_phase_changes")
    assert callable(check), "phase-specific path guard not implemented"
    check(["A\ta.py"], {"a.py"}, exact=True)
    with pytest.raises(AssertionError):
        check([], {"a.py"}, exact=True)
    check(["M\tguard.py", "A\ta.py"], {"a.py"}, modifications={"guard.py"})
    with pytest.raises(AssertionError):
        check(["M\tother.py"], {"a.py"}, modifications={"guard.py"})


def _preparation_profile_changes(rows: list[str]) -> None:
    _phase_changes(
        rows,
        {
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
        },
        modifications={
            "tests/test_audit_compatibility_history_architecture.py",
            "tests/test_h1_cancellation_cleanup.py",
        },
    )


def _preparation_profile_composed_changes(
    frozen_rows: list[str], new_rows: list[str], current_rows: list[str]
) -> None:
    expected = {
        "A\tdocs/superpowers/specs/2026-11-03-h1-cancellation-cleanup-design.md",
        "A\tdocs/superpowers/plans/2026-11-03-h1-cancellation-cleanup.md",
        "A\ttests/test_h1_cancellation_cleanup.py",
        "A\tdocs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json",
        "M\ttests/audit_compatibility_executor/runner.py",
        "M\ttests/audit_compatibility_executor/supervision.py",
        "M\ttests/test_audit_compatibility_history_architecture.py",
        "M\ttests/test_h1_outcome_consistency.py",
        "M\ttests/test_actions_preflight_registration.py",
    }
    assert len(frozen_rows) == len(expected) and set(frozen_rows) == expected
    _h1_cancellation_changes(frozen_rows)
    _preparation_profile_changes(new_rows)
    composed = {row.split("\t")[1]: row.split("\t")[0] for row in frozen_rows}
    for row in new_rows:
        status, path = row.split("\t")
        if path in composed:
            assert status == "M"
        else:
            composed[path] = status
    assert len(current_rows) == len(composed)
    assert set(current_rows) == {status + "\t" + path for path, status in composed.items()}
