"""H7 exact-source/semantic/history audit; no producer or native imports."""

import argparse
import ast
import copy
import hashlib
import json
import math
import re
import subprocess
from dataclasses import replace
from numbers import Number
from pathlib import Path
from types import SimpleNamespace

from cyberpilot_autotune.observability import validation as v
from cyberpilot_autotune.observability.schema import semantic_schema, validate_semantic_schema
from cyberpilot_autotune.observability.types import (
    CURRENT,
    RUNTIME,
    CallbackFamily,
    CallbackFunction,
    CallbackStage,
    Precision,
    ScalarOrigin,
    Signal,
    Stage,
    digest,
    require,
)
from tests.audit import validate_friction_model as h6
from tests.fixtures.friction_receipt import complete, scalar

ROOT = Path(__file__).resolve().parents[2]
BASE = "a5d3514f23797829eb58d08c638b22cf4dd30c8a"
FREEZE = "83c2170d699894a8044b1e82d453281ccd495d5d"
SOURCE_PATH = "docs/evidence/friction_observability_receipt_sources.json"
SCHEMA_PATH = "docs/evidence/friction_observability_receipt_schema.json"
SOURCE_MANIFEST_SHA256 = "c2bc6a566ec0a9906e9ce407fce6ec803d1c8f0dc72edd696b6dd2f46c36a747"
COMPATIBILITY = (
    "tests/architecture/test_knowledge_boundary.py",
    "tests/audit/test_carrot_writer_ownership.py",
    "tests/audit/test_hoya_c3_atune_evidence.py",
)
BASIS = (
    "docs/friction_observation_contract.md",
    "docs/friction_observability_gap_matrix.md",
    "docs/friction_model_estimand.md",
    "docs/friction_model_identifiability.md",
    "docs/torque_geometry_context.md",
    "docs/friction_model_redesign_result.md",
    "docs/evidence/friction_model_policy.json",
    "docs/evidence/friction_model_sources.json",
    "docs/evidence/torque_geometry_context.json",
)


def source_specs():
    result = []
    for identity, revision, path, symbols in h6.source_specs():
        revision = BASE if revision == h6.BASE else revision
        if identity.endswith("_controller"):
            symbols += ("LatControlTorque.update_live_torque_params",)
        if identity.endswith("_controlsd"):
            symbols += ("Controls.state_control", "Controls.run")
        result.append((identity, revision, path, symbols))
    result.extend(
        (profile + "_car_schema", revision, "opendbc_repo/opendbc/car/car.capnp", ())
        for profile, revision in (("runtime", RUNTIME), ("current", CURRENT))
    )
    result.extend(("h6_basis_" + str(i), BASE, path, ()) for i, path in enumerate(BASIS))
    return tuple(result)


def _span(raw, start, end):
    return hashlib.sha256(b"".join(raw.splitlines(keepends=True)[start - 1 : end])).hexdigest()


def _block(raw, pattern):
    match = re.search(pattern, raw.decode(), re.S)
    require(match is not None, "SOURCE_BLOCK")
    return raw[: match.start()].count(b"\n") + 1, raw[: match.end()].count(b"\n") + 1


