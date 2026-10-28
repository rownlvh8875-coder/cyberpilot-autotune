"""Inspect pinned source syntax without importing a CarState/Params/CAN implementation."""

import ast
import json
import os
from pathlib import Path


def test_qualified_assignment_runs_before_every_normal_hyundai_return():
    reference = Path(os.environ["CARROT_REFERENCE_CHECKOUT"])
    tree = ast.parse((reference / "opendbc_repo/opendbc/car/hyundai/carstate.py").read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CarState")
    for name, line, end, torque in (
        ("update", 552, 696, "MDPS12"),
        ("update_canfd", 1396, 1625, "MDPS"),
    ):
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        # Both assignments are directly in the function body, outside conditions.
        assignment = next(n for n in fn.body if isinstance(n, ast.Assign) and n.lineno == line)
        assert ast.unparse(assignment.targets[0]) == "ret.steeringPressed"
        assert isinstance(assignment.value, ast.Call)
        assert ast.unparse(assignment.value.func) == "self.update_steering_pressed"
        assert assignment.value.args[1].value == 5
        assert ast.unparse(assignment.value.args[0]) == (
            "abs(ret.steeringTorque) > self.params.STEER_THRESHOLD"
        )
        returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
        normal = [n for n in returns if isinstance(n.value, ast.Name) and n.value.id == "ret"]
        assert [n.lineno for n in normal] == [end]
        torque_assignment = next(
            n for n in fn.body if isinstance(n, ast.Assign) and n.lineno == line - 2
        )
        assert torque in ast.unparse(torque_assignment.value)
    dispatch = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "update")
    canfd_if = next(n for n in dispatch.body if isinstance(n, ast.If) and n.lineno == 506)
    assert ast.unparse(canfd_if.test) == "self.CP.flags & HyundaiFlags.CANFD"
    assert ast.unparse(canfd_if.body[0].value.func) == "self.update_canfd"


def test_runtime_unconfirmed_evidence_never_claims_vehicle_qualification():
    evidence = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/evidence/hyundai_santafe_override_capability.json"
        ).read_text()
    )
    assert evidence["source_status"] == "SOURCE_PLATFORM_QUALIFIED"
    assert evidence["runtime_status"] == "RUNTIME_FINGERPRINT_UNCONFIRMED"
    assert evidence["santa_fe"]["canfd"] is False
    assert evidence["runtime_contract"]["no_actual_carparams_reader"] is True
