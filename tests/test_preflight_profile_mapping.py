"""Source evidence remains diagnostic, typed, redacted and non-authoritative."""

import copy
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256

import pytest

from tests.fixtures.preflight_profile_mapping import (
    S0,
    binding_fields,
    encoded,
    registration,
    source_bytes,
    source_document,
)


def api():
    assert importlib.util.find_spec("tests.audit_preflight_profile_mapping") is not None, (
        "diagnostic mapper missing"
    )
    return importlib.import_module("tests.audit_preflight_profile_mapping")


def complete():
    module = api()
    return module.map_registered_preflight(
        source_bytes(), module.PreflightRunBinding(**binding_fields()), source_profile_id=S0
    )


@pytest.mark.parametrize("case", registration()["acceptance"]["cases"], ids=lambda c: c["id"])
def test_reviewed_acceptance_case(case):
    module = api()
    values = {"source": source_document(), "binding": binding_fields()}
    for mutation in case["mutations"]:
        target = values
        for key in mutation[:-2]:
            target = target[key]
        target[mutation[-2]] = mutation[-1]
    raw = encoded(values["source"])
    if "raw_override" in case:
        raw = bytes.fromhex(case["raw_override"]["hex"])
    transform = case.get("raw_transform")
    if transform == "DUPLICATE_IDENTICAL_SCHEMA_KEY":
        raw = b'{"schema":"actions-runner-preflight-v1",' + raw[1:]
    elif transform == "ASCII_SPACE_32769_BYTES":
        raw = b" " * 32769
    elif transform == "REVERSE_ROOT_KEY_ORDER_PRETTY_JSON_NO_RECOMPUTED_PROFILE_HASH":
        raw = json.dumps(dict(reversed(list(values["source"].items()))), indent=2).encode()
    binding = None if case["binding"] == "NONE" else module.PreflightRunBinding(**values["binding"])

    def evaluate():
        return module.map_registered_preflight(
            raw, binding, source_profile_id=case["source_profile_id"]
        )

    if case["expected_ValueError"]:
        with pytest.raises(ValueError):
            evaluate()
        return
    result = evaluate()
    assert result.source_consistency == case["expected_consistency"]
    assert set(case["required_error_codes"]) <= {r.code for r in result.errors}
    assert set(case["required_unavailable_codes"]) <= {r.code for r in result.unavailable}
    diagnostics = {d.source_pointer: d for d in result.diagnostics}
    for expected in case["diagnostic_assertions"]:
        diagnostic = diagnostics[expected["pointer"]]
        for key in ("value", "availability", "meaning"):
            if key in expected:
                assert getattr(diagnostic, key) == expected[key]
                if key == "value":
                    assert type(diagnostic.value) is type(expected[key])
    if "no_unexpected_text_in_decision" in case:
        assert case["no_unexpected_text_in_decision"] not in repr(result)
    assert result.mapping_status == "DIAGNOSTIC_ONLY" and result.profile_record is None
    assert not result.H_executed and not result.integrated_admission
    assert result.content_identity_only and result.atomicity == "NOT_ESTABLISHED"
    assert len(result.permissions) == 9 and all(flag is False for _, flag in result.permissions)
    assert len(result.diagnostics) == 83 and len(result.target_gaps) == 132
    assert result.source_sha256 == sha256(raw).hexdigest()


@pytest.mark.parametrize("field", list(binding_fields()))
def test_every_binding_field_missing_is_not_borrowed(field):
    module = api()
    values = binding_fields()
    values[field] = None
    result = module.map_registered_preflight(
        source_bytes(), module.PreflightRunBinding(**values), source_profile_id=S0
    )
    assert result.source_consistency == "UNAVAILABLE_BINDING"
    assert ("BINDING_VALUE_UNAVAILABLE", "binding." + field) in {
        (r.code, r.subject) for r in result.unavailable
    }


@pytest.mark.parametrize("field", list(binding_fields()))
def test_every_available_wrong_binding_field_rejects(field):
    module = api()
    values = binding_fields()
    old = values[field]
    values[field] = (
        0 if type(old) is int else ("other/repo" if field == "repository" else "0" * len(old))
    )
    result = module.map_registered_preflight(
        source_bytes(), module.PreflightRunBinding(**values), source_profile_id=S0
    )
    assert result.source_consistency == "REGISTERED_SNAPSHOT_MISMATCH"
    assert ("BINDING_VALUE_MISMATCH", "binding." + field) in {
        (r.code, r.subject) for r in result.errors
    }


@pytest.mark.parametrize(
    "bad",
    [
        b"",
        b"{}",
        b"null",
        b"[]",
        b"1",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{}{}",
        b"NaN",
        b"[" * 1200 + b"]" * 1200,
        b" " * 32769,
        "{}",
        bytearray(b"{}"),
    ],
)
def test_raw_structure_encoding_capacity_and_exact_type_rejected(bad):
    module = api()
    with pytest.raises(ValueError):
        module.map_registered_preflight(bad)


