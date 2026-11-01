"""Synthetic test bytes, not actual guest captures or observed provenance."""

import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, replace

import pytest


def api():
    return (
        importlib.import_module("tests.deny_fd_v2.contracts"),
        importlib.import_module("tests.deny_fd_v2.wire"),
        importlib.import_module("tests.deny_fd_v2.validation"),
    )


def vector(*, expected=(0,), observed=(0, 3), causes=(3,), outcome=None, subject=0, case="DFD01"):
    rows = []

    def row(kind, *values):
        seq = len(rows) + 1
        rows.append([seq, seq * 100, kind, *values])
        return seq

    row(
        "BEGIN",
        "guest-data-fd-denial-observed-v2",
        "c" * 32,
        "a" * 40,
        "b" * 64,
        "GUEST_MONOTONIC_NS",
        "OBSERVED_UNTRUSTED",
        case,
    )
    row("POLICY", 1, subject, len(expected))
    for fd in expected:
        row("EXPECT", 1, fd)
    row("BIRTH", 1, 0)
    refs = {fd: row("FD", 1, "PRE_EXEC_INVENTORY", 1, 0, fd, None) for fd in observed}
    row("SNAP", 1, "PRE_EXEC_INVENTORY", 1, 0, 1, len(observed), 1, 65534, 65534, 1, None, None)
    if outcome is None:
        for fd in causes:
            row("CAUSE", 1, fd, refs.get(fd, 0))
        row("DENY", 1, "PRE_EXEC_INVENTORY", 1, 0, 1, "UNEXPECTED_FD", None, len(causes))
    else:
        row("RESULT", 1, "PRE_EXEC_INVENTORY", 1, 0, 1, outcome)
    row("REAP", 1, 0, "SIGNALLED", 9)
    row("END", 1, 0, None)
    return rows


def encoded(rows=None):
    if rows is None:
        rows = vector()
    return (
        b"boot noise\nDFD2_EXEC\n"
        + b"".join(
            b"DFD2 " + json.dumps(row, separators=(",", ":")).encode() + b"\n" for row in rows
        )
        + b"DFD2_PROBE_EXIT=0\nDFD2_DONE\nboot done\n"
    )


def test_decoder_api_must_exist():
    assert importlib.util.find_spec("tests.deny_fd_v2") is not None


def test_flat_wire_and_crlf_are_equivalent_without_promoting_test_bytes():
    c, w, v = api()
    capture = w.decode(encoded())
    assert w.decode(encoded().replace(b"\n", b"\r\n")) == capture
    assert len(capture.events) == 11
    assert capture.events[7].values == (1, 3, 6)
    assert v.check_inventory(capture).outcome == "WIRE_DIAGNOSTIC_CONSISTENT"
    assert v.check_inventory(capture).status == "BLOCKED"
    assert len(v.check_inventory(capture).permissions) == 9
    assert all(value is False for _, value in v.check_inventory(capture).permissions)
    assert not hasattr(capture, "application_authorized")
    with pytest.raises(FrozenInstanceError):
        capture.events = ()
    with pytest.raises(FrozenInstanceError):
        capture.events[0].seq = 0
    values = list(capture.events[0].values)
    event = c.Event(1, 100, "BEGIN", values)
    values[0] = "changed"
    assert event == capture.events[0]
    events = list(capture.events)
    copied = c.Capture(events)
    events.clear()
    assert copied == capture


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b[:-1],
        lambda b: b.replace(b"DFD2_EXEC\n", b"DFD2_EXEC\nDFD2_EXEC\n"),
        lambda b: b.replace(b"DFD2_PROBE_EXIT=0", b"DFD2_PROBE_EXIT=2"),
        lambda b: b.replace(b"DFD2_DONE", b"noise\nDFD2_DONE"),
        lambda b: b.replace(b"DFD2_DONE\n", b""),
        lambda b: b.replace(b"DFD2 [", b"HFD [", 1),
        lambda b: b.replace(b"boot noise", b"HFD_EXEC"),
        lambda b: b + b"DFD2 stray\n",
        lambda b: b.replace(b"DFD2 [", b"DFD2 \v[", 1),
        lambda b: b.replace(b"DFD2 [", b"DFD2 \f[", 1),
        lambda b: b.replace(b"DFD2 [", b"DFD2 \xff[", 1),
        lambda b: b.replace(b"DFD2 [", b"DFD2 {}", 1),
        lambda b: b.replace(b"DFD2 [", b"DFD2 " + b" " * 4096 + b"[", 1),
        lambda b: b"x" * (1024 * 1024) + b,
        lambda b: b.replace(b"DFD2_EXEC", b"DFD2_EXEC\r\r"),
    ],
)
def test_invalid_physical_framing_is_not_repaired(mutate):
    with pytest.raises(ValueError):
        api()[1].decode(mutate(encoded()))


