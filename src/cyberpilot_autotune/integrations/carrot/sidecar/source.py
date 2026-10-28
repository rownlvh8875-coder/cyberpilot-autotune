"""Pinned SubMaster receive bridge; no publisher, reader batch or background work."""

import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from ..availability import require_schema
from ..errors import CarrotDependencyUnavailable
from ..extraction import DecodedTopicSample
from ..health import SessionToken, TopicHealthEvidence, uint64
from .config import TOPICS, SidecarError, SidecarReason, require


class SubMasterView(Protocol):
    services: Sequence[str]
    simulation: bool
    ignore_alive: Sequence[str]
    ignore_average_freq: Sequence[str]
    ignore_valid: Sequence[str]
    seen: Mapping[str, bool]
    alive: Mapping[str, bool]
    valid: Mapping[str, bool]
    freq_ok: Mapping[str, bool]
    updated: Mapping[str, bool]
    logMonoTime: Mapping[str, int]

    def __getitem__(self, topic: str) -> object: ...
    def update(self, timeout: int) -> None: ...


@dataclass(frozen=True, slots=True)
class MessagingAPI:
    SubMaster: Callable[..., SubMasterView]


def require_live_dependencies() -> MessagingAPI:
    require_schema()
    try:
        from openpilot.cereal import messaging

        constructor = messaging.SubMaster
        require(callable(constructor), SidecarReason.UNSUPPORTED_ENVIRONMENT)
    except ImportError:
        raise CarrotDependencyUnavailable() from None
    except Exception:
        raise SidecarError(SidecarReason.UNSUPPORTED_ENVIRONMENT) from None
    return MessagingAPI(cast(Callable[..., SubMasterView], constructor))


def open_live_source(session: SessionToken) -> "SubMasterSource":
    api = require_live_dependencies()
    require(sys.platform == "linux", SidecarReason.UNSUPPORTED_ENVIRONMENT)
    try:
        sm = api.SubMaster(list(TOPICS), poll=list(TOPICS))
        return SubMasterSource(sm, session)
    except SidecarError:
        raise
    except Exception:
        raise SidecarError(SidecarReason.UNSUPPORTED_ENVIRONMENT) from None


def _flag(sm: SubMasterView, name: str, topic: str) -> bool | None:
    values = getattr(sm, name, None)
    value = values.get(topic) if isinstance(values, Mapping) else None
    return value if type(value) is bool else None


class SubMasterSource:
    def __init__(self, submaster: SubMasterView, session: SessionToken) -> None:
        require(type(session) is SessionToken, SidecarReason.SESSION_TOKEN_MISSING)
        self._sm: SubMasterView | None = submaster
        self._session = session
        self._validate()

    @property
    def session(self) -> SessionToken:
        return self._session

    def _validate(self) -> SubMasterView:
        sm = self._sm
        require(sm is not None, SidecarReason.SOURCE_CLOSED)
        assert sm is not None
        try:
            supported = (
                tuple(sm.services) == TOPICS
                and sm.simulation is False
                and tuple(sm.ignore_alive) == ()
                and tuple(sm.ignore_average_freq) == ()
                and tuple(sm.ignore_valid) == ()
            )
        except Exception:
            supported = False
        require(supported, SidecarReason.UNSUPPORTED_ENVIRONMENT)
        return sm

    def poll(self, timeout_ms: int, consume: Callable[[DecodedTopicSample], None]) -> None:
        sm = self._validate()
        sm.update(timeout_ms)
        self._validate()
        for topic in TOPICS:
            updated = _flag(sm, "updated", topic)
            require(updated is not None, SidecarReason.INVALID_SOURCE_METADATA)
            if updated is not True:
                continue
            health = TopicHealthEvidence(
                *(
                    _flag(sm, field, topic)
                    for field in ("seen", "alive", "valid", "freq_ok", "updated")
                )
            )
            try:
                stamp = uint64(sm.logMonoTime.get(topic))
                valid = _flag(sm, "valid", topic)
                require(type(valid) is bool, SidecarReason.INVALID_SOURCE_METADATA)
                assert valid is not None
                sample = DecodedTopicSample(topic, stamp, valid, health, sm[topic], self.session)
            except Exception:
                raise SidecarError(SidecarReason.INVALID_SOURCE_METADATA, topic=topic) from None
            # Consume synchronously before another SubMaster.update can replace backing.
            consume(sample)

    def close(self) -> None:
        self._sm = None
