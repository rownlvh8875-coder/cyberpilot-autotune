# Managed-root fork-copy evidence — design result

Base PR38 `420538d7c20edcfca3eadf136b30b622ca2bede9`.
Branch `design/managed-root-fork-copy-evidence`;append-only own stacked Draft.

## Delivered,not implemented

[Per-slot contract](fork_copy_evidence_contract.md),
[preferred future capture architecture](fork_copy_capture_design.md),
closed neutral semantic schema,exact source references,18synthetic cases,pure
test-only evaluator and offline source/case auditor. No C/API/kernel modifications,
build/boot/producer/collector,actual copy records or inventory adapter this turn.
Existing PR38/37 source/binaries/captures and all earlier runtime remain unchanged.

Source: exact PR38 patched Debian Linux6.12.113;3pristine/4patched files/36ranges,
whole-file SHA256/Git blob SHA1/range SHA256,archive/package and base provenance.
Both source-root optional byte checks passed separately. No compiled/running
kernel equivalence,fresh distribution signatures or complete build closure claimed.

## Decisions

- Capture consumed READ→existing REFERENCE or CLEAR_OPEN→actual STORE per FD.
  Do not reconstruct from a later inventory,expected fixture,TABLE_NEW or task commit.
- The selected empty source still scans64FDs;64 is not the open-FD count.
- NULL vs PRESENT-with-unknown-cookie vs unavailable read remain distinct.
  Clearing child open/full bits does not clear copied raw CLOEXEC. NULL has no
  effective binding flag,even when that raw bitmap bit istrue.
- Source file_lock/private-copy result do not prove absence of in-flight lockless
  installations or hidden source sharers.6abstract schedules include1without even
  a matching source presence state;the other5 do not prove a cut.
- Future explicit copy context passed from copy_files into the selected dup_fd
  walk is preferred. Current constructor cookie is issued after the walk;future
  allocation-cookie linkage/abort/failure capture must be deliberately redesigned.
-196proposed records per successful64-slot copy exceed existing128capacity. Two
  proposals plus18separate CPS records imply410before extra metadata,not an actual
  observed count,safety threshold or transport qualification. No buffer change.

`Decision.consistent` means only checked synthetic premises.145statement/36branch
coverage does not turn assumptions into source attestation. Every decision retains
status BLOCKED,atomic_cut_proven=False,runtime_producer_implemented=False,all9
permissions false and actual copy/global loss/prohibited counts unavailable.

## Verification checkpoint

- Baseline3085passed36.18s;initial full3152passed35.93s;hardened full3155passed35.91s.
-48missing-contract tests RED→GREEN,unknown-open-bitmap RED before implementation;
  wrong structurally valid branch stage KeyError RED→reasoned rejection GREEN.
-13missing-audit tests RED→GREEN;18catalog cases/3consistent synthetic premises;
  source/schema/catalog tampering,unknowns/loss/stage/type/identity/no-authority cases.
- Pre-review author hardening:2root-scope cookie role collision variants and
  STORE boolTrue impersonating integer1,all3RED→GREEN. Root task role remains
  explicit even when current creator differs;STORE identity is type-validated
  independently of equality. Source implementation binding refreshed;cases/schema
  unchanged. No silent previous-phase fix.
-70focused tests including2architecture guards;pure evaluator145/145statements,
  36/36branches100/100%,no exclusions. This is Python,not kernel or observer coverage.
- Ruff/format,mypy71installed+3new modules pass. Prior H2..H7/source/history,
  observation-v2/guest/PR35/36/37/38 audits and192passive native cases pass.
- Python sdist/wheel build;fresh vanilla/research wheel outside checkout imports,
  replay,Carrot/knowledge/owner/science/H6/H7 smokes pass. tests/compatibility/NumPy
  absent before explicit research extra. New design is not installed runtime code.
- CRLF,final exact-head review and push/PR CI are recorded in the own PR handoff
  only after observed;never inferred from these earlier verification checkpoints.

Offline: `python -m tests.fork_copy_design.audit`. Optional sources:
`--kernel-source <PR38-patched-root> --pristine-source <pristine-root>`.
Default source-byte flags false,never VM execution. New kernel/probe/device or
actual per-slot copy execution was not performed and must not be inferred.

## Status and preserved blockers

FORK_COPY_EVIDENCE_CONTRACT_DESIGN_READY.
FORK_COPY_CAPTURE_ARCHITECTURE_DESIGN_READY.
FORK_COPY_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FORK_COPY_RUNTIME_EVIDENCE_UNAVAILABLE.
QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN.
COPY_CUT_PROOF_UNAVAILABLE.
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED.
OBSERVER_PERTURBATION_UNQUANTIFIED.
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED.
NO_PR35_SEMANTIC_ADAPTER / NO_PR30_QUALIFIED_BRIDGE.

FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED.
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED.
RUNTIME_FINGERPRINT_UNCONFIRMED.
WATCHDOG_EXECUTION_MODEL_UNRESOLVED.
EXTERNAL_EXECUTOR_UNQUALIFIED.
APPLICATION_NOT_AUTHORIZED.

No previous src/compatibility/CI/tests/evidence/PR changes. No vehicle/Params/cereal/
controller/torqued/estimator/candidate/owner/application bridge,longitudinal,external
AI or upstream PR. Prior PR34M1 and PR33M1/M2/M3 remain deferred unchanged.

## Next single task

**Fixed disposable-guest per-slot fork-copy prototype**: implement the selected
explicit-context capture narrowly,including constructor-cookie linkage,actual
read/ref/clear/store records,task failure/loss paths and a derived bounded buffer
budget. Keep all qualification/adapter/application permissions false. This design
does not automatically start that task or authorize host/vehicle execution.
