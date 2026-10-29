"""Close PR18-M1 against actual pinned bodies, not a duplicate latch model."""

import hashlib
import importlib
import json
import os
from pathlib import Path

import pytest

from compatibility.friction_native import bundle
from compatibility.friction_native.test_controls import schemas as schemas
from compatibility.friction_native.test_controls import source as source


def harness():
    assert (bundle.ROOT / "compatibility/friction_native/custom_cohort.py").is_file(), (
        "CUSTOM_COHORT_HARNESS_MISSING"
    )
    return importlib.import_module("compatibility.friction_native.custom_cohort")


def test_custom_cohort_harness_is_present():
    harness()


@pytest.fixture(scope="module")
def callback():
    return harness().load_callback(Path(os.environ["FRICTION_NATIVE_REFERENCE"]))


def expected(frame, selector):
    """Hand-derived literal cohort oracle, not baseline output or harness logic."""
    if frame < 10:
        return 0, (2.5, 0.125, 0.0625), (0.125, 0.0625, 0.03125, 0.5)
    if frame < 20:
        return selector, (1.75, 0.125, 0.03125), (0.25, 0.125, 0.0625, 0.5)
    if frame < 30:
        return selector, (2.0, 0.25, 0.03125), (0.5, 0.25, 0.125, 0.75)
    if frame == 30:
        # Actual condition is previous selector>1, despite comment "1 -> 0".
        installed = (2.0, 0.25, 0.03125) if selector == 1 else (2.0, 0.0625, 0.03125)
        return 0, installed, (0.5, 0.25, 0.125, 0.75)
    return 0, (3.0, 0.1875, 0.125), (0.5, 0.25, 0.125, 0.75)


def assert_cohorts(result, selector, family, *, receipts=True, freeze=False):
    installed_epoch = gain_epoch = -1
    previous_installed = previous_gains = None
    for step in result["steps"]:
        latched, installed, gains = expected(step["frame"], selector)
        assert step["selector"] == latched, "LATCH_COHORT"
        assert step["installed"] == installed, "INSTALLED_COHORT"
        assert step["gains"] == gains, "GAIN_COHORT"
        assert len(step["calls"]) == (3 if step["active"] else 0), "CALLBACK_COUNT"
        assert all(call["installed"] == installed for call in step["calls"]), (
            "CALLBACK_CONSUMED_COHORT"
        )
        if step["active"]:
            assert step["pid_values"][3] == step["calls"][-1]["raw"] * gains[3], "PID_F_STAGE"
        assert step["live_accepted"] == (step["frame"] <= 10 or step["frame"] == 31), "LIVE_BYPASS"
        if not step["active"] or not receipts:
            assert step["receipt"] is None
            continue
        payload = step["receipt"].payload
        actual = payload["context"]["installed"]
        assert (
            actual["factor_installed"],
            actual["friction_installed"],
            actual["offset_installed"],
        ) == installed, "RECEIPT_INSTALLED_COHORT"
        assert actual["custom_selector"] == latched, "RECEIPT_SELECTOR"
        assert payload["controller_mode"] == ("CUSTOM" if latched else "STANDARD")
        assert payload["callback_family"] == family
        assert payload["signals"].get("q_observed") is None
        assert payload["stages"]["callback_output_raw"]["value"] == step["calls"][-1]["raw"]
        assert payload["stages"]["pid_f"]["value"] == step["pid_values"][3]
        observed_gains = payload["context"]["gains"]
        assert tuple(observed_gains[key] for key in ("k_p", "k_i", "k_d", "k_f")) == (
            gains[0],
            None if freeze else gains[1],
            gains[2],
            gains[3],
        ), "RECEIPT_GAIN_COHORT"
        installed_key = (latched, *installed)
        installed_epoch += installed_key != previous_installed
        gain_epoch += gains != previous_gains
        previous_installed, previous_gains = installed_key, gains
        assert actual["generation"] == installed_epoch, "INSTALLED_EPOCH"
        assert payload["cycle"]["installed_parameter_generation"] == installed_epoch
        assert observed_gains["generation"] == (None if freeze else gain_epoch), "GAIN_EPOCH"
        assert payload["cycle"]["controller_cycle_id"] == step["frame"]
        assert payload["consumption_manifest_complete"] is False