def build_sources(reference):
    files, raw_files = [], {}
    for identity, revision, path, symbols in source_specs():
        raw = h6.git_bytes(ROOT if revision == BASE else reference, revision, path)
        raw_files[identity] = raw
        files.append(
            {
                "id": identity,
                "repository": "rownlvh8875-coder/cyberpilot-autotune"
                if revision == BASE
                else "rownlvh8875-coder/openpilot"
                if revision == RUNTIME
                else "ajouatom/openpilot",
                "revision": revision,
                "path": path,
                "git_blob": hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "line_count": len(raw.splitlines()),
                "ranges": h6.spans(raw, symbols),
            }
        )
    byid = {f["id"]: f for f in files}
    claims = []

    def claim(identity, file_id, symbol, meaning):
        file = byid[file_id]
        raw = raw_files[file_id]
        if symbol == "LateralTorqueState":
            start, end = _block(raw, r"struct LateralTorqueState\s*\{.*?\}")
        elif symbol == "LateralTorqueTuning":
            start, end = _block(raw, r"struct LateralTorqueTuning\s*\{.*?\}")
        else:
            span = next(s for s in file["ranges"] if s["name"] == symbol)
            start, end = span["start"], span["end"]
        claims.append(
            {
                "id": identity,
                "file_id": file_id,
                "repository": file["repository"],
                "revision": file["revision"],
                "path": file["path"],
                "symbol": symbol,
                "start": start,
                "end": end,
                "git_blob": file["git_blob"],
                "sha256": _span(raw, start, end),
                "meaning": meaning,
            }
        )

    for profile in ("runtime", "current"):
        for name, file, symbol, meaning in (
            (
                "linear_inputs",
                "controller",
                "LatControlTorque.update",
                (
                    "a_cb=desired-roll*g; friction_input=desired-actual; ff call before "
                    "PID; compensation=True/gravity_adjusted=True"
                ),
            ),
            (
                "linear_return",
                "callback",
                "CarInterfaceBase.torque_from_lateral_accel_linear",
                "a/float(F)+get_friction; installed offset not read",
            ),
            (
                "deadzone",
                "friction",
                "apply_center_deadzone",
                "strict interior zero, endpoints survive, no width subtraction",
            ),
            (
                "helper_interp",
                "friction",
                "get_friction",
                (
                    "np.interp centered error [-T,T] -> [-C,C]; flag gates term; NO "
                    "independent q output"
                ),
            ),
            (
                "threshold",
                "callback",
                "whole_file",
                "FRICTION_THRESHOLD=0.3 imported by executed callback",
            ),
            (
                "pid_order",
                "pid",
                "PIDController.update",
                "latch speed, p/f/d, integrate/clip i, sum, output clip; f=ff*k_f",
            ),
            (
                "pid_effective_gain_capture",
                "pid",
                "whole_file",
                (
                    "speed-dependent interpolation means effective gains captured after "
                    "current PID speed latch"
                ),
            ),
            (
                "nn_lite_nn_custom",
                "controller",
                "LatControlTorque.update",
                (
                    "NN_LITE accel/jerk input; NN path/override; custom selector and actual "
                    "F/C/gain latch, no default inference"
                ),
            ),
            (
                "installed_offset",
                "controller",
                "LatControlTorque.update_live_torque_params",
                (
                    "offset stored from live context; custom can bypass; LINEAR callback "
                    "ignores offset"
                ),
            ),
            (
                "return_sign",
                "controller",
                "LatControlTorque.update",
                "internal PID output negated at return and log; existing logged values Float32",
            ),
            (
                "existing_precision",
                "schema",
                "LateralTorqueState",
                "p/i/d/f/output/actual/desired/error Float32, not exact local binary64 receipt",
            ),
            (
                "parameter_precision",
                "car_schema",
                "LateralTorqueTuning",
                (
                    "initial F/C/offset/gains Float32; Float64 capture preserves consumed "
                    "value, cannot restore original intent precision"
                ),
            ),
            (
                "geometry_apply",
                "controlsd",
                "whole_file",
                (
                    "R static CP geometry; C VM.update_geometry from consumed LP then "
                    "update_params; actual applied snapshot required"
                ),
            ),
            (
                "delay_and_requested",
                "controlsd",
                "whole_file",
                (
                    "SAD/liveDelay branch; LaC return assigned torque; carControl "
                    "publication later, not retroactive consumed input; CS is wire carState, "
                    "CC freshly allocated per state_control invocation; LP may use local fallback"
                ),
            ),
            (
                "cycle_entry",
                "controlsd",
                "Controls.state_control",
                (
                    "future cycle start is state_control entry before fresh local CC/fallback LP "
                    "creation, not callback/context/publication time; entry capture not published"
                ),
            ),
            (
                "serial_cycle_order",
                "controlsd",
                "Controls.run",
                "serial update -> state_control -> publish before next cycle entry, "
                "not companion completion",
            ),
        ):
            claim(profile + "_" + name, profile + "_" + file, symbol, meaning)
    claim(
        "current_dynamic_geometry",
        "current_geometry",
        "LateralGeometry",
        (
            "coherent rate-limited geometry; Params zero is vehicle-default intent; "
            "not actual VM receipt"
        ),
    )
    claim(
        "observation_v2_mapping",
        "observation_v2",
        "whole_file",
        (
            "sourceCS/exact lookup/measurement receipts reusable only for specified "
            "stage; no q/raw ff/installed gain cohort"
        ),
    )
    return {
        "schema": "friction-observability-source-v1",
        "base": BASE,
        "freeze_commit": FREEZE,
        "primary_pins": {"R": RUNTIME, "C": CURRENT},
        "carrot_wip_start": {
            "observed_head": CURRENT,
            "moved": False,
            "relevant_commits": [],
            "auto_promoted": False,
        },
        "files": files,
        "claims": claims,
        "neutral_schema_sha256": digest(semantic_schema()),
        "h6_validator_compatibility_sha256": hashlib.sha256(
            (ROOT / "tests/audit/validate_friction_model.py").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "runtime_producer_implemented": False,
        "native_runtime_imported": False,
        "params_accessed": False,
        "candidate_generation_allowed": False,
        "application_authorized": False,
        "runtime_accepted": False,
        "owner_proposal_allowed": False,
    }


def validate_sources(source, reference=None):
    require(digest(source) == SOURCE_MANIFEST_SHA256, "SOURCE_MANIFEST_MUTATION")
    require(source["base"] == BASE and source["freeze_commit"] == FREEZE, "SOURCE_HISTORY")
    require(source["neutral_schema_sha256"] == digest(semantic_schema()), "SOURCE_SCHEMA")
    require(
        all(
            source[k] is False
            for k in (
                "runtime_producer_implemented",
                "native_runtime_imported",
                "params_accessed",
                "candidate_generation_allowed",
                "application_authorized",
                "runtime_accepted",
                "owner_proposal_allowed",
            )
        ),
        "SOURCE_AUTHORITY",
    )
    require(
        source["h6_validator_compatibility_sha256"]
        == hashlib.sha256(
            (ROOT / "tests/audit/validate_friction_model.py").read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "HISTORICAL_VALIDATOR_MUTATION",
    )
    validate_semantic_schema(json.loads((ROOT / SCHEMA_PATH).read_text()))
    if reference is not None:
        require(source == build_sources(reference), "EXACT_SOURCE_BYTES")
        verify_source_equations(reference)


def check_consumed_source_fragments(raw):
    """Read source AST only; never import/execute controlsd or access Params."""
    tree = ast.parse(raw)
    state = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "state_control"
    )
    publication = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "publish"
    )

    def assignments(node):
        return {
            (ast.unparse(target), ast.unparse(item.value))
            for item in ast.walk(node)
            if isinstance(item, ast.Assign)
            for target in item.targets
        }

    pairs = assignments(state)
    require(("CS", "self.sm['carState']") in pairs, "CONSUMED_CS_WIRE_ORIGIN")
    require(("CC", "car.CarControl.new_message()") in pairs, "CONSUMED_CC_LOCAL_ORIGIN")
    require(
        (
            "lp",
            "self.sm['liveParameters'] if lateral_ready else "
            "lateral_vehicle_parameters(self.sm, self.CP)",
        )
        in pairs,
        "CONSUMED_LP_SOURCE_ALTERNATIVES",
    )
    calls = [
        item
        for item in ast.walk(state)
        if isinstance(item, ast.Call) and ast.unparse(item.func) == "self.LaC.update"
    ]
    require(
        len(calls) == 1
        and len(calls[0].args) > 6
        and ast.unparse(calls[0].args[1]) == "CS"
        and ast.unparse(calls[0].args[3]) == "lp"
        and ast.unparse(calls[0].args[6]) == "CC",
        "CONSUMED_LOCAL_CC_CALL_ARGUMENT",
    )
    local_cc = next(
        item
        for item in state.body
        if isinstance(item, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CC" for t in item.targets)
    )
    require(state.lineno < local_cc.lineno < calls[0].lineno, "LOCAL_OBJECT_CREATION_IN_CYCLE")
    published = assignments(publication)
    require(
        ("cc_send", "messaging.new_message('carControl')") in published
        and ("cc_send.carControl", "CC") in published,
        "PUBLISHED_CC_NOT_CONSUMED_EVENT",
    )
    event_order = (
        "messaging.new_message('controlsState')",
        "self.pm.send('controlsState', dat)",
        "messaging.new_message('carControl')",
        "self.pm.send('carControl', cc_send)",
    )
    call_lines = {
        ast.unparse(item): item.lineno
        for item in ast.walk(publication)
        if isinstance(item, ast.Call)
    }
    require(
        all(call in call_lines for call in event_order)
        and all(
            call_lines[a] < call_lines[b]
            for a, b in zip(event_order[:-1], event_order[1:], strict=True)
        ),
        "CONTROL_AND_COMMAND_EVENT_ORDER",
    )
    runner = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    loop = next(node for node in ast.walk(runner) if isinstance(node, ast.While))
    serial_calls = [
        ast.unparse(call.func)
        for statement in loop.body
        for call in ast.walk(statement)
        if isinstance(call, ast.Call)
        and ast.unparse(call.func) in {"self.update", "self.state_control", "self.publish"}
    ]
    require(
        serial_calls == ["self.update", "self.state_control", "self.publish"],
        "SERIAL_CONTROLLER_CYCLE_ORDER",
    )


def check_callback_fragments(raw):
    tree = ast.parse(raw)
    pairs = {
        (ast.unparse(target), ast.unparse(node.value))
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
    }
    require(
        ("gravity_adjusted_lateral_accel", "desired_lateral_accel - roll_compensation") in pairs,
        "CALLBACK_A_EQUATION",
    )
    require(
        ("error", "desired_lateral_accel - actual_lateral_accel") in pairs
        and ("friction_input", "error") in pairs,
        "FRICTION_INPUT_EQUATION",
    )
    ff = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "ff" for t in node.targets)
        and isinstance(node.value, ast.Call)
        and ast.unparse(node.value.func) == "self.torque_from_lateral_accel"
    ]
    require(len(ff) == 1, "FF_CALL_SITE")
    args = {kw.arg: ast.literal_eval(kw.value) for kw in ff[0].keywords}
    require(args == {"friction_compensation": True, "gravity_adjusted": True}, "FF_FLAGS")
    require(
        ast.unparse(ff[0].args[0]).startswith("LatControlInputs(gravity_adjusted_lateral_accel,")
        and ast.unparse(ff[0].args[2]) == "friction_input"
        and ast.unparse(ff[0].args[3]) == "lateral_accel_deadzone",
        "FF_RAW_INPUTS",
    )


