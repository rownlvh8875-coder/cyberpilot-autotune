"""Independent literal CPRv1 fixtures catch stage substitution and invented links."""

import importlib
from dataclasses import FrozenInstanceError

import pytest

from tests.guest_tag_snapshot.fixtures import POINTER, REFERENCE, SNAPSHOT, STORE, frame, line


def api():
    try:
        return (
            importlib.import_module("tests.guest_tag_snapshot.wire").parse_serial,
            importlib.import_module("tests.guest_tag_snapshot.model").assess,
        )
    except ModuleNotFoundError:
        pytest.fail("MISSING_POST_REFERENCE_DIAGNOSTIC")


def test_full_saved_snapshot_remains_unqualified_and_immutable():
    parse, assess = api()
    capture = parse(frame())
    result = assess(capture)
    snap = result.snapshots[0]
    assert (snap.copy_id, snap.fd, snap.raw_cookie, snap.raw_scope) == (1, 5, 6, 0)
    assert (snap.raw_epoch, snap.raw_origin, snap.logical_cookie) == (1, 1, 6)
    assert (snap.pointer_record_n, snap.reference_record_n, snap.store_record_n) == (1, 2, 3)
    assert snap.source_join_complete
    assert snap.generation is snap.lifetime_witness is snap.publication_witness is None
    assert snap.membership_witness is None
    assert result.evidence_class == "OBSERVED_UNTRUSTED" and result.status == "BLOCKED"
    assert result.local_accounting_balanced and not result.local_loss_observed
    assert not result.runtime_qualified and not result.tag_publication_qualified
    assert not result.target_lifetime_proven and not result.source_happens_before_proven
    assert not result.allocation_history_complete and not result.atomic_cut_proven
    assert result.actual_global_drops is result.actual_prohibited_operations is None
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)
    with pytest.raises(FrozenInstanceError):
        snap.raw_cookie = 2


def test_raw_zero_is_available_and_does_not_become_logical_identity():
    parse, assess = api()
    raw = SNAPSHOT.replace(b"raw_cookie=6", b"raw_cookie=0")
    raw = raw.replace(b"raw_epoch=1", b"raw_epoch=0").replace(b"raw_origin=1", b"raw_origin=0")
    snap = assess(parse(frame((POINTER, REFERENCE, STORE, raw)))).snapshots[0]
    assert snap.raw_cookie == 0 and snap.logical_cookie is None and snap.generation is None


@pytest.mark.parametrize("missing", [POINTER, REFERENCE, STORE])
def test_lost_source_marker_is_not_reconstructed(missing):
    parse, assess = api()
    rows = tuple(r for r in (POINTER, REFERENCE, STORE, SNAPSHOT) if r != missing)
    result = assess(parse(frame(rows, failed=1)))
    assert result.local_loss_observed and result.local_accounting_balanced
    assert not result.snapshots[0].source_join_complete
    assert "SOURCE_RECEIPT_UNAVAILABLE" in result.reasons


def test_missing_snapshot_is_not_derived_from_store_or_installed_context():
    parse, assess = api()
    result = assess(parse(frame((POINTER, REFERENCE, STORE), failed=1)))
    assert result.snapshots == () and "SNAPSHOT_RECEIPT_UNAVAILABLE" in result.reasons


@pytest.mark.parametrize(
    "old,new",
    [
        (b"POST_REFERENCE_RAW_V1", b"OLD_CPB"),
        (b"cptagread-v1", b"cpbootstrap-v1"),
        (b"POST_EXISTING_REFERENCE_PRE_STORE", b"PRE_REFERENCE"),
        (b"SAVED_SCALARS_AFTER_STORE", b"TARGET_POINTER_AFTER_STORE"),
        (b"lifetime=UNAVAILABLE", b"lifetime=PROVEN"),
        (b"generation=UNAVAILABLE", b"generation=0"),
        (b"raw_cookie=6", b"raw_cookie=18446744073709551616"),
        (b"raw_cookie=6", b"raw_cookie=-1"),
        (b"raw_cookie=6", b"raw_cookie=06"),
        (b"raw_cookie=6", b"raw_cookie=True"),
        (b"raw_cookie=6", b"raw_cookie=6.0"),
        (b"raw_cookie=6", b"raw_cookie=NaN"),
        (b"raw_cookie=6", b"raw_cookie=6 raw_cookie=6"),
        (b"raw_origin=1", b"raw_origin=3"),
        (b"fd=5", b"fd=64"),
        (b"cpus=1", b"cpus=2"),
        (b"epoch=1", b"epoch=0"),
        (b"CPR_END", b"CPB_END"),
        (b"CPR_DRIVER ok=1", b"CPR_DRIVER ok=0"),
        (b"CPR_EVENT", b"CPB_EVENT"),
    ],
)
def test_wrong_stage_profile_and_noncanonical_values_rejected(old, new):
    parse, _ = api()
    with pytest.raises(ValueError):
        parse(frame().replace(old, new))


