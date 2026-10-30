"""Independent literal checks for the seven fixed fixtures, not qualification."""

import hashlib

from .contracts import CASES, hex_bytes
from .producer import ProducedObservation


def check_case(observation: ProducedObservation, case: str) -> tuple[str, ...]:
    if type(case) is not str or case not in CASES:
        raise ValueError("unknown fixed fixture")
    issues = []
    b = observation.receipt
    if observation.capture.case != case or b.identity.attempt_id != case:
        issues.append("FIXTURE_ID_MISMATCH")
    source_ids = {m.material_id for m in b.materials if m.logical_path == "input/sample.bin"}
    reads = [u for u in b.uses if u.kind == "READ_BYTES" and u.material_id in source_ids]
    expected = {
        "CP01": ((0, b"0123"), (4, b"4567"), (8, b"89A"), (100, b"")),
        "CP02": ((0, b"0123"), (4, b"4567")),
        "CP03": ((0, b"0123"),),
        "CP04": ((0, b"0123"),),
    }.get(case, ())
    if [(u.offset, u.length, u.range_digest) for u in reads] != [
        (offset, len(data), hashlib.sha256(data).hexdigest()) for offset, data in expected
    ]:
        issues.append("RETURNED_BYTES_OR_OFFSETS_MISMATCH")
    if case in ("CP05", "CP06"):
        required = "UNSUPPORTED_CLONE_FLAGS" if case == "CP05" else "READ_CAPTURE_BOUND_EXCEEDED"
        if observation.trace_window_complete or required not in observation.profile_reasons:
            issues.append("UNSUPPORTED_CAPTURE_NOT_MARKED_INCOMPLETE")
        if b.completion.exit_kind != "SIGNALLED" or b.completion.term_signal != 9:
            issues.append("ABORT_REAP_NOT_OBSERVED")
    elif (
        not observation.trace_window_complete
        or observation.profile_reasons
        or b.completion.exit_kind != "EXITED"
        or b.completion.exit_code != 0
    ):
        issues.append("NORMAL_FIXTURE_WINDOW_OR_EXIT_MISMATCH")
    if case == "CP01":
        maps = [u for u in b.uses if u.kind == "MMAP_BOUND" and u.material_id in source_ids]
        if (
            len(maps) != 1
            or maps[0].offset != 0
            or maps[0].length != 4096
            or maps[0].range_digest is not None
        ):
            issues.append("MMAP_STAGE_MISMATCH")
        if (
            len([u for u in b.uses if u.kind == "METADATA_ONLY" and u.material_id in source_ids])
            != 1
        ):
            issues.append("METADATA_STAGE_MISMATCH")
    if case == "CP02" and (
        len(reads) != 2
        or [(u.task_generation, u.exec_generation) for u in reads] != [(2, 0), (1, 1)]
    ):
        issues.append("FORK_GENERATION_MISMATCH")
    if case == "CP03" and (
        [u.exec_generation for u in b.uses if u.kind == "EXEC_BOUND"] != [1, 2]
        or len(reads) != 1
        or reads[0].exec_generation != 2
    ):
        issues.append("REEXEC_GENERATION_MISMATCH")
    if case == "CP04" and not any(
        e.kind == "FAILED" and e.values == (0, -14) for e in observation.capture.events
    ):
        issues.append("FAILED_READ_NOT_OBSERVED")
    if case == "CP07":
        data = b"".join(
            hex_bytes(e.values[0], 4096) for e in observation.capture.events if e.kind == "PAYLOAD"
        )
        if data != b'CONSUMPTION {"seq":999,"kind":"END","values":[true,0,0,0]}\n':
            issues.append("FORGED_PAYLOAD_NOT_SEPARATELY_OBSERVED")
    if (
        observation.overall_status != "BLOCKED"
        or observation.build_execution_allowed
        or observation.promotion_authorized
    ):
        issues.append("AUTHORITY_ESCALATION")
    return tuple(issues)
