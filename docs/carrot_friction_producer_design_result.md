# Carrot read-only friction producer patch design — result

## Outcome and boundary

PASSIVE_FRICTION_PRODUCER_PATCH_DESIGN_READY

The selected future patch is a default-disabled, partial diagnostic producer.
It is NOT a complete eligible H7 producer: independent observed q is unavailable
in the legacy helper, so even an otherwise complete passive receipt remains
REJECTED/MISSING_Q. No native patch, compiled schema, decoder, subscriber or
runtime producer was implemented in this task. No application/science authority.

The user approved the next single recommended task, which was patch DESIGN.
Implementation/activation, merging H7 and vehicle/runtime work are not inferred.
The execution-plan skill guided the source-first design and tracked rulings;
test-driven development kept offline audit mutations RED before implementation;
verification/review skills require exact-head evidence, not a readiness inference.

## Git and source basis

| Item | Exact basis |
|---|---|
| Design branch | design/carrot-friction-observability-producer |
| CyberPilot/H7 base, PR16 | 5357d5d555d49b258affa237d83b8491b8a8c6ce |
| First docs-only freeze | 115fd98534eed0f39e4017e0d72fafbb662fc71d |
| Primary native blueprint R | c2130730239bcdb4cbde9361ab90c8d99aa4ff55 |
| Comparative native C | f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 |
| carrot-wip re-read | unchanged C; no auto-promotion/device claim |
| Preserved main | a5d3514f23797829eb58d08c638b22cf4dd30c8a |
| Preserved PR8, OPEN/Draft | e4361678ed176cbd7c0bb6f838d3daa7174caf22 |
| Preserved PR9, OPEN/Draft | 6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5 |

PR16 remains OPEN/Draft/MERGEABLE and its exact head has12/12 push+PR CI success.
The new design Draft PR is stacked against feat/friction-observability-receipt,
not main. Final exact head/commit list, independent review and publication CI are
recorded in that PR's final verification section, avoiding a self-referential SHA
inside the commit. Neither PR is automatically merged. All commits append-only.

## Delivered artifacts

- [Frozen design](superpowers/specs/2026-10-29-carrot-friction-producer-design.md)
  and [execution ledger](superpowers/plans/2026-10-29-carrot-friction-producer-design.md).
- [Future native implementation plan](carrot_friction_producer_implementation_plan.md),
  explicitly unexecuted, with source/symbol boundaries and native RED/GREEN gates.
- [32-file source/blob/range manifest](evidence/carrot_friction_patch_sources.json):
  nine native files/profile plus14 H7 acceptance files, all exact pinned Git bytes.
- [Wire mapping](evidence/carrot_friction_patch_wire.json):144 H7 semantics mapped,
  134 proposed wire fields/13 records/16 enums and10 local-only evaluator fields.
- [Synthetic binary64 proof](evidence/carrot_friction_patch_math.json):40 cases per
  R/C profile. Tests/audit/validate_carrot_friction_patch_design.py regenerates all
  manifests and validates exact native source equations without native imports.
- Tests/audit/test_carrot_friction_patch_design.py:19 design/mutation tests.
- CI adds only new audit/source-warming hooks, preserving every old gate.

## Selected architecture and wire design

Cycle-local LatControlTorque feedforward capture with caller-supplied consumed
source/applied context, narrowly optional PID taps and final sealing after the
existing control/command sends. Callback-only/PID-only/controlsd-only alternatives
cannot capture the full atomic cohort. No background collector or nearest-time join.

The target callback is the FF invocation with gravity_adjusted=True, not the
setpoint/measurement callbacks used for pid_log.error. a=desired-roll_compensation,
friction_input=desired-actual; raw ff precedes k_f. PID f, actual preclip sum,
clipped controller output, sign-inverted requested torque and downstream applied
torque remain different stages. Unsupported modes do not fall back to LINEAR.

Exact source/clock/reception IDs, local CC allocation identity, MODEL consumption,
applied geometry/installed F/C generations and actual gain-read cohort are explicit.
Later CC orientation mutation cannot backfill the consumed object. Unread k_i,
unselected delay, unavailable limit/applied witnesses stay unavailable. Final
identity is sealed only after real t_ctl/t_cmd and snapshot-completion time exist.

Proposed slot: empty CustomReserved3 type0xda96579883444c35 / Event ordinal110.
This is a proposal, not an allocated native patch. Float64 retains decoded consumed
values, UInt64 times/IDs, fixed-length Data digests; explicit unavailable/value
unions and unknown enum0 reject default/empty values. Receipt version is separate
from source/schema version. Initial proposed ordinals freeze after shipping and
cannot be regenerated from a different Python field order. Local evaluator and
authority fields never become wire permissions. No identifying payload is included.

