"""Breaks caught: fabricated stage/object/byte/availability evidence and bad framing."""

import hashlib
import json

import pytest

from tests.experiments.guest_data_fd_handoff import model

PAYLOAD = b"fixed DATA bytes\n"
HASH = hashlib.sha256(PAYLOAD).hexdigest()
PROGRAM = "a" * 64


def rows(case="HH01"):
    """Hand specified positive trace; SYNTHETIC unit input, never published as observed."""
    empty = case == "HH07"
    size = 0 if empty else 17
    digest = hashlib.sha256(b"").hexdigest() if empty else HASH

    def fd(stage):
        return [
            "FD",
            stage,
            1 if stage != "PRE_EXEC" else 0,
            0,
            0,
            1,
            100,
            size,
            0 if stage == "PRE_EXEC" else 524288,
            47,
            0,
            digest,
            None,
            1,
        ]

    return [
        ["BEGIN", "guest-data-fd-handoff-observed-v1", case, "GUEST_MONOTONIC_NS"],
        ["OBJECT", "primary", 1, 100, size, digest, 47, 0],
        ["OBJECT", "program", 2, 200, 800000, PROGRAM, None, 22],
        ["BIRTH", 1],
        ["SNAP", "PRE_TRANSFER", 0, 0, 1, 0, 0, 0, None],
        fd("PRE_EXEC"),
        ["SNAP", "PRE_EXEC", 0, 1, 1, 65534, 65534, 1, None],
        ["OFD_PIN", 0, -1, 1],
        ["EXEC", 0, 1, 2, 200, 800000, PROGRAM],
        fd("POST_EXEC"),
        ["SNAP", "POST_EXEC", 1, 1, 1, 65534, 65534, 1, None],
        ["READY", 1],
        fd("READ_CHECK"),
        ["READ", 1, 0, 0, 0, 17, size, "" if empty else PAYLOAD.hex()],
        ["CLOSE", 1, 0, 0, 0],
        ["SNAP", "CLOSED", 1, 0, 1, 65534, 65534, 1, None],
        ["REAP", 1, "EXITED", 0],
        ["RELEASE", "primary_rw", 0],
        ["RELEASE", "primary_ro", 0],
        ["RELEASE", "program", 0],
        ["END", 1, None],
    ]


def serial(events):
    records = ["HFD " + json.dumps([i, i * 100, *r]) for i, r in enumerate(events, 1)]
    return (
        "kernel boot\nHFD_EXEC\n" + "\n".join(records) + "\nHFD_PROBE_EXIT=0\nHFD_DONE\n"
    ).encode()


def test_positive_read_is_scoped_not_qualification():
    result = model.check_case(model.parse_serial(serial(rows()), "HH01"), PROGRAM)
    assert result.transport_observed is True
    assert result.status == "BLOCKED"
    assert result.fd_table_generation is None
    assert result.global_prohibited_counts is None
    assert all(v is False for _, v in result.permissions)


def test_empty_file_has_actual_zero_not_missing():
    result = model.check_case(model.parse_serial(serial(rows("HH07")), "HH07"), PROGRAM)
    assert result.returned_bytes == b""


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r[5].__setitem__(6, 101),  # same bytes, wrong object
        lambda r: r[5].__setitem__(8, 524288),  # pre-exec CLOEXEC
        lambda r: r[9].__setitem__(8, 0),  # post-exec not resealed CLOEXEC
        lambda r: r[9].__setitem__(2, 0),  # stale exec cohort
        lambda r: r[9].__setitem__(12, 0),  # unavailable OFD becomes invented equality
        lambda r: r[13].__setitem__(7, "00" * 17),  # returned buffer forgery
        lambda r: r[13].__setitem__(6, None),  # missing is not zero
        lambda r: r[13].__setitem__(3, 1),  # slot generation drift
        lambda r: r[13].__setitem__(2, 3),  # wrong FD
        lambda r: r[16].__setitem__(3, 2),  # unsuccessful target exit
        lambda r: r[4].__setitem__(8, 0),  # invented FD-table generation
        lambda r: r[14].__setitem__(4, -9),  # close failure
        lambda r: r.insert(12, ["READY", 1]),  # duplicate barrier
        lambda r: r.reverse(),
    ],
)
def test_false_evidence_is_rejected(mutate):
    events = rows()
    mutate(events)
    with pytest.raises(ValueError):
        model.check_case(model.parse_serial(serial(events), "HH01"), PROGRAM)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.replace(b"HFD_EXEC\n", b"HFD_EXEC\nHFD_EXEC\n"),
        lambda b: b.replace(b"HFD_PROBE_EXIT=0", b"HFD_PROBE_EXIT=2"),
        lambda b: b.replace(b"HFD_DONE\n", b"HFD_DONE"),
        lambda b: b.replace(b"HFD ", b"HFD\x85 ", 1),
        lambda b: b + b"HFD_DONE\n",
        lambda b: b.replace(b"[1, 100,", b"[true, 100,", 1),
        lambda b: b.replace(b"[2, 200,", b"[2, 99,", 1),
        lambda b: b.replace(b"null", b"NaN", 1),
    ],
)
def test_physical_framing_and_exact_numeric_types(mutate):
    with pytest.raises(ValueError):
        model.parse_serial(mutate(serial(rows())), "HH01")


