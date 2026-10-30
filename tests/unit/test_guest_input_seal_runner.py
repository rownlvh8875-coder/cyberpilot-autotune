"""Catch default execution, unbound build inputs and unsafe guest arguments."""

import copy
import hashlib
import subprocess

import pytest

from compatibility.guest_consumption.vm_runner import qemu_arguments
from compatibility.guest_input_closure.archive import parse_image
from compatibility.guest_input_seal.host_main import main
from compatibility.guest_input_seal.image import INPUT, SCOPE, build_image
from compatibility.guest_input_seal.vm_runner import validate_build_manifest


def test_default_and_invalid_arguments_never_load_assets(capsys):
    assert main([]) == 2
    assert "BLOCKED" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["--command", "echo unsafe"])
    with pytest.raises(SystemExit):
        main(["--run-prepared-guest", "--case", "IS99"])


def test_derived_fixed_image(fake_guest_files):
    raw = build_image(fake_guest_files, b"\x7fELF\x02\x01fixed", "IS04")
    members = {m.path: m for m in parse_image(raw)}
    assert members["etc/guest-input-seal-scope"].data == SCOPE
    assert members["lab/chmod-input"].data == INPUT
    assert b"/input-seal-probe IS04" in members["init"].data
    assert members["input-seal-probe"].mode == 0o100755
    with pytest.raises(ValueError):
        build_image(fake_guest_files, b"bad", "IS01")
    with pytest.raises(ValueError):
        build_image(fake_guest_files, b"\x7fELF\x02\x01fixed", "IS99")


@pytest.fixture
def fake_guest_files():
    from compatibility.containment_backend_harmless.guest_image import GUEST_FILES

    return {p: (0o100444 if p.endswith("guard.bpf.o") else 0o100755, b"fixed") for p in GUEST_FILES}


def manifest():
    return {
        "schema": "guest-input-seal-build-v1",
        "scope": "FIXED_HARMLESS_GUEST_OBJECT_SEALS_ONLY",
        "base_revision": "ae7b3644984cd5ecc8fbb23532f5ec7e0da3998f",
        "vm_cohort_digest": "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c",
        "legacy_snapshot_digest": "a" * 64,
        "binary": {"path": "input-seal-probe", "sha256": "b" * 64, "bytes": 123},
        "sources": [],
        "build_commands": ["cc fixed"],
        "build_input_closure_qualified": False,
        "permissions": dict(
            __import__(
                "compatibility.guest_input_seal.contracts", fromlist=["PERMISSIONS"]
            ).PERMISSIONS
        ),
    }


def test_complete_manifest_and_mutations():
    from compatibility.guest_input_seal.vm_runner import SOURCES

    data = manifest()
    data["sources"] = [
        {"path": name, "sha256": hashlib.sha256(b"fixed").hexdigest(), "bytes": 5}
        for name in SOURCES
    ]
    validate_build_manifest(data)
    for key, value in [
        ("scope", "QUALIFIED"),
        ("binary", {"path": "../escape", "sha256": "b" * 64, "bytes": 123}),
        ("sources", data["sources"] + data["sources"][:1]),
        ("build_input_closure_qualified", True),
        ("permissions", {"application_authorized": False}),
    ]:
        bad = copy.deepcopy(data)
        bad[key] = value
        with pytest.raises(ValueError):
            validate_build_manifest(bad)
    for key in data["permissions"]:
        bad = copy.deepcopy(data)
        bad["permissions"][key] = True
        with pytest.raises(ValueError):
            validate_build_manifest(bad)


def test_fixed_qemu_has_no_external_io(tmp_path):
    image = tmp_path / "has spaces" / "fixed initrd"
    args = qemu_arguments(image)
    assert args[args.index("-initrd") + 1] == str(image)
    assert args[args.index("-nic") + 1] == "none"
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert not set(args) & {"-drive", "-hda", "-fsdev", "-virtfs", "-qmp", "-enable-kvm"}


def test_capture_boundary_preserves_actual_serial(monkeypatch, fake_guest_files, tmp_path):
    from compatibility.guest_input_seal import vm_runner
    from tests.unit.test_guest_input_seal_contract import fixture, wire

    raw = (
        "ACTUAL_GUEST_KERNEL=6.12.113+deb13-cloud-amd64\n"
        + wire(fixture())
        + "\nINPUT_SEAL_PROBE_EXIT 0\nINPUT_SEAL_GUEST_DONE\n"
    ).encode()
    monkeypatch.setattr(vm_runner.sys, "platform", "linux")
    monkeypatch.setattr(
        vm_runner, "load_assets", lambda: (fake_guest_files, b"\x7fELF\x02\x01fixed", {})
    )

    def fixed_run(args, **kwargs):
        assert kwargs["timeout"] == 180
        assert kwargs["input"] == b""
        assert args[args.index("-nic") + 1] == "none"
        return subprocess.CompletedProcess(args, 0, raw)

    monkeypatch.setattr(vm_runner.subprocess, "run", fixed_run)
    # Only substitute disposable directory placement, not image/parser behavior.
    original = vm_runner.tempfile.TemporaryDirectory
    monkeypatch.setattr(
        vm_runner.tempfile, "TemporaryDirectory", lambda **kwargs: original(dir=tmp_path)
    )
    observed = vm_runner.capture_cases(("IS01",))
    assert observed == ((fixture(), raw),)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 180, output=b"partial serial")

    monkeypatch.setattr(vm_runner.subprocess, "run", timeout)
    with pytest.raises(vm_runner.CaptureUnavailable) as error:
        vm_runner.capture_cases(("IS01",))
    assert error.value.raw == b"partial serial"
    assert error.value.completed == ()


@pytest.mark.parametrize("cases", [(), ("IS01", "IS01"), ("IS99",), ["IS01"]])
def test_invalid_case_selection_before_asset_access(cases, monkeypatch):
    from compatibility.guest_input_seal import vm_runner

    with pytest.raises(ValueError):
        vm_runner.capture_cases(cases)
