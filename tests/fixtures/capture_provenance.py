"""Fictional provenance metadata,never captured H values or proposed H budgets."""

import importlib
import importlib.util
import json
from hashlib import sha256
from pathlib import Path


def registration():
    root = Path(__file__).resolve().parents[2]
    return json.loads(
        (
            root / "docs/evidence/audit_compatibility/capture-provenance-v1/registration.json"
        ).read_text()
    )


def api():
    assert importlib.util.find_spec("tests.audit_capture_provenance"), "capture API absent"
    return importlib.import_module("tests.audit_capture_provenance")


def digest(label):
    return sha256(label.encode("ascii")).hexdigest()


def document():
    data = registration()
    recipe = data["acceptance"]["baseline_recipe"]
    witnesses = []
    for row in data["catalog"]["rows"]:
        for role in row["required_witnesses"]:
            scope = role["expected_command_id"] or "BATCH"
            stage = role["allowed_stages"][0]
            witnesses.append(
                {
                    "target_path": row["target_path"],
                    "role": role["role"],
                    "stage": stage,
                    "context": {
                        "epoch": dict(recipe["epoch"]),
                        "command_id": role["expected_command_id"],
                        "attempt": None if scope == "BATCH" else 0,
                        "boundary_digest": digest("SYNTHETIC_BOUNDARY:" + scope),
                        "boundary_generation": 0,
                    },
                    "source_id": digest("SYNTHETIC_SOURCE:" + scope),
                    "event_id": digest(
                        "SYNTHETIC_EVENT:" + row["target_path"] + ":" + role["role"]
                    ),
                    "sequence": 0,
                    "event_time_ns": recipe["stage_time_ns"][stage],
                    "content_digest": "4" * 64,
                    "outcome": "PRESENT_CLAIM",
                }
            )
    renumber(witnesses)
    return {
        "epoch": dict(recipe["epoch"]),
        "capture_begin_ns": 0,
        "capture_end_ns": 100,
        "witnesses": witnesses,
    }


def renumber(witnesses):
    for source in {w["source_id"] for w in witnesses}:
        selected = [w for w in witnesses if w["source_id"] == source]
        for index, witness in enumerate(sorted(selected, key=lambda w: w["event_time_ns"])):
            witness["sequence"] = index


def find(doc, target="artifacts.executor_content.sha256", role="PREPARED_CONTENT"):
    return next(w for w in doc["witnesses"] if (w["target_path"], w["role"]) == (target, role))


def materialize(doc):
    module = api()

    def epoch(value):
        return None if value is None else module.CaptureEpoch(**value)

    def context(value):
        return (
            None
            if value is None
            else module.WitnessContext(**{**value, "epoch": epoch(value["epoch"])})
        )

    return module.CaptureWitnessBundle(
        epoch(doc["epoch"]),
        doc["capture_begin_ns"],
        doc["capture_end_ns"],
        tuple(
            module.CaptureWitness(**{**w, "context": context(w["context"])})
            for w in doc["witnesses"]
        ),
    )


def evaluate(doc):
    module = api()
    return module.assess_capture_bundle(materialize(doc))
