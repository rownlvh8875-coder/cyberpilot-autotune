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

## Execution decisions

- The supplied architecture and explicit instruction to implement are sufficient
  authorization; no additional design approval step is introduced.
- Local git author is the repository owner's login and GitHub noreply address;
  no global git configuration is changed.
- First nonzero change has no rate evidence and is rejected. Missing required
  observations are rejected before learner execution.
