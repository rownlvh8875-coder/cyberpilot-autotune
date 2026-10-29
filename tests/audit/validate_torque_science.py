"""Exact-source H5 audit and explicit offline reproduction, never a runtime import."""

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import sys
import types
from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path, PurePosixPath

from cyberpilot_autotune.research.torque_identification.contracts import (
    POLICY_SHA256,
    PREREGISTRATION_COMMIT,
    RESEARCH,
    RUNTIME,
    canonical,
    digest,
    require,
    sha,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = "3ded3dec7011f24b7f1195f0c73bbed290891ff3"
PINS = {
    "runtime": RUNTIME,
    "integration": "7a2f051b1f3847786318900444c88c2ba7a74a67",
    "current": "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
    "research": RESEARCH,
}
POLICY_PATH = "docs/evidence/torque_identification_policy.json"
RESULT_PATH = "docs/evidence/torque_identification_results.json"
SOURCE_PATH = "docs/evidence/torque_identification_scientific_sources.json"


def source_specs():
    native = (
        (
            "torqued",
            "openpilot/selfdrive/locationd/torqued.py",
            (
                "slope2rot",
                "TorqueEstimator.estimate_params",
                "TorqueEstimator.handle_log",
                "TorqueEstimator.get_msg",
            ),
        ),
        (
            "callback",
            "opendbc_repo/opendbc/car/interfaces.py",
            ("CarInterfaceBase.torque_from_lateral_accel_linear",),
        ),
        (
            "friction",
            "opendbc_repo/opendbc/car/__init__.py",
            ("apply_center_deadzone", "get_friction"),
        ),
        (
            "other_friction",
            "opendbc_repo/opendbc/car/lateral.py",
            ("apply_center_deadzone", "get_friction"),
        ),
        (
            "consumer",
            "openpilot/selfdrive/controls/lib/latcontrol_torque.py",
            ("LatControlTorque.update",),
        ),
        ("buckets", "openpilot/selfdrive/locationd/helpers.py", ("PointBuckets",)),
        (
            "native_test",
            "openpilot/selfdrive/controls/tests/test_torqued_lat_accel_offset.py",
            ("generate_inputs", "test_estimated_offset"),
        ),
    )
    result = [
        (f"{pin}_{name}", "carrot", PINS[pin], path, symbols)
        for pin in ("runtime", "current")
        for name, path, symbols in native
    ]
    for name, path in (
        ("identification", "openpilot/tools/cyber_autotune/torque_identification.py"),
        ("aggregation", "openpilot/tools/cyber_autotune/torque_aggregation.py"),
        (
            "identification_tests",
            "openpilot/tools/cyber_autotune/tests/test_torque_identification.py",
        ),
        ("aggregation_tests", "openpilot/tools/cyber_autotune/tests/test_torque_aggregation.py"),
        ("identification_doc", "docs/cyberpilot/changes/cyber-autotune-torque-identification.md"),
        ("aggregation_doc", "docs/cyberpilot/changes/cyber-autotune-torque-aggregation.md"),
        ("contracts", "openpilot/tools/cyber_autotune/contracts.py"),
        ("evidence", "openpilot/tools/cyber_autotune/evidence.py"),
        ("cluster_tls", "openpilot/tools/cyber_autotune/torque_cluster_tls.py"),
        ("cluster_stability", "openpilot/tools/cyber_autotune/torque_cluster_stability.py"),
    ):
        result.append(("research_" + name, "research", RESEARCH, path, ()))
    return tuple(result)


def git_bytes(checkout, revision, path):
    return subprocess.check_output(["git", "-C", str(checkout), "show", f"{revision}:{path}"])


def _ranges(raw, symbols):
    lines = raw.splitlines(keepends=True)
    ranges = [("whole_file", 1, len(lines))]
    if symbols:
        nodes = {}
        for node in ast.parse(raw).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                nodes[node.name] = node
                if isinstance(node, ast.ClassDef):
                    nodes.update(
                        {
                            node.name + "." + child.name: child
                            for child in node.body
                            if isinstance(child, ast.FunctionDef)
                        }
                    )
        ranges += [(name, nodes[name].lineno, nodes[name].end_lineno) for name in symbols]
    return [
        {
            "name": name,
            "start": start,
            "end": end,
            "sha256": hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest(),
        }
        for name, start, end in ranges
    ]


@cache
def _preserved_hashes():
    paths = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            BASE,
            "src",
            "tests/fixtures/replay",
            "tests/unit/test_owner_protocol.py",
            "tests/unit/test_owner_protocol_failures.py",
            "tests/property/test_owner_protocol_properties.py",
            "tests/architecture/test_owner_protocol_boundary.py",
            "tests/audit/test_shared_torque_owner_contract.py",
            "docs/evidence/carrot_writer_ownership_sources.json",
            "docs/evidence/carrot_writer_ownership_audit.json",
            "docs/evidence/steering_parameter_knowledge_sources.json",
            "docs/evidence/shared_torque_owner_contract.json",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return {
        path: hashlib.sha256(git_bytes(ROOT, BASE, path).replace(b"\r\n", b"\n")).hexdigest()
        for path in paths
    }


def build_sources(checkouts):
    files = []
    for identity, repo, revision, path, symbols in source_specs():
        raw = git_bytes(checkouts[repo], revision, path)
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        files.append(
            {
                "id": identity,
                "repository": repo,
                "revision": revision,
                "path": path,
                "git_blob": blob,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "line_count": len(raw.splitlines()),
                "ranges": _ranges(raw, symbols),
            }
        )
    return {
        "schema_version": 1,
        "scope": "OFFLINE_SCIENTIFIC_DIAGNOSTIC_ONLY",
        "h5_base": BASE,
        "pins": PINS,
        "policy_freeze_commit": PREREGISTRATION_COMMIT,
        "policy_sha256": POLICY_SHA256,
        "files": files,
        "preserved_files": _preserved_hashes().copy(),
        "reference_execution": "ISOLATED_EXACT_SOURCE_MATH_FUNCTIONS_ONLY",
        "runtime_construction": False,
        "candidate_generation_allowed": False,
        "application_authorized": False,
        "runtime_accepted": False,
    }


def validate(sources, policy, checkouts=None):
    require(sources["schema_version"] == 1 and sources["h5_base"] == BASE, "SOURCE_SCHEMA")
    require(sources["pins"] == PINS, "SOURCE_PINS")
    require(
        sources["scope"] == "OFFLINE_SCIENTIFIC_DIAGNOSTIC_ONLY"
        and sources["reference_execution"] == "ISOLATED_EXACT_SOURCE_MATH_FUNCTIONS_ONLY",
        "SOURCE_SCOPE",
    )
    require(
        sources["policy_freeze_commit"] == PREREGISTRATION_COMMIT
        and sources["policy_sha256"] == digest(policy) == POLICY_SHA256,
        "POLICY_MUTATION",
    )
    require(
        all(
            sources[k] is False
            for k in (
                "runtime_construction",
                "candidate_generation_allowed",
                "application_authorized",
                "runtime_accepted",
            )
        ),
        "AUTHORITY",
    )
    expected = {
        identity: (repo, revision, path) for identity, repo, revision, path, _ in source_specs()
    }
    require(
        len(sources["files"]) == len(expected)
        and {f["id"] for f in sources["files"]} == set(expected),
        "SOURCE_FILE_SET",
    )
    range_count = 0
    for item in sources["files"]:
        require(
            (item["repository"], item["revision"], item["path"]) == expected[item["id"]],
            "SOURCE_BINDING",
        )
        path = PurePosixPath(item["path"])
        require(not path.is_absolute() and ".." not in path.parts, "SOURCE_PATH")
        require(sha(item["git_blob"], 40) and sha(item["sha256"]), "SOURCE_HASH")
        require(
            type(item["line_count"]) is int and item["line_count"] > 0 and item["ranges"],
            "SOURCE_RANGES",
        )
        for span in item["ranges"]:
            require(
                type(span["start"]) is int
                and type(span["end"]) is int
                and 1 <= span["start"] <= span["end"] <= item["line_count"]
                and sha(span["sha256"]),
                "SOURCE_RANGE",
            )
            range_count += 1
        if checkouts is not None:
            raw = git_bytes(checkouts[item["repository"]], item["revision"], item["path"])
            require(
                hashlib.sha256(raw).hexdigest() == item["sha256"]
                and hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
                == item["git_blob"],
                "SOURCE_BYTES",
            )
            lines = raw.splitlines(keepends=True)
            require(len(lines) == item["line_count"], "SOURCE_LINES")
            for span in item["ranges"]:
                require(
                    hashlib.sha256(b"".join(lines[span["start"] - 1 : span["end"]])).hexdigest()
                    == span["sha256"],
                    "SOURCE_RANGE_BYTES",
                )
    require(sources["preserved_files"] == _preserved_hashes(), "PRESERVATION_SET")
    for path, expected_hash in sources["preserved_files"].items():
        require(
            sha(expected_hash)
            and hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            == expected_hash,
            "PRESERVED_FILE_CHANGED",
        )
    return {
        "files": len(expected),
        "ranges": range_count,
        "source_bytes_verified": checkouts is not None,
        "application_authorized": False,
    }


def _namespace(name, nodes):
    import numpy as np

    module = types.ModuleType(name)
    module.__dict__.update(
        dict(
            np=np,
            math=math,
            re=re,
            json=json,
            hashlib=hashlib,
            dataclass=dataclass,
            asdict=asdict,
            field=field,
        )
    )
    sys.modules[name] = module
    future = ast.parse("from __future__ import annotations").body
    tree = ast.fix_missing_locations(ast.Module(body=future + nodes, type_ignores=[]))
    exec(compile(tree, f"<{name}:verified-math-only>", "exec"), module.__dict__)
    return module.__dict__


def numerical_parity(checkouts):
    import numpy as np

    from cyberpilot_autotune.research.torque_identification.estimator import fit_raw
    from cyberpilot_autotune.research.torque_identification.experiments import catalog
    from cyberpilot_autotune.research.torque_identification.synthetic import generate

    native = ast.parse(
        git_bytes(checkouts["carrot"], RUNTIME, "openpilot/selfdrive/locationd/torqued.py")
    )
    slope = next(n for n in native.body if isinstance(n, ast.FunctionDef) and n.name == "slope2rot")
    owner = next(
        n for n in native.body if isinstance(n, ast.ClassDef) and n.name == "TorqueEstimator"
    )
    estimate = next(
        n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == "estimate_params"
    )
    shell = ast.ClassDef(
        name="TorqueEstimator", bases=[], keywords=[], body=[estimate], decorator_list=[]
    )
    multiplier = ast.parse("FRICTION_FACTOR = 1.5").body[0]
    ns = _namespace("_h5_native_math", [multiplier, slope, shell])
    # The source multiplier is independently bound to its exact assignment.
    assignment = next(
        n
        for n in native.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "FRICTION_FACTOR" for t in n.targets)
    )
    require(ast.literal_eval(assignment.value) == 1.5, "NATIVE_MULTIPLIER_CHANGED")
    source = ast.parse(
        git_bytes(
            checkouts["research"],
            RESEARCH,
            "openpilot/tools/cyber_autotune/torque_identification.py",
        )
    )
    nodes = [n for n in source.body if isinstance(n, (ast.Assign, ast.FunctionDef, ast.ClassDef))]
    contracts = ast.parse(
        git_bytes(checkouts["research"], RESEARCH, "openpilot/tools/cyber_autotune/contracts.py")
    )
    helper = [
        n
        for n in contracts.body
        if isinstance(n, ast.FunctionDef) and n.name in {"finite_number", "is_sha256"}
    ]
    evidence = ast.parse(
        git_bytes(checkouts["research"], RESEARCH, "openpilot/tools/cyber_autotune/evidence.py")
    )
    keys = next(
        n
        for n in evidence.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PROVENANCE_KEYS" for t in n.targets)
    )
    cyber = _namespace("_h5_cyber_math", [keys, *helper, *nodes])
    errors = []
    for case in (catalog()[0], catalog()[6]):
        points = generate(case).points
        rows = np.array([[p.normalized_command, 1.0, p.lateral_accel_mps2] for p in points])
        obj = object.__new__(ns["TorqueEstimator"])
        obj.filtered_points = types.SimpleNamespace(get_points=lambda count, values=rows: values)
        obj.fit_points = len(points)
        native_values = tuple(float(x) for x in obj.estimate_params())
        request = cyber["TorqueFitInput"](
            tuple(cyber["TorquePoint"](**asdict(p)) for p in points),
            "development_fit",
            tuple((key, digest(key)) for key in sorted(cyber["PROVENANCE_KEYS"])),
            cyber["SIGNAL_CONTRACT"],
        )
        frozen = cyber["identify_torque"](request)
        require(
            frozen.status == "NUMERICAL_DIAGNOSTIC" and frozen.estimate is not None,
            "CYBER_PARITY_INPUT",
        )
        require(
            not any(
                (
                    frozen.parameter_identification_qualified,
                    frozen.candidate_generation_allowed,
                    frozen.runtime_accepted,
                )
            ),
            "REFERENCE_AUTHORITY",
        )
        ours = fit_raw(points)
        our_values = (
            ours.linear_mode_tls_lat_accel_slope,
            ours.lat_accel_offset_mps2,
            ours.native_residual_spread_coefficient,
        )
        cyber_values = (
            frozen.estimate.lat_accel_factor,
            frozen.estimate.lat_accel_offset_mps2,
            frozen.estimate.native_residual_spread_coefficient,
        )
        require(
            np.allclose(native_values, cyber_values, atol=1e-13, rtol=1e-13)
            and np.allclose(native_values, our_values, atol=1e-13, rtol=1e-13),
            "NATIVE_NUMERICAL_PARITY_FAILED",
        )
        errors.append(max(abs(a - b) for a, b in zip(native_values, our_values, strict=True)))
    helper_raw = git_bytes(checkouts["carrot"], RUNTIME, "opendbc_repo/opendbc/car/__init__.py")
    functions = [
        n
        for n in ast.parse(helper_raw).body
        if isinstance(n, ast.FunctionDef) and n.name in {"get_friction", "apply_center_deadzone"}
    ]
    friction = _namespace("_h5_friction_math", functions)["get_friction"]
    from cyberpilot_autotune.research.torque_identification.analytic import friction_shape

    for error in (-0.5, -0.3, -0.1, -0.099, 0.0, 0.099, 0.1, 0.3, 0.5):
        tuning = types.SimpleNamespace(friction=0.2)
        require(
            math.isclose(
                friction(error, 0.1, 0.3, tuning, True),
                0.2 * friction_shape(error, 0.1, 0.3),
                abs_tol=1e-15,
            ),
            "FRICTION_HELPER_PARITY",
        )
        require(friction(error, 0.1, 0.3, tuning, False) == 0.0, "FRICTION_DISABLED")
    return {
        "status": "NATIVE_NUMERICAL_PARITY_PASS",
        "cases": 2,
        "maximum_absolute_error": max(errors),
        "actual_imported_friction_helper_cases": 18,
        "native_bucket_sampling_reproduced": False,
        "scientific_identification_pass": False,
    }