Activation is default off, no new Params key. should_log=False; bounded scalar
taps only, hash/serialization/publication after existing command send. Exact
PubMaster.send is synchronous, with no Python nonblocking flag: numerical parity
does NOT qualify transport/deadline/allocation behavior or vehicle safety. Native
failure/performance qualification is mandatory before any activation.

## Why observed q remains unavailable

The unchanged helper directly interpolates [-C,C]. A straightforward q-first
rewrite changes binary64 values; parallel telemetry normalization is reconstructed,
not a proved operational helper state. Dividing by installed C is forbidden.
Both pinned profiles give19 bit differences/40, including16 numeric differences;
the remaining3 are signed-zero differences. A nonzero witness is:

| Operand/output | binary64 hex |
|---|---|
| synthetic error0.06 | 0x1.eb851eb851eb8p-5 |
| C0.125 | 0x1.0000000000000p-3 |
| diagnostic error/0.3 | 0x1.999999999999ap-3 |
| existing helper | 0x1.9999999999998p-6 |
| straightforward C*q | 0x1.999999999999ap-6 |

The toy deadzone0.06 is synthetic, not a proposed vehicle threshold; threshold0.3
comes from pinned source. This disproves universal bit-equivalence of that rewrite,
not the possibility of every future implementation. No numerical tolerance or
empirical/safety significance is inferred. H6 estimand u=a/F+C*q+b0 is unchanged.

## Verification run in this task

Local environment: Python3.12.14, NumPy2.5.4, existing dev/research venv; no new
dependencies, service setup or reusable environment configuration was necessary.

| Check | Observed result |
|---|---|
| Initial baseline |1416 passed |
| New audit RED |17 failed/1 passed before auditor/artifacts; later19 GREEN |
| Full pytest |1435 passed |
| Full branch coverage |98.52% combined,4350 statements/1192 branches |
| H7 observability |843/843 statements and276/276 branches,100%/100% |
| Ruff / format / strict mypy | pass;71 source files typed |
| H2/H3/H4/H5/H6/H7 audits | pass, exact-source and history checks retained |
| New design source audit |32 files,144 semantics;292 H7 tracked files protected |
| Synthetic replay goldens |11 tests pass; all4 fixture digests unchanged |
| sdist + fresh wheel | build pass;70 modules import without NumPy/native schema |
| Installed wheel H7/H6 | six source hashes each; immutable receipts/no authority |
| Wheel knowledge/owner/science | pass; optional dependency failures and research pass |

The only permitted edit to a H7 base-tracked file is the exact additive CI
extension. All H7 production source, tests, documents and evidence are unchanged.
The19 design tests exercise offline proposal validation, not a native producer.
No new production package exists, so coverage is explicitly the preserved package,
not a claim of100% coverage of the new audit tool. The new source audit runs with
GIT_NO_LAZY_FETCH=1 locally and is added to CI's network-isolated source job.
Final exact-head push/PR CI and reviewer verdict belong to the published PR record;
local verification alone is not reported as hosted CI success.

## Rulings and costs

1. Approval covers patch design, not native implementation/merges: another decision
   is needed for implementation/activation; no implied vehicle/application authority.
2. Stack on H7 without merging it: design PR depends on PR16's exact head.
3. Passive q unavailable rather than bit-changing C*q: full friction observability
   and eligible H7 observations remain blocked.
4. Reuse the dedicated cloud checkout and tracked ledger instead of unavailable
   remote skill shell scripts: manual bookkeeping, mitigated by commits/history audit.

Fresh builder check: nothing important left. Final read-only whole-branch review
is on the immutable final exact head and published externally, along with any
review findings/rulings/deferred minors. This is design review, not runtime approval.

## Retained status and next single task

PASSIVE_FRICTION_PRODUCER_PATCH_DESIGN_READY

FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
NO_EMPIRICAL_ESTIMATOR_BRIDGE
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED

All candidate_generation_allowed/application_authorized/runtime_accepted/
owner_proposal_allowed permissions stay false/absent. PR8/9 unchanged; no actual
native schema/controller/Params edits, vehicle, real data, estimator qualification,
application bridge, longitudinal work, external AI integration or upstream PR.

Recommended next single task: implement the selected passive diagnostic native
schema/producer patch with synthetic bit/state parity tests and default-disabled
activation, after separate approval. It cannot solve missing independent q, qualify
friction estimation or permit runtime use; those gates remain. Not started here.
