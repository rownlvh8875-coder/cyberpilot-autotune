"""Explicit caller health/session observations; no SubMaster or clock access."""

from dataclasses import dataclass

from .errors import CarrotInputError


def uint64(value: object, *, present: bool = True) -> int:
    if type(value) is not int or not int(present) <= value < 2**64:
        raise CarrotInputError("INVALID_PUBLICATION_TIMESTAMP")
    return value


@dataclass(frozen=True, slots=True)
class SessionToken:
    generation: int
    token: str

    def __post_init__(self) -> None:
        if (
            type(self.generation) is not int
            or self.generation < 0
            or type(self.token) is not str
            or len(self.token) != 32
            or any(char not in "0123456789abcdef" for char in self.token)
        ):
            raise CarrotInputError("INVALID_SOFTWARE_SESSION_TOKEN")


@dataclass(frozen=True, slots=True)
class TopicHealthEvidence:
    seen: bool | None
    alive: bool | None
    valid: bool | None
    freq_ok: bool | None
    updated: bool | None

    def __post_init__(self) -> None:
        if any(
            value is not None and type(value) is not bool
            for value in (
                self.seen,
                self.alive,
                self.valid,
                self.freq_ok,
                self.updated,
            )
        ):
            raise CarrotInputError("INVALID_TOPIC_HEALTH")

    @property
    def healthy(self) -> bool:
        return all(
            value is True
            for value in (
                self.seen,
                self.alive,
                self.valid,
                self.freq_ok,
                self.updated,
            )
        )