def verify_history(require_results=True):
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, "HEAD"], cwd=ROOT, check=True
    )
    frozen = json.loads(git_bytes(ROOT, PREREGISTRATION_COMMIT, POLICY_PATH))
    require(digest(frozen) == POLICY_SHA256, "POLICY_HISTORY")
    current = json.loads((ROOT / POLICY_PATH).read_text())
    require(digest(current) == POLICY_SHA256, "POSTHOC_POLICY_MUTATION")
    absent = (
        subprocess.run(
            ["git", "cat-file", "-e", f"{PREREGISTRATION_COMMIT}:{RESULT_PATH}"],
            cwd=ROOT,
            capture_output=True,
        ).returncode
        != 0
    )
    require(absent, "RESULTS_PRESENT_AT_FREEZE")
    introduction = subprocess.check_output(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", RESULT_PATH], cwd=ROOT, text=True
    ).splitlines()
    if require_results:
        require(bool(introduction), "RESULTS_NOT_COMMITTED")
    if introduction:
        require(introduction[-1] != PREREGISTRATION_COMMIT, "POLICY_AND_RESULTS_SAME_COMMIT")
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, introduction[-1]],
            cwd=ROOT,
            check=True,
        )
    return {
        "freeze_ancestor": True,
        "results_absent_at_freeze": True,
        "policy_freeze_commit": PREREGISTRATION_COMMIT,
        "results_introduction_commit": introduction[-1] if introduction else None,
    }


