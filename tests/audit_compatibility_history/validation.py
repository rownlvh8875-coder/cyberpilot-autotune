"""Pure consistency of supplied claims. Never observes or authorizes execution."""

import json
from hashlib import sha256

from .contracts import (
    PROFILE,
    HistoricalCommandPolicy,
    HistoricalCommandRecord,
    HistoricalReplayDecision,
    HistoricalReplayPolicy,
    HistoricalReplayRecord,
    OriginPin,
    SourcePin,
    children,
)

COHORTS = (
    (
        "O",
        SourcePin(
            "5357d5d555d49b258affa237d83b8491b8a8c6ce", "18e63fc8e03077684cd14c1ed33e2c7a8ceb89a5"
        ),
    ),
    (
        "D",
        SourcePin(
            "75e00280a09323ad4a3fc82453383f220c92f6c6", "d0dd929f3bb46d1a33d8bb00f29e7638b48d9483"
        ),
    ),
)
COMMANDS = (
    ("O-PYTEST", "O", "PYTEST", "pytest.main"),
    ("O-H6", "O", "AUDIT", "tests.audit.validate_friction_model"),
    ("O-H7", "O", "AUDIT", "tests.audit.validate_friction_receipt"),
    ("D-PYTEST", "D", "PYTEST", "pytest.main"),
    ("D-H6", "D", "AUDIT", "tests.audit.validate_friction_model"),
    ("D-COVERAGE", "D", "AUDIT", "tests.audit.validate_actual_binding_coverage"),
)
H6_HASHES = (
    ("O", "aa27d15517e693b0288ed37893deae4515a7c1f88388bb29e871c9fe0e68d032"),
    ("D", "eaddb6091b5054613ec8e7f0eb15cae9b64aa3d1d8f4e1205c688b89f1947efe"),
)


def _duplicates(values: tuple[str, ...]) -> bool:
    return len(values) != len(set(values))


def _registered_D_nodes(nodes: tuple[str, ...]) -> bool:
    diagnostic = sorted(n for n in nodes if n.startswith("tests/diagnostics/actual_binding/"))
    raw = json.dumps(diagnostic, ensure_ascii=True, separators=(",", ":")).encode()
    return (
        sha256(raw).hexdigest()
        == "403787af65a67f069df2d13d3e91d1cd95d99642ba3a3d3e658bc286485a5ab4"
    )


def _known_origins(
    command_id: str, cohort_id: str, origins: tuple[OriginPin, ...], errors: set[str]
) -> None:
    if command_id in ("O-H6", "D-H6") and not any(
        o.module == "tests.audit.validate_friction_model" for o in origins
    ):
        errors.add("MISSING_H6_ORIGIN")
    for origin in origins:
        if origin.module == "tests.audit.validate_friction_model" and (
            origin.path != "tests/audit/validate_friction_model.py"
            or origin.archive_member is not None
            or origin.sha256 != dict(H6_HASHES).get(cohort_id)
        ):
            errors.add("H6_COHORT_ORIGIN")


def _observed(item: HistoricalCommandRecord, errors: set[str], missing: set[str]) -> None:
    errors.update(item.errors)
    missing.update(item.unavailable)
    if item.subject is None:
        missing.add("SOURCE_MISSING")
    elif item.cohort_id not in dict(COHORTS) or item.subject != dict(COHORTS)[item.cohort_id]:
        errors.add("SOURCE_MISMATCH")
    if item.exit_code is None:
        missing.add("EXIT_UNAVAILABLE")
    elif item.exit_code != 0:
        errors.add("COMMAND_FAILED")
    for value in (
        item.entrypoint,
        item.argv,
        item.collected_nodeids,
        item.outcomes,
        item.origins,
        item.coverage,
        item.coverage_artifact_sha256,
        item.coverage_producer_command_id,
    ):
        if value is None:
            missing.add("COMMAND_OBSERVATION_MISSING")
    if item.collected_nodeids is not None and _duplicates(item.collected_nodeids):
        errors.add("DUPLICATE_NODE")
    if item.command_id == "D-PYTEST":
        if item.collected_nodeids is not None and not _registered_D_nodes(item.collected_nodeids):
            errors.add("REGISTERED_D_COLLECTION")
        if (
            item.exit_code == 0
            and item.outcomes is not None
            and not _registered_D_nodes(tuple(o.nodeid for o in item.outcomes))
        ):
            errors.add("REGISTERED_D_OUTCOMES")
    if item.outcomes is not None:
        if _duplicates(tuple(o.nodeid for o in item.outcomes)):
            errors.add("DUPLICATE_OUTCOME")
        for outcome in item.outcomes:
            for phase in (outcome.setup, outcome.call, outcome.teardown):
                if phase == "UNAVAILABLE":
                    missing.add("CASE_PHASE_UNAVAILABLE")
                elif phase != "PASSED":
                    errors.add("CASE_NOT_PASSED")
    if item.origins is not None:
        if not item.origins or _duplicates(tuple(o.module for o in item.origins)):
            errors.add("ORIGIN_INVENTORY")
        _known_origins(item.command_id, item.cohort_id, item.origins, errors)
    if item.coverage is not None and _duplicates(tuple(c.path.casefold() for c in item.coverage)):
        errors.add("DUPLICATE_COVERAGE_MODULE")
    if item.coverage is not None:
        statements = sum(c.statements for c in item.coverage)
        covered = sum(c.covered for c in item.coverage)
        branches = sum(c.branches for c in item.coverage)
        covered_branches = sum(c.covered_branches for c in item.coverage)
        # Passing groups imply a passing weighted union;the converse is false.
        # Never impose a per-module floor or call this an independent group pass.
        if (
            statements == 0
            or branches == 0
            or covered * 100 < statements * 98
            or covered_branches * 100 < branches * 95
        ):
            errors.add("IMPOSSIBLE_COVERAGE")


