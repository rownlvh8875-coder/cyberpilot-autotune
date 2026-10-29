"""H6 exact-source/history/result audit. Explicit read-only references only."""

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

from cyberpilot_autotune.research.friction_model.candidates import normalize_state
from cyberpilot_autotune.research.friction_model.contracts import (
    BASE,
    CURRENT,
    POLICY_SHA256,
    PREREGISTRATION,
    RUNTIME,
    digest,
    require,
)
from cyberpilot_autotune.research.friction_model.experiments import run_experiments
from cyberpilot_autotune.research.friction_model.geometry import vehicle_diagnostic

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "docs/evidence/friction_model_sources.json"
POLICY_PATH = "docs/evidence/friction_model_policy.json"
RESULT_PATH = "docs/evidence/friction_model_synthetic_results.json"
GEOMETRY_PATH = "docs/evidence/torque_geometry_context.json"


def source_specs():
    common = (
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
        ("other_friction", "opendbc_repo/opendbc/car/lateral.py", ("get_friction",)),
        (
            "controller",
            "openpilot/selfdrive/controls/lib/latcontrol_torque.py",
            ("LatControlTorque.update",),
        ),
        ("controlsd", "openpilot/selfdrive/controls/controlsd.py", ()),
        ("paramsd", "openpilot/selfdrive/locationd/paramsd.py", ()),
        (
            "vehicle_model",
            "opendbc_repo/opendbc/car/vehicle_model.py",
            ("VehicleModel", "create_dyn_state_matrices", "calc_slip_factor"),
        ),
        ("gm", "opendbc_repo/opendbc/car/gm/interface.py", ()),
        ("pid", "openpilot/common/pid.py", ("PIDController.update",)),
        (
            "steer_ratio",
            "openpilot/selfdrive/controls/lib/steer_ratio.py",
            ("resolve_vehicle_model_steer_ratio",),
        ),
        ("schema", "openpilot/cereal/log.capnp", ()),
        ("params_keys", "openpilot/common/params_keys.h", ()),
    )
    result = [
        (f"{profile}_{name}", revision, path, symbols)
        for profile, revision in (("runtime", RUNTIME), ("current", CURRENT))
        for name, path, symbols in common
    ]
    for name, path, symbols in (
        (
            "geometry",
            "opendbc_repo/opendbc/car/lateral_geometry.py",
            ("requested_center_to_front_ratio", "LateralGeometry"),
        ),
        ("geometry_migration", "openpilot/common/lateral_geometry_params.py", ()),
        ("geometry_test", "openpilot/selfdrive/controls/tests/test_live_lateral_geometry.py", ()),
        ("vehicle_test", "opendbc_repo/opendbc/car/tests/test_vehicle_model.py", ()),
    ):
        result.append(("current_" + name, CURRENT, path, symbols))
    for name, path in (
        ("observation_v2", "src/cyberpilot_autotune/adapters/carrot_receipt_contract.py"),
        ("snapshot", "src/cyberpilot_autotune/contracts/observation.py"),
    ):
        result.append((name, BASE, path, ()))
    return tuple(result)


def git_bytes(checkout, revision, path):
    return subprocess.check_output(["git", "-C", str(checkout), "show", f"{revision}:{path}"])


def spans(raw, symbols):
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
        ranges.extend((name, nodes[name].lineno, nodes[name].end_lineno) for name in symbols)
    return [
        {
            "name": name,
            "start": start,
            "end": end,
            "sha256": hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest(),
        }
        for name, start, end in ranges
    ]


