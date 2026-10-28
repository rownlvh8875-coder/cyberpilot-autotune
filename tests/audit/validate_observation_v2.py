"""Offline evidence validator; optional reference inspection uses read-only Git."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from cyberpilot_autotune.adapters.carrot_receipt_contract import evaluate
from tests.audit.test_observation_v2_cases import from_case, projection
from tests.audit.validate_observability import (
    _constant,
    _metadata,
    _pairs,
    _require,
    _schema_fields,
)
from tests.fixtures.carrot_v2 import BASELINE

ROOT = Path(__file__).resolve().parents[2]
BASE = "604bc0a22733e648ec05b268da1ffaae7db52a69"
HEAD = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"


def load_evidence():
    def load(suffix):
        path = ROOT / "docs/evidence" / f"carrot_observation_v2_{suffix}.json"
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
        )

    return load("sources"), load("cases")


def validate(sources, cases, reference_repository=None):
    _require(sources["schema_version"] == cases["schema_version"] == 1)
    _require(sources["original_base"] == BASE)
    _require(sources["observation_v2_head"] == cases["reference_head"] == HEAD)
    _require(sources["target_base"] == "03c3f2f36cbe47a9afec97ce7b9d411d3aa81ccb")
    _require(sources["repository"] == "https://github.com/rownlvh8875-coder/openpilot")
    _require(sources["provenance"]["source_bodies_copied"] is False)
    _require(sources["decision"] == "CONTRACT_READY_FOR_PHASE_8B")
    _require(set(sources["mandatory_gates"].values()) == {"PROVEN"})
    changed, support = sources["changed_files"], sources["supporting_files"]
    _require(len(changed) == 26)
    by_path = {item["path"]: item for item in changed + support}
    _require(len(by_path) == len(changed + support))
    for path, item in by_path.items():
        _require(not Path(path).is_absolute() and ".." not in Path(path).parts)
        for version in ("base", "head"):
            metadata = item[version]
            if metadata is not None:
                _require(re.fullmatch("[0-9a-f]{64}", metadata["sha256"]) is not None)
                _require(metadata["bytes"] > 0 and metadata["lines"] > 0)
    for item in changed:
        _require(item["reviewed"] is True and item["copied_into_target"] is False)
        _require(bool(item["responsibility"]) and bool(item["inspected_symbols"]))
        for symbol in item["inspected_symbols"]:
            _require(1 <= symbol["start_line"] <= symbol["end_line"] <= item["head"]["lines"])
    for item in sources["evidence_ranges"]:
        _require(item["path"] in by_path)
        _require(
            1 <= item["start_line"] <= item["end_line"] <= by_path[item["path"]]["head"]["lines"]
        )
        _require(re.fullmatch("[0-9a-f]{64}", item["range_sha256"]) is not None)
        _require(
            f"/blob/{HEAD}/{item['path']}#L{item['start_line']}-L{item['end_line']}" in item["url"]
        )
    _require(len(sources["snapshot_contracts"]) == 13)
    for item in sources["snapshot_contracts"]:
        _require(item["path"] in by_path and all(item.values()))
    identifiers = [item["id"] for item in cases["cases"]]
    _require(len(identifiers) >= 40 and len(set(identifiers)) == len(identifiers))
    for case in cases["cases"]:
        attempt, policy = from_case(case)
        before = dict(attempt.baseline_parameters)
        decision = evaluate(attempt, policy, BASELINE)
        _require(
            projection(decision, dict(attempt.baseline_parameters) == before) == case["expected"]
        )

    verified = legacy = 0
    if reference_repository is not None:

        def blob(commit, path):
            result = subprocess.run(
                ["git", "show", f"{commit}:{path}"],
                cwd=reference_repository,
                capture_output=True,
                check=False,
            )
            return result.stdout if result.returncode == 0 else None

        actual_paths = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, HEAD],
            cwd=reference_repository,
            text=True,
        ).splitlines()
        _require(sorted(actual_paths) == sorted(item["path"] for item in changed))
        for path, item in by_path.items():
            for version, commit in (("base", BASE), ("head", HEAD)):
                data = blob(commit, path)
                _require((None if data is None else _metadata(data)) == item[version])
                verified += data is not None
        for item in sources["evidence_ranges"]:
            lines = blob(HEAD, item["path"]).splitlines(keepends=True)
            data = b"".join(lines[item["start_line"] - 1 : item["end_line"]])
            _require(hashlib.sha256(data).hexdigest() == item["range_sha256"])
        car_schema = "opendbc_repo/opendbc/car/car.capnp"
        for name in ("LateralControlObservation", "LateralMeasurementObservation"):
            actual = _schema_fields(blob(HEAD, car_schema), name)
            _require(
                {key: value[0] for key, value in actual.items()} == sources["schema_ordinals"][name]
            )
        baseline = json.loads(
            blob(HEAD, "openpilot/selfdrive/car/tests/fixtures/actuation_schema_baseline.json")
        )
        for name, fields in baseline["fields"].items():
            path = (
                car_schema if name in ("CarControl", "CarOutput") else "openpilot/cereal/log.capnp"
            )
            before, after = (
                _schema_fields(blob(BASE, path), name),
                _schema_fields(blob(HEAD, path), name),
            )
            for field in fields:
                _require(before[field] == after[field])
                legacy += 1
    return dict(
        changed_files=len(changed),
        supporting_files=len(support),
        evidence_ranges=len(sources["evidence_ranges"]),
        cases=len(identifiers),
        raw_blobs_verified=verified,
        legacy_fields_verified=legacy,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-repository", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(*load_evidence(), args.reference_repository), sort_keys=True))


if __name__ == "__main__":
    main()
