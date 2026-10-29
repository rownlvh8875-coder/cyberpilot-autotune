# Hoya c3-atune selective architecture audit

Status: **HOYA_SELECTIVE_AUDIT_COMPLETE**. Scope: design and source audit only.
Date: 2026-10-29. No reference implementation or real log was executed.
The [source manifest](evidence/hoya_c3_atune_sources.json) pins raw Git blobs,
SHA-256, symbols, line ranges, range hashes and confidence. The
[feature manifest](evidence/hoya_c3_atune_features.json) records every decision,
episode predicate, named parameter, provider, comparison and score. Evidence IDs
below resolve to exact source links in the index at the end of this document.
PROVEN describes a source fact, not vehicle safety or a causal diagnosis.

## Pins and branch history

| Reference | Exact commit / result |
|---|---|
| CyberPilot main / audit base | b24ef18e4270af5ab4f731aca31cf95f4f4b0cce |
| PR #8, Open/Draft/unmerged | e4361678ed176cbd7c0bb6f838d3daa7174caf22 |
| PR #9, Open/Draft/unmerged | 6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5 |
| ajouatom/openpilot hoya/c3-atune | 0e9c589c1b83027146f909a9cdc306c2c665ceaf, unchanged |
| First AI feature commit on this path | c1006caadfd7b47d528ab466338da223aa79dd8e |
| Initial feature message | feat(web): add AI Tuning feature for driving log analysis and parameter recommendations |
| Latest Hoya feature message | autotune: add carrotMan telemetry, parameter definitions, and core control code reference |
| Previously observed carrot-wip | bfc3ebb44f24e99e2d46e65ef091c4cf27627be9 |
| Current carrot-wip | f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 |
| Merge base, Hoya versus current carrot-wip | 9bd031e12759dac4332eb47b920a6d156253c296 |
| Reachable commits unique to each side | Hoya 10; carrot-wip 1013, including merges |

`git log --reverse <Hoya> -- <autotune.py>` identifies c1006ca as the first
feature commit and 0e9c589 as the only later edit to that path. Current carrot-wip
advanced by two commits since the supplied observation: 1ef27534 (optional
center-of-gravity ratio tuning) and f5e4f8b8 (live center-of-gravity tuning).
Their 21 changed paths include VehicleModel, paramsd, controlsd, settings/schema
and tests; the manifest records the full path list. This is material VM/context
drift, not an instruction to update the existing integration pin. No cherry-pick
compatibility is presumed. The current integration's c213073 source and PR #9
owner gates remain unchanged.

## What the implementation actually does

| Question | Verdict | Evidence |
|---|---|---|
| Online learner? | No continuous estimator, evidence accumulation or control feedback loop in the audited feature | H:telemetry, W:flow, A:rules |
| Offline/post-drive analyzer? | Yes: selected saved route/segments are decompressed and sampled on demand | H:selection, H:sampling, W:flow |
| Live parameter writer? | A direct device settings writer exists; it is user-triggered, not a closed-loop adaptive controller | H:apply, P:write, W:apply |
| AI explanation/recommendation layer? | Yes: Free keyword/statistic rules or browser-side provider requests return explanations and numeric recommendations | A:rules, A:parse, A:network |
| Rollback UI? | Yes: prior settings snapshot, before/after display, selected restoration using the same endpoint | A:config, W:rollback, V:rollback |

The flow is saved logs → latest-slot telemetry → frame predicates/statistics →
rules or LLM → numeric recommendation → checked user selection → per-key Params
write → browser rollback snapshot. It must not be described as autonomous online
learning. A click or an HTTP success does not independently qualify a parameter.

## Telemetry extraction and provenance

H:telemetry sets `DOWN_SAMPLE_HZ=5.0` and `MAX_TELEMETRY_POINTS=300`.
The latter is a prompt-size intention, not a strict cap: for 301–599 frames,
integer division gives stride 1 and returns all points. The analogous episode
reduction can return 31–59 episodes instead of at most 30. The four-segment
selection is actually bounded; it is representative positional selection, not
coverage of all requested segments. `segmentCount` still counts selected folders,
not just the up-to-four extracted folders (H:sampling).