def _leaves(value, path=()):
    if type(value) is dict:
        for key, child in value.items():
            yield from _leaves(child, (*path, key))
    elif type(value) is list:
        for i, child in enumerate(value):
            yield from _leaves(child, (*path, i))
    else:
        yield path


@pytest.mark.parametrize(
    "path", list(_leaves(source_document())), ids=lambda p: "/".join(map(str, p))
)
def test_every_source_leaf_rejects_wrong_graph_even_if_not_exported(path):
    module = api()
    doc = source_document()
    parent = doc
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = {"FICTIONAL_SECRET_CANARY": "do not echo"}
    with pytest.raises(ValueError) as caught:
        module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    assert "FICTIONAL_SECRET_CANARY" not in str(caught.value)


def test_immutable_values_have_no_authority_fields_and_diagnostics_are_owned():
    module = api()
    result = complete()
    assert result.evidence_kind == "SYNTHETIC_NOT_OBSERVED_OR_H_BUDGET"
    assert not hasattr(result, "__dict__")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.source_sha256 = "0" * 64
    for cls in (
        module.PreflightRunBinding,
        module.SourceDiagnostic,
        module.TargetGap,
        module.MappingReason,
        module.PreflightMappingDecision,
    ):
        assert not {"profile_record", "permissions", "H_executed", "mapping_status"} & {
            f.name for f in fields(cls)
        }
    reversed_diagnostics = tuple(reversed(result.diagnostics))
    owned = replace(result, diagnostics=reversed_diagnostics)
    assert owned.diagnostics is not reversed_diagnostics
    assert owned.diagnostics == result.diagnostics
    for field in ("diagnostics", "target_gaps"):
        for value in ([], (), (getattr(result, field)[0],) * len(getattr(result, field))):
            with pytest.raises(ValueError):
                replace(result, **{field: value})


def test_redaction_marker_is_available_and_cannot_be_forged_to_echo_text():
    module = api()
    marker = "[REDACTED_UNREGISTERED_SOURCE_TEXT]"
    diagnostic = module.SourceDiagnostic("/security/CapEff", marker, "SOURCE_TEXT_REDACTED")
    assert diagnostic.availability == "AVAILABLE"
    for pointer, value, meaning in (
        ("/status", "FICTIONAL_PRIVATE_CANARY", "NON_AUTHORITY_DECLARATION"),
        ("/security/CapEff", marker, "HOST_PROCESS_CONTEXT_ONLY"),
        ("/security/NoNewPrivs", marker, "SOURCE_TEXT_REDACTED"),
        ("/security/CapEff", None, "SOURCE_TEXT_REDACTED"),
        ("/host/uid", 0, "HOST_PROCESS_CONTEXT_ONLY"),
    ):
        with pytest.raises(ValueError) as caught:
            module.SourceDiagnostic(pointer, value, meaning)
        assert "FICTIONAL_PRIVATE_CANARY" not in str(caught.value)
    result = complete()
    bad = copy.deepcopy(result.diagnostics[0])
    object.__setattr__(bad, "value", "FICTIONAL_PRIVATE_CANARY")
    with pytest.raises(ValueError):
        replace(result, diagnostics=(bad,) + result.diagnostics[1:])


def test_binding_forgery_subclasses_and_reason_categories_reject():
    module = api()
    binding = module.PreflightRunBinding(**binding_fields())
    object.__setattr__(binding, "attempt", True)
    with pytest.raises(ValueError):
        module.map_registered_preflight(source_bytes(), binding, source_profile_id=S0)
    with pytest.raises(ValueError):
        module.map_registered_preflight(source_bytes(), object(), source_profile_id=S0)

    class Foreign(module.PreflightRunBinding):
        pass

    with pytest.raises(ValueError):
        Foreign(**binding_fields())
    result = complete()
    missing = module.MappingReason("BINDING_UNAVAILABLE", "binding")
    with pytest.raises(ValueError):
        replace(result, errors=(missing,))
    for code, subject in (("UNKNOWN", "binding"), ("BINDING_UNAVAILABLE", "private/source/path")):
        with pytest.raises(ValueError):
            module.MappingReason(code, subject)


def test_known_errors_precede_missing_binding_without_losing_source_facts():
    module = api()
    doc = source_document()
    doc["permissions"]["application_authorized"] = True
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    assert result.source_consistency == "REGISTERED_SNAPSHOT_MISMATCH"
    assert {"REGISTERED_SNAPSHOT_CONTENT_MISMATCH", "SOURCE_DECLARATION_CONTRADICTION"} <= {
        r.code for r in result.errors
    }
    assert any(r.code == "BINDING_UNAVAILABLE" for r in result.unavailable)
    assert next(d for d in result.diagnostics if d.source_pointer == "/security/Seccomp").value == 0


