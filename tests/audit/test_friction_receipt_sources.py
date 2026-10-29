"""Exact callback/PID provenance cannot drift or acquire runtime authority."""

import copy
import json
from pathlib import Path

import pytest

from tests.audit import validate_friction_receipt as audit

ROOT = Path(__file__).resolve().parents[2]


def test_h7_source_schema_history_and_protected_base_reproduce():
    manifest = json.loads((ROOT / audit.SOURCE_PATH).read_text())
    audit.validate_sources(manifest)
    assert audit.verify_history()["production_source_unchanged"]
    report = audit.validate_synthetic_cases()
    assert report["cases"] == 20
    assert not report["empirical_qualified"]


@pytest.mark.parametrize(
    "change", ["revision", "range", "hash", "missing", "authority", "schema", "freeze"]
)
def test_source_manifest_mutations_reject(change):
    manifest = copy.deepcopy(json.loads((ROOT / audit.SOURCE_PATH).read_text()))
    if change == "revision":
        manifest["files"][0]["revision"] = "main"
    elif change == "range":
        manifest["claims"][0]["start"] = 0
    elif change == "hash":
        manifest["files"][0]["sha256"] = "0" * 64
    elif change == "missing":
        manifest["claims"].pop()
    elif change == "authority":
        manifest["runtime_producer_implemented"] = True
    elif change == "schema":
        manifest["neutral_schema_sha256"] = "0" * 64
    else:
        manifest["freeze_commit"] = manifest["base"]
    with pytest.raises(ValueError):
        audit.validate_sources(manifest)


def test_coverage_checks_independent_statement_and_branch_floors():
    for lines, branches, passes in ((98, 95, True), (97, 100, False), (100, 94, False)):
        report = {
            "files": {
                "src/cyberpilot_autotune/observability/contracts.py": {
                    "summary": {
                        "num_statements": 100,
                        "covered_lines": lines,
                        "num_branches": 100,
                        "covered_branches": branches,
                    }
                }
            }
        }
        if passes:
            audit.check_coverage(report)
        else:
            with pytest.raises(ValueError):
                audit.check_coverage(report)


def test_callback_source_ast_rejects_wrong_a_error_or_compensation_without_execution():
    raw = b"""raise RuntimeError("never execute this file")
gravity_adjusted_lateral_accel = desired_lateral_accel - roll_compensation
error = desired_lateral_accel - actual_lateral_accel
friction_input = error
ff = self.torque_from_lateral_accel(
  LatControlInputs(gravity_adjusted_lateral_accel, roll_compensation, CS.vEgo, CS.aEgo),
  self.torque_params, friction_input, lateral_accel_deadzone,
  friction_compensation=True, gravity_adjusted=True)
"""
    audit.check_callback_fragments(raw)
    for old, new in (
        (
            b"desired_lateral_accel - actual_lateral_accel",
            b"desired_lateral_accel + actual_lateral_accel",
        ),
        (b"desired_lateral_accel - roll_compensation", b"actual_lateral_accel - roll_compensation"),
        (b"friction_compensation=True", b"friction_compensation=False"),
    ):
        with pytest.raises(ValueError):
            audit.check_callback_fragments(raw.replace(old, new))


def test_consumed_source_ast_pins_local_builder_wire_state_and_fallback_without_execution():
    raw = b"""raise RuntimeError("never execute this file")
def state_control(self):
  CS = self.sm['carState']
  lp = self.sm['liveParameters'] if lateral_ready else lateral_vehicle_parameters(self.sm, self.CP)
  CC = car.CarControl.new_message()
  steer, angle, log = self.LaC.update(CC.latActive, CS, self.VM, lp, limited, desired, CC, limited)
def publish(self, CC):
  dat = messaging.new_message('controlsState')
  self.pm.send('controlsState', dat)
  cc_send = messaging.new_message('carControl')
  cc_send.carControl = CC
  self.pm.send('carControl', cc_send)
"""
    audit.check_consumed_source_fragments(raw)
    for old, new in (
        (b"CS = self.sm['carState']", b"CS = car.CarState.new_message()"),
        (b"CC = car.CarControl.new_message()", b"CC = self.sm['carControl']"),
        (b"desired, CC, limited", b"desired, self.sm['carControl'], limited"),
        (b"cc_send.carControl = CC", b"cc_send.carControl = other"),
        (b"lateral_vehicle_parameters(self.sm, self.CP)", b"other(self.sm, self.CP)"),
        (
            b"self.pm.send('controlsState', dat)\n  cc_send = messaging.new_message('carControl')",
            b"cc_send = messaging.new_message('carControl')\n  self.pm.send('controlsState', dat)",
        ),
    ):
        with pytest.raises(ValueError):
            audit.check_consumed_source_fragments(raw.replace(old, new))