| Aspect | Hoya | CyberPilot | Adoption decision |
|---|---|---|---|
| Join | `curr_cs/rs/lp/cc/cm` retain latest observed payloads | Exact receipt/source CC/source CS identities | Reject join algorithm; reuse existing exact contract |
| Sample timestamp | Current event's logMonoTime, even an unrelated topic; rounded to 0.01 s | Explicit host-apply anchor and source publication stamps | Retain exact stamps and clock labels |
| carState/carControl | No command/apply relation, age, active controller or message-health guard | B:contract/B:adapter exact lookup, validity/context/version gates | No latest fallback |
| radarState/lead | Latest lead reused without source timestamp/age | No approved radar/lead input contract here | UNRESOLVED_INPUT for future longitudinal events |
| carrotMan | Latest navigation target/source reused without freshness | No approved navigation diagnostic join | Defer; cannot treat current target as previous cohort intent |
| longitudinalPlan | Latest target/first accel reused, missing becomes zero | No longitudinal observer contract approved | Defer |
| Source quality | Event.valid/canValid/alive/frequency/skew not checked by extractor | Transport and embedded health separated | Source-quality failures are diagnostic facts, not valid samples |
| Segment/time boundary | Per-file slots reset, frames concatenated; detector/counts compare across folder gaps | Stream/domain/order constraints explicit | Never form transitions across discontinuities |
| Completeness | Entire decompressed event list materialized; per-file/event failures suppressed | Bounded immutable cache/consumed attempts | No log loader or raw-event materialization adopted |

One sampled row can contain five different source ages. Neither its timestamp nor
its rounded values identifies those cohorts. Downsampling may omit short pedal
pulses, limit changes or transients; no persistence-duration test or episode
clustering compensates. `durationSec=frame_count/5` is a sampling estimate, not a
measured route duration, especially across gaps. Current Params are read during
analysis, not tied to historical parameter epochs. These limitations prevent use
as training/admission/authorization evidence (H:knowledge).

## Missing/default and exception inventory

The manifest includes a complete AST inventory for autotune.py and the three
specified supporting services: **20** zero/False `getattr` defaults and **19**
pass-only exception handlers. It also records **11** empty JS catches in the four
specified UI modules. This is a scoped inventory, not a claim about all openpilot.
Each site carries file identity, line/end and classification; optional local
source verification recomputes the Python inventory without importing it.

H:telemetry lines 57–63 collapse missing speed/acceleration/angles and driver bits;
80–82 collapse actuator values; 92–97 collapse lead state/kinematics; 106–114
collapse navigation/plan values. Local initializers additionally turn absent
topics/plan targets into zero/False/empty text. Nested alias fallbacks do not prove
field availability, units or producer capability. Scalar schema defaults also
require external availability evidence; a successful `getattr` is insufficient.
P:read gives absent settings a default zero in bulk reads. Event errors (142–143),
segment errors (302–303), description failures and audit-history failures can be
hidden. Some supporting handlers intentionally attempt another fallback; a
pass-only handler alone does not prove final failure. None establishes validity.

CyberPilot retains **unknown != zero and unknown != False**. No Hoya coercion or
silent failure path is proposed for the learner, exact adapter or SafetyGate.

## Episodes: diagnostic heuristics only

These are frame predicates, not confirmed causes or safety limits. Every constant
in this table is **DIAGNOSTIC_HEURISTIC_ONLY**, quoted for audit, never proposed as
a vehicle bound. Complete source fields/units/exclusions/false-positive and
false-negative analysis are in the feature manifest (H:episodes).

