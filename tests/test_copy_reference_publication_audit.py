"""Independent static-audit expectations catch missing duties and type conflation."""

import copy
import importlib
from dataclasses import FrozenInstanceError, asdict

import pytest


def api():
    try:
        return importlib.import_module("tests.copy_reference_audit.audit")
    except ModuleNotFoundError:
        pytest.fail("MISSING_COPY_REFERENCE_PUBLICATION_AUDIT")


def catalog():
    audit = api()
    sources = audit.load_catalog(audit.SOURCES)
    result = audit.load_catalog(audit.RESULT)
    claims = audit.validate_sources(sources)
    return audit, result, claims


def test_static_result_separates_six_dimensions_and_never_qualifies():
    audit, data, claims = catalog()
    result = audit.validate_result(data, claims)
    assert {r.dimension for r in result.dimensions} == {
        "CONSUMED_REFERENCE",
        "TAG_PUBLICATION",
        "SNAPSHOT_TRANSFER",
        "IDENTITY_MEMBERSHIP",
        "REPRESENTATION",
        "ADMISSION",
    }
    assert result.evidence_class == "STATIC_SOURCE_AUDIT_ONLY" and result.status == "BLOCKED"
    assert result.source_binding_qualified is result.publication_qualified is False
    assert result.type_fidelity_qualified is result.runtime_qualified is False
    assert result.allocation_history_complete is result.atomic_cut_proven is False
    assert result.actual_global_drops is result.actual_prohibited_operations is None
    assert all(v is False for _, v in result.permissions) and len(result.permissions) == 9
    with pytest.raises(FrozenInstanceError):
        result.status = "ELIGIBLE"


def test_epoch_object_saved_buffer_wire_and_probe_domains_are_not_conflated():
    audit, data, claims = catalog()
    result = audit.validate_result(data, claims)
    flows = {f.field: f for f in result.type_flows}
    epoch = flows["raw_epoch"]
    assert (epoch.object_type, epoch.saved_type, epoch.buffer_type) == (
        "u64",
        "unsigned int",
        "unsigned int",
    )
    assert (epoch.wire, epoch.decoder_domain, epoch.probe_object_type) == (
        "%u",
        "UInt64",
        "unsigned int",
    )
    assert epoch.source_width_effect == "SOURCE_TO_SAVED_NARROWING_POSSIBLE"
    assert flows["raw_cookie"].source_width_effect == "DECLARED_WIDTH_PRESERVED"
    assert flows["raw_scope"].object_type == "u64"
    assert flows["raw_origin"].object_type == "u8"
    assert flows["raw_origin"].source_width_effect == "DECLARED_WIDENING"


def test_default_byte_audit_does_not_claim_external_or_semantic_verification():
    result = api().validate()
    assert result["dimensions"] == 6 and result["type_flow_fields"] == 4
    assert result["embedded_range_hashes_verified"]
    assert not result["external_source_bytes_verified"]
    assert not result["source_interpretations_machine_proven"]
    assert result["actual_runtime_executions_this_task"] == 0
    assert result["prior_observations_reclassified"] is False
    assert result["runtime_qualified"] is result["publication_qualified"] is False


def test_independent_publication_arguments_retain_exact_missing_guards():
    audit, data, claims = catalog()
    result = audit.validate_result(data, claims)
    pub = next(r for r in result.dimensions if r.dimension == "TAG_PUBLICATION")
    assert set(pub.conditional_arguments) == {
        "PREINSTALL_INITIALIZATION_ORDER_CONDITIONAL",
        "SAME_NAMESPACE_LOCK_HANDOFF_CONDITIONAL",
    }
    assert "AFTER_PUBLICATION_SEED_REQUIRES_EXACT_GUARD" in pub.open_obligations
    assert "ALIAS_NAMESPACE_WRITERS_NOT_EXCLUDED" in pub.open_obligations
    assert "ALL_TAG_WRITERS_NOT_CLOSED" in pub.open_obligations


