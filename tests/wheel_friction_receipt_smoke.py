"""Run H7 installed-wheel contract without NumPy, native schemas, or source imports."""

import argparse
import hashlib
import json
import runpy
from dataclasses import replace
from pathlib import Path

from cyberpilot_autotune import observability
from cyberpilot_autotune.observability.schema import semantic_schema
from cyberpilot_autotune.observability.validation import ObservationPolicy, evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    installed = Path(observability.__file__).resolve().parent
    assert not installed.is_relative_to(args.source_root.resolve())
    count = 0
    for source in (args.source_root / "cyberpilot_autotune/observability").glob("*.py"):
        assert (
            hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            == hashlib.sha256(
                (installed / source.name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
        )
        count += 1
    assert count == 6
    fixture = runpy.run_path(str(args.fixture))
    receipt = fixture["complete"]()
    decision = evaluate(receipt, ObservationPolicy())
    assert decision.status.value == "ELIGIBLE"
    assert all(
        getattr(decision, name) is False
        for name in (
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "owner_proposal_allowed",
        )
    )
    for field, record in (("q_observed", "signals"), ("callback_output_raw", "stages")):
        partial = replace(receipt, **{record: replace(getattr(receipt, record), **{field: None})})
        assert evaluate(partial, ObservationPolicy()).status.value == "REJECTED"
    assert semantic_schema() == json.loads(args.schema.read_text())
    print(
        "H7_WHEEL_PASS: 6 hashes / immutable full+partial receipts / semantic schema / no authority"
    )


if __name__ == "__main__":
    main()
