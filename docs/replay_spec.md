# Future deterministic replay specification (Phase 7, not implemented)

This is the next single work item after admission hardening. The harness is not
implemented by that hardening. Replay acceptance criteria must precede any later
persistence work; persistent learner state remains unauthorized.

Only small programmatically constructed synthetic observations are used today.
There is no replay runner, real log reader or automatic driving-data collection.

Proposed schema v1 will contain an ordered list of canonical observations,
explicit source units, source validity, actual control_active and source age, monotonic timestamp
origin, sequence, a versioned nonidentifying context, baseline/spec snapshots and
injected clock readings. Missing data will remain null and must never become zero.
Reject unknown schema versions, non-finite JSON values, duplicate keys, unordered
sequences, inconsistent time domains and ambiguous units before execution.

A synthetic golden fixture must specify expected proposal count, rejection counts
by stable ReasonCode, override/saturation exclusion counts, maximum proposed
delta, safety invariant violations (required zero), and baseline/shadow comparison.
Every effective value must equal baseline in this milestone and future shadow
replay. Record total/per-event latency as a separate nondeterministic measurement;
do not mix timing measurements into the deterministic output hash.

Canonical serialization for hashing will use sorted parameter IDs, exact ordered
events, a declared float encoding, schema/learner/config versions and no wall
clock, filesystem paths, driver IDs, VINs, GPS or video. Golden digest tests must
run in two fresh processes; corruption and schema incompatibility must fail
closed. Cross-platform numeric determinism needs evidence before claims.

Replay acceptance criteria and authorized source provenance require owner review.
Performance improvement cannot be inferred from candidate acceptance counts.
