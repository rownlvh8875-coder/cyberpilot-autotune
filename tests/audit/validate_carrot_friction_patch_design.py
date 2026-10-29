"""Offline proposal audit only: no native patch, runtime import or producer."""

import argparse
import ast
import hashlib
import json
import math
import re
import struct
import subprocess
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from cyberpilot_autotune.observability.schema import CONTRACT_TYPES, semantic_schema
from cyberpilot_autotune.observability.types import CURRENT, RUNTIME, digest, require
from tests.audit import validate_friction_receipt as h7

ROOT = Path(__file__).resolve().parents[2]
BASE = "5357d5d555d49b258affa237d83b8491b8a8c6ce"
FREEZE = "115fd98534eed0f39e4017e0d72fafbb662fc71d"
PREFIX = "docs/evidence/carrot_friction_patch_"
SOURCE_DIGEST = "e9265926f330d17b34cdf549417e8a677727ca31b7c1420de730365ba9e404dc"
MATH_DIGEST = "c432bd380f820b3cc3373daa728322a60319527ae4c519f2887d4a69ff071b18"
CI_PATH = ".github/workflows/ci.yml"
LOCAL_RECORDS = {"ObservationPolicy", "ObservationEligibilityDecision"}
NATIVE = (
    ("helper", "opendbc_repo/opendbc/car/__init__.py", ("apply_center_deadzone", "get_friction")),
    (
        "callback",
        "opendbc_repo/opendbc/car/interfaces.py",
        ("CarInterfaceBase.torque_from_lateral_accel_linear",),
    ),
    ("pid", "openpilot/common/pid.py", ("PIDController.update",)),
    (
        "controller",
        "openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        ("LatControlTorque.update",),
    ),
    (
        "controlsd",
        "openpilot/selfdrive/controls/controlsd.py",
        ("Controls.update", "Controls.state_control", "Controls.publish", "Controls.run"),
    ),
    ("log", "openpilot/cereal/log.capnp", ()),
    ("custom", "openpilot/cereal/custom.capnp", ()),
    ("services", "openpilot/cereal/services.py", ()),
    (
        "messaging",
        "openpilot/cereal/messaging/__init__.py",
        ("new_message", "SubMaster.update_msgs", "PubMaster.send"),
    ),
)
BASIS = (
    "docs/friction_observability_receipt_contract.md",
    "docs/friction_observability_wire_design.md",
    "docs/friction_observability_capture_architecture.md",
    "docs/friction_observability_source_compatibility.md",
    "docs/friction_receipt_observation_v2_mapping.md",
    "docs/friction_observability_h7_result.md",
    "docs/evidence/friction_observability_receipt_schema.json",
    "docs/evidence/friction_observability_receipt_sources.json",
) + tuple(
    "src/cyberpilot_autotune/observability/" + name + ".py"
    for name in ("__init__", "types", "context", "contracts", "schema", "validation")
)


def git_bytes(checkout, revision, path):
    return h7.h6.git_bytes(checkout, revision, path)


def git_text(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True)


def source_specs():
    return tuple(
        (profile + "_" + name, revision, path, symbols)
        for profile, revision in (("R", RUNTIME), ("C", CURRENT))
        for name, path, symbols in NATIVE
    ) + tuple(("h7_" + str(i), BASE, path, ()) for i, path in enumerate(BASIS))


def build_sources(reference):
    files = []
    for identity, revision, path, symbols in source_specs():
        raw = git_bytes(ROOT if revision == BASE else reference, revision, path)
        files.append(
            {
                "id": identity,
                "revision": revision,
                "path": path,
                "repository": "rownlvh8875-coder/cyberpilot-autotune"
                if revision == BASE
                else "rownlvh8875-coder/openpilot"
                if revision == RUNTIME
                else "ajouatom/openpilot",
                "blob_sha": hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "ranges": h7.h6.spans(raw, symbols),
            }
        )
    return {
        "schema": "carrot-friction-patch-design-sources-v1",
        "base": BASE,
        "freeze": FREEZE,
        "primary_native_base": RUNTIME,
        "comparative_native_base": CURRENT,
        "carrot_wip_observed": CURRENT,
        "auto_promoted": False,
        "candidate_revision": None,
        "native_patch_implemented": False,
        "files": files,
        "wire_digest": digest(build_wire()),
        "math_digest": digest(build_math(reference)),
    }


