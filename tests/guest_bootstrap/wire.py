"""Closed bounded observed CPBv1 wire,not an old-CPC or synthetic adapter."""

import re

from tests.guest_raw_lifetime.model import _fields, _uint, require

from .contracts import CASES, Capture, Event, Value

COPY_CONTEXT = {"copy", "local", "scope", "actor", "task", "source", "dest"}
COPY_PAYLOADS = {
    "BEGIN": {"scan_bound", "capacity"},
    "BITMAPS": {"open_fds", "cloexec"},
    "READ": {"fd", "presence", "ofd", "origin"},
    "REFERENCE": {"fd", "read_ordinal"},
    "CLEAR_OPEN": {"fd", "read_ordinal"},
    "STORE": {"fd", "read_ordinal", "presence", "ofd", "origin"},
    "COPY_RETURN": {"result", "tail_zeroed", "reason"},
    "TASK_FINALIZE": {"result", "reason"},
    "ALLOC_FREE": {"reason"},
}
FIELDS = {
    "SEED_BEGIN": set(),
    "NODE": {"object", "role", "origin", "stage", "generation"},
    "SEED_SLOT": {"task", "source", "fd", "presence", "ofd", "origin", "open", "cloexec"},
    "SEED_END": {"parent", "source", "result"},
    "SEED_ABORT": {"reason"},
    "SEED_REJECT": {"reason"},
    "ARM_REJECT": {"reason"},
    "ARM": {"status"},
    "STOP": {"result"},
    **{k: v | COPY_CONTEXT for k, v in COPY_PAYLOADS.items()},
}
ENUMS = {
    "role": {"TASK", "NAMESPACE", "OFD"},
    "origin": {"FIRST_OBSERVED", "ALLOCATION", "UNAVAILABLE"},
    "stage": {"PRE_ARM_SEED", "POST_INIT_ALLOC"},
    "presence": {"PRESENT", "NULL"},
    "status": {"ACTIVE"},
    "reason": {
        "NONE",
        "INJECTED",
        "CONTEXT_UNSUPPORTED",
        "TAG_STATE_INVALID",
        "ISSUER_EXHAUSTED",
        "ALREADY_ATTEMPTED",
        "SEED_NOT_COMPLETE",
        "CASE_MISMATCH",
        "ALLOC_INJECTED",
        "CONSTRUCTOR_INJECTED",
        "NATURAL_ALLOC",
        "TASK_INJECTED",
        "TASK_FAILED",
        "COPY_FAILED",
    },
}
RESULTS = {
    "SEED_END": {"COMPLETE"},
    "STOP": {"DRAINED_EMITTERS_ONLY"},
    "COPY_RETURN": {"SUCCESS", "FAILED"},
    "TASK_FINALIZE": {"COMMITTED", "ABORTED"},
}
IDENTITIES = {"root", "actor", "task", "source", "dest", "parent", "ofd"}


