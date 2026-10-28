"""Fixed native factory boundary without loading msgq or launching a service."""

import builtins
from types import SimpleNamespace

import pytest

from cyberpilot_autotune.integrations.carrot.errors import CarrotDependencyUnavailable
from cyberpilot_autotune.integrations.carrot.sidecar import source
from cyberpilot_autotune.integrations.carrot.sidecar.config import SidecarError
from tests.fixtures.carrot_adapter import session
from tests.fixtures.carrot_readers import binding
from tests.fixtures.sidecar import ScriptedSubMaster


@pytest.mark.parametrize("failure", [None, ImportError, RuntimeError])
def test_fixed_local_messaging_import_is_explicit_and_typed(monkeypatch, failure):
    monkeypatch.setattr(source, "require_schema", binding)
    original = builtins.__import__
    expected = SimpleNamespace(SubMaster=lambda *args, **kwargs: None, PubMaster=object())

    def load(name, *args, **kwargs):
        if name == "openpilot.cereal":
            if failure is not None:
                raise failure("SECRET-IMPORT")
            return SimpleNamespace(messaging=expected)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", load)
    if failure is None:
        api = source.require_live_dependencies()
        assert api.SubMaster is expected.SubMaster
        assert not hasattr(api, "PubMaster")
    else:
        with pytest.raises(
            CarrotDependencyUnavailable if failure is ImportError else SidecarError
        ) as error:
            source.require_live_dependencies()
        assert "SECRET" not in str(error.value)


@pytest.mark.parametrize("mode", ["ok", "wrong_platform", "backend_failure", "simulation"])
def test_live_factory_subscribes_to_exact_three_topics_without_publishers(monkeypatch, mode):
    sm = ScriptedSubMaster([])

    def factory(services, *, poll):
        assert services == poll == ["carControl", "carState", "carOutput"]
        if mode == "backend_failure":
            raise RuntimeError("SECRET-IPC")
        sm.simulation = mode == "simulation"
        return sm

    monkeypatch.setattr(
        source, "require_live_dependencies", lambda: SimpleNamespace(SubMaster=factory)
    )
    monkeypatch.setattr(source.sys, "platform", "win32" if mode == "wrong_platform" else "linux")
    if mode == "ok":
        source.open_live_source(session()).close()
    else:
        with pytest.raises(SidecarError, match="UNSUPPORTED_ENVIRONMENT"):
            source.open_live_source(session())


def test_missing_session_and_malformed_submaster_cannot_open_bridge():
    with pytest.raises(SidecarError, match="SESSION_TOKEN_MISSING"):
        source.SubMasterSource(ScriptedSubMaster([]), None)
    with pytest.raises(SidecarError, match="UNSUPPORTED_ENVIRONMENT"):
        source.SubMasterSource(object(), session())