def _policy_command(item: HistoricalCommandPolicy, errors: set[str], missing: set[str]) -> None:
    if item.expected_nodeids is None:
        missing.add("EXPECTED_CASE_INVENTORY")
    elif _duplicates(item.expected_nodeids) or (
        bool(item.expected_nodeids) != (item.kind == "PYTEST")
    ):
        errors.add("POLICY_NODE_INVENTORY")
    if item.command_id == "D-PYTEST" and item.expected_nodeids is not None:
        # Content pin from the design's D499 inventory,not an authority token.
        if not _registered_D_nodes(item.expected_nodeids):
            errors.add("REGISTERED_D_CASE_INVENTORY")
    if item.origins is None:
        missing.add("EXPECTED_ORIGIN_INVENTORY")
    elif not item.origins or _duplicates(tuple(o.module for o in item.origins)):
        errors.add("POLICY_ORIGIN_INVENTORY")
    if item.origins is not None:
        _known_origins(item.command_id, item.cohort_id, item.origins, errors)
    if item.coverage_groups is None:
        missing.add("EXPECTED_COVERAGE_INVENTORY")
    else:
        wanted = {
            "friction_model",
            "observability" if item.cohort_id == "O" else "diagnostics.actual_binding",
        }
        names = tuple(g[0] for g in item.coverage_groups)
        paths = tuple(p.casefold() for _, group in item.coverage_groups for p in group)
        if set(names) != wanted or _duplicates(names) or _duplicates(paths):
            errors.add("POLICY_COVERAGE_GROUPS")
        for name, group in item.coverage_groups:
            prefix = (
                "src/cyberpilot_autotune/"
                + (
                    "research/friction_model"
                    if name == "friction_model"
                    else name.replace(".", "/")
                )
                + "/"
            )
            if not group or any(not p.startswith(prefix) for p in group):
                errors.add("POLICY_COVERAGE_PATHS")


def _compare(
    item: HistoricalCommandRecord,
    policy: HistoricalCommandPolicy,
    errors: set[str],
    missing: set[str],
) -> None:
    if item.entrypoint is not None and item.entrypoint != policy.entrypoint:
        errors.add("ENTRYPOINT_MISMATCH")
    if item.argv is not None and item.argv != policy.argv:
        errors.add("ARGV_MISMATCH")
    if (
        item.origins is not None
        and policy.origins is not None
        and set(item.origins) != set(policy.origins)
    ):
        errors.add("ORIGIN_MISMATCH")
    if policy.expected_nodeids is not None:
        expected = set(policy.expected_nodeids)
        if item.collected_nodeids is not None and set(item.collected_nodeids) != expected:
            errors.add("NODE_INVENTORY_MISMATCH")
        if item.outcomes is not None:
            observed = {o.nodeid for o in item.outcomes}
            if observed - expected or (item.exit_code == 0 and observed != expected):
                errors.add("OUTCOME_INVENTORY_MISMATCH")
            elif observed != expected:
                missing.add("CASE_OUTCOMES_INCOMPLETE")
    if item.coverage is not None and policy.coverage_groups is not None:
        counts = {c.path: c for c in item.coverage}
        expected_paths = {p for _, group in policy.coverage_groups for p in group}
        if set(counts) != expected_paths:
            errors.add("COVERAGE_MODULE_INVENTORY")
        for _, group in policy.coverage_groups:
            if not set(group) <= counts.keys():
                continue
            statements = sum(counts[p].statements for p in group)
            covered = sum(counts[p].covered for p in group)
            branches = sum(counts[p].branches for p in group)
            covered_branches = sum(counts[p].covered_branches for p in group)
            if (
                statements == 0
                or branches == 0
                or covered * 100 < statements * 98
                or covered_branches * 100 < branches * 95
            ):
                errors.add("COVERAGE_FLOOR")


