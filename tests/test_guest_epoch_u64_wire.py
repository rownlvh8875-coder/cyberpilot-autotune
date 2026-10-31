"""Literal synthetic frames, never converted from retained v1 captures."""

from dataclasses import FrozenInstanceError

import pytest

from tests.guest_epoch_u64.fixtures import FRAME, META, SNAPSHOT
from tests.guest_epoch_u64.wire import parse_serial
from tests.guest_tag_snapshot.wire import parse_serial as parse_v1


@pytest.mark.parametrize(
    "decimal",
    [
        b"0",
        b"1",
        b"4294967295",
        b"4294967296",
        b"4294967297",
        b"9007199254740991",
        b"9007199254740993",
        b"9223372036854775807",
        b"9223372036854775808",
        b"18446744073709551614",
        b"18446744073709551615",
    ],
)
def test_literal_full_width_values_are_decoded_without_authority(decimal):
    capture = parse_serial(FRAME.replace(b"raw_epoch=1 ", b"raw_epoch=" + decimal + b" "))
    assert dict(capture.events[0].values)["raw_epoch"] == int(decimal)
    assert capture.evidence_class == "WIRE_BYTES_UNTRUSTED" and capture.status == "BLOCKED"
    assert capture.runtime_qualified is False and capture.actual_global_drops is None
    assert all(flag is False for _, flag in capture.permissions)
    with pytest.raises(FrozenInstanceError):
        capture.root = 0


def test_unknown_epoch_and_raw_zero_are_distinct():
    missing = FRAME.replace(
        b"raw_epoch_status=OBSERVED raw_epoch=1",
        b"raw_epoch_status=UNAVAILABLE raw_epoch=UNAVAILABLE",
    )
    assert dict(parse_serial(missing).events[0].values)["raw_epoch"] is None
    zero = FRAME.replace(b"raw_epoch=1 ", b"raw_epoch=0 ")
    assert dict(parse_serial(zero).events[0].values)["raw_epoch"] == 0


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"raw_epoch=1 ", b"raw_epoch=01 "),
        (b"raw_epoch=1 ", b"raw_epoch=-1 "),
        (b"raw_epoch=1 ", b"raw_epoch=+1 "),
        (b"raw_epoch=1 ", b"raw_epoch=1.0 "),
        (b"raw_epoch=1 ", b"raw_epoch=18446744073709551616 "),
        (b"raw_epoch=1 ", b"raw_epoch=UNAVAILABLE "),
        (b"raw_epoch_status=OBSERVED", b"raw_epoch_status=UNAVAILABLE"),
        (b"raw_epoch_status=OBSERVED", b"raw_epoch_status=False"),
        (b"version=2", b"version=1"),
        (b"EPOCH_U64_V2", b"RAW_V1"),
        (b"UINT64_DECIMAL_V1", b"FLOAT64"),
        (b"cptagread-u64-v2", b"cptagread-v1"),
        (b"CPR2_END", b"CPR_END"),
        (b"CPR2_EVENT", b"CPR_EVENT"),
        (b"CPR2_EXIT", b"CPR_EXIT"),
        (b"CPR2_DRIVER", b"CPR_DRIVER"),
        (b"kind=TAG_SNAPSHOT", b"kind=WRONG_STAGE"),
        (b"POST_EXISTING_REFERENCE_PRE_STORE", b"POINTER_READ"),
        (b"SAVED_SCALARS_AFTER_STORE", b"PID_OUTPUT"),
        (b"raw_origin=1", b"raw_origin=3"),
        (b"fd=5", b"fd=64"),
        (b"read_ordinal=1", b"read_ordinal=0"),
        (b"local=1", b"local=0"),
        (b"copy=1", b"copy=3"),
        (b"epoch=1", b"epoch=2"),
        (b"root=8", b"root=0"),
        (b"copies=2", b"copies=1"),
        (b"capacity=512", b"capacity=128"),
        (b"cpus=1", b"cpus=2"),
        (b"seed_walk=COMPLETE", b"seed_walk=ABORTED"),
        (b"0123456789abcdef0123456789abcdef", b"00000000000000000000000000000000"),
        (b"committed=1", b"committed=0"),
        (b"failed=0", b"failed=1"),
        (b"discarded=0", b"discarded=1"),
        (b"pending=0", b"pending=1"),
        (b"generation=UNAVAILABLE", b"generation=0"),
        (b"lifetime=UNAVAILABLE", b"lifetime=PROVEN"),
        (b"raw_scope=0", b"raw_scope=0 extra=1"),
        (b"raw_scope=0", b"raw_scope=0 raw_scope=0"),
    ],
)
def test_bad_values_stages_profiles_and_mixed_frames_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse_serial(FRAME.replace(old, new))


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        None,
        "text",
        b"x" * (2**21 + 1),
        b"\xff",
        b"\x00" + FRAME,
        FRAME[:-1],
        FRAME + FRAME,
        FRAME.replace(b"CPR2_END\n", b""),
        FRAME + b"CPB_EVENT x=1\n",
        FRAME + b"CPR2_UNKNOWN x=1\n",
        FRAME.replace(SNAPSHOT, SNAPSHOT + SNAPSHOT),
    ],
)
def test_malformed_duplicate_truncated_or_oversize_frames_reject(raw):
    with pytest.raises(ValueError):
        parse_serial(raw)


