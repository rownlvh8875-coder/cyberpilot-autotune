"""Explicit guest-only command selection; importing or default invocation performs no IO."""

import argparse
import sys
from collections.abc import Sequence


def execute_guest(selected: tuple[str, ...]) -> int:
    from .vm_runner import execute_guest_job

    return execute_guest_job(selected)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixed software-VM harmless fixtures only")
    parser.add_argument("--execute-guest", action="store_true")
    parser.add_argument(
        "--fixture", choices=tuple(f"HF{i:02d}" for i in range(1, 25)), action="append"
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2
    if not args.execute_guest or not args.fixture or len(set(args.fixture)) != len(args.fixture):
        parser.print_usage(sys.stderr)
        return 2
    return execute_guest(tuple(args.fixture))


if __name__ == "__main__":
    raise SystemExit(main())
