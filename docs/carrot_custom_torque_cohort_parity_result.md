# Offline custom selector/frame10 latch-reset parity result

## Outcome

PR18_M1_OFFLINE_CUSTOM_COHORT_TEST_GAP_CLOSED
CUSTOM_TORQUE_LATCH_RESET_RECEIPT_PARITY_VERIFIED_SYNTHETIC_ONLY

This closes the specific deferred PR18-M1 test gap: positive custom selectors,
tenth-frame latching/refresh, selector exit/reset and live-parameter recovery are
now exercised against actual pinned baseline and unchanged patched bodies. It is
not a native producer fix, deployment, estimator or runtime qualification. No old
tracked file, native asset/schema/controller, installed source, old CI/evidence or
prior PR is modified. PR19's NR-M1 non-ASCII reference-path issue remains deferred.

Base: CyberPilot PR19 f0fc6cdcab10447c2b855c9c65e7acafe7e3c2a9.
Branch: test/custom-torque-cohort-parity; stacked Draft PR against PR19, not main.
Native R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55.
Comparative C/carrot-wip re-read unchanged: f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
Tests target R only; C is not automatically ported/promoted or a device fingerprint.

## Exact execution, not a duplicate controller model

The repository-only harness loads the real R PID/LatControlTorque bodies using the
existing AST fixture. It additionally hash-validates and executes the exact R
LINEAR callback, apply_center_deadzone, get_friction and threshold assignment.
No native Python imports, Params instance, services, threads, socket or vehicle.
Only synthetic settings/vehicle-model/IO boundaries are doubled. The original
constructor is not executed: a documented post-construction state is supplied.

Actual compiled native Cap'n Proto tuning and LateralTorqueState fields preserve
Float32 installed/log readback, including pid_log.error. The fixture values are
binary-exact where used as literal cohort expectations. Callback calculations and
PID components/raw FF remain their actual consumed Python float operations; no
Float32 telemetry is substituted for raw callback output. All three callback
invocations per active update retain their actual arguments, F/C/offset and raw
returns. The recording wrapper delegates exactly once, never recomputes the FF.

Each baseline/patched pair runs31 consecutive cycles. Comparisons include output
and PID-state binary64 bits, actual serialized native log bytes, callback trace,
all settings reads/order/value/count, installed F/C/offset, gains and latched
selector. Independent hand-derived cohort tables prevent simple baseline/patched
agreement from hiding an unexecuted branch. The live-update call precedes update,
matching exact controlsd source order; this new fixture is NOT the full caller.

## Source behavior pinned — comment is not authority

Settings are requested before a latch, not treated as already installed. Request
positive selector1/2/3 at frame9; update reads/latches at10. Change custom values
after10, but capture the old installed cohort through19; refresh at20. Request0
at29; it is not executed until30. New live values remain blocked through30 and
are accepted at31. Regular scenario reads are exactly3 integer and12 float calls.

| Frames | Actually consumed installed F / C / offset | Effective gains kp / ki / kd / kf |
|---|---|---|
|1–9 |2.5 /0.125 /0.0625 |0.125 /0.0625 /0.03125 /0.5 |
|10–19 |1.75 /0.125 /0.03125 |0.25 /0.125 /0.0625 /0.5 |
|20–29 |2 /0.25 /0.03125 |0.5 /0.25 /0.125 /0.75 |
|30, previous selector1 |2 /0.25 /0.03125 |same custom gains |
|30, previous selector>=2 |2 /0.0625 /0.03125 |same custom gains |
|31 |3 /0.1875 /0.125 |same custom gains |

These are synthetic fixtures, NOT suggested values, thresholds or bounds. Native
condition is `elif self.lateralTorqueCustom > 1`, despite the source comment
`1 -> 0`. Thus1->0 does NOT immediately reset F/C/offset;2/3->0 does. Neither exit
resets PID gains, and a later live update changes only F/C/offset. This task pins
the behavior instead of silently changing native semantics or "correcting" it.

