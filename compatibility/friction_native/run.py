"""Required source-backed native tests; offline, never starts openpilot services."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from compatibility.friction_native import bundle

BASE = "cd02d81b745565aa8ae41d4799fd1b1687f2a07e"
FREEZE = "2f137a2"
ROOT = bundle.ROOT


def manifest(reference):
    before = bundle.originals(reference)
    after = bundle.instrument(before)
    return {
        "schema": "passive-native-friction-patch-v1",
        "native_base": bundle.PIN,
        "cyberpilot_base": BASE,
        "instrumented_native_revision": None,
        "q_observed": None,
        "deployment_performed": False,
        "runtime_qualified": False,
        "empirical_qualified": False,
        "application_authorized": False,
        "source_files": [
            {"path": path, "sha256": hashlib.sha256(bundle.git_bytes(reference, path)).hexdigest()}
            for path in bundle.reference_paths()
        ],
        "target_files": [
            {"path": path, "sha256": hashlib.sha256(after[path]).hexdigest()}
            for path in bundle.EDIT_PATHS
        ],
        "patch_sha256": hashlib.sha256(bundle.patch(before, after).encode()).hexdigest(),
    }


def history():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args])

    paths = git("ls-tree", "-r", "--name-only", BASE).decode().splitlines()
    authorized = {
        ".github/workflows/ci.yml",
        "tests/audit/validate_carrot_friction_patch_design.py",
    }
    for path in paths:
        old = git("show", BASE + ":" + path)
        if path not in authorized:
            if git("show", "HEAD:" + path) != old:
                raise ValueError("BASE_COMMITTED_BLOB_CHANGED:" + path)
            if (ROOT / path).read_bytes().replace(b"\r\n", b"\n") != old.replace(b"\r\n", b"\n"):
                raise ValueError("BASE_WORKING_COPY_CHANGED:" + path)
    validator = "tests/audit/validate_carrot_friction_patch_design.py"
    before = git("show", BASE + ":" + validator).decode()
    old_function = "    return actual in (original, extend_ci(original))"
    new_function = (
        "    from compatibility.friction_native.ci import extend as native_extension\n\n"
        "    design = extend_ci(original)\n"
        "    return actual in (original, design, native_extension(design))"
    )
    if (ROOT / validator).read_text() != before.replace(old_function, new_function, 1):
        raise ValueError("HISTORICAL_VALIDATOR_EXTENSION_ONLY")
    from compatibility.friction_native.ci import extend

    ci = ".github/workflows/ci.yml"
    if (ROOT / ci).read_text() != extend(git("show", BASE + ":" + ci).decode()):
        raise ValueError("CI_ADDITIVE_ONLY")
    if git("diff-tree", "--no-commit-id", "--name-only", "-r", FREEZE).decode().splitlines() != [
        "docs/superpowers/plans/2026-10-29-carrot-passive-producer-implementation.md"
    ]:
        raise ValueError("PREIMPLEMENTATION_FREEZE")
    return {
        "base_files": len(paths),
        "authorized_extensions": sorted(authorized),
        "other_committed_blobs_exact": True,
        "working_tree_comparison": "CRLF_NORMALIZED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-checkout", required=True, type=Path)
    parser.add_argument("--verify-history", action="store_true")
    args = parser.parse_args()
    import capnp
    import pytest

    if capnp.__version__ != "2.1.0":
        raise ValueError("PINNED_PYCAPNP_REQUIRED")
    actual = manifest(args.reference_checkout)
    evidence = json.loads((ROOT / "docs/evidence/carrot_passive_native_patch.json").read_text())
    if actual != evidence:
        raise ValueError("NATIVE_PATCH_SOURCE_OR_TARGET_DRIFT")
    before = bundle.originals(args.reference_checkout)
    if (bundle.ASSETS / "instrumentation.patch").read_text() != bundle.patch(
        before, bundle.instrument(before)
    ):
        raise ValueError("PATCH_REGENERATION_MISMATCH")
    if args.verify_history:
        print(json.dumps(history(), sort_keys=True))
    os.environ["FRICTION_NATIVE_REFERENCE"] = str(args.reference_checkout.resolve())
    sys.dont_write_bytecode = True
    result = pytest.main(
        [str(ROOT / "tests/native_friction"), str(ROOT / "compatibility/friction_native"), "-q"]
    )
    if result != 0:
        return result
    print(
        "PASSIVE_NATIVE_PATCH_OFFLINE_PASS: "
        "no deployment/runtime/empirical/application qualification"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
