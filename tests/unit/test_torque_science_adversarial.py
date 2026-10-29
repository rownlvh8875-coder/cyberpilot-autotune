"""Invalid scientific inputs cannot be converted into apparently valid fits."""

from dataclasses import replace

import pytest

from tests.unit.test_torque_science_clusters import dataset
from tests.unit.test_torque_science_synthetic import scenario


@pytest.mark.parametrize("function", ["projected_coefficient", "symmetric_tls_prediction"])
def test_bounded_friction_state_cannot_have_variance_above_one(function):
    from cyberpilot_autotune.research.torque_identification import analytic

    with pytest.raises(ValueError):
        getattr(analytic, function)(
            2.0,
            0.1,
            2.0 if function == "projected_coefficient" else 0.1,
            0.0 if function == "projected_coefficient" else 2.0,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("factor", 0.0),
        ("controller_friction", -0.1),
        ("deadzone", -0.1),
        ("friction_threshold", 0.0),
        ("x_noise_std", -0.1),
        ("y_noise_std", float("nan")),
        ("commands", ()),
        ("errors", (0.0,)),
        ("roll_bias_rad", (0.0,)),
        ("lag_steps", -1),
        ("alignment_steps", 100),
        ("sample_group_size", 0),
        ("seed", True),
        ("name", ""),
    ],
)
def test_invalid_synthetic_configuration_is_rejected_before_generating_points(field, value):
    with pytest.raises(ValueError):
        replace(scenario(), **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_sha256", "missing"),
        ("time_ns", -1),
        ("time_ns", True),
        ("normalized_command", 10**1000),
        ("lateral_accel_mps2", float("inf")),
        ("normalized_command", True),
    ],
)
def test_invalid_sample_identity_time_or_number_is_rejected(field, value):
    point = dataset().routes[0].epochs[0].points[0]
    with pytest.raises(ValueError):
        replace(point, **{field: value})


@pytest.mark.parametrize(
    "change",
    [
        "overlap",
        "gap_clock_reset",
        "adjacent_manifest_gap",
        "second_start",
        "epoch_source",
        "epoch_identity",
    ],
)
def test_inconsistent_route_epoch_boundaries_are_not_silently_pooled(change):
    route = dataset(route_count=1, epoch_count=2).routes[0]
    first, second = route.epochs
    with pytest.raises(ValueError):
        if change == "epoch_source":
            replace(second, source_revision="0" * 40)
        elif change == "epoch_identity":
            replace(second, epoch_sha256="")
        else:
            if change == "overlap":
                second = replace(second, start_segment=0)
            elif change == "gap_clock_reset":
                second = replace(second, start_segment=3, end_segment=3)
            elif change == "adjacent_manifest_gap":
                second = replace(second, boundary_reason="MANIFEST_GAP")
            else:
                second = replace(second, boundary_reason="START")
            replace(route, epochs=(first, second))


def test_each_epoch_source_domain_is_checked_independently():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    data = dataset(route_count=1)
    route, epoch = data.routes[0], data.routes[0].epochs[0]
    points = tuple(replace(p, lateral_accel_mps2=2.0 * p.lateral_accel_mps2) for p in epoch.points)
    result = analyze_clusters(
        replace(data, routes=(replace(route, epochs=(replace(epoch, points=points),)),))
    )
    assert result.epochs[0].status == "INVALID_SOURCE_CONTRACT"
    assert "NATIVE_EPOCH_VALIDITY_NOT_ESTABLISHED" in result.blockers


def test_all_degenerate_data_returns_unknown_and_no_jackknife_interval():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    data = dataset()
    routes = tuple(
        replace(
            r,
            epochs=tuple(
                replace(
                    e,
                    points=tuple(
                        replace(p, normalized_command=0.2, lateral_accel_mps2=0.4) for p in e.points
                    ),
                )
                for e in r.epochs
            ),
        )
        for r in data.routes
    )
    result = analyze_clusters(replace(data, routes=routes))
    assert result.full.fit is None and result.residuals is None
    assert result.factor_jackknife_se is None and result.confidence_interval is None
    assert "LEAVE_ONE_ROUTE_FIT_UNAVAILABLE" in result.blockers
