"""Integration regressions: canonical API, no legacy fallback or false authority."""

import importlib.util
import json
import shutil
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest


def test_canonical_api_is_installed():
    # Catch an unshipped namespace; do not accept the old standalone top-level API.
    assert importlib.util.find_spec("cyberpilot_autotune.diagnostics") is not None
    from cyberpilot_autotune.diagnostics.actual_binding import (
        ActualDiagnosticBundle,
        assess_actual_binding,
    )

    bundle = ActualDiagnosticBundle((), ())
    result = assess_actual_binding(bundle, expected_pre=None, expected_post=None)
    assert result.structural_status == "REJECTED"
    assert result.status == "BLOCKED" and result.integrated_admission is False
    assert all(value is False for _, value in result.permissions)


def test_old_type_does_not_fall_back_to_checkout_or_cwd(tmp_path):
    from tests.diagnostics.actual_binding.legacy_probe import assert_old_exact_reference_rejected

    (tmp_path / "tests").mkdir()
    for path in (
        "tests/__init__.py",
        "contracts.py",
        "seven_input_contracts.py",
        "actual_binding.py",
    ):
        (tmp_path / path).write_text("raise AssertionError('ambient shadow executed')\n")
    assert_old_exact_reference_rejected(cwd=tmp_path)


@pytest.mark.parametrize("damage", ("missing_archive", "missing_member", "changed_member"))
def test_damaged_legacy_fixture_cannot_satisfy_actual_type_test(tmp_path, damage):
    from tests.diagnostics.actual_binding.legacy_probe import (
        ARCHIVE,
        assert_old_exact_reference_rejected,
    )

    dest = tmp_path / "legacy.zip"
    if damage != "missing_archive":
        with ZipFile(ARCHIVE) as original, ZipFile(dest, "w") as changed:
            for name in original.namelist():
                if name == "content.py" and damage == "missing_member":
                    continue
                data = original.read(name)
                if name == "content.py":
                    data += b"\n# changed historical bytes\n"
                changed.writestr(name, data)
    with pytest.raises(ValueError, match="historical fixture absent or corrupt"):
        assert_old_exact_reference_rejected(dest)


def test_legacy_fixture_and_vector_relocate_without_old_worktrees(tmp_path):
    from tests.diagnostics.actual_binding.legacy_probe import (
        ARCHIVE,
        assert_old_exact_reference_rejected,
    )

    dest = tmp_path / "한글 space" / "legacy.zip"
    dest.parent.mkdir()
    shutil.copyfile(ARCHIVE, dest)
    assert_old_exact_reference_rejected(dest, cwd=tmp_path)


def test_runtime_is_byte_identical_to_portable_reviewed_sources():
    from cyberpilot_autotune.diagnostics import actual_binding

    root = Path(actual_binding.__file__).parent
    path = (
        Path(__file__).resolve().parents[3]
        / "docs/evidence/actual_binding_integration_sources.json"
    )
    rows = json.loads(path.read_bytes())["runtime_files"]
    assert len(rows) == 9
    assert sorted(p.name for p in root.glob("*.py")) == sorted(r["file"] for r in rows)
    for r in rows:
        assert sha256((root / r["file"]).read_bytes()).hexdigest() == r["original_sha256"]


def test_namespace_preserves_original_content_identities():
    from cyberpilot_autotune.diagnostics.actual_binding._identity import (
        post_reference_identity,
        pre_reference_identity,
    )
    from tests.diagnostics.actual_binding.actual_binding_test_vectors import complete_vector

    # Golden captured from the pinned portable release, not from the code under test.
    v = complete_vector()
    assert pre_reference_identity(v.pre) == (
        "5866be784ccfcffff77d838255bb2185748f425237ff443cdaf9d025ec7a1642"
    )
    assert post_reference_identity(v.post) == (
        "063a6c56092c8b28b87be88d365a7ab8866ca9872d7bea3a1733dc4dee361e74"
    )
    assert dict((k, sha256(b).hexdigest()) for k, b in v.bundle.documents) == {
        "baseline": "30a7d55d91651834f4c86bd5083b37c2dee3147ec0acfb10458518b3cc711630",
        "command": "7229173953cb4b477bd72e51d62f67ef78ce2e9ac6023b222e1cbc0e951f0acb",
        "exit": "3f2a12e6f04d21d3a1e77d008c36281656395858b8615724daebaeaca22c6c3c",
        "intent": "fb48b083a0f04505a3514bd0910ccba14ae01b9a311a609b8056ead905e390d1",
        "preflight": "db4db0946f1b67f0c56ad830852ff63b5b606c80ddbcf581b6123ed118f47ebd",
        "snapshot": "17ecc02b38f06305b14d0a778d298ea4453f710fb3222b01ca3ccf58dd8abd74",
    }


@pytest.mark.parametrize("damage", ("extra", "missing", "changed", "changed_parent"))
def test_new_inventory_does_not_exempt_unknown_or_changed_source(tmp_path, damage):
    from tests.audit.diagnostic_inventory import verified_diagnostic_paths

    checkout = Path(__file__).resolve().parents[3]
    package = "src/cyberpilot_autotune/diagnostics"
    shutil.copytree(
        checkout / package, tmp_path / package, ignore=shutil.ignore_patterns("__pycache__")
    )
    manifest = "docs/evidence/actual_binding_integration_sources.json"
    (tmp_path / manifest).parent.mkdir(parents=True)
    shutil.copyfile(checkout / manifest, tmp_path / manifest)
    target = tmp_path / package / "actual_binding/assessment.py"
    if damage == "extra":
        (target.parent / "unknown.py").write_text("pass\n")
    elif damage == "missing":
        target.unlink()
    elif damage == "changed_parent":
        (tmp_path / package / "__init__.py").write_text("import os\n")
    else:
        target.write_bytes(target.read_bytes() + b"\n# changed\n")
    with pytest.raises(AssertionError):
        verified_diagnostic_paths(tmp_path)


@pytest.mark.parametrize(
    "path",
    (
        "tests/architecture/test_knowledge_boundary.py",
        "tests/audit/test_carrot_writer_ownership.py",
        "tests/audit/test_hoya_c3_atune_evidence.py",
        "MANIFEST.in",
    ),
)
def test_history_extension_requires_exact_guard_patch(path):
    from tests.audit import validate_friction_model as audit

    expected = audit.git_bytes(audit.ROOT, audit.BASE, path).replace(b"\r\n", b"\n")
    actual = (audit.ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    assert audit.historical_inventory_equivalent(path, expected, actual)
    assert not audit.historical_inventory_equivalent(path, expected, actual + b"\n# drift\n")
    assert not audit.historical_inventory_equivalent("unrelated.py", expected, actual)
