"""Pure linkage of reported context and original bytes, without provenance or repair."""

from dataclasses import dataclass
from hashlib import sha256
from typing import cast

from ._codec import _DecodedDocuments
from ._identity import pre_reference_identity
from ._schema import JsonObject
from .constants import (
    ASSET_KEYS,
    CHECK_GROUP_ORDER,
    DOCUMENT_ROLES,
    ENV_KEYS,
    RAW_ROLES,
    REASON_ORDER,
    SHARED_IDENTITIES,
)
from .values import (
    ActualDiagnosticBundle,
    CaptureFreezeExpectedReference,
    PrelaunchExpectedReference,
    require,
)


@dataclass(frozen=True, slots=True)
class _CheckResult:
    reasons: tuple[str, ...]
    not_evaluated_checks: tuple[str, ...]


def facts(issues: list[str], skipped: list[str]) -> _CheckResult:
    return _CheckResult(
        tuple(r for r in REASON_ORDER if r in issues),
        tuple(g for g in CHECK_GROUP_ORDER if g in skipped),
    )


def part(decoded: _DecodedDocuments, role: str, key: str = "body") -> JsonObject | None:
    d = decoded.documents.get(role)
    return None if d is None else cast(JsonObject, d[key])


def _targets(role: str) -> tuple[str, ...]:
    return (
        ("baseline", "command")
        if role == "preflight"
        else ("baseline", "command", "preflight")
        if role == "intent"
        else ("intent",)
        if role == "exit"
        else DOCUMENT_ROLES[:-1]
    )


def _conflicting_hash_claims(
    decoded: _DecodedDocuments,
    pre: PrelaunchExpectedReference | None,
    post: CaptureFreezeExpectedReference | None,
    complete_pre_identity: str | None,
) -> bool:
    """Compare known claims only within their exact semantic target domain."""
    claims: dict[str, set[str]] = {}

    def claim(target: str, value: object) -> None:
        if value is not None:
            claims.setdefault(target, set()).add(cast(str, value))

    for role, value in decoded.document_sha256.items():
        claim("document:" + role, value)
    if pre is not None:
        for role in ("baseline", "command", "preflight"):
            claim("document:" + role, getattr(pre, role + "_sha256"))
    if post is not None:
        for role in ("intent", "exit", "snapshot"):
            claim("document:" + role, getattr(post, role + "_sha256"))
        claim("pre-reference-identity", post.pre_reference_content_sha256)
    claim("pre-reference-identity", complete_pre_identity)
    for role in ("preflight", "intent", "exit", "snapshot"):
        body = part(decoded, role)
        if body is None:
            continue
        for target in _targets(role):
            claim("document:" + target, body[target + "_sha256"])
        if role == "intent":
            claim("pre-reference-identity", body["pre_reference_content_sha256"])
    return any(len(values) > 1 for values in claims.values())


