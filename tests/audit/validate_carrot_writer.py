"""H3 audit integrity and optional local Git reads. Never execute reference code."""

import argparse
import ast
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from tests.audit.validate_steering_knowledge import verify_blob

ROOT = Path(__file__).resolve().parents[2]
PINS = dict(
    runtime="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
    current="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
    hoya="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
    pr9="6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5",
)
BASE = "66f4b79036560a11e7020af9cc214118dcbd4fba"
INTEGRATION = "7a2f051b1f3847786318900444c88c2ba7a74a67"
REQUIREMENTS = {
    "snapshot",
    "owner_identity",
    "scope",
    "context",
    "baseline_epoch",
    "monotonic_timestamp",
    "revision",
    "expected_revision_cas",
    "atomic_selected_tuple",
    "revision_plus_one_ack",
    "independent_readback",
    "unrelated_preservation",
    "exclusive_ownership",
    "rollback",
    "failure_semantics",
    "watchdog",
}
CONFLICTS = {
    "torqued/live path",
    "manual/custom",
    "full NN / NN-lite / brand NN",
    "default CarParams",
    "controlsd initialization",
    "Params/UI refresh",
    "CyberPilot proposed writer",
}
VERDICTS = {
    "FACTOR_UNIT_EQUIVALENCE_UNRESOLVED",
    "FRICTION_UNIT_EQUIVALENCE_UNRESOLVED",
    "OFFSET_SEMANTICS_PROVEN",
    "OWNERSHIP_MODEL_SELECTED",
    "CAS_SOURCE_CHANGE_REQUIRED",
    "READBACK_SOURCE_CHANGE_REQUIRED",
    "VEHICLE_APPLICATION_BOUNDS_UNRESOLVED",
    "PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED",
    "RUNTIME_FINGERPRINT_UNCONFIRMED",
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def hex_id(value, size):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{" + str(size) + "}", value) is not None


def validate(sources, matrix):
    require(sources["schema_version"] == matrix["schema_version"] == 1, "unsupported schema")
    require(sources["scope"] == matrix["scope"] == "AUDIT_DESIGN_ONLY", "scope")
    require(sources["pins"] == PINS and sources["base"] == BASE, "source revision mismatch")
    require(sources["integration"] == INTEGRATION, "integration mismatch")
    require(
        sources["copied_source_bodies"]
        is sources["reference_execution"]
        is sources["network_or_vehicle_runtime"]
        is False,
        "audit boundary",
    )
    files = {f["id"]: f for f in sources["files"]}
    require(len(files) == len(sources["files"]) == 55, "file inventory")
    for f in files.values():
        role = f["id"].split(":")[0]
        require(role in PINS and f["exact_revision"] == PINS[role], "file source role/revision")
        require(f["id"] == role + ":" + f["path"], "file identity")
        expected_repo = (
            "rownlvh8875-coder/cyberpilot-autotune"
            if role == "pr9"
            else "rownlvh8875-coder/openpilot"
            if role == "runtime"
            else "ajouatom/openpilot"
        )
        require(f["repository"] == expected_repo, "repository")
        path = PurePosixPath(f["path"])
        require(not path.is_absolute() and ".." not in path.parts and "\\" not in f["path"], "path")
        require(hex_id(f["git_blob_sha"], 40) and hex_id(f["sha256"], 64), "file hash")
        require(type(f["line_count"]) is int and f["line_count"] > 0, "source size")
    claims = {c["id"]: c for c in sources["claims"]}
    require(len(claims) == len(sources["claims"]) == 93, "claim inventory")
    for c in claims.values():
        require(
            c["file_id"] in files and c["id"].split(":")[0] == c["file_id"].split(":")[0],
            "claim source",
        )
        f = files[c["file_id"]]
        require(
            type(c["range_start"]) is type(c["range_end"]) is int
            and 1 <= c["range_start"] <= c["range_end"] <= f["line_count"],
            "claim range",
        )
        require(hex_id(c["source_range_sha256"], 64), "range digest")
        require(
            c["confidence"] in {"PROVEN", "CONDITIONAL", "HEURISTIC", "UNRESOLVED", "REJECTED"},
            "confidence",
        )
        require(
            bool(c["symbol"]) and bool(c["semantic_claim"]) and bool(c["conditions"]),
            "claim semantics",
        )
    ps = {p["parameter_id"]: p for p in matrix["parameters"]}
    require(
        len(ps) == len(matrix["parameters"]) == 3
        and set(ps) == {"lat_accel_factor", "friction", "lat_accel_offset"},
        "tuple",
    )
    for key in ("lat_accel_factor", "friction"):
        require(
            ps[key]["tunable"] is True and ps[key]["storage_scale"] == 0.001,
            "coefficient transform",
        )
        require(
            ps[key]["global_status"]
            == ("FACTOR" if key == "lat_accel_factor" else "FRICTION")
            + "_UNIT_EQUIVALENCE_UNRESOLVED",
            "unit overclaim",
        )
        require(
            ps[key]["confidence"] == "CONDITIONAL" and bool(ps[key]["unresolved_gaps"]), "unit gaps"
        )
    require(
        ps["lat_accel_offset"]["tunable"] is False
        and ps["lat_accel_offset"]["stored_representation"] is None,
        "preserved offset",
    )
    require(ps["friction"]["unit"] is None, "unproven friction unit")
    require(
        {c["source"] for c in matrix["writer_conflicts"]} == CONFLICTS
        and len(matrix["writer_conflicts"]) == 7,
        "conflict completeness",
    )
    require(
        {c["requirement"] for c in matrix["pr9_requirements"]} == REQUIREMENTS
        and len(matrix["pr9_requirements"]) == 16,
        "requirement completeness",
    )
    for entry in matrix["writer_conflicts"]:
        require(
            entry["conflict"] in {"NONE", "CONDITIONAL", "DEFINITE", "UNRESOLVED"},
            "conflict status",
        )
    for entry in matrix["pr9_requirements"]:
        require(
            entry["status"] in {"PROVEN", "DESIGNABLE", "SOURCE_CHANGE_REQUIRED", "BLOCKED"},
            "requirement status",
        )
    require(
        matrix["existing"]
        == dict(
            cas="NO_EXISTING_CAS",
            readback="NO_EXISTING_VERIFIED_READBACK",
            atomic_tuple="ATOMIC_TUPLE_NOT_PROVEN",
        ),
        "existing protocol overclaim",
    )
    require(
        len(matrix["readback_candidates"]) == 5
        and all(c["existing_verified"] is False for c in matrix["readback_candidates"]),
        "readback overclaim",
    )
    require(
        {o["option"] for o in matrix["options"]} == set("ABCDE") and len(matrix["options"]) == 5,
        "option completeness",
    )
    for option in matrix["options"]:
        require(
            len(option["scores"]) == 12
            and all(type(v) is int and 0 <= v <= 5 for v in option["scores"].values())
            and bool(option["rationale"]),
            "scores/rationale",
        )
    require(
        matrix["selected_option"] == "C"
        and matrix["selected_architecture"] == "SHARED_TORQUE_PARAMETER_OWNER",
        "selection",
    )
    require(
        len(matrix["implementation_gates"]) == 12
        and {g["gate"]: g["status"] for g in matrix["implementation_gates"]}["vehicle_bounds_rates"]
        == "BLOCKED",
        "implementation gates",
    )
    require(
        set(matrix["verdicts"]) == VERDICTS and len(matrix["verdicts"]) == len(VERDICTS),
        "qualification overclaim",
    )
    require(
        matrix["application_bounds"] is matrix["application_rates"] is None, "no vehicle policy"
    )
    require(
        matrix["writer_implemented"]
        is matrix["watchdog_owner_approved"]
        is matrix["physical_actuation_proven"]
        is False,
        "implementation/approval overclaim",
    )
    require(matrix["hoya_apply"] == "APPLICATION_ARCHITECTURE_REJECTED", "Hoya is not owner")
    for group in (
        "parameters",
        "writer_conflicts",
        "pr9_requirements",
        "options",
        "readback_candidates",
    ):
        for item in matrix[group]:
            require(
                bool(item["evidence"]) and set(item["evidence"]) <= claims.keys(),
                "dangling evidence",
            )
    require(set(matrix["drift"]["evidence"]) <= claims.keys(), "drift evidence")
    return dict(
        files=len(files), claims=len(claims), parameters=len(ps), requirements=len(REQUIREMENTS)
    )


def coefficient_scales(data):
    found = {}
    keys = {"LateralTorqueAccelFactor", "LateralTorqueFriction"}
    for node in ast.walk(ast.parse(data.decode("utf8"))):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.BinOp):
            continue
        v = node.value
        if not (
            isinstance(v.op, ast.Mult)
            and isinstance(v.left, ast.Call)
            and isinstance(v.left.func, ast.Attribute)
            and v.left.func.attr == "get_float"
            and v.left.args
            and isinstance(v.left.args[0], ast.Constant)
            and isinstance(v.right, ast.Constant)
        ):
            continue
        name = v.left.args[0].value
        if name in keys:
            require(
                type(v.right.value) is float and v.right.value == 0.001, "wrong storage transform"
            )
            require(
                any(
                    isinstance(t, ast.Attribute)
                    and t.attr
                    == ("latAccelFactor" if name == "LateralTorqueAccelFactor" else "friction")
                    for t in node.targets
                ),
                "wrong consumer destination",
            )
            found[name] = v.right.value
    require(set(found) == keys, "missing coefficient transform")
    return found