@pytest.mark.parametrize("selector", [1, 2, 3])
@pytest.mark.parametrize("family", ["LINEAR", "NN_LITE"])
@pytest.mark.parametrize("kind", ["absent", "disabled", "enabled", "failing"])
def test_continuous_custom_latch_refresh_exit_and_live_recovery(
    source, schemas, callback, selector, family, kind
):
    suite = harness()
    before = suite.run(
        source[0],
        callback,
        selector=selector,
        family=family,
        observer_kind="absent",
        schemas=schemas[0],
    )
    after = suite.run(
        source[1],
        callback,
        selector=selector,
        family=family,
        observer_kind=kind,
        schemas=schemas[1],
    )
    suite.assert_parity(before, after)
    assert_cohorts(before, selector, family, receipts=False)
    assert_cohorts(after, selector, family, receipts=kind == "enabled")
    keys = (
        "LateralTorqueAccelFactor",
        "LateralTorqueFriction",
        "LateralTorqueKpV",
        "LateralTorqueKiV",
        "LateralTorqueKf",
        "LateralTorqueKd",
    )
    want = [(10, "int", "LateralTorqueCustom")]
    want += [(10, "float", key) for key in keys]
    want += [(20, "int", "LateralTorqueCustom")]
    want += [(20, "float", key) for key in keys]
    want += [(30, "int", "LateralTorqueCustom")]
    assert [(frame, method, key) for frame, method, key, _ in after["settings_reads"]] == want


@pytest.mark.parametrize("selector", [1, 2])
@pytest.mark.parametrize("family", ["LINEAR", "NN_LITE"])
@pytest.mark.parametrize("inactive", [(10,), (20,), (30,), (10, 20, 30)])
def test_inactive_latch_cycles_change_context_without_inventing_a_callback_receipt(
    source, schemas, callback, selector, family, inactive
):
    suite = harness()
    before = suite.run(
        source[0],
        callback,
        selector=selector,
        family=family,
        observer_kind="absent",
        schemas=schemas[0],
        inactive=inactive,
    )
    after = suite.run(
        source[1],
        callback,
        selector=selector,
        family=family,
        observer_kind="enabled",
        schemas=schemas[1],
        inactive=inactive,
    )
    suite.assert_parity(before, after)
    assert_cohorts(after, selector, family)
    for frame in inactive:
        assert after["steps"][frame - 1]["calls"] == ()
        assert after["steps"][frame - 1]["output_bits"][0] == suite.bits(-0.0)


@pytest.mark.parametrize("selector", [1, 2])
@pytest.mark.parametrize("family", ["LINEAR", "NN_LITE"])
def test_driver_override_keeps_exact_installed_gains_but_skipped_ki_unavailable(
    source, schemas, callback, selector, family
):
    suite = harness()
    before = suite.run(
        source[0],
        callback,
        selector=selector,
        family=family,
        observer_kind="absent",
        schemas=schemas[0],
        freeze=True,
    )
    after = suite.run(
        source[1],
        callback,
        selector=selector,
        family=family,
        observer_kind="enabled",
        schemas=schemas[1],
        freeze=True,
    )
    suite.assert_parity(before, after)
    assert_cohorts(after, selector, family, freeze=True)


@pytest.mark.parametrize("index", [0, 1])
def test_original_settings_failure_at_latch_is_not_swallowed(source, schemas, callback, index):
    suite = harness()
    with pytest.raises(suite.SettingsFailure, match="synthetic setting failure"):
        suite.run(
            source[index],
            callback,
            selector=2,
            family="LINEAR",
            observer_kind="enabled" if index else "absent",
            schemas=schemas[index],
            fail_at=10,
        )


