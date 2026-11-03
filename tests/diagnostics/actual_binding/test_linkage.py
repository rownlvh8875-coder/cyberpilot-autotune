"""Linkage failures must survive partial data; no caller expectation repair."""

import importlib
import importlib.util
from dataclasses import replace

import pytest

from cyberpilot_autotune.diagnostics.actual_binding._codec import decode_documents
from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    RAW,
    Vector,
    complete_vector,
    digest,
    document,
    mutate_document,
    replace_document,
)


def links(v, *, pre="DEFAULT", post="DEFAULT"):
    assert (
        importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding._linkage")
        is not None
    ), "linkage missing"
    m = importlib.import_module("cyberpilot_autotune.diagnostics.actual_binding._linkage")
    return m.check_links(
        decode_documents(v.bundle),
        v.bundle,
        v.pre if pre == "DEFAULT" else pre,
        v.post if post == "DEFAULT" else post,
    )


def test_original_refs_reject_rewrite():
    old = complete_vector()
    changed = complete_vector(body_changes={"baseline": {"policy_reference_sha256": "f" * 64}})
    v = Vector(changed.bundle, old.pre, old.post)
    assert "HASH_MISMATCH" in links(v).reasons
    assert old.pre != changed.pre


def test_both_changed_refs_do_not_authenticate():
    v = complete_vector(body_changes={"baseline": {"policy_reference_sha256": "f" * 64}})
    facts = links(v)
    assert facts.reasons == () and not hasattr(facts, "reference")


def test_empty_and_unavailable_raw_are_not_aliases():
    assert links(complete_vector()).reasons == ()
    v = complete_vector(raw_changes={"cli_stderr": None})
    assert "MISSING_RAW" in links(v).reasons
    raw = dict(v.bundle.raw) | {"cli_stderr": b""}
    v = replace(v, bundle=replace(v.bundle, raw=tuple(raw.items())))
    assert "RAW_DESCRIPTOR_MISMATCH" in links(v).reasons


@pytest.mark.parametrize("role", RAW)
@pytest.mark.parametrize("field", ("sha256", "byte_length"))
def test_each_raw_descriptor_compares_original_bytes(role, field):
    v = complete_vector()
    wrong = "0" * 64 if field == "sha256" else 999
    v = mutate_document(
        v, "snapshot", lambda d: d["body"]["raw_descriptors"][role].__setitem__(field, wrong)
    )
    assert "RAW_DESCRIPTOR_MISMATCH" in links(v).reasons


@pytest.mark.parametrize("role", RAW)
def test_missing_present_raw_is_conflict_not_zero(role):
    v = complete_vector()
    raw = dict(v.bundle.raw) | {role: None}
    v = replace(v, bundle=replace(v.bundle, raw=tuple(raw.items())))
    assert "RAW_DESCRIPTOR_MISMATCH" in links(v).reasons


def test_reference_missing_is_not_manufactured():
    v = complete_vector()
    assert "MISSING_PRE_REFERENCE" in links(v, pre=None).reasons
    assert "MISSING_POST_REFERENCE" in links(v, post=None).reasons


@pytest.mark.parametrize(
    "field",
    (
        "host_clock_cohort_sha256",
        "host_clock_generation",
        "baseline_sha256",
        "command_sha256",
        "preflight_sha256",
    ),
)
def test_partial_pre_keeps_known_conflicts_without_derived_null_hash(field):
    v = complete_vector()
    pre = replace(v.pre, **{field: None})
    r = links(v, pre=pre)
    assert "MISSING_PRE_REFERENCE" in r.reasons and "HASH_MISMATCH" not in r.reasons
    if field != "baseline_sha256":
        pre = replace(pre, baseline_sha256="0" * 64)
        assert "HASH_MISMATCH" in links(v, pre=pre).reasons


@pytest.mark.parametrize(
    "field", ("pre_reference_content_sha256", "intent_sha256", "exit_sha256", "snapshot_sha256")
)
def test_partial_post_is_incomplete(field):
    v = complete_vector()
    assert "MISSING_POST_REFERENCE" in links(v, post=replace(v.post, **{field: None})).reasons


@pytest.mark.parametrize("field", ("baseline_sha256", "command_sha256", "preflight_sha256"))
def test_pre_expected_content_root_mismatch(field):
    v = complete_vector()
    assert "HASH_MISMATCH" in links(v, pre=replace(v.pre, **{field: "0" * 64})).reasons


@pytest.mark.parametrize(
    "field", ("pre_reference_content_sha256", "intent_sha256", "exit_sha256", "snapshot_sha256")
)
def test_post_expected_content_root_mismatch(field):
    v = complete_vector()
    assert "HASH_MISMATCH" in links(v, post=replace(v.post, **{field: "0" * 64})).reasons


@pytest.mark.parametrize(
    "role,key",
    (
        ("preflight", "baseline_sha256"),
        ("intent", "command_sha256"),
        ("exit", "intent_sha256"),
        ("snapshot", "exit_sha256"),
    ),
)
def test_document_link_null_is_unknown(role, key):
    v = complete_vector(body_changes={role: {key: None}})
    assert "MISSING_CONTEXT" in links(v).reasons


@pytest.mark.parametrize(
    "role,key",
    (
        ("preflight", "command_sha256"),
        ("intent", "baseline_sha256"),
        ("intent", "preflight_sha256"),
        ("exit", "intent_sha256"),
        ("snapshot", "exit_sha256"),
        ("intent", "pre_reference_content_sha256"),
    ),
)
def test_document_link_conflict(role, key):
    v = complete_vector(body_changes={role: {key: "0" * 64}})
    assert "HASH_MISMATCH" in links(v).reasons


