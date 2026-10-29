"""Cluster admission and statistics exercise real synthetic frozen observations."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest


def dataset(route_count=3, epoch_count=1, count=16, **changes):
    from cyberpilot_autotune.research.torque_identification.contracts import (
        RESEARCH,
        RUNTIME,
        SIGNAL,
        Epoch,
        FrozenDevelopment,
        Point,
        Route,
        digest,
    )

    routes = []
    for r in range(route_count):
        epochs = []
        for e in range(epoch_count):
            points = tuple(
                Point(
                    digest((r, e, i)),
                    i * 1_000_000,
                    (-0.4, -0.2, 0.2, 0.4)[i % 4],
                    2.0 * (-0.4, -0.2, 0.2, 0.4)[i % 4],
                )
                for i in range(count)
            )
            epochs.append(
                Epoch(
                    digest(("epoch", r, e)),
                    RUNTIME,
                    e,
                    e,
                    "START" if e == 0 else "CLOCK_RESET",
                    points,
                )
            )
        routes.append(Route(digest(("route", r)), tuple(epochs)))
    return replace(
        FrozenDevelopment(
            "development_fit",
            SIGNAL,
            RUNTIME,
            RESEARCH,
            "negative_applied_normalized_torque",
            "m/s^2",
            1,
            "LINEAR_TORQUE",
            digest("provenance"),
            digest("selection"),
            tuple(routes),
        ),
        **changes,
    )


def policy():
    return (
        Path(__file__).resolve().parents[2] / "docs/evidence/torque_identification_policy.json"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("role", "holdout", "ROLE"),
        ("role", "development_evaluation", "ROLE"),
        ("signal_contract", "positive torque", "SIGNAL_CONTRACT"),
        ("x_stage", "requested_torque", "APPLIED_STAGE"),
        ("x_stage", "positive_applied_normalized_torque", "APPLIED_STAGE"),
        ("y_unit", "g", "UNIT"),
        ("delay_applications", 2, "DELAY"),
        ("delay_applications", True, "DELAY"),
        ("runtime_revision", "0" * 40, "SOURCE_REVISION"),
        ("research_revision", "0" * 40, "SOURCE_REVISION"),
        ("controller_mode", "NN_TORQUE", "MODE"),
        ("controller_mode", "NN_LITE", "MODE"),
        ("controller_mode", "GM_CALLBACK", "MODE"),
        ("controller_mode", "CUSTOM_TORQUE", "MODE"),
        ("provenance_sha256", "", "PROVENANCE"),
        ("selection_binding_sha256", "", "PROVENANCE"),
    ],
)
def test_unsupported_role_source_signal_or_mode_never_reaches_a_fit(field, value, reason):
    with pytest.raises(ValueError, match=reason):
        dataset(**{field: value})


@pytest.mark.parametrize("kind", ["route", "epoch", "sample", "time", "order", "missing_route"])
def test_identity_and_time_failures_cannot_inflate_cluster_support(kind):
    data = dataset()
    route = data.routes[0]
    epoch = route.epochs[0]
    with pytest.raises(ValueError):
        if kind == "route":
            replace(data, routes=(*data.routes, route))
        elif kind == "epoch":
            replace(data, routes=(replace(route, epochs=(epoch, epoch)), *data.routes[1:]))
        elif kind in {"sample", "time", "order"}:
            points = list(epoch.points)
            if kind == "sample":
                points[-1] = replace(points[-1], sample_sha256=points[0].sample_sha256)
            elif kind == "time":
                points[-1] = replace(points[-1], time_ns=points[0].time_ns)
            else:
                points.reverse()
            replace(
                data,
                routes=(
                    replace(route, epochs=(replace(epoch, points=tuple(points)),)),
                    *data.routes[1:],
                ),
            )
        else:
            replace(route, route_sha256="")


def test_same_route_epochs_are_not_counted_as_independent_routes():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    result = analyze_clusters(dataset(route_count=2, epoch_count=3))
    assert result.cluster_count == 2 and result.epoch_count == 6
    assert result.factor_jackknife_se is None
    assert "INSUFFICIENT_CLUSTER_COUNT" in result.blockers
    assert len(result.leave_one_route_out) == 2
    assert len(result.leave_one_epoch_out) == 6


def test_all_route_omissions_and_descriptive_jackknife_are_deterministic():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    data = dataset()
    result = analyze_clusters(data)
    assert result == analyze_clusters(replace(data, routes=tuple(reversed(data.routes))))
    assert len(result.leave_one_route_out) == 3
    assert result.factor_jackknife_se == pytest.approx(0.0, abs=2e-12)
    assert all(abs(r.factor_delta) < 2e-12 for r in result.leave_one_route_out)
    assert result.confidence_interval is None


def test_empty_route_never_increases_independent_cluster_count_or_jackknife_n():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    data = dataset()
    empty = dataset(route_count=4, count=0).routes[-1]
    # Pick an actual fourth identity, not the canonical last identity by accident.
    empty = next(
        r
        for r in dataset(route_count=4, count=0).routes
        if r.route_sha256 not in {x.route_sha256 for x in data.routes}
    )
    result = analyze_clusters(replace(data, routes=(*data.routes, empty)))
    assert result.cluster_count == 3 and len(result.leave_one_route_out) == 4
    assert result.factor_jackknife_se == pytest.approx(0.0, abs=2e-12)


def test_native_coverage_requires_each_epoch_not_pooled_thresholds():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters
    from cyberpilot_autotune.research.torque_identification.contracts import Point, digest

    data = dataset(route_count=1, epoch_count=1)
    epoch = data.routes[0].epochs[0]
    counts = (100, 300, 500, 1100, 1100, 500, 300, 100)
    xs = (-0.4, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.4)
    rows = [(x, i) for x, count in zip(xs, counts, strict=True) for i in range(count)]
    points = tuple(Point(digest((x, i)), k, x, 2 * x) for k, (x, i) in enumerate(rows))
    route = replace(data.routes[0], epochs=(replace(epoch, points=points),))
    result = analyze_clusters(replace(data, routes=(route,)))
    assert result.epochs[0].status == "VALID"
    assert result.epochs[0].bucket_counts == counts
    short = analyze_clusters(dataset(route_count=3, epoch_count=2))
    assert all(e.status == "INSUFFICIENT_COVERAGE" for e in short.epochs)


def test_route_influence_is_reported_without_a_posthoc_pass_cutoff():
    from cyberpilot_autotune.research.torque_identification.cluster_stats import analyze_clusters

    data = dataset()
    route = data.routes[0]
    epoch = route.epochs[0]
    altered = replace(
        epoch,
        points=tuple(replace(p, lateral_accel_mps2=p.normalized_command) for p in epoch.points),
    )
    data = replace(data, routes=(replace(route, epochs=(altered,)), *data.routes[1:]))
    result = analyze_clusters(data)
    assert any(abs(r.factor_delta) > 0.01 for r in result.leave_one_route_out)
    assert result.maximum_route_factor_relative_delta > 0.0
    assert result.stability_qualified is False
    assert "THRESHOLD_NOT_JUSTIFIED" in result.blockers


def test_missing_development_data_returns_unknown_not_historical_claimed_counts():
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    report = qualify(None, policy())
    assert report.cluster_count is None and report.point_count is None
    assert report.cluster_statistics is None
    assert "FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE" in report.blockers
    assert report.friction_verdict == "FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION"
    assert report.joint_identifiability == "NONIDENTIFIABLE"


@pytest.mark.parametrize(
    "field",
    [
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "parameter_identification_qualified",
    ],
)
def test_scientific_report_cannot_be_dataclass_replaced_into_authority(field):
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    report = qualify(dataset(), policy())
    assert getattr(report, field) is False
    with pytest.raises(ValueError):
        replace(report, **{field: True})


def test_posthoc_policy_mutation_rejected_even_with_self_consistent_json():
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    altered = json.loads(policy())
    altered["route_stability_acceptance_threshold"] = 0.99
    with pytest.raises(ValueError, match="POLICY_MUTATION"):
        qualify(dataset(), json.dumps(altered))


def test_same_frozen_input_has_byte_identical_research_report():
    from cyberpilot_autotune.research.torque_identification.contracts import canonical
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    data = dataset()
    assert canonical(asdict(qualify(data, policy()))) == canonical(asdict(qualify(data, policy())))