def test_security_reads_are_collector_process_context_not_declared_flags():
    result = complete()
    security = [d for d in result.diagnostics if d.source_pointer.startswith("/security/")]
    assert len(security) == 3
    assert all(d.meaning == "HOST_PROCESS_CONTEXT_ONLY" for d in security)


def test_forged_expected_pin_cannot_fabricate_a_legacy_content_mismatch():
    module = api()
    doc = source_document()
    tool = doc["tools"]["/usr/bin/setpriv"]
    tool["sha256"] = tool["expected_sha256"]  # Actual equals the registered legacy pin.
    tool["expected_sha256"] = "3" * 64
    tool["pin_matches"] = False
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    diagnostic = next(
        d
        for d in result.diagnostics
        if d.source_pointer == "/tools/~1usr~1bin~1setpriv/pin_matches"
    )
    assert diagnostic.value is False
    assert diagnostic.meaning == "LEGACY_TOOL_CONTENT_ONLY"
    assert any(r.code == "SOURCE_DECLARATION_CONTRADICTION" for r in result.errors)


@pytest.mark.parametrize(
    "available,required,inconsistent",
    [(True, None, True), (False, True, True), (False, None, False), (True, False, False)],
)
@pytest.mark.parametrize("name", ["fcntl", "resource"])
def test_native_module_presence_and_api_availability_are_separate(
    available, required, inconsistent, name
):
    module = api()
    doc = source_document()
    doc["native_apis"][name].update(module_available=available, required_apis_present=required)
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    found = [(r.code, r.subject) for r in result.errors]
    assert (
        ("SOURCE_TOOL_RELATION_INCONSISTENT", f"source:/native_apis/{name}/required_apis_present")
        in found
    ) is inconsistent
    diagnostic = next(
        d
        for d in result.diagnostics
        if d.source_pointer == f"/native_apis/{name}/required_apis_present"
    )
    assert diagnostic.value is required and result.profile_record is None


@pytest.mark.parametrize(
    "status,membership,coherent",
    [
        ("UNAVAILABLE_MEMBERSHIP", False, True),
        ("UNAVAILABLE_MEMBERSHIP", None, True),
        ("UNAVAILABLE_MEMBERSHIP", True, False),
        ("UNAVAILABLE_COHORT_DRIFT", None, True),
        ("UNAVAILABLE_COHORT_DRIFT", False, False),
        ("UNAVAILABLE_MAPPING", None, True),
        ("UNAVAILABLE_MAPPING", True, False),
        ("MEMBERSHIP_OBSERVED_NOT_DELEGATION", False, False),
    ],
)
def test_cgroup_source_branch_relations_never_imply_h_ownership(status, membership, coherent):
    module = api()
    doc = source_document()
    doc["cgroup"].update(status=status, membership_confirmed=membership)
    if status != "MEMBERSHIP_OBSERVED_NOT_DELEGATION":
        doc["cgroup"].update(directory=None, controls=None)
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    found = {(r.code, r.subject) for r in result.errors}
    assert (("SOURCE_DECLARATION_CONTRADICTION", "source:/cgroup/status") in found) is (
        not coherent
    )
    assert len(result.target_gaps) == 132 and not result.H_executed


def test_false_pin_without_content_is_not_a_known_legacy_hash_failure():
    module = api()
    doc = source_document()
    doc["tools"]["/usr/bin/bwrap"]["pin_matches"] = False
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    diagnostic = next(
        d for d in result.diagnostics if d.source_pointer == "/tools/~1usr~1bin~1bwrap/pin_matches"
    )
    assert diagnostic.value is False and diagnostic.meaning == "LEGACY_TOOL_CONTENT_ONLY"
    assert any(r.code == "SOURCE_TOOL_RELATION_INCONSISTENT" for r in result.errors)


def test_incomplete_and_forged_dtos_are_revalidated_without_echoing_values():
    module = api()
    incomplete = object.__new__(module.PreflightRunBinding)
    with pytest.raises(ValueError):
        module.map_registered_preflight(source_bytes(), incomplete, source_profile_id=S0)
    result = complete()
    with pytest.raises(ValueError):
        replace(
            result, diagnostics=(object.__new__(module.SourceDiagnostic),) + result.diagnostics[1:]
        )
    with pytest.raises(ValueError):
        module.TargetGap(result.target_gaps[0].target_path, "UNKNOWN")
    with pytest.raises(ValueError):
        replace(
            result, unavailable=(module.MappingReason("BINDING_VALUE_MISMATCH", "binding.job_id"),)
        )
    with pytest.raises(ValueError):
        replace(result, errors=[])


