"""Closed-default diagnostics; even recognized guest scenarios exit2/BLOCKED."""

import argparse
import json
import subprocess
from dataclasses import asdict

from .contracts import CASES
from .evaluation import evaluate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-prepared-guest", action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--case", choices=CASES)
    group.add_argument("--all-cases", action="store_true")
    args = parser.parse_args(argv)
    if not args.run_prepared_guest or not (args.case or args.all_cases):
        print(json.dumps({"overall": "BLOCKED", "capture": "NOT_STARTED"}))
        return 2
    from .vm_runner import capture_cases

    try:
        for capture, _ in capture_cases(CASES if args.all_cases else (args.case,)):
            decision = evaluate(capture)
            print(
                json.dumps(
                    {
                        **asdict(decision),
                        "overall": decision.overall,
                        "permissions": dict(decision.permissions),
                    },
                    sort_keys=True,
                )
            )
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"overall": "BLOCKED", "capture": "UNAVAILABLE", "reason": str(error)}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