def build_sources(reference):
    files = []
    for identity, revision, path, symbols in source_specs():
        checkout = ROOT if revision == BASE else reference
        raw = git_bytes(checkout, revision, path)
        files.append(
            {
                "id": identity,
                "revision": revision,
                "path": path,
                "git_blob": hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "line_count": len(raw.splitlines()),
                "ranges": spans(raw, symbols),
            }
        )
    static_files = [
        f
        for f in files
        if f["revision"] == RUNTIME
        and f["id"]
        in {
            "runtime_controlsd",
            "runtime_paramsd",
            "runtime_vehicle_model",
            "runtime_schema",
            "runtime_params_keys",
        }
    ]
    absent = all(
        b"CenterToFrontRatio" not in git_bytes(reference, RUNTIME, f["path"])
        and b"centerToFrontRatio" not in git_bytes(reference, RUNTIME, f["path"])
        and b"update_geometry" not in git_bytes(reference, RUNTIME, f["path"])
        for f in static_files
    )
    dynamic_claims = {
        "current_params_keys": b"CenterToFrontRatio",
        "current_schema": b"centerToFrontRatio",
        "current_controlsd": b"self.VM.update_geometry",
        "current_paramsd": b"liveParameters.centerToFrontRatio",
        "current_geometry": b"class LateralGeometry",
    }
    dynamic = all(
        token
        in git_bytes(reference, CURRENT, next(f["path"] for f in files if f["id"] == identity))
        for identity, token in dynamic_claims.items()
    )
    return {
        "schema": "friction-model-source-v1",
        "base": BASE,
        "policy_freeze_commit": PREREGISTRATION,
        "policy_sha256": POLICY_SHA256,
        "files": files,
        "static_runtime_dynamic_geometry_absent": absent,
        "current_dynamic_geometry_path_present": dynamic,
        "absence_scope": [f["id"] for f in static_files],
        "current_branch_review": {
            "branch": "ajouatom/openpilot:carrot-wip",
            "observed_start_head": CURRENT,
            "drift": "UNCHANGED_AT_H6_START",
        },
        "runtime_imported": False,
        "candidate_generation_allowed": False,
        "runtime_accepted": False,
        "owner_proposal_allowed": False,
        "application_authorized": False,
    }


def validate_sources(source, reference=None):
    require(
        source["schema"] == "friction-model-source-v1" and source["base"] == BASE, "SOURCE_SCHEMA"
    )
    require(
        source["policy_freeze_commit"] == PREREGISTRATION
        and source["policy_sha256"] == POLICY_SHA256,
        "SOURCE_FREEZE",
    )
    require(
        source["runtime_imported"] is False and source["application_authorized"] is False,
        "SOURCE_AUTHORITY",
    )
    require(source["static_runtime_dynamic_geometry_absent"] is True, "STATIC_RUNTIME_GEOMETRY")
    require(source["current_dynamic_geometry_path_present"] is True, "CURRENT_DYNAMIC_GEOMETRY")
    require(
        all(
            source[k] is False
            for k in ("candidate_generation_allowed", "runtime_accepted", "owner_proposal_allowed")
        ),
        "SOURCE_AUTHORITY",
    )
    expected = {identity: (revision, path) for identity, revision, path, _ in source_specs()}
    require(
        len(source["files"]) == len(expected)
        and {f["id"] for f in source["files"]} == set(expected),
        "SOURCE_FILE_SET",
    )
    for item in source["files"]:
        require((item["revision"], item["path"]) == expected[item["id"]], "SOURCE_BINDING")
        for key, size in (("git_blob", 40), ("sha256", 64)):
            require(
                type(item[key]) is str
                and re.fullmatch(f"[0-9a-f]{{{size}}}", item[key]) is not None,
                "SOURCE_HASH",
            )
        require(item["ranges"] and type(item["line_count"]) is int, "SOURCE_RANGE")
        for span in item["ranges"]:
            require(
                1 <= span["start"] <= span["end"] <= item["line_count"]
                and re.fullmatch("[0-9a-f]{64}", span["sha256"]) is not None,
                "SOURCE_RANGE",
            )
    require(
        digest(json.loads((ROOT / POLICY_PATH).read_text())) == POLICY_SHA256, "POLICY_MUTATION"
    )
    if reference is not None:
        require(source == build_sources(reference), "EXACT_SOURCE_MISMATCH")
        verify_source_equations(reference)


