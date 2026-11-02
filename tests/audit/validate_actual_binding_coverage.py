"""Additional diagnostics coverage gate; does not replace any existing gate."""

import argparse
import json
from pathlib import Path


def validate(report):
    summaries = [
        entry["summary"]
        for name, entry in report["files"].items()
        if "/diagnostics/actual_binding/" in "/" + name.replace("\\", "/")
    ]
    if len(summaries) != 9:
        raise ValueError("COVERAGE_SOURCE_INVENTORY")
    statements = sum(s["num_statements"] for s in summaries)
    covered = sum(s["covered_lines"] for s in summaries)
    branches = sum(s["num_branches"] for s in summaries)
    branch_covered = sum(s["covered_branches"] for s in summaries)
    if not (
        statements > 0
        and covered / statements >= 0.98
        and branches > 0
        and branch_covered / branches >= 0.95
    ):
        raise ValueError("DIAGNOSTICS_COVERAGE")
    return {
        "statement_pct": 100 * covered / statements,
        "branch_pct": 100 * branch_covered / branches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_json", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.coverage_json.read_bytes())), sort_keys=True))


if __name__ == "__main__":
    main()
