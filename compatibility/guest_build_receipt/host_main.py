"""No default IO, no runner, and no permission-granting command line."""

import json
import sys
from dataclasses import asdict

from .planning import current_reference_plan


def main(argv: list[str] | None = None) -> int:
    selected = sys.argv[1:] if argv is None else argv
    if selected == ["--describe-plan"]:
        print(json.dumps(asdict(current_reference_plan()), sort_keys=True, allow_nan=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