def check_links(
    decoded: _DecodedDocuments,
    bundle: ActualDiagnosticBundle,
    pre: PrelaunchExpectedReference | None,
    post: CaptureFreezeExpectedReference | None,
) -> _CheckResult:
    require(pre is None or type(pre) is PrelaunchExpectedReference)
    require(post is None or type(post) is CaptureFreezeExpectedReference)
    issues: list[str] = []
    skipped: list[str] = []
    groups = (
        "headers",
        "assets",
        "pre_reference",
        "document_links",
        "raw_binding",
        "reported_ids",
        "command_context",
        "post_reference",
    )
    if (
        pre is not None
        and post is not None
        and (
            pre.workflow_run_id != post.workflow_run_id
            or pre.workflow_attempt_id != post.workflow_attempt_id
            or pre.case != post.case
        )
    ):
        issues.append("CONTEXT_MISMATCH")
    if not decoded.container_valid:
        return facts(issues, list(groups))

    def compare(wanted: object, actual: object, group: str) -> None:
        if wanted is None or actual is None:
            skipped.append(group)
        elif wanted != actual:
            issues.append("HASH_MISMATCH")

    headers = [h for role in DOCUMENT_ROLES if (h := part(decoded, role, "header")) is not None]
    if len(headers) != len(DOCUMENT_ROLES):
        skipped.append("headers")
    for h in headers:
        for ref in (pre, post):
            if ref is not None and any(
                h[k] != value
                for k, value in (
                    ("workflow_run_id", ref.workflow_run_id),
                    ("workflow_attempt_id", ref.workflow_attempt_id),
                    ("case", ref.case),
                )
            ):
                issues.append("CONTEXT_MISMATCH")
        if any(h[k] != headers[0][k] for k in SHARED_IDENTITIES):
            issues.append("CONTEXT_MISMATCH")

    pre_id = None
    if pre is None:
        issues.append("MISSING_PRE_REFERENCE")
        skipped.append("pre_reference")
    else:
        if any(
            x is None
            for x in (
                pre.host_clock_cohort_sha256,
                pre.host_clock_generation,
                pre.baseline_sha256,
                pre.command_sha256,
                pre.preflight_sha256,
            )
        ):
            issues.append("MISSING_PRE_REFERENCE")
            skipped.append("pre_reference")
        else:
            pre_id = pre_reference_identity(pre)
        for role in ("baseline", "command", "preflight"):
            compare(
                getattr(pre, role + "_sha256"), decoded.document_sha256.get(role), "pre_reference"
            )

    if _conflicting_hash_claims(decoded, pre, post, pre_id):
        issues.append("HASH_MISMATCH")
    for role in ("preflight", "intent", "exit", "snapshot"):
        body = part(decoded, role)
        if body is None:
            skipped.append("document_links")
            continue
        for target in _targets(role):
            value = body[target + "_sha256"]
            if value is None:
                issues.append("MISSING_CONTEXT")
            compare(value, decoded.document_sha256.get(target), "document_links")
        if role == "intent":
            value = body["pre_reference_content_sha256"]
            if value is None:
                issues.append("MISSING_CONTEXT")
            compare(value, pre_id, "pre_reference")

    raw = dict(bundle.raw)
    raw_hashes = {
        r: sha256(v).hexdigest()
        for r, v in bundle.raw
        if v is not None and "raw:" + r not in decoded.limited
    }
    baseline, preflight = part(decoded, "baseline"), part(decoded, "preflight")
    expected = None if baseline is None else cast(JsonObject, baseline["expected_assets"])
    observed = None if preflight is None else cast(JsonObject, preflight["observed_assets"])
    checks = None if preflight is None else cast(JsonObject, preflight["asset_checks"])
    if baseline is None or preflight is None:
        skipped.append("assets")
    for name in ASSET_KEYS:
        if (
            expected is not None
            and expected[name] is None
            or observed is not None
            and observed[name] is None
            or checks is not None
            and checks[name] == "UNAVAILABLE"
        ):
            issues.append("MISSING_CONTEXT")
            skipped.append("assets")
        if checks is not None and checks[name] == "MISMATCH_REPORTED":
            issues.append("CONTEXT_MISMATCH")
        if (
            expected is not None
            and observed is not None
            and expected[name] is not None
            and observed[name] is not None
            and expected[name] != observed[name]
        ):
            issues.append("CONTEXT_MISMATCH")
    if "initrd" not in raw_hashes:
        skipped.append("assets")
    else:
        for context in (expected, observed):
            if (
                context is not None
                and context["image"] is not None
                and context["image"] != raw_hashes["initrd"]
            ):
                issues.append("CONTEXT_MISMATCH")

    snapshot = part(decoded, "snapshot")
    if snapshot is None:
        skipped.append("raw_binding")
    else:
        descriptors = cast(JsonObject, snapshot["raw_descriptors"])
        for role in RAW_ROLES:
            d = cast(JsonObject, descriptors[role])
            raw_value = raw[role]
            if "raw:" + role in decoded.limited:
                skipped.append("raw_binding")
                continue
            if raw_value is None:
                skipped.append("raw_binding")
                issues.append(
                    "MISSING_RAW"
                    if d["availability"] == "UNAVAILABLE"
                    else "RAW_DESCRIPTOR_MISMATCH"
                )
            elif (
                d["availability"] != "PRESENT"
                or d["byte_length"] != len(raw_value)
                or d["sha256"] != raw_hashes[role]
            ):
                issues.append("RAW_DESCRIPTOR_MISMATCH")

    exit_body = part(decoded, "exit")
    if exit_body is None or snapshot is None:
        skipped.append("reported_ids")
    else:
        left, right = (
            cast(JsonObject, exit_body["reported_source_ids"]),
            cast(JsonObject, snapshot["reported_source_ids"]),
        )
        for name in ("producer_attempt_id", "guest_capture_id"):
            if left[name] is None or right[name] is None:
                issues.append("MISSING_CONTEXT")
                skipped.append("reported_ids")
            elif left[name] != right[name]:
                issues.append("REPORTED_ID_MISMATCH")

    command = part(decoded, "command")
    if command is None or exit_body is None:
        skipped.append("command_context")
    else:
        pairs = (
            ("host_cli_argv", "host_cli_argv_observed", "COMMAND_MISMATCH"),
            ("interpreter_sha256", "host_interpreter_sha256_observed", "INTERPRETER_MISMATCH"),
        )
        for intended, actual, reason in pairs:
            if command[intended] is None or exit_body[actual] is None:
                issues.append("MISSING_CONTEXT")
                skipped.append("command_context")
            elif command[intended] != exit_body[actual]:
                issues.append(reason)
        expected_env, observed_env = (
            cast(JsonObject, command["environment"]),
            cast(JsonObject, exit_body["host_environment_observed"]),
        )
        for key in ENV_KEYS:
            if expected_env[key] is None or observed_env[key] is None:
                issues.append("MISSING_CONTEXT")
                skipped.append("command_context")
            elif expected_env[key] != observed_env[key]:
                issues.append("ENVIRONMENT_MISMATCH")
        if exit_body["host_context_observation_kind"] != "LAUNCH_BOUNDARY_REPORTED":
            issues.append("MISSING_CONTEXT")
            skipped.append("command_context")

    if post is None:
        issues.append("MISSING_POST_REFERENCE")
        skipped.append("post_reference")
    else:
        if any(
            v is None
            for v in (
                post.pre_reference_content_sha256,
                post.intent_sha256,
                post.exit_sha256,
                post.snapshot_sha256,
            )
        ):
            issues.append("MISSING_POST_REFERENCE")
            skipped.append("post_reference")
        compare(post.pre_reference_content_sha256, pre_id, "post_reference")
        for role in ("intent", "exit", "snapshot"):
            compare(
                getattr(post, role + "_sha256"), decoded.document_sha256.get(role), "post_reference"
            )
    return facts(issues, skipped)
