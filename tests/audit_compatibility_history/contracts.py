"""Immutable neutral claims and closed wire encoding;never authority or an executor."""

import json
from dataclasses import dataclass, fields
from hashlib import sha256
from typing import Any, cast

PROFILE = "ENTRY_HISTORICAL_SOURCE_AUDIT_V1"
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
BLOCKERS = (
    "ACTUAL_Q_I",
    "APPLICATION_NOT_AUTHORIZED",
    "ENTRY_GUARD_INTEGRATION",
    "EXACT_I_CI",
    "HISTORICAL_REPLAY",
    "SOURCE_CAPTURE_ATOMICITY",
    "STACK_ADOPTION",
)


def need(condition: bool) -> None:
    if not condition:
        raise ValueError("invalid H1 supplied claim")


def text(value: Any) -> None:
    need(type(value) is str and bool(value) and not any(c in value for c in "\0\r\n"))
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise ValueError("invalid H1 text") from error


def hex_value(value: Any, size: int) -> None:
    need(type(value) is str and len(value) == size and all(c in "0123456789abcdef" for c in value))


def path(value: Any) -> None:
    text(value)
    need(
        not any(c in value for c in "\\:*?[]")
        and all(p not in ("", ".", "..") for p in value.split("/"))
    )


def strings(value: Any) -> None:
    need(type(value) is tuple)
    for item in value:
        text(item)


def reasons(value: Any) -> None:
    strings(value)
    need(value == tuple(sorted(set(value))))


def children(value: Any, cls: type[Any]) -> None:
    need(type(value) is tuple)
    for item in value:
        need(type(item) is cls)
        cls.__post_init__(item)


class _Blocked:
    __slots__ = ()

    @property
    def status(self) -> str:
        return "BLOCKED"

    @property
    def permissions(self) -> tuple[tuple[str, bool], ...]:
        return PERMISSIONS

    @property
    def integrated_admission(self) -> bool:
        return False

    @property
    def content_identity_only(self) -> bool:
        return True

    @property
    def atomicity(self) -> str:
        return "NOT_ESTABLISHED"

    @property
    def remaining_blockers(self) -> tuple[str, ...]:
        return BLOCKERS


@dataclass(frozen=True, slots=True)
class SourcePin:
    revision: str
    tree: str

    def __post_init__(self) -> None:
        hex_value(self.revision, 40)
        hex_value(self.tree, 40)


@dataclass(frozen=True, slots=True)
class OriginPin:
    module: str
    path: str
    sha256: str
    archive_member: str | None

    def __post_init__(self) -> None:
        text(self.module)
        need(all(p.isidentifier() for p in self.module.split(".")))
        path(self.path)
        hex_value(self.sha256, 64)
        if self.archive_member is not None:
            path(self.archive_member)


@dataclass(frozen=True, slots=True)
class CoverageCounts:
    path: str
    statements: int
    covered: int
    branches: int
    covered_branches: int

    def __post_init__(self) -> None:
        path(self.path)
        need(
            all(
                type(x) is int and x >= 0
                for x in (self.statements, self.covered, self.branches, self.covered_branches)
            )
        )
        need(self.covered <= self.statements and self.covered_branches <= self.branches)


@dataclass(frozen=True, slots=True)
class CaseOutcome:
    nodeid: str
    setup: str
    call: str
    teardown: str

    def __post_init__(self) -> None:
        text(self.nodeid)
        for value in (self.setup, self.call, self.teardown):
            need(
                type(value) is str
                and value
                in ("PASSED", "FAILED", "SKIPPED", "XFAIL", "XPASS", "NOT_RUN", "UNAVAILABLE")
            )


@dataclass(frozen=True, slots=True)
class HistoricalCommandPolicy:
    command_id: str
    cohort_id: str
    kind: str
    entrypoint: str
    argv: tuple[str, ...]
    expected_nodeids: tuple[str, ...] | None
    origins: tuple[OriginPin, ...] | None
    coverage_groups: tuple[tuple[str, tuple[str, ...]], ...] | None

    def __post_init__(self) -> None:
        for value in (self.command_id, self.cohort_id, self.entrypoint):
            text(value)
        need(type(self.kind) is str and self.kind in ("PYTEST", "AUDIT"))
        strings(self.argv)
        if self.expected_nodeids is not None:
            strings(self.expected_nodeids)
        if self.origins is not None:
            children(self.origins, OriginPin)
        if self.coverage_groups is not None:
            need(type(self.coverage_groups) is tuple)
            for row in self.coverage_groups:
                need(type(row) is tuple and len(row) == 2)
                text(row[0])
                strings(row[1])
                for item in row[1]:
                    path(item)


@dataclass(frozen=True, slots=True)
class HistoricalCommandRecord:
    command_id: str
    cohort_id: str
    run_id: str
    subject: SourcePin | None
    entrypoint: str | None
    argv: tuple[str, ...] | None
    exit_code: int | None
    collected_nodeids: tuple[str, ...] | None
    outcomes: tuple[CaseOutcome, ...] | None
    origins: tuple[OriginPin, ...] | None
    coverage: tuple[CoverageCounts, ...] | None
    coverage_artifact_sha256: str | None
    coverage_producer_command_id: str | None
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        text(self.command_id)
        text(self.cohort_id)
        hex_value(self.run_id, 32)
        if self.subject is not None:
            children((self.subject,), SourcePin)
        if self.entrypoint is not None:
            text(self.entrypoint)
        for value in (self.argv, self.collected_nodeids):
            if value is not None:
                strings(value)
        need(self.exit_code is None or type(self.exit_code) is int)
        for nested_values, cls in (
            (self.outcomes, CaseOutcome),
            (self.origins, OriginPin),
            (self.coverage, CoverageCounts),
        ):
            if nested_values is not None:
                children(nested_values, cls)
        if self.coverage_artifact_sha256 is not None:
            hex_value(self.coverage_artifact_sha256, 64)
        if self.coverage_producer_command_id is not None:
            text(self.coverage_producer_command_id)
        reasons(self.errors)
        reasons(self.unavailable)