@pytest.mark.parametrize(
    "path,value",
    [
        (("host", "python_version", 0), 2**64),
        (("host", "uid"), -1),
        (("host", "uid"), False),
        (("security", "Seccomp"), 3),
        (("security", "NoNewPrivs"), 2),
        (("security", "CapEff"), "NOT_HEX"),
        (("cgroup", "controls", "cpu.max", "value"), "0 1"),
        (("cgroup", "controls", "cpu.max", "value"), "max 0"),
        (("cgroup", "controls", "memory.max", "value"), "-1"),
        (("cgroup", "controls", "cgroup.controllers", "value"), "cpu cpu"),
        (("cgroup", "controls", "cgroup.controllers", "value"), "UNKNOWN"),
        (("cgroup", "directory", "mode"), "0999"),
        (("cgroup", "directory", "effective_write_access"), 0),
        (("host", "python_version"), [3, 12]),
    ],
)
def test_strict_source_formats_types_and_ranges_are_not_coerced(path, value):
    module = api()
    doc = source_document()
    parent = doc
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError):
        module.map_registered_preflight(encoded(doc), source_profile_id=S0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_json_is_rejected_without_input_echo(value):
    module = api()
    doc = source_document()
    doc["host"]["python_version"][0] = value
    with pytest.raises(ValueError):
        module.map_registered_preflight(json.dumps(doc).encode(), source_profile_id=S0)


def test_null_metadata_is_unavailable_while_zero_remains_available():
    module = api()
    doc = source_document()
    doc["cgroup"]["directory"] = None
    doc["cgroup"]["controls"]["pids.max"]["metadata"] = None
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    diagnostics = {d.source_pointer: d for d in result.diagnostics}
    assert diagnostics["/cgroup/directory/mode"].value is None
    assert (
        diagnostics["/cgroup/controls/pids.max/metadata/effective_write_access"].availability
        == "UNAVAILABLE"
    )
    assert diagnostics["/security/NoNewPrivs"].value == 0
    assert diagnostics["/security/NoNewPrivs"].availability == "AVAILABLE"


def test_default_profile_never_selects_synthetic_input_automatically():
    module = api()
    result = module.map_registered_preflight(
        source_bytes(), module.PreflightRunBinding(**binding_fields())
    )
    assert result.source_profile_id == "REGISTERED_PREFLIGHT_R0"
    assert result.source_consistency == "REGISTERED_SNAPSHOT_MISMATCH"
    assert result.evidence_kind == "REGISTERED_SOURCE_CONTEXT_ONLY_NOT_H"


@pytest.mark.parametrize(
    "pointer", registration()["contract"]["diagnostic_string_policy"]["safe_values_by_pointer"]
)
def test_every_string_pointer_rejects_forged_unregistered_text(pointer):
    module = api()
    result = complete()
    diagnostics = list(copy.deepcopy(result.diagnostics))
    index = next(i for i, d in enumerate(diagnostics) if d.source_pointer == pointer)
    object.__setattr__(diagnostics[index], "value", "FICTIONAL_PRIVATE_CANARY")
    with pytest.raises(ValueError) as caught:
        replace(result, diagnostics=tuple(diagnostics))
    assert "FICTIONAL_PRIVATE_CANARY" not in str(caught.value)
    marker = module.SourceDiagnostic(
        pointer, "[REDACTED_UNREGISTERED_SOURCE_TEXT]", "SOURCE_TEXT_REDACTED"
    )
    assert marker.availability == "AVAILABLE"


@pytest.mark.parametrize(
    "path,value,pointer",
    [
        (("cgroup", "directory", "mode"), "0777", "/cgroup/directory/mode"),
        (("execution_context", "run_id"), "2", "/execution_context/run_id"),
        (("tools", "/usr/bin/setpriv", "sha256"), "3" * 64, "/tools/~1usr~1bin~1setpriv/sha256"),
        (
            ("cgroup", "controls", "cgroup.controllers", "value"),
            "cpu",
            "/cgroup/controls/cgroup.controllers/value",
        ),
    ],
)
def test_unregistered_but_valid_source_text_is_redacted_not_unavailable(path, value, pointer):
    module = api()
    doc = source_document()
    parent = doc
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    result = module.map_registered_preflight(encoded(doc), source_profile_id=S0)
    diagnostic = next(d for d in result.diagnostics if d.source_pointer == pointer)
    assert diagnostic.value == "[REDACTED_UNREGISTERED_SOURCE_TEXT]"
    assert diagnostic.meaning == "SOURCE_TEXT_REDACTED" and diagnostic.availability == "AVAILABLE"
    assert any(r.code == "REGISTERED_SNAPSHOT_CONTENT_MISMATCH" for r in result.errors)
