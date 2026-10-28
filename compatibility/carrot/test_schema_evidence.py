"""Frozen metadata and result hashes; this test never rewrites evidence."""

import hashlib
import json
from pathlib import Path

import capnp
import pytest
from openpilot.cereal import car, log

from cyberpilot_autotune.integrations.carrot.availability import (
    INTEGRATION_MERGE,
    ORIGINAL_BASE,
    SCHEMA_LAYOUT_SHA256,
    SOURCE_REVISION,
    require_schema,
    schema_layout,
)
from cyberpilot_autotune.integrations.carrot.errors import CarrotSchemaIncompatible
from tests.audit.test_observation_v2_cases import CASES


def test_actual_layout_and_all_independent_expected_result_hashes():
    root = Path(__file__).resolve().parents[2]
    evidence = json.loads(
        (root / "docs/evidence/carrot_phase8b_schema_compatibility.json").read_text()
    )
    assert evidence["original_base"] == ORIGINAL_BASE == "604bc0a22733e648ec05b268da1ffaae7db52a69"
    assert (
        evidence["source_revision"] == SOURCE_REVISION == "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"
    )
    assert (
        evidence["integration_merge"]
        == INTEGRATION_MERGE
        == "7a2f051b1f3847786318900444c88c2ba7a74a67"
    )
    assert evidence["fields_and_unions"] == schema_layout(car, log)
    assert evidence["generated_reader"]["layout_sha256"] == SCHEMA_LAYOUT_SHA256
    expected = [
        dict(
            id=c["id"],
            result_sha256=hashlib.sha256(
                json.dumps(
                    c["expected"], sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest(),
        )
        for c in CASES["cases"]
    ]
    assert evidence["neutral_contract_cases"] == expected and len(expected) == 69
    assert evidence["source_bodies_copied"] is False


@pytest.mark.parametrize("mutation", ["version", "layout", "backend"])
def test_unqualified_dependency_or_layout_is_typed_failure(monkeypatch, mutation):
    if mutation == "version":
        monkeypatch.setattr(capnp, "__version__", "unqualified")
    elif mutation == "layout":
        monkeypatch.setattr(
            "cyberpilot_autotune.integrations.carrot.availability.schema_layout", lambda *a: {}
        )
    else:

        def failed(*args):
            raise RuntimeError("raw backend detail")

        monkeypatch.setattr(
            "cyberpilot_autotune.integrations.carrot.availability.schema_layout", failed
        )
    with pytest.raises(CarrotSchemaIncompatible, match="^CARROT_SCHEMA_INCOMPATIBLE$"):
        require_schema()
