"""Closed successor phase;no historical allowlist or execution-authority expansion."""

import ast
import importlib
import json
import os
import stat
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "33d358fdac148fccc7f02c19e24bb35c4b09e417"
DESIGN = "ac6adf32ab163fa1fe9eaeb635644037c0de8cde"
GUARD = "tests/test_audit_compatibility_history_architecture.py"
REGISTRATION = "docs/evidence/audit_compatibility/actions-runner-preflight-v1/registration.json"
ADDITIONS = {
    ".github/workflows/runner-preflight.yml",
    "tools/actions_runner_preflight.py",
    "tests/test_actions_runner_preflight.py",
    "tests/test_actions_preflight_registration.py",
    "docs/actions_runner_preflight.md",
    REGISTRATION,
}
MODIFICATIONS = {GUARD, ".gitattributes"}


def git(*args):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"},
    )


def scope():
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    check = getattr(m, "_registered_preflight_changes", None)
    assert callable(check), "scoped successor phase guard not implemented"
    return check


def test_registered_phase_accepts_only_explicit_successor_paths():
    scope()(["A\t" + p for p in sorted(ADDITIONS)] + ["M\t" + p for p in sorted(MODIFICATIONS)])


@pytest.mark.parametrize(
    "rows",
    [
        ["A\tdocs/unregistered.md"],
        ["M\ttests/audit_compatibility_executor/runner.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\ttools/actions_runner_preflight.py"],
        ["D\ttools/actions_runner_preflight.py"],
        ["R100\ta.py\ttools/actions_runner_preflight.py"],
        ["A\ttools/actions_runner_preflight.py", "A\ttools/actions_runner_preflight.py"],
        ["A\t../tools/actions_runner_preflight.py"],
        ["A\ttools//actions_runner_preflight.py"],
        ["A tools/actions_runner_preflight.py"],
        ["M\t.gitattributes", "M\t.gitattributes"],
    ],
)
def test_registered_phase_rejects_scope_status_and_alias_expansion(rows):
    check = scope()
    with pytest.raises(AssertionError):
        check(rows)


def test_old_nonconsumer_functions_and_top_level_semantics_stay_exact():
    old = git("show", BASE + ":" + GUARD).decode()
    new = (ROOT / GUARD).read_text()
    before, after = ast.parse(old), ast.parse(new)
    functions = {
        n.name: ast.get_source_segment(new, n) for n in after.body if isinstance(n, ast.FunctionDef)
    }
    for node in before.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name != "test_all_earlier_files_and_guard_bytes_are_preserved"
        ):
            assert functions[node.name] == ast.get_source_segment(old, node)
    assert [ast.dump(n) for n in before.body if not isinstance(n, ast.FunctionDef)] == [
        ast.dump(n) for n in after.body if not isinstance(n, ast.FunctionDef)
    ]


def test_registration_does_not_authorize_itself_or_execution():
    path = ROOT / REGISTRATION
    assert path.is_file(), "successor semantic registration missing"
    value = json.loads(path.read_text())
    assert value["schema"] == "actions-runner-preflight-registration-v1"
    assert value["base"] == value["synthetic_phase_end"] == BASE
    assert set(value["new_paths"]) == ADDITIONS and len(value["new_paths"]) == 6
    assert set(value["modified_paths"]) == MODIFICATIONS and len(value["modified_paths"]) == 2
    assert (
        value["prepared_manifest_sha256"]
        == "2b7ffd5d32014d74a24e442f1b14b6a81cd73b1a8c66b7deb069d80064fa7f60"
    )
    assert (
        value["collector_sha256"]
        == "3b3b99e4fb1dab67b2972c06cc432ed80f6b38c3f48c3aa69a4d13517750429e"
    )
    assert (
        value["workflow_sha256"]
        == "40781c65ecb75467cdcd1204902e72869249ad018c7c4bc51e11996830572b1d"
    )
    assert (
        value["prepared_workflow_sha256"]
        == "36bb270a74d831637c44f6cb9eb73e431366af127c2de61461797c58be0e668f"
    )
    assert value["workflow_normalization"] == "REMOVE_ONE_FINAL_EMPTY_LINE_ONLY"
    assert value["global_status"] == "BLOCKED"
    assert value["local_registration_only"] is True and value["content_identity_only"] is True
    assert value["github_registered"] is value["github_execution_observed"] is False
    assert value["permissions"] == dict.fromkeys(
        (
            "build_execution_allowed",
            "promotion_authorized",
            "runtime_qualified",
            "device_class_qualified",
            "policy_adopted",
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
        ),
        False,
    )


