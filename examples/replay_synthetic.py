"""Read only the repository's explicit synthetic fixture; print in-memory evidence."""

import json
from pathlib import Path

from cyberpilot_autotune.replay import load_replay, run_replay


def main() -> None:
    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/replay/golden_v1.json"
    report = run_replay(load_replay(fixture.read_text(encoding="utf-8")))
    summary = report.summary
    print(
        json.dumps(
            {
                "scope": "SYNTHETIC_TEST_ONLY",
                "modes": ["OFF", "SHADOW"],
                "baseline": dict(report.scenario.baseline_parameters),
                "all_effective_equal_baseline": all(
                    result.effective_parameters == report.scenario.baseline_parameters
                    for result in (*report.off_results, *report.shadow_results)
                ),
                "event_count": summary.event_count,
                "proposal_count": summary.proposal_count,
                "eligible_count": summary.eligible_count,
                "rejection_counts": {
                    key.value: count for key, count in summary.rejection_counts.items()
                },
                "override_exclusion_count": summary.override_exclusion_count,
                "saturation_exclusion_count": summary.saturation_exclusion_count,
                "maximum_proposed_delta": [
                    summary.maximum_proposed_delta.numerator,
                    summary.maximum_proposed_delta.denominator,
                ],
                "invariant_violations": summary.invariant_violations,
                "internal_error_count": summary.internal_error_count,
                "software_checks_passed": report.software_checks_passed,
                "sha256": report.digest,
                "latency_ns": {
                    "off": report.latency.off_ns,
                    "shadow": report.latency.shadow_ns,
                    "off_total": report.latency.off_total_ns,
                    "shadow_total": report.latency.shadow_total_ns,
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
