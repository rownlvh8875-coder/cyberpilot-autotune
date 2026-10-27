# Progress

## Phase 0

- 2026-10-28: target remote had no refs; initial main commit bf042cc contains
  README.md and .gitignore only. All subsequent work is on feat/bootstrap-shadow-core.
- Dedicated previously empty checkout provides feature-branch isolation. No
  existing user work required a second worktree.
- References cloned to sibling directories; no source commits, branches or pushes.
- Corrected official pinned CyberPilot baseline:
  588d6b21c21089065a7d9165d6e7a438e8aa6297. The initial prompt had a SHA typo;
  the user supplied the correction and authorized unifying provenance on it.
- Branch-ref fetch, cat-file, detached checkout, rev-parse and full commit metadata
  verified. The separately recorded current HEAD equals the pinned baseline.
- Actual Carrot refs and Python configuration inspected; see carrot_integration.md.
- No source code copied. Pinned-source audit blocker is resolved; selected
  responsibilities and unresolved per-file attribution are documented.
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
- The earlier source-object blocker was subsequently resolved by the user's
  explicit SHA correction; all current documents use the corrected official pin.

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

## Architecture and regression verification

- AST tests cover all package layers for forbidden vehicle imports, dynamic
  import/code execution, and write APIs. The adapter exposes only to_observation.
- Six fresh guarded import processes verified every package module plus OFF and
  SHADOW with no file writes, sockets or threads. All tests deny network access.
- Added generated deterministic stream properties, arbitrary malformed input,
  non-finite runtime input and atomic discard after a second gate evaluation fails.
- Independent read-only reviewer found no Critical, Important or Minor findings
  in source through b08da16. Reviewer ran 165 tests, lint/format/mypy and targeted
  edge-case probes. Subsequent changes add tests/docs only.
- Review exclusions stand because they match the authorized scope: future learner,
  integration/application/persistence/replay; hostile in-process code/private-state
  mutation; hard preemption; untrusted standalone gate history; standalone gate
  exception recovery; first-frame nonzero acceptance and in-place fault recovery.
  Source-object concern is resolved by the explicit corrected pin. Parent verified
  architecture and final docs separately. No deferred review findings remain.

## Execution decisions

- The supplied architecture and explicit instruction to implement are sufficient
  authorization; no additional design approval step is introduced.
- Local git author is the repository owner's login and GitHub noreply address;
  no global git configuration is changed.
- First nonzero change has no rate evidence and is rejected. Missing required
  observations are rejected before learner execution.
