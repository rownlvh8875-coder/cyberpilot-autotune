"""Future explicit diagnostics only. Default always exits2/BLOCKED without I/O."""

import argparse
import json
from pathlib import Path

from .contracts import CASES, PERMISSIONS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-prepared-guest", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--case", choices=CASES)
    selection.add_argument("--all-cases", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args(argv)
    result: dict[str, object] = {"status": "BLOCKED", "permissions": dict(PERMISSIONS)}
    if not args.run_prepared_guest or not (args.case or args.all_cases) or args.destination is None:
        print(json.dumps(result | {"capture": "NOT_STARTED"}, sort_keys=True))
        return 2
    from .capture import CaptureFailure
    from .runner import capture_cases

    try:
        records = capture_cases(
            CASES if args.all_cases else (args.case,), args.destination, run_prepared_guest=True
        )
        result |= {"capture": "RECORDED_UNTRUSTED", "records": [r.metadata() for r in records]}
    except CaptureFailure as error:
        current = error.current_record
        result |= {
            "capture": "FAILED",
            "reason": str(error),
            "raw_bytes": len(error.raw),
            "raw_complete": error.raw_complete,
            "completed": len(error.completed),
            "current_record": current.metadata() if current is not None else None,
            "current_record_digest": current.content_digest if current is not None else None,
            "acquisition_error": error.acquisition_error,
            "persistence_error": error.persistence_error,
        }
    except (OSError, ValueError) as error:
        result |= {"capture": "UNAVAILABLE", "reason": str(error)}
    print(json.dumps(result, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
