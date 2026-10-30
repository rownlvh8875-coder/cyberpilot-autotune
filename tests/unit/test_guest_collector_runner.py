"""Only the already-bound software guest can execute the fixed collector."""

import gzip
import importlib
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec("compatibility.containment_guest_collector.host_main")
    return importlib.import_module("compatibility.containment_guest_collector.host_main")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--execute-guest"],
        ["--fixture", "HF01"],
        ["--execute-host"],
        ["--command", "anything"],
        ["--execute-guest", "--fixture", "HF25"],
        ["--execute-guest", "--fixture", "HF01", "--fixture", "HF01"],
        ["--execute-guest", "--fixture", "HF01", "--kernel", "/arbitrary"],
    ],
)
def test_invalid_selection_has_no_operational_dispatch(argv, monkeypatch):
    module = api()
    monkeypatch.setattr(module, "execute", lambda selected: pytest.fail("must not execute"))
    assert module.main(argv) == 2


def test_missing_new_inputs_cannot_fall_back_to_old_harness(monkeypatch, tmp_path):
    module = importlib.import_module("compatibility.containment_guest_collector.vm_runner")
    monkeypatch.setattr(module, "MANIFEST", tmp_path / "missing")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: pytest.fail("no subprocess"))
    assert module.execute(("HF01",)) == 2


def cpio_entries(raw):
    data = gzip.decompress(raw)
    offset = 0
    entries = {}
    while data[offset : offset + 6] == b"070701":
        fields = [int(data[offset + 6 + 8 * i : offset + 14 + 8 * i], 16) for i in range(13)]
        size, namesize = fields[6], fields[11]
        name = data[offset + 110 : offset + 109 + namesize].decode()
        offset = (offset + 110 + namesize + 3) & ~3
        content = data[offset : offset + size]
        offset = (offset + size + 3) & ~3
        if name == "TRAILER!!!":
            break
        assert name not in entries
        entries[name] = (fields[1], content)
    return entries


def test_image_only_adds_fixed_collector_and_invocation_not_caller_command():
    from compatibility.containment_backend_harmless.guest_image import GUEST_FILES

    module = importlib.import_module("compatibility.containment_guest_collector.image")
    files = {
        name: (0o100444 if name == "guard.bpf.o" else 0o100755, b"frozen") for name in GUEST_FILES
    }
    raw = module.build_collector_image(files, b"fixed-collector", ("HF01",))
    entries = cpio_entries(raw)
    assert entries["syscall-collector"] == (0o100755, b"fixed-collector")
    assert b'/syscall-collector "$fixture"' in entries["init"][1]
    assert b"for fixture in HF01;" in entries["init"][1]
    assert entries["harmless-fixtures"][1] == b"frozen"
    assert raw == module.build_collector_image(files, b"fixed-collector", ("HF01",))
    with pytest.raises(ValueError):
        module.build_collector_image(files, b"fixed", ("HF01; command",))
    with pytest.raises(ValueError):
        module.build_collector_image(
            files | {"init": (0o100755, b"arbitrary")}, b"fixed", ("HF01",)
        )


def test_fixed_recipe_excludes_hardware_shares_and_network():
    module = importlib.import_module("compatibility.containment_guest_collector.vm_runner")
    args = module.qemu_arguments(Path("/fixed"), Path("/owned/image"))
    assert args[args.index("-accel") + 1] == "tcg,thread=single"
    assert args[args.index("-nic") + 1] == "none"
    assert not {"-device", "-enable-kvm", "-virtfs", "-drive", "-fsdev", "-qmp"} & set(args)
