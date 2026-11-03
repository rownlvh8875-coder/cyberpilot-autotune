# Registered preflight diagnostic mapping implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> task-by-task. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Build one pure supplied-bytes diagnostic mapper,never a target H receipt.

**Architecture:** Three test-only package files;one synthetic fixture;three test
files;registration/spec/plan;exact10A2M successor. No runtime/product dependency.

**Tech Stack:** Existing Python>=3.12.3,<3.13,stdlib,pytest/Ruff/mypy/coverage;
no new dependency/config/workflow. Existing proxy/credentials untouched.

**Spec:** mapping-design.md,mapping-contract.json,mapping-matrix.json,
scope-proposal.json and acceptance.json in this exact reviewed artifact pack.
Adopt at the two exact repository docs paths from scope-proposal.json;registration
embeds this contract/catalog/synthetic S0 fixture and their reviewed manifest hash.

## Global constraints

- Source0ac6e3519ad7191b036eb777b4317174121851bb/tree974837bb773c5e18b90f01e9ce7491769a3d4b2a.
- Existing PR60/8/9/main remain unchanged. Future branch stacks from exact0ac6,
  Draft base feat/preparation-profile-receipt;do not merge/retarget the old PR.
- Only10new paths and2old named consumer functions. No old helper/function/top-level
  changes otherwise. New guard helpers stay in new scope-test module only.
- Five frozen/slotted DTOs and one pure API from mapping-contract.json. Exact
 83diagnostics/132gaps;profile_record=None;all9permissionsfalse;DIAGNOSTIC_ONLY always.
- Explicit default R0 or explicit synthetic S0,never automatic fallback/new profile
  from caller context. Raw source bytes/hash are not authenticity or execution.
- Use only fictitious S0 in public CI fixtures. No real R0 raw blob/UID/GID/log or
  new capture/network/native probe required for CI. Real retained R0 local audit
  is distinct evidence,not a CI skip or an inferred executed mapper result.
- Statement>=98%/branch>=95%,zero exclusions;all old floors/tests preserved.
- No collector/provider/launcher/clock/file/network/H1/prep/application/owner bridge.

## Review focus

- R0 input failure must not fall back to matching S0(Task2 default-profile case).
- Source knownFalse/0/pin mismatch must survive missing binding and other nulls
  (Task2 partial-context/semantic negative table),without filling H controls.
- Missing cgroup parent must not be filled withFalse/zero/nested source facts
  (Task2 nullable branch tests),and source byte mismatch remains explicit.
- Existing raw4b77/current209/untracked hooks must remain live after freezing old
  profile inventory(Task1 inherited/new tamper cases and Task3 exact preservation).
- Output must not contain raw source/UID/GID and must never instantiate/import H
  receipt types;unexpected strings use tagged available redaction,not raw echo or
  unknown(Task2 PM-033/034 and Task3 constructor/forged output/import guard).

### Task1: separately closed successor and frozen profile consumer

**Files:** Create registration,spec,plan,tests/test_preflight_profile_mapping_scope.py.
Modify only named functions in scope-proposal.json (global history consumer and
profile final inventory). No appended helpers or imports/globals in old modules.

**Interfaces:** New scope test module defines
`assert_mapping_scope(rows:list[str])->None` for literal10A2M and
`assert_mapping_composition(frozen_repair:list[str],frozen_profile:list[str],
new_rows:list[str],profile_current:list[str],all_current:list[str])->None`.
Both are test helpers,not runtime/producer capabilities. Importing this test
module has no calls into old consumers;test functions use local imports later.

- [ ] RED accept full literal scope,construction subset;reject unknown/aliases/
  duplicates/statusD/R,old product/executor/workflow edits and manifest expansion.
  Expected:FAIL missing new guards,not collection/import typo.
- [ ] Freeze209edaa..db9159rows and4b77..0ac6old14A2M,assert exact literal sets;
  unchanged old helpers validate them. Retain all earlier tree/range checks.
- [ ] Global consumer still reads raw4b77..current/raw209edaa..current and untracked
  plus separately new0ac6..current. New helpers compare exact composed statuses,
  rejecting missing,extra,duplicate,renamed/aliased rows. OldA+M remainsA.
- [ ] Profile inventory consumer reads4b77..0ac6 (notcurrent/untracked);retains
  every original inventory/registration assertion and calls real global consumer
  via function-local import. Existing nonconsumer source/top-level AST unchanged.
- [ ] Run all old profile/cancellation/outcome/preflight/history tests,new frozen/
  current/new/untracked/tree tamper cases and full pytest. Expected:all green.
