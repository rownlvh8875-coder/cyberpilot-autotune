"""Frozen receipts cannot broaden reads or substitute unobserved consumed bytes."""

import hashlib
import sys
from pathlib import Path

import pytest

from compatibility.guest_input_closure.contracts import InputEntry, InputSnapshot
from compatibility.guest_input_closure.legacy import _manifest, _Verifier

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux anchored reads")


def roots(tmp_path):
    result = {
        "repo_selected": tmp_path / "repo",
        "toolchain_exact_tree": tmp_path / "cache/toolchain",
        "vm_exact_tree": tmp_path / "vm/sysroot",
        "fixture_selected": tmp_path / "cache/build",
        "collector_selected": tmp_path / "collector/build",
        "host_gcc_selected": Path("/"),
    }
    for role, path in result.items():
        if role != "host_gcc_selected":
            path.mkdir(parents=True)
    return result


def test_manifest_symlink_is_rejected_without_reading_outside_bytes(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    root = tmp_path / "repo"
    root.mkdir()
    (root / "manifest").symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        _manifest(root, "manifest", hashlib.sha256(b"outside").hexdigest())


def test_manifest_content_pin_is_checked_before_interpreting_path_fields(tmp_path):
    (tmp_path / "manifest").write_bytes(b'{"inputs":[{"path":"/outside"}]}')
    with pytest.raises(ValueError, match="pin mismatch"):
        _manifest(tmp_path, "manifest", "0" * 64)


@pytest.mark.parametrize("path", ["../outside", "/etc/passwd", "/not-a-fixed-root/input"])
def test_frozen_record_cannot_request_arbitrary_roots_or_parent_traversal(tmp_path, path):
    checker = _Verifier(InputSnapshot([]), roots(tmp_path))
    with pytest.raises(ValueError):
        checker.check({"path": path, "sha256": "0" * 64})


def test_support_archive_link_is_not_read_even_when_target_content_hash_matches(
    tmp_path, monkeypatch
):
    import compatibility.guest_input_closure.filesystem as fs

    bindings = roots(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"outside")
    link = tmp_path / "cache/linked-package"
    link.symlink_to(outside)

    def forbidden(*args):
        pytest.fail("symlink target bytes were read")

    monkeypatch.setattr(fs.hashlib, "file_digest", forbidden)
    with pytest.raises(ValueError, match="kind mismatch"):
        _Verifier(InputSnapshot([]), bindings).check(
            {"path": str(link), "sha256": hashlib.sha256(b"outside").hexdigest()}
        )


def test_image_asset_bytes_must_match_the_earlier_observed_content(tmp_path):
    bindings = roots(tmp_path)
    root = bindings["fixture_selected"]
    (root / "asset").write_bytes(b"b")
    old = "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
    observed = InputSnapshot(
        [InputEntry("fixture_selected", "asset", "file", 0o100644, 1, old, None)]
    )
    with pytest.raises(ValueError, match="consumed legacy asset"):
        _Verifier(observed, bindings).bytes(
            {"path": str(root / "asset"), "bytes": 1, "sha256": old}
        )