def verify_source_equations(reference):
    import numpy as np

    cases = 0
    for revision in (RUNTIME, CURRENT):
        check_consumed_source_fragments(
            h6.git_bytes(reference, revision, "openpilot/selfdrive/controls/controlsd.py")
        )
        controller = h6.git_bytes(
            reference, revision, "openpilot/selfdrive/controls/lib/latcontrol_torque.py"
        )
        check_callback_fragments(controller)
        interface = h6.git_bytes(reference, revision, "opendbc_repo/opendbc/car/interfaces.py")
        threshold = next(
            node.value.value
            for node in ast.parse(interface).body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "FRICTION_THRESHOLD" for t in node.targets)
        )
        require(threshold == 0.3, "SOURCE_THRESHOLD")
        ns = {
            "np": np,
            "structs": SimpleNamespace(CarParams=SimpleNamespace(LateralTorqueTuning=object)),
            "LatControlInputs": object,
            "FRICTION_THRESHOLD": threshold,
        }
        raw = h6.git_bytes(reference, revision, "opendbc_repo/opendbc/car/__init__.py")
        nodes = [
            n
            for n in ast.parse(raw).body
            if isinstance(n, ast.FunctionDef)
            and n.name in {"apply_center_deadzone", "get_friction"}
        ]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<exact-friction-math>", "exec"), ns)
        for enabled in (False, True):
            for error in (-0.6, -0.06, -0.01, 0.0, 0.01, 0.06, 0.15, 0.6):
                native = ns["get_friction"](
                    error, 0.06, threshold, SimpleNamespace(friction=1.0), enabled
                )
                reconstructed = v.reconstruct_q_diagnostic(error, 0.06, threshold, enabled)
                require(
                    math.isclose(native, reconstructed, rel_tol=0, abs_tol=2e-15), "Q_SOURCE_PARITY"
                )
                cases += 1
        node = next(
            node
            for top in ast.parse(interface).body
            if isinstance(top, ast.ClassDef) and top.name == "CarInterfaceBase"
            for node in top.body
            if isinstance(node, ast.FunctionDef) and node.name == "torque_from_lateral_accel_linear"
        )
        require(
            not any(
                isinstance(n, ast.Attribute) and n.attr == "latAccelOffset" for n in ast.walk(node)
            ),
            "OFFSET_NOT_LINEAR_INPUT",
        )
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<exact-linear-math>", "exec"), ns)
        for offset in (0.0, 99.0):
            params = SimpleNamespace(latAccelFactor=2.0, friction=0.125, latAccelOffset=offset)
            for acceleration in (1.0, np.float64(1.0)):
                actual = ns["torque_from_lateral_accel_linear"](
                    None,
                    SimpleNamespace(lateral_acceleration=acceleration),
                    params,
                    0.5,
                    0.06,
                    True,
                    True,
                )
                require(
                    actual == 0.625 and isinstance(actual, (float, np.float64)),
                    "CALLBACK_RAW_BINARY64",
                )
                cases += 1
        pid = h6.git_bytes(reference, revision, "openpilot/common/pid.py")
        cls = next(
            n
            for n in ast.parse(pid).body
            if isinstance(n, ast.ClassDef) and n.name == "PIDController"
        )
        env = {"np": np, "Number": Number}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), "<exact-pid-math>", "exec"), env)
        math_pid = env["PIDController"](
            [[0, 20], [0.2, 0.8]], 0.0, k_f=0.5, pos_limit=1.0, neg_limit=-1.0
        )
        require(math_pid.k_p == 0.2, "GAIN_INITIAL_SPEED")
        output = math_pid.update(0.1, speed=20.0, feedforward=0.625)
        require(
            math_pid.k_p == 0.8
            and math.isclose(math_pid.p, 0.08)
            and math_pid.f == 0.3125
            and math.isclose(output, 0.3925),
            "PID_CURRENT_SPEED_GAIN_AND_KF",
        )
        output = math_pid.update(0.0, speed=20.0, feedforward=4.0)
        require(math_pid.f == 2.0 and output == 1.0, "PID_PRE_POST_CLIP_STAGE")
        cases += 2
    h6.verify_source_equations(reference)
    return {
        "isolated_math_cases": cases,
        "native_runtime_imported": False,
        "params_accessed": False,
    }


