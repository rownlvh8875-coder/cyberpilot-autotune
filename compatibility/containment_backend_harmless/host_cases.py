"""Independent checks on named raw guest measurements, never containment admission."""

import json
import math
from typing import Any

FIXTURES = tuple(f"HF{i:02d}" for i in range(1, 25))


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite measurement")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def check_case(record: dict[str, Any]) -> tuple[str, ...]:
    fixture = record.get("fixture_id")
    if fixture not in FIXTURES:
        raise ValueError("unknown fixture")
    data = record.get("measurements")
    if type(data) is not dict:
        raise ValueError("missing measurements")
    failures = []

    def exact(name: str, expected: object) -> bool:
        value = data.get(name)
        return type(value) is type(expected) and value == expected

    def positive(name: str) -> bool:
        return type(data.get(name)) is int and data[name] > 0

    def require(condition: bool, reason: str) -> None:
        if not condition:
            failures.append(reason)

    match fixture:
        case "HF01":
            require(
                (type(data.get("fd_received")) is int and data["fd_received"] >= 0)
                and exact("read_matches", True)
                and exact("object_matches", True),
                "READ_OR_OBJECT_MISMATCH",
            )
            require(
                exact("read_only", True)
                and exact("broker_lookup_calls", 1)
                and exact("continue_calls", 0),
                "READ_ONLY_BROKER_MISMATCH",
            )
        case "HF02":
            require(
                exact("buffer_changed", True)
                and exact("copied_path_used", True)
                and exact("read_matches", True)
                and exact("continue_calls", 0),
                "MUTABLE_ARGUMENT_NOT_BOUND",
            )
        case "HF03":
            require(
                exact("resolution_safe", True) and exact("source_drift_detected", True),
                "SYMLINK_RACE_NOT_REJECTED_OR_CONFINED",
            )
        case "HF04":
            require(
                exact("resolution_safe", True) and exact("outside_read", False),
                "SCOPED_RESOLUTION_MISMATCH",
            )
        case "HF05":
            require(
                exact("magiclink_rejected", True) and exact("fd_received", -1),
                "MAGICLINK_NOT_REJECTED",
            )
        case "HF06":
            require(
                exact("unknown_dirfd_rejected", True) and exact("broker_lookup_calls", 0),
                "UNBOUND_DIRFD_USED",
            )
        case "HF07":
            require(
                exact("mutation_rejected", True) and exact("input_unchanged", True),
                "PROTECTED_INPUT_MUTATED",
            )
        case "HF08":
            require(exact("open_errno", 1) and exact("broker_lookup_calls", 0), "OPATH_NOT_BLOCKED")
        case "HF09":
            require(
                exact("invalid_flags_errno", 22) and exact("x32_errno", 1),
                "UNSUPPORTED_FLAGS_OR_ABI_REACHED_KERNEL",
            )
        case "HF10":
            require(
                exact("invalid_scope_errno", 22) and exact("fallback_calls", 0),
                "INVALID_SCOPING_OR_FALLBACK",
            )
        case "HF11":
            require(
                exact("stale_id_errno", 2)
                and exact("no_injection_after_cancel", True)
                and exact("child_reaped", True),
                "CANCELED_REQUEST_NOT_BOUND",
            )
        case "HF12":
            require(
                exact("fork_denial_errno", 1)
                and exact("exec_denial_errno", 1)
                and exact("children_reaped", 2),
                "DESCENDANT_GUARD_OR_REAP_MISMATCH",
            )
        case "HF13":
            require(positive("kernel_events"), "MISSING_KERNEL_EVENT")
            require(
                all(
                    exact(name, True)
                    for name in ("duplicate_detected", "drop_detected", "reorder_detected")
                ),
                "TRACE_FAULT_NOT_DETECTED",
            )
        case "HF14":
            require(
                exact("observer_exit_signal", 9) and exact("denial_after_loss_errno", 1),
                "OBSERVER_LOSS_WIDENED_GUARD",
            )
            require(exact("tree_exit_observed", True), "TREE_EXIT_NOT_OBSERVED")
        case "HF15":
            require(
                exact("listener_errno", 38) and exact("alive_after_errno", True),
                "ENOSYS_MISTAKEN_FOR_TERMINATION",
            )
            require(exact("tree_exit_observed", True), "TREE_EXIT_NOT_OBSERVED")
        case "HF16":
            require(
                exact("detach_attempt_errno", 1) and exact("denial_after_attempt_errno", 1),
                "POLICY_TAMPER_NOT_BLOCKED",
            )
        case "HF17":
            require(
                exact("threaded_type", True)
                and exact("kill_errno", 95)
                and exact("payload_started", False),
                "THREADED_CGROUP_NOT_REJECTED",
            )
        case "HF18":
            require(
                exact("extra_fd_detected", True) and exact("payload_started", False),
                "UNINVENTORIED_FD_ADMITTED",
            )
        case "HF19":
            require(
                exact("input_changed", True) and exact("cohort_drift_rejected", True),
                "INPUT_DRIFT_NOT_REJECTED",
            )
        case "HF20":
            require(
                exact("exec_errno", 1) and exact("generated_code_started", False),
                "GENERATED_CODE_PROMOTED",
            )
        case "HF21":
            require(
                exact("proposal_changed", True)
                and exact("proposal_rejected", True)
                and exact("policy_adopted", False),
                "CALLER_POLICY_BECAME_AUTHORITY",
            )
        case "HF22":
            require(
                exact("end_marker_missing", True)
                and exact("trace_complete", None)
                and exact("counts_claimed_zero", False),
                "MISSING_EVIDENCE_BECAME_ZERO",
            )
        case "HF23":
            require(
                exact("standin_regular", True)
                and exact("policy_refusal_errno", 1)
                and exact("device_class_qualified", False),
                "STANDIN_BECAME_DEVICE_PROOF",
            )
        case "HF24":
            require(
                exact("write_open_errno", 1)
                and exact("new_file_created", False)
                and exact("original_unchanged", True),
                "EFFECTFUL_OPEN_NOT_BLOCKED",
            )
    return tuple(failures)


def parse_guest_log(raw: str, selected: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(x not in FIXTURES for x in selected)
    ):
        raise ValueError("invalid fixture selection")
    found = {}
    exits = {}
    done = 0
    for line in raw.replace("\r", "").splitlines():
        if line == "GUEST_HARNESS_DONE":
            done += 1
        elif line.startswith("RAW_FIXTURE "):
            record = json.loads(line.removeprefix("RAW_FIXTURE "), object_pairs_hook=_unique)
            _finite(record)
            if type(record) is not dict or record.get("fixture_id") not in selected:
                raise ValueError("unknown raw record")
            key = record["fixture_id"]
            if key in found:
                raise ValueError("duplicate raw fixture")
            found[key] = record
        elif line.startswith("HARNESS_EXIT "):
            parts = line.split()
            if (
                len(parts) != 3
                or parts[1] not in selected
                or parts[1] in exits
                or parts[2] != "0"
                or parts[1] not in found
                or done
            ):
                raise ValueError("failed, unknown, early or duplicate fixture exit")
            exits[parts[1]] = 0
        elif "Kernel panic" in line:
            raise ValueError("guest panicked")
    if done != 1 or set(found) != set(selected) or set(exits) != set(selected):
        raise ValueError("incomplete actual guest records")
    return tuple(found[key] for key in selected)