def validate_results(results, sources, policy):
    require(results["scientific_sources_digest"] == digest(sources), "RESULT_SOURCE_BINDING")
    report = results["report"]
    require(
        report["statistical_policy_digest"] == digest(policy) == POLICY_SHA256
        and report["preregistration_commit"] == PREREGISTRATION_COMMIT,
        "RESULT_POLICY_BINDING",
    )
    require(
        all(
            report[key] is False
            for key in (
                "candidate_generation_allowed",
                "application_authorized",
                "runtime_accepted",
                "parameter_identification_qualified",
            )
        ),
        "RESULT_AUTHORITY",
    )
    require(
        results["development_fit_executed"] is False
        and all(
            report[key] is None
            for key in (
                "cluster_count",
                "epoch_count",
                "point_count",
                "cluster_statistics",
                "development_evidence_digest",
            )
        ),
        "UNAVAILABLE_DATA_PROMOTED",
    )
    require(
        report["status"].startswith("TORQUE_IDENTIFICATION_BLOCKED_")
        and report["friction_verdict"] == "FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION"
        and report["joint_identifiability"] == "NONIDENTIFIABLE",
        "VERDICT_OVERCLAIM",
    )
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    expected = json.loads(canonical(asdict(qualify(None, canonical(policy)))))
    _same_result(report, expected)
    require(
        results["historical_claims_recomputed"] is False
        and results["native_numerical_parity"]["status"] == "NATIVE_NUMERICAL_PARITY_PASS"
        and results["native_numerical_parity"]["scientific_identification_pass"] is False,
        "RESULT_SCOPE",
    )
    return {
        "development_fit_executed": False,
        "synthetic_cases": len(report["synthetic_recovery_summary"]),
        "application_authorized": False,
    }


