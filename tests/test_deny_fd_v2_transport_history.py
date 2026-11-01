"""Real Git policy boundaries for the dedicated transport successor."""

import importlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def api():
    name = "tests.history_transition.deny_fd_v2_transport_successor"
    assert importlib.util.find_spec(name) is not None, "transport successor required"
    return importlib.import_module(name)


def test_predecessor_has_no_transport_permission(tmp_path):
    root = tmp_path / "predecessor"
    subprocess.run(
        ["git", "clone", "--shared", "--quiet", "--no-checkout", str(ROOT), str(root)], check=True
    )
    subprocess.run(
        ["git", "checkout", "--quiet", "27cfdee55d2276f66d899adc07565da717ab554f"],
        cwd=root,
        check=True,
    )
    assert api().validate_transport_successor(root) == frozenset()


@pytest.mark.parametrize("constant", ("BASE", "PREREGISTRATION"))
def test_missing_git_object_cannot_grant_transport_permission(monkeypatch, constant):
    successor = api()
    monkeypatch.setattr(successor, constant, "0" * 40)
    with pytest.raises(ValueError):
        successor.validate_transport_successor(ROOT)


def test_invalid_git_root_cannot_be_treated_as_historical(tmp_path):
    with pytest.raises(ValueError):
        api().validate_transport_successor(tmp_path)
