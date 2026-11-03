"""Synthetic CI infrastructure;never runtime or actual host qualification."""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.audit_compatibility_capture import api, git, prepared, request
from tests.fixtures.audit_compatibility_capture import (
    isolated_capture_config as isolated_capture_config,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = "ce138c503ff320a2a6956ceff3d8735418b72bcc"
FOLLOWUP_BASE = "3fc532d5c2634e716401701278cb45b49dbea3ac"
FOLLOWUP_MODIFICATIONS = {
    "tests/test_audit_compatibility_capture_portability.py",
    "docs/superpowers/specs/2026-11-03-ci-portability-design.md",
    "docs/superpowers/plans/2026-11-03-ci-portability.md",
}
ADDITIONS = {
    "docs/superpowers/specs/2026-11-03-ci-portability-design.md",
    "docs/superpowers/plans/2026-11-03-ci-portability.md",
    "tests/test_audit_compatibility_capture_portability.py",
    "docs/evidence/audit_compatibility/ci-portability-v1/registration.json",
}
MODIFICATIONS = {
    ".gitattributes",
    "tests/test_audit_compatibility_capture_cohort.py",
    "tests/test_audit_compatibility_capture_git.py",
    "tests/test_audit_compatibility_capture_worktree.py",
    "tests/fixtures/audit_compatibility_capture.py",
    "tests/test_audit_compatibility_capture_architecture.py",
    "tests/test_audit_compatibility_history_architecture.py",
    "tests/test_actions_preflight_registration.py",
}


def source_git(*args):
    """Trusted test metadata calls retain the actual checkout's Git configuration."""
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0"},
        stderr=subprocess.PIPE,
    )


def scope():
    fixtures = importlib.import_module("tests.fixtures.audit_compatibility_capture")
    function = getattr(fixtures, "synthetic_config_scope", None)
    assert callable(function), "test-only restoring scope missing"
    return function


def test_synthetic_capture_declares_private_config_sources(tmp_path):
    root = prepared(tmp_path)
    sources = request(root).layout.control_roots
    assert len(sources) == 3 and len(set(sources)) == 3
    assert all(Path(p).is_relative_to(tmp_path.parent) for p in sources)
    assert all(Path(p).read_bytes() == b"" for p in sources)


def test_synthetic_git_does_not_consume_ambient_global_config(tmp_path, monkeypatch):
    ambient = tmp_path / "ambient.config"
    ambient.write_bytes(b"[core]\neditor = SYNTHETIC_AMBIENT_EDITOR\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(ambient))
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "--quiet")
    with pytest.raises(subprocess.CalledProcessError):
        git(root, "config", "--get", "core.editor")
    assert ambient.read_bytes() == b"[core]\neditor = SYNTHETIC_AMBIENT_EDITOR\n"


def test_frozen_core_bytes_survive_fresh_autocrlf_checkout(tmp_path):
    root, checkout = tmp_path / "repository", tmp_path / "checkout"
    root.mkdir()
    checkout.mkdir()
    git(root, "init", "--quiet")
    git(root, "config", "core.autocrlf", "false")
    (root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    expected = {}
    for source in sorted((ROOT / "tests/audit_compatibility").glob("*.py")):
        relative = source.relative_to(ROOT)
        data = source_git("show", "c71e573d3c42c3122c07338cc34135e4aa8efa52:" + relative.as_posix())
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        expected[relative] = data
    assert expected
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "TEST_ONLY",
    )
    git(
        root,
        "-c",
        "core.autocrlf=true",
        "checkout-index",
        "--all",
        "--prefix=" + checkout.as_posix() + "/",
    )
    assert {p: (checkout / p).read_bytes() for p in expected} == expected


def test_checkout_policy_only_adds_the_frozen_core_rule():
    previous = source_git("show", BASE + ":.gitattributes").decode()
    # The policy is a text file;the K1 source comparison above remains raw bytes.
    assert (ROOT / ".gitattributes").read_text() == (
        previous + "tests/audit_compatibility/*.py text eol=lf\n"
    )


@pytest.mark.parametrize("raise_inside", [False, True])
def test_synthetic_scope_restores_discovery_even_on_exception(tmp_path, raise_inside):
    reader = api("worktree_reader")
    original = reader.config_candidates
    paths = tuple(str(tmp_path / name) for name in ("system", "user", "xdg"))
    try:
        with scope()(paths):
            assert reader.config_candidates(None) == paths
            if raise_inside:
                raise RuntimeError("TEST_ONLY")
    except RuntimeError:
        assert raise_inside
    assert reader.config_candidates is original


