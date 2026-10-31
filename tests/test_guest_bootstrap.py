"""Literal proposed CPB wire examples,not actual telemetry or producer evidence."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest

CASES = (
    "NORMAL",
    "SEED_LOSS",
    "SMALL_BUFFER",
    "SEED_FAIL",
    "UNSEEDED_OFD",
    "RESEED_REJECTED",
    "EARLY_ARM_REJECTED",
    "CONSTRUCTOR_FAIL",
    "TASK_FAIL",
    "ALLOC_FAIL",
)


def api():
    assert importlib.util.find_spec("tests.guest_bootstrap") is not None, "missing CPB API"
    return (
        importlib.import_module("tests.guest_bootstrap.wire").parse_serial,
        importlib.import_module("tests.guest_bootstrap.model").assess,
    )


def frame(case="NORMAL"):
    rows = []

    def emit(kind, **payload):
        rows.append(
            f"CPB_EVENT n={len(rows) + 1} epoch=1 kind={kind}"
            + "".join(f" {k}={v}" for k, v in payload.items())
        )

    def node(cookie, role, origin):
        emit(
            "NODE",
            object=cookie,
            role=role,
            origin=origin,
            stage="PRE_ARM_SEED" if origin == "FIRST_OBSERVED" else "POST_INIT_ALLOC",
            generation=0,
        )

    if case == "EARLY_ARM_REJECTED":
        emit("ARM_REJECT", reason="SEED_NOT_COMPLETE")
    emit("SEED_BEGIN")
    node(1, "TASK", "FIRST_OBSERVED")
    node(2, "NAMESPACE", "FIRST_OBSERVED")
    seeded = {0: 3, 1: 3, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0 if case == "UNSEEDED_OFD" else 7, 40: 6}
    seen = set()
    for fd in range(64):
        cookie = seeded.get(fd, 0)
        if cookie and cookie not in seen:
            node(cookie, "OFD", "FIRST_OBSERVED")
            seen.add(cookie)
        emit(
            "SEED_SLOT",
            task=1,
            source=2,
            fd=fd,
            presence="PRESENT" if fd in seeded else "NULL",
            ofd=cookie,
            origin="FIRST_OBSERVED" if cookie else "UNAVAILABLE",
            open=int(fd in seeded),
            cloexec=int(fd in (5, 6, 40)),
        )
        if case == "SEED_FAIL":
            emit("SEED_ABORT", reason="INJECTED")
            break
    if case != "SEED_FAIL":
        emit("SEED_END", parent=1, source=2, result="COMPLETE")
        if case == "RESEED_REJECTED":
            emit("SEED_REJECT", reason="ALREADY_ATTEMPTED")
        emit("ARM", status="ACTIVE")
        root = 7 if case == "UNSEEDED_OFD" else 8
        root_ns, post_ofd, child, child_ns = root + 1, root + 2, root + 3, root + 4
        for attempt in (1, 2):
            actor, task, source, dest = (
                (1, root, 2, root_ns) if attempt == 1 else (root, child, root_ns, child_ns)
            )
            node(task, "TASK", "ALLOCATION")
            if attempt == 2 and case == "ALLOC_FAIL":
                payloads = [
                    dict(
                        kind="COPY_RETURN", result="FAILED", tail_zeroed=-1, reason="ALLOC_INJECTED"
                    ),
                    dict(kind="TASK_FINALIZE", result="ABORTED", reason="COPY_FAILED"),
                ]
                dest = 0
            else:
                node(dest, "NAMESPACE", "ALLOCATION")
                payloads = [dict(kind="BEGIN", scan_bound=64, capacity=64)]
                if attempt == 2 and case == "CONSTRUCTOR_FAIL":
                    payloads += [
                        dict(kind="ALLOC_FREE", reason="CONSTRUCTOR_INJECTED"),
                        dict(
                            kind="COPY_RETURN",
                            result="FAILED",
                            tail_zeroed=-1,
                            reason="CONSTRUCTOR_INJECTED",
                        ),
                        dict(kind="TASK_FINALIZE", result="ABORTED", reason="COPY_FAILED"),
                    ]
                else:
                    present = dict(seeded)
                    if attempt == 2:
                        present.update({7: post_ofd, 41: post_ofd})
                    opened = sum(1 << fd for fd in present)
                    cloexec = sum(
                        1 << fd for fd in ((5, 6, 40) if attempt == 1 else (5, 6, 7, 40, 41))
                    )
                    payloads.append(dict(kind="BITMAPS", open_fds=opened, cloexec=cloexec))
                    for fd in range(64):
                        cookie = present.get(fd, 0)
                        origin = (
                            ("ALLOCATION" if cookie == post_ofd else "FIRST_OBSERVED")
                            if cookie
                            else "UNAVAILABLE"
                        )
                        read = len(payloads) + 1
                        payloads += [
                            dict(
                                kind="READ",
                                fd=fd,
                                presence="PRESENT" if fd in present else "NULL",
                                ofd=cookie,
                                origin=origin,
                            ),
                            dict(
                                kind="REFERENCE" if fd in present else "CLEAR_OPEN",
                                fd=fd,
                                read_ordinal=read,
                            ),
                            dict(
                                kind="STORE",
                                fd=fd,
                                read_ordinal=read,
                                presence="PRESENT" if fd in present else "NULL",
                                ofd=cookie,
                                origin=origin,
                            ),
                        ]
                    payloads += [
                        dict(kind="COPY_RETURN", result="SUCCESS", tail_zeroed=1, reason="NONE"),
                        dict(
                            kind="TASK_FINALIZE",
                            result="ABORTED"
                            if attempt == 2 and case == "TASK_FAIL"
                            else "COMMITTED",
                            reason="TASK_INJECTED"
                            if attempt == 2 and case == "TASK_FAIL"
                            else "NONE",
                        ),
                    ]
            for local, payload in enumerate(payloads, 1):
                emit(
                    **payload,
                    copy=attempt,
                    local=local,
                    scope=root,
                    actor=actor,
                    task=task,
                    source=source,
                    dest=dest,
                )
            if attempt == 1:
                node(post_ofd, "OFD", "ALLOCATION")
    else:
        root = 0
    emit("STOP", result="DRAINED_EMITTERS_ONLY")
    attempted = len(rows)
    if case == "SEED_LOSS":
        rows = [r for r in rows if "kind=NODE object=6 " not in r]
    if case == "SMALL_BUFFER":
        rows = rows[:128]
    count = len(rows)
    return (
        "CPB_DRIVER ok=1 forked=" + str(int(case != "SEED_FAIL")) + "\n"
        f"CPB_META version=1 case={case} release=6.12.113-cpbootstrap-v1 cpus=1 "
        f"capacity={128 if case == 'SMALL_BUFFER' else 512} "
        f"copies={0 if case == 'SEED_FAIL' else 2} "
        f"root={root} boot_nonce=1234567890abcdef1234567890abcdef epoch=1 "
        f"seed_walk={'ABORTED' if case == 'SEED_FAIL' else 'COMPLETE'}\n"
        f"CPB_COUNT attempted={attempted} reserved={count} committed={count} "
        f"failed={attempted - count} discarded=0 pending=0\n"
        + "\n".join(rows)
        + "\nCPB_END\nCPB_EXIT ok=1\n"
    ).encode()


def test_normal_records_seed_origin_alias_and_new_allocations_without_authority():
    parse, assess = api()
    capture = parse(frame())
    result = assess(capture)
    assert capture.attempted == 472 and len(capture.events) == 472
    assert result.local_accounting_balanced and result.seed_walk_recorded_complete
    assert result.committed_stage_sequences == (1, 2)
    assert result.seed_to_first_copy_links == (
        (0, 3),
        (1, 3),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (40, 6),
    )
    assert result.first_observed_cookies == (1, 2, 3, 4, 5, 6, 7)
    assert result.allocation_cookies == (8, 9, 10, 11, 12)
    assert capture.root_id == 8 and capture.root_id != 1
    assert not result.unknown_present_count and not result.missing_origin_witness_ids
    assert result.evidence_class == "OBSERVED_UNTRUSTED" and result.status == "BLOCKED"
    assert (
        not result.allocation_history_complete
        and not result.atomic_cut_proven
        and not result.runtime_qualified
    )
    assert result.actual_global_drops is None and all(v is False for _, v in result.permissions)
    with pytest.raises(FrozenInstanceError):
        capture.events[0].kind = "NODE"


@pytest.mark.parametrize(
    ("case", "attempted", "received", "copies", "seeded"),
    [
        ("SEED_LOSS", 472, 471, (1, 2), True),
        ("SMALL_BUFFER", 472, 128, (), True),
        ("SEED_FAIL", 7, 7, (), False),
        ("UNSEEDED_OFD", 471, 471, (1, 2), True),
        ("RESEED_REJECTED", 473, 473, (1, 2), True),
        ("EARLY_ARM_REJECTED", 473, 473, (1, 2), True),
        ("CONSTRUCTOR_FAIL", 280, 280, (1,), True),
        ("TASK_FAIL", 472, 472, (1,), True),
        ("ALLOC_FAIL", 277, 277, (1,), True),
    ],
)
def test_actual_fault_and_rejected_command_grammar_never_implies_history(
    case, attempted, received, copies, seeded
):
    parse, assess = api()
    capture = parse(frame(case))
    result = assess(capture)
    assert capture.attempted == attempted and len(capture.events) == received
    assert result.local_accounting_balanced and result.committed_stage_sequences == copies
    assert result.seed_walk_recorded_complete is seeded
    assert not result.allocation_history_complete and result.status == "BLOCKED"
    if case == "SEED_LOSS":
        assert result.missing_origin_witness_ids == (6,)
        assert (5, 6) not in result.seed_to_first_copy_links and (
            40,
            6,
        ) not in result.seed_to_first_copy_links
    if case == "UNSEEDED_OFD":
        assert result.unknown_present_count == 2 and (6, 7) not in result.seed_to_first_copy_links


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"version=1", b"version=2"),
        (b"epoch=1", b"epoch=2"),
        (b"cpus=1", b"cpus=2"),
        (b"case=NORMAL", b"case=OTHER"),
        (b"boot_nonce=1234567890abcdef1234567890abcdef", b"boot_nonce=0"),
        (b"n=2 epoch", b"n=1 epoch"),
        (b"origin=FIRST_OBSERVED", b"origin=TRUSTED_BIRTH"),
        (b"role=TASK", b"role=UNKNOWN"),
        (b"generation=0", b"generation=1"),
        (b"ofd=0", b"ofd=-1"),
        (b"fd=63", b"fd=64"),
        (b"CPB_END", b""),
        (b"CPB_EXIT ok=1", b"CPB_EXIT ok=0"),
        (b"kind=READ", b"kind=APPLICATION"),
        (b"copy=2 local=", b"copy=3 local="),
        (b"copy=2 local=", b"copy=0 local="),
    ],
)
def test_unknown_or_wrong_wire_cohort_is_rejected_not_silently_upgraded(before, after):
    parse, _ = api()
    with pytest.raises(ValueError):
        parse(frame().replace(before, after))


@pytest.mark.parametrize(
    ("before", "after", "reason"),
    [
        (
            b"kind=NODE object=8 role=TASK origin=ALLOCATION stage=POST_INIT_ALLOC",
            b"kind=NODE object=8 role=TASK origin=FIRST_OBSERVED stage=PRE_ARM_SEED",
            "POST_ARM_SEED_ORIGIN",
        ),
        (
            b"kind=NODE object=1 role=TASK origin=FIRST_OBSERVED stage=PRE_ARM_SEED",
            b"kind=NODE object=1 role=TASK origin=ALLOCATION stage=POST_INIT_ALLOC",
            "PRE_ARM_ALLOCATION_ORIGIN",
        ),
        (
            b"kind=READ fd=5 presence=PRESENT ofd=6 origin=FIRST_OBSERVED",
            b"kind=READ fd=5 presence=PRESENT ofd=6 origin=ALLOCATION",
            "READ_STORE_ORIGIN_MISMATCH",
        ),
        (
            b"kind=SEED_SLOT task=1 source=2 fd=5 presence=PRESENT ofd=6 origin=FIRST_OBSERVED",
            b"kind=SEED_SLOT task=1 source=2 fd=5 presence=PRESENT ofd=6 origin=ALLOCATION",
            "OBJECT_ORIGIN_MISMATCH",
        ),
        (
            b"kind=STORE fd=5 read_ordinal=18",
            b"kind=STORE fd=5 read_ordinal=3",
            "READ_PAIR_MISMATCH",
        ),
        (
            b"result=COMMITTED reason=NONE",
            b"result=COMMITTED reason=TASK_INJECTED",
            "TERMINAL_REASON_CONTRADICTION",
        ),
        (
            b"result=SUCCESS tail_zeroed=1 reason=NONE",
            b"result=SUCCESS tail_zeroed=1 reason=CONSTRUCTOR_INJECTED",
            "TERMINAL_REASON_CONTRADICTION",
        ),
        (b"source=9 dest=12", b"source=2 dest=12", "SOURCE_TASK_NAMESPACE_MISMATCH"),
        (b"actor=8 task=11", b"actor=8 task=8", "COPY_IDENTITY_COLLISION"),
        (b"source=9 dest=12", b"source=9 dest=9", "COPY_IDENTITY_COLLISION"),
        (b"scope=8 actor=8", b"scope=1 actor=8", "MANAGED_ROOT_SCOPE_MISMATCH"),
        (b"scope=8 actor=8", b"scope=8 actor=0", "POSITIVE_ID_OR_ORDINAL_REQUIRED"),
        (b"attempted=472", b"attempted=471", "LOCAL_ACCOUNTING_MISMATCH"),
        (b"kind=NODE object=7 role=OFD", b"kind=NODE object=6 role=OFD", "OBJECT_ID_REISSUED"),
    ],
)
def test_impossible_identity_origin_stage_and_consumed_pair_provenance_cannot_link(
    before, after, reason
):
    parse, assess = api()
    result = assess(parse(frame().replace(before, after)))
    assert reason in result.reasons and result.seed_to_first_copy_links == ()


def test_content_does_not_merge_independent_ofds_or_change_alias_identity():
    parse, assess = api()
    result = assess(parse(frame()))
    links = dict(result.seed_to_first_copy_links)
    assert links[5] == links[40] == 6 and links[6] == 7 and links[5] != links[6]


def test_wire_field_order_does_not_change_consumed_values_or_origin_diagnostics():
    parse, assess = api()
    raw = frame()
    reordered = (
        b"\n".join(
            b" ".join([parts[0], *reversed(parts[1:])])
            if line.startswith((b"CPB_EVENT ", b"CPB_META ", b"CPB_COUNT ", b"CPB_DRIVER "))
            else line
            for line in raw.splitlines()
            for parts in [line.split(b" ")]
        )
        + b"\n"
    )
    assert parse(raw) == parse(reordered)
    assert assess(parse(raw)) == assess(parse(reordered))


@pytest.mark.parametrize("cookie", [1, 2, 8, 9])
def test_missing_parent_or_new_subject_issuance_cannot_be_filled_from_copy_tags(cookie):
    raw = (
        b"\n".join(
            line
            for line in frame().splitlines()
            if f"kind=NODE object={cookie} ".encode() not in line
        )
        + b"\n"
    )
    raw = raw.replace(
        b"reserved=472 committed=472 failed=0", b"reserved=471 committed=471 failed=1"
    )
    parse, assess = api()
    result = assess(parse(raw))
    assert result.missing_origin_witness_ids == (cookie,)
    assert result.seed_to_first_copy_links == ()


def test_unavailable_and_real_zero_bitmap_or_flag_are_distinct():
    parse, assess = api()
    capture = parse(frame("UNSEEDED_OFD"))
    result = assess(capture)
    unknown = next(s for s in result.seed_bindings if s.fd == 6)
    zero = next(s for s in result.seed_bindings if s.fd == 0)
    null = next(s for s in result.seed_bindings if s.fd == 10)
    assert (
        unknown.presence == "PRESENT"
        and unknown.file_id is None
        and unknown.origin == "UNAVAILABLE"
    )
    assert zero.file_id == 3 and zero.binding_cloexec is False
    assert null.file_id is None and null.binding_cloexec is None


@pytest.mark.parametrize("raw", [b"", b"\xff", b"a" * (2**21 + 1), b"CPC_META version=1", True])
def test_old_frames_nonbytes_and_unbounded_inputs_do_not_become_bootstrap_evidence(raw):
    parse, _ = api()
    with pytest.raises(ValueError):
        parse(raw)
