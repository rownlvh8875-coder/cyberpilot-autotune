# Phase 8A.2 observability exact-head contract re-audit

## Authority, pins and audit plan

This audit implements the owner's Phase 8A.2 specification. It authorizes source
inspection, independently written evidence and executable message-neutral truth
tables only. No actual adapter, message extraction, SubMaster connection, Params,
reference repository change, real log, persistence or Apply is authorized.

Target main: `73769b7a173c0ee49f7d18335c06554c6e4291f0`.
Reference: https://github.com/rownlvh8875-coder/openpilot, PR #20, base
`604bc0a22733e648ec05b268da1ffaae7db52a69`, exact observability head
`4d89f044fc74138b0938f309ff8ea88d90faddcd`.
Initial remote checks confirm Draft/Open, mergeable, unchanged head, and five
successful exact-head checks. PR #20 remains unchanged by this audit.

The implementation plan is executed inline with one fresh final read-only review:

- [x] Verify remote pins and establish an isolated feature worktree; run baseline
  regression (475 passed).
- [x] Inspect all 21 changed files and supporting producer/consumer/schema/clock
  sources as raw pinned Git blobs; hash base/head and record evidence ranges.
- [x] Trace the complete receipt lifecycle and decide each mandatory gate before
  considering any production contract module.
- [x] Write failing tests for the literal synthetic truth tables and evidence
  validator, then implement only test-side message-neutral evaluation.
- [x] Complete the signal matrix, unavailable policies, source-valid composition,
  age algebra, provenance and explicit readiness decision.
- [x] Run full regression, unchanged replay goldens, lint, types and independent
  review; correct the findings with failing tests and a green full regression.
- [ ] Publication verification: final build/wheel smoke, append-only commit, push
  and Draft PR exact-head CI are tracked in the PR and final report.

Review focus: delayed publication versus current-command confusion; missing
pointer/enum states versus numeric zero; cross-domain timestamp subtraction;
sensor history gaps and future samples; controller-specific desired versus
measured curvature semantics. Each is covered by synthetic rejection cases.

Ruling: keep the executable truth-table model under tests. The mandatory signal
audit is blocked, so a production mapper is prohibited. These tests characterize
proven software evidence and a conditional policy subset, not an installed adapter.

## Decision and scope of proof

**CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**.

The two historical activity/saturation blockers are resolved as *software
observation semantics*. Full Snapshot admission still cannot be proven at this
pin. Naming a future validation predicate does not supply its missing source
evidence. The exact remaining blockers are:

- **BLOCKED_MEASUREMENT_PROVENANCE**: the actual model configuration/current health
  and estimator input cohort used for the published VM curvature are not exposed.
- **BLOCKED_MEB_DESIRED_RESPONSE_SEMANTICS**: the final MEB actuator request is a
  PID/corrected output, not the target used by the existing desired-minus-measured
  learner contract; that target lacks a same-command receipt binding.

No Phase 8B readiness, implementation or vehicle safety approval follows. The
upstream-base Phase 8A blocked decision remains historically correct.

| Mandatory gate | Verdict | Proof and restriction |
|---|---|---|
| control_active | PROVEN | Completed same-apply receipt, final host activity and healthy observed safety permission; tri-state rules below |
| controller_saturated | PROVEN | Independent calculation and returned-output predicates; never use the old alert timer as this flag |
| Cohort binding | PROVEN | Exact source Event timestamp plus apply-start timestamp, value copies and delayed publication |
| Clock domains | PROVEN | Python monotonic for command/apply/required Python topics; separate boot-time safety pair |
| Sensor alignment | UNRESOLVED for measurement provenance | Bounded history is a necessary policy, not proof of the actual estimator inputs/configuration used |
| Desired response | UNRESOLVED for MEB | Final corrected request differs from original target; no replacement research mode is authorized |
| Source validity | BLOCKED | Missing measurement/target facts prevent True at this pin |
| Baseline | PROVEN target boundary | Caller-owned immutable values and epoch; exact trusted match, never inferred from Params or actuator output |

