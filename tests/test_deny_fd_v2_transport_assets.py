"""Closed transport profile and immutable source context."""

import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError

import pytest


def api():
    assert importlib.util.find_spec("tests.deny_fd_v2_transport") is not None, (
        "transport package required"
    )
    return importlib.import_module("tests.deny_fd_v2_transport.assets")


def test_transport_context_keeps_old_source_identity(monkeypatch):
    from tests.test_deny_fd_v2_harness_assets import synthetic_assets

    old, _, _ = synthetic_assets(monkeypatch)
    bundle = api().TransportAssets(old.preflight())
    assert bundle.base.source_revision == "2481b84405beda95a394d1ca0248d7c9d632d28b"
    assert all(value is False for _, value in bundle.permissions)
    with pytest.raises(FrozenInstanceError):
        bundle.base = None


@pytest.mark.parametrize("value", (None, False, {}, "bundle"))
def test_unbound_context_refused(value):
    with pytest.raises(ValueError):
        api().TransportAssets(value)


@pytest.mark.parametrize(
    "mutation", ("runtime", "numeric_false", "extra", "limit", "endpoint", "config")
)
def test_drifted_transport_profile_refused_before_old_preflight(monkeypatch, mutation):
    a = api()
    profile = json.loads(json.dumps(a.PROFILE))
    if mutation == "runtime":
        profile["runtime_qualified"] = True
    elif mutation == "numeric_false":
        profile["permissions"]["application_authorized"] = 0
    elif mutation == "extra":
        profile["override"] = "caller VM"
    elif mutation == "limit":
        profile["aggregate_limit"] += 1
    elif mutation == "endpoint":
        profile["telemetry"] = profile["console"]
    else:
        profile["kernel_config_sha256"] = "0" * 64
    monkeypatch.setattr(a, "read_regular", lambda *args: json.dumps(profile).encode())
    with pytest.raises(ValueError, match="profile changed"):
        a.preflight()


def test_changed_config_refused(monkeypatch):
    a = api()

    def read(root, path, limit):
        return json.dumps(a.PROFILE).encode() if path == a.MANIFEST else b"changed kernel config"

    monkeypatch.setattr(a, "read_regular", read)
    with pytest.raises(ValueError, match="kernel config changed"):
        a.preflight()