def test_malformed_and_missing_targets_do_not_create_fake_hashes():
    v = replace_document(complete_vector(), "baseline", None)
    facts = links(v)
    assert "HASH_MISMATCH" not in facts.reasons
    assert "assets" in facts.not_evaluated_checks
    v = replace_document(complete_vector(), "baseline", b"bad")
    assert "HASH_MISMATCH" in links(v).reasons


@pytest.mark.parametrize(
    "field,new",
    (
        ("workflow_run_id", "9" * 32),
        ("workflow_attempt_id", "9" * 32),
        ("case", "DFD03"),
        ("producer_source_revision", "9" * 40),
    ),
)
def test_header_identity_mismatch(field, new):
    v = mutate_document(complete_vector(), "exit", lambda d: d["header"].__setitem__(field, new))
    assert "CONTEXT_MISMATCH" in links(v).reasons


def test_reported_source_ids_not_guessed():
    ids = dict(producer_attempt_id="7" * 32, guest_capture_id="9" * 32)
    assert (
        "REPORTED_ID_MISMATCH"
        in links(complete_vector(body_changes={"exit": {"reported_source_ids": ids}})).reasons
    )
    ids["guest_capture_id"] = None
    r = links(complete_vector(body_changes={"exit": {"reported_source_ids": ids}}))
    assert "MISSING_CONTEXT" in r.reasons and "REPORTED_ID_MISMATCH" not in r.reasons


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("host_cli_argv_observed", ["/NOT_THE_HOST_CLI"], "COMMAND_MISMATCH"),
        ("host_interpreter_sha256_observed", "0" * 64, "INTERPRETER_MISMATCH"),
    ),
)
def test_observed_and_intended_command_context(field, value, reason):
    assert reason in links(complete_vector(body_changes={"exit": {field: value}})).reasons


@pytest.mark.parametrize("key", ("LANG", "LC_ALL", "PATH", "PYTHONDONTWRITEBYTECODE"))
def test_each_nonsecret_environment_entry(key):
    env = dict(document(complete_vector(), "exit")["body"]["host_environment_observed"])
    env[key] = "DIFFERENT"
    assert (
        "ENVIRONMENT_MISMATCH"
        in links(complete_vector(body_changes={"exit": {"host_environment_observed": env}})).reasons
    )
    env[key] = None
    assert (
        "MISSING_CONTEXT"
        in links(complete_vector(body_changes={"exit": {"host_environment_observed": env}})).reasons
    )


def test_both_interpreter_environment_conflicts_retained():
    env = dict(document(complete_vector(), "command")["body"]["environment"]) | {"LANG": "OTHER"}
    v = complete_vector(
        body_changes={
            "exit": {"host_environment_observed": env, "host_interpreter_sha256_observed": "0" * 64}
        }
    )
    assert {"INTERPRETER_MISMATCH", "ENVIRONMENT_MISMATCH"} <= set(links(v).reasons)


@pytest.mark.parametrize("field", ("host_cli_argv_observed", "host_interpreter_sha256_observed"))
def test_missing_observation_not_replaced_by_intended(field):
    assert "MISSING_CONTEXT" in links(complete_vector(body_changes={"exit": {field: None}})).reasons


def test_named_role_order_is_irrelevant():
    v = complete_vector()
    other = replace(
        v, bundle=replace(v.bundle, documents=v.bundle.documents[::-1], raw=v.bundle.raw[::-1])
    )
    assert links(v) == links(other)


def test_malformed_raw_can_bind_without_content_validation():
    v = complete_vector(
        raw_changes={
            "record_json": b"\xffnotJSON",
            "exit_receipt": b"{bad",
            "cli_stdout": b"NOT_JSON",
        }
    )
    assert links(v).reasons == ()


@pytest.mark.parametrize("state", ("MISMATCH_REPORTED", "UNAVAILABLE"))
def test_asset_check_not_promoted(state):
    checks = dict(document(complete_vector(), "preflight")["body"]["asset_checks"]) | {
        "kernel": state
    }
    r = links(complete_vector(body_changes={"preflight": {"asset_checks": checks}}))
    assert ("CONTEXT_MISMATCH" if state == "MISMATCH_REPORTED" else "MISSING_CONTEXT") in r.reasons


def test_expected_and_observed_assets_compare_even_partial():
    observed = dict(document(complete_vector(), "preflight")["body"]["observed_assets"])
    observed["probe"] = "0" * 64
    assert (
        "CONTEXT_MISMATCH"
        in links(complete_vector(body_changes={"preflight": {"observed_assets": observed}})).reasons
    )
    observed["probe"] = None
    assert (
        "MISSING_CONTEXT"
        in links(complete_vector(body_changes={"preflight": {"observed_assets": observed}})).reasons
    )


def test_expected_image_not_init_script_matches_raw_image():
    v = complete_vector()
    assert links(v).reasons == ()
    assets = dict(document(v, "baseline")["body"]["expected_assets"])
    assets["image"] = "0" * 64
    bad = complete_vector(
        body_changes={
            "baseline": {"expected_assets": assets},
            "preflight": {"observed_assets": assets},
        }
    )
    assert "CONTEXT_MISMATCH" in links(bad).reasons
    assert assets["init"] != digest(dict(v.bundle.raw)["initrd"])


def test_invalid_container_does_not_open_or_repair_roles():
    v = complete_vector()
    v = replace(v, bundle=replace(v.bundle, documents=v.bundle.documents[:-1]))
    assert "headers" in links(v).not_evaluated_checks
