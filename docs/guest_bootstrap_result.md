# Fixed guest FIRST_OBSERVED bootstrap result

BOUNDED_GUEST_FIRST_OBSERVED_BOOTSTRAP_PROTOTYPE_IMPLEMENTED
BOUNDED_BOOTSTRAP_ORIGIN_OBSERVATIONS_CAPTURED

These mean a bounded source prototype and actual fixed-guest observations,not
qualified lifetime history,inventory,estimator/controller or vehicle readiness.
BasePR41 `2d11becc2f5b3b71558db6c944de74ddf18354b3`;branch
`feat/guest-first-observed-bootstrap`. All previous source/tests/evidence/assets,
28earlier Open PRs and main are preserved;no actual→SYNTHETIC/PR41/PR35/PR30 bridge.

## Actual observations

New static driver really booted the preserved PR40 kernel first:missing new proc
interface,CPB_UNAVAILABLEerrno2,4942original bytes;new decoder rejected it. Then
fresh exact6.12.113 source/kernel was built and10fresh1vCPU512MiBTCG guests ran.
No KVM/network/sharedFS/passthrough/vehicle/host probe or guest ELF host execution.

| Fresh case | Attempted | Received | Own-buffer failure | Committed mechanical copies | First-copy links |
|---|---:|---:|---:|---|---:|
| NORMAL |472|472|0|1,2|8|
| SEED_LOSS |472|471|1|1,2|6|
| SMALL_BUFFER |472|128|344|none|0|
| SEED_FAIL |7|7|0|none,noARM/fork|0|
| UNSEEDED_OFD |471|471|0|1,2|7|
| RESEED_REJECTED |473|473|0|1,2|8|
| EARLY_ARM_REJECTED |473|473|0|1,2|8|
| CONSTRUCTOR_FAIL |280|280|0|1|8|
| TASK_FAIL |472|472|0|1|8|
| ALLOC_FAIL |277|277|0|1|8|

Total3524original events;alllocal equations balanced,345deliberate own-buffer
failures remain visible,not global counts. Normal has7FIRST_OBSERVED objects and
5allocation-stage objects,64seed slots,128READ/128STORE/18REFERENCE/110CLEAR_OPEN.
Seed parent1/namespace2 do not become managed root8. Same pre-arm file atFD5/40
carries tag6;independent equal-data FD6 tag7. Post-arm OFD10 has allocation origin.
These are frame-local observations,not full birth/destruction history.

Lost NODE6 is not reconstructed from later tag6;links atFD5/40 are omitted despite
complete copy mechanics. Unknown FD6 stays PRESENT/None/UNAVAILABLE in both copy
reads;root ID shifts7 without fabricated tag7 for that file. Partial seed abort
keeps only partial diagnostics and no fork. Duplicate seed/early arm were actually
rejected with driver-checked EBUSY/EINVAL. Constructor/late-task/preallocator
injections take actual cleanup paths but do not measure natural failure rates.

## Artifacts and verification

New test-only tests/guest_bootstrap package:immutable contracts,closed CPBv1 wire,
pure diagnostic,memory image builder,opt-in frozen runner,static driver,complete
ten-file standalone patch/config,offline source/original-byte audit. New build/
actual/source manifests under docs/evidence/guest_bootstrap_*.json.
Source7pristine/10patched files45ranges,file/blob/range hashes.

Kernel SHA256 `41ff311f04db5a8d4509fd20f45f293f89c5ea854758bf72d653c8a767cc0ace`;
init `5a7798a78d22869d87cfe8a583ce092d3d90cdf1d9bd4f83839120828839fc08`;
actualconfig `10d1aa082c6dbc91d9db2e275d0ab92cbe90aad66aef95b40b95496a29549151`.
Prepared assets remain `/workspace/scratch/guest-bootstrap-producer.O8Npmg`,outside
the recoverably archived author plan workspace. Prior producer assets unchanged.

Offline `python -m tests.guest_bootstrap.audit`;optional explicit both source roots
and --verify-assets check prepared bytes,not execution qualification. Guest boot
requires explicit `python -m tests.guest_bootstrap.runner --execute-fixed NORMAL`
or one of ten fixed enum cases. Ordinary tests/audits/import do not boot/build.

Codec/runner missingAPI39+8RED→GREEN;additional context/copy-ID/role loss guards
8RED→GREEN before actualcapture. Audit21missingAPIRED→GREEN plus frozen nonce
characterization;focused verification and full regressions/review/exactheadCI
are recorded in the own Draft PR handoff. Fresh independent review at28db46d found
C0/I1/M1. I1:contradictory observed control ordering could retain seed links. One
author RED→GREEN pass added13cases,checks observed one-shot relations and preserves
missing-control availability. No second review or independent final-head approval
is claimed. All four pure modules total359statements100branches100/100;no runtime/
source C coverage or qualification inferred from Python coverage.
Post-fix focused97/full3382tests pass;ten fresh guest captures match pre-hook
literal event signatures. Source/assets/native192/replay4/build/fresh-wheel checks
pass. Exact-head CRLF/remote CI completion is recorded in the Draft PR handoff.

Deferred new M1:--verify-assets verifies prepared inputs/tools,not retained final
capture images. Reviewer separately checked all10retained images;runner regenerates
them from verified init/case rather than consuming the retained outputs. Automatic
retained-output image verification is deferred,not advertised as implemented.

## Retained blockers / next single task

QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED;
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED;LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN;
COPY_CUT_PROOF_UNAVAILABLE;LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED;
OBSERVER_PERTURBATION_UNQUANTIFIED;CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED;
NO_PR35_SEMANTIC_ADAPTER;NO_PR30_QUALIFIED_BRIDGE.
FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED;FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED;
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE;
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE;
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED;RUNTIME_FINGERPRINT_UNCONFIRMED;
WATCHDOG_EXECUTION_MODEL_UNRESOLVED;EXTERNAL_EXECUTOR_UNQUALIFIED;
APPLICATION_NOT_AUTHORIZED. All9false,history/atomic/runtimefalse,globalcountsNone.

Next single recommendation:**bounded bootstrap tag initialization/reuse boundary
audit**. Actual first-observation continuity is now visible,but selected allocation
routes and issuer guards are not complete memory/reuse/publication proofs. Audit
those boundaries before any inventory/PR35/PR30 or runtime admission. This does not
authorize general host probes,device execution,merges or vehicle/application use.

Prior4deferredminors unchanged:PR34M1HH03diagnosticFD0/actualFD3;PR33M1fixtureordering,
M2float-equalresourcemetadata,M3genericenvelopecatalog.
