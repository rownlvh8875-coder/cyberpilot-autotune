# Proposed deterministic read-only Episode Observer

Status: **EPISODE_OBSERVER_DESIGN_READY** as a design proposal. No observer runtime
module exists or is added by H1. Real runtime/parked qualification is separate.
Decider for implementation: owner, by a subsequent request. Design choices below
are audit recommendations, not previously approved product behavior.

## Intent and alternatives

Retain useful Hoya episode vocabulary while preserving exact evidence, uncertainty
and existing learning admission. The observer answers what was observed and what
deserves investigation; it does not identify safe parameter values.

1. Read-only consumer of existing exact neutral evidence: recommended; one
   observation contract, bounded state and explicit unavailable inputs.
2. Port Hoya saved-log/latest-slot detector: rejected; mixed cohorts, rounded/default
   values, gaps and controller-agnostic thresholds violate the current boundary.
3. Put episode detection inside the learner/gate: rejected; diagnostic policy must
   not mutate statistical evidence, admission or veto decisions.

See [source comparison](hoya_c3_atune_audit.md) and H:episodes/H:telemetry evidence.

## Proposed input boundary

The observer may consume immutable already-extracted data supplied by the caller:

| Input | Contract |
|---|---|
| Accepted ObservationSnapshot | Original sequence/context/baseline and source age; no replacement of unavailable values |
| MappingDecision diagnostics | Rejection reason/cohort/source-quality facts; a rejected partial diagnostic cannot reconstruct a Snapshot |
| GateDecision summary | Original reason/version and correlated observation identity; no reconsideration of gate result |
| Shadow proposal summary | Explicit research-only candidate identity/statistics, not a commit or owner permission |
| Optional driver feedback | Separately supplied, non-identifying self-report with its own provenance and scope |

No SubMaster, Cap'n Proto extraction, message cache, Params, raw log loader,
controller object, learner or application capability is passed in. Future live
ingestion must first satisfy PR #8 and parked qualification. The observer cannot
make an unavailable source available or repair a rejected mapping attempt.

## Proposed policy and bounded state

Caller-supplied immutable policy must explicitly specify supported contract/
heuristic versions, allowed diagnostic types, units, relevant controller/context,
maximum records/window capacity, window duration, maximum source age/skew, minimum
coverage, continuity/gap rules, minimum dwell, hysteresis and threshold predicates
where applicable. No vehicle/default threshold or pre-intervention N is supplied.
Incomplete policy prevents the affected detector from producing an episode.

Proposed state is a bounded in-memory window and a bounded deterministic event
history. No persistence, files, threads, network or autonomous execution. Consume
input identity once; duplicates/ordering faults cannot produce another episode.
Do not compare transitions across session/context/baseline epoch changes, cache
loss or timestamp gaps. Reset window explicitly on such discontinuities, retaining
their diagnostic fact. A new observer window does not reset learner or adapter
high-water/session state. The observer cannot replay an old window into learning.

Window processing is deterministic: stable event ordering by session/sequence/
cohort, explicit interval endpoints, stable aggregation order and ties. Diagnostic
heuristic versions and policy digests bind results. Numeric thresholds are never
described as actuator limits or vehicle-approved safety bounds.

## Immutable EpisodeRecord proposal

| Field group | Meaning |
|---|---|
| Identity | Diagnostic schema/heuristic version, policy digest, context/session and deterministic episode identity |
| Time | Clock-domain label, start/end observation sequence and monotonic timestamps; no wall-clock substitution |
| Cohorts | Original mapping receipt (source CC time, host apply time), source CS identity where available; unavailable stays absent |
| Coverage | Available/expected counts, gaps, exclusions and truncation; no invented continuous window |
| Observed facts | Explicit signal/predicate/transition and source quality, units and controller context |
| Hypotheses | Separate unproven cause labels with evidence references and uncertainty; never overwrite observed facts |
| Classification | DIAGNOSTIC_ONLY; no numerical target, SteeringRequest, authorization, lease or safety approval |

A stable hash identifies content, not authenticity or authority. Baseline mapping
is never mutated; baseline epoch may be retained as non-identifying context, not
converted into an approved registry.

## Candidate events and actual available inputs

| Candidate | Existing exact input | Proposed meaning | Limitation |
|---|---|---|---|
| Driver steering intervention | Qualified sourceCS steeringPressed via exact contract; explicit prior/current value | DRIVER_INPUT_TRANSITION | No edge across gaps; no motive/physical steering claim |
| Tracking deviation | Desired pre-controller and VM-estimated measured curvature, speed and controller context | Difference exceeded caller diagnostic policy | VM estimate is not a physical sensor truth; not lane departure |
| Controller limit | Same-cohort instantaneous/output tri-state diagnostics | Limit was explicitly observed | Never use timer-saturated as a substitute; unknown not False |
| Target mismatch | Source-bound pre-controller target and returned host request/output evidence if separately provided | Specific software-stage difference | MEB correction is expected, not automatic tracking fault; current Snapshot alone lacks full actuator tuple |
| Source quality loss | Mapping/gate rejection reasons and identities | Known missing/stale/invalid evidence | No reconstructed numerical sample from rejection |
| Harsh lateral response | No independent physical lateral-acceleration measurement in initial Snapshot contract | UNRESOLVED_INPUT | Do not promote curvature×speed² to physical acceleration |
| Brake/gas intervention | No canonical brake/gas fields in current Snapshot | UNRESOLVED_INPUT | No latest-topic or Boolean-default extension |
| Lead response/departure/catch-up | No exact radar/lead/longitudinal target contract here | UNRESOLVED_INPUT | FUTURE_LONGITUDINAL_EPISODE only |
| Curve-speed mismatch | No exact navigation target/source join here | UNRESOLVED_INPUT | Source-not-vturn alone does not imply wrong speed |
| Physical lane drift | No approved lane position/road-truth input | UNRESOLVED_INPUT | SteeringPressed/angle error does not prove lane drift |

For a driver input at T, retain only eligible diagnostic evidence from caller-defined
T−N…T, with coverage/gaps and exact cohort references. Do not train on override
frames, backfill default values, relabel prior frames as dissatisfied, or change
the existing override veto. Human reports may say "reported discomfort"; possible
traffic/obstacle/navigation/preference/manual-takeover causes stay hypotheses.

## Acceptance plan for a separately authorized implementation

- Identical immutable inputs/policy produce byte-identical records; input mutation
  after submission cannot change evidence. State remains bounded.
- Duplicate/reordered/session-changing/gapped inputs do not manufacture transitions;
  late or unavailable inputs stay unavailable with an explicit diagnostic reason.
- Driver transition and user feedback remain distinct; no dissatisfaction label
  appears without explicit feedback and no causal proof is claimed from it.
- Existing override/saturation/admission behavior and learner statistics remain
  unchanged when the observer is enabled or disabled.
- Exact zero/known False differ from unknown; units/context/controller/version
  mismatches prevent the affected comparison.
- Pre-window duration, dwell/hysteresis/thresholds and capacity are explicit; boundary
  events, insufficient coverage and truncation have deterministic outcomes.
- MEB target/final request difference is preserved; ordinary correction is not
  promoted to a fault. A VM estimate is always labeled an estimate.
- Architecture tests prove no engine/learner mutation, application/Params/write,
  IO/network/process/thread/persistence capability. Synthetic fixtures only.

These are future acceptance tests, not tests reported as executed in H1. Unresolved
inputs bound the design's capabilities; they do not authorize schema/runtime work.
