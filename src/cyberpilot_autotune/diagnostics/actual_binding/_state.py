"""Pure reported state checks; no clock acquisition or process execution."""

from typing import cast

from ._codec import _DecodedDocuments
from ._linkage import _CheckResult, facts, part
from ._schema import JsonObject
from .values import PrelaunchExpectedReference

type ClockKey = tuple[str, str, int]
TIMED_ROLES = ("preflight", "intent", "exit", "snapshot")
TIME_FIELDS = (
    ("preflight", "mono_ns"),
    ("intent", "mono_ns"),
    ("exit", "launch_before_ns"),
    ("exit", "launch_after_ns"),
    ("exit", "exit_observed_ns"),
    ("exit", "mono_ns"),
    ("snapshot", "mono_ns"),
)


def _clock_key(context: JsonObject) -> ClockKey | None:
    if context["context_status"] != "REPORTED":
        return None
    return (
        cast(str, context["cohort_sha256"]),
        cast(str, context["context_material_sha256"]),
        cast(int, context["generation"]),
    )


def _process_issues(p: JsonObject) -> list[str]:
    issues = []
    kind, term, code = p["observation_kind"], p["termination"], p["returncode"]
    if kind == "UNAVAILABLE":
        issues.append("MISSING_CONTEXT")
        if (
            any(p[k] is not None for k in ("pid", "process_identity_sha256", "returncode"))
            or term != "UNKNOWN"
        ):
            issues.append("PROCESS_STATE_CONFLICT")
    if term == "UNKNOWN":
        issues.append("MISSING_CONTEXT")
        if code is not None:
            issues.append("PROCESS_STATE_CONFLICT")
    elif term == "NOT_STARTED":
        issues.append("MISSING_CONTEXT")
        if (
            any(p[k] is not None for k in ("pid", "process_identity_sha256", "returncode"))
            or kind == "DIRECT_REAP_REPORTED"
        ):
            issues.append("PROCESS_STATE_CONFLICT")
    elif code is None:
        issues.append("MISSING_CONTEXT")
    elif (term == "EXITED" and cast(int, code) < 0) or (
        term == "SIGNALLED" and cast(int, code) >= 0
    ):
        issues.append("PROCESS_STATE_CONFLICT")
    return issues


def check_state(decoded: _DecodedDocuments, pre: PrelaunchExpectedReference | None) -> _CheckResult:
    issues: list[str] = []
    skipped: list[str] = []
    if not decoded.container_valid:
        return facts([], ["process_state", "clocks", "completeness"])
    keys: dict[str, ClockKey | None] = {}
    for role in TIMED_ROLES:
        header = part(decoded, role, "header")
        if header is None:
            skipped.append("clocks")
            continue
        keys[role] = _clock_key(cast(JsonObject, header["host_clock_context"]))
        if keys[role] is None:
            issues.append("CLOCK_CONTEXT_UNAVAILABLE")
            skipped.append("clocks")
    early = [keys[r] for r in ("preflight", "intent") if keys.get(r) is not None]
    if len(early) == 2 and early[0] != early[1]:
        issues.append("CONTEXT_MISMATCH")
    if pre is None or pre.host_clock_cohort_sha256 is None or pre.host_clock_generation is None:
        skipped.append("clocks")
    if pre is not None:
        for key in early:
            assert key is not None
            if (
                pre.host_clock_cohort_sha256 is not None and key[0] != pre.host_clock_cohort_sha256
            ) or (pre.host_clock_generation is not None and key[2] != pre.host_clock_generation):
                issues.append("CONTEXT_MISMATCH")
    known_keys = {key for key in keys.values() if key is not None}
    if len(known_keys) > 1 and any(keys.get(r) is not None for r in ("exit", "snapshot")):
        issues.append("CLOCK_CONTEXT_CHANGED")
    last: dict[ClockKey, int] = {}
    for role, field in TIME_FIELDS:
        body = part(decoded, role)
        if body is None:
            skipped.append("clocks")
            continue
        value = body[field]
        if value is None:
            issues.append("CLOCK_CONTEXT_UNAVAILABLE")
            skipped.append("clocks")
            continue
        key = keys[role]
        if key is not None:
            number = cast(int, value)
            if key in last and number < last[key]:
                issues.append("TIME_REVERSED")
            last[key] = max(last.get(key, number), number)

    exit_body = part(decoded, "exit")
    if exit_body is None:
        skipped.append("process_state")
    else:
        processes = [
            cast(JsonObject, exit_body[k]) for k in ("cli_observation", "qemu_observation")
        ]
        for p in processes:
            found = _process_issues(p)
            issues.extend(found)
            if "MISSING_CONTEXT" in found:
                skipped.append("process_state")
        outcome, failure = exit_body["capture_outcome"], exit_body["failure_stage"]
        if outcome == "COMPLETE_REPORTED":
            if failure != "NONE" or any(p["termination"] == "NOT_STARTED" for p in processes):
                issues.append("CAPTURE_STATE_CONFLICT")
        else:
            issues.append("MISSING_CONTEXT")
            if failure == "NONE":
                issues.append("CAPTURE_STATE_CONFLICT")
        if any(
            v != "FINALIZED_REPORTED"
            for v in cast(JsonObject, exit_body["raw_close_states"]).values()
        ):
            issues.append("MISSING_CONTEXT")
    if len(decoded.documents) != 6 or any(
        r in ("MISSING_CONTEXT", "CLOCK_CONTEXT_UNAVAILABLE") for r in issues
    ):
        skipped.append("completeness")
    return facts(issues, skipped)
