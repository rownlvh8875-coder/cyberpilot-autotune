"""Untrusted inventory relationships; the fixture generator is not a producer."""

import hashlib
import importlib
import json
import struct
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from tests.test_deny_fd_v2_wire import api, encoded, vector


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"observed": (0,), "outcome": "NO_DENIAL", "case": "DFD02"},
        {"expected": (3,), "causes": (0,), "subject": 3, "case": "DFD03"},
        {"observed": (0, 3, 4), "causes": (3, 4), "case": "DFD04"},
        {"observed": (), "outcome": "UNSUPPORTED_MISSING", "case": "DFD05"},
        {"observed": (3,), "outcome": "UNSUPPORTED_MIXED", "case": "DFD06"},
        {"observed": (0, 2**31 - 1), "causes": (2**31 - 1,)},
        {"expected": (), "observed": (0,), "causes": (0,), "subject": None},
    ],
)
def test_six_fixed_relations_and_zero_maximum_empty_boundaries_remain_blocked(kwargs):
    _, w, v = api()
    decision = v.check_inventory(w.decode(encoded(vector(**kwargs))))
    assert decision.outcome == "WIRE_DIAGNOSTIC_CONSISTENT" and decision.reasons == ()
    assert decision.status == "BLOCKED" and all(value is False for _, value in decision.permissions)


def checked(rows):
    c, _, v = api()
    rows = [row.copy() for row in rows]
    for i, row in enumerate(rows, 1):
        row[0:2] = [i, i * 100]
    return v.check_inventory(
        c.Capture(tuple(c.Event(r[0], r[1], r[2], tuple(r[3:])) for r in rows))
    )


@pytest.mark.parametrize(
    "kind,index,value",
    [
        ("EXPECT", 3, 2),
        ("BIRTH", 3, 2),
        ("BIRTH", 4, 1),
        ("FD", 3, 2),
        ("FD", 5, 2),
        ("FD", 6, 1),
        ("SNAP", 3, 0),
        ("SNAP", 5, 2),
        ("SNAP", 6, 1),
        ("SNAP", 7, 2),
        ("SNAP", 8, 1),
        ("SNAP", 9, 2),
        ("SNAP", 10, 0),
        ("SNAP", 11, 0),
        ("SNAP", 12, 0),
        ("CAUSE", 3, 2),
        ("CAUSE", 4, 0),
        ("CAUSE", 5, 5),
        ("CAUSE", 5, 100),
        ("DENY", 3, 2),
        ("DENY", 5, 2),
        ("DENY", 6, 1),
        ("DENY", 7, 2),
        ("DENY", 10, 0),
        ("REAP", 3, 2),
        ("REAP", 4, 1),
        ("REAP", 6, 0),
        ("END", 3, 2),
        ("END", 4, 1),
    ],
)
def test_wrong_point_source_cohort_count_and_lifecycle_are_rejected(kind, index, value):
    rows = vector()
    next(row for row in rows if row[2] == kind)[index] = value
    assert checked(rows).outcome == "REJECTED"


@pytest.mark.parametrize(
    "kind", ("POLICY", "EXPECT", "BIRTH", "FD", "SNAP", "CAUSE", "DENY", "REAP")
)
def test_missing_required_rows_are_not_invented(kind):
    rows = vector()
    del rows[next(i for i, row in enumerate(rows) if row[2] == kind)]
    assert checked(rows).outcome == "REJECTED"


def test_duplicate_unsorted_and_incomplete_sets_are_rejected():
    rows = vector()
    rows[5][7] = 0
    assert checked(rows).outcome == "REJECTED"
    rows = vector(expected=(3, 0))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(3, 0))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(0, 3, 4), causes=(4, 3))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(0, 3, 4), causes=(3,))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(expected=(0, 0))
    assert checked(rows).outcome == "REJECTED"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"expected": (0, 4)},
        {"observed": (0,), "causes": ()},
        {"outcome": "NO_DENIAL"},
        {"observed": (0,), "outcome": "UNSUPPORTED_MISSING"},
        {"observed": (), "outcome": "UNSUPPORTED_MIXED"},
    ],
)
def test_denial_and_result_labels_must_follow_the_actual_set_relation(kwargs):
    assert checked(vector(**kwargs)).outcome == "REJECTED"


def test_cause_rows_cannot_accompany_a_nondenial_result_or_replace_the_source():
    rows = vector()
    rows[-3] = [0, 0, "RESULT", 1, "PRE_EXEC_INVENTORY", 1, 0, 1, "NO_DENIAL"]
    assert checked(rows).outcome == "REJECTED"
    rows = vector()
    rows.insert(-2, rows[-3].copy())
    assert checked(rows).outcome == "REJECTED"


