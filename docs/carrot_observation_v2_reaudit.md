# Observation v2 exact-head contract re-audit

## Authority and execution plan

This implements the owner's Phase 8A.4 specification. Target base:
`03c3f2f36cbe47a9afec97ce7b9d411d3aa81ccb`. Reference repository:
https://github.com/rownlvh8875-coder/openpilot, original source base
`604bc0a22733e648ec05b268da1ffaae7db52a69`, observation-v2 exact head
`c2130730239bcdb4cbde9361ab90c8d99aa4ff55`.

The supplied specification is the approved design and execution authority.
Implementation is inline, with an independent read-only source-gate review and
one final whole-branch review. Existing isolated worktree is reused. No reference
repository changes, actual extraction, cache implementation, SubMaster adapter,
persistence, controller writes, real logs or vehicle work are authorized.

- [x] Recheck target main, reference PR base/head, Draft/Open/mergeability,
  successful exact-head checks and unresolved threads; baseline: 536 tests pass.
- [x] Inspect all 26 changed files plus supporting schema/clock/VM sources;
  record raw Git blob hashes and symbol ranges in the source evidence JSON.
- [x] Prove the mandatory joins and truth tables before adding runtime code.
  If any gate is unresolved, add only audit evidence and record the blocker.
- [x] Write failing synthetic contract/evidence tests, observe the failures,
  implement the minimum permitted evaluator, and pass the full regression.
- [x] Specify immutable caller policy, static non-identifying context, baseline
  epoch and cache ownership; pin at least 40 independent literal expected cases.
- [x] Verify lint, formatting, types, branch coverage, four unchanged replay
  goldens, build, fresh wheel and independent review. Append-only publication and
  exact-head CI are separately recorded on the Draft PR and completion report.

Files: this report; `docs/evidence/carrot_observation_v2_sources.json`;
`docs/evidence/carrot_observation_v2_cases.json`; audit validator/tests; and,
only after all mandatory gates are proven,
`src/cyberpilot_autotune/adapters/carrot_receipt_contract.py` and its focused
tests. Existing runtime, gate, learner, replay fixtures and reference source
remain unchanged.

Review focus: receipt duplication after bounded cache eviction; clock-domain
mixing and evaluation-delay double counting; current/latest substitution for an
exact source; caller context that fails to distinguish MEB routing; unavailable
unions or malformed numerics converted into valid zero/False. Tests must pin
these failure classes, not merely mirror implementation branches.

Initial source ruling: v2 optional Float64 payloads preserve actual calculation
values. Float32 actuator rounding is not a target mismatch. Exact source CC and
source CS are mandatory; latest-value fallback cannot repair missing history.
The readiness decision below follows an independent source-gate review and
executable synthetic contract evidence, not the presence of fields alone.

## Decision and proof boundary

**CONTRACT_READY_FOR_PHASE_8B**, exclusively for implementing the documented
read-only extraction boundary in a separately authorized phase. No actual
adapter, source subscription, cache or learner connection is implemented here.
PR #20 remains Draft/Open at the exact pin. This contract does not approve its
merge, vehicle use, production safety or physical measurement.

All mandatory gates are PROVEN within the explicit software contract: exact
receipt/source-command/source-CarState joins; activity and instantaneous/output
limit tri-state evidence; frozen live-VM provenance; clipped pre-controller
target; known override producer; same-domain clocks/age; caller static context,
policy and immutable baseline. The old measurement and MEB target blockers are
resolved at this new pin. Historical audits remain correct for their old pins.

Ruling: the latest owner specification defines desired response as the actual
clipped pre-controller **host intent**. It does not require proof that the
underlying model/lane-plan/pose was currently correct. The old plan-health claim
is not carried forward as an attested fact. No planning-quality or physical
vehicle-response claim may follow from source_valid. If a later application
requires target-origin health, that is an additional contract and source audit.

## Source evidence and provenance

[Source manifest](evidence/carrot_observation_v2_sources.json) lists all **26**
changed files and **20** supporting files: raw base/head Git blob SHA-256, byte
and line counts, inspected symbols and **46** hashed source ranges. It includes
all schema/card/controls/CAN tests, fixture metadata, CI/developer tools and both
upstream protocol documents. Local read-only verification covers **75** existing
raw blobs and **48** preserved legacy field declarations. Missing base blobs are
null. Hashes use Git bytes, independently of checkout line endings.

