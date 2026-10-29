"""Scientific identities and authority boundaries under generated inputs."""

from dataclasses import asdict, replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.unit.test_torque_science_clusters import dataset, policy
from tests.unit.test_torque_science_synthetic import measured, scenario


@settings(max_examples=25, deadline=None, derandomize=True)
@given(st.floats(min_value=0.25, max_value=4.0), st.floats(min_value=0.01, max_value=1.0))
def test_increasing_ideal_factor_increases_recovered_slope(factor, increment):
    first = measured(scenario(factor=factor))
    second = measured(scenario(factor=factor + increment))
    assert second.linear_mode_tls_lat_accel_slope > first.linear_mode_tls_lat_accel_slope


@settings(max_examples=20, deadline=None, derandomize=True)
@given(st.floats(min_value=0.001, max_value=0.05))
def test_no_friction_with_noise_is_not_an_identified_friction_magnitude(noise):
    fit = measured(scenario(x_noise_std=noise, y_noise_std=noise))
    assert fit.native_residual_spread_coefficient > 0.0


@settings(max_examples=12, deadline=None, derandomize=True)
@given(st.permutations(tuple(range(8))))
def test_point_permutation_policy_rejects_nonmonotonic_sample_time(order):
    data = dataset(count=8)
    route, epoch = data.routes[0], data.routes[0].epochs[0]
    points = tuple(epoch.points[i] for i in order)
    if tuple(order) == tuple(range(8)):
        assert replace(epoch, points=points) == epoch
    else:
        with pytest.raises(ValueError, match="NONINCREASING_TIME"):
            replace(epoch, points=points)
    assert route.epochs[0] == epoch


@settings(max_examples=12, deadline=None, derandomize=True)
@given(st.integers(min_value=0, max_value=15))
def test_duplicate_sample_across_route_clusters_is_rejected(index):
    data = dataset()
    route = data.routes[1]
    epoch = route.epochs[0]
    points = list(epoch.points)
    points[index] = replace(
        points[index], sample_sha256=data.routes[0].epochs[0].points[0].sample_sha256
    )
    changed = replace(route, epochs=(replace(epoch, points=tuple(points)),))
    with pytest.raises(ValueError, match="DUPLICATE_SAMPLE"):
        replace(data, routes=(data.routes[0], changed, data.routes[2]))


@settings(max_examples=10, deadline=None, derandomize=True)
@given(st.integers(min_value=100, max_value=10000))
def test_cluster_relabeling_changes_bound_evidence_digest(label):
    from cyberpilot_autotune.research.torque_identification.contracts import digest

    data = dataset()
    changed = replace(data.routes[0], route_sha256=digest(("relabel", label)))
    assert replace(data, routes=(changed, *data.routes[1:])).digest != data.digest


@settings(max_examples=8, deadline=None, derandomize=True)
@given(st.integers(min_value=1, max_value=3))
def test_same_frozen_data_produces_byte_identical_report(route_count):
    from cyberpilot_autotune.research.torque_identification.contracts import canonical
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    data = dataset(route_count=route_count)
    assert canonical(asdict(qualify(data, policy()))) == canonical(asdict(qualify(data, policy())))


@given(
    st.sampled_from(
        [
            "candidate_generation_allowed",
            "application_authorized",
            "runtime_accepted",
            "parameter_identification_qualified",
        ]
    )
)
def test_report_dataclass_replacement_cannot_grant_any_authority(field):
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    report = qualify(None, policy())
    with pytest.raises(ValueError):
        replace(report, **{field: True})


@given(st.sampled_from(["0" * 40, "f" * 40, "1" * 40]))
def test_changed_source_revision_invalidates_scientific_input(source):
    with pytest.raises(ValueError, match="SOURCE_REVISION"):
        replace(dataset(), runtime_revision=source)
