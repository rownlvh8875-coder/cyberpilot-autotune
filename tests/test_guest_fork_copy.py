"""Source-wire boundary examples are synthetic tests,not actual capture evidence."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest


def api():
    assert importlib.util.find_spec("tests.guest_fork_copy.model") is not None, (
        "missing observed codec"
    )
    return importlib.import_module("tests.guest_fork_copy.model")


def frame(case="NORMAL"):
    rows = []
    for attempt in (1, 2):
        actor, task, source, dest = (0, 1, 0, 2) if attempt == 1 else (1, 4, 2, 5)
        if attempt == 2 and case == "ALLOC_FAIL":
            dest = 0
        payloads = ["kind=BEGIN scan_bound=64 capacity=64"]
        if attempt == 2 and case == "CONSTRUCTOR_FAIL":
            payloads += [
                "kind=ALLOC_FREE reason=CONSTRUCTOR_INJECTED",
                "kind=COPY_RETURN result=FAILED tail_zeroed=-1 reason=CONSTRUCTOR_INJECTED",
                "kind=TASK_FINALIZE result=ABORTED reason=COPY_FAILED",
            ]
        elif attempt == 2 and case == "ALLOC_FAIL":
            payloads = [
                "kind=COPY_RETURN result=FAILED tail_zeroed=-1 reason=ALLOC_INJECTED",
                "kind=TASK_FINALIZE result=ABORTED reason=COPY_FAILED",
            ]
        else:
            op, cl = (31, 0) if attempt == 1 else (1099511627839, 1099511627808)
            payloads.append(f"kind=BITMAPS open_fds={op} cloexec={cl}")
            for fd in range(64):
                present = fd < 5 or attempt == 2 and fd in (5, 40)
                presence = "PRESENT" if present else "NULL"
                ofd = 3 if attempt == 2 and fd in (5, 40) else 0
                read = len(payloads) + 1
                payloads += [
                    f"kind=READ fd={fd} presence={presence} ofd={ofd}",
                    f"kind={'REFERENCE' if present else 'CLEAR_OPEN'} fd={fd} read_ordinal={read}",
                    f"kind=STORE fd={fd} read_ordinal={read} presence={presence} ofd={ofd}",
                ]
            payloads += [
                "kind=COPY_RETURN result=SUCCESS tail_zeroed=1 reason=NONE",
                "kind=TASK_FINALIZE result=ABORTED reason=TASK_INJECTED"
                if attempt == 2 and case == "TASK_FAIL"
                else "kind=TASK_FINALIZE result=COMMITTED reason=NONE",
            ]
        for local, payload in enumerate(payloads, 1):
            n = len(rows) + 1
            rows.append(
                f"CPC_EVENT n={n} copy={attempt} local={local} scope=1 actor={actor} "
                f"task={task} source={source} dest={dest} {payload}"
            )
    attempted = len(rows)
    if case == "READ_LOSS":
        rows = [r for r in rows if not r.startswith("CPC_EVENT n=214 ")]
    if case == "SMALL_BUFFER":
        rows = rows[:128]
    count = len(rows)
    return (
        "CPC_DRIVER ok=1 root=0 child=0\n"
        f"CPC_META version=1 case={case} release=6.12.113-cpcopy-v1 cpus=1 "
        f"capacity={128 if case == 'SMALL_BUFFER' else 512} copies=2\n"
        f"CPC_COUNT attempted={attempted} reserved={count} committed={count} "
        f"failed={attempted - count} discarded=0 pending=0\n"
        + "\n".join(rows)
        + "\nCPC_END\nCPC_EXIT ok=1\n"
    ).encode()


def test_actual_class_codec_preserves_root_unknown_and_exact_consumed_stages():
    model = api()
    capture = model.parse_serial(frame())
    assert len(capture.events) == 392
    assert capture.events[0].actor_id is None and capture.events[0].source_id is None
    result = model.assess(capture)
    assert result.local_accounting_balanced and not result.local_loss_observed
    assert result.committed_stage_sequences == (1, 2)
    assert not result.identity_complete
    assert "OFD_ID_UNAVAILABLE" in result.reasons
    assert result.evidence_class == "OBSERVED_UNTRUSTED"
    assert result.status == "BLOCKED" and result.actual_global_drops is None
    assert result.atomic_cut_proven is False and all(v is False for _, v in result.permissions)
    with pytest.raises(FrozenInstanceError):
        capture.events[0].task_id = 9


@pytest.mark.parametrize(
    ("case", "records", "failed", "committed", "reason"),
    [
        ("READ_LOSS", 391, 1, (1,), "LOCAL_RESERVATION_LOSS"),
        ("SMALL_BUFFER", 128, 264, (), "COPY_SEQUENCE_INCOMPLETE"),
        ("CONSTRUCTOR_FAIL", 200, 0, (1,), "COPY_CONSTRUCTOR_FAILED"),
        ("TASK_FAIL", 392, 0, (1,), "TASK_ABORTED"),
        ("ALLOC_FAIL", 198, 0, (1,), "COPY_CONSTRUCTOR_FAILED"),
    ],
)
def test_faults_loss_and_abort_never_become_a_committed_child(
    case, records, failed, committed, reason
):
    model = api()
    captured = model.parse_serial(frame(case))
    decision = model.assess(captured)
    assert len(captured.events) == records and captured.failed == failed
    assert decision.local_accounting_balanced
    assert decision.committed_stage_sequences == committed and reason in decision.reasons
    assert decision.status == "BLOCKED" and decision.actual_global_drops is None


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"version=1", b"version=2"),
        (b"cpus=1", b"cpus=2"),
        (b"case=NORMAL", b"case=OTHER"),
        (b"capacity=512", b"capacity=513"),
        (b"scope=1 actor=1 task=4", b"scope=1 actor=0 task=4"),
        (b"n=2 copy", b"n=1 copy"),
        (b"local=2 scope", b"local=1 scope"),
        (b"source=2 dest=5", b"source=2 dest=2"),
        (b"kind=READ fd=0", b"kind=UNSUPPORTED fd=0"),
        (b"ofd=0", b"ofd=-1"),
        (b"open_fds=31", b"open_fds=18446744073709551616"),
        (b"fd=63", b"fd=64"),
        (b"CPC_END", b""),
        (b"CPC_EXIT ok=1", b"CPC_EXIT ok=0"),
    ],
)
def test_wrong_wire_or_source_context_never_silently_falls_back(before, after):
    with pytest.raises(ValueError):
        api().parse_serial(frame().replace(before, after))


def test_wrong_store_pair_and_unknown_read_do_not_pass_mechanical_sequence():
    model = api()
    raw = frame().replace(b"kind=STORE fd=5 read_ordinal=18", b"kind=STORE fd=5 read_ordinal=3")
    result = model.assess(model.parse_serial(raw))
    assert not result.committed_stage_sequences and "READ_PAIR_MISMATCH" in result.reasons


def test_bitmap_zero_is_observed_false_not_unavailable_or_null_binding_cloexec():
    model = api()
    result = model.assess(model.parse_serial(frame()))
    slot = next(s for s in result.slots if s.copy_id == 1 and s.fd == 0)
    assert slot.presence == "PRESENT" and slot.file_id is None
    assert slot.open_after is True and slot.binding_cloexec is False
    null = next(s for s in result.slots if s.copy_id == 1 and s.fd == 6)
    assert null.presence == "NULL" and null.binding_cloexec is None and null.open_after is False


def test_copy_source_namespace_must_match_its_recorded_committed_creator():
    model = api()
    raw = frame().replace(b"source=2 dest=5", b"source=9 dest=5")
    decision = model.assess(model.parse_serial(raw))
    assert decision.committed_stage_sequences == (1,)
    assert "SOURCE_TASK_NAMESPACE_MISMATCH" in decision.reasons


def test_constructor_abort_is_explicit_even_without_a_full_slot_sequence():
    model = api()
    decision = model.assess(model.parse_serial(frame("CONSTRUCTOR_FAIL")))
    assert "TASK_ABORTED" in decision.reasons


def test_inconsistent_observed_counts_remain_visible_without_global_zero():
    model = api()
    raw = frame().replace(b"attempted=392", b"attempted=391")
    decision = model.assess(model.parse_serial(raw))
    assert not decision.local_accounting_balanced
    assert "LOCAL_ACCOUNTING_MISMATCH" in decision.reasons
    assert decision.actual_global_drops is None


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            b"result=SUCCESS tail_zeroed=1 reason=NONE",
            b"result=SUCCESS tail_zeroed=1 reason=CONSTRUCTOR_INJECTED",
        ),
        (b"result=COMMITTED reason=NONE", b"result=COMMITTED reason=TASK_INJECTED"),
        (b"result=ABORTED reason=TASK_INJECTED", b"result=ABORTED reason=NONE"),
    ],
)
def test_terminal_failure_reason_cannot_be_ignored_for_mechanical_admission(before, after):
    model = api()
    case = "TASK_FAIL" if b"ABORTED" in before else "NORMAL"
    result = model.assess(model.parse_serial(frame(case).replace(before, after)))
    assert "TERMINAL_REASON_CONTRADICTION" in result.reasons
    assert result.committed_stage_sequences == ((1,) if case == "TASK_FAIL" else ())


@pytest.mark.parametrize("change", ["OFD_IS_LATER_TASK", "NAMESPACE_IS_LATER_OFD", "SCOPE_DRIFT"])
def test_capture_wide_identity_graph_rejects_role_collisions_and_scope_drift(change):
    raw = frame()
    if change == "OFD_IS_LATER_TASK":
        lines = raw.splitlines()
        raw = (
            b"\n".join(
                line.replace(b"ofd=0", b"ofd=4")
                if b"copy=1 " in line and b"presence=PRESENT" in line
                else line
                for line in lines
            )
            + b"\n"
        )
    elif change == "NAMESPACE_IS_LATER_OFD":
        raw = raw.replace(b"source=0 dest=2", b"source=0 dest=3")
        raw = raw.replace(b"source=2 dest=5", b"source=3 dest=5")
    else:
        raw = raw.replace(b"scope=1 actor=1 task=4", b"scope=8 actor=1 task=4")
    with pytest.raises(ValueError, match="COOKIE_ROLE_COLLISION|COPY_SCOPE_DRIFT"):
        api().parse_serial(raw)


@pytest.mark.parametrize("raw", [b"", b"\xff", b"a" * (2**21 + 1), b"CPS_META version=1", True])
def test_nonbytes_oversize_and_old_frames_are_not_observed_copy_records(raw):
    with pytest.raises(ValueError):
        api().parse_serial(raw)
