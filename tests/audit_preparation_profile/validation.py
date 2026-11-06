"""Compare supplied claims only. Every outcome stays blocked and non-authoritative."""

from hashlib import sha256
from typing import Any

from .contracts import (
    ARTIFACTS,
    BATCH_LIMITS,
    COHORTS,
    COMMAND_LIMITS,
    COMMANDS,
    CONTROLS,
    PROFILE,
    SPECS,
    UINT64_MAX,
    PreparationProfileDecision,
    PreparationProfilePolicy,
    PreparationProfileRecord,
    ProfileReason,
    normalized_fields,
)
from .wire import _body, canonical_policy


def assess_profile(
    record: PreparationProfileRecord,
    policy: PreparationProfilePolicy | None = None,
) -> PreparationProfileDecision:
    normalized_fields(record, PreparationProfileRecord)
    if policy is not None:
        normalized_fields(policy, PreparationProfilePolicy)
    errors: list[ProfileReason] = []
    unavailable: list[ProfileReason] = []

    def error(code: str, subject: str) -> None:
        errors.append(ProfileReason(code, subject))

    def missing(code: str, subject: str) -> None:
        unavailable.append(ProfileReason(code, subject))

    actual = _body(record)
    desired = None if policy is None else _body(policy)
    if record.producer_errors:
        error("PRODUCER_FAILURE", "record.producer")
    if record.producer_unavailable:
        missing("PRODUCER_UNAVAILABLE", "record.producer")
    if policy is None:
        missing("POLICY_UNAVAILABLE", "policy")

    def scalar(value: Any, subject: str) -> None:
        if value is None:
            missing("VALUE_UNAVAILABLE", subject)

    def table(value: Any, names: tuple[str, ...], key: str, subject: str) -> dict[str, Any]:
        if value is None:
            missing("TABLE_UNAVAILABLE", subject)
            return {}
        result = {item[key]: item for item in value}
        if set(result) != set(names):
            error("TABLE_INVENTORY_MISMATCH", subject)
        return result

    def context(value: Any, names: tuple[str, ...], subject: str) -> None:
        if value is None:
            scalar(None, subject)
        else:
            for name in names:
                scalar(value[name], subject + "." + name)

    def limits(value: Any, registry: Any, subject: str) -> dict[str, Any]:
        result = table(value, tuple(item[0] for item in registry), "name", subject)
        for name, entry in result.items():
            amount = entry["value"]
            path = subject + "." + name + ".value"
            scalar(amount, path)
            if amount == 0:
                error("LIMIT_NONPOSITIVE", path)
            elif amount == "UNBOUNDED":
                error("LIMIT_UNBOUNDED", path)
        return result

    for side, values in (("record", actual), ("policy", desired)):
        if values is None:
            continue
        if values["profile_id"] != PROFILE:
            error("PROFILE_ID_MISMATCH", side + ".profile_id")
        scalar(values["run_id"], side + ".run_id")
        artifacts = table(values["artifacts"], ARTIFACTS, "role", side + ".artifacts")
        for name, entry in artifacts.items():
            scalar(entry["sha256"], side + ".artifacts." + name + ".sha256")
        cohorts = table(
            values["cohorts"], tuple(k for k, _, _ in COHORTS), "cohort_id", side + ".cohorts"
        )
        for name, revision, tree in COHORTS:
            if name not in cohorts:
                continue
            for field, expected in (("revision", revision), ("tree", tree)):
                found = cohorts[name][field]
                path = side + ".cohorts." + name + "." + field
                scalar(found, path)
                if found is not None and found != expected:
                    error("COHORT_PIN_MISMATCH", path)
        controls = table(values["controls"], CONTROLS, "name", side + ".controls")
        for name, entry in controls.items():
            path = side + ".controls." + name + ".value"
            scalar(entry["value"], path)
            if entry["value"] is False:
                error("CONTROL_CLAIM_FALSE", path)
        batch = values["batch_boundary"]
        context(batch, ("identity_digest", "generation", "clock_domain"), side + ".batch_boundary")
        batch_limits = limits(values["batch_limits"], BATCH_LIMITS, side + ".batch_limits")
        commands = table(
            values["commands"], tuple(k for k, _ in COMMANDS), "command_id", side + ".commands"
        )
        seen = set()
        if batch is not None and batch["identity_digest"] is not None:
            seen.add(batch["identity_digest"])
        for name, cohort in COMMANDS:
            if name not in commands:
                continue
            cmd = commands[name]
            root = side + ".commands." + name
            if cmd["cohort_id"] != cohort:
                error("COMMAND_CONTEXT_MISMATCH", root + ".cohort_id")
            boundary = cmd["boundary"]
            timing = cmd["timing"]
            context(boundary, ("identity_digest", "generation", "clock_domain"), root + ".boundary")
            context(timing, ("start_ns", "deadline_ns", "clock_domain"), root + ".timing")
            cmd_limits = limits(cmd["limits"], COMMAND_LIMITS, root + ".limits")
            for limit_name, _, batch_name in COMMAND_LIMITS:
                amount = cmd_limits.get(limit_name, {}).get("value")
                cap = batch_limits.get(batch_name, {}).get("value")
                if type(amount) is int and type(cap) is int and amount > cap:
                    error("LIMIT_SCOPE_INCONSISTENT", root + ".limits." + limit_name + ".value")
            identity = None if boundary is None else boundary["identity_digest"]
            if identity is not None:
                if identity in seen:
                    error("BOUNDARY_REUSE", root + ".boundary.identity_digest")
                seen.add(identity)
            clocks = {
                item["clock_domain"]
                for item in (batch, boundary, timing)
                if item is not None and item["clock_domain"] is not None
            }
            if len(clocks) > 1:
                error("CLOCK_DOMAIN_MISMATCH", root)
            if timing is not None:
                start, deadline = timing["start_ns"], timing["deadline_ns"]
                path = root + ".timing.deadline_ns"
                if start is not None and deadline is not None and deadline < start:
                    error("TIME_ORDER_INVALID", path)
                wall = cmd_limits.get("wall_limit_ns", {}).get("value")
                if type(wall) is int and wall > 0 and start is not None:
                    if start + wall > UINT64_MAX:
                        error("TIME_OVERFLOW", path)
                    elif deadline is not None and start + wall != deadline:
                        error("DEADLINE_MISMATCH", path)

    def compare(left: Any, right: Any, spec: tuple[Any, ...], path: str) -> None:
        if left is None or right is None:
            return
        tag = spec[0]
        if tag == "nullable":
            compare(left, right, spec[1], path)
        elif tag == "dto":
            for field, child in SPECS[spec[1]]:
                compare(left[field], right[field], child, path + "." + field)
        elif tag == "table":
            old = {item[spec[2]]: item for item in right}
            for item in left:
                key = item[spec[2]]
                if key in old:
                    compare(item, old[key], ("dto", spec[1]), path + "." + key)
        elif left != right:
            error("POLICY_RECORD_MISMATCH", path)

    if desired is not None:
        for field, spec in SPECS[PreparationProfilePolicy]:
            compare(actual[field], desired[field], spec, "record." + field)
    scalar(record.policy_digest, "record.policy_digest")
    if policy is not None and record.policy_digest is not None:
        if record.policy_digest != sha256(canonical_policy(policy)).hexdigest():
            error("POLICY_DIGEST_MISMATCH", "record.policy_digest")
    return PreparationProfileDecision(tuple(errors), tuple(unavailable))
