"""TEST_ONLY supplied claims,never execution witnesses or approved policy."""

import importlib
import importlib.util
import json
from pathlib import Path


def api(name="contracts"):
    assert importlib.util.find_spec("tests.audit_compatibility_history") is not None, "H1 absent"
    return importlib.import_module("tests.audit_compatibility_history." + name)


def complete():
    c = api()
    root = Path(__file__).resolve().parents[2]
    data = json.loads(
        (
            root / "docs/evidence/audit_compatibility/historical-design-v1/case_inventory.json"
        ).read_bytes()
    )
    subjects = (
        (
            "O",
            c.SourcePin(
                "5357d5d555d49b258affa237d83b8491b8a8c6ce",
                "18e63fc8e03077684cd14c1ed33e2c7a8ceb89a5",
            ),
        ),
        (
            "D",
            c.SourcePin(
                "75e00280a09323ad4a3fc82453383f220c92f6c6",
                "d0dd929f3bb46d1a33d8bb00f29e7638b48d9483",
            ),
        ),
    )
    policies, records = [], []
    for label, subject in subjects:
        nodes = (
            tuple(data["D"]["all_diagnostic_nodes"])
            if label == "D"
            else ("tests/TEST_ONLY.py::test_supplied",)
        )
        other = "observability" if label == "O" else "diagnostics.actual_binding"
        paths = (
            "src/cyberpilot_autotune/research/friction_model/TEST_ONLY.py",
            "src/cyberpilot_autotune/" + other.replace(".", "/") + "/TEST_ONLY.py",
        )
        groups = (("friction_model", (paths[0],)), (other, (paths[1],)))
        origins = (
            c.OriginPin(
                "tests.audit.validate_friction_model",
                "tests/audit/validate_friction_model.py",
                "aa27d15517e693b0288ed37893deae4515a7c1f88388bb29e871c9fe0e68d032"
                if label == "O"
                else "eaddb6091b5054613ec8e7f0eb15cae9b64aa3d1d8f4e1205c688b89f1947efe",
                None,
            ),
        )
        coverage = tuple(c.CoverageCounts(path, 100, 98, 100, 95) for path in paths)
        for suffix in ("PYTEST", "H6", "H7" if label == "O" else "COVERAGE"):
            identity = label + "-" + suffix
            entrypoint = (
                "pytest.main"
                if suffix == "PYTEST"
                else "tests.audit.validate_friction_model"
                if suffix == "H6"
                else "tests.audit.validate_friction_receipt"
                if suffix == "H7"
                else "tests.audit.validate_actual_binding_coverage"
            )
            argv = ("TEST_ONLY_SUPPLIED_ARGUMENTS", identity)
            expected = nodes if suffix == "PYTEST" else ()
            policies.append(
                c.HistoricalCommandPolicy(
                    identity,
                    label,
                    "PYTEST" if suffix == "PYTEST" else "AUDIT",
                    entrypoint,
                    argv,
                    expected,
                    origins,
                    groups,
                )
            )
            records.append(
                c.HistoricalCommandRecord(
                    identity,
                    label,
                    "1" * 32,
                    subject,
                    entrypoint,
                    argv,
                    0,
                    expected,
                    tuple(c.CaseOutcome(node, "PASSED", "PASSED", "PASSED") for node in expected),
                    origins,
                    coverage,
                    ("a" if label == "O" else "b") * 64,
                    label + "-PYTEST",
                    (),
                    (),
                )
            )
    policy = c.HistoricalReplayPolicy(
        "ENTRY_HISTORICAL_SOURCE_AUDIT_V1",
        subjects,
        tuple(policies),
        "2" * 40,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        "6" * 64,
    )
    record = c.HistoricalReplayRecord(
        "ENTRY_HISTORICAL_SOURCE_AUDIT_V1", "1" * 32, policy.content_digest, tuple(records), (), ()
    )
    return record, policy
