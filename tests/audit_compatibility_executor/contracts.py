"""Immutable supplied values. Even complete observations confer no authority."""

from dataclasses import dataclass
from enum import Enum

PERMISSIONS = tuple(
    (name, False)
    for name in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)


class SyntheticCase(Enum):
    FD_CLOSED = "FD_CLOSED"
    DIRECTORY_READ_ONLY = "DIRECTORY_READ_ONLY"
    DESCENDANT_NETWORK = "DESCENDANT_NETWORK"
    TIMEOUT_SETSID = "TIMEOUT_SETSID"
    OUTPUT_FLOOD = "OUTPUT_FLOOD"
    MISSING_MOUNT = "MISSING_MOUNT"
    NONZERO_EXIT = "NONZERO_EXIT"
    SUPERVISOR_ABORT = "SUPERVISOR_ABORT"


def _path(value: str) -> None:
    if (
        type(value) is not str
        or not value.startswith("/")
        or "\0" in value
        or any(p in ("", ".", "..") for p in value.split("/")[1:])
    ):
        raise ValueError("absolute literal non-root path required")


def _reasons(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (tuple, list) or any(type(v) is not str or not v for v in value):
        raise ValueError("nonempty literal reason strings required")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class SyntheticRequest:
    case: SyntheticCase
    owner_directory: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if type(self) is not SyntheticRequest or type(self.case) is not SyntheticCase:
            raise ValueError("exact closed request required")
        _path(self.owner_directory)


@dataclass(frozen=True, slots=True)
class SyntheticResult:
    case: SyntheticCase
    outcome: str
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]
    cleanup: str
    stdout: bytes
    stderr: bytes
    run_directory: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "errors", _reasons(self.errors))
        object.__setattr__(self, "unavailable", _reasons(self.unavailable))
        self.validate()

    def validate(self) -> None:
        if type(self) is not SyntheticResult or type(self.case) is not SyntheticCase:
            raise ValueError("exact result required")
        if type(self.errors) is not tuple or type(self.unavailable) is not tuple:
            raise ValueError("immutable reasons required")
        _reasons(self.errors)
        _reasons(self.unavailable)
        if type(self.cleanup) is not str or self.cleanup not in ("CONFIRMED", "UNCONFIRMED"):
            raise ValueError("explicit cleanup state required")
        if type(self.stdout) is not bytes or type(self.stderr) is not bytes:
            raise ValueError("raw bytes required")
        if len(self.stdout) + len(self.stderr) > 65536:
            raise ValueError("combined retained output exceeded")
        if self.run_directory is not None:
            _path(self.run_directory)
        expected = (
            "REJECTED"
            if self.errors
            else "UNAVAILABLE"
            if self.unavailable or self.cleanup != "CONFIRMED"
            else "SYNTHETIC_OBSERVATION_COMPLETE"
        )
        if type(self.outcome) is not str or self.outcome != expected:
            raise ValueError("outcome contradicts known facts")

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def content_identity_only(self) -> bool:
        return True

    @property
    def historical_execution(self) -> bool:
        return False

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def historical_replay(self) -> str:
        return "UNAVAILABLE"


def _result(
    case: SyntheticCase,
    root: str | None = None,
    *,
    errors: tuple[str, ...] = (),
    unavailable: tuple[str, ...] = (),
    cleanup: str = "CONFIRMED",
    stdout: bytes = b"",
    stderr: bytes = b"",
) -> SyntheticResult:
    outcome = (
        "REJECTED"
        if errors
        else "UNAVAILABLE"
        if unavailable or cleanup != "CONFIRMED"
        else "SYNTHETIC_OBSERVATION_COMPLETE"
    )
    return SyntheticResult(case, outcome, errors, unavailable, cleanup, stdout, stderr, root)
