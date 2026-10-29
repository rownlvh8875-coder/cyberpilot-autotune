"""Reject malformed evidence rather than inventing defaults or observed trust."""

import importlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.native_containment import synthetic_case


def api():
    # A failing assertion (not a collection error) demonstrates the absent API first.
    module = importlib.util.find_spec("compatibility.native_containment")
    assert module is not None, "synthetic containment contract is not implemented"
    return importlib.import_module("compatibility.native_containment.contracts")


def test_valid_case_is_recursively_immutable_and_defensively_copied():
    contract = api()
    raw = synthetic_case()
    case = contract.parse_synthetic_case(json.dumps(raw))
    events = list(case.events)
    flags = list(case.events[0].flags)
    event = replace(case.events[0], flags=flags)
    copied = replace(case, events=events)
    flags.append("O_PATH")
    events.clear()
    assert event.flags == ("O_CLOEXEC", "O_RDWR")
    assert len(copied.events) == 1
    with pytest.raises(FrozenInstanceError):
        case.actor_id = "other"
    with pytest.raises(FrozenInstanceError):
        case.modeled_proofs.trace_complete = False
    with pytest.raises(FrozenInstanceError):
        case.events[0].effect_observed = True


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "v2"),
        ("evidence_kind", "OBSERVED"),
        ("source_cohort_digest", "A" * 64),
        ("actor_id", ""),
        ("process_generation", True),
        ("exec_generation", -1),
        ("exec_generation", 2**64),
        ("clock_domain", "wall-clock"),
        ("successful_prohibited_handles", False),
        ("successful_prohibited_effects", 1.5),
        ("cpu_backend", "GPU"),
        ("events", []),
        ("events", {}),
        ("candidate_generation_allowed", True),
        ("runtime_accepted", 0),
    ],
)
def test_invalid_root_fields_are_rejected(field, value):
    raw = synthetic_case()
    raw[field] = value
    with pytest.raises(ValueError):
        api().parse_synthetic_case(json.dumps(raw))


@pytest.mark.parametrize(
    "field,value",
    [
        ("sequence", True),
        ("sequence", -1),
        ("mono_time_ns", 2**64),
        ("process_generation", None),
        ("exec_generation", 1.0),
        ("actor_id", ""),
        ("clock_domain", 3),
        ("operation_class", "STAT"),
        ("requested_endpoint", 0),
        ("flags", ["O_RDWR", "O_RDWR"]),
        ("flags", "O_RDWR"),
        ("flags", [0]),
        ("resolved_kind", "ABSENT"),
        ("resolution_bound", 0),
        ("result_known", 1),
        ("errno_name", False),
        ("fd_created_or_imported", 0),
        ("effect_observed", 1),
    ],
)
def test_invalid_event_scalars_are_rejected(field, value):
    raw = synthetic_case()
    raw["events"][0][field] = value
    with pytest.raises(ValueError):
        api().parse_synthetic_case(json.dumps(raw))


@pytest.mark.parametrize("location", ["root", "proof", "event"])
@pytest.mark.parametrize("mutation", ["missing", "unknown", "duplicate"])
def test_exact_keys_at_every_level(location, mutation):
    raw = synthetic_case()
    obj = {"root": raw, "proof": raw["modeled_proofs"], "event": raw["events"][0]}[location]
    key = next(iter(obj))
    if mutation == "missing":
        del obj[key]
    elif mutation == "unknown":
        obj["unrecognized"] = None
    encoded = json.dumps(raw)
    if mutation == "duplicate":
        needle = json.dumps(key) + ": " + json.dumps(obj[key])
        encoded = encoded.replace(needle, needle + ", " + needle, 1)
    with pytest.raises(ValueError):
        api().parse_synthetic_case(encoded)


@pytest.mark.parametrize("raw", ["null", "[]", "{", "NaN", "Infinity", "-Infinity"])
def test_invalid_json_shapes_and_nonfinite_rejected(raw):
    with pytest.raises(ValueError):
        api().parse_synthetic_case(raw)


def test_direct_constructors_cannot_bypass_scalar_validation():
    contract = api()
    case = contract.parse_synthetic_case(json.dumps(synthetic_case()))
    for fields in (
        {"evidence_kind": "OBSERVED"},
        {"process_generation": True},
        {"events": []},
        {"modeled_proofs": {}},
        {"runtime_accepted": True},
    ):
        with pytest.raises(ValueError):
            replace(case, **fields)
    with pytest.raises(ValueError):
        replace(case.events[0], result_known=1)
    with pytest.raises(ValueError):
        replace(case.modeled_proofs, observer_intact=1)


def test_canonical_digest_preserves_unknown_and_source_generation_identity():
    contract = api()
    raw = synthetic_case()

    def digest(value):
        return contract.canonical_digest(contract.parse_synthetic_case(json.dumps(value)))

    base = digest(raw)
    assert len(base) == 64
    assert base == digest(dict(reversed(list(raw.items()))))
    raw["events"][0]["flags"].reverse()
    assert base == digest(raw)
    for key, value in [
        ("source_cohort_digest", "b" * 64),
        ("exec_generation", 3),
        ("successful_prohibited_handles", None),
    ]:
        changed = synthetic_case()
        changed[key] = value
        assert base != digest(changed)
    changed = synthetic_case()
    changed["events"][0]["effect_observed"] = None
    assert base != digest(changed)
