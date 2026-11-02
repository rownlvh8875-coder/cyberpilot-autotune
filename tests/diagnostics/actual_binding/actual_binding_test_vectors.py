"""TEST_ONLY prospective vectors; no producer, reference source or real evidence."""

import copy
import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256

from cyberpilot_autotune.diagnostics.actual_binding.values import (
    ActualDiagnosticBundle,
    CaptureFreezeExpectedReference,
    PrelaunchExpectedReference,
)

LABEL = "TEST_ONLY_NOT_REAL_EVIDENCE"
DOCS = ("baseline", "command", "preflight", "intent", "exit", "snapshot")
RAW = ("telemetry", "console", "cli_stdout", "cli_stderr", "record_json", "initrd", "exit_receipt")
PERMS = tuple(
    (k, False)
    for k in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(value):
    return sha256(value).hexdigest()


def reference_digest(ref):
    return digest(canonical({"domain": ref.contract_version, "value": asdict(ref)}))


def clock(**changes):
    return (
        dict(
            domain="HOST_MONOTONIC_NS",
            cohort_sha256="3" * 64,
            context_material_sha256="4" * 64,
            generation=0,
            context_status="REPORTED",
        )
        | changes
    )


def unavailable_clock():
    return clock(
        cohort_sha256=None,
        context_material_sha256=None,
        generation=None,
        context_status="UNAVAILABLE",
    )


@dataclass(frozen=True)
class Vector:
    bundle: ActualDiagnosticBundle
    pre: PrelaunchExpectedReference | None
    post: CaptureFreezeExpectedReference | None
    label: str = LABEL


def complete_vector(*, body_changes=None, header_changes=None, raw_changes=None):
    """Build a new TEST_ONLY model, not a runtime reference acquisition facility."""
    body_changes = body_changes or {}
    header_changes = header_changes or {}
    raw = {name: ("TEST_ONLY_OPAQUE_" + name).encode() for name in RAW}
    raw["cli_stderr"] = b""
    raw.update(raw_changes or {})
    documents = {}

    def doc(role, body):
        header = dict(
            contract_version="actual-diagnostic-receipt-v1",
            role=role,
            mode="ACTUAL_DIAGNOSTIC_REPORTED_UNTRUSTED",
            origin="PROSPECTIVE_CAPTURE_REPORTED_UNTRUSTED",
            synthetic=False,
            workflow_run_id="1" * 32,
            workflow_attempt_id="2" * 32,
            case="DFD02",
            producer_implementation_revision="a" * 40,
            producer_source_revision="b" * 40,
            capture_implementation_sha256="c" * 64,
            host_clock_context=clock(),
            status="BLOCKED",
            permissions=dict(PERMS),
        )
        header.update(copy.deepcopy(header_changes.get(role, {})))
        body.update(copy.deepcopy(body_changes.get(role, {})))
        documents[role] = canonical({"header": header, "body": body})
        return header

    assets = {
        k: digest(("TEST_ONLY_ASSET_" + k).encode())
        for k in ("probe", "vm", "kernel", "kernel_config", "transport_profile", "init", "image")
    }
    if raw["initrd"] is not None:
        assets["image"] = digest(raw["initrd"])
    h = doc(
        "baseline",
        dict(
            expected_assets=assets,
            declared_case_profile=dict(
                expected_fds=[0],
                installed_fds=[0],
                cause_fds=[],
                decision_kind="RESULT",
                decision_value="NO_DENIAL",
            ),
            producer_record_schema="deny-fd-v2-dual-acquisition-v1",
            policy_reference_sha256=None,
        ),
    )
    env = dict(LANG="C", LC_ALL="C", PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1")
    argv = ["/TEST_ONLY/python", "-m", "TEST_ONLY_never_executed"]
    doc(
        "command",
        dict(
            host_cli_argv=argv,
            host_cli_cwd="/TEST_ONLY",
            interpreter_sha256="d" * 64,
            environment_scope="DECLARED_NONSECRET_ALLOWLIST_NOT_FULL_ENV",
            environment=env,
            planned_destination="/TEST_ONLY/result",
            expected_qemu_argv=None,
        ),
    )
    p_header = doc(
        "preflight",
        dict(
            baseline_sha256=digest(documents["baseline"]),
            command_sha256=digest(documents["command"]),
            observed_assets=assets,
            observation_kind="REPORTED_NOT_ATTESTED",
            asset_checks=dict.fromkeys(assets, "MATCHED_REPORTED"),
            mono_ns=0,
            event_ordinal=0,
        ),
    )
    pre = PrelaunchExpectedReference(
        "actual-diagnostic-prelaunch-reference-v1",
        h["workflow_run_id"],
        h["workflow_attempt_id"],
        h["case"],
        p_header["host_clock_context"]["cohort_sha256"],
        p_header["host_clock_context"]["generation"],
        *(digest(documents[r]) for r in ("baseline", "command", "preflight")),
    )
    doc(
        "intent",
        dict(
            baseline_sha256=digest(documents["baseline"]),
            command_sha256=digest(documents["command"]),
            preflight_sha256=digest(documents["preflight"]),
            pre_reference_content_sha256=reference_digest(pre),
            mono_ns=1,
            event_ordinal=1,
        ),
    )
    ids = dict(producer_attempt_id="7" * 32, guest_capture_id="8" * 32)
    proc = dict(
        observation_kind="TOOL_REPORTED",
        process_identity_sha256=None,
        pid=None,
        returncode=2,
        termination="EXITED",
    )
    doc(
        "exit",
        dict(
            intent_sha256=digest(documents["intent"]),
            reported_source_ids=ids,
            host_cli_argv_observed=argv,
            cli_observation=proc,
            qemu_observation=proc
            | {"returncode": 0, "observation_kind": "PRODUCER_RECORD_REPORTED"},
            launch_before_ns=2,
            launch_after_ns=3,
            exit_observed_ns=4,
            mono_ns=5,
            event_ordinal=2,
            raw_close_states=dict.fromkeys(RAW, "FINALIZED_REPORTED"),
            capture_outcome="COMPLETE_REPORTED",
            failure_stage="NONE",
            host_interpreter_sha256_observed="d" * 64,
            host_environment_observed=env,
            host_context_observation_kind="LAUNCH_BOUNDARY_REPORTED",
        ),
    )
    desc = {
        r: dict(availability="UNAVAILABLE", byte_length=None, sha256=None)
        if value is None
        else dict(availability="PRESENT", byte_length=len(value), sha256=digest(value))
        for r, value in raw.items()
    }
    doc(
        "snapshot",
        dict(
            **{r + "_sha256": digest(documents[r]) for r in DOCS[:-1]},
            raw_descriptors=desc,
            reported_source_ids=ids,
            original_case_directory="/TEST_ONLY/original",
            mono_ns=6,
            event_ordinal=3,
        ),
    )
    post = CaptureFreezeExpectedReference(
        "actual-diagnostic-capture-reference-v1",
        h["workflow_run_id"],
        h["workflow_attempt_id"],
        h["case"],
        reference_digest(pre),
        *(digest(documents[r]) for r in ("intent", "exit", "snapshot")),
    )
    return Vector(ActualDiagnosticBundle(tuple(documents.items()), tuple(raw.items())), pre, post)


def document(vector, role):
    return json.loads(dict(vector.bundle.documents)[role])


def replace_document(vector, role, raw):
    docs = dict(vector.bundle.documents)
    docs[role] = raw
    return replace(vector, bundle=replace(vector.bundle, documents=tuple(docs.items())))


def mutate_document(vector, role, mutate):
    value = document(vector, role)
    mutate(value)
    return replace_document(vector, role, canonical(value))
