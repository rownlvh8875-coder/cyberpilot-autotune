"""Fixed read-only filesystem observations must reject drift, never follow links."""

import importlib
import os
import sys

import pytest


def filesystem():
    assert importlib.util.find_spec("compatibility.guest_input_closure.filesystem") is not None
    return importlib.import_module("compatibility.guest_input_closure.filesystem")


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
def test_real_tree_change_add_remove_mode_and_link_target_have_distinct_evidence(tmp_path):
    m = filesystem()
    (tmp_path / "a").write_bytes(b"a")
    (tmp_path / "a").chmod(0o444)
    (tmp_path / "alias").symlink_to("a")
    before = m.scan_tree("test", tmp_path)
    assert [(e.path, e.kind) for e in before] == [
        (".", "directory"),
        ("a", "file"),
        ("alias", "symlink"),
    ]
    assert before[1].sha256 == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
    (tmp_path / "a").chmod(0o644)
    (tmp_path / "a").write_bytes(b"b")
    (tmp_path / "new").write_bytes(b"new")
    (tmp_path / "alias").unlink()
    (tmp_path / "alias").symlink_to("new")
    after = {e.path: e for e in m.scan_tree("test", tmp_path)}
    assert after["a"].mode == 0o100644 and after["a"].sha256 != before[1].sha256
    assert after["alias"].target == "new" and after["alias"].sha256 is None
    (tmp_path / "new").unlink()
    assert "new" not in {e.path for e in m.scan_tree("test", tmp_path)}


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
def test_symlink_directory_is_recorded_without_reading_its_outside_target(tmp_path):
    m = filesystem()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "not-input").write_bytes(b"not in scope")
    root = tmp_path / "root"
    root.mkdir()
    (root / "alias").symlink_to(outside, target_is_directory=True)
    observed = m.scan_tree("test", root)
    assert [e.path for e in observed] == [".", "alias"]
    assert observed[1].target == str(outside)
    with pytest.raises((ValueError, OSError)):
        m.scan_tree("test", root / "alias")
    with pytest.raises((ValueError, OSError)):
        m.scan_selected("test", root, ("alias/not-input",))


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
def test_file_changed_during_hash_is_not_a_stable_input(tmp_path, monkeypatch):
    m = filesystem()
    path = tmp_path / "a"
    path.write_bytes(b"a")
    original = m.hashlib.file_digest

    def drift(stream, algorithm):
        path.write_bytes(b"changed")
        return original(stream, algorithm)

    monkeypatch.setattr(m.hashlib, "file_digest", drift)
    with pytest.raises(ValueError, match="changed"):
        m.scan_tree("test", tmp_path)


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
def test_growing_file_cannot_make_hashing_consume_unbounded_new_bytes(tmp_path, monkeypatch):
    m = filesystem()
    path = tmp_path / "a"
    path.write_bytes(b"a")

    def growing(reader, algorithm):
        assert algorithm == "sha256"
        path.write_bytes(b"a" * 100)
        reader.readinto(bytearray(16))
        pytest.fail("hash reader consumed beyond the initial bounded input")

    monkeypatch.setattr(m.hashlib, "file_digest", growing)
    with pytest.raises(ValueError, match="changed"):
        m.scan_tree("test", tmp_path)


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
@pytest.mark.parametrize("limit", ["entries", "depth", "file"])
def test_resource_bound_rejects_without_partial_success(tmp_path, monkeypatch, limit):
    m = filesystem()
    (tmp_path / "a").write_bytes(b"two")
    (tmp_path / "d").mkdir()
    (tmp_path / "d/e").mkdir()
    monkeypatch.setattr(
        m, {"entries": "MAX_ENTRIES", "depth": "MAX_DEPTH", "file": "MAX_FILE_BYTES"}[limit], 1
    )
    with pytest.raises(ValueError):
        m.scan_tree("test", tmp_path)


@pytest.mark.skipif(sys.platform != "linux", reason="Anchored no-follow inventory is Linux-only")
def test_fifo_is_never_opened_and_selected_paths_cannot_traverse(tmp_path):
    m = filesystem()
    os.mkfifo(tmp_path / "fifo")
    with pytest.raises(ValueError):
        m.scan_tree("test", tmp_path)
    with pytest.raises(ValueError):
        m.scan_selected("test", tmp_path, ("../escape",))
    with pytest.raises(ValueError):
        m.scan_selected("test", tmp_path, ("fifo", "fifo"))


def test_default_cli_has_no_observer_io_and_no_arbitrary_command_interface(monkeypatch):
    assert importlib.util.find_spec("compatibility.guest_input_closure.host_main") is not None
    main = importlib.import_module("compatibility.guest_input_closure.host_main")
    fixed = importlib.import_module("compatibility.guest_input_closure.fixed")

    def forbidden():
        pytest.fail("default/unknown CLI must not observe inputs")

    monkeypatch.setattr(fixed, "observe_fixed_inputs", forbidden)
    assert main.main([]) == 2
    for flags in (
        ["--command", "true"],
        ["--root", "/"],
        ["--execute-guest"],
        ["--verify-current", "--verify-current"],
    ):
        assert main.main(flags) == 2


def test_explicit_verification_prints_blocked_even_for_matching_current_inputs(monkeypatch, capsys):
    assert importlib.util.find_spec("compatibility.guest_input_closure.host_main") is not None
    main = importlib.import_module("compatibility.guest_input_closure.host_main")
    fixed = importlib.import_module("compatibility.guest_input_closure.fixed")
    from compatibility.guest_input_closure.contracts import InputSnapshot
    from tests.fixtures.guest_closure import image_bytes

    snapshot = InputSnapshot([])
    monkeypatch.setattr(fixed, "observe_fixed_inputs", lambda: (snapshot, (image_bytes(),)))
    monkeypatch.setattr(fixed, "expected_snapshot", lambda: snapshot)
    assert main.main(["--verify-current"]) == 2
    assert '"overall_status": "BLOCKED"' in capsys.readouterr().out


def test_unavailable_fixed_asset_does_not_fall_back_to_a_host_command(monkeypatch, capsys):
    assert importlib.util.find_spec("compatibility.guest_input_closure.host_main") is not None
    main = importlib.import_module("compatibility.guest_input_closure.host_main")
    fixed = importlib.import_module("compatibility.guest_input_closure.fixed")

    def unavailable():
        raise OSError("fixed input unavailable")

    monkeypatch.setattr(fixed, "observe_fixed_inputs", unavailable)
    assert main.main(["--verify-current"]) == 2
    assert "UNAVAILABLE" in capsys.readouterr().out
