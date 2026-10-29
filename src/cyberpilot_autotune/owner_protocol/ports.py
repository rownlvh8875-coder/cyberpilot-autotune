"""Trusted in-memory capabilities only; no runtime adapter or authority supplied."""

from typing import Protocol

from .contracts import AuthorityContext, InstalledTuple, OwnerProtocolError


class Clock(Protocol):
    def now_s(self) -> float: ...


class Authority(Protocol):
    def approve(self, grant: AuthorityContext, now_s: float) -> bool: ...


class TuplePort(Protocol):
    def read(self) -> InstalledTuple: ...
    def compare_and_swap(self, expected: InstalledTuple, update: InstalledTuple) -> int: ...


class MemoryTuplePort:
    """Single-caller reference cell, not thread-safe or a controller interface."""

    def __init__(self, initial: InstalledTuple) -> None:
        if type(initial) is not InstalledTuple:
            raise ValueError("explicit installed state required")
        self._installed = initial

    def read(self) -> InstalledTuple:
        return self._installed

    def compare_and_swap(self, expected: InstalledTuple, update: InstalledTuple) -> int:
        if self._installed.digest != expected.digest:
            raise OwnerProtocolError("FOREIGN_STATE")
        self._installed = update
        return update.revision