def _math_namespace(raw, namespace):
    # No imports/top-level effects: only exact function/class declarations compiled in an audit.
    nodes = [
        node for node in ast.parse(raw).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    ]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pinned-math-only>", "exec"), namespace)


def verify_source_equations(reference):
    import numpy as np

    ns = {
        "np": np,
        "structs": SimpleNamespace(CarParams=SimpleNamespace(LateralTorqueTuning=object)),
    }
    raw = git_bytes(reference, CURRENT, "opendbc_repo/opendbc/car/__init__.py")
    nodes = [
        node
        for node in ast.parse(raw).body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"get_friction", "apply_center_deadzone"}
    ]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<friction-math-only>", "exec"), ns)
    for enabled in (False, True):
        for error in (-0.6, -0.06, -0.01, 0, 0.01, 0.06, 0.15, 0.6):
            actual = ns["get_friction"](error, 0.06, 0.3, SimpleNamespace(friction=1.0), enabled)
            require(
                math.isclose(actual, normalize_state(error, 0.06, 0.3, enabled), abs_tol=1e-15),
                "Q_SOURCE_EQUATION",
            )
    vm_ns = {
        "np": np,
        "math": math,
        "solve": np.linalg.solve,
        "CarParams": object,
        "ACCELERATION_DUE_TO_GRAVITY": 9.81,
        "GEOMETRY_RATE": 0.1,
    }
    _math_namespace(
        git_bytes(reference, CURRENT, "opendbc_repo/opendbc/car/lateral_geometry.py"), vm_ns
    )
    _math_namespace(
        git_bytes(reference, CURRENT, "opendbc_repo/opendbc/car/vehicle_model.py"), vm_ns
    )
    cp = SimpleNamespace(
        mass=1234.0,
        rotationalInertia=2300.0,
        wheelbase=2.73,
        centerToFront=1.1739,
        steerRatio=14.7,
        steerRatioRear=0.0,
        tireStiffnessFront=70000.0,
        tireStiffnessRear=90000.0,
    )
    for ratio in (0.43, 0.44, 0.51):
        vm = vm_ns["VehicleModel"](cp)
        vm.update_params(0.95, 14.7)
        vm.update_geometry(ratio)
        toy = vehicle_diagnostic(ratio)
        require(
            math.isclose(vm.calc_curvature(0.035, 18.0, 0.02), toy.curvature, abs_tol=1e-14),
            "VM_CURVATURE_SOURCE",
        )
        a, b = vm_ns["create_dyn_state_matrices"](18.0, vm)
        state = np.zeros(2)
        series = []
        for _ in range(200):
            derivative = a @ state + b @ np.array([0.035, 0.02])
            series.append(float(derivative[0] + 18 * state[1]))
            state += 0.001 * derivative
        require(
            np.allclose(series, toy.acceleration_series, rtol=0, atol=1e-12), "VM_TRANSIENT_SOURCE"
        )


def history_order(checkout, base, head):
    return subprocess.check_output(
        ["git", "rev-list", "--topo-order", "--reverse", f"{base}..{head}"],
        cwd=checkout,
        text=True,
    ).splitlines()


def historical_inventory_equivalent(path, expected, actual):
    """H7 only: exact new-namespace inventory entries, never a general hash exemption."""
    if expected == actual:
        return True
    additions = {
        "tests/architecture/test_knowledge_boundary.py": (
            b'                "src/cyberpilot_autotune/research/",\n',
            b'                "src/cyberpilot_autotune/research/",\n'
            b'                "src/cyberpilot_autotune/observability/",\n',
        ),
        "tests/audit/test_carrot_writer_ownership.py": (
            b'            ("src/cyberpilot_autotune/owner_protocol/", '
            b'"src/cyberpilot_autotune/research/")\n',
            b"            (\n"
            b'                "src/cyberpilot_autotune/owner_protocol/",\n'
            b'                "src/cyberpilot_autotune/research/",\n'
            b'                "src/cyberpilot_autotune/observability/",\n'
            b"            )\n",
        ),
        "tests/audit/test_hoya_c3_atune_evidence.py": (
            b'        and "research" not in p.parts\n',
            b'        and "research" not in p.parts\n        and "observability" not in p.parts\n',
        ),
    }
    if path not in additions:
        return False
    old, new = additions[path]
    return expected.count(old) == 1 and actual == expected.replace(old, new, 1)