def _camel(name):
    parts = name.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


def _wire_type(field):
    expression, name = field["python_type"], field["field"].split(".")[1]
    primitive = expression.removesuffix(" | None")
    if primitive in {"float", "<class 'float'>"}:
        return "OptionalFloat64"
    if primitive in {"int", "<class 'int'>"}:
        return "OptionalUInt64"
    if primitive in {"bool", "<class 'bool'>"}:
        return "OptionalBool"
    if primitive in {"str", "<class 'str'>"}:
        return (
            "OptionalDigest"
            if name.endswith(("_digest", "_id", "_identity")) or name == "source_revision"
            else "Text"
        )
    for cls in CONTRACT_TYPES:
        if cls.__name__ in expression:
            return f"List({cls.__name__})" if expression.startswith("tuple[") else cls.__name__
    match = re.fullmatch(r"<enum '([^']+)'>", expression)
    require(match is not None, "UNMAPPED_WIRE_TYPE")
    return match.group(1)


def build_wire():
    schema = semantic_schema()
    counters = defaultdict(int)
    result = []
    for field in schema["fields"]:
        record, name = field["field"].split(".")
        local = record in LOCAL_RECORDS
        entry = {
            "semantic_field": field["field"],
            "local_only": local,
            "native_name": None if local else _camel(name),
            "ordinal": None if local else counters[record],
            "wire_type": None if local else _wire_type(field),
            "semantic_required": field["required"],
            "unit": field["unit"],
            "stage": field["stage"],
        }
        result.append(entry)
        counters[record] += 1
    enums = []
    for enum in schema["enums"]:
        if enum["type"] in {"EligibilityStatus", "ObservationReason"}:
            continue
        values = [v for v in enum["values"] if v != "UNKNOWN"]
        enums.append(
            {
                "type": enum["type"],
                "unknown_ordinal": 0,
                "values": [{"semantic": value, "ordinal": i + 1} for i, value in enumerate(values)],
            }
        )
    return {
        "schema": "carrot-friction-wire-proposal-v1",
        "allocation_state": "PROPOSAL_ONLY",
        "native_patch_implemented": False,
        "candidate_revision": None,
        "primary_native_base": RUNTIME,
        "q_observed_policy": "UNAVAILABLE_ALWAYS_PASSIVE",
        "slot": {
            "existing_name": "customReserved3",
            "proposed_name": "lateralTorqueIdentification",
            "event_ordinal": 110,
            "type_id": "0xda96579883444c35",
        },
        "service": {
            "name": "lateralTorqueIdentification",
            "frequency_hz": 100,
            "should_log": False,
            "activation_default": False,
            "transport_qualified": False,
        },
        "optional_wrappers": {
            name: {"unavailable_ordinal": 0, "value_ordinal": 1, "payload": payload}
            for name, payload in (
                ("OptionalFloat64", "Float64"),
                ("OptionalUInt64", "UInt64"),
                ("OptionalBool", "Bool"),
                ("OptionalDigest", "Data"),
            )
        },
        "required_presence": "WRAPPER_VALUE_ARM_OR_POINTER_PRESENT_AND_VALIDATED",
        "digest_lengths": {"source_revision": 20, "sha256": 32},
        "fields": result,
        "enums": enums,
        "source_registration": "NEW_EXACT_PATCH_SHA_REQUIRED_NO_OLD_PIN_SUBSTITUTION",
        "empirical_qualified": False,
        "application_authorized": False,
    }


