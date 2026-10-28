"""Installed-wheel receive bridge smoke; never launches native SubMaster."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--reference-checkout", type=Path)
    args = parser.parse_args()
    import cyberpilot_autotune

    assert Path(sys.prefix) in Path(cyberpilot_autotune.__file__).resolve().parents
    from cyberpilot_autotune.integrations.carrot.errors import CarrotDependencyUnavailable
    from cyberpilot_autotune.integrations.carrot.sidecar.source import require_live_dependencies

    if args.reference_checkout is None:
        try:
            require_live_dependencies()
        except CarrotDependencyUnavailable:
            print("SIDECAR_OPTIONAL_DEPENDENCY_ERROR_VERIFIED")
        else:
            raise AssertionError("unexpected native dependency in the base wheel environment")
        return
    sys.path.insert(0, str(args.reference_checkout))
    sys.path.insert(0, str(args.repository))
    from compatibility.carrot.sidecar_streams import stream
    from cyberpilot_autotune.integrations.carrot.sidecar.runner import SidecarRunner
    from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
    from tests.fixtures.sidecar import ScriptedSubMaster

    for name, override in (("hyundai_false", False), ("hyundai_true", True)):
        cfg, frames = stream(name)
        source = SubMasterSource(ScriptedSubMaster(frames), cfg.adapter.attestation.session)
        runner = SidecarRunner(cfg, source, clock=lambda: 10_010_000_000)
        decisions = []
        for _ in frames:
            decisions.extend(runner.poll_once())
        assert decisions[-1].snapshot.driver_override is override
        assert decisions[-1].snapshot.baseline_parameters == cfg.adapter.baseline_parameters
        assert runner.diagnostics().receipt_attempt_count == 1
        runner.close()
    assert "cyberpilot_autotune.runtime.engine" not in sys.modules
    assert "cyberpilot_autotune.core.residual" not in sys.modules
    assert Path(sys.prefix) in Path(cyberpilot_autotune.__file__).resolve().parents
    print("SIDECAR_ACTUAL_SCHEMA_WHEEL_VERIFIED_2_STREAMS")


if __name__ == "__main__":
    main()