def test_digest_is_content_only_and_revalidates_nested_values():
    c, w, v = api()
    capture = w.decode(encoded())
    assert v.canonical_digest(capture) == v.canonical_digest(w.decode(encoded()))
    for field, value in ((2, "d" * 40), (1, "e" * 32)):
        values = list(capture.events[0].values)
        values[field] = value
        other = replace(
            capture, events=(replace(capture.events[0], values=values), *capture.events[1:])
        )
        assert v.canonical_digest(capture) != v.canonical_digest(other)
    for value in (None, (), "capture"):
        with pytest.raises(ValueError):
            v.canonical_digest(value)
        with pytest.raises(ValueError):
            v.check_inventory(value)
    object.__setattr__(capture.events[0], "values", (False,))
    with pytest.raises(ValueError):
        v.canonical_digest(capture)
    with pytest.raises(ValueError):
        v.check_inventory(capture)


def test_decisions_cannot_carry_permission_or_inconsistent_reasons():
    c, _, _ = api()
    for outcome, reasons in (
        ("ELIGIBLE", ()),
        ("REJECTED", ()),
        ("WIRE_DIAGNOSTIC_CONSISTENT", ("BAD",)),
        ("REJECTED", (None,)),
        (True, ()),
        ("REJECTED", "BAD"),
    ):
        with pytest.raises(ValueError):
            c.Decision(outcome, reasons)
    reasons = ["BAD"]
    decision = c.Decision("REJECTED", reasons)
    reasons.clear()
    assert decision.reasons == ("BAD",)


@pytest.fixture
def build_context(tmp_path, monkeypatch):
    b = importlib.import_module("tests.deny_fd_v2.build")
    project = Path(__file__).resolve().parents[1]
    root = tmp_path / "source"
    root.mkdir()
    paths = tuple(
        "tests/deny_fd_v2/" + p
        for p in (
            "__init__.py",
            "build.py",
            "contracts.py",
            "guest/probe.c",
            "validation.py",
            "wire.py",
        )
    )
    for p in paths:
        target = root / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((project / p).read_bytes())

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)

    git("init", "--quiet")
    git("-c", "core.autocrlf=false", "add", "-A")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--quiet",
        "-m",
        "fixed sources",
    )
    revision = git("rev-parse", "HEAD").decode().strip()
    monkeypatch.setattr(b, "ROOT", root)
    descriptor = b.describe_sources(revision)
    assert {r["path"] for r in descriptor["sources"]} == set(paths)
    for r in descriptor["sources"]:
        assert r["sha256"] == hashlib.sha256((root / r["path"]).read_bytes()).hexdigest()
    manifest = root / "docs/evidence/deny_fd_v2_sources.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(descriptor))
    return b, root, revision, descriptor, manifest


def fake_elf():
    raw = bytearray(120)
    raw[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<HHI", raw, 16, 2, 62, 1)
    struct.pack_into("<Q", raw, 32, 64)
    struct.pack_into("<HHH", raw, 52, 64, 56, 1)
    struct.pack_into("<I", raw, 64, 1)
    return bytes(raw)


def compiler_double(monkeypatch, b, output=None, *, corrupt_source=False, expected_source=None):
    calls = []
    real_run = subprocess.run

    def run(args, **kwargs):
        if args[0] == "git":
            return real_run(args, **kwargs)
        calls.append(args)
        assert args[0] == "/usr/bin/cc"
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout=b"unit compiler boundary\n")
        assert "-static" in args and "-no-pie" in args and "-Werror" in args
        assert args[-2] == "-o"
        expected = (
            (b.ROOT / "tests/deny_fd_v2/guest/probe.c").read_bytes()
            if expected_source is None
            else expected_source
        )
        assert Path(args[-3]).read_bytes() == expected
        Path(args[-1]).write_bytes(fake_elf() if output is None else output)
        if corrupt_source:
            Path(args[-3]).write_bytes(b"changed during external compile")
        return subprocess.CompletedProcess(args, 0, stdout=b"compile diagnostics\n")

    monkeypatch.setattr(b.subprocess, "run", run)
    return calls


