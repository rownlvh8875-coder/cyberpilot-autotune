"""AR01–56 TEST_ONLY software assertions; policy rows are not real-world proof."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding
from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    Vector,
    clock,
    complete_vector,
    document,
    mutate_document,
    replace_document,
    unavailable_clock,
)
from tests.diagnostics.actual_binding.legacy_probe import assert_old_exact_reference_rejected
from tests.diagnostics.actual_binding.test_assessment import blocked
from tests.diagnostics.actual_binding.test_state import proc


def scenario(n):
    v = complete_vector()
    status, reason = "REPORTED_BINDING_CONSISTENT", None
    if n == 2:
        v = replace(
            v, bundle=replace(v.bundle, documents=v.bundle.documents[::-1], raw=v.bundle.raw[::-1])
        )
    elif n == 3:
        v = replace_document(v, "baseline", dict(v.bundle.documents)["baseline"] + b"\n")
        status, reason = "REJECTED", "PARSE_INVALID"
    elif n == 5:
        v = complete_vector(raw_changes={"cli_stderr": None})
        status, reason = "INCOMPLETE", "MISSING_RAW"
    elif n == 6:
        v = complete_vector(raw_changes={"cli_stderr": None})
        v = replace(
            v,
            bundle=replace(
                v.bundle, raw=tuple((k, b"" if k == "cli_stderr" else b) for k, b in v.bundle.raw)
            ),
        )
        status, reason = "REJECTED", "RAW_DESCRIPTOR_MISMATCH"
    elif n == 7:
        v = replace(v, bundle=replace(v.bundle, raw=v.bundle.raw[:-1]))
        status, reason = "REJECTED", "ROLE_SET_INVALID"
    elif n == 8:
        v = replace_document(v, "exit", None)
        status, reason = "INCOMPLETE", "MISSING_DOCUMENT"
    elif n == 9:
        raw = dict(v.bundle.raw) | {"record_json": b"CHANGED_TEST_ONLY"}
        v = replace(v, bundle=replace(v.bundle, raw=tuple(raw.items())))
        status, reason = "REJECTED", "RAW_DESCRIPTOR_MISMATCH"
    elif n in (10, 11):
        v = replace(v, **({"pre": None} if n == 10 else {"post": None}))
        status, reason = (
            "INCOMPLETE",
            "MISSING_PRE_REFERENCE" if n == 10 else "MISSING_POST_REFERENCE",
        )
    elif n == 12:
        v = complete_vector(
            body_changes={"intent": {"pre_reference_content_sha256": v.post.snapshot_sha256}}
        )
        status, reason = "REJECTED", "HASH_MISMATCH"
    elif n in (13, 14, 17):
        changed = complete_vector(body_changes={"baseline": {"policy_reference_sha256": "0" * 64}})
        v = Vector(changed.bundle, v.pre, v.post) if n == 13 else changed
        if n == 13:
            status, reason = "REJECTED", "HASH_MISMATCH"
    elif n == 16:
        v = complete_vector(header_changes={"exit": {"synthetic": True}})
        status, reason = "REJECTED", "WRONG_ORIGIN"
    elif n == 18:
        v = mutate_document(v, "exit", lambda d: d["header"].__setitem__("case", "DFD03"))
        status, reason = "REJECTED", "CONTEXT_MISMATCH"
    elif n == 19:
        v = complete_vector(
            header_changes={
                r: {"workflow_attempt_id": "7" * 32}
                for r in ("baseline", "command", "preflight", "intent", "exit", "snapshot")
            }
        )
    elif n in (20, 21):
        ids = dict(document(v, "exit")["body"]["reported_source_ids"])
        ids["guest_capture_id"] = None if n == 21 else "9" * 32
        v = complete_vector(body_changes={"exit": {"reported_source_ids": ids}})
        status, reason = (
            ("INCOMPLETE", "MISSING_CONTEXT") if n == 21 else ("REJECTED", "REPORTED_ID_MISMATCH")
        )
    elif n == 22:
        v = replace(v, pre=replace(v.pre, host_clock_cohort_sha256="9" * 64))
        status, reason = "REJECTED", "CONTEXT_MISMATCH"
    elif n == 23:
        v = complete_vector(header_changes={"exit": {"host_clock_context": clock(generation=1)}})
        status, reason = "REPORTED_TIME_ORDER_UNCOMPARABLE", "CLOCK_CONTEXT_CHANGED"
    elif n == 24:
        v = complete_vector(header_changes={"exit": {"host_clock_context": unavailable_clock()}})
        status, reason = "INCOMPLETE", "CLOCK_CONTEXT_UNAVAILABLE"
    elif n == 25:
        v = complete_vector(
            header_changes={"exit": {"host_clock_context": clock(domain="GUEST_MONOTONIC_NS")}}
        )
        status, reason = "REJECTED", "DOCUMENT_SHAPE_INVALID"
    elif n == 26:
        v = complete_vector(body_changes={"intent": {"mono_ns": 100}})
        status, reason = "REJECTED", "TIME_REVERSED"
    elif n == 27:
        changes = {r: {"mono_ns": 0} for r in ("preflight", "intent", "exit", "snapshot")}
        changes["exit"].update(launch_before_ns=0, launch_after_ns=0, exit_observed_ns=0)
        v = complete_vector(body_changes=changes)
    elif n in (28, 30):
        v = complete_vector(body_changes={"exit": {"host_cli_argv_observed": ["/TEST_ONLY_QEMU"]}})
        status, reason = "REJECTED", "COMMAND_MISMATCH"
    elif n == 29:
        v = complete_vector(body_changes={"exit": {"host_interpreter_sha256_observed": None}})
        status, reason = "INCOMPLETE", "MISSING_CONTEXT"
    elif n == 31:
        v = complete_vector(
            body_changes={
                "exit": dict(
                    capture_outcome="FAILED_REPORTED",
                    failure_stage="LAUNCH",
                    cli_observation=proc("NOT_STARTED", None),
                    qemu_observation=proc("NOT_STARTED", None),
                    launch_before_ns=None,
                    launch_after_ns=None,
                    exit_observed_ns=None,
                )
            }
        )
        status, reason = "INCOMPLETE", "MISSING_CONTEXT"
    elif n == 32:
        v = mutate_document(
            v, "snapshot", lambda d: d["body"].__setitem__("snapshot_sha256", "0" * 64)
        )
        status, reason = "REJECTED", "DOCUMENT_SHAPE_INVALID"
    elif n == 33:
        v = replace_document(v, "baseline", b"\xff")
        status, reason = "REJECTED", "PARSE_INVALID"
    elif n == 34:
        v = complete_vector(body_changes={"preflight": {"mono_ns": False}})
        status, reason = "REJECTED", "DOCUMENT_SHAPE_INVALID"
    elif n == 35:
        v = complete_vector(raw_changes={"initrd": b"x" * 4194305})
        status, reason = "REJECTED", "INPUT_LIMIT"
    elif n in (36, 41):
        v = complete_vector(raw_changes={"cli_stderr": None}) if n == 41 else v
        v = mutate_document(
            v,
            "snapshot",
            lambda d: d["header"]["permissions"].__setitem__("application_authorized", True),
        )
        status, reason = "REJECTED", "PERMISSION_ESCALATION"
    elif n == 42:
        v = replace_document(v, "baseline", b"bad")
        status, reason = "REJECTED", "PARSE_INVALID"
    elif n in (47, 48):
        v = complete_vector(
            raw_changes={
                "record_json": b"\xffnot_json",
                "cli_stdout": b"{bad",
                "exit_receipt": b"not_json",
            }
        )
    elif n == 49:
        env = dict.fromkeys(document(v, "exit")["body"]["host_environment_observed"])
        v = complete_vector(body_changes={"exit": {"host_environment_observed": env}})
        status, reason = "INCOMPLETE", "MISSING_CONTEXT"
    elif n == 50:
        env = dict(document(v, "exit")["body"]["host_environment_observed"]) | {"LANG": "OTHER"}
        v = complete_vector(
            body_changes={
                "exit": {
                    "host_environment_observed": env,
                    "host_interpreter_sha256_observed": "0" * 64,
                }
            }
        )
        status, reason = "REJECTED", "INTERPRETER_MISMATCH"
    elif n in (51, 52, 53, 55):
        term, code = {
            51: ("NOT_STARTED", 0),
            52: ("SIGNALLED", -9),
            53: ("EXITED", -1),
            55: ("NOT_STARTED", None),
        }[n]
        v = complete_vector(body_changes={"exit": {"cli_observation": proc(term, code)}})
        if n != 52:
            status, reason = (
                "REJECTED",
                "CAPTURE_STATE_CONFLICT" if n == 55 else "PROCESS_STATE_CONFLICT",
            )
    elif n == 54:
        v = complete_vector(
            body_changes={"exit": {"capture_outcome": "PARTIAL_REPORTED", "failure_stage": "NONE"}}
        )
        status, reason = "REJECTED", "CAPTURE_STATE_CONFLICT"
    elif n == 56:
        v = complete_vector(
            raw_changes={"cli_stderr": None},
            body_changes={
                "exit": {"capture_outcome": "PARTIAL_REPORTED", "failure_stage": "COLLECT"}
            },
        )
        status, reason = "INCOMPLETE", "MISSING_RAW"
    return v, status, reason


@pytest.mark.parametrize("case_id", [f"AR-{n:02}" for n in range(1, 57)])
def test_acceptance(case_id):
    n = int(case_id[3:])
    if n == 15:
        assert_old_exact_reference_rejected()
    v, status, reason = scenario(n)
    result = assess_actual_binding(v.bundle, expected_pre=v.pre, expected_post=v.post)
    assert result.structural_status == status
    if reason:
        assert reason in result.reasons
    blocked(result)
    if n in (37, 38, 39, 40, 46):
        with pytest.raises(TypeError):
            assess_actual_binding(
                v.bundle,
                expected_pre=v.pre,
                expected_post=v.post,
                retention_receipt={"claimed": "READBACK_MATCH"},
            )
    if n == 42:
        assert "assets" in result.not_evaluated_checks
    if n == 50:
        assert "ENVIRONMENT_MISMATCH" in result.reasons
    if n == 55:
        other = complete_vector(body_changes={"exit": {"cli_observation": proc("UNKNOWN", None)}})
        r = assess_actual_binding(other.bundle, expected_pre=other.pre, expected_post=other.post)
        assert r.structural_status == "INCOMPLETE" and "CAPTURE_STATE_CONFLICT" not in r.reasons


def test_all56cases_have_owned_evidence():
    path = (
        Path(__file__).resolve().parents[2] / "fixtures/actual_binding/acceptance-coverage-map.json"
    )
    assert path.is_file(), "actual case evidence mapping missing"
    rows = json.loads(path.read_bytes())["cases"]
    assert [r["id"] for r in rows] == [f"AR-{n:02}" for n in range(1, 57)]
    assert all(r["real_world_qualified"] is False for r in rows)
