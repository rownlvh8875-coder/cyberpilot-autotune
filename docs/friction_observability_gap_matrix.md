# Current observability gaps

A=AVAILABLE_CURRENTLY; E=DERIVABLE_EXACTLY from the named source/static evidence;
P=DERIVABLE_APPROXIMATELY; N=NOT_PUBLISHED/UNAVAILABLE; W=WRONG_STAGE;
M=MISSING_COHORT_BINDING. A published field is not proof that data were collected,
healthy, or aligned. No driving data is read in H6.

| Required signal | c213 runtime | f5e4 current | local observation-v2 at H6 base |
|---|---|---|---|
| raw callback a | P, M (desired-roll*g inputs) | P, M | N; target curvature/measurement not ff input |
| raw callback u | N; f is scaled, quantized | N; f is scaled, quantized | W; requested/controller-output/applied actuator evidence |
| applied normalized torque | A, W for callback | A, W for callback | A receipt candidate, W for callback |
| desired / actual controller lateral accel | A Float32, M input linkage | A Float32, M input linkage | P via curvature/speed; not these controller locals |
| actual friction_input | P in LINEAR, N NN state | P in LINEAR, N NN state | N |
| normalized q | N; P only with additional exact inputs | N; P only with additional exact inputs | N |
| deadzone | P with CP and actual VM, M | P with actual VM, M | N (angle deadzone/effective helper state absent) |
| threshold | E=0.3 only exact callback pin | E=0.3 only exact callback pin | E via source only, N applied callback ID |
| per-call compensation flag | N executed branch | N executed branch | N |
| explicit friction contribution | N | N; NN override differs in stage | N |
| mode / callback / NN model identity | CP tuning partial; N/M executed branch | CP tuning partial; N/M executed branch | controller_kind partial, N full NN/GM/custom identity |
| installed F/C | CP startup/liveTorque estimates W/M | CP startup/liveTorque estimates W/M | baseline_parameters is caller metadata, W/M installed receipt |
| p/i/d/f decomposition | A, M exact inputs/gains | A, M exact inputs/gains | N |
| k_f / preclip / integrator state | N complete applied cohort | N complete applied cohort | N |
| saturation / full limiting | A saturation timer, N full receipt | A saturation timer, N full receipt | A explicit limit/activity receipts for pinned contract; no callback decomposition |
| steeringPressed | A carState, M consumed sample | A carState, M consumed sample | A exact-lookup carState/support contract (conditional caller evidence) |
| CP wheelbase / centerToFront | A static, E ratio with actual CP | A static baseline, W as dynamic state | A StaticVehicleContext at pinned R, E static ratio |
| dynamic geometry ratio | N: absent by design, not missing schema default | A liveParameters.centerToFrontRatio, M exact VM receipt | N; pinned R contract does not imply C support |
| applied VM geometry generation | static startup binding needs actual CP | N/M; LP ratio is candidate, not atomic applied receipt | N |
| stiffness / effective steer ratio | LP candidates; M applied SR-rate/CustomSR | LP candidates; M applied SR-rate/CustomSR | A MeasurementEvidence effective values, R-only mapping; no raw-setting/installed generation |
| SAD/liveDelay alignment | A candidates, M applied alignment | A candidates, M applied alignment | command/apply times A, N effective controller delay identity |
| input/output exact timestamp linkage | Event times A, M full controller cohort | Event times A, M full controller cohort | explicit receipt/source measurement timestamps A; N q/ff/geometry-generation cohort |
| vehicle/source identity | CP candidates E digest, runtime confirmation separate | CP candidates E digest, runtime confirmation separate | qualified caller static source contract R only, not actual runtime fingerprint confirmation |

## Evidence and admissibility

friction_model_sources.json pins 30 files and 52 whole-file/symbol ranges.
The explicit source audit proves no CenterToFrontRatio, centerToFrontRatio or
update_geometry in c213 controlsd/paramsd/VM/schema/Params-key files. It separately
checks C's Params key, schema field, paramsd publication, controlsd update call
and LateralGeometry class. These are revision-specific facts, not version-name
assumptions. Source math is executed only as isolated AST function/class
declarations over toy scalars; native imports, Params and services never run.

Native Event/controlsd publication provides timestamps, not an exact receipt of
which LP/gain/friction inputs a specific callback consumed. observation-v2
already solves some command/carState/measurement receipt questions for c213;
it is preserved byte-for-byte and does NOT solve missing q/ff/installed geometry
state by analogy. The wire/schema has not been extended.

The prerequisites are not met. Final selection remains
NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS; design readiness is not empirical
or runtime readiness. No unavailable signal is synthesized from installed C,
a vehicle default, a branch name, or a later message.
