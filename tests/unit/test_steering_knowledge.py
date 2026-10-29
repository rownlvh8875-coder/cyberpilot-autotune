"""Revision-bound explanatory catalogs; no numerical recommendation or policy."""

import pytest

REVISIONS = (
    "0e9c589c1b83027146f909a9cdc306c2c665ceaf",
    "c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
    "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
)


@pytest.mark.parametrize("revision", REVISIONS)
def test_catalog_is_exact_immutable_steering_only_and_source_separated(revision):
    from cyberpilot_autotune.knowledge.contracts import STEERING_IDS
    from cyberpilot_autotune.knowledge.steering import get_registry

    r = get_registry(revision)
    assert r.source_revision == revision
    assert {p.parameter_id for p in r.parameters} == STEERING_IDS
    assert tuple(p.parameter_id for p in r.parameters) == tuple(sorted(STEERING_IDS))
    assert all(c.exact_revision == revision for c in r.claims)
    assert all(p.source_revision == revision for p in r.parameters)
    assert r.get_any("CarSelected3") is r.get_any("CruiseMaxVals1") is None
    assert len({c.claim_id for c in r.claims}) == len(r.claims)


def test_source_selection_never_guesses_latest_or_promotes_current_upstream():
    from cyberpilot_autotune.knowledge.steering import get_registry

    with pytest.raises(TypeError):
        get_registry()
    for revision in ("carrot-wip", "hoya/c3-atune", "c213073", "1" * 40):
        assert get_registry(revision) is None
    values = [get_registry(r).get_any("SteerRatioRate") for r in REVISIONS]
    assert len({p.digest for p in values}) == 3
    assert "MEB" in " ".join(values[0].mode_conditions)
    assert values[0].consumer_transform_description != values[1].consumer_transform_description


@pytest.mark.parametrize("revision", REVISIONS)
def test_preserved_offset_and_mode_selector_are_not_tuning_targets(revision):
    from cyberpilot_autotune.knowledge.contracts import Classification
    from cyberpilot_autotune.knowledge.steering import get_registry

    r = get_registry(revision)
    offset = r.get_any("liveTorqueParameters.latAccelOffset")
    assert offset.classification is Classification.COUPLED_PRESERVED_STATE
    assert offset.storage_key is offset.ui_default is offset.storage_registry_default is None
    assert offset.runtime_field == "liveTorqueParameters.latAccelOffsetFiltered"
    assert offset.canonical_unit is None
    assert r.get_proven(offset.parameter_id) is None
    mode = r.get_proven("LateralTorqueCustom")
    assert mode.classification is Classification.MODE_SELECTOR
    assert mode.ui_default == 1 and mode.storage_registry_default == 0


@pytest.mark.parametrize("revision", REVISIONS)
def test_known_scales_do_not_resolve_application_units_or_use_ui_labels(revision):
    from cyberpilot_autotune.knowledge.steering import get_registry

    r = get_registry(revision)
    for name in ("LateralTorqueAccelFactor", "LateralTorqueFriction"):
        p = r.get_any(name)
        assert p.storage_scale == 0.001
        assert "UNRESOLVED_UNIT_EQUIVALENCE" in p.evidence_gaps
        assert r.get_proven(name) is None
    kf = r.get_proven("LateralTorqueKf")
    assert kf.storage_scale == 0.01
    assert "0.001" in kf.ui_unit_description
    assert "UI_LABEL_SCALE_MISMATCH" in kf.evidence_gaps
    delay = r.get_proven("SteerActuatorDelay")
    assert delay.ui_default == 30 and delay.storage_registry_default == 0
    assert delay.canonical_unit == "s"
    assert "liveDelay" in delay.consumer_transform_description


def test_compatibility_evidence_does_not_change_pinned_catalogs():
    from cyberpilot_autotune.knowledge.contracts import Confidence
    from cyberpilot_autotune.knowledge.steering import get_registry

    for revision in REVISIONS:
        r = get_registry(revision)
        assert sum(p.evidence_status is Confidence.PROVEN for p in r.parameters) == 6
        for p in r.parameters:
            assert p.descriptive_owner
            assert p.consumer_claim_ids
            assert all(c for c in r.claims if c.claim_id in p.consumer_claim_ids)


def test_mode_ownership_and_offset_nonuse_claims_have_direct_consumer_evidence():
    from cyberpilot_autotune.knowledge.steering import get_registry

    for revision in REVISIONS:
        r = get_registry(revision)
        mode = r.get_any("LateralTorqueCustom")
        offset = r.get_any("liveTorqueParameters.latAccelOffset")
        assert any(
            c.claim_id.endswith(":live-tuple")
            and c.claim_id in mode.consumer_claim_ids
            and mode.parameter_id in c.parameter_ids
            for c in r.claims
        )
        assert any(
            c.claim_id.endswith(":linear")
            and c.claim_id in offset.consumer_claim_ids
            and offset.parameter_id in c.parameter_ids
            for c in r.claims
        )
        assert any(
            c.claim_id.endswith(":nn")
            and c.claim_id in offset.consumer_claim_ids
            and offset.parameter_id in c.parameter_ids
            for c in r.claims
        )


def test_custom_selector_getter_is_integer_separate_from_float_coefficients():
    from cyberpilot_autotune.knowledge.steering import get_registry

    for revision in REVISIONS:
        registry = get_registry(revision)
        assert "Params.get_int" in registry.get_proven("LateralTorqueCustom").consumer_value_source
        assert "Params.get_float" in registry.get_proven("LateralTorqueKpV").consumer_value_source