def nn_modes(data):
    tree = ast.parse(data.decode("utf8"))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    require(
        {
            "use_nnff",
            "use_nnff_lite",
            "torque_from_nn",
            "nn_friction_override",
            "torque_from_lateral_accel",
        }
        <= attrs,
        "NN/fallback alternatives",
    )
    full = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.BoolOp)
            and isinstance(node.test.op, ast.And)
        ):
            if any(
                isinstance(v, ast.Attribute) and v.attr == "use_nnff" for v in node.test.values
            ) and any(isinstance(v, ast.Name) and v.id == "model_good" for v in node.test.values):
                full.append(node)
    require(len(full) == 1, "full NN requires model_good")
    require(
        len(full[0].orelse) > 0 and not isinstance(full[0].orelse[0], ast.If),
        "explicit non-NN fallback",
    )
    fallback = ast.Module(body=full[0].orelse, type_ignores=[])
    require(
        any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "torque_from_lateral_accel"
            for n in ast.walk(fallback)
        ),
        "fallback callback",
    )


def semantic_check(path, data):
    """Selected structural witnesses supplement hashes and human semantic review."""
    text = data.decode("utf8")
    if path.endswith("latcontrol_torque.py"):
        coefficient_scales(data)
        tree = ast.parse(text)
        cls = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LatControlTorque"
        )
        functions = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
        setter = functions["update_live_torque_params"]
        require(
            [a.arg for a in setter.args.args]
            == ["self", "latAccelFactor", "latAccelOffset", "friction"],
            "setter is not a CAS port",
        )
        require(
            isinstance(setter.body[0], ast.If)
            and any(isinstance(n, ast.Return) for n in ast.walk(setter.body[0])),
            "custom suppresses live setter",
        )
        guard = setter.body[0].test
        require(
            isinstance(guard, ast.Compare)
            and isinstance(guard.left, ast.Attribute)
            and guard.left.attr == "lateralTorqueCustom"
            and len(guard.ops) == 1
            and isinstance(guard.ops[0], ast.Gt)
            and isinstance(guard.comparators[0], ast.Constant)
            and guard.comparators[0].value == 0,
            "cached positive custom guard",
        )
        require(
            [n.targets[0].attr for n in setter.body if isinstance(n, ast.Assign)]
            == ["latAccelFactor", "latAccelOffset", "friction"],
            "live tuple fields",
        )
        update = functions["update"]
        attrs = {n.attr for n in ast.walk(update) if isinstance(n, ast.Attribute)}
        require(
            {
                "use_nnff",
                "use_nnff_lite",
                "torque_from_nn",
                "nn_friction_override",
                "torque_from_lateral_accel",
            }
            <= attrs,
            "NN/fallback alternatives",
        )
        nn_modes(data)
        require(
            any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get_int"
                and n.args
                and isinstance(n.args[0], ast.Constant)
                and n.args[0].value == "LateralTorqueCustom"
                for n in ast.walk(update)
            ),
            "custom selector getter",
        )
    elif path.endswith("/torqued.py"):
        tree = ast.parse(text)
        calls = {
            n.func.attr
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        require(
            {"svd", "std", "matmul", "interp", "put_nonblocking"} <= calls,
            "fit/lifecycle witnesses",
        )
        require(
            {
                "latAccelOffsetFiltered",
                "latAccelOffsetRaw",
                "frictionCoefficientFiltered",
                "latAccelFactorFiltered",
            }
            <= attrs,
            "producer fields",
        )
        require("LateralTorqueCustom" not in text, "estimator independent of custom selector")
    elif path.endswith("/controlsd.py"):
        tree = ast.parse(text)
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "update_live_torque_params"
        ]
        require(
            len(calls) == 1
            and [a.attr for a in calls[0].args]
            == ["latAccelFactorFiltered", "latAccelOffsetFiltered", "frictionCoefficientFiltered"],
            "filtered consumer tuple",
        )
        require("liveValid" not in text, "consumer does not gate estimate liveValid")
    elif path.endswith("/log.capnp"):
        start = text.index("struct LiveTorqueParametersData")
        block = text[start : text.index("\n}", start)]
        for field, ordinal in (
            ("latAccelFactorFiltered", 4),
            ("latAccelOffsetFiltered", 5),
            ("frictionCoefficientFiltered", 6),
        ):
            require(
                re.search(field + r"\s+@" + str(ordinal) + r"\s*:Float32", block),
                "wire field/ordinal",
            )
        require(
            "version @11 :Int32" in block and "revision" not in block and "owner" not in block,
            "schema version is not owner revision",
        )