def test_compile_boundary_binds_source_and_never_executes_target(
    build_context, tmp_path, monkeypatch
):
    b, root, revision, descriptor, _ = build_context
    calls = compiler_double(monkeypatch, b)
    out = tmp_path / "output"
    record = b.compile_fixed_probe(out)
    assert record["source_revision"] == revision
    expected = hashlib.sha256(
        json.dumps(descriptor, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    assert record["source_manifest_digest"] == expected
    assert record["binary"]["sha256"] == hashlib.sha256(fake_elf()).hexdigest()
    assert record["runtime_qualified"] is False and record["build_input_closure_qualified"] is False
    assert all(v is False for v in record["permissions"].values())
    assert len(calls) == 2 and all(args[0] == "/usr/bin/cc" for args in calls)
    assert json.loads((out / "build-record.json").read_text()) == record
    assert (out / "compiler.log").read_bytes() == b"compile diagnostics\n"
    with pytest.raises(ValueError):
        b.compile_fixed_probe(out)
    with pytest.raises(ValueError):
        b.compile_fixed_probe(root / "unsafe-output")


@pytest.mark.parametrize("revision", (None, True, "HEAD", "a" * 39, "f" * 40))
def test_build_source_revision_is_exact_and_local(build_context, revision):
    with pytest.raises(ValueError):
        build_context[0].describe_sources(revision)


@pytest.mark.parametrize(
    "mutation",
    ("missing", "extra", "duplicate", "source_drift", "malformed", "directory", "nonobject"),
)
def test_manifest_or_working_source_drift_cannot_be_compiled(build_context, tmp_path, mutation):
    b, root, _, descriptor, manifest = build_context
    if mutation == "missing":
        manifest.unlink()
    elif mutation == "extra":
        descriptor["authority"] = True
        manifest.write_text(json.dumps(descriptor))
    elif mutation == "duplicate":
        manifest.write_text('{"schema":0,"schema":1}')
    elif mutation == "source_drift":
        (root / "tests/deny_fd_v2/guest/probe.c").write_bytes(b"changed source")
    elif mutation == "directory":
        manifest.unlink()
        manifest.mkdir()
    elif mutation == "nonobject":
        manifest.write_text("[]")
    else:
        manifest.write_text("not json")
    with pytest.raises(ValueError):
        b.compile_fixed_probe(tmp_path / "must-not-build")
    assert not (tmp_path / "must-not-build").exists()


@pytest.mark.parametrize(
    "failure",
    (
        OSError("no compiler"),
        subprocess.TimeoutExpired("cc", 60),
        subprocess.CalledProcessError(1, "cc", output=b"compile failed"),
    ),
)
def test_external_compiler_failure_preserves_failure_not_success(
    build_context, tmp_path, monkeypatch, failure
):
    b = build_context[0]
    real_run = subprocess.run

    def fail(*args, **kwargs):
        if args[0][0] == "git":
            return real_run(*args, **kwargs)
        raise failure

    monkeypatch.setattr(b.subprocess, "run", fail)
    out = tmp_path / "failed-build"
    with pytest.raises(ValueError):
        b.compile_fixed_probe(out)
    assert (out / "compiler-failure.log").is_file()
    assert not (out / "build-record.json").exists()


@pytest.mark.parametrize("output", (b"bad ELF", b"\x7fELF" + bytes(116)))
def test_wrong_compiler_output_is_not_a_verified_build(
    build_context, tmp_path, monkeypatch, output
):
    b = build_context[0]
    compiler_double(monkeypatch, b, output)
    with pytest.raises(ValueError):
        b.compile_fixed_probe(tmp_path / "invalid-elf")


def test_compiler_cannot_silently_change_pinned_input(build_context, tmp_path, monkeypatch):
    b = build_context[0]
    compiler_double(monkeypatch, b, corrupt_source=True)
    with pytest.raises(ValueError):
        b.compile_fixed_probe(tmp_path / "changed-input")


def test_verification_race_cannot_select_unverified_compiler_input(
    build_context, tmp_path, monkeypatch
):
    b, root, revision, _, _ = build_context
    source_path = root / "tests/deny_fd_v2/guest/probe.c"
    pinned = subprocess.check_output(
        ["git", "show", revision + ":tests/deny_fd_v2/guest/probe.c"], cwd=root
    )
    original_read = b._read_regular

    def edit_after_read(path):
        raw = original_read(path)
        if path == source_path:
            source_path.write_bytes(b"changed between verification and input selection")
        return raw

    monkeypatch.setattr(b, "_read_regular", edit_after_read)
    compiler_double(monkeypatch, b, expected_source=pinned)
    out = tmp_path / "race-build"
    record = b.compile_fixed_probe(out)
    assert (out / "probe.c").read_bytes() == pinned
    assert record["source_revision"] == revision and record["runtime_qualified"] is False


def test_source_manifest_rejects_git_executable_modes(build_context):
    b, root, _, _, _ = build_context
    subprocess.run(
        ["git", "update-index", "--chmod=+x", "--", "tests/deny_fd_v2/wire.py"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "wrong source mode",
        ],
        cwd=root,
        check=True,
    )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    with pytest.raises(ValueError):
        b.describe_sources(revision)


@pytest.mark.parametrize("variant", ("wrong_type", "interpreter", "dynamic"))
def test_dynamic_or_wrong_target_artifact_is_rejected(
    build_context, tmp_path, monkeypatch, variant
):
    raw = bytearray(fake_elf())
    if variant == "wrong_type":
        struct.pack_into("<H", raw, 16, 3)
    else:
        struct.pack_into("<I", raw, 64, 3 if variant == "interpreter" else 2)
    b = build_context[0]
    compiler_double(monkeypatch, b, bytes(raw))
    with pytest.raises(ValueError):
        b.compile_fixed_probe(tmp_path / "wrong-target")