def _same_result(actual, expected):
    if type(expected) is float:
        require(
            type(actual) in (float, int)
            and math.isfinite(actual)
            and math.isclose(actual, expected, abs_tol=2e-12, rel_tol=0.0),
            "RESULT_NUMERICS",
        )
    elif type(expected) is dict:
        require(type(actual) is dict and set(actual) == set(expected), "RESULT_SHAPE")
        for key, value in expected.items():
            _same_result(actual[key], value)
    elif type(expected) is list:
        require(type(actual) is list and len(actual) == len(expected), "RESULT_SHAPE")
        for a, e in zip(actual, expected, strict=True):
            _same_result(a, e)
    else:
        require(type(actual) is type(expected) and actual == expected, "RESULT_BINDING")


def check_coverage(payload):
    totals = payload["totals"]
    require(totals["num_statements"] > 0 and totals["num_branches"] > 0, "EMPTY_RESEARCH_COVERAGE")
    statements = 100 * totals["covered_lines"] / totals["num_statements"]
    branches = 100 * totals["covered_branches"] / totals["num_branches"]
    require(statements >= 98.0 and branches >= 95.0, "RESEARCH_COVERAGE_BELOW_GATE")
    return {"statements_percent": statements, "branches_percent": branches}


def build_results(sources, policy, checkouts):
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    return {
        "schema_version": 1,
        "scientific_sources_digest": digest(sources),
        "development_fit_executed": False,
        "historical_claims_recomputed": False,
        "historical_claims_source_id": "research_aggregation_doc",
        "historically_reported": {
            "epochs": 19,
            "nonempty_epochs": 15,
            "points": 31595,
            "bucket_counts": [104, 608, 2709, 11591, 10588, 4443, 1194, 358],
            "point_manifest_sha256": (
                "27ed097453beeb075b133cc492b8462d5b5c2de7bf36e2f1d94e145f95b846d8"
            ),
        },
        "source_verification": validate(sources, policy, checkouts),
        "native_numerical_parity": numerical_parity(checkouts),
        "report": asdict(qualify(None, canonical(policy))),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrot-checkout", type=Path)
    parser.add_argument("--research-checkout", type=Path)
    parser.add_argument("--emit-sources", action="store_true")
    parser.add_argument("--emit-results", action="store_true")
    parser.add_argument("--verify-history", action="store_true")
    parser.add_argument("--coverage-json", type=Path)
    args = parser.parse_args()
    if args.coverage_json is not None:
        print(canonical(check_coverage(json.loads(args.coverage_json.read_text()))))
        return
    checkouts = (
        {"carrot": args.carrot_checkout, "research": args.research_checkout}
        if args.carrot_checkout is not None and args.research_checkout is not None
        else None
    )
    policy = json.loads((ROOT / POLICY_PATH).read_text())
    if args.emit_sources:
        require(checkouts is not None, "REFERENCE_CHECKOUTS_REQUIRED")
        print(json.dumps(build_sources(checkouts), indent=2))
        return
    sources = json.loads((ROOT / SOURCE_PATH).read_text())
    if args.emit_results:
        require(checkouts is not None, "REFERENCE_CHECKOUTS_REQUIRED")
        print(json.dumps(build_results(sources, policy, checkouts), indent=2, allow_nan=False))
        return
    output = validate(sources, policy, checkouts)
    output.update(validate_results(json.loads((ROOT / RESULT_PATH).read_text()), sources, policy))
    if checkouts is not None:
        output["native_numerical_parity"] = numerical_parity(checkouts)
    if args.verify_history:
        output["history"] = verify_history()
    print(canonical(output))


if __name__ == "__main__":
    main()
