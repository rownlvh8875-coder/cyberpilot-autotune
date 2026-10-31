# Fixed guest per-slot fork-copy result

BOUNDED_GUEST_PER_SLOT_FORK_COPY_PROTOTYPE_IMPLEMENTED
BOUNDED_GUEST_PER_SLOT_COPY_OBSERVATIONS_CAPTURED

These mean a bounded source prototype and six actual disposable-guest observations,
not a qualified observer, inventory backend, controller receipt or vehicle readiness.
Base PR39 `4a04a5a38a68970624380c10113c97a752af4aa8`; branch
`feat/guest-per-slot-fork-copy`. Prior runtime/tests/evidence/PRs and main unchanged.

## Actual observations

Before new hooks, the new driver really booted the preserved PR38 kernel:
`CPC_UNAVAILABLE errno=2`,4943 original serial bytes; new decoder rejects it.
Then a fresh exact6.12.113 source extract/build and static driver were used.
No host kernel/package/security modification or guest ELF execution on host.

| Fresh guest | Attempted | Received | Own copy-buffer failure | Complete committed mechanical copies |
|---|---:|---:|---:|---|
| NORMAL |392|392|0|1,2|
| READ_LOSS |392|391|1|1|
| SMALL_BUFFER |392|128|264|none|
| CONSTRUCTOR_FAIL |200|200|0|1|
| TASK_FAIL |392|392|0|1|
| ALLOC_FAIL |198|198|0|1|

Total1,701 original copy records. Every local equation balanced, but deliberate
loss remains visible. Normal has2BEGIN/2BITMAPS/128READ/12REFERENCE/116CLEAR_OPEN/
128STORE/2COPY_RETURN/2TASK_FINALIZE. Normal copy2 actually inherits source-table
cookie2 and constructor5. Unknown parent identity and inherited OFDs stay unknown:
identity_complete=false for every case. No synthetic-oracle admission.

READ_LOSS loses real copy2local18; SMALL_BUFFER fails264 local reservations.
Constructor injection frees real partial allocation and emits no successful
TABLE_NEW for it; late task failure records copied slots but aborted child;
preallocation failure has no destination cookie/BEGIN. Fault injections change
operation results, not natural failure frequencies. Separate lifecycle counts
18/18/18/13/15/13 have no observed own-buffer failure; they are not CPC/global counts.

## Reproduction and evidence

- Test-only contract: `tests/guest_fork_copy/{model,image,runner,audit}.py`.
- Standalone ten-file source patch/config/static-driver source in that directory.
- `docs/evidence/guest_fork_copy_{build,actual,sources}.json` binds original serial,
  images/build/tools/source inputs and57ranges across7pristine/10patched files.
- Prepared kernel SHA256 `f2a8dce470fb64e42a47294cc46594b3054d36725dd0f50f92b2510d3aa559a7`;
  static init `a853c2c4de7c062d677d8f9b8584c1a42134c317c4cd0f0f2d2183270b3f9c38`;
  actual config `bf7279ed344ced3caa4520fe7f8b6f0ad9a9a4ad632602d16fd9afb108f0c6a7`.
- Assets `/workspace/scratch/guest-copy-producer.IGDFFC` are retained separately
  from the recoverably archived author plan workspace. Earlier assets untouched.
- Offline: `python -m tests.guest_fork_copy.audit`; explicit prepared source roots
  and `--verify-assets` are optional stronger byte checks, never a runtime verdict.
- Only `python -m tests.guest_fork_copy.runner --execute-fixed NORMAL` (or another
  one of six enum cases) boots the frozen guest. No arbitrary payload/input.

Verification results, exact-head review/CI and publication metadata are recorded
in the own Draft PR handoff. Pure codec coverage is100%statements and97.92%branches
(47/48); no impossible-success branch is artificially exercised for100%.

Fresh independent review at41614f7 reported C0/I2/M0: terminal reason contradictions
and capture-wide scope/cookie roles. One author fix pass reproduced5failing
adversaries (plus1already-rejected regression), then36codec tests passed. All six
actual guests were recaptured with the final pinned codec/runner; the kernel,
driver, images and source-range pins did not change. Pre-review captures are
retained separately, not overwritten/labeled as reviewed final evidence. Final
head is the append-only fix commit; no second review or runtime approval claimed.

## Retained limits and next single task

QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED;
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED; LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN;
COPY_CUT_PROOF_UNAVAILABLE; LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED;
OBSERVER_PERTURBATION_UNQUANTIFIED; CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED;
NO_PR35_SEMANTIC_ADAPTER; NO_PR30_QUALIFIED_BRIDGE.

FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED;
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED;
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE;
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE;
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED; RUNTIME_FINGERPRINT_UNCONFIRMED;
WATCHDOG_EXECUTION_MODEL_UNRESOLVED; EXTERNAL_EXECUTOR_UNQUALIFIED;
APPLICATION_NOT_AUTHORIZED. All9permissions false, global counts unavailable.

Next single task: **bounded inherited-OFD identity provenance design**. Actual copy
stages are now visible but inherited pre-arm OFDs/root parent remain unidentified;
design exact birth/lineage obligations and explicit unavailable cases before any
inventory bridge. This is not authorization to implement a general observer,
host probe, device runtime qualification or vehicle/application execution.

Four earlier deferred minors remain: PR34M1 HH03 diagnosticFD0 vs actualFD3;
PR33M1 fixture ordering, M2 float-equal resource metadata, M3 generic envelope catalog.