Installed selector/F/C/offset and gain epochs are checked separately, including a
selector-only epoch change when values remain the same. Inactive latch frames
still update settings before the active branch but never invent a callback/receipt.
If steeringPressed freezes integration, skipped k_i and gain generation remain
unavailable, not zero/default. Original synthetic settings failures propagate;
observer-only capture failures do not change commands, state or source reads.

## Cases and sensitivity

- 24 normal cases: selectors1/2/3 × LINEAR/NN_LITE × observer absent/disabled/enabled/failing.
- 16 inactive-latch cases: selectors1/2 × families ×10/20/30/all three inactive.
- 4 driver-override/frozen-integrator cases;2 original settings-failure cases.
- 6 in-memory mutants killed: cadence10->9, reset condition `>1`->`>0`, live bypass
  removed, extra settings read, wrong installed-factor capture, stale k_f capture.
- Additional harness/source/evidence checks: total58 new tests, all pass.

Mutants are byte-map copies used only in tests, never persisted to assets or native
Git state. Numeric/parity assertions catch control/read drift; independent receipt
checks catch metadata-only corruption even when controller values stay identical.
No universal equivalence, full controller branch coverage, full NN/weights, native
hardware/C++ build or deadline/backpressure result is inferred from this corpus.

## Evidence and preserved identity

[Evidence](evidence/carrot_custom_torque_cohort_parity.json) binds five exact-R
source files and their existing whole-file/symbol ranges by repo/revision/Git blob
and SHA-256, literal checkpoints and the six detected mutants. Tests verify source
bytes/ranges and actual consumed checkpoint values, not just artifact existence.

The native patch remains SHA-256
8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac.
Applied tree stays6185197d6f334f745a9c082519013b8fe0376f65; offline synthetic
candidate stays9957868acc7459f515f1b79e9315cf93a878d933. PR19 registration re-verifies
unchanged. Nothing is published to a native branch, source policy or device.

Receipt constructor source/schema/session/context IDs remain clearly synthetic,
as in the existing native fixtures. Source provenance of test inputs is separately
bound in evidence. q_observed is always absent and consumption_manifest_complete
false; these are partial diagnostic receipts, not eligible H7 observations. No
registry/decoder/estimator bridge, actual runtime fingerprint or authority emerges.

## Verification and setup

Core1494 pass; mandatory native184 pass/no skips; new custom58 pass. New harness
coverage124/124 statements and22/22 branches100%/100% — NOT full-native coverage.
Installed-source coverage98.52%; H7 remains843 statements/276 branches100%/100%.
H2–H7/design source/history/coverage audits, lint/format/mypy71 files, build/fresh
wheel70 neutral imports, H7/H6 hash checks, replay11/four digests and knowledge/
owner/science/research/optional-dependency smokes pass. No required check skipped.

The existing source CI job already warms R callback/helper from historical source
audits and discovers the new test module. CI files and old tests are unchanged.
Cloud setup now warms11 exact-R blobs, including the two callback/helper inputs;
tested full install_script gives1494/184 pass. install_script/start_skill saved as
draft only: user review/save and Publish required. No services, network policy,
credentials or repository ref selection changed. No new installed dependencies.

Final independent exact-head review, C/I/M findings, rulings/deferred minors and
hosted push/PR CI are recorded in the new Draft PR, not by rewriting reviewed code.

## Retained gates and next single task

FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
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

All candidate/application/runtime/owner proposal flags false. No real driving
data, Params, real SubMaster/runtime producer, vehicle/device execution, estimator
qualification, candidate generation, application bridge, longitudinal behavior
change, external AI integration, prior-PR modification, merge or upstream PR.

Recommended next SINGLE task: fix PR19 NR-M1 non-ASCII reference-path quoting with
a regression test, offline. It is the remaining known portability defect, not a
runtime or empirical blocker resolution. Not started automatically.
