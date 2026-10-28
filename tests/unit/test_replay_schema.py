"""Strict pre-execution admission of explicit synthetic replay documents."""

import json
from dataclasses import FrozenInstanceError, replace
from importlib import import_module

import pytest

from cyberpilot_autotune.contracts import ValidationError
from tests.fixtures.replay_data import replay_document, replay_event


def load(document):
    return import_module("cyberpilot_autotune.replay").load_replay(json.dumps(document))


def test_valid_schema_preserves_explicit_units_activity_and_unavailable_signals():
    scenario = load(replay_document())
    assert scenario.schema_version == 1
    assert len(scenario.events) == 3
    assert scenario.events[0].observation.control_active is True
    assert scenario.events[0].observation.lateral_acceleration_mps2 is None
    assert scenario.units["speed_mps"] == "m/s"


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), 2),
        (("schema_version",), True),
        (("scope",), "VEHICLE_LOG"),
        (("learner_version",), "unknown"),
        (("time_domain",), "wall-clock-utc"),
        (("monotonic_origin_s",), -1),
        (("monotonic_origin_s",), 11),
        (("units", "speed_mps"), "km/h"),
        (("parameter_spec", "parameter_id"), "vehicle.gain"),
        (("parameter_spec", "out_of_range_policy"), "CLIP"),
        (("parameter_spec", "persistence_eligible"), True),
        (("baseline_parameters",), {"unknown": 10}),
        (("gate_config", "minimum_speed_mps"), 0.5),
        (("learner_config", "alpha"), 0),
        (("events",), []),
        (("events",), {}),
    ],
)
def test_unknown_scope_version_units_policy_and_invalid_configuration_rejected(path, value):
    document = replay_document()
    target = document
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        load(document)


@pytest.mark.parametrize("part", [None, "gate_config", "learner_config", "parameter_spec", "units"])
def test_unknown_and_missing_keys_are_not_ignored(part):
    document = replay_document()
    target = document if part is None else document[part]
    target["unknown_metadata"] = "not admitted"
    with pytest.raises(ValidationError):
        load(document)
    del target["unknown_metadata"]
    del target[next(iter(target))]
    with pytest.raises(ValidationError):
        load(document)


@pytest.mark.parametrize(
    "changes",
    [
        {"control_active": "enabled"},
        {"speed_mps": float("nan")},
        {"desired_curvature_inv_m": float("inf")},
        {"source_age_s": -1},
        {"sequence": True},
        {"context_key": "driver/identity"},
    ],
)
def test_invalid_observation_contracts_fail_before_execution(changes):
    document = replay_document()
    document["events"][0]["observation"].update(changes)
    with pytest.raises(ValidationError):
        load(document)


def test_events_and_observations_require_exact_keys_and_explicit_activity():
    for section, key in [("observation", "control_active"), (None, "clock_before_s")]:
        document = replay_document()
        target = document["events"][0]
        if section:
            target = target[section]
        del target[key]
        with pytest.raises(ValidationError):
            load(document)
    document = replay_document()
    document["events"][0]["observation"]["vin"] = "not a permitted field"
    with pytest.raises(ValidationError):
        load(document)


@pytest.mark.parametrize("mutation", ["sequence", "timestamp", "clock", "after", "origin"])
def test_reordering_or_inconsistent_clock_domains_rejected(mutation):
    document = replay_document()
    event = document["events"][1]
    if mutation == "sequence":
        event["observation"]["sequence"] = 0
    elif mutation == "timestamp":
        event["observation"]["timestamp_s"] = 10
    elif mutation == "clock":
        event["clock_before_s"] = 9
    elif mutation == "after":
        event["clock_after_s"] = 10
    else:
        event["clock_before_s"] = -1
    with pytest.raises(ValidationError):
        load(document)


