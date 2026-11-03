# H1 Pure Historical Record Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a development-only pure consistency gate for supplied H1 records,not a historical executor or H admission bridge.

**Architecture:** Immutable exact-type DTOs and closed canonical wire encoding in a new sibling namespace;pure policy comparison with known-error-over-missing precedence. Existing core/C1 remain untouched. Even a complete supplied record can only be STRUCTURAL_RECORD_MATCH,BLOCKED,all9false.

**Tech Stack:** Python>=3.12.3,<3.13,stdlib,pytest,Ruff,strict mypy;no new runtime dependency.

**Spec:** docs/superpowers/specs/2026-11-02-entry-historical-replay-design.md and historical-design-v1/{semantics,sources,acceptance,case_inventory}.json. This plan is not started by its design commit.

## Global Constraints

- ADD ONLY the eight literal paths below. No old file/config/manifest/guard/CI edit.
- Status BLOCKED,all9permissions false,integrated_admission=false,source_capture_atomicity=NOT_ESTABLISHED,HISTORICAL_REPLAY unavailable.
- No filesystem/process/network/clock/Git/runtime/application/owner/estimator dependency in the pure package or first import.
- No historical O/D collection or execution,runner,CLI,snapshot setup or H-to-C1/core bridge.
- DTO fields/signatures from spec section8;run_id32lowercase hex;SHA25664hex;source IDs40hex;bool not integer.
- None is unavailable,not empty/zero/false. Revalidate nested values;known contradictions outrank unavailable peers.
- Record wire schema historical-replay-record-v1,canonical sorted UTF8 JSON;duplicate/unknown keys and nonfinite values reject.
- Coverage counts nonnegative exact ints;exact group/module sets;each group independently statement>=98%,branch>=95%.
- Existing2121tests and all90/95/98coverage floors preserved;new package statement>=98%,branch>=95%,target100/100.
- Local append-only work in an isolated branch;no push/PR/merge/rebase/force-push or prior branch mutation.
- Original40HR cases stay PLANNED until individually executed. This slice covers HR-001–026 only;HR-027–040 require separately scoped I/O.

## Review Focus

- Producer omits errors but supplies wrong origin/nonzero exit/failed node:derive rejection,not trust its lists (Task2).
- Correct test count with one substituted or repeated node:reject exact set,not count (Task2).
- Good coverage group hides bad peer or counts refer to an old run/artifact:reject independently (Task2).
- Forged nested dataclass or mutable alias bypasses validation after construction:revalidate before assessment/digest (Task1).
- Matching record is presented as real historical/ENTRY/application proof:fixed blocked outputs and no bridge/import capability (Task3).

## File map

1. tests/audit_compatibility_history/__init__.py — inert exports/docstring.
2. tests/audit_compatibility_history/contracts.py — frozen records,canonical encoding/strict record decoder,content digests.
3. tests/audit_compatibility_history/validation.py — pure assessment and reasoned decision.
4. tests/fixtures/audit_compatibility_history.py — explicit TEST_ONLY supplied policies/records,not execution witnesses.
5. tests/test_audit_compatibility_history_values.py — type/wire/immutability/digest cases.
6. tests/test_audit_compatibility_history_validation.py — exact policy/cohort/command/node/origin/coverage cases.
7. tests/test_audit_compatibility_history_adversarial.py — missing+invalid,forged nested values,run substitution cases.
8. tests/test_audit_compatibility_history_architecture.py — inert import,no capabilities,no bridge,old byte preservation.

No runner.py,subprocess adapter or product src file is created.

### Task 1: Immutable supplied records and canonical wire

**Files:**Create paths1,2,4,5 from the literal map.

**Interfaces:**
- Consumes:spec section8 record fields and unchanged core PERMISSIONS values.
- Produces:SourcePin,OriginPin,CoverageCounts,CaseOutcome,HistoricalCommandPolicy,HistoricalCommandRecord,HistoricalReplayPolicy,HistoricalReplayRecord,HistoricalReplayDecision.
- Produces:canonical_record(record:HistoricalReplayRecord)->bytes;decode_record(raw:bytes)->HistoricalReplayRecord;content_digest properties over canonical bytes.

