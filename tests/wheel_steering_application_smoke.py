"""Installed-wheel synthetic commit/readback/rollback, never a vehicle writer."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    args = parser.parse_args()
    import cyberpilot_autotune
    from cyberpilot_autotune.application.coordinator import BoundedSteeringApplicator

    assert Path(sys.prefix) in Path(cyberpilot_autotune.__file__).resolve().parents
    sys.path.insert(0, str(args.repository))  # src layout does not shadow installed package
    from tests.fixtures.steering_application import (
        Authority,
        Clock,
        MemoryTarget,
        baseline,
        policy,
        request,
    )

    p, clock = policy(), Clock()
    target = MemoryTarget(clock, baseline(p))
    app = BoundedSteeringApplicator(p, baseline(p), target, Authority(), clock)
    result = app.process(request(p))
    assert result.reason.value == "VERIFIED" and target.current.values["lat_accel_factor"] == 11.0
    assert app.disarm().effective_parameters == baseline(p).values == target.current.values
    assert "cyberpilot_autotune.runtime.engine" not in sys.modules
    assert "cyberpilot_autotune.core.residual" not in sys.modules
    assert "openpilot" not in sys.modules
    print("SYNTHETIC_STEERING_APPLY_ROLLBACK_WHEEL_VERIFIED")


if __name__ == "__main__":
    main()
