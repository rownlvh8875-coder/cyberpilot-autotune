"""Pure untrusted point consistency, never producer qualification or admission."""

import json
from dataclasses import asdict
from hashlib import sha256

from .contracts import STAGE, Capture, Decision, require


def check_inventory(capture: Capture) -> Decision:
    require(type(capture) is Capture)
    capture.__post_init__()
    events = capture.events

    def reject(reason: str) -> Decision:
        return Decision("REJECTED", (reason,))

    if len(events) < 7 or events[1].kind != "POLICY":
        return reject("POLICY_MISSING")
    policy, _, count = events[1].values
    i = 2
    expected = []
    for _ in range(count):
        if i >= len(events) or events[i].kind != "EXPECT":
            return reject("EXPECTED_FD_MISSING")
        p, fd = events[i].values
        if p != policy:
            return reject("POLICY_COHORT_MISMATCH")
        expected.append(fd)
        i += 1
    if expected != sorted(set(expected)):
        return reject("EXPECTED_FD_ORDER_INVALID")
    if i >= len(events) or events[i].kind != "BIRTH" or events[i].values != (1, 0):
        return reject("BIRTH_INVALID")
    i += 1
    fds = []
    while i < len(events) and events[i].kind == "FD":
        fds.append(events[i])
        i += 1
    if i >= len(events) or events[i].kind != "SNAP":
        return reject("SNAPSHOT_MISSING")
    snapshot = events[i]
    sid, stage, root, epoch, p, observed_count, *context = snapshot.values
    if (
        sid == 0
        or p != policy
        or (root, epoch) != (1, 0)
        or context != [1, 65534, 65534, 1, None, None]
    ):
        return reject("SNAPSHOT_CONTEXT_INVALID")
    if len(fds) != observed_count:
        return reject("INVENTORY_COUNT_MISMATCH")
    observed = [e.values[4] for e in fds]
    if observed != sorted(set(observed)):
        return reject("OBSERVED_FD_ORDER_INVALID")
    cohort = (sid, STAGE, 1, 0)
    if any(e.values[:4] != cohort for e in fds):
        return reject("FD_COHORT_MISMATCH")
    by_fd = {e.values[4]: e for e in fds}
    i += 1
    causes = []
    while i < len(events) and events[i].kind == "CAUSE":
        causes.append(events[i])
        i += 1
    if i >= len(events) or events[i].kind not in ("DENY", "RESULT"):
        return reject("DECISION_MISSING")
    decision = events[i]
    if decision.values[:5] != (*cohort, policy):
        return reject("DECISION_COHORT_MISMATCH")
    extras, missing = set(observed) - set(expected), set(expected) - set(observed)
    if decision.kind == "DENY":
        if missing or not extras:
            return reject("DENIAL_SET_RELATION_INVALID")
        if decision.values[-1] != len(causes):
            return reject("CAUSE_COUNT_MISMATCH")
        if [e.values[1] for e in causes] != sorted(extras):
            return reject("CAUSE_SET_MISMATCH")
        if any(e.values != (sid, e.values[1], by_fd[e.values[1]].seq) for e in causes):
            return reject("CAUSE_SOURCE_MISMATCH")
    else:
        wanted = (
            "UNSUPPORTED_MIXED"
            if missing and extras
            else "UNSUPPORTED_MISSING"
            if missing
            else "NO_DENIAL"
        )
        if causes or extras and not missing or decision.values[5] != wanted:
            return reject("RESULT_SET_RELATION_INVALID")
    tail = events[i + 1 :]
    if (
        len(tail) != 2
        or tail[0].kind != "REAP"
        or tail[0].values != (1, 0, "SIGNALLED", 9)
        or tail[1].values != (1, 0, None)
    ):
        return reject("LIFECYCLE_INVALID")
    return Decision("WIRE_DIAGNOSTIC_CONSISTENT", ())


def canonical_digest(capture: Capture) -> str:
    require(type(capture) is Capture)
    capture.__post_init__()
    raw = json.dumps(asdict(capture), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(raw.encode("utf-8")).hexdigest()
