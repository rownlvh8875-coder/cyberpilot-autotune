# Lossless raw-epoch representation design result

RAW_EPOCH_LOSSLESS_REPRESENTATION_DESIGN_READY
RAW_EPOCH_WIRE_MIGRATION_DESIGN_READY

Design only: UInt64 object→saved scalar→buffer→canonical decimal→exact integer,
explicit unknown distinct from zero, separate future CPRv2 profile and no V1
promotion. The synthetic fixture codec is **not** a full CPRv2 decoder or producer.

Base PR46 `72362dcf235f91cbce30501aeeb72b66ee6c124c`;
branch `design/lossless-raw-epoch`, stacked Draft base
`audit/copy-reference-publication`. Source/fixture digests and full future
acceptance gates are in `docs/epoch_encoding_design.md`. No new kernel/source
type-probe/producer build or guest run; existing regression units may compile
their unchanged stand-in test. Every prior tracked source/test/evidence/workflow
blob, asset and other PR is preserved.

## Verification

Task 1 absent API RED→GREEN: 62 focused PASS, full3771 PASS37.45s.
Task 2 audit API RED observed before implementation; six malformed/mutable
decision constructor cases also RED→GREEN. Final focused78 PASS; full3787
PASS104.86s with installed package coverage98.52%. New pure model53statements/
14branches100/100; whole new package92statements/20branches100/100 after
focused tests plus explicit source-root CLI execution (focused alone93.75%).
These are Python executable-specification coverage figures, not C proofs.

Lint/format612files, mypy71sourcefiles, old source/hash/history/original-asset
audits, new reference source-byte audit, native192/replay4, build and fresh
vanilla/research wheel smoke PASS. The first wheel recipe used an incorrect
smoke-script path; it was corrected to the repository's existing CI recipe
and the whole build/wheel recipe rerun successfully. No product failure hidden.
CRLF fresh checkout462tests plus default audit PASS, clean checkout;
core safety/residual/replay/adapter/knowledge/owner coverage gates and
research/observability100/100 audit gates PASS. Fresh independent exact-head
review and push/PR CI results are recorded in the own Draft handoff after
their actual runs. No design status implies runtime qualification or an
empirical epoch-loss measurement.

## Retained status

RAW_EPOCH_PRODUCER_CORRECTION_NOT_IMPLEMENTED
RAW_EPOCH_RUNTIME_ENCODING_UNQUALIFIED
LOSSLESS_SOURCE_EPOCH_REPRESENTATION_UNQUALIFIED
EPOCH_RANGE_INVARIANT_UNPROVEN
COPY_REFERENCE_RUNTIME_BINDING_UNQUALIFIED
TAG_PUBLICATION_RUNTIME_UNQUALIFIED
QUALIFIED_TAG_READ_RUNTIME_PROTOCOL_NOT_IMPLEMENTED
TAG_READ_LIFETIME_PUBLICATION_RUNTIME_UNQUALIFIED
QUALIFIED_LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN
COPY_CUT_PROOF_UNAVAILABLE
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED
OBSERVER_PERTURBATION_UNQUANTIFIED
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED
NO_PR35_SEMANTIC_ADAPTER
NO_PR30_QUALIFIED_BRIDGE
FRICTION_RUNTIME_PRODUCER_NOT_IMPLEMENTED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED

All nine permissions and qualification proofs false. Actual epoch loss/global
drops remain None. A consistent synthetic scalar chain is not a receipt,
runtime witness, application evidence or permission to execute a producer.
Prior13source obligations remain open.

## Deferred minors (unchanged, not fixed by this design)

- PR46 M1: embedded caller/wrapper/initial-lock citation chain polish.
- PR45 M1: old decoder UInt64/nativeUInt32 bound mismatch.
- PR43 M1: portable paired-root/cohort-routing integration coverage.
- PR42 M1: retained-image automatic verification.
- PR34 M1: HH03 diagnostic FD0 versus actual FD3.
- PR33 M1: fixture ordering.
- PR33 M2: float-equal resource metadata.
- PR33 M3: generic envelope catalog.

## Next single recommendation

**Bounded lossless raw-epoch producer correction implementation**, against a
new exact source/build/wire profile, with actual-declaration type checks and
independent high-bit tests. It must preserve all runtime/lifetime/publication
blockers and old captures; implementing it does not qualify a vehicle or an
estimator. Not started by this design.
