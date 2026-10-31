"""Frozen source-byte/citation verifier,not C semantics or runtime admission."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import need
from tests.bootstrap_tag_audit.audit import _digest, verify_excerpt, verify_source_file

from .model import CLAIMS, ReferenceAudit, assess

ROOT = Path(__file__).resolve().parents[2]
BASE = "5581049957088b348498eb5ef0b1061f76d19b7c"
SOURCES = ROOT / "docs/evidence/copy_reference_publication_sources.json"
RESULT = ROOT / "docs/evidence/copy_reference_publication_result.json"
SOURCE_DIGEST = "11b7d1e538851ee4d93ceb5477a57a805833217c0c2824e711a0796de1c22044"
RESULT_DIGEST = "cdc7aa0cc9c7727141a92882885b1e3bafc7ade1228f87d043e54fd769e38fc1"
QUALIFICATION = frozenset(
    "source_binding_qualified publication_qualified type_fidelity_qualified "
    "epoch_range_invariant_proven runtime_qualified "
    "allocation_history_complete atomic_cut_proven".split()
)


def load_catalog(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            need(key not in result, "DUPLICATE_JSON_FIELD")
            result[key] = value
        return result

    with path.open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    need(len(raw) <= 4 * 1024 * 1024, "CATALOG_RESOURCE_BOUND")
    return json.loads(raw, object_pairs_hook=unique)


def validate_sources(data: Any, source_root: Path | None = None) -> frozenset[str]:
    # Freeze entire metadata before any metadata-derived filesystem access.
    need(_digest(data) == SOURCE_DIGEST, "SOURCE_CATALOG_DRIFT")
    need(
        data["base_revision"] == BASE and data["source_interpretations_machine_proven"] is False,
        "SOURCE_CONTEXT_DRIFT",
    )
    claims = set()
    for row in data["kernel_files"] + data["repository_files"]:
        for span in row.get("ranges", []):
            verify_excerpt(span)
            need(span["claim"] not in claims, "DUPLICATE_SOURCE_CLAIM")
            claims.add(span["claim"])
    need(frozenset(claims) == CLAIMS, "CLAIM_COHORT")
    for row in data["repository_files"]:
        verify_source_file(ROOT, row)
    if source_root is not None:
        for row in data["kernel_files"]:
            verify_source_file(source_root, row)
    return frozenset(claims)


def validate_result(data: Any, claims: frozenset[str]) -> ReferenceAudit:
    need(_digest(data) == RESULT_DIGEST, "RESULT_CATALOG_DRIFT")
    need(
        data["base_revision"] == BASE and data["source_catalog_digest"] == SOURCE_DIGEST,
        "RESULT_SOURCE_COHORT",
    )
    result = assess(data["dimensions"], data["type_flows"], claims)
    need(
        data["evidence_class"] == result.evidence_class
        and data["status"] == result.status
        and data["permissions"] == dict(result.permissions)
        and all(value is False for value in data["permissions"].values())
        and set(data["qualification"]) == QUALIFICATION
        and all(
            value is False and getattr(result, key) is False
            for key, value in data["qualification"].items()
        )
        and data["actual_epoch_loss"]
        is data["actual_global_drops"]
        is data["actual_prohibited_operations"]
        is None
        and data["prior_observations_reclassified"] is False,
        "NO_STATIC_AUDIT_AUTHORITY",
    )
    return result


def validate(source_root: Path | None = None) -> dict[str, Any]:
    sources = load_catalog(SOURCES)
    claims = validate_sources(sources, source_root)
    result = validate_result(load_catalog(RESULT), claims)
    report = asdict(result)
    report["dimension_results"] = report.pop("dimensions")
    report.update(
        dimensions=len(result.dimensions),
        type_flow_fields=len(result.type_flows),
        open_obligations=sum(len(row.open_obligations) for row in result.dimensions),
        conditional_arguments=sum(len(row.conditional_arguments) for row in result.dimensions),
        source_files=dict(
            kernel=len(sources["kernel_files"]), repository=len(sources["repository_files"])
        ),
        embedded_source_ranges=len(claims),
        embedded_range_hashes_verified=True,
        external_source_bytes_verified=source_root is not None,
        source_interpretations_machine_proven=False,
        actual_runtime_executions_this_task=0,
        prior_observations_reclassified=False,
        source_catalog_digest=SOURCE_DIGEST,
        permissions=dict(result.permissions),
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.source_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