def parse_serial(raw: bytes) -> Capture:
    require(type(raw) is bytes and 0 < len(raw) <= 2**21, "SERIAL_BOUND")
    try:
        lines = [s.rstrip("\r") for s in raw.decode().splitlines() if s.startswith("CPB_")]
    except UnicodeError as exc:
        raise ValueError("SERIAL_ENCODING") from exc
    require(5 <= len(lines) <= 517, "CPB_RECORD_BOUND")
    driver = _fields(lines[0], "CPB_DRIVER", {"ok", "forked"})
    require(driver["ok"] == "1" and driver["forked"] in ("0", "1"), "FIXED_DRIVER_FAILED")
    require(lines[-2:] == ["CPB_END", "CPB_EXIT ok=1"], "COMPLETED_FRAME_REQUIRED")
    meta = _fields(
        lines[1],
        "CPB_META",
        {
            "version",
            "case",
            "release",
            "cpus",
            "capacity",
            "copies",
            "root",
            "boot_nonce",
            "epoch",
            "seed_walk",
        },
    )
    require(
        meta["version"] == "1"
        and meta["case"] in CASES
        and meta["release"] == "6.12.113-cpbootstrap-v1"
        and meta["cpus"] == "1"
        and meta["epoch"] == "1"
        and re.fullmatch(r"[0-9a-f]{32}", meta["boot_nonce"]) is not None
        and meta["boot_nonce"] != "0" * 32,
        "OBSERVED_SOURCE_COHORT",
    )
    cap, copies, root = (_uint(meta[k]) for k in ("capacity", "copies", "root"))
    abort = meta["case"] == "SEED_FAIL"
    require(
        cap == (128 if meta["case"] == "SMALL_BUFFER" else 512)
        and copies == (0 if abort else 2)
        and (root == 0) is abort
        and meta["seed_walk"] == ("ABORTED" if abort else "COMPLETE")
        and (driver["forked"] == "0") is abort,
        "FIXED_CAPTURE_PROFILE",
    )
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    counts = _fields(lines[2], "CPB_COUNT", set(names))
    events: list[Event] = []
    for line in lines[3:-2]:
        kinds = [p[5:] for p in line.split(" ") if p.startswith("kind=")]
        require(len(kinds) == 1 and kinds[0] in FIELDS, "UNSUPPORTED_STAGE")
        kind = kinds[0]
        row = _fields(line, "CPB_EVENT", {"n", "epoch", "kind"} | FIELDS[kind])
        n, epoch = _uint(row["n"]), _uint(row["epoch"])
        require(n > (events[-1].n if events else 0) and epoch == 1, "EVENT_ORDER_OR_EPOCH")
        values: dict[str, Value] = {}
        for name in FIELDS[kind]:
            value = row[name]
            if name in ENUMS:
                require(value in ENUMS[name], "UNSUPPORTED_FIELD_ENUM")
                values[name] = value
            elif name == "result":
                require(value in RESULTS[kind], "UNSUPPORTED_STAGE_RESULT")
                values[name] = value
            elif name == "tail_zeroed":
                require(value in ("-1", "0", "1"), "TAIL_AVAILABILITY")
                values[name] = None if value == "-1" else value == "1"
            else:
                number = _uint(value)
                require(name != "fd" or number < 64, "FD_PROFILE_WIDTH")
                require(
                    name not in ("open", "cloexec") or kind != "SEED_SLOT" or number in (0, 1),
                    "RAW_BITMAP_BIT_REQUIRED",
                )
                require(name != "generation" or number == 0, "GENERATION_UNSUPPORTED")
                require(name != "object" or number > 0, "POSITIVE_OBJECT_ID_REQUIRED")
                values[name] = (
                    (number or None)
                    if name in IDENTITIES
                    else bool(number)
                    if name in ("open", "cloexec") and kind == "SEED_SLOT"
                    else number
                )
        if kind in ("READ", "STORE", "SEED_SLOT"):
            require(values["presence"] != "NULL" or values["ofd"] is None, "NULL_IS_NOT_OFD")
            require(
                values["ofd"] is not None or values["origin"] == "UNAVAILABLE", "ID_ORIGIN_MISMATCH"
            )
        if kind == "NODE":
            require(
                (values["origin"], values["stage"])
                in (("FIRST_OBSERVED", "PRE_ARM_SEED"), ("ALLOCATION", "POST_INIT_ALLOC")),
                "NODE_ORIGIN_STAGE_MISMATCH",
            )
        events.append(Event(n, epoch, kind, tuple(sorted(values.items()))))
    require(len(events) <= cap, "OWN_BUFFER_BOUND")
    a, r, c, f, d, p = (_uint(counts[k]) for k in names)
    return Capture(
        meta["case"],
        cap,
        copies,
        root or None,
        meta["boot_nonce"],
        1,
        meta["seed_walk"],
        driver["forked"] == "1",
        a,
        r,
        c,
        f,
        d,
        p,
        tuple(events),
    )