| Type | Exact predicate on sampled frames | Driver/state caveat | Principal risk |
|---|---|---|---|
| departure_start | previous standstill, current not standstill, current hasLead | No override/engagement exclusion | Manual departure or cross-segment edge |
| harsh_catchup_accel | hasLead and aTarget >= 1.4 m/s² and not gas | No brake/steer/active gate | Necessary acceleration or stale lead is called harsh |
| harsh_decel | (aTarget <= -1.8 or aEgo <= -2.0 m/s²) and not brake | Brake exclusion only | Traffic-required braking; real precursor excluded after takeover |
| steering_tracking_error | vEgo >= 30 km/h, absolute angle error >= 3°, not steer | No controller-kind/latActive guard | Unsupported/default angle or inactive controller appears faulty |
| curve_speed_mismatch | vEgo >= 30, max absolute angle >= 15°, 0 < abs(vTurnSpeed) < vEgo−5, then desiredSpeed >= vEgo−1 **or source != vturn** | No override/active gate | A valid lower model/route speed still triggers source mismatch |
| driver_brake_override | optional inclusion, brake rising, vEgo >= 5 km/h | Previous sampled aTarget retained | Transition does not identify motive or automated control |
| driver_gas_override | optional inclusion, gas rising, vEgo <= 80 km/h | No minimum speed/active gate | Ordinary manual acceleration called automation lag |
| driver_steer_override | optional inclusion, steer rising, vEgo >= 20 km/h | No producer/active proof | Positioning/takeover called tracking failure |

All can miss between-sample events; missing defaults or stale topics can create
both false positives and negatives. Non-override episodes label `isOverride=False`
without proving absence of all driver interventions. Several frames may be emitted
for the same prolonged condition. No Hoya threshold is adopted.

### Intervention is not dissatisfaction

A:prompt explicitly interprets overrides as direct dissatisfaction; A:rules also
asserts motives in generated explanations. H:episodes uses discomfort/lag/correction
wording for simple transitions. This inference is **REJECTED**. A
DriverInterventionEvent can say an independently supported input transitioned.
Possible causes include traffic, an obstacle, preference, navigation, lane
positioning, ordinary takeover, discomfort or an unrelated action. Only separate
optional feedback may record reported dissatisfaction; even that is a self-report,
not automatic causal proof.

Hoya includes the previous sampled aTarget for pedal events and asks the model to
correlate preceding telemetry. It does not implement a configurable exact-cohort
T−N…T evidence window. The proposed [observer](episode_observer_design.md) makes
that window caller-supplied, bounded and diagnostic only. Override samples remain
vetoed by existing learning admission.

## Parameter knowledge versus parameter authority

The feature manifest classifies **38 explicitly named/requested-related keys**
individually, with catalog min/max/default, actual consumer, scaling and source IDs.
The catalog has **175** unique entries; the other **140** are explicitly UNRESOLVED
and unauthorized. Three named fallback keys have no catalog entry. This is not a
finite allowlist: A:parse accepts arbitrary JSON names and the endpoint can attempt
unknown settings. Catalog exposure is not a reviewed recommendation.

| Family / keys | Classification | Consumer evidence / restriction |
|---|---|---|
| CruiseMaxVals0–6 | FUTURE_LONGITUDINAL_RESEARCH | /100 m/s², interpolated speed bins and driving-mode multiplier; F:params, N:accel |
| DynamicTFollow, DynamicTFollowLC, EnableSpeedTF, TFollowGap1–4, TFollowDecelBoost | FUTURE_LONGITUDINAL_RESEARCH | Conditional gap/lead/lane-change/speed logic; F:follow, N:mpc |
| AChangeCostStarting | FUTURE_LONGITUDINAL_RESEARCH | MPC departure cost, not a vehicle-safe comfort recommendation; N:cost |
| LongTuningKpV/KiV/Kf, StoppingAccel, StopDistanceCarrot | SAFETY_SENSITIVE | Conditional/fixed Hyundai gains, stopping logic and MPC; L:long, N:mpc |
| LateralTorqueKpV/KiV/Kf, LateralTorqueCustom | SAFETY_SENSITIVE | Custom-mode gains/mode and live/NN conflicts; L:torque, L:nn |
| LateralTorqueAccelFactor, LateralTorqueFriction | POTENTIAL_APPLICATION_FAMILY | Name overlap only; /1000 custom path does not establish PR #9 unit/evidence/ownership equivalence |
| SteerRatioRate, SteerActuatorDelay | SAFETY_SENSITIVE | VM ratio custom/MEB branches; delay 0 selects liveDelay; U:ratio, U:delay |
| TurnSpeedControlMode, CruiseEcoControl, LongitudinalPersonality | USER_PREFERENCE | Selection behavior is also safety-relevant; not granted write permission |
| AutoCurveSpeedFactor, ModelTurnSpeedFactor, MapTurnSpeedFactor, AutoCurveSpeedLowerLimit | FUTURE_LONGITUDINAL_RESEARCH | Vision scaling, future model time/filter and arbitration; M:vision, D:model, C:sources |
| RadarReactionFactor | UNRESOLVED | Removed from catalog (K:removed); no executable Python consumer found; not assumed effective |
| CarSelected3 | NOT_SUITABLE | get_car can force a platform candidate (K:selection); never a tuning knob or runtime-fingerprint proof |