@pytest.mark.parametrize(
    "mutation,selector,reason",
    [
        ("cadence", 2, "CONTROL_PARITY|SETTINGS_READ_PARITY"),
        ("reset", 1, "CONTROL_PARITY"),
        ("live_bypass", 2, "CONTROL_PARITY"),
        ("extra_read", 2, "SETTINGS_READ_PARITY"),
        ("installed_capture", 2, "RECEIPT_INSTALLED_COHORT"),
        ("gain_capture", 2, "RECEIPT_GAIN_COHORT"),
    ],
)
def test_in_memory_mutants_are_rejected_by_real_parity_or_literal_cohort_oracle(
    source, schemas, callback, mutation, selector, reason
):
    suite = harness()
    mutant = suite.mutate(source[1], mutation)
    before = suite.run(
        source[0],
        callback,
        selector=selector,
        family="LINEAR",
        observer_kind="absent",
        schemas=schemas[0],
    )
    after = suite.run(
        mutant,
        callback,
        selector=selector,
        family="LINEAR",
        observer_kind="enabled",
        schemas=schemas[1],
    )
    with pytest.raises(AssertionError, match=reason):
        suite.assert_parity(before, after)
        assert_cohorts(after, selector, "LINEAR")


def test_custom_evidence_is_present_and_all_source_ranges_are_exact():
    path = bundle.ROOT / "docs/evidence/carrot_custom_torque_cohort_parity.json"
    assert path.is_file(), "CUSTOM_COHORT_EVIDENCE_MISSING"
    evidence = json.loads(path.read_text())
    reference = Path(os.environ["FRICTION_NATIVE_REFERENCE"])
    for entry in evidence["sources"]:
        raw = bundle.git_bytes(reference, entry["path"])
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        assert (
            hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            == entry["blob_sha"]
        )
        for span in entry["ranges"]:
            selected = b"".join(raw.splitlines(keepends=True)[span["start"] - 1 : span["end"]])
            assert hashlib.sha256(selected).hexdigest() == span["sha256"]
    registration = json.loads(
        (bundle.ROOT / "docs/evidence/carrot_passive_native_registration.json").read_text()
    )
    assert evidence["native_applied_tree"] == registration["native_applied_tree"]
    assert evidence["offline_candidate_revision"] == registration["offline_candidate_revision"]
    assert (
        evidence["patch_sha256"]
        == hashlib.sha256((bundle.ASSETS / "instrumentation.patch").read_bytes()).hexdigest()
        == registration["patch_sha256"]
    )
    assert evidence["native_patch_changed"] is False
    for field in (
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    ):
        assert evidence[field] is False


@pytest.mark.parametrize("selector", [1, 2, 3])
def test_evidence_checkpoints_match_actual_consumed_installed_context(
    source, schemas, callback, selector
):
    path = bundle.ROOT / "docs/evidence/carrot_custom_torque_cohort_parity.json"
    assert path.is_file(), "CUSTOM_COHORT_EVIDENCE_MISSING"
    evidence = json.loads(path.read_text())
    suite = harness()
    result = suite.run(
        source[1],
        callback,
        selector=selector,
        family="LINEAR",
        observer_kind="enabled",
        schemas=schemas[1],
    )
    rows = evidence["checkpoints"]["selector1" if selector == 1 else "selector_ge2"]
    for row in rows:
        step = result["steps"][row["frame"] - 1]
        assert step["installed"] == tuple(row["installed_factor_friction_offset"])
        assert step["gains"] == tuple(row["gains_kp_ki_kd_kf"])
        assert step["selector"] == (selector if row["custom_latched"] else 0)


def test_changed_callback_source_rejects_before_loading_any_native_code(monkeypatch):
    suite = harness()
    monkeypatch.setattr(bundle, "git_bytes", lambda *args: b"changed source")
    with pytest.raises(ValueError, match="EXACT_CALLBACK_SOURCE_REQUIRED"):
        suite.load_callback(Path("synthetic-unused-input"))
