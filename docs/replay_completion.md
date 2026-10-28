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

## Focused fixtures and review

All three focused fixtures first failed verification while absent. Their event
reasons, sample counts and summary metrics were hand-derived and checked before
pinning new digests. constant_residual_v1: 5 events/3 proposals/3 eligible;
admission_reset_v1: 17/3/3; ordering_high_water_v1: 16/2/2. Every result retains
trusted baseline and has no INTERNAL_ERROR. Two fresh processes with distinct
hash seeds reproduce full canonical output, all hash domains, counts and reasons.
Original golden_v1 files remain byte-unchanged relative to 9500196.

One independent read-only review found a P2 verifier downgrade: any scenario could
use legacy expectations and omit event/sample-count/split-hash evidence. A RED test
reproduced acceptance of downgraded focused expectations. GREEN restricts legacy
compatibility to the historical aggregate result digest; focused expectations must
match the complete field set. No deferred findings. Separately, invalid metadata
types were reproduced returning unsupported exit 5 and corrected to input exit 2.

## CI and documentation

Local full regression now passes 475 tests; lint/format (88 Python files) and
strict mypy (31 source files) pass. The example delegates to the CLI, keeping file
reads at one explicit boundary. Matrix remains Ubuntu/Windows x Python 3.12.3/3.12,
on both push and PR. Overall coverage floor is 90%; safety/residual/replay remain
95%. CI invokes verify-all, fresh-process aggregate/focused tests, and installed
wheel CLI verification with an explicit fixture-directory argument outside checkout.
Version is 0.1.0a4, with zero runtime dependencies. No golden auto-update path.
Fresh-environment results and remote CI are recorded after execution.

## Fresh-environment verification

Remote clone at 4f3b2abff67e95c1e2b47833913b77026bdf3fc4 into the sibling
cyberpilot-autotune-replay-completion-clean directory, new CPython 3.12.14 venv.
Executed pip upgrade/editable dev install, diff check, ruff check/format --check,
strict mypy, full pytest, pytest-cov with 90% floor, all three 95% package floors,
CLI verify-all and wheel/sdist build. Results:

- 475 passed, 0 failed, 0 skipped; overall branch coverage 98.53%; safety 100.00%;
  residual learner 97.85%; replay 98.48%. Ruff/format: 88 files; mypy: 31 sources.
- Wheel and sdist 0.1.0a4 built. Artifacts/caches stay ignored and source tree clean.
- Separate fresh sibling wheel venv, only package and pip, --no-deps installation.
  Isolated Python outside checkout imports package plus all 30 submodules.
- Installed wheel's `-I -m cyberpilot_autotune.replay.cli verify-all` passes with an
  explicit fixture-directory argument. All four fixture hashes and every event's
  trusted baseline check pass. No INTERNAL_ERROR/invariant violations occur.
- CLI run/verify/verify-all success exits 0. Malformed/missing/oversized/invalid
  UTF-8 input and invalid flags exit 2; changed counts/reasons/digests/sample counts
  or downgraded focused expectations exit 3; injected invariant/internal faults exit
  4; unsupported recognized configuration exits 5. Raw input/path/exception text
  is absent from stderr. No update-golden capability exists.
- Guarded CLI execution and AST checks enforce no filesystem writes/network/thread
  or process creation and no vehicle dependencies. Engine/gate/learner and both
  historical aggregate fixture files are byte-unchanged from 9500196.

Code/delivery SHA 4f3b2ab passed all four matrix jobs for both push and PR (8/8):
[push](https://github.com/rownlvh8875-coder/cyberpilot-autotune/actions/runs/40613175679),
[PR](https://github.com/rownlvh8875-coder/cyberpilot-autotune/actions/runs/40613180849).
The completion-record commit changes docs only. Final SHA/check results are kept
in PR #3, which remains Draft/HOLD. No new phase starts; persistence remains
NOT_AUTHORIZED, with no real log loader, adapter, application or live vehicle test.

## Digest manifest

| Fixture | Events | Proposals | Eligible | Scenario SHA-256 | Configuration SHA-256 | Result SHA-256 |
|---|---:|---:|---:|---|---|---|
| golden_v1 | 21 | 5 | 2 | ba456b58382795f9734fd33f9e40331d09cb9ad648eaa564b5f309afce304952 | 9e35a0f23565f9f57c7f42145cfde9ac1e7471a2738e6339b8268f4eedc274e1 | 5434e0cd203a08fb97662d94b91d66665bb950ba8cb276f90597efc8af673af5 |
| constant_residual_v1 | 5 | 3 | 3 | c9998aff17ec5481cd48338f750b5e479a44dbe8ffc440fb67f69ffb60d4a480 | 9e35a0f23565f9f57c7f42145cfde9ac1e7471a2738e6339b8268f4eedc274e1 | 44b7b8210df78f3e0fd885655f8c123ca4a556c8486ce01c565a56733c17b383 |
| admission_reset_v1 | 17 | 3 | 3 | 98700a3b86cf3e68c180bc4cd4ea1cb0492be89ee177387af29a326903f51e17 | 9e35a0f23565f9f57c7f42145cfde9ac1e7471a2738e6339b8268f4eedc274e1 | 1c566a3e8626a924217acaab5ca2a4343c4de64590ff5a56bf200b5a8404e294 |
| ordering_high_water_v1 | 16 | 2 | 2 | 107698ff144c9a6411268bc52dab1d72f085ba72623119c56a5294647bc4a2eb | 685d4192b1043704bf77d993ed176b74b47dfdad7baa142b4e404a565d4a9a0b | 7a6b70118a247342ea68453bf7b6193088e374dc974b1e3fb8b9416ff25e1ae2 |

All full canonical CLI outputs and their hash/count/reason fields are checked in
two fresh processes with distinct hash seeds. The pinned expectations run in all
Windows/Ubuntu x Python CI jobs; latency is absent from output/hash comparisons.
Aggregate's result digest and fixture bytes are unchanged. The separate sample
count sidecar is checked directly by focused expectations, outside historical
report v1 hashing; it is not silently added to that compatibility projection.

## Change scope

Completion adds six append-only commits after preserved head 9500196 (12 total
replay commits relative to main), changing 33 files during completion, 39 files in
the complete PR diff. Source changes are confined to replay/. Final full file
list, exact SHA and current CI are available in PR #3. No Phase 5/admission
implementation reappears, no branch was deleted and no history was rewritten.