Important discrepancies: prompt CruiseMaxVals1 default 200 versus catalog 160;
DynamicTFollow 30 versus 0; StopDistanceCarrot 450 versus 600. LateralTorqueKf's UI
title says ×0.001 while its consumer uses ×0.01; LongTuningKiV's title says ×0.01
while its non-fixed consumer uses ×0.001. Hyundai gains are fixed in this source.
SteerRatioRate is bypassed on MEB or by applicable CustomSR. Increasing factor to
increase steering torque is not universally correct: K:linear divides by
latAccelFactor and NN/brand behavior differs. Fixed numerical recommendations and
regex/fabricated fallback targets are **not adopted** (A:rules, A:parse).

H:knowledge's title/description/min/max/default/current-value structure is useful
for explanation. The proposed ParameterDescriptor is descriptive; the separate
ApplicationParameterPolicy still needs reviewed hard/step/rate limits, owner,
evidence, rollback and watchdog. UI ranges/defaults never supply that policy.

## Independent source-grounding check

CORE_CONTROL_SOURCE_CODE is a commented synopsis, not a verbatim source body.
The manifest independently compares **19** whitespace/comment-normalized statement
pairs with pinned consumers: **17 match**, **2 do not** (inline route guard format
and eco guard missing `v_cruise_kph > 20`). Matching statements alone do not prove
the surrounding English assertions. Raw/range hashes and pair hashes are verified.

- Eco then carrotMan calls and the min expression exist (F:calls/F:min); min is
  guarded by carrotMan alive. The eco state machine has reset/exit/speed conditions
  omitted by the synopsis (F:eco).
- Modes 3/4 exclude the **vturn candidate**, but model and other speed candidates
  remain (C:sources). The prompt's assertion of no curve deceleration without
  navigation, and mode 0 implying no turn deceleration, overstate that fact.
- The shown min picks the lower candidate at that point. Later intentional gas
  floors can replace desiredSpeed/source (C:gas); "lowest always wins" is not a
  universal pipeline invariant.
- ModelTurnSpeedFactor's actual interpolation, ×1.2 and filter are supported
  (D:model). This does not validate the model's confidence or optimal tuning.

Adopt pinned SourceKnowledgeDescriptor claims with conditions/confidence, not raw
snippet strings as authority. Hoya's prompt is not SHA-bound and cannot update
itself when branch consumers drift. No copied source body is added here.

## Providers, network and privacy

Free uses local deterministic rules. Gemini, OpenAI, Claude, Grok and Custom make
browser requests; Custom can be any configured OpenAI-compatible endpoint and is
not inherently local. Model listing also uses network. The external request is
the composed system/user prompt: **route identifier**, selected episode/statistics,
current Params, descriptions/UI ranges, source synopsis and free-text complaint.
`telemetrySample` itself is **not** serialized by buildUserPrompt; carrotMan values
reach the prompt through relevant episode fields, not the entire sampled array.
No claim is made that the source explicitly sends VIN/GPS/raw CAN/raw logs; there
is no sufficient allowlist/redaction guarantee for arbitrary Params/user text
(A:providers/A:prompt/A:network).

Credentials/config synchronize through localStorage, device API, Params and a
file; rollback snapshot also persists in the browser (A:config/H:config). These
implementations are not adopted. Optional speech uses browser speech facilities;
no speech service or privacy behavior was exercised. This audit and both proposed
CyberPilot designs remain **NO NETWORK**; future external AI is NOT_AUTHORIZED.
Future payload policy forbids VIN, route, GPS, device/driver identifiers, raw logs
and raw CAN, with explicit field allowlists, approval and data-flow review first.

## Apply and rollback: APPLICATION_ARCHITECTURE_REJECTED

