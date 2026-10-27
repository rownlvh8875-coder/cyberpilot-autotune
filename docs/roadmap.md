# Roadmap after Phase 0-4

Everything below is unimplemented. The next change should be one small shadow-only
learner PR, with the completed pinned source audit retained as provenance evidence.

## Phase 5: Conservative residual statistics learner

Build context-aware residual statistics using robust EWMA or an equally
conservative method. Require explicit minimum samples, reset rules for context
and validity changes, maximum state age and documented confidence calculation.
Return proposals only. Do not add controller references, IO or optimization
dependencies. Test known synthetic residual streams, outliers, missing signals,
override/saturation exclusion, resets, bounded memory, sample thresholds and two
fresh deterministic runs. Show no claim of vehicle performance improvement.

## Phase 6: Persistence

Design schema and learner versions, checksum, temporary file write, fsync and
atomic replace. Reject corruption, incompatible versions and incomplete writes;
never guess partial state recovery. Define ownership, permissions, allowed
location, maximum size, reset/expiry and opt-in policy. Test truncation at every
stage, replacement failure, checksum mismatch, incompatible state and safe
baseline fallback. Filesystem/OS guarantees must be explicitly scoped.

## Phase 7: Replay framework

Implement the deterministic schema in replay_spec.md with one small synthetic
golden fixture. Compare baseline versus shadow; report proposal count, rejection
reason counts, override/saturation exclusions, maximum proposed delta, invariant
violations, runtime latency and deterministic hash. Test malformed/unknown units,
reordered sequences, invalid timestamps, corruption and repeated fresh-process
hash identity. Real logs require a separate authorized data policy.

## Phase 8: Optional Carrot adapter

Pin the actual owner-selected branch and SHA. Isolate openpilot/cereal imports to
an optional adapter distribution/package. Core tests must still pass without
openpilot. Prove read-only mapping with mocks and golden unit/freshness fixtures,
including controller-specific saturation semantics and missing-signal vetoes.
Inspect actual types again rather than relying on old branch names. No controller
application, Params writes or vehicle installation is part of this phase.

## Phase 9: Bounded application RFC

Do not implement an application mode until an owner-approved parameter registry,
vehicle-specific hard bounds and rate limits, replay acceptance criteria,
rollback-latency criteria, watchdog contract, driver override priority, saturation
handling, state reset policy, parked test protocol and closed-course test protocol
all exist and have review evidence. Specify authorization and deployment policy
before adding a write capability. The present rate screening rule and synthetic
limits are not an approved application policy. Tests must include veto priority,
bounded transitions, stale-source rollback, injected faults and rollback latency.

## Phase 10: Small upstream PR series

1. Contracts, architecture and read-only adapter interface.
2. Fail-closed safety primitives.
3. Shadow runtime and invariant tests.
4. Learner, persistence and replay evidence, preferably further split by concern.
5. Optional Carrot integration against a pinned owner-selected target.

Each PR must be independently reviewable. Resolve licensing/provenance before
copying any code upstream. No ajouatom/openpilot PR is created during Phase 0-4.