def test_runtime_veto_inputs_remain_valid_synthetic_fixture_data():
    document = replay_document()
    document["events"] = [
        replay_event(0, source_age_s=2, control_active=None),
        replay_event(1, source_valid=False),
        replay_event(2, timestamp_s=20),
    ]
    scenario = load(document)
    assert scenario.events[0].observation.control_active is None
    assert scenario.events[2].observation.timestamp_s == 20


@pytest.mark.parametrize(
    "raw",
    ["{}", "null", "[]", "{", '{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'],
)
def test_malformed_duplicate_or_nonfinite_json_rejected(raw):
    with pytest.raises(ValidationError):
        import_module("cyberpilot_autotune.replay").load_replay(raw)


def test_resource_caps_and_overflow_exponents_fail_closed():
    module = import_module("cyberpilot_autotune.replay")
    with pytest.raises(ValidationError):
        module.load_replay(" " * (256 * 1024 + 1))
    document = replay_document()
    document["events"] = [replay_event(i) for i in range(1001)]
    with pytest.raises(ValidationError):
        load(document)
    raw = json.dumps(replay_document()).replace('"speed_mps": 2.0', '"speed_mps": 1e999')
    with pytest.raises(ValidationError):
        module.load_replay(raw)


@pytest.mark.parametrize("coordinate", ["origin", "capture", "before", "after"])
def test_clock_integers_that_lose_precision_in_engine_are_rejected(coordinate):
    document = replay_document()
    document["monotonic_origin_s"] = 2**53
    for i, event in enumerate(document["events"]):
        exact = 2**53 + 4 * (i + 1)
        event["observation"]["timestamp_s"] = exact
        event["clock_before_s"] = event["clock_after_s"] = exact
    if coordinate == "origin":
        document["monotonic_origin_s"] += 1
    elif coordinate == "capture":
        document["events"][0]["observation"]["timestamp_s"] += 1
    elif coordinate == "before":
        document["events"][0]["clock_before_s"] -= 1
    else:
        document["events"][0]["clock_after_s"] += 1
    with pytest.raises(ValidationError, match="losslessly"):
        load(document)


def test_lossless_large_integer_clock_boundary_remains_admitted():
    document = replay_document()
    document["monotonic_origin_s"] = 2**53
    for i, event in enumerate(document["events"], start=1):
        exact = 2**53 + 2 * i
        event["observation"]["timestamp_s"] = exact
        event["clock_before_s"] = event["clock_after_s"] = exact
    from cyberpilot_autotune.replay import run_replay

    report = run_replay(load(document))
    assert report.summary.rejection_counts == {}
    assert report.summary.eligible_count == 1
    assert report.software_checks_passed


def test_scenario_is_frozen_and_defensively_copies_nested_input():
    scenario = load(replay_document())
    baseline = {"synthetic.test_only": 10.0}
    copied = replace(scenario, baseline_parameters=baseline)
    baseline["synthetic.test_only"] = 99
    assert copied.baseline_parameters["synthetic.test_only"] == 10
    with pytest.raises(TypeError):
        scenario.units["speed_mps"] = "km/h"
    with pytest.raises(TypeError):
        scenario.events[0].observation.baseline_parameters["synthetic.test_only"] = 99
    with pytest.raises(FrozenInstanceError):
        scenario.schema_version = 2


def test_canonical_encoding_has_exact_float_integer_and_rational_types():
    from fractions import Fraction

    canonical = import_module("cyberpilot_autotune.replay.canonical").canonical_bytes
    assert canonical({"value": 0.5, "count": 3}) == (
        b'{"count":3,"value":{"float64":"0x1.0000000000000p-1"}}'
    )
    assert canonical(Fraction(3, 2)) == b'{"rational":["3","2"]}'
    assert canonical(-0.0) != canonical(0.0)
    assert canonical(2**53 + 1) == b"9007199254740993"
    for invalid in [float("nan"), float("inf"), object(), {1: "bad key"}]:
        with pytest.raises(ValidationError):
            canonical(invalid)
