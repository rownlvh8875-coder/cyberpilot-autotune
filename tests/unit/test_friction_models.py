"""Behavioral contracts: wrong sign/stage, latent q and mixed epochs must not pass."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cyberpilot_autotune.research.friction_model import candidates, contracts, geometry, synthetic


def context(**changes):
    base = contracts.SteeringGeometryContext(
        source_revision=contracts.CURRENT,
        vehicle_context_digest="a" * 64,
        wheelbase=2.73,
        center_to_front=1.1739,
        center_to_front_ratio=0.43,
        steer_ratio_effective=14.7,
        stiffness_factor=0.95,
        controller_mode="LINEAR_TORQUE",
        geometry_generation=1,
        snapshot_time_ns=100,
        cohort="toy-cohort-1",
        geometry_source="APPLIED_VM",
        steer_ratio_rate=100.0,
        custom_sr=0.0,
        delay_source="LIVE_DELAY",
        effective_delay_s=0.2,
        custom_torque_mode=0,
        factor_installed=2.4,
        friction_installed=0.17,
    )
    return replace(base, **changes)


def rows(**changes):
    return synthetic.generate(synthetic.Scenario(**changes), context())


@pytest.mark.parametrize("family", ["controller", "inverse", "branch", "explicit"])
def test_four_models_recover_synthetic_coefficient_with_correct_inverse_sign(family):
    result = candidates.fit(rows(), family)
    assert result.friction == pytest.approx(0.17, abs=1e-10)
    if family == "explicit":
        assert result.status == "IMPLEMENTED_COEFFICIENT_CONSISTENCY_ONLY"
        assert result.factor is None
    else:
        assert result.status == "CONDITIONALLY_IDENTIFIABLE_SYNTHETIC_ONLY"
        assert result.factor == pytest.approx(2.4, abs=1e-10)


@pytest.mark.parametrize("family", ["controller", "inverse", "branch"])
def test_zero_friction_and_nonzero_bias_are_not_confused(family):
    result = candidates.fit(rows(friction=0.0, offset=0.19), family)
    assert result.friction == pytest.approx(0, abs=1e-10)
    assert result.factor == pytest.approx(2.4)


@pytest.mark.parametrize("family", ["controller", "inverse", "branch"])
def test_known_factor_is_distinct_from_joint_unknown_factor(family):
    result = candidates.fit(rows(), family, factor=2.4)
    assert result.factor == 2.4
    assert result.friction == pytest.approx(0.17)
    assert candidates.fit(rows(), family, factor=0).status == "INVALID_FACTOR_CONTEXT"


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        ({"state": "deadzone"}, "FRICTION_UNOBSERVABLE_IN_DEADZONE"),
        ({"state": "positive"}, "FRICTION_EXCITATION_INSUFFICIENT"),
        ({"state": "collinear"}, "NONIDENTIFIABLE_DESIGN_MATRIX"),
        ({"compensation": False}, "FRICTION_UNOBSERVABLE_IN_DEADZONE"),
        ({"saturated": True}, "SATURATION_OR_OVERRIDE"),
        ({"override": True}, "SATURATION_OR_OVERRIDE"),
        ({"context_change": "geometry"}, "GEOMETRY_CONTEXT_CHANGED"),
        ({"context_change": "mode"}, "CONTEXT_CHANGED"),
    ],
)
def test_identification_admission_rejects_structural_and_health_failures(scenario, status):
    assert candidates.fit(rows(**scenario), "controller").status == status


def test_missing_observations_and_wrong_modes_never_get_scientific_success():
    sample = rows()
    assert candidates.fit((), "controller").status == "INSUFFICIENT_POINTS"
    assert candidates.fit(sample[:2], "controller").status == "INSUFFICIENT_POINTS"
    assert candidates.fit(sample, "controller", q_observed=False).status == "Q_STATE_UNOBSERVED"
    incomplete = replace(context(), cohort=None)
    assert (
        candidates.fit(tuple(replace(r, context=incomplete) for r in sample), "controller").status
        == "CONTEXT_UNAVAILABLE"
    )
    nn = replace(context(), controller_mode="NN")
    assert (
        candidates.fit(tuple(replace(r, context=nn) for r in sample), "controller").status
        == "MODE_OUTSIDE_LINEAR_SCOPE"
    )
    with pytest.raises(ValueError, match="MODEL"):
        candidates.fit(sample, "tls_spread")
    with pytest.raises(ValueError, match="TARGET"):
        candidates.fit(sample, "controller", target="physical_truth")


def test_pid_contamination_is_exposed_not_hidden_by_low_error_selection():
    sample = rows(pid_gain=1.0)
    raw = candidates.fit(sample, "controller")
    contaminated = candidates.fit(sample, "controller", target="total")
    subtracted = candidates.fit(sample, "controller", target="pid_subtracted")
    assert raw.friction == pytest.approx(0.17)
    assert contaminated.friction == pytest.approx(0.40)
    assert contaminated.factor != pytest.approx(2.4)
    assert contaminated.target_claim == "WRONG_STAGE_DIAGNOSTIC_ONLY"
    assert subtracted.friction == pytest.approx(0.17)
    assert subtracted.target_claim == "UNCLIPPED_SYNTHETIC_SUBTRACTION_ONLY"


@pytest.mark.parametrize("field", ["u_noise", "a_noise", "q_noise"])
def test_noise_is_applied_to_observations_not_to_truth_labels(field):
    sample = rows(**{field: 0.08})
    result = candidates.fit(sample, "controller")
    assert result.friction != pytest.approx(0.17, abs=1e-8)
    assert result.condition_number is not None


def test_factor_interval_propagates_covarying_a_q_without_claiming_confidence():
    sample = rows(state="correlated")
    low = candidates.fit(sample, "controller", factor=2.1)
    high = candidates.fit(sample, "controller", factor=2.7)
    interval = candidates.factor_sensitivity(sample, (2.1, 2.7))
    assert interval.status == "DETERMINISTIC_FACTOR_SENSITIVITY_NOT_CI"
    assert interval.lower == pytest.approx(min(low.friction, high.friction))
    assert interval.upper == pytest.approx(max(low.friction, high.friction))
    assert interval.lower < 0.17 < interval.upper
    assert candidates.factor_sensitivity(sample, (2.7, 2.1)).status == "INVALID_FACTOR_INTERVAL"
    assert candidates.factor_sensitivity(rows(state="deadzone"), (2.1, 2.7)).lower is None


def test_branch_excludes_transition_and_handles_unequal_occupancy_without_zero_intercept():
    result = candidates.fit(rows(state="asymmetric"), "branch")
    assert result.friction == pytest.approx(0.17)
    assert result.positive_count != result.negative_count
    assert (
        candidates.fit(rows(state="transition"), "branch").status
        == "BRANCH_REQUIRES_SATURATED_STATES"
    )
    # An asymmetric physical response yields an average branch separation, not a single optimum C.
    asym = candidates.fit(rows(negative_friction=0.27), "branch")
    assert asym.friction == pytest.approx(0.22)


@pytest.mark.parametrize(
    ("error", "deadzone", "threshold", "enabled", "want"),
    [
        (0.05, 0.06, 0.3, True, 0),
        (0.06, 0.06, 0.3, True, 0.2),
        (-0.06, 0.06, 0.3, True, -0.2),
        (0.15, 0.06, 0.3, True, 0.5),
        (0.6, 0.06, 0.3, True, 1),
        (-0.6, 0.06, 0.3, True, -1),
        (0.6, 0.06, 0.3, False, 0),
    ],
)
def test_q_reconstruction_matches_strict_source_deadzone_not_width_subtraction(
    error, deadzone, threshold, enabled, want
):
    assert candidates.normalize_state(error, deadzone, threshold, enabled) == pytest.approx(want)


@pytest.mark.parametrize(
    "args", [(float("nan"), 0, 0.3, True), (0, -0.1, 0.3, True), (0, 0, 0, True), (0, 0, 0.3, 1)]
)
def test_q_reconstruction_rejects_invalid_context(args):
    with pytest.raises(ValueError, match="FRICTION_STATE_INPUT"):
        candidates.normalize_state(*args)


def test_timestamp_and_negative_factor_cannot_claim_identifiability():
    sample = rows()
    assert (
        candidates.fit((sample[1], sample[0], *sample[2:]), "controller").status
        == "NONINCREASING_TIME"
    )
    flipped = tuple(replace(r, callback_output=-r.callback_output) for r in sample)
    for family in ("controller", "inverse", "branch"):
        assert candidates.fit(flipped, family).status == "NONPOSITIVE_FACTOR"


@pytest.mark.parametrize(
    "changes",
    [
        {"source_revision": "main"},
        {"vehicle_context_digest": "bad"},
        {"wheelbase": 0},
        {"steer_ratio_effective": float("inf")},
        {"custom_sr": -1},
        {"center_to_front_ratio": 0},
        {"center_to_front": 3},
        {"center_to_front_ratio": 0.6},
        {"geometry_generation": True},
        {"snapshot_time_ns": -1},
        {"controller_mode": "ANY"},
        {"cohort": ""},
        {"geometry_source": "STATIC_CP"},
        {"delay_source": "INFERRED"},
    ],
)
def test_context_validation_prevents_fake_defaults_and_incoherent_geometry(changes):
    with pytest.raises(ValueError):
        context(**changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"factor": 0},
        {"threshold": 0},
        {"deadzone": -1},
        {"offset": float("nan")},
        {"negative_friction": -1},
        {"state": "sign_a"},
        {"context_change": "guess"},
        {"count": 0},
        {"delay_samples": -1},
        {"seed": "606"},
        {"compensation": 1},
    ],
)
def test_oracle_rejects_invalid_scenarios(changes):
    with pytest.raises(ValueError):
        synthetic.Scenario(**changes)


def test_sample_and_intent_validation_are_not_implicit_casts():
    for changes in (
        {"acceleration": float("nan")},
        {"q": 1.1},
        {"context": None},
        {"time_ns": -1},
        {"saturated": 1},
    ):
        with pytest.raises(ValueError):
            replace(rows()[0], **changes)
    for args in ((True, None, None), (0, 0, 2.73)):
        with pytest.raises(ValueError):
            geometry.resolve_intent(*args)
    with pytest.raises(ValueError):
        geometry.vehicle_diagnostic(0)
    with pytest.raises(ValueError):
        synthetic.generate(synthetic.Scenario(), context(), (1.0,))
    with pytest.raises(ValueError):
        synthetic.generate(synthetic.Scenario(), None)
    with pytest.raises(ValueError):
        synthetic.generate(
            synthetic.Scenario(context_change="geometry"),
            contracts.SteeringGeometryContext(contracts.CURRENT),
        )
    with pytest.raises(ValueError):
        candidates.fit(list(rows()), "controller")
    with pytest.raises(ValueError):
        candidates.fit(rows(), "controller", q_observed=1)
    with pytest.raises(ValueError):
        candidates.factor_sensitivity(rows(), (1.0,))
    with pytest.raises(ValueError):
        candidates.select_model(required_signals_complete=1, independent_response=True)
    assert not contracts.finite(10**1000)


def test_delay_roll_and_all_noise_stressors_are_reproducible_and_not_recovered_as_truth():
    for scenario in (
        synthetic.Scenario(delay_samples=3),
        synthetic.Scenario(roll_mismatch=0.12),
        synthetic.Scenario(u_noise=0.08, a_noise=0.08, q_noise=0.08),
    ):
        first = synthetic.generate(scenario, context())
        assert first == synthetic.generate(scenario, context())
        result = candidates.fit(first, "controller")
        assert result.friction != pytest.approx(0.17, abs=1e-5)


def test_an_unobserved_q_has_observationally_equivalent_friction_values():
    # Same measured a,u: distinct C/q pairs fit exactly. x/y alone do not identify C.
    a, factor = 1.2, 2.4
    u1 = a / factor + 0.2 * 0.5
    u2 = a / factor + 0.4 * 0.25
    assert u1 == u2 == 0.6


def test_geometry_unknowns_remain_unknown_and_immutable():
    unknown = contracts.SteeringGeometryContext(source_revision=contracts.CURRENT)
    assert not unknown.complete
    assert unknown.center_to_front_ratio is None
    assert geometry.resolve_intent(0, None, None) == (None, "VEHICLE_DEFAULT")
    assert geometry.resolve_intent(0, 1.1739, 2.73) == (0.43, "VEHICLE_DEFAULT")
    assert geometry.resolve_intent(51, None, None) == (0.51, "MANUAL_OVERRIDE")
    assert geometry.resolve_intent(30, 1.1739, 2.73) == (0.43, "VEHICLE_DEFAULT")
    with pytest.raises(FrozenInstanceError):
        unknown.cohort = "invented"


@pytest.mark.parametrize(
    ("field", "value", "status"),
    [
        ("geometry_generation", 2, "GEOMETRY_CONTEXT_CHANGED"),
        ("center_to_front_ratio", 0.44, "GEOMETRY_CONTEXT_CHANGED"),
        ("steer_ratio_effective", 15.2, "CONTEXT_CHANGED"),
        ("stiffness_factor", 0.9, "GEOMETRY_CONTEXT_CHANGED"),
        ("steer_ratio_rate", 101.0, "CONTEXT_CHANGED"),
        ("custom_sr", 14.0, "CONTEXT_CHANGED"),
        ("effective_delay_s", 0.21, "CONTEXT_CHANGED"),
        ("delay_source", "MANUAL", "CONTEXT_CHANGED"),
        ("custom_torque_mode", 1, "CONTEXT_CHANGED"),
        ("factor_installed", 2.5, "CONTEXT_CHANGED"),
        ("friction_installed", 0.18, "CONTEXT_CHANGED"),
        ("controller_mode", "NN", "CONTEXT_CHANGED"),
        ("source_revision", contracts.RUNTIME, "GEOMETRY_CONTEXT_CHANGED"),
        ("cohort", "new-cohort", "CONTEXT_CHANGED"),
    ],
)
def test_every_confounder_closes_epoch_and_changes_context_digest(field, value, status):
    before = context()
    # Build coherent changed geometry, without introducing an invalid ratio/length pair.
    changes = {field: value}
    if field == "center_to_front_ratio":
        changes["center_to_front"] = 2.73 * value
    if field == "source_revision":
        changes["geometry_source"] = "STATIC_CP"
    after = replace(before, **changes)
    assert after.digest != before.digest
    assert geometry.epoch_boundary(before, after) == status
    assert geometry.epoch_boundary(before, before) == "SAME_CONTEXT"


def test_source_geometry_redistribution_preserves_steady_slip_but_changes_transient():
    base = geometry.vehicle_diagnostic(0.43)
    other = geometry.vehicle_diagnostic(0.51)
    assert other.center_to_front == pytest.approx(1.3923)
    assert other.front_stiffness < base.front_stiffness
    assert other.rear_stiffness > base.rear_stiffness
    assert other.curvature == pytest.approx(base.curvature, abs=1e-12)
    assert other.roll_compensation == pytest.approx(base.roll_compensation, abs=1e-12)
    assert abs(other.yaw_rate - base.yaw_rate) > 1e-5
    assert len(other.acceleration_series) == 200


def test_selection_is_current_signal_gated_even_for_perfect_synthetic_recovery():
    assert (
        candidates.select_model(required_signals_complete=False, independent_response=True)
        == "NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS"
    )
    assert (
        candidates.select_model(required_signals_complete=True, independent_response=False)
        == "NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS"
    )
    assert (
        candidates.select_model(required_signals_complete=True, independent_response=True)
        == "CONTROLLER_DOMAIN_CONDITIONAL_MODEL"
    )
