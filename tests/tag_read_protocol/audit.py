"""Offline synthetic design replay and static references,never actual-read admission."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import PERMISSIONS, need, shape
from tests.audit.validate_kernel_lifetime_feasibility import load
from tests.bootstrap_tag_audit.audit import SOURCES as AUDITED_SOURCES
from tests.bootstrap_tag_audit.audit import _digest as digest
from tests.bootstrap_tag_audit.audit import validate_sources as validate_audited_sources

from .model import BASE, FALSE_FIELDS, SECTION_FIELDS, SOURCE_DIGEST, TOP_FIELDS, VERSION, evaluate

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs/evidence/tag_read_protocol_schema.json"
SOURCES = ROOT / "docs/evidence/tag_read_protocol_sources.json"
CASES = ROOT / "docs/evidence/tag_read_protocol_cases.json"
SCHEMA_DIGEST = "8f10186b5757b137ead2b23b17d5d0fda4f623636179a909b5537df3e7ed67f1"
SOURCES_DIGEST = "b4a20e13b556d2d482b2aec566669604a76b64ea5dda9e36645420e40c0d4f07"
CASES_DIGEST = "f9728363b6d7f2fab767bd55a3018ce08e1c769e2c76991e8daac01018ae08c6"


def validate_schema(data: Any) -> None:
    need(digest(data) == SCHEMA_DIGEST, "SEMANTIC_SCHEMA_DRIFT")
    need(data["model_version"] == VERSION and data["source_base"] == BASE, "SCHEMA_PROFILE_DRIFT")
    for section, fields in (("envelope", TOP_FIELDS), *SECTION_FIELDS):
        rows = data["sections"][section]
        need(
            len(rows) == len(fields) and {r["field"] for r in rows} == fields,
            "SCHEMA_MODEL_FIELD_DRIFT",
        )
    need(
        data["evidence_class"] == "SYNTHETIC_ONLY"
        and data["status"] == "BLOCKED"
        and data["wire_implemented"] is False
        and set(data["qualifications"]) == set(FALSE_FIELDS)
        and all(v is False for v in data["qualifications"].values())
        and data["permissions"] == dict(PERMISSIONS)
        and all(v is False for v in data["permissions"].values())
        and data["actual_global_drops"] is None
        and data["actual_prohibited_operations"] is None,
        "DESIGN_SCHEMA_HAS_NO_AUTHORITY",
    )


def validate_sources(data: Any) -> frozenset[str]:
    need(digest(data) == SOURCES_DIGEST, "SOURCE_REFERENCES_DRIFT")
    need(
        data["base_revision"] == BASE and data["source_catalog_digest"] == SOURCE_DIGEST,
        "SOURCE_COHORT_MISMATCH",
    )
    for row in data["repository_files"]:
        with (ROOT / row["path"]).open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        need(
            len(raw) <= 4 * 1024 * 1024
            and len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "SOURCE_REFERENCE_BYTES_CHANGED",
        )
    # Source catalog integrity only. The parent may hash-check old actual-manifest
    # bytes as provenance,but never parses/passes actual records to this model.
    prior_claims = validate_audited_sources(load(AUDITED_SOURCES))
    claims = frozenset(data["claims"])
    need(len(claims) == 10 and claims <= prior_claims, "SOURCE_CLAIMS_UNBOUND")
    return claims


def validate_cases(data: Any) -> tuple[int, int]:
    need(digest(data) == CASES_DIGEST, "SYNTHETIC_CATALOG_DRIFT")
    need(
        data["evidence_class"] == "SYNTHETIC_ONLY"
        and data["base_revision"] == BASE
        and data["model_version"] == VERSION,
        "SYNTHETIC_CASE_COHORT",
    )
    rows = data["cases"]
    need(len(rows) == 60 and len({r["name"] for r in rows}) == 60, "FINITE_CASE_COHORT")
    consistent = 0
    for row in rows:
        shape(row, {"name", "payload", "expected_consistent"})
        need(type(row["expected_consistent"]) is bool, "LITERAL_EXPECTATION_REQUIRED")
        result = evaluate(row["payload"])
        need(result.premises_consistent is row["expected_consistent"], "SYNTHETIC_OUTCOME_MISMATCH")
        need(
            result.status == "BLOCKED"
            and result.evidence_class == "SYNTHETIC_ONLY"
            and all(getattr(result, name) is False for name in FALSE_FIELDS)
            and result.actual_global_drops is None
            and result.actual_prohibited_operations is None
            and result.permissions == PERMISSIONS
            and all(v is False for _, v in result.permissions)
            and (result.proposed_snapshot is not None) is result.premises_consistent,
            "NO_ACTUAL_IDENTITY_OR_RUNTIME_AUTHORITY",
        )
        consistent += result.premises_consistent
    return len(rows), consistent


def validate() -> dict[str, Any]:
    claims = validate_sources(load(SOURCES))
    validate_schema(load(SCHEMA))
    count, consistent = validate_cases(load(CASES))
    return dict(
        synthetic_cases=count,
        consistent_cases=consistent,
        inconsistent_cases=count - consistent,
        source_claims=len(claims),
        retained_source_obligations=13,
        evidence_class="SYNTHETIC_ONLY",
        source_reference_evidence_class="STATIC_SOURCE_AUDIT_ONLY",
        status="BLOCKED",
        external_source_bytes_verified=False,
        actual_records_passed_to_model=False,
        actual_capture_adapter_implemented=False,
        actual_global_drops=None,
        actual_prohibited_operations=None,
        permissions=dict(PERMISSIONS),
        **dict.fromkeys(FALSE_FIELDS, False),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
