# Progress

## Phase 0

- 2026-10-28: target remote had no refs; initial main commit bf042cc contains
  README.md and .gitignore only. All subsequent work is on feat/bootstrap-shadow-core.
- Dedicated previously empty checkout provides feature-branch isolation. No
  existing user work required a second worktree.
- References cloned to sibling directories; no source commits, branches or pushes.
- BLOCKER: pinned CyberPilot 588d6baff90d5ed839b41554f447f12c7f23bed3 cannot
  be fetched (upload-pack: not our ref); GitHub API independently returned 422
  No commit found. Pinned audit remains incomplete and the baseline is unchanged.
- Supplemental HEAD inspected separately: 588d6b21c21089065a7d9165d6e7a438e8aa6297.
- Actual Carrot refs and Python configuration inspected; see carrot_integration.md.
- No source code copied. Full Phase 0-4 acceptance cannot be claimed until the
  unavailable pinned source audit is resolved; independent software work proceeds.
- Phase 0 verification: git diff --check. Python checks N/A (no package yet).

## Phase 1

- Import smoke RED: 1 failed because find_spec returned None before scaffolding.
- GREEN: editable installation succeeded; 1 passed, mypy 0 errors, ruff 0 errors.
- Added src layout, py.typed, Python constraints, dev tools, coverage configuration,
  CI including wheel isolation, README, CONTRIBUTING, SECURITY and PR template.
- Workflow safety/import targets are exercised when Phase 3/4 modules exist.

## Phase 2

- Contract tests RED: missing contracts module caused the expected test failure.
- GREEN: 74 tests passed; numeric validation, immutability, alias protection,
  unsupported modes and decision/result invariants covered.
- Typed ValidationError remains visible at construction. Source validity and
  optional override/saturation flags reject numeric boolean substitutes.

## Phase 3

- Gate tests RED: missing safety.gate caused expected failure before implementation.
- Ordered stateless gate, exact bounds/step/rate checks and stable reason codes
  implemented with no real parameter defaults or clipping.
- Initial regression: 125 passed, 93.42% overall branch-inclusive coverage.
- Additional malformed metadata checks exercise fail-closed paths; final counts
  and safety coverage are recorded in the final validation section.
- Required pinned object remains unavailable; user could not supply a corrected
  SHA. This is recorded as unresolved, without substituting supplemental HEAD.

## Phase 4

- Runtime tests RED: missing runtime.engine caused expected failure.
- Added OFF/SHADOW engine, injected clock, NoOp learner, read-only adapter Protocol
  and in-memory diagnostics. ScriptedLearner exists only in test fixtures.
- A forged uninitialized dataclass regression was observed RED (metadata escaped
  before try); moving metadata extraction inside the outer boundary made it GREEN.
- 165 tests passed; overall branch-inclusive coverage 96.96%, safety 100%.
- Synthetic example printed ACCEPTED_FOR_SHADOW for an independently constructed
  demonstration proposal and effective == baseline: True. Packaged NoOp produces
  no proposals; the runtime evaluation path is exercised by test-only learners.
- Internal faults latch unhealthy until engine replacement. Clock regression and
  completed slow learner work fail closed, without claiming preemption deadlines.

## Execution decisions

- The supplied architecture and explicit instruction to implement are sufficient
  authorization; no additional design approval step is introduced.
- Local git author is the repository owner's login and GitHub noreply address;
  no global git configuration is changed.
- First nonzero change has no rate evidence and is rejected. Missing required
  observations are rejected before learner execution.
