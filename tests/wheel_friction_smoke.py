"""Execute the installed H6 wheel outside checkout; no native/runtime imports."""

import argparse
import hashlib
from pathlib import Path

from cyberpilot_autotune.research import friction_model
from cyberpilot_autotune.research.friction_model.candidates import fit
from cyberpilot_autotune.research.friction_model.experiments import run_experiments, toy_context
from cyberpilot_autotune.research.friction_model.synthetic import Scenario, generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expect-optional-dependency", action="store_true")
    args = parser.parse_args()
    installed = Path(friction_model.__file__).parent.resolve()
    assert not installed.is_relative_to(args.source_root.resolve())
    count = 0
    for source in (args.source_root / "cyberpilot_autotune/research/friction_model").glob("*.py"):
        expected = hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        actual = hashlib.sha256(
            (installed / source.name).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        assert expected == actual
        count += 1
    assert count == 6
    rows = generate(Scenario(), toy_context())
    if args.expect_optional_dependency:
        try:
            fit(rows, "controller")
        except ValueError as error:
            assert str(error) == "RESEARCH_EXTRA_REQUIRED"
            print("H6_OPTIONAL_DEPENDENCY_AND_6_WHEEL_HASHES_PASS")
            return
        raise AssertionError("vanilla wheel unexpectedly fits without NumPy")
    result = fit(rows, "controller")
    assert abs(result.estimate - 0.17) < 1e-10
    assert not result.owner_proposal_allowed
    report = run_experiments(args.policy.read_text())
    assert report["selected_model"] == "NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS"
    assert len(report["scenarios"]) == 26
    assert not any(report["authority"].values())
    print("H6_WHEEL_PASS: 6 hashes / 4 candidates / 26 scenarios / all authority false")


if __name__ == "__main__":
    main()
