"""Synthetic coverage summaries cannot lower either independent CI floor."""

import pytest

from tests.audit.validate_actual_binding_coverage import validate


def coverage(statements, branches):
    files = {
        f"src/cyberpilot_autotune/diagnostics/actual_binding/file{i}.py": {
            "summary": {
                "num_statements": 100,
                "covered_lines": statements,
                "num_branches": 100,
                "covered_branches": branches,
            }
        }
        for i in range(9)
    }
    return {"files": files}


@pytest.mark.parametrize("statement,branch", ((97, 100), (100, 94), (0, 0)))
def test_each_floor_is_independently_enforced(statement, branch):
    with pytest.raises(ValueError, match="DIAGNOSTICS_COVERAGE"):
        validate(coverage(statement, branch))


def test_exact_floors_are_accepted():
    assert validate(coverage(98, 95)) == {"statement_pct": 98.0, "branch_pct": 95.0}


@pytest.mark.parametrize("count", (0, 8, 10))
def test_coverage_must_include_all_and_only_nine_modules(count):
    report = coverage(100, 100)
    entries = report["files"]
    if count < 9:
        entries = dict(list(entries.items())[:count])
    else:
        entries["src/cyberpilot_autotune/diagnostics/actual_binding/extra.py"] = next(
            iter(entries.values())
        )
    with pytest.raises(ValueError, match="COVERAGE_SOURCE_INVENTORY"):
        validate({"files": entries})
