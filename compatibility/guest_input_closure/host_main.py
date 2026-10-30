"""Closed-default, fixed read-only verification; BLOCKED always exits2."""

import json
import sys
from dataclasses import asdict


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if selected != ["--verify-current"]:
        return 2
    from .evaluation import evaluate_closure
    from .fixed import expected_snapshot, observe_fixed_inputs

    try:
        actual, images = observe_fixed_inputs()
        report = evaluate_closure(expected_snapshot(), actual, images)
        print(json.dumps(asdict(report), sort_keys=True, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(
            json.dumps(
                {"overall_status": "BLOCKED", "observation": "UNAVAILABLE", "reason": str(error)},
                sort_keys=True,
            )
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
