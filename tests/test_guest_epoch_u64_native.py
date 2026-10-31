"""Actual-source snippet scalar tests supplement, never replace, kernel builds."""

import shutil
import subprocess

import pytest

from tests.guest_epoch_u64.native_probe import probe

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="GNU C compiler unavailable")
EXPECTED = (
    "0",
    "1",
    "4294967295",
    "4294967296",
    "4294967297",
    "9007199254740991",
    "9007199254740993",
    "9223372036854775807",
    "9223372036854775808",
    "18446744073709551614",
    "18446744073709551615",
    "UNAVAILABLE",
)


def test_source_snippets_preserve_literal_epochs_after_original_object_changes(tmp_path):
    assert probe(tmp_path) == EXPECTED


@pytest.mark.parametrize(
    "mutation", ["saved32", "buffer32", "signed", "format32", "mask32", "float"]
)
def test_each_narrowing_or_lossy_mutation_fails_independent_native_checks(tmp_path, mutation):
    with pytest.raises(subprocess.CalledProcessError):
        probe(tmp_path, mutation)


def test_probe_refuses_unknown_mutation_before_running_a_compiler(tmp_path):
    with pytest.raises(ValueError, match="MUTATION"):
        probe(tmp_path, "legacy-upgrade")


def test_probe_refuses_nonempty_destination_without_overwriting_it(tmp_path):
    sentinel = tmp_path / "existing"
    sentinel.write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="EMPTY_OWNED"):
        probe(tmp_path)
    assert sentinel.read_bytes() == b"unchanged"
