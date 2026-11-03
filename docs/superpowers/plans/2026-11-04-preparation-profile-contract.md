# Pure preparation-profile contract implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> for native implementation task-by-task. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Build the supplied-values-only DTO/wire/comparator with exact closed
successor integration;never launch or authorize H.

**Architecture:** Four test-only package files,one fixture,five behavior/architecture
test files plus scope test,three registration/doc inputs,exact2scope-consumer
modifications. Runtime package only stdlib json/dataclasses/hashlib/typing and
exact local contracts/wire siblings. No H1/product/application import or I/O.

**Tech Stack:** Existing Python>=3.12.3,<3.13,stdlib,pytest,Ruff,existing coverage;
no new dependency/config/workflow installed or changed.

**Spec:** contract-design.md,registries.json,dto-wire-schema.json,assessment.json,
scope-registration.json and conformance-vectors.json in this frozen artifact pack.
At implementation,adopt the reviewed spec and this plan at their two exact
registered repository docs paths;their hashes/provenance belong in registration.

## Global constraints

- Exactly14new paths and2modified consumers from scope-registration.json,not a
  prefix allowance or permission supplied by a mutable manifest.
- Source base main4b77,old source checkpointdb915,equal treec853. Preserve every
  existing branch/PR(#8/#9 included);new append-only feature work only.
- All9permissions false,BLOCKED,content identity only,no H or collection/producer/
  provider/launcher/ENTRY/application/estimator/owner/vehicle/longitudinal bridge.
- All11exact frozen/slotted DTOs,closed registries,UInt64 integers excludingbool,
  None/0/False/UNBOUNDED distinctions,1MiB wire bound,no floats/duplicates/unknowns.
- Preserve all old tests/thresholds;new package>=98%statement/>=95%branch,no
  exclusions. Hypothetical fixture numbers are not H budgets or safety thresholds.
- Old records/source helpers/guards remain frozen except two named consumers and
  two new closed guard helpers;all old tamper injections remain effective.
- Retain operationalI1/host-config equality UNCONFIRMED and all inherited blockers.

## Review focus

- A false/zero/unbounded known contradiction beside null policy must reject
  (Task3 exhaustive missing-policy cases),not silently become unavailable.
- A forged nested DTO or foreign H1 type cannot bypass exact revalidation
  (Task2 construction/serialization plus Task3 assessment negatives).
- Keyed-table reordering is semantically irrelevant but duplicate/unknown IDs
  must not overwrite another value(Task2 wire and canonical equality tests).
- Frozen repair rows and current raw tamper hooks both remain checked,not a
  wider old allowlist(Task1 and final Task3 source/scope architecture tests).
- A synthetic complete match grants nothing(Task3 all-result-facet checks).

### Task1: separately closed successor and preserved historic/current consumers

**Files:** Create registered spec/plan/registration JSON and
tests/test_preparation_profile_scope.py. Modify only the two named scope consumers;
append only _preparation_profile_changes and _preparation_profile_composed_changes
to the old architecture module. Existing import/global/nonconsumer AST stays exact.

**Interfaces:** `_preparation_profile_changes(rows:list[str])->None` validates
literal14A/2M ceiling via old _phase_changes. `_preparation_profile_composed_changes
(frozen_rows:list[str],new_rows:list[str],current_rows:list[str])->None` verifies
the exact9frozen repair rows,the closed successor and exact A/M status composition.
These test helpers acquire no runtime/producer/application role.

- [ ] RED `test_closed_successor_rejects_unknown_status_alias_duplicate_and_manifest_expansion`:
  accept only literal sets;reject Mproduct/workflow/executor,unknown A,D/R,aliases,
  duplicates and source manifest additions. Run scope tests;missing helper FAIL.
- [ ] Implement helpers with literal registries,not JSON-authorized path sets.
  Freeze209edaa..db915 exact4A5M;assert4b77/db915 tree==c853;new diff4b77..workingtree
  plus untracked rows passes only closed successor. Still read raw209edaa..current
  plus untracked;assert it equals verified status composition(A+M=A,M+M=M,newA=A).
- [ ] Change only old cancellation inventory consumer to use literal enddb915
  without current untracked augmentation. It still invokes the real global
  consumer;keep its same exact old9inventory/oldregistration/assertions.
- [ ] RED->GREEN `test_frozen_new_current_untracked_tampering_all_fail` through the
  real consumer. Keep original existing frozen/current/untracked injections and
  preflight call-tracking assertions unchanged;prove each still fails tampering.
- [ ] Run targeted scope+all existing cancellation/outcome/preflight/architecture
  tests and current full pytest. Expect green,old floors/tests unchanged. During
  construction helper may admit a subset of14new paths;final exact inventory is
  enforced by the Task3 architecture test,not removed or skipped.
- [ ] Commit this bounded successor registration and consumer freeze only.

### Task2: exact immutable values and canonical closed wire

**Files:** Create tests/audit_preparation_profile/{__init__,contracts,wire}.py,
tests/fixtures/preparation_profile.py,tests/test_preparation_profile_values.py,
tests/test_preparation_profile_wire.py. validation.py/assessment tests are Task3.

**Interfaces:** Eleven DTOs/field order from dto-wire-schema.json. Four encoder/
decoder APIs from the spec;policy digest uses SHA256(canonical_policy(policy)),
not a self-containing field. __init__ initially exports only implemented values/
wire functions;Task3 adds assess_profile. No effect at import.

- [ ] RED value tests cover all valid/null/int0/controlFalse/unbounded states,
  exact types,UInt64edges,invalidfloats/bools,foreign/forged children,mutable/list/
  subclass inputs and unknown IDs/units;all fixed facets remain9false.
- [ ] RED wire tests use synthetic spec vectors:policy+record roundtrip,object/
  keyed-table reordering stable canonical digest,kind/version/key/UTF8/BOM/float/
  duplicate/trailing/oversize rejection,UInt64exactness above2**53 and max.
- [ ] Implement minimal closed exact DTO validation/owned normalized tuples and
  registry-driven codec. Non-null valid subsets remain subsets for assessment;
  malformed ambiguous/unknown/duplicate structure raises ValueError.
- [ ] Boundary tests mutate nested frozen instances via object.__setattr__ only
  inside tests;both serialization and decode/assessment later must reject malformed
  graphs. No source/config/environment/kernel probes in fixtures.
- [ ] Run values/wire tests,Ruff/format and pure module import architecture checks.
  Expect green;no future assessment stub is called a completed component.
- [ ] Commit these self-contained supplied-value/wire artifacts only.

### Task3: reasoned comparator,adversarial invariants and full branch verification

**Files:** Create tests/audit_preparation_profile/validation.py,
tests/test_preparation_profile_validation.py,tests/test_preparation_profile_adversarial.py,
tests/test_preparation_profile_architecture.py. Extend only new package fixture/
__init__/tests as needed,not old helpers or behavior tests.

**Interface:** `assess_profile(record:PreparationProfileRecord,
policy:PreparationProfilePolicy|None=None)->PreparationProfileDecision` with
assessment.json traversal/error/subject semantics;no I/O or authority output.

- [ ] RED conformance tests for every error/unavailable code and locator,each
  side,each missing whole table/scalar/DTO and each well-formed contradiction.
  Missing policy never hides recordFalse/0/UNBOUNDED/wrongpin/command/clock/time.
- [ ] Implement known-failure-first traversal and exact per-key policy matching.
  Preserve all independent unknowns beside errors;sort/deduplicate reasons.
  Non-null tables are complete claims;inspect present members despite inventory
  errors. Positive command caps<=known parentcaps;generation0 remains valid.
- [ ] Add RED->GREEN boundary reuse,clockpair,time reversal/UInt64overflow/
  deadline arithmetic and policy digest cases;known timing is absolute instant,
  budgets durations. No real timing/OS clock read to make these tests pass.
- [ ] Add adversarial fixture changes pairing hidden contradiction with unrelated
  nulls;canonical field-order/property checks;strict malformed graphs/foreign types
  at assessment;complete synthetic match fixedBLOCKED/9false/no H on every result.
- [ ] Add fresh subprocess import-only audit guard tests(no writes/socket/process/
  clock/native provider capability),stdlib/sibling imports only,no H1/product/
  application bridge,exact14A2M source inventory and every old nonconsumer/helper
  body/global unchanged atdb915 except two named consumers/two appended helpers.
- [ ] Run full pytest,package statement+branch coverage with zero exclusions
  (>=98/>=95),existing Ruff/format/mypy/build/fresh wheel/replay/source validators.
  Pure component must run Linux/Windows without schema/native-host dependency.
- [ ] Fresh exact-head independent whole-branch review;fix C/I with RED->GREEN
  evidence,full rerun and fresh review. No source code after final clean review.
- [ ] Commit append-only;publish only a new Draft PR if normal exact-pin guards/
  credentials/policy permit,attach it and verify actual-head CI. Never admin/
  squash/rebase/force or touch8/9. Report old blockers/all9false and stop before
  any provider/collector/launcher/H execution or scientific/application inference.

## Self-review

Spec primitives/DTO/wire->Task2;registry/reason/time/coherence->Task3;
phase-ceiling/oldtamper preservation->Task1 and Task3 final architecture.
All5API names/types agree;fourwire functions Task2,assessment Task3. No undefined
runtime provider/collector is needed for this pure implementation. Task1 first
proves legacy/current checks coexist;no acceptance floor is relaxed. The plan
does not require user-invented numeric budgets or privileged infrastructure.
