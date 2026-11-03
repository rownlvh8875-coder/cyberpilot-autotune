"""Parser/profile regressions. Raw bytes must never become document JSON."""

import importlib
import importlib.util
from dataclasses import asdict, replace
from hashlib import sha256

import pytest

from tests.diagnostics.actual_binding.actual_binding_test_vectors import (
    DOCS,
    canonical,
    complete_vector,
    document,
    mutate_document,
    replace_document,
)


def codec():
    assert (
        importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding._codec")
        is not None
    ), "bounded codec missing"
    return importlib.import_module("cyberpilot_autotune.diagnostics.actual_binding._codec")


def decode(v):
    return codec().decode_documents(v.bundle)


def test_canonical_six_documents_only():
    v = complete_vector()
    d = decode(v)
    assert d.reasons == ()
    assert set(d.documents) == set(DOCS)
    assert all(raw.startswith(b"TEST_ONLY") for name, raw in v.bundle.raw if name != "cli_stderr")
    assert v.label == "TEST_ONLY_NOT_REAL_EVIDENCE"


@pytest.mark.parametrize("raw", (b"{}", b"[]", b"null", b"false", b'{"header":{}}'))
def test_incomplete_document_shape_rejects(raw):
    assert (
        "DOCUMENT_SHAPE_INVALID"
        in decode(replace_document(complete_vector(), "baseline", raw)).reasons
    )


@pytest.mark.parametrize(
    "raw",
    (
        b"not json",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{\0}",
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1.0}',
        b'{"x":1e0}',
        b"[" * 1500 + b"]" * 1500,
        b'{"x":' + b"1" * 5000 + b"}",
    ),
)
def test_noncanonical_and_bad_json_reject(raw):
    assert "PARSE_INVALID" in decode(replace_document(complete_vector(), "baseline", raw)).reasons


@pytest.mark.parametrize("suffix", (b"\n", b" ", b"\r\n"))
def test_canonical_bytes_not_repaired(suffix):
    v = complete_vector()
    raw = dict(v.bundle.documents)["baseline"]
    assert "PARSE_INVALID" in decode(replace_document(v, "baseline", raw + suffix)).reasons


@pytest.mark.parametrize("key", tuple(document(complete_vector(), "baseline")["header"]))
def test_header_missing_key_rejects(key):
    v = mutate_document(complete_vector(), "baseline", lambda d: d["header"].pop(key))
    assert "DOCUMENT_SHAPE_INVALID" in decode(v).reasons


@pytest.mark.parametrize(
    "role,key", [(r, k) for r in DOCS for k in document(complete_vector(), r)["body"]]
)
def test_body_field_types_and_missing_keys(role, key):
    v = mutate_document(complete_vector(), role, lambda d: d["body"].pop(key))
    assert "DOCUMENT_SHAPE_INVALID" in decode(v).reasons
    v = mutate_document(
        complete_vector(), role, lambda d: d["body"].__setitem__(key, {"bad": False})
    )
    expected = "ROLE_SET_INVALID" if key == "raw_descriptors" else "DOCUMENT_SHAPE_INVALID"
    assert expected in decode(v).reasons


@pytest.mark.parametrize(
    "key,value,reason",
    (
        ("contract_version", "future", "UNSUPPORTED_VERSION"),
        ("mode", "SYNTHETIC", "WRONG_ORIGIN"),
        ("origin", "LEGACY_SAVED_CONTENT_ONLY", "WRONG_ORIGIN"),
        ("synthetic", True, "WRONG_ORIGIN"),
        ("status", "ELIGIBLE", "PERMISSION_ESCALATION"),
        ("role", "exit", "CONTEXT_MISMATCH"),
        ("workflow_run_id", "A" * 32, "DOCUMENT_SHAPE_INVALID"),
        ("workflow_attempt_id", False, "DOCUMENT_SHAPE_INVALID"),
        ("producer_implementation_revision", "main", "DOCUMENT_SHAPE_INVALID"),
        ("producer_source_revision", "c" * 39, "DOCUMENT_SHAPE_INVALID"),
        ("capture_implementation_sha256", 0, "DOCUMENT_SHAPE_INVALID"),
        ("case", "DFD07", "DOCUMENT_SHAPE_INVALID"),
    ),
)
def test_shape_mode_version_reason_split(key, value, reason):
    v = mutate_document(
        complete_vector(), "baseline", lambda d: d["header"].__setitem__(key, value)
    )
    assert reason in decode(v).reasons


@pytest.mark.parametrize(
    "value,valid",
    (
        ("f" * 64, True),
        (None, True),
        ("g" * 64, False),
        (False, False),
        (0, False),
        ([], False),
        ({}, False),
    ),
)
def test_observed_interpreter_is_hash_not_descriptor(value, valid):
    v = complete_vector(body_changes={"exit": {"host_interpreter_sha256_observed": value}})
    assert ("DOCUMENT_SHAPE_INVALID" not in decode(v).reasons) is valid


@pytest.mark.parametrize("value", (True, 0, "false", None))
def test_permission_false_is_exact_bool(value):
    permissions = dict(document(complete_vector(), "snapshot")["header"]["permissions"])
    permissions["application_authorized"] = value
    v = complete_vector(header_changes={"snapshot": {"permissions": permissions}})
    expected = "PERMISSION_ESCALATION" if value is True else "DOCUMENT_SHAPE_INVALID"
    assert expected in decode(v).reasons