H:apply reads old values, optionally clamps using UI metadata, then calls
set_param_value once per requested key. Metadata lookup/coercion failure does not
prevent attempting the write. Per-key failures can leave partial changes. Returned
`applied` is the intended value, not independent readback. `engaged=False` is a
history argument, not an engagement check. The history allowlist omits `autotuner`,
so the label normalizes to `unknown`; logging can silently fail (J:history).
W:apply throws on partial errors **before saving** the returned rollback snapshot.

| Requirement | Hoya Apply | CyberPilot PR #9 exact contract |
|---|---|---|
| Exclusive owner | Absent; Params can have other writers | Trusted single-owner target required |
| Expected revision/CAS | Absent | Exact expected revision and +1 acknowledgement |
| Exact tuple/coupled commit | Sequential per-key; partial success | Atomic selected tuple, preserve offset/untuned fields |
| Readback | Echo intended values | Independent tuple/revision readback |
| Baseline epoch | Prior values only | Trusted immutable baseline/epoch |
| Source/context | No tuning-source/context binding | Policy/source/context/session/evidence binding |
| Authorization | Human UI selection; no independent grant here | Trusted independent authority, no production implementation supplied |
| Bounds | Best-effort UI clamp; missing metadata still writes | Reject outside caller-approved bounds |
| Step / elapsed rate | Neither | Both against actual verified tuple/time |
| Override / saturation veto | Neither | Explicit known-false requirements |
| Source freshness | Absent | Observation/target/evidence/grant freshness |
| Deadline | No application deadline; analysis timeout unrelated | Transaction/hold/grant/recovery deadlines |
| Rollback verification | Same settings endpoint; no owner confirmation | Owned cohort CAS and baseline readback |
| Uncertain/foreign writes | Per-key error reporting only | No guessed overwrite; explicit unknown/failed recovery |
| Sticky fault | Absent | Faulted domain cannot auto rearm |
| Watchdog | Absent | Caller-driven; synchronous/external-owner limitation explicit |
| One-shot identity | Absent | Session sequence/identity consumption and high-water |

The feature manifest splits these into 22 comparisons. Generic HTTP authentication
outside this endpoint is not judged absent; it would still not supply independent
parameter evidence or controller ownership. PR #9 is a port contract/core, not a
deployed safety system: real torqued/custom/NN arbitration, CAS owner implementation,
friction equivalence, independent identification, approved bounds/rates, recovery/
watchdog acceptance and runtime fingerprint/context remain unresolved (G:application).
Hoya cannot close or bypass any of them.

Rollback's prior/current display, selection and confirmation are **UX_CONCEPT_ONLY**.
Future UI must distinguish recommended, authorized, committed, readback verified,
rollback requested, rollback verified, rollback failed and ownership uncertain.
A stored prior-value map is not a verified baseline or qualified recovery. No
recommendation-to-SteeringRequest or Supervisor-to-AuthorizationGrant path is proposed.

## Decisions and completion meaning

See the [adoption matrix](hoya_c3_atune_adoption_matrix.md),
[observer design](episode_observer_design.md), and
[advisory supervisor design](autotune_supervisor_design.md).

The observer and supervisor designs are ready as bounded, read-only/advisory
**proposals**. Brake/gas/lead/navigation and physical-response inputs remain
UNRESOLVED_INPUT, not implied telemetry support. No runtime source, schema,
roadmap activation, application code, longitudinal code or AI client is created.
RUNTIME_FINGERPRINT_UNCONFIRMED and parked qualification pending remain unchanged.
Repository license evidence is MIT-style (Z:license), without a new file-specific
Hoya attribution determination. No reference body is copied; no target LICENSE is
added. Hash verification is source integrity, not a license or safety approval.

Recommended single next development candidate: **ParameterDescriptor /
SourceKnowledgeDescriptor**. Source/units/default discrepancies must be made
explicit before an observer or supervisor can responsibly discuss parameter
families. This does not advance PR #9 real writer activation: its independent
owner/policy/evidence gates stay closed. No next task starts in H1.

## Evidence index

All 104 inspected ranges across 40 source/reference files are linked below,
including 35 individual named catalog entries. Supporting full-file hashes do
not qualify unrelated service behavior.