def _historical_validator_unchanged_elsewhere():
    path = "tests/audit/validate_friction_model.py"
    before = ast.parse(h6.git_bytes(ROOT, BASE, path))
    after = ast.parse((ROOT / path).read_text())
    original = {n.name: n for n in before.body if isinstance(n, ast.FunctionDef)}
    current = {n.name: n for n in after.body if isinstance(n, ast.FunctionDef)}
    retained_before = [
        ast.dump(n)
        for n in before.body
        if not (isinstance(n, ast.FunctionDef) and n.name == "verify_history")
    ]
    retained_after = [
        ast.dump(n)
        for n in after.body
        if not (
            isinstance(n, ast.FunctionDef)
            and n.name in {"verify_history", "historical_inventory_equivalent"}
        )
    ]
    require(retained_before == retained_after, "H6_VALIDATOR_UNRELATED_CHANGE")
    require(
        set(current) == set(original) | {"historical_inventory_equivalent"}, "H6_VALIDATOR_NODE_SET"
    )
    expected = copy.deepcopy(original["verify_history"])

    class ReplaceComparison(ast.NodeTransformer):
        def visit_Compare(self, node):
            if isinstance(node.left, ast.Call) and "read_bytes" in ast.unparse(node.left):
                return ast.Call(
                    func=ast.Name(id="historical_inventory_equivalent", ctx=ast.Load()),
                    args=[ast.Name(id="path", ctx=ast.Load()), node.comparators[0], node.left],
                    keywords=[],
                )
            return self.generic_visit(node)

    expected = ReplaceComparison().visit(expected)
    require(ast.dump(expected) == ast.dump(current["verify_history"]), "H6_HISTORY_EXTENSION_ONLY")


