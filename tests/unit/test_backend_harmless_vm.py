"""Software guest recipe only; these tests never start a VM or load a guard."""

import importlib
import json
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec("compatibility.containment_backend_harmless.vm_runner")
    return importlib.import_module("compatibility.containment_backend_harmless.vm_runner")


def test_fixed_qemu_recipe_has_no_host_policy_or_device_arguments():
    args = api().qemu_arguments(Path("/fixed/vm"), Path("/owned/guest.cpio.gz"))
    assert "tcg,thread=single" in args
    assert args[args.index("-nic") + 1] == "none"
    assert args[args.index("-monitor") + 1] == "none"
    assert "console=ttyS0" in args[-2]
    assert not any(
        x in args for x in ("-enable-kvm", "-drive", "-fsdev", "-virtfs", "-device", "-qmp")
    )


def test_default_runner_fails_before_process_for_missing_cohort(monkeypatch, tmp_path):
    module = api()
    monkeypatch.setattr(module, "MANIFEST", tmp_path / "missing")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: pytest.fail("must not spawn"))
    assert module.execute_guest_job(("HF01",)) == 2


@pytest.mark.parametrize("selected", [(), ("HF25",), ("HF01", "HF01")])
def test_invalid_selection_rejected_before_inputs(selected, monkeypatch):
    module = api()
    monkeypatch.setattr(module, "verified_manifest", lambda: pytest.fail("must not inspect"))
    assert module.execute_guest_job(selected) == 2


def test_hash_drift_rejected(tmp_path):
    path = tmp_path / "file"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="INPUT_HASH_MISMATCH"):
        api().verify_file(path, "0" * 64)


def test_guest_image_is_deterministic_and_selection_is_fixed_data():
    images = importlib.import_module("compatibility.containment_backend_harmless.guest_image")
    one = images.build_image({"bin/busybox": (0o100755, b"fixed")}, ("HF01",))
    assert one == images.build_image({"bin/busybox": (0o100755, b"fixed")}, ("HF01",))
    assert one != images.build_image({"bin/busybox": (0o100755, b"fixed")}, ("HF02",))
    with pytest.raises(ValueError):
        images.build_image({}, ("HF01; arbitrary",))


def test_manifest_cannot_turn_a_shell_string_into_vm_arguments():
    data = json.loads(
        (
            Path(__file__).parents[2]
            / "compatibility/containment_backend_harmless/host/build_manifest.json"
        ).read_text()
    )
    assert "command" not in data
    assert data["scope"] == "SOFTWARE_GUEST_ONLY_NO_DEVICE_ATTEMPT"
    assert data["permissions"] == {
        name: False
        for name in (
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
            "runtime_qualified",
            "device_class_qualified",
            "policy_adopted",
        )
    }


@pytest.mark.parametrize(
    "change", ["permissions", "guest_name", "unhashed_guest", "duplicate_guest"]
)
def test_manifest_cannot_override_bootstrap_or_skip_guest_hashes(change):
    module = api()
    data = json.loads(module.MANIFEST.read_text())
    if change == "permissions":
        data["permissions"] = {}
    elif change == "guest_name":
        data["guest_files"][0]["guest_path"] = "init"
    elif change == "unhashed_guest":
        data["guest_files"][0]["path"] = "/arbitrary/unbound"
    else:
        data["guest_files"].append(data["guest_files"][0])
    with pytest.raises(ValueError):
        module.validate_manifest_structure(data)


@pytest.mark.parametrize("name", ["init", "../escape", "/absolute", "etc/guest-harmless-scope"])
def test_guest_archive_rejects_bootstrap_replacement_or_path_escape(name):
    module = importlib.import_module("compatibility.containment_backend_harmless.guest_image")
    with pytest.raises(ValueError):
        module.build_image({name: (0o100755, b"unbound")}, ("HF01",))
