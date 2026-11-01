"""Inspect image bytes only; no init, busybox, probe or VM is executed."""

from dataclasses import replace

import pytest

from compatibility.guest_input_closure.archive import parse_image
from tests.test_deny_fd_v2_harness_assets import synthetic_assets


def test_image_is_deterministic_and_minimal(monkeypatch):
    a, _, _ = synthetic_assets(monkeypatch)
    from tests.deny_fd_v2_harness.image import build_image

    bundle = a.preflight()
    raw = build_image(bundle, "DFD01")
    assert raw == build_image(bundle, "DFD01")
    entries = {e.path: e for e in parse_image(raw)}
    assert set(entries) == {
        "bin",
        "dev",
        "proc",
        "sys",
        "etc",
        "dev/console",
        "dev/null",
        "bin/busybox",
        "deny-fd-v2-probe",
        "etc/deny-fd-v2-scope",
        "init",
    }
    assert entries["deny-fd-v2-probe"].data == bundle.probe
    assert entries["bin/busybox"].data == bundle.busybox
    assert (
        entries["etc/deny-fd-v2-scope"].data == b"deny-fd-v2: fixed pre-exec inventory probe only\n"
    )
    assert entries["dev/console"].mode == 0o020600
    assert (entries["dev/console"].major, entries["dev/console"].minor) == (5, 1)
    assert entries["deny-fd-v2-probe"].mode == 0o100755


@pytest.mark.parametrize("case", ("DFD01", "DFD02", "DFD03", "DFD04", "DFD05", "DFD06"))
def test_each_fixed_case_has_distinct_image_and_literal_invocation(monkeypatch, case):
    a, _, _ = synthetic_assets(monkeypatch)
    from tests.deny_fd_v2_harness.image import build_image

    entries = {e.path: e for e in parse_image(build_image(a.preflight(), case))}
    assert b"/deny-fd-v2-probe --probe " + case.encode() + b"\n" in entries["init"].data
    assert b"DFD2_PROBE_EXIT=$probe_status" in entries["init"].data


@pytest.mark.parametrize("case", ("DFD00", "DFD07", "DFD01;id", "", None, True, ["DFD01"]))
def test_unknown_case_or_payload_rejected(monkeypatch, case):
    a, _, _ = synthetic_assets(monkeypatch)
    from tests.deny_fd_v2_harness.image import build_image

    with pytest.raises(ValueError):
        build_image(a.preflight(), case)


def test_changed_bundle_cannot_insert_unpinned_payload(monkeypatch):
    a, _, _ = synthetic_assets(monkeypatch)
    from tests.deny_fd_v2_harness.image import build_image

    bundle = replace(a.preflight(), probe=a.preflight().probe + b"other")
    with pytest.raises(ValueError):
        build_image(bundle, "DFD01")
