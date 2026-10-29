# H7 mapping to existing observation-v2 — no adapter implementation

The existing R-pinned observation-v2 mapping and PR8 are unchanged.
H7 adds no automatic support in the sidecar, no Phase8B.2B bypass and no mapping
into an H6 estimator or application evidence. Every reuse is conditional on an
independently verified exact source lookup/health contract.

| Existing v2 field / evidence | Classification | H7 treatment |
|---|---|---|
| exact source carState steeringPressed + support/health | REUSABLE_EXACT | candidate source join only when the very sample consumed by callback is proven |
| source carState time / event validity / CAN validity | REUSABLE_EXACT | retain domain and identity; receipt arrival/latest-seen is not consumption |
| source-command and host-apply times, exact lookup | REUSABLE_EXACT | future downstream command linkage candidate; not callback-local binding by itself |
| StaticVehicleContext mechanical digest | REUSABLE_CONTEXT_ONLY | R CP baseline; not current dynamic applied VM snapshot |
| effective stiffness/SR/angle offset/roll in MeasurementEvidence | REUSABLE_CONTEXT_ONLY / MISSING_COHORT | R measurement calculation context, not proof of callback consumption |
| requested / returned / final actuator torque | WRONG_STAGE | never substitutes callback_output_raw; keep exact downstream event identity |
| applied normalized torque | WRONG_STAGE | observable diagnostic, not raw pre-PID u |
| desired/measured curvature + speed | WRONG_STAGE | does not equal exact local desired/actual acceleration/error or callback a |
| baseline_parameters | REUSABLE_CONTEXT_ONLY / MISSING_COHORT | caller metadata, not exact installed F/C/gains or trusted baseline automatically |
| source timing/age/skew policy | REUSABLE_CONTEXT_ONLY | not an H7 empirical cutoff; exact causal IDs still required |
| controller_kind | REUSABLE_CONTEXT_ONLY | not executed LINEAR/NN_LITE/NN/GM/custom callback family/site |
| control_active / instantaneous receipt limits | REUSABLE_CONTEXT_ONLY / MISSING_COHORT | retain timer/instantaneous distinctions, require this callback cycle's witnesses |
| actual raw ff and callback a | MISSING | local binary64 capture required |
| independent observed q / per-call flag/deadzone/threshold | MISSING | no q reconstruction fallback |
| current installed F/C and realized PID gain generation | MISSING_COHORT | new actual latch/use receipts required |
| applied geometry generation / VM context ID | MISSING_COHORT | CP default or LP candidate is not sufficient |
| delay method/version/pair-correction receipt | MISSING | no implicit/double alignment |
| callback invocation / complete dependency manifest | MISSING | exact actual-consumption capture required |

REUSABLE_EXACT describes the semantics of a correctly supplied v2 witness; it
does not claim PR8's real extraction/runtime has been qualified. A similar field
name or equal numeric value cannot make an old field a new raw observation.
No actual v2-to-H7 adapter is provided.

## Stage example

raw ff=.625 and k_f=.5 imply PID f=.3125 in a synthetic example, before feedback
or clipping. Final requested torque has the opposite internal PID sign; applied
torque may then differ through downstream limits/dynamics. Even if applied torque
numerically equals .625, its stage/origin/event witness is not raw callback u.
Legacy Float32 logs widened to float64 remain legacy approximate evidence.

## Future causal join contract

Capture input carControl's local builder identity separately from the later
published command Event identity. DownstreamStageIdentity links host/applied data
to that exact command/cycle, with timestamps/domain/health. Unknown linkage means
unavailable/rejected, never a nearest-message guess. H7 core receipts normally
leave future applied stages None. A separate future adapter/sidecar upgrade and
native/schema/runtime qualification will be required after a producer exists.

NO_EMPIRICAL_ESTIMATOR_BRIDGE remains. Receipt != QualifiedEvidence;
receipt digest != AuthorizationGrant; installed context != trusted baseline or
approved target. Application bounds, writer ownership and application authority
are not supplied by observability.