def test_closed_result_is_defensively_copied_and_order_independent():
    audit, data, claims = catalog()
    first = audit.assess(data["dimensions"], data["type_flows"], claims)
    frozen = asdict(first)
    data["dimensions"].reverse()
    data["type_flows"].reverse()
    for row in data["dimensions"]:
        for key in ("citations", "conditional_arguments", "open_obligations"):
            row[key].reverse()
    assert audit.assess(data["dimensions"], data["type_flows"], claims) == first
    data["dimensions"][0]["citations"].clear()
    data["type_flows"][0]["object_type"] = "invented"
    assert asdict(first) == frozen


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_dimension",
        "duplicate_dimension",
        "unknown_dimension",
        "extra_field",
        "missing_citation",
        "duplicate_citation",
        "foreign_citation",
        "missing_obligation",
        "duplicate_obligation",
        "qualified_argument",
        "missing_flow",
        "duplicate_flow",
        "epoch_object_type",
        "epoch_saved_type",
        "epoch_probe_type",
        "epoch_wire_type",
        "epoch_decoder_domain",
        "epoch_effect",
        "fake_type_proof",
        "extra_claim",
        "missing_claim",
    ],
)
def test_closed_metadata_cannot_erase_duties_or_relabel_type_fidelity(mutation):
    audit, data, claims = catalog()
    rows, flows = data["dimensions"], data["type_flows"]
    row = rows[0]
    epoch = next(f for f in flows if f["field"] == "raw_epoch")
    if mutation == "missing_dimension":
        rows.pop()
    elif mutation == "duplicate_dimension":
        rows[-1] = copy.deepcopy(row)
    elif mutation == "unknown_dimension":
        row["dimension"] = "APPLICATION"
    elif mutation == "extra_field":
        row["source_binding_qualified"] = True
    elif mutation == "missing_citation":
        row["citations"].pop()
    elif mutation == "duplicate_citation":
        row["citations"][-1] = row["citations"][0]
    elif mutation == "foreign_citation":
        row["citations"][-1] = "GET_FILE_PROVES_ACQUIRE"
    elif mutation == "missing_obligation":
        row["open_obligations"].pop()
    elif mutation == "duplicate_obligation":
        row["open_obligations"][-1] = row["open_obligations"][0]
    elif mutation == "qualified_argument":
        row["conditional_arguments"][0] = "UNCONDITIONAL_RUNTIME_PROOF"
    elif mutation == "missing_flow":
        flows.pop()
    elif mutation == "duplicate_flow":
        flows[-1] = copy.deepcopy(flows[0])
    elif mutation.startswith("epoch_"):
        key = {
            "epoch_object_type": "object_type",
            "epoch_saved_type": "saved_type",
            "epoch_probe_type": "probe_object_type",
            "epoch_wire_type": "wire",
            "epoch_decoder_domain": "decoder_domain",
            "epoch_effect": "source_width_effect",
        }[mutation]
        epoch[key] = "u64" if epoch[key] != "u64" else "unsigned int"
    elif mutation == "fake_type_proof":
        epoch["runtime_type_proven"] = True
    elif mutation == "extra_claim":
        claims |= {"FABRICATED_SOURCE"}
    else:
        claims = frozenset(set(claims) - {next(iter(claims))})
    with pytest.raises(ValueError):
        audit.assess(rows, flows, claims)


@pytest.mark.parametrize("bad", [None, True, 0, {}, "SOURCE_AUDIT", [None] * 6])
def test_unavailable_or_wrong_typed_catalog_is_not_a_default_audit(bad):
    audit, data, claims = catalog()
    with pytest.raises(ValueError):
        audit.assess(bad, data["type_flows"], claims)


@pytest.mark.parametrize(
    "flag",
    [
        "runtime_qualified",
        "publication_qualified",
        "source_binding_qualified",
        "type_fidelity_qualified",
    ],
)
def test_result_manifest_cannot_upgrade_source_checks_to_authority(flag):
    audit, data, claims = catalog()
    data["qualification"][flag] = True
    with pytest.raises(ValueError):
        audit.validate_result(data, claims)


def test_source_catalog_drift_rejected_before_any_metadata_filesystem_read():
    audit = api()
    data = audit.load_catalog(audit.SOURCES)
    data["kernel_files"][0]["path"] = "../../outside"
    with pytest.raises(ValueError, match="CATALOG_DRIFT"):
        audit.validate_sources(data)


def test_wrong_explicit_source_root_is_not_silently_embedded_only(tmp_path):
    audit = api()
    with pytest.raises((ValueError, OSError)):
        audit.validate_sources(audit.load_catalog(audit.SOURCES), tmp_path)


def test_duplicate_json_fields_and_oversized_catalog_rejected(tmp_path):
    audit = api()
    path = tmp_path / "catalog.json"
    path.write_bytes(b'{"schema":1,"schema":1}')
    with pytest.raises(ValueError, match="DUPLICATE"):
        audit.load_catalog(path)
    path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="BOUND"):
        audit.load_catalog(path)