- [ ] Write lazy-import RED tests for namespace absence,all9false,all fixed blocked outputs,None!=0/false/empty,exact-type/nonfinite/unsafe paths,defensive nested ownership. Fixture declarations are visibly TEST_ONLY,never a real process result.
- [ ] Run `python -m pytest -q tests/test_audit_compatibility_history_values.py`. Expected:fail because namespace/interfaces are absent,not malformed fixture setup.
- [ ] Implement only exact frozen DTO validation and closed canonical record encoder/decoder. Invalid construction/wire raises ValueError;do not silently coerce or normalize identities.
- [ ] Add RED→GREEN tests for duplicate/unknown JSON keys,NaN/Inf,bool-int confusion,field-order canonicalization,changed source/command/run digest,object.__setattr__ nested tampering and round-trip exact types (HR-013–018,024).
- [ ] Run values tests,Ruff and strict mypy on new package. Expected:green with no allowed-import expansion. Run the whole suite;commit only this literal subset.

### Task 2: Pure policy consistency assessment

**Files:**Create paths3,6,7;extend only new paths2,4 as needed.

**Interfaces:**
- Consumes:Task1 DTOs,strict field semantics,and separately supplied HistoricalReplayPolicy|None.
- Produces:assess_record(record:HistoricalReplayRecord,policy:HistoricalReplayPolicy|None)->HistoricalReplayDecision.
- Derived consistency:REJECTED if any known contradiction,else UNAVAILABLE if missing required facts,else STRUCTURAL_RECORD_MATCH. None of these clears project H blockers.

- [ ] Create RED tests for valid complete synthetic supplied record,missing policy/O inventory,wrong profile/cohort/H6 origin,mandatory command missing,wrong/duplicate command ID and source. Cover HR-001–009,019,020,022,023 with parameterization.
- [ ] Run `python -m pytest -q tests/test_audit_compatibility_history_validation.py tests/test_audit_compatibility_history_adversarial.py`. Expected:missing assessor assertion failures.
- [ ] Implement independent derivation from source/argv/exit/origin/node/coverage facts. Do not trust producer errors;inspect available peers before returning unavailable. No I/O or real module-origin lookup.
- [ ] RED→GREEN tests:remove one original476node;replace a node at identical count;mislabel56AR scenarios as476;skip/xfail/xpass/deselect;omit setup/teardown;nonzero exit beside missing peer;good peer cannot hide known bad source.
- [ ] RED→GREEN tests:97/100 and100/94coverage;one good group hides bad peer;missing/extra/duplicate module;zero aggregate;wrong run_id/PYTEST producer/artifact SHA;one available wrong origin beside unavailable command. Expected:reasoned rejection;missing facts alone unavailable (HR-010–012).
- [ ] Run all new tests and whole suite. Expected:green;no old test or threshold changed. Commit append-only.

### Task 3: Architecture,acceptance mapping and verification handoff

**Files:**Create path8;extend only new tests/fixture paths as needed.

**Interfaces:**
- Consumes:Task2 pure gate;old core/C1 as read-only references,not runtime dependencies.
- Produces:explicit external mapping of HR-001–026 to actual pytest nodeids and measured coverage;no real historical result.

- [ ] RED tests for fresh import with file/process/network/clock writes forbidden;AST stdlib-only allowlist;no application/research/owner/C1/core-assessor bridge.
- [ ] Add architecture negatives proving a structural H record cannot clear old IO_UNAVAILABLE or override a separately rejected current C (HR-021,025,026). Preserve old files byte-for-byte;do not modify the old classes to accept H.
- [ ] Run `python -m pytest -q` and targeted branch coverage. Expected:all old2121tests plus new tests green,new statement>=98% and branch>=95%,old floors unchanged. Map actual collected IDs;do not mark unimplemented IO cases executed.
- [ ] Run Ruff/format,strict mypy,existing source/history audits,replay4goldens,build,fresh outside-checkout vanilla/research wheel and old-source/ZIP equality. These are current regression gates,not H execution. No installation/build inside historical subjects.
- [ ] Freeze exact local head;one fresh whole-branch reviewer checks type tampering,missing+invalid precedence,wrong cohort/origin,coverage laundering and qualification overclaim. Follow executing-plans' one RED→GREEN fix pass;do not reuse earlier review verdict.
- [ ] Preserve branch/worktree/external evidence;verify prior refs/PR/main unchanged;report exact head,tests,coverage,review scope and still-unavailable historical execution. No automatic I/O runner or ENTRY integration.

## Self-review

Spec1–4/9–10→Task3scope/preservation;spec8DTOs→Task1;
spec8assessment/lineage→Task2;spec5–7actual process behavior→explicitly outside
this pure plan,HR-027–040 not claimed executed. All task interfaces use the same
section8 signatures. The implementation cannot supply missing real O inventories,
enforcement or authority by filling fixture values;fixtures remain TEST_ONLY.