@pytest.mark.parametrize("raw", [b"", b"\xff", b"CPR_UNAVAILABLE errno=2\n", b"x" * (2**21 + 1)])
def test_invalid_incomplete_or_oversized_frames_rejected(raw):
    parse, _ = api()
    with pytest.raises(ValueError):
        parse(raw)


@pytest.mark.parametrize(
    "rows",
    [
        (POINTER, REFERENCE.replace(b"fd=5", b"fd=6"), STORE, SNAPSHOT),
        (POINTER, REFERENCE, STORE.replace(b"presence=PRESENT", b"presence=NULL"), SNAPSHOT),
        (POINTER.replace(b"presence=PRESENT", b"presence=NULL"), REFERENCE, STORE, SNAPSHOT),
        (POINTER, REFERENCE, STORE, SNAPSHOT.replace(b"source=2", b"source=3")),
        (POINTER, REFERENCE, STORE, SNAPSHOT.replace(b"read_ordinal=1", b"read_ordinal=2")),
        (POINTER, REFERENCE, STORE, SNAPSHOT.replace(b"local=4", b"local=3")),
        (POINTER, REFERENCE, STORE, SNAPSHOT.replace(b"kind=TAG_SNAPSHOT", b"kind=STORE")),
        (
            POINTER,
            STORE.replace(b"n=3", b"n=2").replace(b"local=3", b"local=2"),
            REFERENCE.replace(b"n=2", b"n=3").replace(b"local=2", b"local=3"),
            SNAPSHOT,
        ),
        (
            POINTER,
            REFERENCE,
            STORE,
            SNAPSHOT,
            SNAPSHOT.replace(b"n=4", b"n=5").replace(b"local=4", b"local=5"),
        ),
    ],
)
def test_contradictory_available_source_context_or_order_rejected(rows):
    parse, assess = api()
    with pytest.raises(ValueError):
        assess(parse(frame(rows, attempted=len(rows))))


def test_unbalanced_counts_do_not_gain_local_completeness():
    parse, assess = api()
    result = assess(parse(frame(attempted=5)))
    assert not result.local_accounting_balanced and "LOCAL_ACCOUNTING_UNBALANCED" in result.reasons


def test_kernel_noise_and_crlf_do_not_change_observed_fields():
    parse, assess = api()
    raw = b"[ 0.1] kernel boot\n" + frame().replace(b"\n", b"\r\n") + b"Power down\n"
    assert assess(parse(raw)) == assess(parse(frame()))


@pytest.mark.parametrize(
    "origin,stage",
    [
        ("FIRST_OBSERVED", "POST_INIT_ALLOC"),
        ("ALLOCATION", "PRE_ARM_SEED"),
        ("UNAVAILABLE", "PRE_ARM_SEED"),
    ],
)
def test_origin_cannot_be_promoted_to_another_stage(origin, stage):
    parse, _ = api()
    node = (
        f"CPR_EVENT n=1 epoch=1 kind=NODE object=6 role=OFD origin={origin} "
        f"stage={stage} generation=0\n"
    ).encode()
    with pytest.raises(ValueError, match="ORIGIN_STAGE"):
        parse(frame((node,), attempted=1))


@pytest.mark.parametrize(
    "presence,ofd,origin",
    [
        ("NULL", 6, "FIRST_OBSERVED"),
        ("PRESENT", 0, "ALLOCATION"),
    ],
)
def test_seed_presence_and_origin_do_not_invent_a_tag(presence, ofd, origin):
    parse, _ = api()
    row = (
        f"CPR_EVENT n=1 epoch=1 kind=SEED_SLOT task=1 source=2 fd=5 "
        f"presence={presence} ofd={ofd} origin={origin} open=1 cloexec=1\n"
    ).encode()
    with pytest.raises(ValueError, match="SEED_TAG"):
        parse(frame((row,), attempted=1))


