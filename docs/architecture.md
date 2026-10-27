# Architecture

This is a research library, not a vehicle control system. The user-supplied
Phase 0-4 specification and subsequently approved Phase 5 learner are the
implementation authority. See phase5_design.md for the statistical contract.

```mermaid
flowchart TD
  Source[Mock or future observation source] --> Adapter[Read-only adapter contract]
  Adapter --> Snapshot[Immutable ObservationSnapshot]
  Snapshot --> Learner[Proposal-only Learner]
  Learner --> Gate[Fail-closed SafetyGate]
  Gate --> Engine[OFF / SHADOW enforcer]
  Baseline[Trusted immutable baseline] --> Engine
  Engine --> Result[EngineResult: effective equals baseline]
```

Contracts use frozen dataclasses, defensive tuple copies and immutable mappings.
Constructors reject invalid types, booleans masquerading as numbers, non-finite
values and invalid ranges with a typed ValidationError. Missing optional signals
are None; missing required gate signals veto eligibility.

SafetyGate is a stateless evaluator with an immutable registry and explicit
configuration. The engine owns a single stream's high-water sequence, observation
time and evaluation time. It admits an observation before invoking the learner.
Invalid, stale or reordered observations never reach the learner. Admitted frames
consume their sequence even if a learner fails. A new engine resets this state.

The engine is configured with a trusted baseline; untrusted snapshots cannot
replace that fallback. It has no controller reference, callbacks, external sinks,
network, threads or persistence. OFF does not read the clock or change stream
state. SHADOW records proposals and decisions in memory only. Every result is
constructed with the same immutable baseline as its effective mapping.

The gate checks each proposed delta against the baseline. Its rate budget is
maximum_rate_per_second times the interval since the preceding admitted frame.
On the first frame only an unchanged candidate has a known zero rate. This is a
conservative shadow screening rule, not a future application rate policy.

Only the engine's outer processing boundary catches unexpected Exception. It
discards partial proposals/decisions, emits INTERNAL_ERROR and preserves baseline.
Constructor/configuration errors remain visible. Diagnostics contain exception
type only, never exception messages, tracebacks, raw inputs or source identities.
SystemExit and KeyboardInterrupt remain process-level signals.

Alternatives considered: copying the existing offline experiment suite would
retain native controller/process dependencies; embedding this in controlsd would
prevent independent validation. The selected standard-library core makes future
small upstream PRs possible. It is single-owner, synchronous and not a real-time
or hostile-plugin sandbox. A learner that hangs cannot be preempted here; no hard
deadline guarantee is claimed.

Phase 5 adds one bounded, context-aware residual-statistics learner. It receives
an explicit target specification and conversion policy, retains no raw history,
and emits only proposals. The optional ResettableLearner lifecycle clears evidence
when SHADOW rejects an observation before or after learner work. Existing stateless
learners need only observe(). OFF invokes neither method. A faulted engine cannot
resume; use a fresh/reset learner when constructing its replacement. Each engine
owns its learner exclusively. Persistence and external data ingestion remain absent.