def build_math(reference):
    import numpy as np

    profiles = []
    errors = (0.06, -0.06, 0.1, -0.1, 0.15, 0.2, -0.2, math.nextafter(0.3, 0.0))
    coefficients = tuple(float(np.float32(v)) for v in (0.1, 0.125, 0.17, 0.2)) + (0.0,)
    for profile, revision in (("R", RUNTIME), ("C", CURRENT)):
        raw = git_bytes(reference, revision, NATIVE[0][1])
        nodes = [
            node
            for node in ast.parse(raw).body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"apply_center_deadzone", "get_friction"}
        ]
        require(len(nodes) == 2, "EXACT_HELPER_FUNCTIONS")
        namespace = {
            "np": np,
            "structs": SimpleNamespace(CarParams=SimpleNamespace(LateralTorqueTuning=object)),
        }
        exec(
            compile(
                ast.Module(body=nodes, type_ignores=[]), "<isolated-friction-design-math>", "exec"
            ),
            namespace,
        )
        cases = []
        for error in errors:
            for coefficient in coefficients:
                legacy = float(
                    namespace["get_friction"](
                        error, 0.06, 0.3, SimpleNamespace(friction=coefficient), True
                    )
                )
                q = max(-1.0, min(1.0, error / 0.3))
                rewritten = coefficient * q
                cases.append(
                    {
                        "error_hex": error.hex(),
                        "C_hex": coefficient.hex(),
                        "q_diagnostic_hex": q.hex(),
                        "legacy_hex": legacy.hex(),
                        "cq_hex": rewritten.hex(),
                        "bit_equal": struct.pack("!d", legacy) == struct.pack("!d", rewritten),
                        "numeric_equal": legacy == rewritten,
                    }
                )
        profiles.append(
            {
                "profile": profile,
                "revision": revision,
                "cases": cases,
                "bit_differences": sum(not c["bit_equal"] for c in cases),
                "numeric_differences": sum(not c["numeric_equal"] for c in cases),
            }
        )
    return {
        "schema": "carrot-friction-synthetic-rounding-v1",
        "profiles": profiles,
        "corpus_kind": "SYNTHETIC_NOT_VEHICLE_DATA",
        "q_origin": "RECONSTRUCTED_DIAGNOSTIC_ONLY",
        "empirical_qualified": False,
        "universal_equivalence_proved": False,
    }


def validate_wire(data):
    require(data == build_wire(), "WIRE_PROPOSAL_MUTATED")


def validate_math(data, reference=None):
    require(digest(data) == MATH_DIGEST, "MATH_PROOF_MUTATED")
    if reference is not None:
        require(data == build_math(reference), "EXACT_SOURCE_MATH_DRIFT")


def validate_sources(data, reference=None):
    require(digest(data) == SOURCE_DIGEST, "SOURCE_MANIFEST_MUTATED")
    require(data["wire_digest"] == digest(build_wire()), "WIRE_BINDING")
    if reference is not None:
        require(data == build_sources(reference), "SOURCE_BYTES_OR_DESIGN_DRIFT")
        verify_native(reference)


def verify_native(reference):
    for revision in (RUNTIME, CURRENT):
        custom = git_bytes(reference, revision, "openpilot/cereal/custom.capnp").decode()
        log = git_bytes(reference, revision, "openpilot/cereal/log.capnp").decode()
        require(
            re.search(r"struct CustomReserved3 @0xda96579883444c35\s*\{\s*\}", custom) is not None,
            "RESERVED_TYPE_NOT_EMPTY",
        )
        require(
            re.search(r"customReserved3\s*@110\s*:Custom.CustomReserved3;", log) is not None,
            "RESERVED_EVENT_LINK_CHANGED",
        )
        service = git_bytes(reference, revision, "openpilot/cereal/services.py").decode()
        require('"lateralTorqueIdentification"' not in service, "SERVICE_ALREADY_ALLOCATED")
        messaging = git_bytes(reference, revision, "openpilot/cereal/messaging/__init__.py")
        tree = ast.parse(messaging)
        pub = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "PubMaster"
        )
        send = next(
            node for node in pub.body if isinstance(node, ast.FunctionDef) and node.name == "send"
        )
        require(
            [arg.arg for arg in send.args.args] == ["self", "s", "dat"], "TRANSPORT_API_CHANGED"
        )
        require(
            "dat.to_bytes()" in ast.unparse(send) and ".send(dat)" in ast.unparse(send),
            "SYNC_SEND_PATH_CHANGED",
        )
    h7.verify_source_equations(reference)


