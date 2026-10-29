"""Installed-wheel scientific execution with and without the optional extra."""

import argparse
from dataclasses import asdict
from pathlib import Path

from cyberpilot_autotune.research.torque_identification.contracts import Point, canonical
from cyberpilot_autotune.research.torque_identification.estimator import fit_raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--expect-optional-dependency", action="store_true")
    args = parser.parse_args()
    points = tuple(
        Point(f"{i:064x}", i, x, 2.0 * x) for i, x in enumerate((-0.2, 0.1, 0.3), start=1)
    )
    if args.expect_optional_dependency:
        try:
            fit_raw(points)
        except ModuleNotFoundError as error:
            assert error.name == "numpy"
            print("OPTIONAL_RESEARCH_DEPENDENCY_ERROR_VERIFIED")
            return
        raise AssertionError("vanilla wheel unexpectedly includes NumPy")
    fit = fit_raw(points)
    assert abs(fit.linear_mode_tls_lat_accel_slope - 2.0) < 2e-12
    from cyberpilot_autotune.research.torque_identification.qualification import qualify

    report = qualify(None, args.policy.read_text(encoding="utf-8"))
    assert not any(
        (
            report.candidate_generation_allowed,
            report.application_authorized,
            report.runtime_accepted,
            report.parameter_identification_qualified,
        )
    )
    assert len(report.synthetic_recovery_summary) == 43
    assert report.cluster_count is None and report.cluster_statistics is None
    assert canonical(asdict(report)) == canonical(asdict(qualify(None, args.policy.read_text())))
    print("SCIENCE_WHEEL_PASS: raw SVD / 43 synthetic cases / deterministic authority-free report")


if __name__ == "__main__":
    main()