def verify_history():
    commits = h6.history_order(ROOT, BASE, "HEAD")
    require(commits and commits[0] == FREEZE, "H7_FREEZE_NOT_FIRST")
    first = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", FREEZE], cwd=ROOT, text=True
    ).splitlines()
    require(
        set(first)
        == {
            "docs/friction_observability_receipt_contract.md",
            "docs/friction_observability_h7_plan.md",
        },
        "H7_PREIMPLEMENTATION_FREEZE",
    )
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
    ).splitlines()
    protected = 0
    for path in paths:
        if path in {".github/workflows/ci.yml", "tests/audit/validate_friction_model.py"}:
            continue
        before = h6.git_bytes(ROOT, BASE, path).replace(b"\r\n", b"\n")
        after = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        require(
            h6.historical_inventory_equivalent(path, before, after), "PRE_H7_FILE_CHANGED:" + path
        )
        protected += 1
    _historical_validator_unchanged_elsewhere()
    return {
        "protected_files": protected,
        "production_source_unchanged": True,
        "exact_inventory_extensions": list(COMPATIBILITY),
    }


def validate_synthetic_cases():
    receipt = complete()
    current = complete(11)
    cases = [("valid_linear", receipt, None, None)]

    def add(name, value, reason, previous=None):
        cases.append((name, value, previous, reason))

    add(
        "missing_q",
        replace(receipt, signals=replace(receipt.signals, q_observed=None)),
        "MISSING_Q",
    )
    add(
        "missing_raw_u",
        replace(receipt, stages=replace(receipt.stages, callback_output_raw=None)),
        "MISSING_RAW_CALLBACK_OUTPUT",
    )
    add(
        "wrong_mode",
        replace(receipt, callback_family=CallbackFamily.OTHER),
        "IDENTIFICATION_MODEL_UNSUPPORTED",
    )
    add("deadzone_interior", complete(error=0.01, q=0.0), None)
    add("positive_deadzone_boundary", complete(error=0.06, q=0.2), None)
    add("negative_deadzone_boundary", complete(error=-0.06, q=-0.2), None)
    add(
        "compensation_disabled",
        complete(error=0.5, q=0.0, compensation=False),
        "CALLBACK_FLAG_INCONSISTENT",
    )
    add(
        "saturation",
        replace(receipt, limits=replace(receipt.limits, timer_saturated=True)),
        "SATURATED",
    )
    add(
        "override",
        replace(receipt, limits=replace(receipt.limits, driver_override=True)),
        "DRIVER_OVERRIDE",
    )
    add(
        "geometry_generation_changed",
        replace(
            current,
            context=replace(
                current.context, geometry=replace(current.context.geometry, generation=4)
            ),
        ),
        "GEOMETRY_CONTEXT_CHANGED",
        receipt,
    )
    for name, field, value in (
        ("installed_F_changed", "factor_installed", 2.1),
        ("installed_C_changed", "friction_installed", 0.15),
    ):
        add(
            name,
            replace(
                current,
                context=replace(
                    current.context, installed=replace(current.context.installed, **{field: value})
                ),
            ),
            "INSTALLED_PARAMETER_CONTEXT_CHANGED",
            receipt,
        )
    source = replace(current.sources[0], source_identity=receipt.sources[0].source_identity)
    add(
        "source_timestamp_mismatch",
        replace(current, sources=(source, *current.sources[1:])),
        "SOURCE_TIMESTAMP_MISMATCH",
        receipt,
    )
    add("duplicate_cycle", receipt, "DUPLICATE_CONTROLLER_CYCLE", receipt)
    try:
        scalar(receipt.cycle, Signal.CALLBACK_OUTPUT, float("nan"), Stage.RAW_CALLBACK)
    except ValueError:
        nonfinite = True
    else:
        nonfinite = False
    require(nonfinite, "NONFINITE_FIXTURE_NOT_REJECTED")
    approximate = replace(
        receipt.stages.callback_output_raw,
        precision=Precision.FLOAT32,
        origin=ScalarOrigin.LEGACY_PUBLISHED,
    )
    add(
        "float32_approximate",
        replace(receipt, stages=replace(receipt.stages, callback_output_raw=approximate)),
        "RAW_PRECISION_UNAVAILABLE",
    )
    add(
        "nn_lite",
        replace(
            receipt,
            callback_stage=CallbackStage.NN_LITE_CALLBACK_PRE_PID,
            callback_family=CallbackFamily.NN_LITE,
        ),
        "IDENTIFICATION_MODEL_UNSUPPORTED",
    )
    add(
        "nn",
        replace(
            receipt,
            callback_stage=CallbackStage.NN_CALLBACK_PRE_PID,
            callback_family=CallbackFamily.NN,
            callback_function=CallbackFunction.NN_MODEL,
        ),
        "IDENTIFICATION_MODEL_UNSUPPORTED",
    )
    applied = scalar(
        receipt.cycle, Signal.APPLIED_TORQUE, 0.625, Stage.APPLIED_TORQUE, ScalarOrigin.DOWNSTREAM
    )
    add(
        "applied_as_callback",
        replace(receipt, stages=replace(receipt.stages, callback_output_raw=applied)),
        "WRONG_CALLBACK_STAGE",
    )
    records = []
    for name, item, previous, expected in cases:
        result = v.evaluate(item, v.ObservationPolicy(), previous=previous)
        names = [r.value for r in result.reasons]
        require((not names) if expected is None else expected in names, "SYNTHETIC_CASE:" + name)
        records.append(
            {
                "case": name,
                "status": result.status.value,
                "reasons": names,
                "receipt_sha256": item.digest,
                "expected_reason": expected,
            }
        )
    records.append(
        {
            "case": "nonfinite_raw",
            "status": "STRUCTURAL_REJECTED",
            "reasons": ["NONFINITE_INPUT"],
            "receipt_sha256": None,
            "expected_reason": "NONFINITE_INPUT",
        }
    )
    require(len(records) == 20, "SYNTHETIC_CASE_COUNT")
    return {
        "cases": 20,
        "records": records,
        "empirical_qualified": False,
        "runtime_producer_implemented": False,
    }


def check_coverage(report):
    summaries = [
        item["summary"]
        for path, item in report["files"].items()
        if "/observability/" in path.replace("\\", "/")
    ]
    total = sum(s["num_statements"] for s in summaries)
    covered = sum(s["covered_lines"] for s in summaries)
    branches = sum(s["num_branches"] for s in summaries)
    branch_covered = sum(s["covered_branches"] for s in summaries)
    require(
        total > 0
        and covered / total >= 0.98
        and branches > 0
        and branch_covered / branches >= 0.95,
        "H7_COVERAGE",
    )
    return {"statement_pct": 100 * covered / total, "branch_pct": 100 * branch_covered / branches}


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
    history = verify_history() if args.verify_history else None
    report = validate_synthetic_cases()
    print(
        json.dumps(
            {
                "H7_AUDIT_PASS": True,
                "files": len(source["files"]),
                "claims": len(source["claims"]),
                "synthetic_cases": report["cases"],
                "history": history,
                "runtime_producer_implemented": False,
                "empirical_qualified": False,
                "application_authorized": False,
            }
        )
    )


if __name__ == "__main__":
    main()
