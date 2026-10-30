"""Hash-bound evidence bytes must survive ordinary Windows/autocrlf checkout."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "path",
    [
        "compatibility/containment_backend_harmless/host/build_manifest.json",
        "docs/evidence/containment_backend_guest_sources.json",
        "docs/evidence/containment_backend_harmless_results.json",
    ],
)
def test_exact_evidence_bytes_are_not_line_ending_converted(path):
    result = subprocess.check_output(["git", "check-attr", "text", "--", path], cwd=ROOT, text=True)
    assert result.strip() == f"{path}: text: unset"