- [H:telemetry](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L21-L145): _extract_telemetry_from_log (PROVEN).
- [H:episodes](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L148-L284): _detect_key_episodes (HEURISTIC).
- [H:selection](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L287-L304): _extract_all_frames_sync (PROVEN).
- [H:snippet](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L307-L340): CORE_CONTROL_SOURCE_CODE (CONDITIONAL).
- [H:sampling](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L343-L453): api_autotune_extract_telemetry (PROVEN).
- [H:knowledge](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L414-L481): api_autotune_extract_telemetry (PROVEN).
- [H:apply](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L484-L549): api_autotune_apply_params (PROVEN).
- [H:config](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/features/autotune.py#L552-L607): api_autotune_get_config / api_autotune_set_config / register (PROVEN).
- [P:clamp](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/params.py#L73-L110): infer_type_from_setting / clamp_numeric (PROVEN).
- [P:read](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/params.py#L124-L217): _read_param_value / get_param_values (PROVEN).
- [P:write](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/params.py#L241-L375): put_typed / set_param_value (PROVEN).
- [J:history](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/param_changes.py#L34-L154): PARAM_CHANGE_SOURCES / append_param_change (PROVEN).
- [S:catalog](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/settings.py#L58-L93): read_settings_file / group_index (PROVEN).
- [S:cache](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/services/settings.py#L214-L234): get_settings_cached (PROVEN).
- [A:providers](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L8-L50): AI_PROVIDERS (PROVEN).
- [A:config](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L52-L205): loadAiConfig / saveAiConfig / saveRollbackSnapshot (PROVEN).
- [A:prompt](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L303-L434): buildSystemPrompt / buildUserPrompt (PROVEN).
- [A:rules](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L436-L809): analyzeWithBuiltinEngine (HEURISTIC).
- [A:parse](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L811-L981): normalizeAiResult / parseFreeformTextToResult (REJECTED).
- [A:network](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/ai_client.js#L984-L1119): callAiTuner (PROVEN).
- [W:flow](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/controller.js#L519-L600): bindEvents (PROVEN).
- [W:apply](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/controller.js#L606-L667): bindResultActions (PROVEN).
- [W:rollback](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/controller.js#L686-L826): showRollbackConfirmModal (PROVEN).
- [V:results](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/view.js#L269-L339): renderResultsHtml (PROVEN).
- [V:rollback](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/view.js#L342-L403): renderRollbackModalHtml (PROVEN).
- [I:index](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/src/features/logs/autotuner/index.js#L1-L1): module export (PROVEN).
- [T:server](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/tests/test_autotune_telemetry.py#L1-L186): four pytest tests (PROVEN).
- [T:web](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/web/tests/autotuner_contract.test.mjs#L1-L370): Node UI contract tests (PROVEN).
- [F:params](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_functions.py#L180-L214): CarrotPlanner.update_params / get_carrot_accel (PROVEN).
- [F:follow](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_functions.py#L216-L369): _get_base_t_follow / dynamic_t_follow (PROVEN).
- [F:eco](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_functions.py#L454-L474): cruise_eco_control (PROVEN).
- [F:min](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_functions.py#L421-L452): _update_carrot_man (PROVEN).
- [F:calls](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_functions.py#L500-L513): update (PROVEN).
- [C:params](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_serv.py#L223-L243): CarrotServ.update_params (PROVEN).
- [C:gas](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_serv.py#L461-L522): _apply_speed_source_gas_floor (PROVEN).
- [C:sources](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_serv.py#L1404-L1437): CarrotServ update speed selection (PROVEN).
- [C:publish](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_serv.py#L1468-L1487): carrotMan publication (PROVEN).
- [M:vision](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/carrot_man.py#L1428-L1465): carrot_curve_speed_params / vturn_speed (PROVEN).
- [D:model](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/desire_helper.py#L76-L91): _update_params_periodic / _make_model_turn_speed (PROVEN).
- [L:torque](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/latcontrol_torque.py#L134-L164): update_live_torque_params / update (PROVEN).
- [L:nn](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/latcontrol_torque.py#L174-L195): update (PROVEN).
- [L:long](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/longcontrol.py#L69-L133): LongControl / _refresh_longitudinal_tuning (PROVEN).
- [U:ratio](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/steer_ratio.py#L1-L23): resolve_vehicle_model_steer_ratio (PROVEN).
- [U:vm](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/controlsd.py#L106-L126): Controls.state_control (PROVEN).
- [U:delay](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/controlsd.py#L168-L175): Controls.state_control (PROVEN).
- [N:mpc](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py#L401-L445): LongitudinalMpc.update (PROVEN).
- [N:accel](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/longitudinal_planner.py#L193-L210): LongitudinalPlanner.update (PROVEN).
- [N:cost](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/controls/lib/longitudinal_planner.py#L270-L284): LongitudinalPlanner.update (PROVEN).
- [K:linear](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/opendbc_repo/opendbc/car/interfaces.py#L593-L600): torque_from_lateral_accel_linear (PROVEN).
- [K:settings](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1-L1): JSON catalog identity (PROVEN).
- [K:parameter:CruiseMaxVals0](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1089-L1104): params[CruiseMaxVals0] (PROVEN).
- [K:parameter:CruiseMaxVals1](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1105-L1120): params[CruiseMaxVals1] (PROVEN).
- [K:parameter:CruiseMaxVals2](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1121-L1136): params[CruiseMaxVals2] (PROVEN).
- [K:parameter:CruiseMaxVals3](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1137-L1152): params[CruiseMaxVals3] (PROVEN).
- [K:parameter:CruiseMaxVals4](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1153-L1168): params[CruiseMaxVals4] (PROVEN).
- [K:parameter:CruiseMaxVals5](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1169-L1184): params[CruiseMaxVals5] (PROVEN).
- [K:parameter:CruiseMaxVals6](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1185-L1200): params[CruiseMaxVals6] (PROVEN).
- [K:parameter:DynamicTFollow](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2709-L2725): params[DynamicTFollow] (PROVEN).
- [K:parameter:DynamicTFollowLC](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2785-L2801): params[DynamicTFollowLC] (PROVEN).
- [K:parameter:EnableSpeedTF](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2769-L2784): params[EnableSpeedTF] (PROVEN).
- [K:parameter:TFollowGap1](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2645-L2660): params[TFollowGap1] (PROVEN).
- [K:parameter:TFollowGap2](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2661-L2676): params[TFollowGap2] (PROVEN).
- [K:parameter:TFollowGap3](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2677-L2692): params[TFollowGap3] (PROVEN).
- [K:parameter:TFollowGap4](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2693-L2708): params[TFollowGap4] (PROVEN).
- [K:parameter:TFollowDecelBoost](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2802-L2818): params[TFollowDecelBoost] (PROVEN).
- [K:parameter:AChangeCostStarting](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1218-L1233): params[AChangeCostStarting] (PROVEN).
- [K:parameter:LongTuningKpV](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1251-L1267): params[LongTuningKpV] (PROVEN).
- [K:parameter:LongTuningKiV](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1285-L1301): params[LongTuningKiV] (PROVEN).
- [K:parameter:LongTuningKf](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1268-L1284): params[LongTuningKf] (PROVEN).
- [K:parameter:StoppingAccel](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2836-L2851): params[StoppingAccel] (PROVEN).
- [K:parameter:StopDistanceCarrot](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1201-L1217): params[StopDistanceCarrot] (PROVEN).
- [K:parameter:LateralTorqueCustom](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L654-L669): params[LateralTorqueCustom] (PROVEN).
- [K:parameter:LateralTorqueKpV](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L702-L717): params[LateralTorqueKpV] (PROVEN).
- [K:parameter:LateralTorqueKiV](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L718-L733): params[LateralTorqueKiV] (PROVEN).
- [K:parameter:LateralTorqueKf](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L734-L749): params[LateralTorqueKf] (PROVEN).
- [K:parameter:LateralTorqueFriction](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L686-L701): params[LateralTorqueFriction] (PROVEN).
- [K:parameter:LateralTorqueAccelFactor](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L670-L685): params[LateralTorqueAccelFactor] (PROVEN).
- [K:parameter:SteerRatioRate](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1072-L1088): params[SteerRatioRate] (PROVEN).
- [K:parameter:SteerActuatorDelay](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L942-L957): params[SteerActuatorDelay] (PROVEN).
- [K:parameter:TurnSpeedControlMode](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L3105-L3120): params[TurnSpeedControlMode] (PROVEN).
- [K:parameter:AutoCurveSpeedFactor](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1334-L1350): params[AutoCurveSpeedFactor] (PROVEN).
- [K:parameter:ModelTurnSpeedFactor](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L3138-L3153): params[ModelTurnSpeedFactor] (PROVEN).
- [K:parameter:MapTurnSpeedFactor](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L3121-L3137): params[MapTurnSpeedFactor] (PROVEN).
- [K:parameter:AutoCurveSpeedLowerLimit](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L2819-L2835): params[AutoCurveSpeedLowerLimit] (PROVEN).
- [K:parameter:CruiseEcoControl](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot_settings.json#L1007-L1023): params[CruiseEcoControl] (PROVEN).
- [K:keys](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/common/params_keys.h#L1-L1): Params key registry identity (PROVEN).
- [Q:plan](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/cereal/log.capnp#L1190-L1219): LongitudinalPlan (PROVEN).
- [Q:car](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/opendbc_repo/opendbc/car/car.capnp#L183-L206): CarState (PROVEN).
- [Q:actuators](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/opendbc_repo/opendbc/car/car.capnp#L424-L438): CarControl.Actuators (PROVEN).
- [Q:carrot](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/cereal/custom.capnp#L14-L34): CarrotMan (PROVEN).
- [Z:license](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/LICENSE#L1-L7): repository license (PROVEN).
- [B:snapshot](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/b24ef18e4270af5ab4f731aca31cf95f4f4b0cce/src/cyberpilot_autotune/contracts/observation.py#L1-L43): ObservationSnapshot (PROVEN).
- [B:gate](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/b24ef18e4270af5ab4f731aca31cf95f4f4b0cce/src/cyberpilot_autotune/safety/gate.py#L1-L220): SafetyGate (PROVEN).
- [B:learner](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/b24ef18e4270af5ab4f731aca31cf95f4f4b0cce/src/cyberpilot_autotune/core/residual.py#L1-L219): ResidualStatisticsLearner (PROVEN).
- [B:contract](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/b24ef18e4270af5ab4f731aca31cf95f4f4b0cce/src/cyberpilot_autotune/adapters/carrot_receipt_contract.py#L1-L491): evaluate (PROVEN).
- [B:adapter](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/b24ef18e4270af5ab4f731aca31cf95f4f4b0cce/src/cyberpilot_autotune/integrations/carrot/adapter.py#L1-L428): CarrotReadOnlyAdapter (PROVEN).
- [R:source](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/e4361678ed176cbd7c0bb6f838d3daa7174caf22/src/cyberpilot_autotune/integrations/carrot/sidecar/source.py#L1-L124): receive-only SubMaster bridge (PROVEN).
- [R:sidecar](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/e4361678ed176cbd7c0bb6f838d3daa7174caf22/src/cyberpilot_autotune/integrations/carrot/sidecar/runner.py#L1-L203): SidecarRunner (PROVEN).
- [G:application](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5/docs/steering_application_contract.md#L1-L149): steering application contract (PROVEN).
- [G:coordinator](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5/src/cyberpilot_autotune/application/coordinator.py#L1-L453): BoundedSteeringApplicator (PROVEN).
- [G:policy](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5/src/cyberpilot_autotune/application/contracts.py#L1-L290): SteeringPolicy / SteeringRequest / AuthorizationGrant (PROVEN).
- [G:ports](https://github.com/rownlvh8875-coder/cyberpilot-autotune/blob/6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5/src/cyberpilot_autotune/application/ports.py#L1-L32): SteeringTarget / ApplicationAuthority (PROVEN).
- [K:selection](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/opendbc_repo/opendbc/car/car_helpers.py#L157-L180): get_car (PROVEN).
- [K:removed](https://github.com/ajouatom/openpilot/blob/0e9c589c1b83027146f909a9cdc306c2c665ceaf/openpilot/selfdrive/carrot/server/tests/test_settings_schema.py#L59-L67): test_obsolete_lead_response_settings_are_removed (PROVEN).
