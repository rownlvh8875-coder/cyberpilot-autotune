"""Closed default; explicit fixed capture still reports BLOCKED and exits2."""

import json
import subprocess
import sys
from dataclasses import asdict

from .contracts import CASES


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if len(selected) != 2 or selected[0] != "--capture" or selected[1] not in CASES:
        return 2
    from .vm_runner import capture_case

    try:
        observation, _ = capture_case(selected[1])
        print(json.dumps(asdict(observation), sort_keys=True, allow_nan=False))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(
            json.dumps(
                {"overall_status": "BLOCKED", "capture": "UNAVAILABLE", "reason": str(error)},
                sort_keys=True,
            )
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
