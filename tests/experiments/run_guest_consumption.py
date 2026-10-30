"""Opt-in actual fixed fixture check; zero means fixture matched, NOT qualification."""

import importlib.util
import json
import sys
from dataclasses import asdict


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if (
        len(selected) != 2
        or selected[0] != "--case"
        or selected[1] not in tuple(f"CP{i:02d}" for i in range(1, 8))
    ):
        return 2
    assert importlib.util.find_spec("compatibility.guest_consumption.vm_runner") is not None, (
        "actual producer/runner missing"
    )
    from compatibility.guest_consumption.checks import check_case
    from compatibility.guest_consumption.vm_runner import CaptureUnavailable, capture_case

    try:
        observation, raw = capture_case(selected[1])
    except CaptureUnavailable as error:
        sys.stdout.buffer.write(error.raw)
        sys.stdout.flush()
        print("GUEST_CAPTURE_UNAVAILABLE", str(error))
        return 2
    sys.stdout.write(raw)
    issues = check_case(observation, selected[1])
    print(
        "FIXED_FIXTURE_CHECK",
        json.dumps({"issues": issues, "observation": asdict(observation)}, sort_keys=True),
    )
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
