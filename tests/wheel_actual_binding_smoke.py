"""TEST_ONLY installed-wheel check; source vectors are synthetic, never admission."""

import argparse
import importlib.util
import json
import runpy
import sys
from hashlib import sha256
from pathlib import Path

from cyberpilot_autotune.diagnostics import actual_binding


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    installed = Path(actual_binding.__file__).resolve().parent
    assert installed.is_relative_to(Path(sys.prefix).resolve())
    assert not installed.is_relative_to(checkout)
    assert importlib.util.find_spec("actual_binding") is None, "duplicate top-level API"
    sources = json.loads(
        (checkout / "docs/evidence/actual_binding_integration_sources.json").read_bytes()
    )
    assert len(sources["runtime_files"]) == 9
    for row in sources["runtime_files"]:
        assert sha256((installed / row["file"]).read_bytes()).hexdigest() == row["original_sha256"]
    vectors = runpy.run_path(
        str(checkout / "tests/diagnostics/actual_binding/actual_binding_test_vectors.py")
    )
    vector = vectors["complete_vector"]()
    result = actual_binding.assess_actual_binding(
        vector.bundle, expected_pre=vector.pre, expected_post=vector.post
    )
    assert result.structural_status == "REPORTED_BINDING_CONSISTENT"
    assert result.status == "BLOCKED" and result.content_status == "NOT_EVALUATED"
    assert result.provenance == "BLOCKED_NO_INDEPENDENT_VERIFICATION"
    assert result.history == "UNAVAILABLE" and result.integrated_admission is False
    assert len(result.permissions) == 9 and all(value is False for _, value in result.permissions)
    missing = actual_binding.assess_actual_binding(
        vector.bundle, expected_pre=None, expected_post=None
    )
    assert missing.structural_status == "INCOMPLETE"
    assert not any(
        name.split(".")[0] in {"cereal", "openpilot", "capnp"}
        or name.startswith("cyberpilot_autotune.application")
        for name in sys.modules
    )
    print("ACTUAL_BINDING_WHEEL_PASS: 9 source hashes / canonical types / all9false / no admission")


if __name__ == "__main__":
    main()
