"""Catch invented copy cuts, collapsed unknowns and wrong source-stage substitution."""

import copy
import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest


def receipt():
    """Hand-specified SYNTHETIC private64 copy, not reconstructed driving/VM data."""
    open_bits = [False] * 64
    cloexec = [False] * 64
    open_bits[0] = cloexec[0] = True  # Reserved NULL, stale copied CLOEXEC bit.
    for fd in (5, 40):
        open_bits[fd] = cloexec[fd] = True
    events = [
        {"n": 1, "kind": "BEGIN", "scan_bound": 64, "capacity": 64},
        {"n": 2, "kind": "BITMAPS", "open_fds": open_bits, "cloexec": cloexec},
    ]
    for fd in range(64):
        n = 3 + 3 * fd
        present = fd in (5, 40)
        presence, ofd = ("PRESENT", 3) if present else ("NULL", None)
        events += [
            {"n": n, "kind": "READ", "fd": fd, "presence": presence, "ofd": ofd},
            {
                "n": n + 1,
                "kind": "REFERENCE" if present else "CLEAR_OPEN",
                "fd": fd,
                "read_ordinal": n,
            },
            {
                "n": n + 2,
                "kind": "STORE",
                "fd": fd,
                "read_ordinal": n,
                "presence": presence,
                "ofd": ofd,
            },
        ]
    events += [
        {"n": 195, "kind": "COPY_RETURN", "result": "SUCCESS", "tail_zeroed": True},
        {"n": 196, "kind": "TASK_FINALIZE", "result": "COMMITTED"},
    ]
    return {
        "schema": "fork-copy-evidence-design-v1",
        "evidence_class": "SYNTHETIC_ONLY",
        "context": {
            "source_profile": "PR38_LINUX_6_12_113_X86_64_PRIVATE64",
            "source_sha256": "129263d5c6923429eb2e98d93a67b9b6e6b2de7de10a48b924595adeab518284",
            "fork_sha256": "32788952871be9b6cc106a47cfd6f6d0b7207cd3a83eafa4aa60f46af5462b7d",
            "fdtable_sha256": "86b2acb622e4bd1d03eeeaa4fe2b8f3bf33ce1779ec32d959402b47d42857dd4",
            "boot_scope": "synthetic-boot",
            "scope_id": 1,
            "copy_attempt_id": 1,
            "actor_task_id": 1,
            "subject_task_id": 4,
            "source_table_id": 2,
            "destination_table_id": 5,
            "root_copy": False,
            "clone_mode": "PRIVATE_FORK",
        },
        "events": events,
        "accounting": {
            "attempted": 196,
            "reserved": 196,
            "committed": 196,
            "failed": 0,
            "discarded": 0,
            "pending": 0,
        },
    }


def api():
    assert importlib.util.find_spec("tests.fork_copy_design.model") is not None, "missing copy API"
    return importlib.import_module("tests.fork_copy_design.model")


def test_complete_copy_has64_slots196_stages_but_never_an_atomic_cut_or_authority():
    result = api().evaluate(receipt())
    assert result.consistent and result.reasons == () and len(result.slots) == 64
    assert result.slots[5].file_id == result.slots[40].file_id == 3
    assert result.slots[5].binding_cloexec is True
    assert result.status == "BLOCKED" and result.actual_global_drops is None
    assert result.actual_prohibited_operations is None
    assert not result.atomic_cut_proven and not result.runtime_producer_implemented
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)
    with pytest.raises(FrozenInstanceError):
        result.slots[0].fd = 8


def test_reserved_null_clears_open_not_copied_cloexec_and_never_becomes_unknown_present():
    result = api().evaluate(receipt())
    slot = result.slots[0]
    assert slot.presence == "NULL" and slot.file_id is None
    assert slot.open_after is False and slot.cloexec_bitmap_bit is True
    assert slot.binding_cloexec is None


def test_present_unknown_ofd_keeps_presence_and_does_not_invent_lifetime_equality():
    data = receipt()
    data["events"][17]["ofd"] = data["events"][19]["ofd"] = None
    result = api().evaluate(data)
    assert not result.consistent and "OFD_ID_UNAVAILABLE" in result.reasons
    assert result.slots[5].presence == "PRESENT" and result.slots[5].file_id is None
    assert result.slots[5].open_after is True


