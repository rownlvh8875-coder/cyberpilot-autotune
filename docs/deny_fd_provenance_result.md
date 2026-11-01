# Denial-FD provenance: local implementation result

## Scope and meaning

Base: `1c4fb3d26db913645cb2292f362396076e47adcb` (PR53 head).
Local branch: `feat/deny-fd-provenance-contract`.
Only the approved two existing and eleven new paths change; cumulative history
scope is forty paths. No push, PR creation/update, CI publication, merge, rebase,
force push, or prior PR/main modification is part of this work.

The test-only `tests/deny_fd_provenance` package provides immutable, exact-type
validated neutral receipts and a pure evaluator. It separates configured subject,
actual operation, and causal FDs. FD0 is valid; unknown, zero and empty inventory
are distinct. The supported synthetic case is PRE_EXEC_INVENTORY/UNEXPECTED_FD:
complete exact-cohort FD witnesses precede the snapshot and denial in sequence
and observation time, and observed-minus-expected equals the causal FD set.
Cause references must match the individual inventory references, including slot
context. HH03-like synthetic data has configured subject0, operationNone,
observed(0,3), expected(0,), cause(3,).

Observed receipts are explicitly rejected as PRODUCER_NOT_IMPLEMENTED. Other
stages/reasons, missing or mixed inventories, incomplete provenance and wrong
clock/cohort/order are rejected rather than silently interpreted. Even a
SYNTHETIC_DIAGNOSTIC_CONSISTENT decision remains BLOCKED with all nine permissions
false. Digests identify content only, not authenticity or authority.

## Successor history policy

Immutable P2: `a7b632f2f331c4029789e2ace7ed8cdb8bb48ca2`.
It descends from the exact base and records27preserved old-phase paths plus the
two finalized modified postimages. The separate new loader pins P2 after that
commit, avoiding self-hashing. It verifies lineage, raw Git blobs, modes,
HEAD/index/worktree, and the exact eleven additions. Missing local objects fail
without fetch or fallback. Original P,22postimages, old scopes and seven additions
remain unchanged. Historical mutable-manifest acceptance runs at fixed1c4;
current immutable loading still ignores that file, while preservation rejects
working-copy corruption. All original architecture guard files remain unchanged.

## Verification evidence

- Baseline:4,295tests passed. Implementation checkpoint:4,397tests passed.
- New contract and purity tests:70passed;255statements/70branches covered100%.
- History and architecture checkpoint:193passed, including actual Git mutations
  across HEAD/index/worktree, modes, CRLF, missing P2 and unlisted additions.
- Ruff check/format, installed-source mypy and separately typed new pure package.
- Package coverage checkpoint:98.52%; safety100%, residual97.85%, replay98.48%,
  receipt adapter100%, knowledge99.71%, owner99.41%. Research and observability
  coverage validators pass their unchanged gates.
- An earlier coverage run failed one scope assertion while other verification
  was concurrent; the same assertion passed alone. Root cause was not established.
  Serialized whole-suite coverage rerun:4,397passed,98.52%. The earlier failing
  run is not treated as a green verification result; its root cause remains
  unconfirmed and must be investigated if it recurs.
- Existing source/history audits pass without claiming unavailable external raw
  source verification. FD/OFD audit explicitly reports kernel_bytes_verified=false
  and runtime_qualified=false. Legacy offline audit replays9captures/4scoped
  transports, all BLOCKED. Replay integration11passed and4goldens match.
- Isolated sdist/wheel build passes. All72wheel package files are byte-identical
  to base source; test/compatibility packages are excluded. Outside-checkout fresh
  wheel imports70submodules. Replay, Carrot optional-dependency/receipt,
  knowledge, owner, science and friction smoke tests pass; research dependency
  absence is checked before installing extras and rerunning the scientific smoke.
- Original v1 producer/checker/capture and22postimages remain byte-identical.
  Exact final SHA, fresh-context internal review and final rerun belong to the
  handoff evidence, not an assertion of GitHub CI or independent human approval.

## Preserved blockers and next boundary

DENY_FD_POINT_PROVENANCE_CONTRACT_READY

DENY_FD_HISTORY_SUCCESSOR_POLICY_READY

PRODUCER_NOT_IMPLEMENTED

LEGACY_PR34_M1_OPEN

FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED

APPLICATION_NOT_AUTHORIZED

No legacy-v1-to-observed-v2 adapter, new C producer, wire decoder, kernel/guest
execution, runtime qualification, installed package change, candidate generation,
vehicle/Params/controller/schema mutation, application/owner bridge or deployment
is implemented. The proposed future observed-v2 wire is design only and cannot
promote original v1 evidence. Recommended next bounded task is publication and
exact-head CI review of this local branch, requiring separate authorization;
it must not modify prior PRs or imply producer/runtime qualification.
