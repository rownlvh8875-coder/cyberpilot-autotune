# Replay completion evidence

## PR dependency

User-authorized PR #2 Ready transition preserved exact head
26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0. Before merge: OPEN, mergeable, main
base, eight successful checks, no review threads and no reviews/requested changes.
Merge_method=merge with exact-head guard succeeded at 2026-10-28T00:52:04Z.
Merge/main: fd8c60c111a6e25443f26093f424b8be0a605940; parents
05b016237afec7c53195cb802bef2c3ae8138a8c and
26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0. Ancestor check exited 0. Branch retained.

PR #3 retargeted from feat/shadow-residual-statistics to main, still OPEN/Draft.
Head stayed 950019643bab050f3cbafeddd1c926913ea1840a; mergeable became true after
GitHub's initial recomputation. Diff: 25 files, 6 commits, +2278/-49. Existing
Phase 5/admission implementation is absent from the diff. No rebase/force push.
Retarget-time CI had the existing eight successful head checks; completion pushes
must run the full matrix again against main.

Retarget file list:

```text
.github/workflows/ci.yml
CONTRIBUTING.md
MANIFEST.in
README.md
docs/architecture.md
docs/replay_acceptance.md
docs/replay_plan.md
docs/replay_progress.md
docs/replay_spec.md
docs/roadmap.md
examples/replay_synthetic.py
pyproject.toml
src/cyberpilot_autotune/replay/__init__.py
src/cyberpilot_autotune/replay/canonical.py
src/cyberpilot_autotune/replay/runner.py
src/cyberpilot_autotune/replay/schema.py
tests/architecture/test_boundaries.py
tests/fixtures/replay/golden_v1.expected.json
tests/fixtures/replay/golden_v1.json
tests/fixtures/replay_data.py
tests/integration/test_replay_golden.py
tests/integration/test_replay_runner.py
tests/property/test_replay_properties.py
tests/unit/test_replay_schema.py
tests/unit/test_replay_validation.py
```

## Ordering implementation

RED: schema blocked valid runtime-order anomaly tests. GREEN: only evaluation
clocks/domain remain ordered at decode; observation ordering reaches the existing
engine. Independent checker uses maxima for prior sequence and safe capture time,
including rejected frames. Regression: 426 passed; lint/format/type/diff checks pass.
Historical aggregate result digest remains unchanged. Engine, gate and residual
learner source files are untouched.

## Digest separation and learner characterization

RED: the three digest properties and characterization API were absent. GREEN:
scenario_sha256 hashes the whole validated scenario; configuration_sha256 hashes
exactly the seven user-specified configuration fields; result_sha256 hashes the
unchanged deterministic report v1 bytes. digest remains an alias. Formatting,
semantic input/policy/output mutations, timer independence and self-exclusion are
tested. Aggregate digest remains 5434e0cd203a08fb97662d94b91d66665bb950ba8cb276f90597efc8af673af5.

characterize_replay returns the report and immutable post-event sample counts
from the same real learner run. This sidecar does not change the historical report
projection; focused expected files and CLI compare it explicitly. None denotes
an empty evidence window, never a fabricated zero observation. Ordering counts:
1,2,None,None,None,None,1,None,None,1,None,None,1,2,3,4. Regression: 429 passed.

## CLI

RED: run/error tests failed because cli.py was absent. GREEN: run/verify/verify-all,
strict typed semantic expectation matching, bounded local reads, sorted discovery,
raw-error redaction and portable canonical stdout. Exits 0/2/3/4/5 are exercised.
Direct-entry and fresh-process outputs agree, including invalid UTF-8/oversized/
missing input, duplicate expected keys and unknown CLI flags. No update command.
AST permits only rb reads in cli.py and writes to stdout/stderr buffers; guarded
CLI execution forbids filesystem writes/network/threads/processes. Regression:
461 passed; overall coverage 98.51%, replay 98.45%; lint/format/type checks pass.
