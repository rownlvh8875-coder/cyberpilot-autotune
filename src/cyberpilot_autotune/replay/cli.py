"""Explicit local synthetic fixture CLI. The only replay package file-IO boundary."""

import argparse
import json
import sys
from pathlib import Path
from typing import Never

from cyberpilot_autotune.contracts import ValidationError

from .canonical import canonical_bytes
from .runner import ReplayReport, characterize_replay
from .schema import (
    MAX_REPLAY_BYTES,
    UnsupportedConfigurationError,
    _nonfinite,
    _unique,
    load_replay,
)

LEGACY_KEYS = frozenset(
    {
        "event_count",
        "proposal_count",
        "eligible_count",
        "rejection_counts",
        "override_exclusion_count",
        "saturation_exclusion_count",
        "maximum_proposed_delta",
        "invariant_violations",
        "internal_error_count",
        "sha256",
    }
)
LEGACY_RESULT_SHA256 = "5434e0cd203a08fb97662d94b91d66665bb950ba8cb276f90597efc8af673af5"


class _GoldenMismatch(Exception):
    pass


class _InvariantFailure(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise ValidationError("invalid CLI arguments")


def _read(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_REPLAY_BYTES + 1)
        if len(raw) > MAX_REPLAY_BYTES:
            raise ValidationError("input exceeds resource cap")
        return raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError("unreadable replay input") from exc


def _evidence(report: ReplayReport, sample_counts: tuple[int | None, ...]) -> dict[str, object]:
    summary = report.summary
    return {
        "event_count": summary.event_count,
        "proposal_count": summary.proposal_count,
        "eligible_count": summary.eligible_count,
        "rejection_counts": {key.value: value for key, value in summary.rejection_counts.items()},
        "override_exclusion_count": summary.override_exclusion_count,
        "saturation_exclusion_count": summary.saturation_exclusion_count,
        "maximum_proposed_delta": [
            summary.maximum_proposed_delta.numerator,
            summary.maximum_proposed_delta.denominator,
        ],
        "invariant_violations": summary.invariant_violations,
        "internal_error_count": summary.internal_error_count,
        "sha256": report.digest,
        "scenario_sha256": report.scenario_sha256,
        "configuration_sha256": report.configuration_sha256,
        "result_sha256": report.result_sha256,
        "software_checks_passed": report.software_checks_passed,
        "events": [
            {
                "reason_codes": [item.reason.value for item in shadow.events]
                + [item.reason.value for item in shadow.gate_decisions],
                "observation_sequence": shadow.observation_sequence,
                "proposal_count": len(shadow.proposals),
                "eligible_count": sum(item.eligible for item in shadow.gate_decisions),
                "sample_count": count,
                "baseline_retained": (
                    off.baseline_parameters
                    == off.effective_parameters
                    == shadow.baseline_parameters
                    == shadow.effective_parameters
                    == report.scenario.baseline_parameters
                ),
            }
            for off, shadow, count in zip(
                report.off_results, report.shadow_results, sample_counts, strict=True
            )
        ],
    }


def _run(path: Path) -> dict[str, object]:
    report, counts = characterize_replay(load_replay(_read(path)))
    if not report.software_checks_passed:
        raise _InvariantFailure
    return _evidence(report, counts)


def _verify(scenario: Path, expected_path: Path) -> dict[str, object]:
    output = _run(scenario)
    try:
        expected = json.loads(
            _read(expected_path), object_pairs_hook=_unique, parse_constant=_nonfinite
        )
    except (ValueError, RecursionError) as exc:
        raise ValidationError("invalid expectation JSON") from exc
    if type(expected) is not dict:
        raise _GoldenMismatch
    legacy = set(expected) == LEGACY_KEYS and output["result_sha256"] == LEGACY_RESULT_SHA256
    if not legacy and set(expected) != output.keys():
        raise _GoldenMismatch
    actual = {key: output[key] for key in expected}
    if canonical_bytes(actual) != canonical_bytes(expected):
        raise _GoldenMismatch
    return output


def _verify_all(directory: Path) -> dict[str, object]:
    try:
        fixtures = sorted(
            (
                path
                for path in directory.iterdir()
                if path.name.endswith("_v1.json")
                and not path.name.endswith(".expected.json")
                and path.is_file()
            ),
            key=lambda path: path.name,
        )
    except OSError as exc:
        raise ValidationError("unreadable fixture directory") from exc
    if not fixtures:
        raise ValidationError("no synthetic scenarios found")
    verified = []
    for path in fixtures:
        output = _verify(path, path.with_name(path.stem + ".expected.json"))
        verified.append({"fixture": path.name, "result_sha256": output["result_sha256"]})
    return {"verified": verified}


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(description="Verify explicit local synthetic replay fixtures")
        commands = parser.add_subparsers(dest="command", required=True)
        run = commands.add_parser("run")
        run.add_argument("scenario", type=Path)
        verify = commands.add_parser("verify")
        verify.add_argument("scenario", type=Path)
        verify.add_argument("expected", type=Path)
        verify_all = commands.add_parser("verify-all")
        verify_all.add_argument("directory", type=Path)
        args = parser.parse_args(argv)
        if args.command == "run":
            output = _run(args.scenario)
        elif args.command == "verify":
            output = _verify(args.scenario, args.expected)
        else:
            output = _verify_all(args.directory)
        sys.stdout.buffer.write(canonical_bytes(output) + b"\n")
        return 0
    except UnsupportedConfigurationError:
        code, reason, description = (
            5,
            "UNSUPPORTED_CONFIGURATION",
            "Unsupported replay configuration",
        )
    except ValidationError:
        code, reason, description = 2, "SCHEMA_INPUT_ERROR", "Invalid replay input"
    except _GoldenMismatch:
        code, reason, description = 3, "GOLDEN_MISMATCH", "Replay expectations differ"
    except Exception:
        code, reason, description = 4, "REPLAY_INVARIANT_VIOLATION", "Replay software checks failed"
    sys.stderr.buffer.write(f"{reason}: {description}\n".encode("ascii"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
