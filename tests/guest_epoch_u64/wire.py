"""One bounded v2 frame; no v1 parser call, conversion or qualification path."""

import re

from tests.guest_raw_lifetime.model import _fields, _uint, require
from tests.guest_tag_snapshot.contracts import CASES
from tests.guest_tag_snapshot.wire import ENUMS as V1_ENUMS
from tests.guest_tag_snapshot.wire import FIELDS as V1_FIELDS
from tests.guest_tag_snapshot.wire import RESULTS

from .contracts import CaptureV2, EventV2, Value

# Vocabulary reuse only: never mutate v1 definitions or call its parser/model.
FIELDS = {kind: frozenset(names) for kind, names in V1_FIELDS.items()}
FIELDS["TAG_SNAPSHOT"] |= {"raw_epoch_status"}
ENUMS = {key: frozenset(values) for key, values in V1_ENUMS.items()}
ENUMS["raw_epoch_status"] = frozenset({"OBSERVED", "UNAVAILABLE"})


def parse_serial(raw: bytes) -> CaptureV2:
    require(type(raw) is bytes and 0 < len(raw) <= 2**21, "SERIAL_BOUND")
    require(raw.endswith(b"\n"), "COMPLETED_LINE_REQUIRED")
    normalized = raw.replace(b"\r\n", b"\n")
    require(all(byte == 10 or 32 <= byte < 127 for byte in normalized), "ASCII_LINE_ENCODING")
    decoded = normalized.decode("ascii").splitlines()
    require(
        not any(line.startswith(("CPR_", "CPB_", "CPC_", "CPL_")) for line in decoded),
        "LEGACY_OR_MIXED_FRAME",
    )
    lines = [line for line in decoded if line.startswith("CPR2_")]
    require(5 <= len(lines) <= 517, "V2_RECORD_BOUND")
    require(lines[0] == "CPR2_DRIVER ok=1", "FIXED_DRIVER_FAILED")
    require(lines[-2:] == ["CPR2_END", "CPR2_EXIT ok=1"], "COMPLETED_FRAME_REQUIRED")
    meta = _fields(
        lines[1],
        "CPR2_META",
        {
            "version",
            "profile",
            "encoding",
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
        meta["version"] == "2"
        and meta["profile"] == "POST_REFERENCE_RAW_EPOCH_U64_V2"
        and meta["encoding"] == "UINT64_DECIMAL_V1"
        and meta["release"] == "6.12.113-cptagread-u64-v2"
        and meta["case"] in CASES
        and meta["cpus"] == meta["epoch"] == "1"
        and meta["seed_walk"] == "COMPLETE"
        and re.fullmatch(r"[0-9a-f]{32}", meta["boot_nonce"]) is not None
        and meta["boot_nonce"] != "0" * 32,
        "V2_PROFILE_NOT_ATTESTATION",
    )
    capacity, copies, root = (_uint(meta[key]) for key in ("capacity", "copies", "root"))
    require(
        capacity == (128 if meta["case"] == "SMALL_BUFFER" else 512) and copies == 2 and root > 0,
        "FIXED_PROFILE",
    )
    names = ("attempted", "reserved", "committed", "failed", "discarded", "pending")
    count_fields = _fields(lines[2], "CPR2_COUNT", set(names))
    counts = tuple(_uint(count_fields[key]) for key in names)
    attempted, reserved, committed, failed, discarded, pending = counts
    require(
        attempted == reserved + failed
        and reserved == committed + pending
        and discarded == 0
        and reserved <= capacity,
        "LOCAL_ACCOUNTING_STRUCTURE",
    )
    events = []
    for text in lines[3:-2]:
        kinds = [part[5:] for part in text.split(" ") if part.startswith("kind=")]
        require(len(kinds) == 1 and kinds[0] in FIELDS, "UNSUPPORTED_STAGE")
        kind = kinds[0]
        row = _fields(text, "CPR2_EVENT", {"n", "epoch", "kind"} | FIELDS[kind])
        n = _uint(row["n"])
        require(
            (events[-1].n if events else 0) < n <= attempted and row["epoch"] == "1",
            "EVENT_ORDER_OR_EPOCH",
        )
        values: dict[str, Value] = {}
        for key in FIELDS[kind]:
            value = row[key]
            if key == "raw_epoch":
                if row["raw_epoch_status"] == "UNAVAILABLE":
                    require(value == "UNAVAILABLE", "UNKNOWN_IS_NOT_ZERO")
                    values[key] = None
                else:
                    values[key] = _uint(value)
            elif key in ENUMS or key == "result":
                require(
                    value in (RESULTS[kind] if key == "result" else ENUMS[key]), "UNSUPPORTED_ENUM"
                )
                values[key] = value
            elif key == "generation":
                require(
                    value == ("UNAVAILABLE" if kind == "TAG_SNAPSHOT" else "0"),
                    "GENERATION_NOT_OBSERVED",
                )
                values[key] = None if kind == "TAG_SNAPSHOT" else 0
            elif key == "tail_zeroed":
                require(value in ("-1", "0", "1"), "TAIL_VALUE")
                values[key] = value
            else:
                number = _uint(value)
                require(key != "copy" or 1 <= number <= 2, "COPY_COHORT")
                require(key != "fd" or number < 64, "FD_BOUND")
                require(key not in {"local", "read_ordinal"} or number > 0, "SOURCE_ID_REQUIRED")
                require(key != "raw_origin" or number <= 2, "RAW_ORIGIN_PROFILE")
                require(
                    kind != "SEED_SLOT" or key not in {"open", "cloexec"} or number <= 1,
                    "BIT_REQUIRED",
                )
                values[key] = number
        if kind == "NODE":
            require(
                (values["origin"], values["stage"])
                in {("FIRST_OBSERVED", "PRE_ARM_SEED"), ("ALLOCATION", "POST_INIT_ALLOC")}
                and values["object"] != 0,
                "NODE_ORIGIN_STAGE_MISMATCH",
            )
        if kind == "SEED_SLOT":
            require(
                (values["presence"] != "NULL" or values["ofd"] == 0)
                and (values["ofd"] != 0 or values["origin"] == "UNAVAILABLE"),
                "SEED_TAG_MISMATCH",
            )
        events.append(EventV2(n, kind, tuple(sorted(values.items()))))
    require(len(events) == committed, "COMMITTED_RECORD_COUNT")
    return CaptureV2(
        meta["case"], capacity, copies, root, meta["boot_nonce"], counts, tuple(events)
    )
