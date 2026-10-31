"""Closed CPRv1 raw observations; no old CPB or synthetic adapter."""

import re

from tests.guest_raw_lifetime.model import _fields, _uint, require

from .contracts import CASES, Capture, Event, Value

CONTEXT = {"copy", "local", "scope", "actor", "task", "source", "dest"}
PAYLOAD = {
    "BEGIN": {"scan_bound", "capacity"},
    "BITMAPS": {"open_fds", "cloexec"},
    "POINTER_READ": {"fd", "presence"},
    "REFERENCE": {"fd", "read_ordinal"},
    "CLEAR_OPEN": {"fd", "read_ordinal"},
    "STORE": {"fd", "read_ordinal", "presence"},
    "TAG_SNAPSHOT": {
        "fd",
        "read_ordinal",
        "raw_cookie",
        "raw_scope",
        "raw_epoch",
        "raw_origin",
        "capture_stage",
        "emit_stage",
        "generation",
        "lifetime",
        "publication",
        "membership",
    },
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
    **{k: v | CONTEXT for k, v in PAYLOAD.items()},
}
ENUMS = {
    "role": {"TASK", "NAMESPACE", "OFD"},
    "origin": {"FIRST_OBSERVED", "ALLOCATION", "UNAVAILABLE"},
    "stage": {"PRE_ARM_SEED", "POST_INIT_ALLOC"},
    "presence": {"PRESENT", "NULL"},
    "status": {"ACTIVE"},
    "capture_stage": {"POST_EXISTING_REFERENCE_PRE_STORE"},
    "emit_stage": {"SAVED_SCALARS_AFTER_STORE"},
    "lifetime": {"UNAVAILABLE"},
    "publication": {"UNAVAILABLE"},
    "membership": {"UNAVAILABLE"},
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


def parse_serial(raw: bytes) -> Capture:
    require(type(raw) is bytes and 0 < len(raw) <= 2**21, "SERIAL_BOUND")
    try:
        decoded = raw.decode().splitlines()
    except UnicodeError as exc:
        raise ValueError("SERIAL_ENCODING") from exc
    require(
        not any(s.startswith(("CPB_", "CPC_", "CPL_")) for s in decoded), "LEGACY_RECORD_PREFIX"
    )
    lines = [s for s in decoded if s.startswith("CPR_")]
    require(5 <= len(lines) <= 517, "CPR_RECORD_BOUND")
    require(lines[0] == "CPR_DRIVER ok=1", "FIXED_DRIVER_FAILED")
    require(lines[-2:] == ["CPR_END", "CPR_EXIT ok=1"], "COMPLETED_FRAME_REQUIRED")
    meta = _fields(
        lines[1],
        "CPR_META",
        {
            "version",
            "profile",
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
        and meta["profile"] == "POST_REFERENCE_RAW_V1"
        and meta["case"] in CASES
        and meta["release"] == "6.12.113-cptagread-v1"
        and meta["cpus"] == "1"
        and meta["epoch"] == "1"
        and meta["seed_walk"] == "COMPLETE"
        and re.fullmatch(r"[0-9a-f]{32}", meta["boot_nonce"]) is not None
        and meta["boot_nonce"] != "0" * 32,
        "OBSERVED_SOURCE_COHORT",
    )
    capacity, copies, root = (_uint(meta[k]) for k in ("capacity", "copies", "root"))
    require(
        capacity == (128 if meta["case"] == "SMALL_BUFFER" else 512) and copies == 2 and root > 0,
        "FIXED_PROFILE",
    )
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    count_fields = _fields(lines[2], "CPR_COUNT", set(names))
    counts = tuple(_uint(count_fields[k]) for k in names)
    events: list[Event] = []
    for text in lines[3:-2]:
        kinds = [x[5:] for x in text.split(" ") if x.startswith("kind=")]
        require(len(kinds) == 1 and kinds[0] in FIELDS, "UNSUPPORTED_STAGE")
        kind = kinds[0]
        row = _fields(text, "CPR_EVENT", {"n", "epoch", "kind"} | FIELDS[kind])
        n = _uint(row["n"])
        require(n > (events[-1].n if events else 0) and row["epoch"] == "1", "EVENT_ORDER_OR_EPOCH")
        values: dict[str, Value] = {}
        for key in FIELDS[kind]:
            value = row[key]
            if key in ENUMS or key == "result":
                require(
                    value in (RESULTS[kind] if key == "result" else ENUMS[key]), "UNSUPPORTED_ENUM"
                )
                values[key] = value
            elif key == "generation":
                require(
                    value == ("UNAVAILABLE" if kind == "TAG_SNAPSHOT" else "0"),
                    "GENERATION_NOT_OBSERVED",
                )
                values[key] = value
            elif key == "tail_zeroed":
                require(value in ("-1", "0", "1"), "TAIL_VALUE")
                values[key] = value
            else:
                number = _uint(value)
                require(key != "copy" or 1 <= number <= 2, "COPY_COHORT")
                require(key != "fd" or number < 64, "FD_BOUND")
                require(key != "local" or number > 0, "LOCAL_ID_REQUIRED")
                require(key != "read_ordinal" or number > 0, "SOURCE_ID_REQUIRED")
                require(key != "raw_origin" or number <= 2, "RAW_ORIGIN_PROFILE")
                require(
                    kind != "SEED_SLOT" or key not in ("open", "cloexec") or number <= 1,
                    "BIT_REQUIRED",
                )
                values[key] = number
        events.append(Event(n, kind, tuple(sorted(values.items()))))
    require(len(events) <= capacity, "OWN_BUFFER_BOUND")
    return Capture(meta["case"], capacity, copies, root, meta["boot_nonce"], counts, tuple(events))
