# Read-Only Friction Observability Schema / Receipt — H7 result

## Outcome and scope

H7 implements a neutral, immutable, read-only evidence contract and pure
structural eligibility evaluator, not a producer, estimator or application path.
The question is: which actual callback, inputs, installed/applied context and
raw return belonged to this exact controller invocation?

The H6 estimand is unchanged: u_cb = a_cb/F + C*q + b0. ELIGIBLE means only that
the supplied receipt satisfies the pinned structural observation policy. It
does not establish excitation, empirical identification, authenticity, safe
bounds, vehicle readiness or any authority. No empirical selection threshold
was invented; SELECTION_THRESHOLD_UNJUSTIFIED is retained.

## PR15 merge / H7 base

PR15 was rechecked OPEN, Draft, MERGEABLE at exact head
e3dd29df5d54a179017badf351138cdd4da977a5, with successful exact-head push and PR
CI, no unresolved review threads, five append-only commits, and independent
final review C0/I0/M0 with no later code. It was marked ready and merged with
the exact-head guard, without squash, rebase, force push or admin bypass.

- Merge and new main: a5d3514f23797829eb58d08c638b22cf4dd30c8a.
- merged_at: 2026-10-29T08:55:18Z.
- Parents: 43ca6761749e71ec575906f099b02386bc76d994 and
  e3dd29df5d54a179017badf351138cdd4da977a5.
- H6 head is an ancestor; H6-head and merge trees are equal.
- H7 branch: feat/friction-observability-receipt, from that new main.

First H7 commit 83c2170d699894a8044b1e82d453281ccd495d5d contains only the
frozen receipt specification and durable execution plan, before any new Python.
Final publication head, independent review and exact-head CI are recorded in the
Draft PR body and Korean handoff, not asserted prospectively in this document.
That keeps publication metadata updates from changing the reviewed code head.

## Source pins and compatibility

R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55.
C: f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
Current carrot-wip re-read at H7 start: still C; no movement to promote.
The nine required H6 authoritative documents/manifests are pinned as acceptance
basis. The H7 source manifest pins 41 files and 30 semantic claims, including
repo/revision/path/symbol/range/blob SHA/range SHA-256. Canonical source-manifest
SHA-256: c1c6697eea57a9024e3178c82a87a3011cc9ed8866c4efb570d874f39269975a.

R/C share LINEAR, helper, NN_LITE/NN, custom-latching and PID stage semantics.
C additionally needs actual dynamic VM geometry, distinct from requested
CenterToFrontRatio, paramsd target and liveParameters candidate. R's static
axle baseline is not silently upgraded to C. Raw zero selection means vehicle
default intent, not a physical center-to-front ratio of zero. See
friction_observability_source_compatibility.md for the complete comparison.

## Receipt contract

LateralTorqueIdentificationReceipt and all nested records are frozen/slots,
strictly typed, finite-validated, defensively copied and canonicalized. The six
observability package files import only stdlib and their neutral sibling types.

- Identity: session digest, deterministic cycle/invocation, source revision and
  source-schema digest, vehicle mechanical-context digest, controller/installed/
  geometry generations and friction-observation-v1 version. No wall clock or
  object address is an identity.
- Timing: entry snapshot, callback entry/exit, actual control Event publication
  and receipt completion; monotonic clock domain is explicit. Actual gain-use
  capture is separately bound to the same cycle after PID latches current speed.
- Sources: complete dependency declaration, per-role actual consumed flag,
  source timestamp/domain/sequence or opaque identity, origin, valid and alive.
  carState/livePose/liveParameters/carControl are declared even when a role is
  explicitly unused. LOCAL_CYCLE_OBJECT carControl is not a later published Event.
  R/C role origins are enforced for local carControl and wire carState; every
  consumed local object binds the current cycle digest. Local source IDs/sequences
  cannot be reused across distinct cycles within one session/controller instance;
  unchanged wire samples may be reused. LP's source-specific local fallback is
  allowed only with the same explicit current-cycle binding.
- Stage/mode: executed family, function and call site, not just a CUSTOM selector.
  Only pinned LINEAR feedforward is eligible. NN_LITE/NN/GM/other receipts remain
  diagnostic and IDENTIFICATION_MODEL_UNSUPPORTED, never fallback to LINEAR.
