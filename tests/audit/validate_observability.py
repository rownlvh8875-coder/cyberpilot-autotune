"""Offline evidence validation; optional read-only raw Git blob verification.

CI needs neither the reference repository nor its Python dependencies. The
optional local command verifies metadata against both exact source trees.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from tests.audit.receipt_model import Policy, evaluate, from_record

ROOT = Path(__file__).resolve().parents[2]
BASE = "604bc0a22733e648ec05b268da1ffaae7db52a69"
HEAD = "4d89f044fc74138b0938f309ff8ea88d90faddcd"
RECEIPT_FIELDS = (
    "receiptVersion",
    "sourceCarControlMonoTime",
    "hostLateralActivityState",
    "safetyPermissionState",
    "safetyStateMonoTime",
    "controllerKind",
    "instantaneousControllerLimitState",
    "finalRequestedActuators",
    "controllerOutputActuators",
    "outputLimitState",
    "hostApplyMonoTime",
    "controllerOutputReturned",
    "safetyObservationMonoTime",
)


def _require(condition):
    if not condition:
        raise ValueError("inconsistent audit evidence")


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result)
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON is forbidden")


def load_evidence():
    def read(name):
        return json.loads(
            (ROOT / "docs/evidence" / name).read_text(encoding="utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )

    return read("carrot_observability_sources.json"), read("carrot_observability_cases.json")


def _metadata(data):
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "lines": len(data.splitlines()),
    }


def _schema_fields(data, name):
    """Inspect direct struct declarations, not nested structs/enums or comments."""
    text = re.sub(r"#[^\n]*", "", data.decode())
    start = re.search(r"struct\s+" + re.escape(name) + r"\s*\{", text).end()
    result, depth = {}, 1
    for line in text[start:].splitlines():
        match = re.search(r"(\w+)\s+@(\d+)\s*:\s*([^;]+);", line)
        if depth == 1 and match:
            field, ordinal, value_type = match.groups()
            result[field] = (int(ordinal), value_type.strip())
        depth += line.count("{") - line.count("}")
        if depth == 0:
            return result
    raise ValueError("unclosed schema struct")


def validate(sources, cases, reference_repository=None):
    _require(sources["schema_version"] == cases["schema_version"] == 1)
    _require(sources["original_base"] == BASE)
    _require(sources["observability_head"] == cases["reference_head"] == HEAD)
    _require(sources["target_base"] == "73769b7a173c0ee49f7d18335c06554c6e4291f0")
    _require(sources["repository"] == "https://github.com/rownlvh8875-coder/openpilot")
    _require(sources["provenance"]["source_bodies_copied"] is False)
    _require(
        sources["contract_decision"]["status"]
        == cases["contract_status"]
        == "CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED"
    )
    _require(sources["contract_decision"]["production_contract_module"] is False)
    _require(
        sources["contract_decision"]["mandatory_blockers"]
        == cases["blockers"]
        == ["BLOCKED_MEASUREMENT_PROVENANCE", "BLOCKED_MEB_DESIRED_RESPONSE_SEMANTICS"]
    )
    changed = sources["changed_files"]
    entries = changed + sources["supporting_files"]
    paths = [entry["path"] for entry in entries]
    _require(len(changed) == 21 and len(set(paths)) == len(paths))
    for entry in entries:
        path = Path(entry["path"])
        _require(not path.is_absolute() and ".." not in path.parts)
        for version in ("base", "head"):
            metadata = entry[version]
            if metadata is not None:
                _require(re.fullmatch("[0-9a-f]{64}", metadata["sha256"]) is not None)
                _require(metadata["bytes"] > 0 and metadata["lines"] > 0)
    for entry in changed:
        _require(bool(entry["responsibility"]) and entry["reviewed"] is True)
        _require(entry["copied_into_target"] is False)
    for item in sources["evidence_ranges"]:
        _require(item["path"] in paths)
        _require(1 <= item["start_line"] <= item["end_line"])
        _require(re.fullmatch("[0-9a-f]{64}", item["range_sha256"]) is not None)
        _require("/blob/" + HEAD + "/" + item["path"] in item["url"])
    ordinals = sources["schema_ordinals"]
    _require(ordinals["CarOutput.actuationReceipt"] == 1)
    _require(ordinals["CarControl.lateralControlObservation"] == 18)
    _require(ordinals["ActuationReceipt"] == dict(zip(RECEIPT_FIELDS, range(13), strict=True)))
    _require(sources["cohort"]["outer_valid_is_receipt_validity"] is False)
    _require(cases["scope"] == "SYNTHETIC_AUDIT_ONLY_NOT_AN_ADAPTER")
    policy = Policy(**cases["synthetic_policy"])
    identifiers = [case["id"] for case in cases["cases"]]
    _require(len(identifiers) >= 25 and len(identifiers) == len(set(identifiers)))
    for case in cases["cases"]:
        _require(evaluate(from_record(case["input"]), policy).as_record() == case["expected"])
        _require(case["expected"]["baseline_unchanged"] is True)
        _require(case["expected"]["source_valid"] is False)
        _require("MEASUREMENT_PROVENANCE_UNPROVEN_AT_PIN" in case["expected"]["reasons"])

    verified = legacy_fields = 0
    if reference_repository is not None:

        def blob(commit, path):
            result = subprocess.run(
                ["git", "show", commit + ":" + path],
                cwd=reference_repository,
                capture_output=True,
                check=False,
            )
            return result.stdout if result.returncode == 0 else None

        actual_names = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, HEAD], cwd=reference_repository, text=True
        ).splitlines()
        _require(sorted(actual_names) == sorted(entry["path"] for entry in changed))
        for entry in entries:
            for version, commit in (("base", BASE), ("head", HEAD)):
                data = blob(commit, entry["path"])
                _require((None if data is None else _metadata(data)) == entry[version])
                verified += data is not None
        for item in sources["evidence_ranges"]:
            lines = blob(HEAD, item["path"]).splitlines(keepends=True)
            data = b"".join(lines[item["start_line"] - 1 : item["end_line"]])
            _require(item["end_line"] <= len(lines))
            _require(hashlib.sha256(data).hexdigest() == item["range_sha256"])
        schema_path = "opendbc_repo/opendbc/car/car.capnp"
        fields = _schema_fields(blob(HEAD, schema_path), "ActuationReceipt")
        _require({name: value[0] for name, value in fields.items()} == ordinals["ActuationReceipt"])
        legacy = json.loads(
            blob(HEAD, "openpilot/selfdrive/car/tests/fixtures/actuation_schema_baseline.json")
        )
        for name, expected in legacy["fields"].items():
            path = (
                schema_path if name in {"CarControl", "CarOutput"} else "openpilot/cereal/log.capnp"
            )
            before = _schema_fields(blob(BASE, path), name)
            after = _schema_fields(blob(HEAD, path), name)
            for field, metadata in expected.items():
                _require(before[field] == after[field])
                _require(before[field][0] == metadata["ordinal"])
                legacy_fields += 1
    return {
        "changed_files": len(changed),
        "supporting_files": len(sources["supporting_files"]),
        "evidence_ranges": len(sources["evidence_ranges"]),
        "cases": len(cases["cases"]),
        "raw_blobs_verified": verified,
        "legacy_fields_verified": legacy_fields,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-repository", type=Path)
    args = parser.parse_args()
    sources, cases = load_evidence()
    result = validate(sources, cases, args.reference_repository)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
