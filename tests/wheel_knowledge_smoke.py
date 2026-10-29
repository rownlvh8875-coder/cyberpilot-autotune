"""Run outside checkout against a fresh, dependency-free installed wheel."""

import sys

from cyberpilot_autotune.knowledge.contracts import Confidence
from cyberpilot_autotune.knowledge.steering import get_registry

PINS = (
    "0e9c589c1b83027146f909a9cdc306c2c665ceaf",
    "c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
    "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
)
for revision in PINS:
    registry = get_registry(revision)
    assert registry is not None and len(registry.parameters) == 9
    assert len(registry.claims) == 26
    assert sum(p.evidence_status is Confidence.PROVEN for p in registry.parameters) == 6
    assert registry.get_proven("LateralTorqueAccelFactor") is None
    assert registry.get_any("CarSelected3") is None
    assert all(p.digest == p.digest and len(p.digest) == 64 for p in registry.parameters)
assert get_registry("carrot-wip") is None
assert not any(
    m.split(".")[0] in {"openpilot", "cereal", "opendbc", "selfdrive"} for m in sys.modules
)
print("KNOWLEDGE_WHEEL_SMOKE_PASS: 3 profiles / 27 descriptors / no runtime dependency")
