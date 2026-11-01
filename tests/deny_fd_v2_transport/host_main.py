"""Explicit fixed diagnostics only; default no IO, every outcome BLOCKED/exit2."""

import argparse
import base64
import json
from pathlib import Path

from tests.deny_fd_v2_harness.contracts import CASES

from .contracts import PERMISSIONS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-prepared-guest", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--case", choices=CASES)
    selection.add_argument("--all-cases", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args(argv)
    output: dict[str, object] = {"status": "BLOCKED", "permissions": dict(PERMISSIONS)}
    if not args.run_prepared_guest or not (args.case or args.all_cases) or args.destination is None:
        print(json.dumps(output | {"capture": "NOT_STARTED"}, sort_keys=True))
        return 2
    from .capture import TransportCaptureFailure
    from .runner import capture_cases

    try:
        records = capture_cases(
            CASES if args.all_cases else (args.case,), args.destination, run_prepared_guest=True
        )
        output |= {"capture": "RECORDED_UNTRUSTED", "records": [r.metadata() for r in records]}
    except TransportCaptureFailure as error:
        output |= {
            "capture": "FAILED",
            "reason": str(error),
            "completed": len(error.completed),
            "telemetry_bytes": len(error.result.telemetry.raw),
            "console_bytes": len(error.result.console.raw),
            "current_record": error.current_record.metadata() if error.current_record else None,
            "acquisition_error": error.acquisition_error,
            "persistence_error": error.persistence_error,
            # Lossless bounded fallback even if every owned file destination
            # fails. Lengths/digests alone cannot recover observed raw bytes.
            "raw_evidence": {
                "encoding": "base64",
                "telemetry": base64.b64encode(error.result.telemetry.raw).decode("ascii"),
                "console": base64.b64encode(error.result.console.raw).decode("ascii"),
            },
        }
    except (OSError, ValueError) as error:
        output |= {"capture": "UNAVAILABLE", "reason": str(error)}
    print(json.dumps(output, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