The root and opendbc LICENSE blobs provide MIT-style license evidence; this is
not a conclusion about every embedded third-party file. No original source body,
legacy binary fixture or source package is copied into this repository. Contract
code, prose and synthetic cases are independently authored from the inspected
semantics. Target license selection/attribution remains an owner decision; no
LICENSE is added.

Critical source trace (links are exact-head, not branch links):

- [VM input/result capture](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/controls/controlsd.py#L119-L135)
  selects CS/LP once, updates VM using effective stiffness/ratio, calculates the
  curvature and immediately freezes the exact result/inputs/current health.
- [Target before MEB correction](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/controls/controlsd.py#L231-L285)
  captures the clip result before PID/EPS/VM output overwrites final curvature.
  Both groups attach to the same CC; its Event is created at lines 457–460.
- [Current measurement health](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/controls/lib/measurement_observation.py#L49-L107)
  excludes simulation/ignored checks, requires seen/alive/valid/freq_ok, canValid,
  LP payload health, present non-future stamps and finite actual values.
  Startup's historical latch is not substituted for current health.
- [Final host apply](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/car/card.py#L415-L442)
  captures after reboot/readiness suppression, immediately before the unchanged
  CI.apply, then completes the same receipt with that call's returned output.
- [Receipt capture/completion](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/car/actuation_receipt.py#L72-L123)
  preserves source-command and apply times, finite request/output value copies,
  controller kind/limits, observed safety permission and return state.
- [Delayed publication](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/car/card.py#L338-L358)
  publishes the previous completed receipt before the next apply (step 512–521).
  A skipped apply clears receipt state rather than reusing an old receipt.
- [Controller evidence](https://github.com/rownlvh8875-coder/openpilot/blob/c2130730239bcdb4cbde9361ab90c8d99aa4ff55/openpilot/selfdrive/controls/lib/lateral_observation.py#L13-L75)
  keeps raw instantaneous flags separate from timer saturation. MEB uses its
  actual PID and never its dummy angle log. Output comparison uses card's
  apply-boundary CS.vEgo, which is not necessarily measurement.inputSpeedMps.
  The evaluator trusts that versioned observation; it never recomputes it using
  the wrong historical speed or introduces a threshold.

## Exact cohort, cache ownership and missing behavior

Receipt identity is `(sourceCarControlMonoTime, hostApplyMonoTime)`. Both must be
present positive monotonic UInt64 timestamps. Repeated source commands are valid
different cohorts only when their apply times differ and advance.

1. Retrieve immutable source CarControl by exact Event.logMonoTime equality with
   receipt.sourceCarControlMonoTime. Require observation v2, recognized matching
   controller and retained event validity. Reject absent or ambiguous keys.
2. Retrieve immutable source CarState by exact Event.logMonoTime equality with
   that command's measurement.carStateMonoTime. Validate its actual event/can
   validity and compare speed/angle exactly to the recorded promoted Float32
   source values. Obtain override only from its steeringPressed.
3. Never join a current/latest command or CarState to a previous receipt.
   finalRequestedActuators describes the final suppressed request, while the
   exact source CC retains the original observation. For host-active cohorts
   their actuator maps must match; inactive suppression is not a target rewrite.
4. Caller owns a bounded immutable message cache with explicit capacity and
   retention policy. Missing source after eviction, key collision with different
   bytes, incomplete extraction or a late receipt rejects. No interpolation or
   latest-value fallback is allowed. Cache implementation is Phase 8B work.
5. Caller consumes every receipt attempt, including rejected attempts, **before**
   retry can occur. It increments an adapter-owned strictly increasing sequence
   and retains a host-apply high-water across admission resets in the same clock
   stream. The evaluator receives previous sequence, previous apply time and
   consumed cohort IDs; it has no mutable state and cannot consume them itself.
   The high-water rejects older/duplicate applies even after bounded ID eviction.
   A new clock/producer stream requires fresh caches/context; never mix hosts or
   boots merely because both timestamps say monotonic.
6. Current carOutput Event.valid describes a different current-command check.
   It neither invalidates a complete previous receipt alone nor repairs a
   malformed one. Independent seen/alive/frequency transport health is required;
   the outer valid bit is deliberately ignored by this evaluator.

Exact liveParameters cache is **not required** by this contract. The pinned
producer freezes the effective stiffness, resolved private/scaled ratio, offset,
roll, source LP timestamp, payload/transport health and actual VM result in that
same command. The evaluator trusts that versioned producer calculation, but
rechecks availability, finiteness, ordered timestamp/domain, current embedded
health, caller static CP attestation and age/skew limits. It does not claim to
recompute VM, verify planner correctness or independently authenticate the
publisher. A later debug/recomputation mode may require retained LP; it is not
silently made mandatory or inferred from a newer LP here.

`static_context_digest`, `steering_pressed_supported`, exact-lookup uniqueness and
transport-health flags in neutral inputs are **caller attestations**, not wire
fields invented by this audit. Phase 8B must establish them from its known pinned
publisher/CP/session and producer capabilities before invoking this contract.
Default message builders cannot attest a False steeringPressed. Audited producer
examples include VW MEB and Tesla; unsupported ports must report unavailable.
The pure evaluator's passing tests do not qualify a real extraction boundary.

## Snapshot mapping

| Snapshot field | Final source and exact join | Units/sign | Missing or failure |
|---|---|---|---|
| timestamp_s | Receipt hostApplyMonoTime / 1e9 | monotonic seconds | Reject missing/wrong domain |
| sequence | Caller mapping-attempt counter | nonnegative, strictly increasing | Reject repeat/regression; never SubMaster.frame |
| source_age_s | Maximum same-domain source duration at apply, below | seconds | Reject negative/unknown duration |
| context_key | Contract/r1/o2/controller + static context digest + baseline epoch | Non-identifying version namespace | Reject mismatch/unpinned context |
| source_valid | Entire join/quality/policy conjunction below | Bool | No Snapshot on mandatory failure |
| speed_mps | Frozen measurement.inputSpeedMps, corroborated by exact CS | m/s, nonnegative | Reject missing/nonfinite/negative |
| desired_curvature_inv_m | Source CC observation desiredTargetCurvatureInvM | 1/m, pinned branch's signed target convention | Reject unavailable; never final MEB actuator |
| measured_curvature_inv_m | Frozen measurement.measuredCurvatureInvM | 1/m, controlsd's negative VM curvature convention | Reject fallback/invalid/unavailable |
| lateral_acceleration_mps2 | Intentionally not supplied | None | Always None; no physical acceleration claim |
| controller_saturated | Same receipt A/B instantaneous/output evidence | Tri-state | None/reject unknown/inactive; no old timer |
| driver_override | Exact source CS.steeringPressed, known producer | Bool/None; input observation | Unknown support/value rejects |
| baseline_parameters | Independently trusted immutable caller map + epoch | Caller-owned units | Exact mismatch rejects; never Params/CP inference |
| control_active | Same-cohort host admission + observed safety permission | Tri-state | None/reject unknown, not cruise/UI enabled |

The two curvature fields retain this pinned branch's common control convention;
this is not a claim of cross-vehicle physical sign calibration. Measured curvature
is a VM estimate, not returned actuator curvature or a physical road sensor.
For PID/torque/angle the target is the pre-controller curvature assigned to the
request before Float32 serialization. Float64 target versus Float32 actuator
rounding is expected. For MEB the pre-PID target and corrected final request can
differ algorithmically. The evaluator preserves both interpretations and makes
no target/request equality requirement.

## Tri-state truth tables and source validity

Activity presupposes a supported, complete receipt, exact source CC/cohort,
known compatible controller, finite actuator pointer contents, known safety and
returned output. Those are software observations, not individual CAN approval.

| Host activity | Safety observation | Returned/cohort | control_active |
|---|---|---|---|
| active | allowed | known compatible | True |
| inactive | allowed or disallowed | known compatible | False |
| active | disallowed | known compatible | False |
| unavailable | any | any | None |
| any | unavailable | any | None |
| any | any | missing/incompatible | None |

| Same active host cohort, supported kind and finite return | A instantaneous | B output | controller_saturated |
|---|---|---|---|
| yes | limited | any known state | True |
| yes | any known state | limited | True |
| yes | notLimited | notLimited | False |
| yes | unavailable | unavailable/notLimited | None |
| yes | notLimited | unavailable | None |
| no, inactive/unknown/nonfinite/mismatched | any | any | None |

Unknown wire enum values normalize to unavailable at extraction, and unknown
neutral values reject. Positive evidence can veto even when the other limit is
unavailable; two negative predicates are necessary to assert False. MEB dummy
angle/timer saturated fields are never inputs.

| Complete conditions | source_valid / result |
|---|---|
| Supported receipt1/observation2/measurement1, exact joins, domains/order, current live measurement health, available finite inputs/target, context/baseline match, known activity/limit/override, transport + all caller bounds pass | True / immutable Snapshot |
| Same, safety disallowed or driver override or positive limit | True / quality-valid Snapshot; existing runtime admission must veto learning |
| Inactive host | False / no Snapshot; saturation unknown; producer intentionally supplies no inactive measurement |
| Any mandatory version/join/pointer/number/health/clock/context/policy missing, invalid or mismatched | False / explicit rejection |

On rejection MappingDecision.snapshot is None. Its optional tri-state diagnostic
fields preserve only proofs reached before rejection; they are not a partial
Snapshot or permission to learn. Inactive commands can prove False even with
their intentionally absent nested measurement. No None becomes numeric zero or
False to satisfy a mapping requirement.

## Caller age, skew and version policy

All seven age/skew limits are required finite nonnegative caller-supplied
seconds: receipt evaluation age; command-to-apply delay; CS age at apply; LP age
at apply; calculation age at apply; safety-state age; maximum source skew.
There are no vehicle defaults. Test limits/geometry are explicitly synthetic
and have no vehicle qualification. Missing/incomplete/unsupported policy rejects.
The policy freezes receipt versions (1), observation versions (2), measurement
versions (1), a nonempty subset of pid/torque/angle/mebCurvature, static context
digest and nonnegative baseline epoch. A caller cannot enable an unaudited wire
version by listing it in configuration.

Let H = hostApplyMonoTime, C = exact source CC time, S = measurement CS time,
L = measurement LP time, K = calculationMonoTime, E = evaluation time, O = safety
observation time and P = safety-state publication time. Require:

`S <= K <= C <= H <= E`, `L <= K`, and separately `P <= O`.

All stamps are positive, present UInt64s. S/L/K/C/H/E use the same attested
CLOCK_MONOTONIC stream. P/O use CLOCK_BOOTTIME. Subtract only within each domain:

`source_age_s = max((H-C)/1e9, (H-S)/1e9, (H-L)/1e9, (H-K)/1e9, (O-P)/1e9)`.

Receipt age `(E-H)/1e9` is checked independently and excluded from source_age_s.
SafetyGate later adds `now_s - snapshot.timestamp_s` exactly once. Cross-domain
absolute offsets never enter that sum. Negative durations reject rather than
clamp. Source skew is `(max(C,S,L,K)-min(C,S,L,K))/1e9`; it never mixes P/O.
The contract assumes one qualified live publisher clock/session; suspend or
stream changes must invalidate that attestation and caches rather than repair
timestamps. No wall clock, receive time or frame number substitutes for stamps.

## Static VehicleModel and baseline context

The caller canonical context contains mass, rotationalInertia, wheelbase,
centerToFront, steerRatioRear, tireStiffnessFront/Rear and initial steerRatio,
as traced through VehicleModel.__init__, update_params and calc_slip_factor.
It also contains steerControlType, lateral tuning kind, **brand and flags**:
is_volkswagen_meb branches on brand plus VolkswagenFlags.MEB (16), not generic
angle type. That bit is an inspected platform discriminator, not a vehicle
tuning constant. Controller kind must agree between static context, source CC,
receipt and allowed policy.

Source software revision is exactly c2130730239bcdb4cbde9361ab90c8d99aa4ff55;
schema revision is observation-v2-measurement-v1, backed by the manifest's raw
schema hash. The caller must independently attest controlsd and card use the
same pinned static CP/session; a command-side envelope digest is not a new
published CP hash. A future extraction implementation must qualify this binding
and reject unknown/restarted/mismatched CP. No CarParams reader is implemented.
Effective stiffness/ratio/offset/roll are the actual frozen per-command values,
so private Params need not and must not be read by this contract.

Canonical JSON uses fixed field names, normalized finite binary64 numbers,
sorted keys, compact separators and SHA-256 lowercase hex. Context namespace
includes contract1, receipt1, observation2, resolved kind, that digest and caller
baseline epoch. No VIN, GPS, route, driver identity or device serial field exists.
Caller versions/epochs are software state identifiers, never identifying strings.
Baseline is defensively copied without coercing numeric values; it must exactly
match an independently trusted caller map and epoch. It is never derived from
actuators, learned Params or CP geometry.

## Synthetic evidence and verification

[Literal cases](evidence/carrot_observation_v2_cases.json) contain 69 independently
specified expected projections covering all 40 requested scenarios and additional
unknown/invalid enums, health, types, geometry, timestamps and output failures.
NON_FINITE is a test-side marker; JSON itself contains no nonfinite value or PII.
Focused tests cover actual inactive wire behavior, positive/negative limit truth
tables, exact zero, Float64/Float32 rounding, caller defensive copies and no
recomputation of MEB output limits using the measurement's different speed.
Property tests exercise malformed boundaries, nonfinite/unavailable inputs,
timestamp substitution, deterministic repeats and evaluation-delay independence.

The source-gate reviewer independently found no Critical/Important source blocker
under this explicitly narrowed host-target contract. The first incomplete mapper
failed 69 literal cases; the completed evaluator passes them. Debugging exposed
an inactive-v2 nuance: its intentionally absent nested measurement must not erase
a proven inactive diagnostic. A failing test preceded its correction. Full
regression, source evidence and final independent review/publication results are
recorded after execution below and in the final PR report.

```sh
python -m tests.audit.validate_observation_v2
python -m tests.audit.validate_observation_v2 --reference-repository <read-only-clone>
python -m ruff check .
python -m ruff format --check .
python -m mypy src/cyberpilot_autotune
python -m pytest -q
python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90
python -m coverage report --include="*/adapters/carrot_receipt_contract.py" --fail-under=95
python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay
python -m build
```

CI validates offline evidence and contract branch coverage on the existing
Windows/Ubuntu and Python 3.12.3/current 3.12 matrix. Wheel checks import every
installed module outside the checkout, verify all four unchanged replay goldens
and evaluate an explicitly supplied synthetic fixture against the installed
wheel. No openpilot/cereal package or reference repository is a test dependency.

## Qualification record

Local CPython 3.12.14: **668 passed, zero failed/skipped**. Coverage is
branch-inclusive: **98.81% overall**, **100.00% contract** (298 statements,
58 branches), **100.00% safety**, **97.85% residual**, **98.48% replay**. Ruff lint
and formatting pass (106 files); strict mypy passes 32 source files. Both the
offline validator and optional raw Git source/range/legacy verification pass.

A separate clean clone and fresh virtual environment installed upgraded pip and
editable .[dev], then repeated lint, formatting, types, validator, full pytest,
coverage, contract threshold, four replay goldens and wheel/sdist build. A further
isolated wheel environment imported the root plus 31 submodules outside the
checkout, ran all four replay CLI goldens and evaluated the explicit synthetic
contract fixture against the installed wheel. Its Snapshot preserved the trusted
baseline. Both evidence JSON files are byte-identical in the built sdist.
Reference source programs were not installed or executed by these target tests.

The independent whole-branch read-only review covered target base
03c3f2f36cbe47a9afec97ce7b9d411d3aa81ccb through implementation head
bc16a00b92960aa454e529214892e7b21f842ecb: **zero Critical, Important or Minor
findings**. The reviewer independently repeated 668 tests, 135 focused tests,
100% contract coverage, raw evidence checks, lint/format/types and 32 additional
adversarial checks. No re-review of this subsequent documentation-only record is
claimed. Source-gate review separately confirmed the required software signals.

Remaining obligations belong to the future authorized extraction boundary:
actual union/pointer extraction, trustworthy static CP/session binding and known
override producer support, bounded exact caches and transactional attempt
consumption. Passing this pure contract does not implement or qualify them.
No production SCons, device IPC, physical actuation, real data or vehicle test is
part of this audit. Phase 8B remains NOT_STARTED; PR #20 remains Draft/unmerged.