def verify_history():
    commits = history_order(ROOT, BASE, "HEAD")
    require(commits and commits[0] == PREREGISTRATION, "PREREGISTRATION_NOT_FIRST")
    changed = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", PREREGISTRATION],
        cwd=ROOT,
        text=True,
    ).splitlines()
    require(
        set(changed)
        == {POLICY_PATH, "docs/friction_model_estimand.md", "docs/friction_model_candidates.md"},
        "PRECOMPARISON_FREEZE",
    )
    frozen = json.loads(git_bytes(ROOT, PREREGISTRATION, POLICY_PATH))
    require(
        digest(frozen) == POLICY_SHA256 == digest(json.loads((ROOT / POLICY_PATH).read_text())),
        "POLICY_HISTORY",
    )
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
    ).splitlines()
    for path in paths:
        if path == ".github/workflows/ci.yml":
            continue
        require(
            historical_inventory_equivalent(
                path,
                git_bytes(ROOT, BASE, path).replace(b"\r\n", b"\n"),
                (ROOT / path).read_bytes().replace(b"\r\n", b"\n"),
            ),
            "PRE_H6_FILE_CHANGED:" + path,
        )
    return len(paths) - 1


def same(actual, expected):
    if type(expected) is float:
        return type(actual) in (int, float) and math.isclose(
            actual, expected, rel_tol=1e-10, abs_tol=1e-12
        )
    if type(expected) is dict:
        return (
            type(actual) is dict
            and actual.keys() == expected.keys()
            and all(same(actual[k], v) for k, v in expected.items())
        )
    if type(expected) is list:
        return (
            type(actual) is list
            and len(actual) == len(expected)
            and all(same(a, e) for a, e in zip(actual, expected, strict=True))
        )
    return type(actual) is type(expected) and actual == expected


def validate_results(result):
    expected = run_experiments((ROOT / POLICY_PATH).read_text())
    require(same(result, expected), "RESULT_REPRODUCTION")
    geometry = json.loads((ROOT / GEOMETRY_PATH).read_text())
    require(same(geometry["diagnostic"], expected["geometry"]), "GEOMETRY_RESULT")


def check_coverage(report):
    summaries = [
        v["summary"]
        for path, v in report["files"].items()
        if "/friction_model/" in path.replace("\\", "/")
    ]
    statements = sum(s["num_statements"] for s in summaries)
    covered = sum(s["covered_lines"] for s in summaries)
    branches = sum(s["num_branches"] for s in summaries)
    branch_covered = sum(s["covered_branches"] for s in summaries)
    require(
        statements > 0
        and covered / statements >= 0.98
        and branches > 0
        and branch_covered / branches >= 0.95,
        "COVERAGE",
    )
    return {
        "statement_pct": 100 * covered / statements,
        "branch_pct": 100 * branch_covered / branches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-checkout", type=Path)
    parser.add_argument("--verify-history", action="store_true")
    parser.add_argument("--coverage-json", type=Path)
    args = parser.parse_args()
    if args.coverage_json:
        print(check_coverage(json.loads(args.coverage_json.read_text())))
    source = json.loads((ROOT / SOURCE_PATH).read_text())
    validate_sources(source, args.reference_checkout)
    validate_results(json.loads((ROOT / RESULT_PATH).read_text()))
    protected = verify_history() if args.verify_history else None
    print(
        f"H6_AUDIT_PASS: {len(source['files'])} source files; 26 scenarios; "
        f"protected={protected}; empirical/application=false"
    )


if __name__ == "__main__":
    main()