- Inputs/output: actual desired/actual acceleration, roll/roll compensation,
  callback a, helper error/deadzone/threshold/flags and q_observed; raw callback
  return is a separate pre-k_f observation, never a downstream torque.
- Installed context: actual F/C, optional offset with field/source identity,
  custom selector and gain generation. These are CONTEXT_ONLY, not truth,
  regression targets, proposed settings or trusted baseline automatically.
- PID/limits: actual speed-effective k_p/k_i/k_d/k_f, p/i/d/f, sum and clipped
  output; timer-qualified saturation and instantaneous clipping/limits remain
  separate, alongside override, steeringPressed, active and source health.
- Geometry: actual applied VM identity/generation, wheelbase/center-to-front/
  ratio, stiffness/effective SR, raw/effective SR-rate and CustomSR. Requested or
  candidate values cannot replace missing applied context.
- Delay: effective value/source, method/version/correction count and exact pair
  identity. Core callback values are unshifted; double correction is rejected.

Partial structural receipts preserve None, including None versus zero/false.
The pure evaluator rejects missing required observations with explicit reasons.
It has no collector, state machine, cache, timer, persistence or producer. An
optional explicit previous receipt detects duplicate/reordered cycles and context
drift; it is not hidden runtime state. epoch_digest splits actual mode/F/C/gain/
geometry/SR/delay/generation changes. Per-observation pair IDs and unapplied
candidate values affect content identity, not installed/applied epoch identity.

## Exact LINEAR semantics and stage separation

For the pinned feedforward call, a = desired_lateral_accel - roll*9.81 and
friction_input = desired_lateral_accel - actual_lateral_accel. Both compensation
and gravity_adjusted arguments are true. Strict deadzone interior maps to zero;
exact positive/negative boundaries survive, width is not subtracted. Normalized
q is the clipped surviving error/0.3. Compensation disabled has diagnostic q=0
but is not eligible as this pinned feedforward call.

The actual helper returns np.interp(error, [-T,T], [-C,C]); there is no independent
q output in the existing implementation. q_observed can only come from a future
reviewed helper-state exposure, never h/C or a reconstructed diagnostic. Rewriting
interpolation as C*q can change rounding and requires compatibility review.
The raw LINEAR callback returns a/float(F) + friction; installed offset is stored
context but not read in that return. H6 b0 remains the model intercept, not an
automatic installed-offset regressor.

| Stage | Meaning / relationship | Never substitute |
|---|---|---|
| raw callback u | actual callback return before k_f | PID f, requested or applied torque |
| PID f | raw u multiplied by actual k_f | raw u unless exact stage/gain receipt exists |
| PID sum / clipped output | p+i+d+f, then PID output clip | callback response |
| requested actuator torque | negative internal output at pinned return, exact command identity | raw u or actual applied torque |
| host / applied torque | separate downstream event/time/health/command linkage | any pre-PID signal |

Optional downstream values require their own exact event and source-command IDs,
cycle/time/domain/health witnesses; a cycle label or nearest timestamp is not
enough. Future host/applied values normally remain None in an in-cycle receipt.
Later companion evidence does not mutate the immutable core.

## Wire, precision and capture design

The neutral semantic schema lists 143 fields in 15 records and 18 enums, with
type/unit/stage/presence/source/qualification meaning. It is not cereal schema.
Proposed wire encoding: Float64 continuous values, UInt64 times/IDs/generations,
explicit enums and Bool with availability, bounded typed source/stage records.
No actual Cap'n Proto tags/ordinals/file IDs, encoder or schema patch are added.
Semantic/stage/timing/unit/precision changes bump receipt version; source SHA and
source-schema digest are separate and need explicit compatibility registration.

Python float/NumPy float64 callback locals should retain binary64 precision.
Existing torqueState and CP tuning fields are Float32; widening cannot recover
lost information or turn old telemetry into direct local observations. PID error
is itself read after the Float32 pid_log.error write, unlike local friction input.
Direct a/error/roll arithmetic is checked exactly in binary64; q/callback/PID
consistency has only a documented eight-ulp roundoff allowance, not a noise or
empirical selection threshold. Float32-only mapping is rejected as exact raw data.
Canonical sorted finite JSON preserves explicit unavailable values; SHA-256 is
content identity only, never authenticity, authorization or safety approval.