def verify_sources(sources, reference, target):
    def git(repo, *args):
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            env=os.environ | {"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"},
            stderr=subprocess.PIPE,
        )

    require(
        git(reference, "rev-parse", INTEGRATION + "^{tree}")
        == git(reference, "rev-parse", PINS["runtime"] + "^{tree}"),
        "integration provenance",
    )
    for file in sources["files"]:
        repo = target if file["id"].startswith("pr9:") else reference
        raw = git(repo, "show", file["exact_revision"] + ":" + file["path"])
        ranges = [c for c in sources["claims"] if c["file_id"] == file["id"]]
        verify_blob(file, ranges, raw)
        semantic_check(file["path"], raw)
    require(
        git(reference, "show", PINS["runtime"] + ":openpilot/selfdrive/locationd/torqued.py")
        == git(reference, "show", PINS["current"] + ":openpilot/selfdrive/locationd/torqued.py"),
        "torqued drift requires renewed review",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", type=Path)
    parser.add_argument("--target-checkout", type=Path, default=ROOT)
    args = parser.parse_args()
    sources, matrix = (
        json.loads((ROOT / "docs/evidence" / n).read_text(encoding="utf8"))
        for n in ("carrot_writer_ownership_sources.json", "carrot_writer_unit_matrix.json")
    )
    result = validate(sources, matrix)
    if args.reference_checkout is not None:
        verify_sources(sources, args.reference_checkout, args.target_checkout)
    print(
        json.dumps(
            result | {"source_bytes_verified": args.reference_checkout is not None}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