@dataclass(frozen=True, slots=True)
class HistoricalReplayPolicy(_Blocked):
    profile_id: str
    cohorts: tuple[tuple[str, SourcePin], ...]
    commands: tuple[HistoricalCommandPolicy, ...]
    executor_revision: str | None
    toolchain_digest: str | None
    case_inventory_digest: str | None
    control_profile_digest: str | None
    budget_profile_digest: str | None

    def __post_init__(self) -> None:
        text(self.profile_id)
        need(type(self.cohorts) is tuple)
        for item in self.cohorts:
            need(type(item) is tuple and len(item) == 2)
            text(item[0])
            children((item[1],), SourcePin)
        children(self.commands, HistoricalCommandPolicy)
        if self.executor_revision is not None:
            hex_value(self.executor_revision, 40)
        for value in (
            self.toolchain_digest,
            self.case_inventory_digest,
            self.control_profile_digest,
            self.budget_profile_digest,
        ):
            if value is not None:
                hex_value(value, 64)

    @property
    def content_digest(self) -> str:
        children((self,), HistoricalReplayPolicy)
        return sha256(_canonical("historical-replay-policy-v1", self)).hexdigest()


@dataclass(frozen=True, slots=True)
class HistoricalReplayRecord(_Blocked):
    profile_id: str
    run_id: str
    policy_digest: str | None
    commands: tuple[HistoricalCommandRecord, ...]
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        text(self.profile_id)
        hex_value(self.run_id, 32)
        if self.policy_digest is not None:
            hex_value(self.policy_digest, 64)
        children(self.commands, HistoricalCommandRecord)
        reasons(self.errors)
        reasons(self.unavailable)

    @property
    def content_digest(self) -> str:
        return sha256(canonical_record(self)).hexdigest()


@dataclass(frozen=True, slots=True)
class HistoricalReplayDecision(_Blocked):
    errors: tuple[str, ...]
    unavailable: tuple[str, ...]

    def __post_init__(self) -> None:
        reasons(self.errors)
        reasons(self.unavailable)

    @property
    def consistency(self) -> str:
        return (
            "REJECTED"
            if self.errors
            else "UNAVAILABLE"
            if self.unavailable
            else "STRUCTURAL_RECORD_MATCH"
        )


def _canonical(schema: str, value: Any) -> bytes:
    def encode(item: Any) -> Any:
        if item is None or type(item) in (str, int):
            return item
        if type(item) is tuple:
            return [encode(v) for v in item]
        need(
            type(item)
            in (
                SourcePin,
                OriginPin,
                CoverageCounts,
                CaseOutcome,
                HistoricalCommandPolicy,
                HistoricalCommandRecord,
                HistoricalReplayPolicy,
                HistoricalReplayRecord,
            )
        )
        return {field.name: encode(getattr(item, field.name)) for field in fields(item)}

    return json.dumps(
        {"schema": schema, "record": encode(value)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()


def canonical_record(record: HistoricalReplayRecord) -> bytes:
    children((record,), HistoricalReplayRecord)
    return _canonical("historical-replay-record-v1", record)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        need(key not in result)
        result[key] = value
    return result


def _number(value: str) -> Any:
    raise ValueError("noninteger H1 wire number")


def _array(value: Any) -> tuple[Any, ...]:
    need(type(value) is list)
    return tuple(value)


def _decode(cls: type[Any], value: Any) -> Any:
    need(type(value) is dict and set(value) == {f.name for f in fields(cls)})
    data = dict(value)
    if cls is HistoricalReplayRecord:
        data["commands"] = tuple(
            _decode(HistoricalCommandRecord, v) for v in _array(data["commands"])
        )
    if cls is HistoricalCommandRecord:
        if data["subject"] is not None:
            data["subject"] = _decode(SourcePin, data["subject"])
        for name, child in (
            ("outcomes", CaseOutcome),
            ("origins", OriginPin),
            ("coverage", CoverageCounts),
        ):
            if data[name] is not None:
                data[name] = tuple(_decode(child, v) for v in _array(data[name]))
        for name in ("argv", "collected_nodeids"):
            if data[name] is not None:
                data[name] = _array(data[name])
    if cls in (HistoricalReplayRecord, HistoricalCommandRecord):
        for name in ("errors", "unavailable"):
            data[name] = _array(data[name])
    return cls(**data)


def decode_record(raw: bytes) -> HistoricalReplayRecord:
    need(type(raw) is bytes)
    try:
        value = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_pairs,
            parse_float=_number,
            parse_constant=_number,
        )
        need(
            type(value) is dict
            and set(value) == {"schema", "record"}
            and value["schema"] == "historical-replay-record-v1"
        )
        return cast(HistoricalReplayRecord, _decode(HistoricalReplayRecord, value["record"]))
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid H1 wire encoding/depth") from error