def test_v1_reader_rejects_v2_and_v2_reader_rejects_v1():
    with pytest.raises(ValueError):
        parse_v1(FRAME)
    legacy = FRAME.replace(b"CPR2_", b"CPR_").replace(b"version=2", b"version=1")
    with pytest.raises(ValueError):
        parse_serial(legacy)


def test_crlf_console_transport_preserves_semantic_values_and_boot_noise_is_not_evidence():
    capture = parse_serial(b"Boot noise\r\n" + FRAME.replace(b"\n", b"\r\n"))
    assert dict(capture.events[0].values)["raw_epoch"] == 1
    assert capture.runtime_qualified is False


def test_event_field_order_is_not_an_implicit_identity():
    rearranged = SNAPSHOT.replace(b"raw_cookie=6 raw_scope=0", b"raw_scope=0 raw_cookie=6")
    assert parse_serial(FRAME.replace(SNAPSHOT, rearranged)) == parse_serial(FRAME)


def test_local_loss_is_retained_without_inventing_global_counts():
    raw = FRAME.replace(b"attempted=1", b"attempted=2").replace(b"failed=0", b"failed=1")
    result = parse_serial(raw)
    assert result.counts == (2, 1, 1, 1, 0, 0) and result.actual_global_drops is None


def test_empty_complete_frame_has_no_invented_snapshot():
    raw = META + b"CPR2_COUNT attempted=0 reserved=0 committed=0 failed=0 discarded=0 pending=0\n"
    assert parse_serial(raw + b"CPR2_END\nCPR2_EXIT ok=1\n").events == ()


