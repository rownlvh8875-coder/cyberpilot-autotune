"""Untrusted inventory relationships; the fixture generator is not a producer."""

from dataclasses import replace

import pytest

from tests.test_deny_fd_v2_wire import api, encoded, vector


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"observed": (0,), "outcome": "NO_DENIAL", "case": "DFD02"},
        {"expected": (3,), "causes": (0,), "subject": 3, "case": "DFD03"},
        {"observed": (0, 3, 4), "causes": (3, 4), "case": "DFD04"},
        {"observed": (), "outcome": "UNSUPPORTED_MISSING", "case": "DFD05"},
        {"observed": (3,), "outcome": "UNSUPPORTED_MIXED", "case": "DFD06"},
        {"observed": (0, 2**31 - 1), "causes": (2**31 - 1,)},
        {"expected": (), "observed": (0,), "causes": (0,), "subject": None},
    ],
)
def test_six_fixed_relations_and_zero_maximum_empty_boundaries_remain_blocked(kwargs):
    _, w, v = api()
    decision = v.check_inventory(w.decode(encoded(vector(**kwargs))))
    assert decision.outcome == "WIRE_DIAGNOSTIC_CONSISTENT" and decision.reasons == ()
    assert decision.status == "BLOCKED" and all(value is False for _, value in decision.permissions)


def checked(rows):
    c, _, v = api()
    rows = [row.copy() for row in rows]
    for i, row in enumerate(rows, 1):
        row[0:2] = [i, i * 100]
    return v.check_inventory(
        c.Capture(tuple(c.Event(r[0], r[1], r[2], tuple(r[3:])) for r in rows))
    )


@pytest.mark.parametrize(
    "kind,index,value",
    [
        ("EXPECT", 3, 2),
        ("BIRTH", 3, 2),
        ("BIRTH", 4, 1),
        ("FD", 3, 2),
        ("FD", 5, 2),
        ("FD", 6, 1),
        ("SNAP", 3, 0),
        ("SNAP", 5, 2),
        ("SNAP", 6, 1),
        ("SNAP", 7, 2),
        ("SNAP", 8, 1),
        ("SNAP", 9, 2),
        ("SNAP", 10, 0),
        ("SNAP", 11, 0),
        ("SNAP", 12, 0),
        ("CAUSE", 3, 2),
        ("CAUSE", 4, 0),
        ("CAUSE", 5, 5),
        ("CAUSE", 5, 100),
        ("DENY", 3, 2),
        ("DENY", 5, 2),
        ("DENY", 6, 1),
        ("DENY", 7, 2),
        ("DENY", 10, 0),
        ("REAP", 3, 2),
        ("REAP", 4, 1),
        ("REAP", 6, 0),
        ("END", 3, 2),
        ("END", 4, 1),
    ],
)
def test_wrong_point_source_cohort_count_and_lifecycle_are_rejected(kind, index, value):
    rows = vector()
    next(row for row in rows if row[2] == kind)[index] = value
    assert checked(rows).outcome == "REJECTED"


@pytest.mark.parametrize(
    "kind", ("POLICY", "EXPECT", "BIRTH", "FD", "SNAP", "CAUSE", "DENY", "REAP")
)
def test_missing_required_rows_are_not_invented(kind):
    rows = vector()
    del rows[next(i for i, row in enumerate(rows) if row[2] == kind)]
    assert checked(rows).outcome == "REJECTED"


def test_duplicate_unsorted_and_incomplete_sets_are_rejected():
    rows = vector()
    rows[5][7] = 0
    assert checked(rows).outcome == "REJECTED"
    rows = vector(expected=(3, 0))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(3, 0))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(0, 3, 4), causes=(4, 3))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(observed=(0, 3, 4), causes=(3,))
    assert checked(rows).outcome == "REJECTED"
    rows = vector(expected=(0, 0))
    assert checked(rows).outcome == "REJECTED"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"expected": (0, 4)},
        {"observed": (0,), "causes": ()},
        {"outcome": "NO_DENIAL"},
        {"observed": (0,), "outcome": "UNSUPPORTED_MISSING"},
        {"observed": (), "outcome": "UNSUPPORTED_MIXED"},
    ],
)
def test_denial_and_result_labels_must_follow_the_actual_set_relation(kwargs):
    assert checked(vector(**kwargs)).outcome == "REJECTED"


def test_cause_rows_cannot_accompany_a_nondenial_result_or_replace_the_source():
    rows = vector()
    rows[-3] = [0, 0, "RESULT", 1, "PRE_EXEC_INVENTORY", 1, 0, 1, "NO_DENIAL"]
    assert checked(rows).outcome == "REJECTED"
    rows = vector()
    rows.insert(-2, rows[-3].copy())
    assert checked(rows).outcome == "REJECTED"


def test_digest_is_content_only_and_revalidates_nested_values():
    c, w, v = api()
    capture = w.decode(encoded())
    assert v.canonical_digest(capture) == v.canonical_digest(w.decode(encoded()))
    for field, value in ((2, "d" * 40), (1, "e" * 32)):
        values = list(capture.events[0].values)
        values[field] = value
        other = replace(
            capture, events=(replace(capture.events[0], values=values), *capture.events[1:])
        )
        assert v.canonical_digest(capture) != v.canonical_digest(other)
    for value in (None, (), "capture"):
        with pytest.raises(ValueError):
            v.canonical_digest(value)
        with pytest.raises(ValueError):
            v.check_inventory(value)
    object.__setattr__(capture.events[0], "values", (False,))
    with pytest.raises(ValueError):
        v.canonical_digest(capture)
    with pytest.raises(ValueError):
        v.check_inventory(capture)


def test_decisions_cannot_carry_permission_or_inconsistent_reasons():
    c, _, _ = api()
    for outcome, reasons in (
        ("ELIGIBLE", ()),
        ("REJECTED", ()),
        ("WIRE_DIAGNOSTIC_CONSISTENT", ("BAD",)),
        ("REJECTED", (None,)),
        (True, ()),
        ("REJECTED", "BAD"),
    ):
        with pytest.raises(ValueError):
            c.Decision(outcome, reasons)
    reasons = ["BAD"]
    decision = c.Decision("REJECTED", reasons)
    reasons.clear()
    assert decision.reasons == ("BAD",)
