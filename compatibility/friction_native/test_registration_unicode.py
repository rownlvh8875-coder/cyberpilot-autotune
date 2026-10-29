"""NR-M1: real Git alternate paths, without native object/source mutations."""

import os
import subprocess
from pathlib import Path

import pytest

from compatibility.friction_native import registration
from compatibility.friction_native.test_registration import snapshot


@pytest.fixture(scope="module")
def source():
    return Path(os.environ["FRICTION_NATIVE_REFERENCE"])


def alias(source, directory, name):
    # A physical Git directory: Path.resolve must NOT erase the Unicode case.
    reference = directory / name
    subprocess.run(
        ["git", "init", "--bare", "--object-format=sha1", "--quiet", str(reference)],
        env=registration._environment(),
        check=True,
    )
    objects = (
        registration._git(source, "rev-parse", "--path-format=absolute", "--git-path", "objects")
        .decode()
        .strip()
    )
    # Git alternates FILE uses UTF-8 lines; the production ENV boundary is the
    # C-quoted path of this new objects directory, not this ASCII backing path.
    (reference / "objects/info/alternates").write_bytes((objects + "\n").encode("utf-8"))
    return reference


@pytest.mark.parametrize(
    "name",
    ["ascii reference", "한글 저장소", "référence", "資料", "증거 😀", "re\u0301fe\u0301rence"],
    ids=["ascii-space", "korean-space", "accent", "cjk", "emoji-space", "combining"],
)
def test_complete_record_is_path_independent_and_reference_stays_read_only(source, tmp_path, name):
    reference = alias(source, tmp_path, name)
    assert reference.resolve() == reference
    before, backing = snapshot(reference), snapshot(source)
    expected = registration.read_record(registration.RECORD)
    try:
        actual = registration.prepare(reference)
    except subprocess.CalledProcessError as error:
        pytest.fail("NR_M1_NONASCII_PATH_REJECTED: " + error.stderr.decode(errors="replace"))
    assert actual == expected
    assert snapshot(reference) == before
    assert snapshot(source) == backing


@pytest.mark.parametrize("name", ["CLI 한글 참조", "référence 😀"])
def test_cli_with_unicode_input_and_overlay_parent_preserves_identity_and_cleans_up(
    source, tmp_path, name, monkeypatch, capsys
):
    reference = alias(source, tmp_path, name)
    overlay_parent = tmp_path / "임시 overlay 😀"
    overlay_parent.mkdir()
    monkeypatch.setattr(registration.tempfile, "tempdir", str(overlay_parent))
    before, backing = snapshot(reference), snapshot(source)
    assert registration.main(["--reference-checkout", str(reference)]) == 0
    assert "no runtime/empirical/application approval" in capsys.readouterr().out
    assert tuple(overlay_parent.iterdir()) == ()
    assert snapshot(reference) == before
    assert snapshot(source) == backing