def assess_record(
    record: HistoricalReplayRecord, policy: HistoricalReplayPolicy | None
) -> HistoricalReplayDecision:
    children((record,), HistoricalReplayRecord)
    errors, missing = set(record.errors), set(record.unavailable)
    registry = {identity: (cohort, kind, entry) for identity, cohort, kind, entry in COMMANDS}
    if record.profile_id != PROFILE:
        errors.add("WRONG_PROFILE")
    if _duplicates(tuple(c.command_id for c in record.commands)):
        errors.add("DUPLICATE_COMMAND")
    actual = {c.command_id: c for c in record.commands}
    if set(actual) - registry.keys():
        errors.add("UNKNOWN_COMMAND")
    if registry.keys() - actual.keys():
        missing.add("REQUIRED_COMMAND")
    for item in record.commands:
        _observed(item, errors, missing)
        if item.run_id != record.run_id:
            errors.add("RUN_ID_MISMATCH")
        if item.command_id in registry:
            cohort, _, entry = registry[item.command_id]
            if item.cohort_id != cohort:
                errors.add("COMMAND_COHORT")
            if item.entrypoint is not None and item.entrypoint != entry:
                errors.add("ENTRYPOINT_REGISTRY")
            if (
                item.coverage_producer_command_id is not None
                and item.coverage_producer_command_id != cohort + "-PYTEST"
            ):
                errors.add("COVERAGE_PRODUCER")
    for cohort, _ in COHORTS:
        peers = tuple(item for item in record.commands if item.cohort_id == cohort)
        if (
            len(
                {
                    item.coverage_artifact_sha256
                    for item in peers
                    if item.coverage_artifact_sha256 is not None
                }
            )
            > 1
        ):
            errors.add("COVERAGE_ARTIFACT_LINEAGE")
        available_counts = tuple(
            tuple(sorted(item.coverage, key=lambda c: c.path))
            for item in peers
            if item.coverage is not None
        )
        if len(set(available_counts)) > 1:
            errors.add("COVERAGE_COUNTS_LINEAGE")
    if policy is None:
        missing.add("POLICY_UNAVAILABLE")
    else:
        children((policy,), HistoricalReplayPolicy)
        if policy.profile_id != PROFILE:
            errors.add("POLICY_PROFILE")
        if record.policy_digest is None:
            missing.add("POLICY_BINDING")
        elif record.policy_digest != policy.content_digest:
            errors.add("POLICY_DIGEST")
        for value in (
            policy.executor_revision,
            policy.toolchain_digest,
            policy.case_inventory_digest,
            policy.control_profile_digest,
            policy.budget_profile_digest,
        ):
            if value is None:
                missing.add("POLICY_PREREQUISITES")
        if _duplicates(tuple(name for name, _ in policy.cohorts)):
            errors.add("POLICY_DUPLICATE_COHORT")
        for name, source in policy.cohorts:
            if name not in dict(COHORTS) or source != dict(COHORTS)[name]:
                errors.add("POLICY_SOURCE")
        if set(dict(COHORTS)) - dict(policy.cohorts).keys():
            missing.add("POLICY_COHORT_MISSING")
        if _duplicates(tuple(c.command_id for c in policy.commands)):
            errors.add("POLICY_DUPLICATE_COMMAND")
        if registry.keys() - {c.command_id for c in policy.commands}:
            missing.add("POLICY_COMMAND_MISSING")
        for command in policy.commands:
            _policy_command(command, errors, missing)
            if registry.get(command.command_id) != (
                command.cohort_id,
                command.kind,
                command.entrypoint,
            ):
                errors.add("POLICY_COMMAND_REGISTRY")
            compared_item = actual.get(command.command_id)
            if compared_item is not None:
                _compare(compared_item, command, errors, missing)
        for cohort, _ in COHORTS:
            groups = tuple(
                tuple(
                    sorted((name, tuple(sorted(paths))) for name, paths in command.coverage_groups)
                )
                for command in policy.commands
                if command.cohort_id == cohort and command.coverage_groups is not None
            )
            if len(set(groups)) > 1:
                errors.add("POLICY_COVERAGE_COHORT")
    return HistoricalReplayDecision(tuple(sorted(errors)), tuple(sorted(missing)))
