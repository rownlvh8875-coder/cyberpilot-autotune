"""Catch full-seal overclaims, object substitution and frame repair."""

import dataclasses
import hashlib
import json

import pytest

from compatibility.guest_input_seal.contracts import SealCapture, SealDecision, SealEvent
from compatibility.guest_input_seal.evaluation import evaluate
from compatibility.guest_input_seal.wire import capture_digest, parse_capture

ORIGINAL = hashlib.sha256(b"0123456789ABCDEF\n").hexdigest()
MUTATED = hashlib.sha256(b"X123456789ABCDEF\n").hexdigest()


def fixture(case="IS01"):
    # Hand-derived Linux6.12 masks/results, not the producer or evaluator.
    def snap(label, mask=47, digest=ORIGINAL, ino=10, err=0, mode=0o666):
        return ("SNAP", label, [1, ino, 17, digest, mask, err, mode])

    def op(label, result=0, err=0):
        return ("OP", label, [result, err])

    before = snap("before", 32)
    seal = [op("seal1"), snap("sealed")]
    bind = ("BIND", "read", [1, 10, 1, 10, 0])
    tail = [bind, snap("read")]
    cases = {
        "IS01": [
            before,
            *seal,
            op("write_original", -1, 1),
            op("write_dup", -1, 1),
            op("write_reopen", -1, 1),
            op("shrink", -1, 1),
            op("grow", -1, 1),
            op("map_shared", -1, 1),
            snap("after"),
            *tail,
        ],
        "IS02": [
            before,
            op("seal1", -1, 16),
            snap("failed", 32),
            ("LOCAL", "shared", [88]),
            snap("mutated", 32, MUTATED),
            op("unmap"),
            op("restore", 17),
            op("seal2"),
            snap("sealed"),
            *tail,
        ],
        "IS03": [
            before,
            op("seal_future"),
            snap("future", 55),
            ("LOCAL", "shared", [88]),
            snap("mutated", 55, MUTATED),
            op("write_original", -1, 1),
            op("map_shared", -1, 1),
            bind,
            snap("read", 55, MUTATED),
        ],
        "IS04": [
            before,
            *seal,
            op("seal_other"),
            snap("other", ino=11),
            ("BIND", "read", [1, 10, 1, 11, 0]),
            snap("read", ino=11),
        ],
        "IS05": [
            snap("before", 1, mode=0o644),
            op("chmod"),
            snap("chmod", 1, mode=0o444),
            ("CRED", "write", [65534, 65534, 1]),
            op("write_original", 1),
            snap("mutated", 1, MUTATED, mode=0o444),
            bind,
            snap("read", 1, MUTATED, mode=0o444),
        ],
        "IS06": [
            before,
            *seal,
            op("replace"),
            snap("replacement", 1, MUTATED, ino=11, mode=0o644),
            ("BIND", "read", [1, 10, 1, 11, 0]),
            snap("read", 1, MUTATED, ino=11, mode=0o644),
            snap("after"),
        ],
        "IS07": [before, *seal, ("LOCAL", "private", [88]), snap("after"), *tail],
        "IS08": [
            before,
            op("seal1", -1, 16),
            snap("failed", 32),
            op("unmap"),
            op("seal2"),
            snap("sealed"),
            *tail,
        ],
    }
    rows = [("BEGIN", case, ["guest-input-seal-v1"]), *cases[case], ("END", case, [])]
    return SealCapture(
        tuple(
            SealEvent(i, i + 1, kind, label, values) for i, (kind, label, values) in enumerate(rows)
        )
    )


@pytest.mark.parametrize(
    "case,full",
    [
        ("IS01", True),
        ("IS02", True),
        ("IS03", False),
        ("IS04", False),
        ("IS05", False),
        ("IS06", False),
        ("IS07", True),
        ("IS08", True),
    ],
)
def test_fixed_diagnostic_is_not_qualification(case, full):
    decision = evaluate(fixture(case))
    assert decision.scenario_recognized
    assert decision.object_seal_observed is full
    assert decision.overall == "BLOCKED"
    assert all(v is False for _, v in decision.permissions)
    assert decision.prohibited_operation_count is None