def test_diagnostic_control_and_multiple_copy_contexts_do_not_supply_witnesses():
    parse, assess = api()
    seed = b"CPR_EVENT n=1 epoch=1 kind=SEED_BEGIN\n"
    begin = line(2, "BEGIN", "scan_bound=64 capacity=64", local=1)
    end = line(3, "COPY_RETURN", "result=SUCCESS tail_zeroed=1 reason=NONE", local=2)
    second = SNAPSHOT.replace(b"n=4", b"n=5").replace(b"copy=1", b"copy=2")
    rows = (seed, begin, end, second)
    result = assess(parse(frame(rows, attempted=5, failed=1)))
    assert result.snapshots[0].lifetime_witness is None
    assert not result.snapshots[0].source_join_complete
    assert result.local_accounting_balanced


@pytest.mark.parametrize(
    "rows",
    [
        (
            POINTER,
            REFERENCE,
            line(3, "CLEAR_OPEN", "fd=5 read_ordinal=1"),
            STORE.replace(b"n=3", b"n=4").replace(b"local=3", b"local=4"),
            SNAPSHOT.replace(b"n=4", b"n=5").replace(b"local=4", b"local=5"),
        ),
        (line(2, "CLEAR_OPEN", "fd=5 read_ordinal=1"), STORE, SNAPSHOT),
        (POINTER.replace(b"PRESENT", b"NULL"), REFERENCE, STORE),
        (POINTER, STORE.replace(b"PRESENT", b"NULL")),
        (POINTER.replace(b"PRESENT", b"NULL"), STORE),
        (POINTER, line(2, "CLEAR_OPEN", "fd=5 read_ordinal=1"), STORE),
        (
            line(2, "CLEAR_OPEN", "fd=5 read_ordinal=1"),
            REFERENCE.replace(b"n=2", b"n=3").replace(b"local=2", b"local=3"),
        ),
        (
            POINTER,
            STORE.replace(b"n=3", b"n=2").replace(b"local=3", b"local=2"),
            REFERENCE.replace(b"n=2", b"n=3").replace(b"local=2", b"local=3"),
        ),
    ],
)
def test_review_i1_contradictory_branches_rejected_even_without_snapshot(rows):
    parse, assess = api()
    with pytest.raises(ValueError):
        assess(
            parse(frame(rows, attempted=max(len(rows), 5), failed=max(len(rows), 5) - len(rows)))
        )


def test_null_branch_without_snapshot_is_a_legitimate_observed_branch():
    parse, assess = api()
    rows = (
        POINTER.replace(b"PRESENT", b"NULL"),
        line(2, "CLEAR_OPEN", "fd=5 read_ordinal=1"),
        STORE.replace(b"PRESENT", b"NULL"),
    )
    result = assess(parse(frame(rows, attempted=3)))
    assert result.snapshots == () and result.reasons == () and result.local_accounting_balanced


@pytest.mark.parametrize(
    "rows",
    [
        (POINTER.replace(b"fd=5", b"fd=6"), REFERENCE, STORE, SNAPSHOT),
        (POINTER.replace(b"fd=5", b"fd=6"), REFERENCE, STORE),
        tuple(
            r.replace(b"read_ordinal=1", b"read_ordinal=9") for r in (REFERENCE, STORE, SNAPSHOT)
        ),
        tuple(
            r.replace(b"read_ordinal=1", b"read_ordinal=2") for r in (REFERENCE, STORE, SNAPSHOT)
        ),
        tuple(r.replace(b"read_ordinal=1", b"read_ordinal=9") for r in (REFERENCE, STORE)),
        (REFERENCE, STORE.replace(b"read_ordinal=1", b"read_ordinal=2")),
        (
            POINTER,
            REFERENCE.replace(b"read_ordinal=1", b"read_ordinal=2"),
            STORE.replace(b"read_ordinal=1", b"read_ordinal=2"),
        ),
        (
            POINTER.replace(b"PRESENT", b"NULL"),
            line(2, "CLEAR_OPEN", "fd=5 read_ordinal=2"),
            STORE.replace(b"PRESENT", b"NULL").replace(b"read_ordinal=1", b"read_ordinal=2"),
        ),
    ],
)
def test_review_i2_visible_foreign_or_future_consumed_ordinal_is_not_missing(rows):
    parse, assess = api()
    with pytest.raises(ValueError):
        assess(parse(frame(rows, attempted=5, failed=5 - len(rows))))


def test_missing_pointer_in_another_copy_is_not_joined_by_equal_local_ordinal():
    parse, assess = api()
    rows = (
        POINTER.replace(b"fd=5", b"fd=6"),
        *(r.replace(b"copy=1", b"copy=2") for r in (REFERENCE, STORE, SNAPSHOT)),
    )
    result = assess(parse(frame(rows, attempted=5, failed=1)))
    assert not result.snapshots[0].source_join_complete
    assert result.snapshots[0].pointer_record_n is None
