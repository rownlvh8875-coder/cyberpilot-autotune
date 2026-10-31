"""Read-only frozen fixture/source audit; never a producer or actual adapter."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tests.audit.fd_ofd_lifetime_model import need
from tests.bootstrap_tag_audit.audit import _digest
from tests.copy_reference_audit.audit import (
    ROOT,
    SOURCE_DIGEST,
    SOURCES,
    load_catalog,
    validate_sources,
)

from .model import EpochScalar, PipelineDecision, assess_pipeline, decode_design, encode_design

CASES = ROOT / "docs/evidence/epoch_encoding_design_cases.json"
CASE_DIGEST = "e177e7c7d95fb083e2f5ec10f63fffd89cdbbd60bd8128732b8e48ede5250e53"


def validate_cases(data: Any) -> dict[str, int]:
    # Closed digest is checked before using any catalog value. JSON numbers
    # above 2^53 are deliberately absent: decimal strings retain exactness.
    need(_digest(data) == CASE_DIGEST, "CASE_CATALOG_DRIFT")
    for value in data["boundaries"]:
        epoch = EpochScalar(None if value is None else int(value))
        wire = encode_design(epoch)
        expected_tail = (
            b"availability=UNAVAILABLE raw_epoch=UNAVAILABLE\n"
            if value is None
            else b"availability=OBSERVED raw_epoch=" + value.encode("ascii") + b"\n"
        )
        need(wire.endswith(expected_tail) and decode_design(wire) == epoch, "FIXTURE_ENCODING")
        result = assess_pipeline(epoch, epoch, epoch, wire, epoch)
        need(result.consistent and result.status == "BLOCKED", "NO_SYNTHETIC_PROMOTION")
    for row in data["mismatches"]:
        source, saved, buffered, wire_epoch, decoded = (
            EpochScalar(None if value is None else int(value)) for value in row["layers"]
        )
        result = assess_pipeline(source, saved, buffered, encode_design(wire_epoch), decoded)
        need(not result.consistent and result.reasons == (row["reason"],), "LOSS_NOT_DETECTED")
    return {"boundary_cases": len(data["boundaries"]), "mismatch_cases": len(data["mismatches"])}


def validate(source_root: Path | None = None) -> dict[str, Any]:
    validate_sources(load_catalog(SOURCES), source_root)
    counts = validate_cases(load_catalog(CASES))
    report = asdict(PipelineDecision((), False))
    report.update(
        counts,
        permissions=dict(report["permissions"]),
        external_source_bytes_verified=source_root is not None,
        source_interpretations_machine_proven=False,
        future_producer_implemented=False,
        reference_source_catalog_digest=SOURCE_DIGEST,
        case_catalog_digest=CASE_DIGEST,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.source_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
