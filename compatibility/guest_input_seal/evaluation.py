"""Recognize eight fixed diagnostics, never qualify an input seal backend."""

import hashlib

from .contracts import SealCapture, SealDecision

ORIGINAL = hashlib.sha256(b"0123456789ABCDEF\n").hexdigest()
MUTATED = hashlib.sha256(b"X123456789ABCDEF\n").hexdigest()


def evaluate(capture: SealCapture) -> SealDecision:
    capture.__post_init__()
    events = capture.events[1:-1]
    # Object identities come from the first pinned object, not a pathname/hash.
    if not events or events[0].kind != "SNAP" or events[0].label != "before":
        return SealDecision(capture.case, False, False, ("SCENARIO_MISMATCH",))
    dev, ino = events[0].values[:2]
    base = (dev, ino)
    by_label = {e.label: e for e in events}
    other_label = "other" if capture.case == "IS04" else "replacement"
    other = by_label.get(other_label)
    alternate = other.values[:2] if other and other.kind == "SNAP" else base

    def snap(
        label: str,
        mask: int | None = 47,
        digest: str = ORIGINAL,
        identity: tuple[object, ...] = base,
        err: int = 0,
        mode: int = 0o666,
    ) -> tuple[object, ...]:
        return ("SNAP", label, (*identity, 17, digest, mask, err, mode))

    def op(label: str, result: int = 0, err: int = 0) -> tuple[object, ...]:
        return ("OP", label, (result, err))

    bind = ("BIND", "read", (*base, *base, 0))
    wrong_bind = ("BIND", "read", (*base, *alternate, 0))
    before = snap("before", 32)
    sealed = [op("seal1"), snap("sealed")]
    tail = [bind, snap("read")]
    expected = {
        "IS01": [
            before,
            *sealed,
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
            ("LOCAL", "shared", (88,)),
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
            ("LOCAL", "shared", (88,)),
            snap("mutated", 55, MUTATED),
            op("write_original", -1, 1),
            op("map_shared", -1, 1),
            bind,
            snap("read", 55, MUTATED),
        ],
        "IS04": [
            before,
            *sealed,
            op("seal_other"),
            snap("other", identity=alternate),
            wrong_bind,
            snap("read", identity=alternate),
        ],
        "IS05": [
            snap("before", 1, mode=0o644),
            op("chmod"),
            snap("chmod", 1, mode=0o444),
            ("CRED", "write", (65534, 65534, 1)),
            op("write_original", 1),
            snap("mutated", 1, MUTATED, mode=0o444),
            bind,
            snap("read", 1, MUTATED, mode=0o444),
        ],
        "IS06": [
            before,
            *sealed,
            op("replace"),
            snap("replacement", 1, MUTATED, alternate, 0, 0o644),
            wrong_bind,
            snap("read", 1, MUTATED, alternate, 0, 0o644),
            snap("after"),
        ],
        "IS07": [before, *sealed, ("LOCAL", "private", (88,)), snap("after"), *tail],
        "IS08": [
            before,
            op("seal1", -1, 16),
            snap("failed", 32),
            op("unmap"),
            op("seal2"),
            snap("sealed"),
            *tail,
        ],
    }[capture.case]
    recognized = [(e.kind, e.label, e.values) for e in events] == expected
    if capture.case in ("IS04", "IS06") and alternate == base:
        recognized = False
    return SealDecision(
        capture.case,
        recognized,
        recognized and capture.case in ("IS01", "IS02", "IS07", "IS08"),
        ("FIXED_DIAGNOSTIC_ONLY", "INPUT_SEAL_BACKEND_UNQUALIFIED")
        if recognized
        else ("SCENARIO_MISMATCH",),
    )
