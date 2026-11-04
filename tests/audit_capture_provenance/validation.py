"""Assess supplied metadata only. A consistent packet proves no physical capture."""

from typing import Any

from .contracts import (
    CATALOG,
    CaptureAlignmentDecision,
    CaptureIssue,
    CaptureWitness,
    CaptureWitnessBundle,
    validate,
)

_ORDER = (
    "BOUNDARY_READY",
    "LIMITS_APPLIED",
    "PRE_RELEASE",
    "COMMAND_START",
    "COMMAND_FINISH",
    "BATCH_FINISH",
)
_EPOCH_FIELDS = ("run_id", "policy_digest", "clock_domain")
_CONTEXT_FIELDS = ("command_id", "attempt", "boundary_digest", "boundary_generation")


def _flat(witness: CaptureWitness) -> dict[str, Any]:
    result = {
        name: getattr(witness, name)
        for name in (
            "source_id",
            "event_id",
            "sequence",
            "event_time_ns",
            "stage",
            "content_digest",
        )
    }
    context = witness.context
    epoch = None if context is None else context.epoch
    result.update(
        ("context." + f, None if context is None else getattr(context, f)) for f in _CONTEXT_FIELDS
    )
    result.update(
        ("context.epoch." + f, None if epoch is None else getattr(epoch, f)) for f in _EPOCH_FIELDS
    )
    return result