def test_capture_defensive_copy_and_exact_program_binding():
    data = serial(rows())
    c = model.parse_serial(data, "HH01")
    assert isinstance(c.events, tuple)
    assert isinstance(c.events[0].values, tuple)
    with pytest.raises(ValueError):
        model.check_case(c, "b" * 64)
    assert model.parse_serial(data.replace(b"\n", b"\r\n"), "HH01") == c


def negative_rows(case):
    r = rows()
    r[0][2] = case
    alt = ["OBJECT", "alternate", 1, 101, 17, HASH, 47, 0]
    before = r[:7]
    if case in ("HH02", "HH06"):
        before.insert(2, alt)
    if case == "HH02":
        before[-2][6] = 101
    if case in ("HH03", "HH06"):
        extra = list(r[5])
        extra[3] = 3
        if case == "HH06":
            extra[6] = 101
        before.insert(-1, extra)
        before[-1][3] = 2
    tail = [
        ["REAP", 0 if case in ("HH02", "HH03") else 1, "SIGNALLED", 9],
        ["RELEASE", "primary_rw", 0],
        ["RELEASE", "primary_ro", 0],
        ["RELEASE", "program", 0],
    ]
    if case in ("HH02", "HH06"):
        tail.extend([["RELEASE", "alternate_rw", 0], ["RELEASE", "alternate_ro", 0]])
    tail.append(["END", tail[0][1], None])
    reasons = {
        "HH02": "PRE_EXEC_BINDING",
        "HH03": "EXTRA_FD",
        "HH04": "EARLY_READ",
        "HH05": "POST_EXEC_BINDING",
        "HH06": "BINDING_CHANGED",
    }
    if case in ("HH02", "HH03"):
        middle = []
    elif case == "HH04":
        middle = r[7:9]
    elif case == "HH05":
        before[-2][8] = 524288
        middle = r[7:9] + [["SNAP", "POST_EXEC", 1, 0, 1, 65534, 65534, 1, None]]
    else:
        extra = list(r[9])
        extra[3] = 3
        extra[6] = 101
        post = list(r[10])
        post[3] = 2
        reused0 = list(r[9])
        reused0[1] = "REUSED"
        reused0[4] = 1
        reused0[6] = 101
        reused3 = list(extra)
        reused3[1] = "REUSED"
        middle = [
            r[7],
            ["OFD_PIN", 3, -1, 1],
            r[8],
            r[9],
            extra,
            post,
            r[11],
            ["CLOSE", 1, 0, 0, 0],
            ["DUP", 1, 3, 0, 1, 0],
            reused0,
            reused3,
            ["SNAP", "REUSED", 1, 2, 1, 65534, 65534, 1, None],
        ]
    return before + middle + [["DENY", reasons[case], tail[0][1], 0]] + tail


@pytest.mark.parametrize("case", ["HH02", "HH03", "HH04", "HH05", "HH06"])
def test_expected_negative_case_is_not_successful_transport(case):
    c = model.parse_serial(serial(negative_rows(case)), case)
    checked = model.check_case(c, PROGRAM)
    assert checked.transport_observed is False
    assert checked.returned_bytes is None
    assert checked.status == "BLOCKED"


@pytest.mark.parametrize("case", ["HH02", "HH03", "HH04", "HH05", "HH06"])
def test_negative_case_cannot_hide_successful_read(case):
    r = negative_rows(case)
    r.insert(-5, ["READ", 1, 0, 0, 0, 17, 17, PAYLOAD.hex()])
    with pytest.raises(ValueError):
        model.check_case(model.parse_serial(serial(r), case), PROGRAM)