def test_copies_lists_and_rejects_mutation():
    values = [0, 0]
    event = SealEvent(0, 1, "OP", "unmap", values)
    values[0] = 9
    assert event.values == (0, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.label = "other"


def test_decision_is_defensively_immutable():
    reasons = ["diagnostic"]
    decision = SealDecision("IS01", False, False, reasons)
    reasons.append("not authority")
    assert decision.reasons == ("diagnostic",)
    with pytest.raises(ValueError):
        SealDecision("IS01", False, True, ())


def test_chmod_control_requires_unprivileged_write_context():
    events = list(fixture("IS05").events)
    i = next(i for i, e in enumerate(events) if e.kind == "CRED")
    events[i] = dataclasses.replace(events[i], values=[0, 0, 1])
    assert not evaluate(SealCapture(events)).scenario_recognized


def test_wrong_object_same_content_is_not_sealed_binding():
    capture = fixture()
    events = list(capture.events)
    position = next(i for i, e in enumerate(events) if e.kind == "BIND")
    events[position] = dataclasses.replace(events[position], values=[1, 10, 1, 11, 0])
    decision = evaluate(SealCapture(events))
    assert not decision.scenario_recognized
    assert not decision.object_seal_observed


@pytest.mark.parametrize(
    "kind,label,values",
    [
        ("OP", "x", [True, 0]),
        ("OP", "x", [-1, 0]),
        ("SNAP", "x", [1, 2, 17, ORIGINAL, None, 0, 0o666]),
        ("SNAP", "x", [1, 2, 17, ORIGINAL, 0, 22, 0o666]),
        ("LOCAL", "x", [float("nan")]),
        ("BIND", "read", [1, 10, 1, 10, -1]),
    ],
)
def test_invalid_scalar_or_unavailable_cohort(kind, label, values):
    with pytest.raises(ValueError):
        SealEvent(0, 1, kind, label, values)


def wire(capture):
    return "\n".join("SEAL " + json.dumps(dataclasses.asdict(e)) for e in capture.events)


def test_canonical_roundtrip_crlf_and_field_order():
    capture = fixture()
    assert parse_capture(wire(capture).replace("\n", "\r\n")) == capture
    reverse = "\n".join(
        "SEAL " + json.dumps(dict(reversed(list(dataclasses.asdict(e).items()))))
        for e in capture.events
    )
    assert capture_digest(parse_capture(reverse)) == capture_digest(capture)
    changed = list(capture.events)
    changed[1] = dataclasses.replace(changed[1], time_ns=100)
    with pytest.raises(ValueError):
        SealCapture(changed)


@pytest.mark.parametrize("separator", ["\v", "\f", "\x85", "\u2028", " prefix "])
def test_nonphysical_separator_not_repaired(separator):
    with pytest.raises(ValueError):
        parse_capture(wire(fixture()).replace("\n", separator, 1))


@pytest.mark.parametrize(
    "mutation", ["truncated", "duplicate", "extra", "sequence", "unknown", "nonfinite"]
)
def test_malformed_frames_rejected(mutation):
    text = wire(fixture())
    if mutation == "truncated":
        text = text.rsplit("\n", 1)[0]
    elif mutation == "duplicate":
        text = text.replace('"seq": 0', '"seq": 0, "seq": 0', 1)
    elif mutation == "extra":
        text += "\n" + text.split("\n")[0]
    elif mutation == "sequence":
        text = text.replace('"seq": 1,', '"seq": 0,', 1)
    elif mutation == "unknown":
        text = text.replace('"kind": "BEGIN"', '"kind": "ERROR"', 1)
    else:
        text = text.replace('"time_ns": 1,', '"time_ns": NaN,', 1)
    with pytest.raises(ValueError):
        parse_capture(text)


@pytest.mark.parametrize(
    "case,label,values",
    [
        ("IS01", "sealed", [1, 10, 17, ORIGINAL, 55, 0, 0o666]),
        ("IS02", "failed", [1, 10, 17, ORIGINAL, 47, 0, 0o666]),
        ("IS03", "mutated", [1, 10, 17, ORIGINAL, 55, 0, 0o666]),
        ("IS07", "after", [1, 10, 17, MUTATED, 47, 0, 0o666]),
    ],
)
def test_wrong_seal_epoch_or_backing_bytes_fail(case, label, values):
    events = list(fixture(case).events)
    i = next(i for i, e in enumerate(events) if e.label == label)
    events[i] = dataclasses.replace(events[i], values=values)
    assert not evaluate(SealCapture(events)).scenario_recognized


@pytest.mark.parametrize(
    "changes",
    [
        {"seq": -1},
        {"time_ns": 0},
        {"label": "../escape"},
        {"values": {}},
        {"kind": "BEGIN", "label": "IS99", "values": ["guest-input-seal-v1"]},
        {"kind": "END", "label": "IS99", "values": []},
        {"kind": "SNAP", "values": [1, 2, 17, "bad", 47, 0, 0o666]},
        {"kind": "LOCAL", "values": [256]},
    ],
)
def test_event_boundary_rejects_unbound_shape(changes):
    args = {"seq": 0, "time_ns": 1, "kind": "OP", "label": "unmap", "values": [0, 0]}
    args.update(changes)
    with pytest.raises(ValueError):
        SealEvent(**args)


@pytest.mark.parametrize("variant", ["short", "untyped", "inner_boundary", "mismatched_end"])
def test_capture_boundaries(variant):
    events = list(fixture().events)
    if variant == "short":
        events = events[:2]
    elif variant == "untyped":
        events[1] = object()
    elif variant == "inner_boundary":
        events[1] = SealEvent(1, 2, "BEGIN", "IS01", ["guest-input-seal-v1"])
    else:
        events[-1] = dataclasses.replace(events[-1], label="IS02")
    with pytest.raises(ValueError):
        SealCapture(events)


def test_missing_snapshot_or_equal_substitute_identity_not_recognized():
    events = list(fixture().events)
    events[1] = SealEvent(1, 2, "OP", "unmap", [0, 0])
    assert not evaluate(SealCapture(events)).scenario_recognized
    events = list(fixture("IS04").events)
    for i, e in enumerate(events):
        if e.label in ("other", "read"):
            values = list(e.values)
            if e.kind == "BIND":
                values[3] = 10
            else:
                values[1] = 10
            events[i] = dataclasses.replace(e, values=values)
    assert not evaluate(SealCapture(events)).scenario_recognized


def test_unknown_does_not_hash_as_zero_and_identity_changes_digest():
    events = list(fixture("IS05").events)
    values = list(events[1].values)
    values[4:6] = [None, 22]
    events[1] = dataclasses.replace(events[1], values=values)
    original = capture_digest(SealCapture(events))
    values[4:6] = [0, 0]
    events[1] = dataclasses.replace(events[1], values=values)
    assert capture_digest(SealCapture(events)) != original


@pytest.mark.parametrize(
    "text",
    [None, "x" * (1024 * 1024 + 1), "SEAL {}", "prefix SEAL {}", "SEAL " + "[" * 1100 + "]" * 1100],
)
def test_wire_bounds_shape_and_deep_nesting(text):
    with pytest.raises(ValueError):
        parse_capture(text)


def test_nonprotocol_console_lines_ignored_but_record_overflow_not_repaired():
    assert parse_capture("boot noise\n" + wire(fixture()) + "\nshutdown") == fixture()
    text = "\n".join(
        "SEAL " + json.dumps(dataclasses.asdict(SealEvent(i, i + 1, "OP", "unmap", [0, 0])))
        for i in range(65)
    )
    with pytest.raises(ValueError, match="overflow"):
        parse_capture(text)


def test_parser_recursion_is_a_contract_error():
    text = "SEAL " + "[" * 10000 + "]" * 10000
    with pytest.raises(ValueError, match="nesting"):
        parse_capture(text)