def assess_capture_bundle(bundle: CaptureWitnessBundle) -> CaptureAlignmentDecision:
    validate(bundle, CaptureWitnessBundle)
    errors: list[CaptureIssue] = []
    unavailable: list[CaptureIssue] = []
    witnesses = bundle.witnesses
    notes = {(w.target_path, w.role): _flat(w) for w in witnesses}
    actual = {(w.target_path, w.role): w for w in witnesses}
    scopes = {key: command for key, _, command in CATALOG}
    root = ("@bundle", "BUNDLE")

    def report(code: str, key: tuple[str, str], field: str, *, missing: bool = False) -> None:
        (unavailable if missing else errors).append(CaptureIssue(code, *key, field))

    def conflicts(candidates: list[tuple[tuple[str, str], str, Any]], code: str) -> None:
        known = [(key, field, value) for key, field, value in candidates if value is not None]
        if len({value for _, _, value in known}) > 1:
            for key, field, _ in known:
                report(code, key, field)

    if bundle.epoch is None:
        report("EPOCH_UNAVAILABLE", root, "epoch", missing=True)
    for field in _EPOCH_FIELDS:
        value = None if bundle.epoch is None else getattr(bundle.epoch, field)
        if bundle.epoch is not None and value is None:
            report("EPOCH_UNAVAILABLE", root, "epoch." + field, missing=True)
        code = "CLOCK_DOMAIN_MISMATCH" if field == "clock_domain" else "EPOCH_MISMATCH"
        conflicts(
            [(root, "epoch." + field, value)]
            + [
                (key, "context.epoch." + field, note["context.epoch." + field])
                for key, note in notes.items()
            ],
            code,
        )
    begin, end = bundle.capture_begin_ns, bundle.capture_end_ns
    for name in ("capture_begin_ns", "capture_end_ns"):
        if getattr(bundle, name) is None:
            report("CAPTURE_WINDOW_UNAVAILABLE", root, name, missing=True)
    if begin is not None and end is not None and end < begin:
        report("TIME_ORDER_INVALID", root, "capture_end_ns")

    groups: dict[str | None, list[tuple[str, str]]] = {}
    sources: dict[str, list[tuple[str, str]]] = {}
    events: dict[Any, list[tuple[str, str]]] = {}
    for key, _, _ in CATALOG:
        if key not in actual:
            report("WITNESS_MISSING", key, "witnesses", missing=True)
    outcomes = {
        "NEGATIVE_CLAIM": "NEGATIVE_CLAIM",
        "ERROR_CLAIM": "PRODUCER_REPORTED_ERROR",
        "UNAVAILABLE_CLAIM": "WITNESS_UNAVAILABLE",
    }
    for key, w in actual.items():
        note, scope = notes[key], scopes[key]
        groups.setdefault(scope, []).append(key)
        if w.outcome in outcomes:
            report(outcomes[w.outcome], key, "outcome", missing=w.outcome == "UNAVAILABLE_CLAIM")
        context = w.context
        if context is None:
            report("CONTEXT_UNAVAILABLE", key, "context", missing=True)
        else:
            if context.epoch is None:
                report("CONTEXT_UNAVAILABLE", key, "context.epoch", missing=True)
            else:
                for field in _EPOCH_FIELDS:
                    if getattr(context.epoch, field) is None:
                        report("CONTEXT_UNAVAILABLE", key, "context.epoch." + field, missing=True)
            if scope is None:
                for field in ("command_id", "attempt"):
                    if getattr(context, field) is not None:
                        report("COMMAND_MISMATCH", key, "context." + field)
            else:
                for field in ("command_id", "attempt"):
                    if getattr(context, field) is None:
                        report("CONTEXT_UNAVAILABLE", key, "context." + field, missing=True)
                if context.command_id is not None and context.command_id != scope:
                    report("COMMAND_MISMATCH", key, "context.command_id")
            for field in ("boundary_digest", "boundary_generation"):
                if getattr(context, field) is None:
                    report("CONTEXT_UNAVAILABLE", key, "context." + field, missing=True)
        for field in ("source_id", "event_id", "sequence", "event_time_ns"):
            if note[field] is None:
                report("EVENT_IDENTITY_UNAVAILABLE", key, field, missing=True)
        if w.content_digest is None:
            report("CONTENT_REFERENCE_UNAVAILABLE", key, "content_digest", missing=True)
        if w.source_id is not None:
            sources.setdefault(w.source_id, []).append(key)
            if w.sequence is not None:
                events.setdefault(("source", w.source_id, w.sequence), []).append(key)
        if w.event_id is not None:
            events.setdefault(("event", w.event_id), []).append(key)

    for members in groups.values():
        for field in ("context.attempt", "context.boundary_digest", "context.boundary_generation"):
            conflicts([(key, field, notes[key][field]) for key in members], "CONTEXT_CHANGED")
    boundaries: dict[str, list[tuple[str, str]]] = {}
    for key, note in notes.items():
        if note["context.boundary_digest"] is not None:
            boundaries.setdefault(note["context.boundary_digest"], []).append(key)
    for members in boundaries.values():
        if len({scopes[key] for key in members}) > 1:
            for key in members:
                report("BOUNDARY_REUSE", key, "context.boundary_digest")
    for members in events.values():
        for field in (
            "source_id",
            "event_id",
            "sequence",
            "event_time_ns",
            "stage",
            "content_digest",
            *("context." + f for f in _CONTEXT_FIELDS),
            *("context.epoch." + f for f in _EPOCH_FIELDS),
        ):
            conflicts([(key, field, notes[key][field]) for key in members], "SOURCE_EVENT_ALIAS")

    def comparable(left: dict[str, Any], right: dict[str, Any]) -> bool:
        clock = left["context.epoch.clock_domain"]
        return clock is not None and clock == right["context.epoch.clock_domain"]

    root_clock = None if bundle.epoch is None else bundle.epoch.clock_domain
    for key, note in notes.items():
        time = note["event_time_ns"]
        if (
            root_clock is not None
            and note["context.epoch.clock_domain"] == root_clock
            and time is not None
        ):
            if (begin is not None and time < begin) or (end is not None and time > end):
                report("EVENT_OUTSIDE_CAPTURE_WINDOW", key, "event_time_ns")
    for members in sources.values():
        for left_key in members:
            a = notes[left_key]
            for right_key in members:
                b = notes[right_key]
                if (
                    comparable(a, b)
                    and a["sequence"] is not None
                    and b["sequence"] is not None
                    and a["event_time_ns"] is not None
                    and b["event_time_ns"] is not None
                    and a["sequence"] < b["sequence"]
                    and a["event_time_ns"] > b["event_time_ns"]
                ):
                    report("TIME_ORDER_INVALID", right_key, "event_time_ns")
    for scope, members in groups.items():
        if scope is None:
            continue
        for left_key in members:
            a = notes[left_key]
            for right_key in members:
                b = notes[right_key]
                if (
                    a["stage"] in _ORDER
                    and b["stage"] in _ORDER
                    and _ORDER.index(a["stage"]) < _ORDER.index(b["stage"])
                    and comparable(a, b)
                    and a["event_time_ns"] is not None
                    and b["event_time_ns"] is not None
                    and a["event_time_ns"] > b["event_time_ns"]
                ):
                    report("STAGE_ORDER_INVALID", right_key, "event_time_ns")
    return CaptureAlignmentDecision(tuple(errors), tuple(unavailable))