@pytest.mark.parametrize("value", (None, "wire", bytearray(b"wire"), b"", b"\n"))
def test_input_must_be_bounded_physical_bytes(value):
    with pytest.raises(ValueError):
        api()[1].decode(value)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw.replace(b"]\n", b"]\r\r\n", 1),
        lambda raw: raw.replace(b"[1,100,", b"[1,\r100,", 1),
    ],
)
def test_event_rows_reject_forbidden_carriage_returns(mutate):
    with pytest.raises(ValueError):
        api()[1].decode(mutate(encoded()))


@pytest.mark.parametrize(
    "index,value",
    [
        (0, 0),
        (0, -1),
        (0, True),
        (0, 1.0),
        (0, 2**64),
        (1, -1),
        (1, False),
        (1, 1.0),
        (1, 2**64),
        (2, "UNKNOWN"),
        (2, None),
        (3, "v1"),
        (4, "nothex"),
        (5, "A" * 40),
        (6, "bad"),
        (7, "WALL_CLOCK"),
        (8, "SYNTHETIC"),
        (9, "OTHER"),
    ],
)
def test_invalid_header_types_and_domains(index, value):
    rows = vector()
    rows[0][index] = value
    with pytest.raises(ValueError):
        api()[1].decode(encoded(rows))


@pytest.mark.parametrize(
    "kind,index,value",
    [
        ("POLICY", 3, True),
        ("POLICY", 4, -1),
        ("POLICY", 4, 2**31),
        ("POLICY", 5, 65),
        ("POLICY", 5, None),
        ("EXPECT", 4, True),
        ("EXPECT", 4, 1.0),
        ("FD", 7, -1),
        ("FD", 7, 2**31),
        ("FD", 8, 0),
        ("FD", 4, "POST_EXEC"),
        ("FD", 3, []),
        ("SNAP", 8, 65),
        ("SNAP", 13, 0),
        ("SNAP", 14, False),
        ("DENY", 8, "OTHER"),
        ("DENY", 9, 0),
        ("END", 5, 0),
    ],
)
def test_invalid_fields_are_not_defaulted(kind, index, value):
    rows = vector()
    next(row for row in rows if row[2] == kind)[index] = value
    with pytest.raises(ValueError):
        api()[1].decode(encoded(rows))


@pytest.mark.parametrize("replacement", (b"NaN", b"Infinity", b"-Infinity", b"1e0"))
def test_json_nonfinite_and_float_spelling_is_rejected(replacement):
    raw = encoded().replace(b"[1,100,", b"[" + replacement + b",100,", 1)
    with pytest.raises(ValueError):
        api()[1].decode(raw)


def test_event_arity_flat_values_and_capture_order_are_enforced():
    c, w, _ = api()
    capture = w.decode(encoded())
    with pytest.raises(ValueError):
        c.Event(1, 100, "BEGIN", ())
    with pytest.raises(ValueError):
        c.Event(1, 100, "BEGIN", "not a vector")
    with pytest.raises(ValueError):
        c.Capture(())
    with pytest.raises(ValueError):
        c.Capture("not a vector")
    with pytest.raises(ValueError):
        c.Capture([None])
    with pytest.raises(ValueError):
        c.Capture(capture.events * 100)
    for index, event in (
        (0, replace(capture.events[0], seq=2)),
        (1, replace(capture.events[1], time_ns=100)),
    ):
        events = list(capture.events)
        events[index] = event
        with pytest.raises(ValueError):
            c.Capture(events)
    rows = vector()
    rows[3] = rows[0].copy()
    rows[3][0:2] = [4, 400]
    with pytest.raises(ValueError):
        w.decode(encoded(rows))