def test_root_parent_unknown_is_diagnostic_but_nonroot_creator_cannot_be_erased():
    data = receipt()
    data["context"].update(
        root_copy=True, subject_task_id=1, actor_task_id=None, source_table_id=None
    )
    result = api().evaluate(data)
    assert not result.consistent and "SOURCE_CONTEXT_UNAVAILABLE" in result.reasons
    data["context"].update(root_copy=False, subject_task_id=4)
    result = api().evaluate(data)
    assert not result.consistent and "DESCENDANT_CREATOR_UNAVAILABLE" in result.reasons


def test_unavailable_bitmap_is_not_actual_false():
    data = receipt()
    data["events"][1]["cloexec"][5] = None
    unknown = api().evaluate(data)
    assert not unknown.consistent and unknown.slots[5].binding_cloexec is None
    data["events"][1]["cloexec"][5] = False
    zero = api().evaluate(data)
    assert zero.consistent and zero.slots[5].binding_cloexec is False
    assert unknown.digest != zero.digest


def test_unknown_open_bitmap_never_becomes_an_observed_true_child_open_bit():
    data = receipt()
    data["events"][1]["open_fds"][5] = None
    result = api().evaluate(data)
    assert not result.consistent and "BITMAP_UNAVAILABLE" in result.reasons
    assert result.slots[5].open_after is None and result.slots[5].binding_cloexec is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["events"].pop(17),  # Missing fd5 read.
        lambda d: d["events"].__setitem__(slice(18, 20), list(reversed(d["events"][18:20]))),
        lambda d: d["events"][19].__setitem__("read_ordinal", 3),
        lambda d: d["events"][19].__setitem__("ofd", 7),
        lambda d: d["events"][18].__setitem__("kind", "CLEAR_OPEN"),
        lambda d: d["events"][3].__setitem__("kind", "REFERENCE"),
        lambda d: d["events"][17].__setitem__("presence", "UNAVAILABLE"),
        lambda d: d["events"][1]["open_fds"].__setitem__(5, False),
        lambda d: d["events"][17].__setitem__("fd", 4),
        lambda d: d["events"][17].__setitem__("fd", True),
        lambda d: d["events"][17].__setitem__("ofd", 3.0),
        lambda d: d["events"][17].__setitem__("ofd", 2**64),
        lambda d: d["events"][0].__setitem__("scan_bound", 5),
        lambda d: d["events"][0].__setitem__("capacity", 128),
        lambda d: d["events"][2].__setitem__("n", 2),
        lambda d: d["events"][19].__setitem__("n", 21),
        lambda d: d["context"].__setitem__("clone_mode", "CLONE_FILES"),
        lambda d: d["context"].__setitem__("source_sha256", "0" * 64),
        lambda d: d["context"].__setitem__("destination_table_id", 2),
        lambda d: d["context"].__setitem__("actor_task_id", 4),
        lambda d: d["context"].__setitem__("copy_attempt_id", 0),
        lambda d: d["context"].__setitem__("boot_scope", ""),
        lambda d: d.__setitem__("evidence_class", "OBSERVED_UNTRUSTED"),
        lambda d: d.__setitem__("application_authorized", True),
        lambda d: d["events"][2].__setitem__("surprise", None),
        lambda d: d["events"][1]["cloexec"].pop(),
        lambda d: d["accounting"].__setitem__("attempted", False),
        lambda d: d["accounting"].__setitem__("reserved", 195),
        lambda d: d["accounting"].__setitem__("pending", 1),
        lambda d: d["events"][-2].__setitem__("tail_zeroed", None),
        lambda d: d["events"][-2].__setitem__("result", "FAILED"),
        lambda d: d["events"][-1].__setitem__("result", "ABORTED"),
        lambda d: d["events"][-1].__setitem__("result", "UNAVAILABLE"),
    ],
)
def test_wrong_stage_pairing_cohort_missing_unknown_or_malformed_evidence_is_not_consistent(mutate):
    data = receipt()
    mutate(data)
    result = api().evaluate(data)
    assert not result.consistent and result.reasons
    assert result.atomic_cut_proven is False and result.status == "BLOCKED"
    assert all(v is False for _, v in result.permissions)