@pytest.mark.parametrize(
    ("kind", "body"),
    [
        ("SEED_BEGIN", ""),
        ("NODE", "object=6 role=OFD origin=FIRST_OBSERVED stage=PRE_ARM_SEED generation=0"),
        ("NODE", "object=6 role=OFD origin=ALLOCATION stage=POST_INIT_ALLOC generation=0"),
        (
            "SEED_SLOT",
            "task=8 source=2 fd=5 presence=NULL ofd=0 origin=UNAVAILABLE open=0 cloexec=0",
        ),
        (
            "SEED_SLOT",
            "task=8 source=2 fd=5 presence=PRESENT ofd=6 origin=ALLOCATION open=1 cloexec=1",
        ),
        ("SEED_END", "parent=1 source=2 result=COMPLETE"),
        ("SEED_ABORT", "reason=INJECTED"),
        ("SEED_REJECT", "reason=SEED_NOT_COMPLETE"),
        ("ARM_REJECT", "reason=SEED_NOT_COMPLETE"),
        ("ARM", "status=ACTIVE"),
        ("STOP", "result=DRAINED_EMITTERS_ONLY"),
        ("BEGIN", "scan_bound=64 capacity=512"),
        ("BITMAPS", "open_fds=0 cloexec=0"),
        ("POINTER_READ", "fd=5 presence=PRESENT"),
        ("REFERENCE", "fd=5 read_ordinal=1"),
        ("CLEAR_OPEN", "fd=5 read_ordinal=1"),
        ("STORE", "fd=5 read_ordinal=1 presence=PRESENT"),
        ("COPY_RETURN", "result=SUCCESS tail_zeroed=-1 reason=NONE"),
        ("TASK_FINALIZE", "result=COMMITTED reason=NONE"),
        ("ALLOC_FREE", "reason=INJECTED"),
    ],
)
def test_each_source_stage_retains_its_own_field_semantics(kind, body):
    context_kinds = {
        "BEGIN",
        "BITMAPS",
        "POINTER_READ",
        "REFERENCE",
        "CLEAR_OPEN",
        "STORE",
        "COPY_RETURN",
        "TASK_FINALIZE",
        "ALLOC_FREE",
    }
    context = (
        " copy=1 local=1 scope=8 actor=1 task=8 source=2 dest=9" if kind in context_kinds else ""
    )
    payload = f"CPR2_EVENT n=1 epoch=1 kind={kind}{context}" + (" " + body if body else "") + "\n"
    capture = parse_serial(FRAME.replace(SNAPSHOT, payload.encode()))
    assert capture.events[0].kind == kind and capture.status == "BLOCKED"


@pytest.mark.parametrize(
    "body",
    [
        b"kind=NODE object=0 role=OFD origin=FIRST_OBSERVED stage=PRE_ARM_SEED generation=0",
        b"kind=NODE object=6 role=OFD origin=ALLOCATION stage=PRE_ARM_SEED generation=0",
        b"kind=NODE object=6 role=OFD origin=ALLOCATION stage=POST_INIT_ALLOC generation=1",
        b"kind=SEED_SLOT task=8 source=2 fd=5 presence=NULL ofd=6 "
        b"origin=ALLOCATION open=0 cloexec=0",
        b"kind=SEED_SLOT task=8 source=2 fd=5 presence=PRESENT ofd=0 "
        b"origin=ALLOCATION open=1 cloexec=0",
        b"kind=SEED_SLOT task=8 source=2 fd=5 presence=PRESENT ofd=6 "
        b"origin=ALLOCATION open=2 cloexec=0",
        b"kind=STOP result=QUALIFIED",
        b"kind=COPY_RETURN copy=1 local=1 scope=8 actor=1 task=8 source=2 dest=9 "
        b"result=SUCCESS tail_zeroed=-2 reason=NONE",
    ],
)
def test_contradictory_other_stage_values_reject(body):
    payload = b"CPR2_EVENT n=1 epoch=1 " + body + b"\n"
    with pytest.raises(ValueError):
        parse_serial(FRAME.replace(SNAPSHOT, payload))


def test_small_buffer_profile_and_pending_counts_remain_blocked():
    small = FRAME.replace(b"case=NORMAL", b"case=SMALL_BUFFER").replace(
        b"capacity=512", b"capacity=128"
    )
    assert parse_serial(small).capacity == 128
    pending = FRAME.replace(b"attempted=1 reserved=1", b"attempted=2 reserved=2").replace(
        b"pending=0", b"pending=1"
    )
    assert parse_serial(pending).counts == (2, 2, 1, 0, 0, 1)


def test_duplicate_metadata_and_nonmonotonic_event_ids_reject():
    for raw in (
        FRAME.replace(SNAPSHOT, META + SNAPSHOT),
        FRAME.replace(b"n=1 epoch=1", b"n=0 epoch=1"),
        FRAME.replace(b"kind=TAG_SNAPSHOT", b"kind=TAG_SNAPSHOT kind=TAG_SNAPSHOT"),
        FRAME + b"CPR2_EVENT n=2 epoch=1 kind=SEED_BEGIN\n",
    ):
        with pytest.raises(ValueError):
            parse_serial(raw)
