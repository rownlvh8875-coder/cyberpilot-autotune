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
    # Partial identities can bridge multiple buckets. Preserve contradictions
    # across the entire equality-connected component without filling None.
    parents = {key: key for key in actual}

    def event_root(key: tuple[str, str]) -> tuple[str, str]:
        while parents[key] != key:
            key = parents[key]
        return key

    for members in events.values():
        for key in members[1:]:
            parents[event_root(key)] = event_root(members[0])
    components: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for key in actual:
        components.setdefault(event_root(key), []).append(key)
    for members in components.values():
        if len(members) < 2:
            continue
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
            candidates = []
            for key in members:
                value = notes[key][field]
                # None is a known absence for a present batch context,not a
                # missing command/attempt. Never infer a missing command context.
                if (
                    field in ("context.command_id", "context.attempt")
                    and value is None
                    and actual[key].context is not None
                    and scopes[key] is None
                ):
                    value = ("KNOWN_BATCH_ABSENCE",)
                candidates.append((key, field, value))
            conflicts(candidates, "SOURCE_EVENT_ALIAS")

    def timed_groups(members: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
        clocks: dict[str, list[tuple[str, str]]] = {}
        for key in members:
            note = notes[key]
            clock = note["context.epoch.clock_domain"]
            if clock is not None and note["event_time_ns"] is not None:
                clocks.setdefault(clock, []).append(key)
        return clocks

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
        for comparable in timed_groups(members).values():
            sequences: dict[int, list[tuple[str, str]]] = {}
            for key in comparable:
                seq = notes[key]["sequence"]
                if seq is not None:
                    sequences.setdefault(seq, []).append(key)
            highest: int | None = None
            for seq in sorted(sequences):
                for key in sequences[seq]:
                    if highest is not None and notes[key]["event_time_ns"] < highest:
                        report("TIME_ORDER_INVALID", key, "event_time_ns")
                current = max(notes[key]["event_time_ns"] for key in sequences[seq])
                highest = current if highest is None else max(highest, current)
    for scope, members in groups.items():
        if scope is None:
            continue
        for comparable in timed_groups(members).values():
            maxima: dict[int, int] = {}
            for key in comparable:
                note = notes[key]
                if note["stage"] in _ORDER:
                    rank, time = _ORDER.index(note["stage"]), note["event_time_ns"]
                    maxima[rank] = max(maxima.get(rank, time), time)
            for key in comparable:
                note = notes[key]
                if note["stage"] in _ORDER:
                    rank = _ORDER.index(note["stage"])
                    if any(r < rank and time > note["event_time_ns"] for r, time in maxima.items()):
                        report("STAGE_ORDER_INVALID", key, "event_time_ns")
    return CaptureAlignmentDecision(tuple(errors), tuple(unavailable))
