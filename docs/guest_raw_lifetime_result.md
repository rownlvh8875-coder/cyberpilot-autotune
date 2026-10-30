# Disposable-guest raw FD lifecycle source prototype — result

Base PR36 `57b2c942d38f26343bb73fa8cf0f813c58f920a5`.
Branch `feat/guest-raw-lifetime-prototype`; append-only, own stacked Draft only.

## Actual implementation and observations

[Contract/limits](guest_raw_lifetime_contract.md), exact7-file guest kernel patch,
fixed static PID1 driver, opt-in frozen-input TCG runner, pure offline parser/
diagnostic and byte-bound build/source/original-serial evidence. No src runtime,
compatibility/CI/old evidence/audits/fixtures/experiments changes or prior PR edits.

Built exact preserved Debian Linux6.12.113 source with GCC14.2.0-19/binutils2.44;
owned-prefix flex/bison/m4/bc/libelf headers, no host package/policy/kernel changes.
sqv freshly verified3 signatures on preserved InRelease, Packages SHA256 matched
its signed Release entry, downloaded dependency package hashes matched that index.
This does not establish current repository freshness or complete build-input closure.

Pristine-source kernel actually booted the fixed driver and failed with errno2 at
missing /proc/cplife (RED). Patched-source guest then supplied raw events (GREEN).
Baseline release `6.12.113-cplife-v1+`; patched release `6.12.113-cplife-v1` uses
explicit empty LOCALVERSION to suppress automatic Git suffix. Releases are labels,
not source/binary identities; both kernels and source/config/patch are separately bound.

Final frozen runner produced three fresh one-CPU512MiB software guests, no KVM,
network, shared folder, passthrough/vehicle or arbitrary workload:

| Actual fixed case | Own-buffer attempted | Raw records received | Own-buffer reservation failures |
|---|---:|---:|---:|
| NORMAL |12|12|0|
| FORCED_LOSS |12|11|1|
| SMALL_BUFFER |12|2|10|

All three local accounting equations balanced; failure cases remain explicitly
lossy. CLI success means the bounded diagnostic ran with balanced local accounting,
not that a capture is lossless, qualified or authorized.25 original raw records
are retained with complete serial bytes and image/source/build digests.

Normal raw sequence: initialized file1 → installFD5 → dup3 writeFD40 → CLOEXEC
flag → occupied dup3 writeFD40 → actual new namespace2 → child closes → namespace
post-free → parent closes → file post-free. Root namespace and task lifetime identity
remain **unavailable**. REPLACE names the source dup-write path, not proof of an
occupied destination; unknown old cookie is not an absence witness.

Kernel `patched-bzImage`:1360896 bytes,
SHA256 `5f4b2a28b6374c1f5b841ad33e30b61957672c04d69f962d3df96d2fb748e7ff`.
Static driver:779416 bytes,
SHA256 `032053b561af85a6a5f3b02bdf7eea6d2825289a1ba8f20aded85bf0ac142001`.
Prepared assets remain at `/workspace/scratch/raw-lifetime-producer.mfFU7h`;
compiled binaries are not committed. New manifests hold original serial and all
recorded source/config/tool/package/kernel/driver/image identities and commands.

## Validation

- Baseline2950/35.43s; pre-final-doc full3011 passed35.73s.61 focused including
  actual-byte/adversarial replay and two architecture guards.
- Pure model/image105/105 statements,14/14 branches100/100%, no exclusions.
  This is Python coverage, not kernel coverage or a lifetime correctness proof.
- Actual pristine missing-interface RED; actual three-case source prototype GREEN.
- Large fabricated count memory expansion RED→GREEN; FD/flags width2 RED→GREEN;
  runner and byte-audit missing APIs RED→GREEN.
- Pristine5/patched7 source files,22 ranges verified; explicit prepared-asset check
  verifies recorded compiler/tools/source/package/config/kernel/driver bytes and
  unchanged prepared QEMU cohort. Default offline audit reports assets/kernel source
  bytes unverified when absent, rather than claiming a successful runtime check.
- Ruff/format, mypy71 installed+5 prototype modules, sdist/wheel build pass.
- Prior H2..H7/history/source/observation-v2/guest/PR35/PR36 audits pass; passive
  native compatibility192/3.99s. No Carrot/device execution.
- Fresh wheel, final exact-head/CRLF runs, independent review and remote CI are
  recorded after observation in the own PR handoff, never inferred from old heads.

Offline only: `python -m tests.guest_raw_lifetime.audit`.
Explicit prepared-asset guest only:
`python -m tests.guest_raw_lifetime.runner --execute-fixed NORMAL`.
No ordinary test/audit/import boots QEMU. The fixed runner rejects unavailable or
changed inputs before its process launch; no host-ELF or alternate-kernel fallback.

## Limits and retained blockers

BOUNDED_GUEST_RAW_LIFECYCLE_PROTOTYPE_IMPLEMENTED.
BOUNDED_GUEST_RAW_LIFECYCLE_OBSERVATIONS_CAPTURED.
QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN.
COPY_CUT_PROOF_UNAVAILABLE.
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED.
OBSERVER_PERTURBATION_UNQUANTIFIED.
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED.
NO_PR35_SEMANTIC_ADAPTER.
NO_PR30_QUALIFIED_BRIDGE.

The prior “runtime producer not implemented” blocker is not silently erased: a
bounded diagnostic now exists, but no **qualified/full-profile** producer exists.
FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED remains unchanged: this is FD telemetry,
not controller friction observability. FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED,
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE,
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE,
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED, RUNTIME_FINGERPRINT_UNCONFIRMED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED, EXTERNAL_EXECUTOR_UNQUALIFIED,
APPLICATION_NOT_AUTHORIZED all remain.

Own-buffer failure0 does not mean global drop0. Pre-arm/boot/static/other constructors,
hidden owners/paths, NMI, copy cuts, actual source closure, later deferred cleanup,
authenticated boot/freshness, arbitrary CPU contexts and general transport remain
unqualified. Do not pool cookies across captures: parser alone has no authenticated
boot identity. Source/emission order is not effect linearization. Metadata digest
means content identity only. Cookie fields/extra instructions/layout perturb execution;
the prototype is not transparent, hostile-host sealed, a watchdog or a generic runner.

All9 operational permissions false; actual global loss/prohibited-operation counts
None. No estimator/candidate/owner/application bridge, Params/controller/cereal,
longitudinal, external AI, upstream PR or vehicle. Prior deferred PR34M1 and
PR33M1/M2/M3 unchanged.

## Next single task

**Managed-root creation-time scope provenance extension**: observe source-issued
task/root namespace birth from before managed-root creation rather than borrowing
PID1's pre-existing unknown namespace. Keep hidden-owner/source closure and all
downstream qualification separately blocked. Do not automatically start it here.