@pytest.mark.parametrize("source", [0, 1, 2])
@pytest.mark.parametrize("helper", ["filter", "fsmonitor", "merge"])
def test_declared_synthetic_helper_still_rejects_before_git(tmp_path, monkeypatch, source, helper):
    root = prepared(tmp_path)
    req = request(root)
    # A failing isolation implementation must never turn this regression into a host writer.
    assert all(
        Path(p).resolve(strict=True).is_relative_to(tmp_path.parent.resolve())
        and not Path(p).is_symlink()
        for p in req.layout.control_roots
    )
    marker = tmp_path / "MUST_NOT_EXECUTE"
    key = {
        "filter": '[filter "evil"]\nclean',
        "fsmonitor": "[core]\nfsmonitor",
        "merge": '[merge "evil"]\ndriver',
    }[helper]
    Path(req.layout.control_roots[source]).write_bytes(f"{key} = touch {marker}\n".encode())

    def forbidden(*args, **kwargs):
        raise AssertionError("rejected helper launched a child")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    result = api("capture").capture_checkout(req)
    assert result.consistency == "REJECTED" and "CUSTOM_HELPER" in result.errors
    assert not marker.exists() and not any(v for _, v in result.permissions)


def test_fresh_nonfixture_process_keeps_actual_config_discovery(tmp_path):
    script = """
import os
from tests.audit_compatibility_capture.worktree_reader import config_candidates
from tests.audit_compatibility_capture.contracts import CaptureFault,absolute
user=os.environ.get('HOME');xdg=os.environ.get('XDG_CONFIG_HOME',(user or '')+'/.config')
if user is not None and absolute(user) and absolute(xdg):
 assert config_candidates(None)==('/etc/gitconfig',user+'/.gitconfig',xdg+'/git/config')
else:
 try: config_candidates(None)
 except CaptureFault as error: assert error.reason=='CONFIG_SCOPE'
 else: raise AssertionError('unsupported actual scope accepted')
print('ACTUAL_DISCOVERY_UNCHANGED')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ACTUAL_DISCOVERY_UNCHANGED"


def test_repair_inventory_is_exact_and_not_manifest_authority():
    rows = source_git("diff", "--no-renames", "--name-status", BASE).decode().splitlines()
    rows += [
        "A\t" + p
        for p in source_git("ls-files", "--others", "--exclude-standard").decode().splitlines()
    ]
    assert set(rows) == {"A\t" + p for p in ADDITIONS} | {"M\t" + p for p in MODIFICATIONS}
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    check = getattr(m, "_ci_portability_changes", None)
    assert callable(check), "separate repair scope missing"
    check(rows)
    path = ROOT / "docs/evidence/audit_compatibility/ci-portability-v1/registration.json"
    assert path.is_file(), "descriptive repair inventory missing"
    value = json.loads(path.read_text())
    old = json.loads(
        source_git(
            "show",
            BASE
            + ":docs/evidence/audit_compatibility/actions-runner-preflight-v1/registration.json",
        )
    )
    assert value["base"] == BASE
    assert set(value["new_paths"]) == ADDITIONS and set(value["modified_paths"]) == MODIFICATIONS
    assert value["status"] == "BLOCKED" and value["permissions"] == old["permissions"]
    assert set(old["retained_blockers"]) <= set(value["retained_blockers"])


@pytest.mark.parametrize(
    "rows",
    [
        ["M\tsrc/cyberpilot_autotune/__init__.py"],
        ["M\ttests/audit_compatibility_capture/worktree_reader.py"],
        ["M\t.github/workflows/ci.yml"],
        ["M\ttools/actions_runner_preflight.py"],
        ["A\tdocs/unknown.md"],
        ["D\t.gitattributes"],
        ["R100\t.gitattributes\tother"],
        ["M\t.gitattributes", "M\t.gitattributes"],
        ["A\t../tests/test_audit_compatibility_capture_portability.py"],
    ],
)
def test_repair_scope_rejects_unknown_paths_and_statuses(rows):
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    check = getattr(m, "_ci_portability_changes", None)
    assert callable(check), "separate repair scope missing"
    with pytest.raises(AssertionError):
        check(rows)


def test_frozen_ranges_and_runtime_bytes_are_not_changed():
    for prefix in (
        "src",
        "tests/audit_compatibility",
        "tests/audit_compatibility_capture",
        "tests/audit_compatibility_history",
        "tests/audit_compatibility_executor",
        ".github/workflows",
        "tools/actions_runner_preflight.py",
        "tests/conftest.py",
    ):
        assert source_git("diff", "--name-only", BASE, "--", prefix) == b""
    guard = ROOT / "tests/test_audit_compatibility_history_architecture.py"
    m = importlib.import_module("tests.test_audit_compatibility_history_architecture")
    old = source_git("show", BASE + ":" + guard.relative_to(ROOT).as_posix()).decode()
    import ast

    for node in ast.parse(old).body:
        if isinstance(node, ast.FunctionDef) and node.name in (
            "_phase_changes",
            "_registered_preflight_changes",
        ):
            current = next(
                n
                for n in ast.parse(guard.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == node.name
            )
            assert ast.dump(node) == ast.dump(current)
    m.test_all_earlier_files_and_guard_bytes_are_preserved()


def test_source_checkout_normalization_preserves_real_change_detection(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    sample = root / "sample.py"
    sample.write_bytes(b"value = 1\n")
    git(root, "init", "--quiet")
    git(root, "-c", "core.autocrlf=false", "add", "sample.py")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "SYNTHETIC_CHECKOUT_ONLY",
    )
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    # Git must materialize a NEW file;checkout-index may retain an existing LF file.
    sample.rename(tmp_path / "original-lf.saved")
    git(root, "-c", "core.autocrlf=true", "checkout-index", "--all", "--force")
    assert sample.read_bytes() == b"value = 1\r\n"
    ambient = tmp_path / "checkout.config"
    ambient.write_bytes(b"[core]\nautocrlf = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(ambient))
    monkeypatch.setattr(sys.modules[__name__], "ROOT", root)
    # Before the fix this is the exact helper used by the real source consumers.
    inspect = globals().get("source_git", lambda *args: git(ROOT, *args))
    assert git(root, "diff", "--no-ext-diff", "--name-status", revision) == b"M\tsample.py\n"
    assert inspect("diff", "--no-ext-diff", "--name-status", revision) == b""
    assert inspect("show", revision + ":sample.py") == b"value = 1\n"
    sample.write_bytes(b"value = 2\r\n")
    assert inspect("diff", "--no-ext-diff", "--name-status", revision) == b"M\tsample.py\n"
    (root / "unexpected.txt").write_bytes(b"untracked\n")
    assert inspect("ls-files", "--others", "--exclude-standard") == b"unexpected.txt\n"
    assert ambient.read_bytes() == b"[core]\nautocrlf = true\n"


@pytest.mark.parametrize(
    "consumer",
    [
        "test_frozen_core_bytes_survive_fresh_autocrlf_checkout",
        "test_checkout_policy_only_adds_the_frozen_core_rule",
        "test_repair_inventory_is_exact_and_not_manifest_authority",
        "test_frozen_ranges_and_runtime_bytes_are_not_changed",
    ],
)
def test_real_source_consumers_do_not_use_neutral_setup_git(tmp_path, monkeypatch, consumer):
    setup_git = git

    def setup_only(root, *args, **kwargs):
        assert Path(root).resolve() != ROOT.resolve(), "source metadata used neutral setup Git"
        return setup_git(root, *args, **kwargs)

    monkeypatch.setattr(sys.modules[__name__], "git", setup_only)
    if consumer == "test_frozen_core_bytes_survive_fresh_autocrlf_checkout":
        globals()[consumer](tmp_path)
    else:
        globals()[consumer]()


def test_normalization_followup_has_only_registered_modifications():
    inspect = globals().get("source_git", lambda *args: git(ROOT, *args))
    rows = inspect("diff", "--no-renames", "--name-status", FOLLOWUP_BASE).decode().splitlines()
    rows += [
        "A\t" + p
        for p in inspect("ls-files", "--others", "--exclude-standard").decode().splitlines()
    ]
    assert sorted(rows) == sorted("M\t" + p for p in FOLLOWUP_MODIFICATIONS)
