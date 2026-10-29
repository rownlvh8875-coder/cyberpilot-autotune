"""Only the additive native-source job extension may pass the older audit."""

import importlib
from pathlib import Path

from tests.audit import validate_carrot_friction_patch_design as prior


def test_native_ci_extension_cannot_remove_old_gates_or_accept_unrelated_changes():
    path = Path(__file__).resolve().parents[2] / "compatibility/friction_native/ci.py"
    assert path.is_file(), "NATIVE_CI_EXTENSION_MISSING"
    ci = importlib.import_module("compatibility.friction_native.ci")
    original = prior.git_bytes(prior.ROOT, prior.BASE, prior.CI_PATH).decode()
    design = prior.extend_ci(original)
    updated = ci.extend(design)
    assert prior.compatible_ci(original, updated)
    assert not prior.compatible_ci(original, updated.replace("--verify-history", ""))
    assert not prior.compatible_ci(original, updated + "# unrelated\n")
