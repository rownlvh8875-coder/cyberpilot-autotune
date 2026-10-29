"""Only exact namespace inventory additions are permitted; no hash guard deletion."""

from pathlib import Path

from tests.audit import validate_friction_model as h6


def test_historical_inventory_extension_allows_only_the_three_exact_h7_additions():
    root = Path(__file__).resolve().parents[2]
    for path in (
        "tests/architecture/test_knowledge_boundary.py",
        "tests/audit/test_carrot_writer_ownership.py",
        "tests/audit/test_hoya_c3_atune_evidence.py",
    ):
        original = h6.git_bytes(root, h6.BASE, path)
        actual = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert h6.historical_inventory_equivalent(path, original, actual)
        assert not h6.historical_inventory_equivalent(
            path, original, actual + b"\n# other change\n"
        )
        assert not h6.historical_inventory_equivalent("src/other.py", original, actual + b"\n")
        assert not h6.historical_inventory_equivalent(path, original, b"# hash checks removed\n")
