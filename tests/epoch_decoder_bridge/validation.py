"""Direct full decoding plus an independently literal synthetic expected cohort."""

from tests.guest_epoch_u64.contracts import CaptureV2
from tests.guest_epoch_u64.wire import parse_serial

EXPECTED = (
    0,
    1,
    4294967295,
    4294967296,
    4294967297,
    9007199254740991,
    9007199254740993,
    9223372036854775807,
    9223372036854775808,
    18446744073709551614,
    18446744073709551615,
)


def check_frame(raw: bytes) -> CaptureV2:
    # Never extract/re-encode raw_epoch or replace the source formatter's bytes.
    capture = parse_serial(raw)
    if (
        capture.case != "NORMAL"
        or capture.capacity != 512
        or capture.copies != 2
        or capture.root != 8
        or capture.boot_nonce != "0123456789abcdef0123456789abcdef"
        or capture.counts != (11, 11, 11, 0, 0, 0)
        or len(capture.events) != 11
    ):
        raise ValueError("EXPECTED_FRAME_COHORT")
    for ordinal, (event, epoch) in enumerate(zip(capture.events, EXPECTED, strict=True), 1):
        expected = {
            "copy": 1,
            "local": ordinal,
            "scope": 8,
            "actor": 1,
            "task": 8,
            "source": 2,
            "dest": 9,
            "fd": 5,
            "read_ordinal": ordinal,
            "raw_cookie": 6,
            "raw_scope": 0,
            "raw_epoch_status": "OBSERVED",
            "raw_epoch": epoch,
            "raw_origin": 1,
            "capture_stage": "POST_EXISTING_REFERENCE_PRE_STORE",
            "emit_stage": "SAVED_SCALARS_AFTER_STORE",
            "generation": None,
            "lifetime": "UNAVAILABLE",
            "publication": "UNAVAILABLE",
            "membership": "UNAVAILABLE",
        }
        if event.n != ordinal or event.kind != "TAG_SNAPSHOT" or dict(event.values) != expected:
            raise ValueError("EXPECTED_EVENT_COHORT")
    return capture