- [ ] Commit only this bounded successor registration and tests.

### Task2: immutable diagnostics and strict source mapping

**Files:** Create tests/audit_preflight_profile_mapping/{__init__,contracts,mapping}.py,
tests/fixtures/preflight_profile_mapping.py,tests/test_preflight_profile_mapping.py.

**Interfaces:** Exact five DTO fields and
`map_registered_preflight(raw:bytes,binding:PreflightRunBinding|None=None,
*,source_profile_id:str='REGISTERED_PREFLIGHT_R0')->PreflightMappingDecision`.
Pure package imports only dataclasses/hashlib/json/re/typing and exact siblings.
Registration contains exact R0/S0 profile constants and synthetic UTF8 byte fixture;
fixture reads registration outside pure package. No observed R0 raw blob is added.

- [ ] RED S0 complete matching supplied binding ->REGISTERED_SNAPSHOT_MATCH,
  source_profile/evidence_kind synthetic,83owneddiagnostics/132gaps,allfalse/None facets.
- [ ] RED every acceptance.json case with exact listed source/binding changes,
  required error/unavailable codes and source value preservation. Structural
  malformed/unknown fields/schema/profile raiseValueError,not fabricated nulls.
- [ ] Implement exact tuple/graph/field validation,source grammar and declared
  constant relations from mapping-contract.json. None/False/0/empty/max distinct.
  Revalidate nested forged/foreign inputs at public pure boundary.
- [ ] Validate rawcontent SHA including newline vs explicitly selected profile;
  compare all supplied8binding facts and available caller context independently.
  Known contradictions outrank missing binding;collect both sorted/deduplicated.
- [ ] Emit only exact83RFC6901pointers,with parent-null children unavailable;never
  include22UID/GIDleaves/rawblob or mint a H identity. After original comparisons,
  map unregistered strings through closed40pointer vocabularies to the fixed
  SOURCE_TEXT_REDACTED/AVAILABLE marker. Explicit marker exception applies to
  output hex/control grammars only;constructors/forged graphs cannot bypass it.
  PM-033 canary must not appear anywhere in returned decision;PM-034 CapEff marker
  must be a valid tagged output despite not being hex. Return exact132static gaps,
  no H receipt import/construction/no policy or budget synthesis.
- [ ] Run value/mapping cases,Ruff/format/strictmypy. Expected:green. Canonical S0
  hash must equal5d813832979c34b7efc5c15c5312d83c266a14ce63144e3f4bb9fe9ca027040d.
- [ ] Commit only new neutral implementation/tests.

### Task3: architecture,adversarial scope and whole-branch verification

**Files:** Create tests/test_preflight_profile_mapping_architecture.py;extend only
new scope/behavior tests and owned fixture/package as needed. No other old edits.

- [ ] RED->GREEN audit fresh subprocess import/calls with writes/socket/process/
  thread/clock/caller-source execution forbidden. Do not import old H1/prep/product/
  application/collector. Assert no profile_record/capability and no raw/identity
  field or unregistered-text echo for every decision/profile. This is not a
  universal DLP/covert-channel/process-security guarantee. No input logging.
- [ ] Assert exact final10A2M,all old nonconsumer bytes and top-level AST at0ac6,
  old helper names/bodies unchanged,all old/new tamper injections and parser strict
  duplicate/nonfinite/field/type/overflow/source-profile-spoof cases exercised.
- [ ] Full pytest,coverage>=98statement/>=95branch(no exclusions),old floors,Ruff/
  format/strictmypy,audits/history/replay/build/freshwheel smoke. Expected:green;
  development/synthetic evidence only,not genuine source/host/H qualification.
- [ ] Optional separate local retained-R0 supplied-byte check uses externally
  provided saved source/binding,never downloads or reads host state from the pure
  package. Report only if actually run;not a substituted CI test or a skip.
- [ ] Commit;fresh exact-head whole-branch independent review. Address C/I via
  RED->GREEN/fullrerun and exact-head review according to project requirements.
- [ ] Publish only a NEW DraftPR on the declared stack if base/head/credentials
  still match;no merge/force/admin/rebase/squash or oldPRchanges. Verify actual
  push/PR CI and recordall9false/status/blockers. Stop before new producer/H.

## Self-review

Scope/reviewhooks->Task1+3;DTO/source grammar/selected profile/binding/unknown/error
rules->Task2;privacy/no capability/complete catalogs->Task2+3. Interfaces use the
same five DTOs/one API as spec. S0 is explicitly fictional,no raw real-source data
release or new workflow is needed for CI. No threshold or acceptance relaxation.