Exactly one preferred future architecture is selected: A, cycle-scoped capture
inside LatControlTorque.update with narrow helper/PID taps, exact consumed-source
and actually applied context supplied by controlsd, then one immutable seal after
actual publication time is known. B callback-only, C PID-only and D controlsd-only
miss essential state. The qualitative 0/1/2 access-score matrix and implementation
coupling/performance/testability costs are in the capture document. Independent
helper q exposure and post-speed-latch gain capture remain real prerequisites.
No capture code, native patch or measured runtime performance claim is made.

## Existing observation-v2 mapping

- REUSABLE_EXACT: conditional exact carState steeringPressed/health and source/
  command-link witnesses, only if the actually consumed sample is proven.
- REUSABLE_CONTEXT_ONLY: static mechanical context, caller baseline metadata,
  controller kind and timing policy; not exact current installed/applied cohort.
- WRONG_STAGE: requested/applied torque and curvature-derived accelerations do
  not replace callback-local a/error/u, even when numerically equal.
- MISSING: raw callback, independent q, complete invocation/dependency and delay
  association receipts. MISSING_COHORT: installed F/C/realized gains and applied
  geometry generation. No automatic sidecar/adapter support is claimed.

PR8/PR9 remain OPEN/Draft at e4361678ed176cbd7c0bb6f838d3daa7174caf22 and
6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5 respectively. They were only inspected,
never rebased, refreshed, conflict-fixed, merged or edited. Phase8B.2B is not
bypassed. Receipt != QualifiedEvidence, digest != AuthorizationGrant, installed
context != approved target or application authority.

## Synthetic/adversarial evidence and verification

All data is synthetic; no real driving, holdout or evaluation data was loaded.
All twenty required cases are registered: full LINEAR; missing q/u; wrong mode;
deadzone interior and both exact boundaries; disabled compensation; saturation;
override; geometry/F/C changes; source timestamp mismatch; duplicate cycle;
nonfinite input; legacy Float32 approximation; NN_LITE; NN; applied-as-callback.
Additional properties cover deterministic/order-independent digests, source/mode/
generation changes, None versus zero/false, defensive copies, q independence,
exact boundary arithmetic, duplicate/reused source/downstream IDs, future times,
wrong clocks, post-speed-latch gains, epoch splits and authority/import barriers.

- Full regression after review fixes: 1380 tests passed; prior baseline was 1261.
- H7 targeted: 119 tests; 829/829 statements and 264/264 branches (100% each).
- Overall combined coverage: 98.51%; all historical coverage gates pass.
- Source audit: 41 files / 30 claims / 44 isolated helper/callback/PID math cases,
  plus H6 exact-source geometry parity. H2/H3/H4/H5/H6 audits remain green.
- ruff check and format, mypy, wheel/sdist build pass. Replay goldens unchanged;
  all four CLI fixtures and eleven focused/golden tests pass.
- Fresh vanilla installed wheel: 70 imports outside checkout with no NumPy or
  native schema, six H7 file hashes, full/partial receipt and semantic-schema
  smoke pass; replay, knowledge, owner and optional-dependency smokes pass.
  Separately installed research wheel passes all 43 H5 and 26 H6 synthetic cases.
- New CI gates are additive: H7 coverage/history/source audit and vanilla-wheel
  smoke; all old matrix, native compatibility and network-isolated audit gates
  remain. Existing native CI is not qualification of a nonexistent H7 producer.

Final exact-head independent review and remote CI must be read from their fresh
results, not inferred from this pre-publication verification ledger. Any C/I
finding requires RED test, append-only fix, full rerun and a new fresh reviewer.