def extend_ci(original):
    receipt_module = "tests.audit.validate_friction_receipt"
    design_module = "tests.audit.validate_carrot_friction_patch_design"
    golden = "      - name: Verify pinned synthetic golden evidence across fresh processes\n"
    old_import = (
        f"          from {receipt_module} import "
        "source_specs as receipt_specs, BASE as receipt_base\n"
    )
    new_import = (
        f"          from {design_module} import source_specs as design_specs, BASE as design_base\n"
    )

    def warm_loop(prefix):
        return (
            f"          for _, revision, path, _ in {prefix}_specs():\n"
            f"              if revision != {prefix}_base:\n"
            "                  git_bytes(sys.argv[1], revision, path)\n"
        )

    command = (
        '          sudo unshare --net -- setpriv --reuid="$audit_uid" '
        '--regid="$audit_gid" --init-groups env PYTHONDONTWRITEBYTECODE=1 '
        'GIT_NO_LAZY_FETCH=1 "$audit_python" -m '
    )
    tail = ' --reference-checkout "$RUNNER_TEMP/knowledge-reference" --verify-history\n'
    old_audit = command + receipt_module + tail
    changes = (
        (golden, f"      - run: python -m {design_module} --verify-history\n" + golden),
        (old_import, old_import + new_import),
        (warm_loop("receipt"), warm_loop("receipt") + warm_loop("design")),
        (old_audit, old_audit + command + design_module + tail),
    )
    result = original
    for old, new in changes:
        require(result.count(old) == 1, "BASE_CI_ANCHOR_CHANGED")
        result = result.replace(old, new, 1)
    return result


def compatible_ci(original, actual):
    return actual in (original, extend_ci(original))


def verify_history():
    commits = h7.h6.history_order(ROOT, BASE, "HEAD")
    require(commits and commits[0] == FREEZE, "DESIGN_FREEZE_NOT_FIRST")
    freeze_files = git_text("diff-tree", "--no-commit-id", "--name-only", "-r", FREEZE).splitlines()
    require(
        set(freeze_files)
        == {
            "docs/superpowers/specs/2026-10-29-carrot-friction-producer-design.md",
            "docs/superpowers/plans/2026-10-29-carrot-friction-producer-design.md",
        },
        "DESIGN_FREEZE_FILES",
    )
    paths = git_text("ls-tree", "-r", "--name-only", BASE).splitlines()
    for path in paths:
        original = git_bytes(ROOT, BASE, path).replace(b"\r\n", b"\n")
        actual = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        require(
            compatible_ci(original.decode(), actual.decode())
            if path == CI_PATH
            else actual == original,
            "H7_BASE_FILE_CHANGED:" + path,
        )
    return {"protected_files": len(paths), "all_h7_source_unchanged": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-checkout", type=Path)
    parser.add_argument("--verify-history", action="store_true")
    args = parser.parse_args()
    source, wire, proof = [
        json.loads((ROOT / (PREFIX + name + ".json")).read_text())
        for name in ("sources", "wire", "math")
    ]
    validate_wire(wire)
    validate_math(proof, args.reference_checkout)
    validate_sources(source, args.reference_checkout)
    output = {
        "PATCH_DESIGN_AUDIT_PASS": True,
        "files": len(source["files"]),
        "semantic_fields": len(wire["fields"]),
        "native_patch_implemented": False,
        "q_observed_available": False,
        "empirical_qualified": False,
        "application_authorized": False,
    }
    if args.verify_history:
        output["history"] = verify_history()
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