No production `carrot_receipt_contract.py` is added. The independently written
oracle is in tests/audit and is not installed in the wheel. It projects literal
synthetic cases, not reference messages or actual ObservationSnapshots. All cases
have source_valid=False at this pin; conditional_checks_passed records only the
synthetic subset, never admission permission.

## Remaining evidence gaps and minimum extension

Measurement evidence is insufficient at this exact pin:

- Controls.state_control chooses liveParameters after lateral_ready, but the
  LateralStartupGate is a process-lifetime latch and does not rearm after later
  bad inputs. A host-active receipt is not proof of current estimator health.
- The VM uses effective steer ratio from liveParameters plus private CustomSR and
  SteerRatioRate settings. The published liveParameters value is not necessarily
  the effective model configuration. Reading additional Params is prohibited and
  would still not identify the configuration used for the historical estimate.
- Neither ControlsState.curvature nor CC.currentCurvature identifies the actual
  CS/liveParameters input stamps or effective configuration epoch used. Newer
  retained topic health cannot retrospectively attest those private inputs.
- The publisher sets controlsState.valid from CS.canValid, which is not a current
  model/calibration validity statement. Numeric finiteness is insufficient.

Evidence: [VM calculation and private settings](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/controls/controlsd.py#L118-L133),
[latched readiness](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/controls/lib/lateral_readiness.py#L9-L18),
[effective ratio](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/controls/lib/steer_ratio.py#L10-L20).

The minimum proposed extension is same-command versioned measurement mode and
current validity (unavailable by default), actual estimator-input publication
stamps/domains, and the effective VM configuration identity/epoch or an equivalent
auditable attestation of the settings/model actually used. Carry it with the
source CC and receipt key. An epoch without accessible semantics/current health
is insufficient. It must distinguish nominal/fallback/stale/live modes without
new tuning thresholds or Params access by the adapter. This is a proposal, not an
implemented or approved extension.

MEB separately needs its original desired curvature bound to that same source CC
before PID/EPS/VM correction. [The actual overwrite](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/controls/controlsd.py#L229-L260)
proves why final actuator curvature cannot substitute for the existing desired
response. A corrected-host-request residual mode would need separate explicit
authorization, naming and validation; it is not adopted here. The extension could
carry the pre-PID target alongside existing observation metadata and receipt.
Do not clear the general measurement blocker by excluding only MEB.

Ruling: reject the provisional READY interpretation after independent source
review identified both gaps. A defined future predicate is not current proof;
all exact-pin Snapshot admission remains blocked. The cost is delayed adapter
implementation, rather than hidden reliance on unverifiable estimates or altered
learner semantics. No observability source is changed by this audit.

## Source provenance and all changed files

[Sources JSON](evidence/carrot_observability_sources.json) records all **21** PR
changed paths, raw base/head Git-blob SHA-256, byte/line counts, inspected symbols
and each file's responsibility. It additionally pins 19 supporting files and 35
symbol/definition ranges with their own hashes and exact-head links. Local
read-only validation checks 68 existing blobs and 48 legacy schema fields.
Hashes use raw Git bytes, independent of checkout line endings. Absent base blobs
for new files are null, not an invented hash. No source body is copied here.

The changed-file review covers: car/log schemas; capture/completion and card
lifecycle; controlsd and all three lateral controllers; the pure observation
helper; four new card/schema/CAN test files; the legacy schema JSON; offline
settings isolation; lateral observation tests; two existing fixture namespace
updates; developer verification/isolated DBC generation; CI and protocol docs.
Original and modified implementations, not names alone, inform the conclusions.

The root LICENSE and opendbc_repo/LICENSE blobs contain MIT-style grants and
notices. Their exact hashes are recorded; this is not an assertion that every
embedded third-party file has identical attribution. The target has no selected
license. Owner license/attribution decisions remain necessary before upstream
reuse. Only independently authored prose, metadata and synthetic test code enter
this repository; no reference implementation or legacy binary fixture is copied.

## Receipt lifecycle and schema

1. Controls.state_control computes the controller output and calls
   record_lateral_observation on the same CC. Version 1 and controller kind are
   carried in CarControl.lateralControlObservation @18.
2. Controls.publish sets CC.currentCurvature, publishes controlsState, then makes
   the carControl Event. Its Event.logMonoTime identifies that exact source CC.
3. Car.step calls state_publish **before** controls_update. The former sends the
   previous completed receipt; it never joins the current CC to that old output.
4. controls_update clears the pending receipt, applies existing reboot/readiness
   suppression, and samples apply_start_ns before capture and the existing apply
   call. hostApplyMonoTime is this software apply-boundary start, not an assertion
   of the precise function-entry instant or the separate now_nanos argument.
5. capture_actuation_receipt copies the final CC.actuators and final latActive.
   It obtains sourceCarControlMonoTime from the same SubMaster carControl slot.
   SPAS/readiness/reboot copies retain the original command identity.
6. CarInterfaceBase.apply forwards the unchanged CC to CarController.update.
   complete_actuation_receipt copies the actuator output returned by that same
   call. It records returned status separately from finite output availability.
7. The completed reader is stored and copied into the next existing carOutput
   publication. A dead/skipped controls_update or passive/uninitialized step
   clears it. One previous valid receipt may still publish before a later skipped
   apply, as required by the existing order; it is never relabeled as a new apply.

Normative source:
[card lifecycle](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/car/card.py#L338-L530),
[capture/completion](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/car/actuation_receipt.py#L72-L123),
[source publication](https://github.com/rownlvh8875-coder/openpilot/blob/4d89f044fc74138b0938f309ff8ea88d90faddcd/openpilot/selfdrive/controls/controlsd.py#L284-L456).
The source manifest supplies all remaining exact symbol/range links.

Cohort key: **(sourceCarControlMonoTime.value, hostApplyMonoTime.value)**, scoped
to an attested same-host monotonic stream. Repeated commands with distinct apply
times are distinct cohorts. Duplicate delivery/corrected resubmission of a key
must not receive another learning sample. Consume attempted identities, including
rejections; retain high-water ordering. A restarted clock/domain requires a new
stream instance, not relabeling old evidence. SubMaster.frame is never this key.

CarOutput.actuationReceipt is appended at @1; old actuatorsOutput remains @0.
ActuationReceipt fields occupy @0 through @12; the JSON records every name and
ordinal. ObservationMonoTime uses an unavailable/value union and an explicit
domain. All activity, permission, return and limit enum ordinal-zero values are
unavailable; controller kind defaults to unknown. Receipt version zero supplies
no evidence. Both actuator struct pointers must be present as well as finite:
default getter zeros do not establish presence. Existing fields/ordinals/types
and legacy decode compatibility are independently covered by the source tests.

The outer carOutput Event.valid describes the **current** carControl check in
state_publish. It cannot validate or invalidate the previous receipt by itself.
Use transport seen/alive/frequency and explicit receipt checks. Do not globally
bypass other topic validity checks to accommodate this one envelope distinction.

## control_active truth table

Complete evidence means supported receipt/version, recognized matching kind and
calculation version, exact cached source-command lookup, positive present ordered
command/apply monotonic stamps, returned status, present finite final/returned
actuators, and ordered present safety source/observation boot-time stamps with
known allowed/disallowed permission. Unknown versions/enums/cohorts do not satisfy
this predicate. Source-health/age/skew policy is additionally required for a usable
Snapshot; diagnostics can retain historical facts when a cohort is rejected.

| Complete | Final host activity | Safety permission observed | control_active |
|---|---|---|---|
| Yes | active | allowed | True |
| Yes | inactive | allowed or disallowed | False |
| Yes | active | disallowed | False |
| No, or host unavailable | any | any | None |
| Any | any | unavailable/mixed/unknown | None |

True means only that this host apply admitted lateral activity and fresh valid
permission was observed. It says nothing about an individual CAN frame or a
physical vehicle response. Reboot/readiness suppression can produce False after
the final CC is copied, with complete permission evidence. Dead/stale/invalid
commands produce no eligible activity. Simulation/replay/unknown execution mode,
missing/invalid/stale/faulted/config-mismatched/mixed pandas produce unavailable
permission in the pinned producer, hence None here. Missing controller return or
legacy version zero also means None, regardless of outer envelope validity.

## Instantaneous versus returned-output limit evidence

| Kind | Calculation evidence A | Returned-output evidence B |
|---|---|---|
| PID | Existing output proximity predicate OR curvature_limited | Existing torque request/output comparison |
| Torque | Existing output proximity predicate OR curvature_limited | Existing torque request/output comparison |
| Angle | Existing instantaneous angle-error predicate OR curvature_limited | Existing steeringAngleDeg comparison |
| mebCurvature | Actual MultiplicativeUnwindPID.control versus its finite bounds OR curvature_limited | Existing curvature-difference times apply-speed-squared comparison |
| unknown/other | unavailable | unavailable |

The predicates/thresholds are source semantics, not newly approved vehicle bounds.
The original _check_saturation timer still has its exclusions; it is independent
of A. MEB explicitly clears the dummy angle instantaneous field and reads the
real curvature PID. Missing PID evidence stays unavailable. A known kind/version
in the receipt implies the producer checked CP selection against the source CC
observation; a future consumer must also check its pinned CP/baseline context.

For a complete matching cohort: A=limited **or** B=limited gives True. A and B
both notLimited, with final host activity active, gives False. Otherwise use None.
Missing/non-finite actuators, missing return, unknown kind/version/cohort give
None before this table. Unknown wire values normalize to unavailable, never False.

An inactive controller calculation publishes unavailable A. Later card suppression
can retain A from an earlier *active calculation* on that same source command;
that is not a new inactive calculation. The final-host-active guard prevents
turning both negative predicates into False after suppression. A positive limit
can remain a conservative veto diagnostic. The adapter must never infer absence
of all physical/CAN limiting from this software predicate's False value.

## Snapshot field matrix

All source paths/symbols below refer to the exact-head manifest. Joins are to
bounded retained history, not whatever SubMaster happens to hold on receipt.

| Snapshot field | Source | Cohort join | Unit | Sign | Freshness | Missing | Verdict |
|---|---|---|---|---|---|---|---|
| timestamp_s | Receipt.hostApplyMonoTime @10 | Key apply component | s from integer ns | positive | Same attested monotonic domain; no future/regression | Reject | PROVEN software apply-start anchor |
| sequence | Future adapter-owned attempted-receipt counter | One new key/attempt; consume rejection; duplicate key never resampled | count | nonnegative, strictly increasing | One stream lifecycle | Reject/skip | Defined; not SM.frame |
| source_age_s | Receipt anchor and required historical source timestamps | Age-at-anchor algebra below | s | nonnegative | Evaluation age checked against caller policy | Reject | Defined; publication age, not sensor latency |
| context_key | Caller controller/schema/baseline epoch | Immutable per stream; recognized controller/version | none | N/A | Reset on explicit context change | Reject | Defined; no VIN/GPS/driver identity |
| source_valid | Receipt + source health + alignment + trusted baseline | Full conjunction below | Bool | N/A | Checked at evaluation | False/reject; never synthesize missing signals | Defined |
| control_active | Complete receipt activity and permission | Exact receipt key | Bool/None | N/A | Full receipt/permission contract | None | PROVEN scoped software meaning |
| controller_saturated | Receipt instantaneous state A and output state B | Exact receipt key | Bool/None | N/A | Matching kind/version/return; table above | None | PROVEN scoped software predicate |
| desired_curvature_inv_m | finalRequestedActuators.curvature for PID/torque/angle only; MEB target unresolved | Exact final CC; never substitute MEB corrected output | 1/m | Preserve native target convention | Complete finite receipt, recognized family | None/reject MEB | PROVEN normal-controller target equivalence; UNRESOLVED MEB |
| measured_curvature_inv_m | ControlsState.curvature @37, a VM estimate | Historical topic times do not identify actual estimator-input/configuration cohort | 1/m | Negative VM curvature | Need effective VM/configuration and input provenance, not canValid alone | None/reject learning | UNRESOLVED; never returned actuator curvature |
| speed_mps | CarState.vEgo @1 | Historical carState at/before apply within approved skew | m/s | Preserve finite nonnegative estimate | Individual health and canValid required | None/reject learning | PROVEN units; conditional bounded temporal join |
| driver_override | CarState.steeringPressed @9 | Same selected carState as speed | Bool/None | N/A | Same health and alignment | None/reject learning | PROVEN steering input observation, not a driver identity |
| lateral_acceleration_mps2 | Optional aligned VM curvature times speed squared | Same selected estimate/speed pair | m/s^2 | Same curvature sign | Both operands and provenance valid | None at this pin | CONDITIONAL future estimate; no inertial claim |
| baseline_parameters | Caller-injected immutable baseline | Exact trusted mapping + caller baseline epoch | Parameter-specific caller contract | Preserve | No inferred registry/values | Reject mismatch | PROVEN target policy |

controlsd assigns actuators.curvature from desired_curvature, then MEB replaces
it with its PID/correction result. PID/torque/angle retain the target in that
field. On MEB, final request is excellent **host-request evidence** but not the
existing desired-response quantity. ControlsState.desiredCurvature retains the
target but has no command ID. Both negative limit predicates can hold while the
corrected request still differs from target. The existing residual learner
subtracts measured from desired (core/residual.py, observe); it has no alternative
corrected-request mode. MEB desired must remain None/reject until same-command
target evidence exists. No alternate residual semantics are approved.

ControlsState.curvature is a model estimate with parameter/roll/offset dependence;
it is not CarController output and not a direct road measurement. Source CC
currentCurvature @17 carries the same VM estimate keyed by the exact command. It
fixes value/command identity, not missing effective model/input provenance.
Event.valid=canValid alone cannot establish current estimator validity. The
synthetic measurement_valid flag is only a counterfactual test assumption, not
source proof. Even when True, actual-pin source_valid remains False.

MEB CarState.steeringCurvature @84 is EPS-specific. Its producer negates the QFK
curvature sign into the branch convention; this is not a generic vehicle fallback.
Other vehicles also reject at this pin; no generic validated fallback is proved.
Likewise a torque union's actualLateralAccel can involve different estimator/input
fallbacks and lacks an exact command key: it is not an unconditional acceleration
fallback. Unknown optional acceleration stays None. No left-positive physical
normalization or cross-vehicle interchangeability is claimed by this contract.

## History, health and clock policy

The future extraction boundary must retain immutable, timestamp-keyed source CC,
CarState and ControlsState history with health metadata. Select the exact source
CC named by the receipt. Select required sensor/estimate samples no later than
the apply anchor, and ControlsState no later than the command, under an immutable
caller-supplied maximum age/skew policy. Missing history, ambiguous stamps,
unsupported domains, future/reordered samples or excess skew reject. Never repair
a past cohort with the current latest source. A bounded timestamp association
does not prove the exact same sensor acquisition/CS object used in computation;
that uncertainty must be explicit in any future estimated research mode. Bounded
history alone cannot clear the mandatory measurement provenance blocker. Extend
the same-command evidence as specified above before declaring a usable mapping.

Required topic health means known live pinned publishers, seen/alive/valid/freq_ok
and no simulator/ignore-list relaxation; carState also requires canValid. Required
measurement inputs include the chosen estimator's validated calibration/model
provenance. Use no invented validity field. Missing proof rejects before learner
admission. Outer carOutput.valid has the distinct current-command meaning above;
transport health is independently necessary but insufficient.

Panda permission is qualified at apply by the source: present valid/alive/freq_ok,
fresh publication and receive observations, matched CP configurations, known
panda/safety enums, no explicit fault/heartbeat/rx-check problem, known live mode,
and unanimous allowed/disallowed values. Mixed values are unavailable. Its
ten-service-period software envelope is existing source policy, not a new vehicle
threshold. Positive safety stamps are ordered within CLOCK_BOOTTIME only. Receipt
age is CLOCK_MONOTONIC. Do not subtract panda boot-time from evaluation monotonic
time, or use receive time as publication time. Suspend offsets are tested.

Let H be hostApplyMonoTime and E the adapter evaluation time in the same attested
monotonic stream. Let T be all required aligned publication times, including the
source command and retained sensor/measurement topics. With all T <= H <= E:

- `evaluated_source_age_s = max(E-H, max(E-t for t in T))`.
- Snapshot `source_age_s = max(0, max(H-t for t in T))`.
- Existing SafetyGate computes `source_age_s + (E-H)`, exactly the evaluation age.

The user's evaluation-age requirement is checked directly. The Snapshot field
must retain age-at-anchor semantics to avoid double counting delayed publication.
The cases record both quantities. Future samples reject rather than clamping a
negative age. No numerical vehicle age/skew defaults are chosen. The .2/.03 values
exist only in explicitly synthetic test policy. A future policy is frozen and
caller-approved, with finite nonnegative limits and a declared estimate mode.

Any future source_valid=True requires supported receipt/version, ordered present matching
cohort stamps, bounded receipt/source age, transport health, every required
CarState/measurement health/provenance check, bounded skew, matching recognized
controller/calculation version, finite present final/returned actuator structs,
known return status, non-None activity and required limit evidence, finite speed,
known override and exact immutable baseline match. It is *quality*, not learning
permission: valid disallowed activity or a positive limit/override still vetoes
learning at the existing engine boundary. Unknown baseline/model/health is never
converted to zero or False. No Params key is read to manufacture a baseline.
At the inspected pin the mandatory measurement/target evidence is absent, so all
real-source mappings reject and every recorded source_valid result is False.

## Synthetic evidence and verification

[Cases JSON](evidence/carrot_observability_cases.json) contains 40 independent
literal expected cases, including all 25 required scenarios plus suppression,
simulation/replay, panda absence/invalid/mixed state, suspended boot-clock offsets,
unknown wire limit, future source, source health, override and absent speed.
Each records both tri-state fields, source_valid=False, pin blocker reasons,
cohort key, anchor, anchor/evaluation ages and unchanged baseline. A separate
conditional_checks_passed field describes only the hypothetical software/health
subset; it cannot clear the pin-level gate. NON_FINITE is a synthetic defect
marker; the JSON itself contains neither NaN nor Infinity. No real log/PII exists.

Tests first failed for the absent oracle and validator; the literal fixtures and
minimal test-only implementation then passed. Mutation/review tests exposed bool
versions, a permuted ordinal inventory, newer-controls mixing, boolean speed and
synthetic health bypassing the pin blocker. All were corrected before regression.
These tests validate the independently specified conditional policy and blocked
source decision. Reference
publisher execution and an actual adapter are not claimed by their success.

```sh
python -m tests.audit.validate_observability
python -m tests.audit.validate_observability --reference-repository <read-only-clone>
python -m pytest tests/audit -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src/cyberpilot_autotune
python -m pytest -q
python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90
python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay
python -m build
```

CI runs the offline evidence validator without downloading/executing openpilot.
The optional local command verifies exact raw blobs, ranges and old field
declarations against both pinned trees. Final local/remote results are recorded
after execution. No reference repository commit, Ready transition or merge occurs.

## Local verification and independent review record

Python 3.12.14: **536 passed, zero failed/skipped**, including 61 audit tests.
Runtime package branch-inclusive coverage is **98.53%**, safety 100.00%, residual
97.85%, replay 98.48%. Runtime source is unchanged from target main; this is
regression coverage, not coverage of a new production mapper. Ruff lint and format
(98 files), strict mypy (31 source files), evidence validation and all four existing
replay goldens pass. Local raw-source verification checks 21 changed paths, 19
supporting paths, 68 existing raw blobs, 35 ranges and 48 legacy fields. Seven
direct normative document links were checked against actual source line counts.

The fresh independent read-only reviewer found zero Critical, two Important and
one Minor issue in the provisional audit. Both Important findings were readiness
overclaims: missing effective measurement provenance and MEB target/request
substitution. They are now explicit blockers, with all actual-pin source_valid
results False. The Minor boolean-speed acceptance was reproduced and corrected
with strict numeric checks. These corrections passed the full regression; a
second independent approval of the corrections is not claimed.

The earlier isolated wheel check imported the root plus 30 submodules, verified
both baseline-only modes and the four unchanged replay goldens outside the
checkout. Audit-only code is excluded from the wheel; both evidence JSON files
are byte-identical in the sdist. Build and wheel checks are repeated for final
publication. No reference source program was executed or installed in this audit.