First final-head review at ad8dfe78392a3c966777fe724493e0b4c23e7725 returned
C0/I2/M0. It independently reproduced role-incompatible source origins and stale
cycle-local carControl reuse passing admission. Regression tests were observed
RED, then role-origin rules, explicit local-object cycle binding and same-instance
cross-cycle local-ID/sequence nonreuse were added; unchanged wire-sample reuse
and the source-specific local LP fallback remain representable. A new source-AST
mutation test pins CS/CC/LP origins, call arguments and later publication without
executing native code. Full regression, 100/100 H7 coverage, source/history audit,
lint/type/build/wheel are rerun before the new exact-head review. No issue is
waived and no old-head approval is carried forward.

Second review at 2f45eed49969989b924675dfe08e5daa11b98a3e returned C0/I1/M0:
an otherwise internally consistent requested command could predate the actual
control Event. Its RED regression and six post-publication PID capture REDs
now pass. PID/gain observations are bounded by controlsState Event time t_ctl;
command/downstream observations cannot precede it. t_cmd remains distinct and
can be later, never forced equal. The source-AST guard now verifies the pinned
controlsState creation/publication then carControl creation/publication order;
its reordering mutation also failed RED before the fix. The full 1380-test suite,
119 H7 tests, 100/100 coverage, all source/history audits, build and wheel checks
are rerun before another new exact-head review. No timing exception is waived.

## Execution rulings / costs

1. Reuse the dedicated managed checkout rather than adding a worktree. Cost:
   less concurrent isolation; mitigated by a clean baseline and preservation audit.
2. Neutral mirror/link of H6 geometry, not a research import. Cost: duplicate
   semantics; mitigated by exact H6 projection/source parity tests.
3. Three historical namespace-inventory tests receive only the exact additional
   observability prefix. Their original source/golden hashes are retained. H6's
   history validator accepts only original bytes or those precise substitutions;
   tests reject unrelated edits and removed hash guards, and every other AST node
   is preserved. Cost: a narrow documented inventory compatibility amendment.
   No H6 candidate/model/result/policy/evidence was changed. History covers 264
   original files, including these exact scoped amendments; CI is additive.

The first full run exposed those three inventory failures, then exact fixes and
full reruns passed. No scientific acceptance criterion or authority was relaxed.
No implementation scope is deferred within the neutral H7 contract.

## Status and retained blockers

- FRICTION_OBSERVABILITY_RECEIPT_CONTRACT_READY.
- FRICTION_OBSERVABILITY_WIRE_DESIGN_READY.
- FRICTION_OBSERVABILITY_CAPTURE_ARCHITECTURE_READY.
- ATOMIC_CONTROLLER_RECEIPT_RECOMMENDED.
- REPRESENTATION_ENCODING_DESIGN_READY.
- FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
- FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED.
- REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED.
- NO_EMPIRICAL_ESTIMATOR_BRIDGE.
- FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
- FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
- PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED.
- VEHICLE_APPLICATION_BOUNDS_UNRESOLVED.
- RUNTIME_FINGERPRINT_UNCONFIRMED.
- WATCHDOG_EXECUTION_MODEL_UNRESOLVED.
- EXTERNAL_EXECUTOR_UNQUALIFIED.
- APPLICATION_NOT_AUTHORIZED.

candidate_generation_allowed/application_authorized/runtime_accepted/
owner_proposal_allowed are absent on receipt or fixed false on decisions.
Encoding design readiness narrows the old design gap only; runtime encoding
qualification and all scientific/application blockers remain.

## Recommended next single task

A: actual Carrot read-only observability schema/producer patch design.
Resolve independent helper-state q exposure and rounding parity, final native
presence/Float64/evolution encoding, exact gain/source/applied-context capture
and a newly registered source profile before implementing any native producer.
H7 alone cannot justify producer implementation, Phase8B.2B bypass, empirical
qualification or application. This recommendation is not started automatically.

## Non-goals / preserved boundaries

No vehicle execution, Params access/write, controller mutation, cereal/log/custom
schema change, controlsd/LatControlTorque/torqued change, liveTorqueParameters
publisher change, real SubMaster producer, estimator qualification/bridge,
candidate generation, application/SteeringRequest/AuthorizationGrant/owner path,
PR8/PR9 modification, longitudinal, external AI integration or upstream fork PR.
No vehicle-model inference or Santa-Fe-specific threshold/bounds are used.