def test_unknown_permission_and_extra_document_key_reject():
    v = mutate_document(
        complete_vector(),
        "baseline",
        lambda d: d["header"]["permissions"].__setitem__("extra", False),
    )
    assert "DOCUMENT_SHAPE_INVALID" in decode(v).reasons
    v = mutate_document(
        complete_vector(), "snapshot", lambda d: d["body"].__setitem__("snapshot_sha256", "a" * 64)
    )
    assert "DOCUMENT_SHAPE_INVALID" in decode(v).reasons


def test_record_schema_unsupported_is_not_promoted():
    v = complete_vector(body_changes={"baseline": {"producer_record_schema": "legacy-v1-upgraded"}})
    assert "UNSUPPORTED_VERSION" in decode(v).reasons


@pytest.mark.parametrize(
    "pairs",
    (
        (("baseline", b"{}"),),
        tuple((r, b"{}") for r in DOCS) + (("extra", b"{}"),),
        tuple((r, b"{}") for r in DOCS[:-1]) + (("baseline", b"{}"),),
    ),
)
def test_document_role_set_invalid(pairs):
    v = complete_vector()
    assert (
        "ROLE_SET_INVALID" in codec().decode_documents(replace(v.bundle, documents=pairs)).reasons
    )


def test_raw_and_descriptor_role_set_invalid():
    v = complete_vector()
    assert (
        "ROLE_SET_INVALID"
        in codec().decode_documents(replace(v.bundle, raw=v.bundle.raw[:-1])).reasons
    )
    v = mutate_document(v, "snapshot", lambda d: d["body"]["raw_descriptors"].pop("telemetry"))
    assert "ROLE_SET_INVALID" in decode(v).reasons


@pytest.mark.parametrize(
    "role,cap",
    (
        ("cli_stdout", 65536),
        ("cli_stderr", 65536),
        ("record_json", 65536),
        ("exit_receipt", 65536),
        ("initrd", 4194304),
        ("telemetry", 1048576),
    ),
)
def test_raw_format_cap_boundaries(role, cap):
    changes = {role: b"x" * cap}
    if role == "telemetry":
        changes["console"] = b""
    assert "INPUT_LIMIT" not in decode(complete_vector(raw_changes=changes)).reasons
    changes[role] = b"x" * (cap + 1)
    assert "INPUT_LIMIT" in decode(complete_vector(raw_changes=changes)).reasons


def test_caps_before_parse():
    v = complete_vector()
    bounded_invalid = replace_document(v, "baseline", b"x" * 65536)
    assert "PARSE_INVALID" in decode(bounded_invalid).reasons
    oversized = replace_document(v, "baseline", b"x" * 65537)
    result = decode(oversized)
    assert "INPUT_LIMIT" in result.reasons and "baseline" not in result.documents


def test_explicit_unavailable_document_not_malformed_json():
    result = decode(replace_document(complete_vector(), "baseline", None))
    assert "MISSING_DOCUMENT" in result.reasons
    assert "PARSE_INVALID" not in result.reasons and "baseline" in result.unavailable


def test_reference_domain_identity_matches_independent_literal():
    assert (
        importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding._identity")
        is not None
    ), "identity functions missing"
    m = importlib.import_module("cyberpilot_autotune.diagnostics.actual_binding._identity")
    v = complete_vector()
    pre_value = asdict(v.pre)
    # Independent literal byte layout, not the production canonicalizer.
    pairs = [
        b'"'
        + k.encode()
        + b'":'
        + (str(value).encode() if type(value) is int else b'"' + value.encode() + b'"')
        for k, value in sorted(pre_value.items())
    ]
    literal = (
        b'{"domain":"actual-diagnostic-prelaunch-reference-v1","value":{' + b",".join(pairs) + b"}}"
    )
    assert m.pre_reference_identity(v.pre) == sha256(literal).hexdigest()
    assert m.pre_reference_identity(v.pre) != m.post_reference_identity(v.post)
    assert (
        m.post_reference_identity(v.post)
        == sha256(
            canonical({"domain": "actual-diagnostic-capture-reference-v1", "value": asdict(v.post)})
        ).hexdigest()
    )
    with pytest.raises(ValueError):
        m.pre_reference_identity(v.post)
    with pytest.raises(ValueError):
        m.post_reference_identity(v.pre)


def test_unicode_and_recursion_fail_closed():
    v = complete_vector(body_changes={"command": {"host_cli_argv": ["x\x00y"]}})
    assert "DOCUMENT_SHAPE_INVALID" in decode(v).reasons
    v = complete_vector(body_changes={"command": {"host_cli_argv": ["x\ud800"]}})
    assert "PARSE_INVALID" in decode(v).reasons


@pytest.mark.parametrize(
    "role,key,value",
    (
        ("preflight", "mono_ns", False),
        ("intent", "mono_ns", -1),
        ("exit", "event_ordinal", True),
        ("snapshot", "mono_ns", 2**64),
        (
            "baseline",
            "declared_case_profile",
            dict(
                expected_fds=[1, 0],
                installed_fds=[0],
                cause_fds=[],
                decision_kind="RESULT",
                decision_value="NO_DENIAL",
            ),
        ),
        ("command", "host_cli_cwd", "/a/../b"),
        ("command", "planned_destination", "relative"),
        ("command", "host_cli_argv", []),
        ("command", "host_cli_argv", [False]),
    ),
)
def test_exact_numbers_lists_and_paths(role, key, value):
    assert (
        "DOCUMENT_SHAPE_INVALID"
        in decode(complete_vector(body_changes={role: {key: value}})).reasons
    )