def test_existing128_buffer_cannot_hide_missing68_copy_records_behind_balanced_counters():
    data = receipt()
    data["events"] = data["events"][:128]
    data["accounting"].update(reserved=128, committed=128, failed=68)
    result = api().evaluate(data)
    assert not result.consistent and "LOCAL_RESERVATION_LOSS" in result.reasons


def test_unknown_accounting_is_not_zero():
    data = receipt()
    data["accounting"]["failed"] = None
    result = api().evaluate(data)
    assert not result.consistent and "ACCOUNTING_UNAVAILABLE" in result.reasons


def test_received_event_outside_declared_attempt_domain_is_visible():
    data = receipt()
    data["accounting"].update(attempted=195, reserved=195, committed=195)
    result = api().evaluate(data)
    assert not result.consistent and "EMISSION_ACCOUNTING_MISMATCH" in result.reasons


def test_completely_empty_source_still_requires64_slot_reads_not_zero_open_count():
    data = receipt()
    data["events"][1].update(open_fds=[False] * 64, cloexec=[False] * 64)
    for fd in (5, 40):
        read, branch, store = data["events"][2 + 3 * fd : 5 + 3 * fd]
        read.update(presence="NULL", ofd=None)
        branch["kind"] = "CLEAR_OPEN"
        store.update(presence="NULL", ofd=None)
    result = api().evaluate(data)
    assert result.consistent and len(result.slots) == 64
    assert all(s.presence == "NULL" and s.open_after is False for s in result.slots)


def test_cookie_roles_cannot_collide_but_repeated_ofd_aliases_are_allowed():
    data = receipt()
    for row in data["events"]:
        if row.get("ofd") == 3:
            row["ofd"] = 4
    result = api().evaluate(data)
    assert not result.consistent and "SOURCE_COOKIE_ROLE_COLLISION" in result.reasons


@pytest.mark.parametrize("variant", ["namespace", "ofd"])
def test_root_scope_cookie_remains_a_task_role_even_when_creator_is_a_descendant(variant):
    data = receipt()
    if variant == "namespace":
        data["context"]["scope_id"] = 2
    else:
        data["context"]["actor_task_id"] = 6
        for row in data["events"]:
            if row.get("ofd") == 3:
                row["ofd"] = 1
    result = api().evaluate(data)
    assert not result.consistent and "SOURCE_COOKIE_ROLE_COLLISION" in result.reasons


def test_store_bool_cannot_impersonate_integer_one_even_when_equality_matches():
    data = receipt()
    data["context"].update(scope_id=6, actor_task_id=6, subject_task_id=7)
    for row in data["events"]:
        if row.get("ofd") == 3:
            row["ofd"] = 1
    assert api().evaluate(data).consistent
    data["events"][19]["ofd"] = True
    result = api().evaluate(data)
    assert not result.consistent and "EXACT_UINT_REQUIRED" in result.reasons


def test_structurally_valid_unrelated_stage_in_reference_position_is_reasoned_rejection():
    data = receipt()
    data["events"][18] = {"n": 19, "kind": "TASK_FINALIZE", "result": "COMMITTED"}
    result = api().evaluate(data)
    assert not result.consistent and "COPY_BRANCH_STAGE" in result.reasons


def test_digest_is_order_independent_attempt_sensitive_and_result_defensively_copied():
    data = receipt()
    before = copy.deepcopy(data)
    result = api().evaluate(data)
    assert data == before
    reordered = {k: data[k] for k in reversed(data)}
    assert api().evaluate(reordered).digest == result.digest
    data["context"]["copy_attempt_id"] = 2
    assert api().evaluate(data).digest != result.digest
    data["events"][1]["cloexec"][5] = False
    assert result.slots[5].binding_cloexec is True


@pytest.mark.parametrize("data", [None, True, b"CPS_META version=1", [], "receipt", float("nan")])
def test_arbitrary_objects_and_actual_cps_frames_are_not_synthetic_receipts(data):
    result = api().evaluate(data)
    assert not result.consistent and result.reasons