def test_new_phase_inventory_and_plain_files_are_exact():
    rows = git("diff", "--no-renames", "--name-status", BASE).decode().splitlines()
    rows += [
        "A\t" + p for p in git("ls-files", "--others", "--exclude-standard").decode().splitlines()
    ]
    assert sorted(rows) == sorted(
        ["A\t" + p for p in ADDITIONS] + ["M\t" + p for p in MODIFICATIONS]
    )
    for path in ADDITIONS:
        assert stat.S_ISREG((ROOT / path).lstat().st_mode)
    for line in git("ls-files", "--stage", "--", *sorted(ADDITIONS)).decode().splitlines():
        assert line.split()[0] == "100644"


def test_frozen_source_and_workflow_have_exact_lf_identities():
    for path, digest in (
        (
            "tools/actions_runner_preflight.py",
            "3b3b99e4fb1dab67b2972c06cc432ed80f6b38c3f48c3aa69a4d13517750429e",
        ),
        (
            ".github/workflows/runner-preflight.yml",
            "40781c65ecb75467cdcd1204902e72869249ad018c7c4bc51e11996830572b1d",
        ),
    ):
        assert (ROOT / path).is_file(), "frozen prepared asset not adopted"
        assert sha256((ROOT / path).read_bytes()).hexdigest() == digest
        assert git("check-attr", "text", "eol", "--", path).decode().splitlines() == [
            path + ": text: set",
            path + ": eol: lf",
        ]
    # The wrapper normalization is exactly reversible to the prepared bytes.
    assert (
        sha256((ROOT / ".github/workflows/runner-preflight.yml").read_bytes() + b"\n").hexdigest()
        == "36bb270a74d831637c44f6cb9eb73e431366af127c2de61461797c58be0e668f"
    )


def test_attributes_only_append_two_nonoverlapping_frozen_paths():
    old = git("show", BASE + ":.gitattributes").decode()
    assert (ROOT / ".gitattributes").read_text() == old + (
        "tools/actions_runner_preflight.py text eol=lf\n"
        ".github/workflows/runner-preflight.yml text eol=lf\n"
    )


@pytest.mark.parametrize("tamper", ["frozen", "untracked"])
def test_real_consumer_rejects_frozen_or_untracked_scope_tampering(monkeypatch, tamper):
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    real = m.subprocess.check_output
    calls = []

    def changed(args, **kwargs):
        calls.append(tuple(args[1:]))
        if tamper == "frozen" and args[1:] == [
            "diff",
            "--no-renames",
            "--name-status",
            DESIGN,
            BASE,
        ]:
            return b"M\tsrc/cyberpilot_autotune/__init__.py\n"
        raw = real(args, **kwargs)
        if tamper == "untracked" and args[1:] == ["ls-files", "--others", "--exclude-standard"]:
            raw += b"unregistered-control.py\n"
        return raw

    monkeypatch.setattr(m.subprocess, "check_output", changed)
    with pytest.raises(AssertionError):
        m.test_all_earlier_files_and_guard_bytes_are_preserved()
    if tamper == "frozen":
        assert ("diff", "--no-renames", "--name-status", DESIGN, BASE) in calls


def test_real_consumer_checks_all_legacy_ranges_and_literal_checkpoint(monkeypatch):
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    real = m.subprocess.check_output
    calls = []

    def capture(args, **kwargs):
        calls.append(tuple(args[1:]))
        return real(args, **kwargs)

    monkeypatch.setattr(m.subprocess, "check_output", capture)
    m.test_all_earlier_files_and_guard_bytes_are_preserved()
    for start, end in (
        ("fa33fbf970adfdcb6b23d35489364158740cc6d9", "61245f6bbf3fdbc3d14ce8c93ff7349234da46f7"),
        ("61245f6bbf3fdbc3d14ce8c93ff7349234da46f7", DESIGN),
        (DESIGN, BASE),
    ):
        assert ("diff", "--no-renames", "--name-status", start, end) in calls
    assert ("diff", "--no-renames", "--name-status", BASE) in calls
