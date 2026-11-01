"""Synthetic wire/receipt adversaries never become actual acquisition evidence."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.test_deny_fd_v2_harness_assets import synthetic_assets
from tests.test_deny_fd_v2_wire import encoded, vector


def api():
    name = "tests.deny_fd_v2_harness.capture"
    assert importlib.util.find_spec(name) is not None, "untrusted capture binding required"
    return importlib.import_module(name)


def serial(bundle, case="DFD01", **changes):
    relation = {
        "DFD01": {},
        "DFD02": {"observed": (0,), "outcome": "NO_DENIAL"},
        "DFD03": {"expected": (3,), "subject": 3, "causes": (0,)},
        "DFD04": {"observed": (0, 3, 4), "causes": (3, 4)},
        "DFD05": {"observed": (), "outcome": "UNSUPPORTED_MISSING"},
        "DFD06": {"observed": (3,), "outcome": "UNSUPPORTED_MIXED"},
    }[case]
    rows = vector(case=case, **(relation | changes))
    rows[0][5:7] = [bundle.source_revision, bundle.source_manifest_digest]
    return encoded(rows)


def record(bundle, **changes):
    api()
    from tests.deny_fd_v2_harness.contracts import AcquisitionRecord, digest

    values = dict(
        case="DFD01",
        attempt_id="1" * 32,
        source_revision=bundle.source_revision,
        source_manifest_digest=bundle.source_manifest_digest,
        probe_sha256=digest(bundle.probe),
        vm_cohort_digest=bundle.vm_cohort_digest,
        kernel_sha256=bundle.kernel_sha256,
        init_sha256="4" * 64,
        image_sha256="5" * 64,
        argv=("fixed-qemu", "-nic", "none"),
        raw=serial(bundle),
        exit_code=0,
        termination="EXITED",
        raw_complete=True,
        host_start_ns=1,
        host_end_ns=2,
    )
    return AcquisitionRecord(**(values | changes))


@pytest.mark.parametrize("case", ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06"))
def test_fixed_source_policy_and_actual_inventory_remain_untrusted(monkeypatch, case):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    capture = v.validate_capture(serial(bundle, case), case, bundle)
    from tests.deny_fd_v2.validation import check_inventory

    assert check_inventory(capture).status == "BLOCKED"
    assert all(value is False for _, value in check_inventory(capture).permissions)


@pytest.mark.parametrize("mutation", ("source", "manifest", "case", "v1", "truncated", "cause"))
def test_wrong_source_case_or_window_rejected(monkeypatch, mutation):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    rows = vector()
    rows[0][5:7] = [bundle.source_revision, bundle.source_manifest_digest]
    if mutation == "source":
        rows[0][5] = "f" * 40
    elif mutation == "manifest":
        rows[0][6] = "f" * 64
    elif mutation == "case":
        rows[0][9] = "DFD02"
    elif mutation == "cause":
        rows[7][-1] = 999
    raw = encoded(rows)
    if mutation == "v1":
        raw = raw.replace(b"DFD2", b"HFD")
    if mutation == "truncated":
        raw = raw[:-1]
    with pytest.raises(ValueError):
        v.validate_capture(raw, "DFD01", bundle)


def test_wrong_requested_policy_or_expected_fd_rejected(monkeypatch):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    raw = serial(bundle, expected=(3,), subject=3, causes=(0,))
    with pytest.raises(ValueError):
        v.validate_capture(raw, "DFD01", bundle)


def test_case_label_does_not_invent_observed_descriptors(monkeypatch):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    capture = v.validate_capture(serial(bundle, observed=(0, 7), causes=(7,)), "DFD01", bundle)
    assert [e.values[1] for e in capture.events if e.kind == "CAUSE"] == [7]


def test_record_is_immutable_content_identity_not_authority(monkeypatch):
    api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    args = ["fixed-qemu", "-nic", "none"]
    r = record(bundle, argv=args)
    args.append("-enable-kvm")
    assert r.argv == ("fixed-qemu", "-nic", "none")
    assert r.content_digest == record(bundle).content_digest
    assert r.content_digest != replace(r, source_revision="f" * 40).content_digest
    assert r.content_digest != replace(r, raw=r.raw + b"noise\n").content_digest
    assert r.raw_size == len(r.raw) and len(r.raw_sha256) == 64
    assert r.status == "BLOCKED" and r.clock_domain == "HOST_MONOTONIC_NS"
    assert all(v is False for _, v in r.permissions)
    with pytest.raises(FrozenInstanceError):
        r.raw_complete = False


def test_none_is_not_zero_exit(monkeypatch):
    api()
    a, _, _ = synthetic_assets(monkeypatch)
    bundle = a.preflight()
    unknown = record(bundle, exit_code=None, termination="TIMEOUT", raw_complete=False)
    zero = replace(unknown, exit_code=0)
    assert unknown.content_digest != zero.content_digest
    with pytest.raises(ValueError):
        replace(unknown, termination="EXITED", raw_complete=True)


@pytest.mark.parametrize(
    "field,value",
    (
        ("exit_code", False),
        ("exit_code", 2**31),
        ("exit_code", 1.0),
        ("raw_complete", 0),
        ("host_start_ns", True),
        ("host_start_ns", -1),
        ("host_end_ns", 0),
        ("host_end_ns", 2**64),
        ("host_end_ns", float("nan")),
        ("termination", "OTHER"),
        ("termination", "NONZERO_EXIT"),
        ("raw", bytearray()),
        ("raw", b"x" * (1024 * 1024 + 1)),
        ("attempt_id", ""),
        ("case", "DFD07"),
        ("argv", "fixed-qemu"),
        ("argv", ("qemu", "bad\x00arg")),
        ("argv", ()),
        ("source_revision", "x" * 40),
        ("image_sha256", "0" * 63),
    ),
)
def test_nonfinite_unknown_and_inconsistent_record_fields_rejected(monkeypatch, field, value):
    api()
    a, _, _ = synthetic_assets(monkeypatch)
    with pytest.raises(ValueError):
        record(a.preflight(), **{field: value})


def test_raw_prefix_and_completed_batch_survive_failure(monkeypatch):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    completed = [record(a.preflight())]
    failure = v.CaptureFailure("output limit", b"partial\n", False, completed)
    completed.clear()
    assert failure.raw == b"partial\n" and failure.raw_complete is False
    assert len(failure.completed) == 1 and str(failure) == "output limit"
    with pytest.raises(AttributeError):
        failure.raw = b"replacement"


def test_current_failure_record_is_explicit_immutable_context(monkeypatch):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    current = record(
        a.preflight(), raw=b"prefix", termination="TIMEOUT", exit_code=None, raw_complete=False
    )
    failure = v.CaptureFailure(
        "volume full",
        current.raw,
        False,
        current_record=current,
        acquisition_error="deadline",
        persistence_error="volume full",
    )
    assert failure.current_record is current and failure.acquisition_error == "deadline"
    assert failure.persistence_error == "volume full"
    for field in ("current_record", "acquisition_error", "persistence_error"):
        with pytest.raises(AttributeError):
            setattr(failure, field, None)
    absent = v.CaptureFailure("setup unavailable", b"", False)
    assert absent.current_record is None
    assert absent.acquisition_error is None and absent.persistence_error is None


@pytest.mark.parametrize(
    "changes",
    (
        {"current_record": False},
        {"acquisition_error": False},
        {"acquisition_error": ""},
        {"acquisition_error": "x" * 4001},
        {"persistence_error": "bad\x00error"},
        {"persistence_error": 0},
    ),
)
def test_failure_context_rejects_unknown_or_unbounded_values(changes):
    v = api()
    with pytest.raises(ValueError):
        v.CaptureFailure("failed", b"", False, **changes)


def test_failure_current_record_must_match_retained_raw_and_completeness(monkeypatch):
    v = api()
    a, _, _ = synthetic_assets(monkeypatch)
    current = record(a.preflight())
    for raw, complete in ((b"different", True), (current.raw, False)):
        with pytest.raises(ValueError):
            v.CaptureFailure("failed", raw, complete, current_record=current)
