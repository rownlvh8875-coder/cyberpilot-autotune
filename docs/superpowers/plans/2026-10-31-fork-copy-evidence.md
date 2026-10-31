# Fork-copy evidence design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a source-grounded per-slot copy contract and verify it with synthetic witnesses only.

**Architecture:** New test-only pure evaluator plus closed finite schema/catalog/source
audit; no producer integration or kernel changes. Source ranges bind existing PR38.

**Tech Stack:** Python3.12,pytest,JSON; read-only Linux6.12.113 source.

**Spec:** `docs/superpowers/specs/2026-10-31-fork-copy-evidence-design.md`

## Global Constraints

- Base420538d7c20edcfca3eadf136b30b622ca2bede9;branch design/managed-root-fork-copy-evidence.
- New tests/fork_copy_design only; all existing source/tests/evidence/PRs unchanged.
- SYNTHETIC_ONLY,64slots/64capacity,196records;no actual producer/build/boot.
- Status BLOCKED,9permissions false,global counts None,atomic_cut_proven=False.
- Inline execution,one final fresh review,own stacked Draft only;no merge.

## Review Focus

1. NULL,unknown present OFD and unavailable read collapsed into the same value.
2. Copied stale CLOEXEC bit mistaken for effective NULL-slot binding flags.
3. Private copy or file_lock mistaken for source-owner closure/atomic cut.
4. Post-return namespace cookie or task commit substituted for consumed slot evidence.
5. Balanced local counters,128buffer or synthetic digest promoted to runtime qualification.

### Task1: Pure per-slot contract

**Files:** create tests/fork_copy_design/{__init__,model}.py;tests/test_fork_copy_design.py.
**Interfaces:** evaluate(data:object)->Decision with frozen slots/reasons/digest and fixed no-authority fields.

- [ ] Test literal private-copy context,64READ/ref-or-clear/STORE triples,196events and FD5/40 aliasing.
- [ ] Test unknown OFD/root creator vs forbidden nonroot unknown,source bit contradictions,NULL stale flags,missing/swapped/paired stages,copy/task abort,counter loss/None,types/cohort/role/resource/digest/copy boundaries.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_fork_copy_design.py`;expect missing API RED.
- [ ] Implement exact closed fields/64-slot grammar and defensive pure evaluator;run focused GREEN and commit.

### Task2: Source/schema/catalog and preferred capture design

**Files:** create tests/fork_copy_design/audit.py;tests/test_fork_copy_design_audit.py;
architecture guard;docs/evidence/fork_copy_design_{sources,schema,cases}.json;
docs/fork_copy_evidence_contract.md;docs/fork_copy_capture_design.md.
**Interfaces:** validate(kernel_root:Path|None=None,pristine_root:Path|None=None)->dict[str,Any];separate optional read-only source verification.

- [ ] Write audit tests for catalog outcomes,all6oldpresence schedules/1no-cut,source/range/schema/case tampering and forbidden authority;run missing API RED.
- [ ] Generate byte/range manifests from current fixed source;freeze semantic schema,synthetic cases and stage distinctions;implement default offline/noVM audit.
- [ ] Document exact source math,constructor cookie gap,capture alternatives/selected explicit context,capacity196vs128,task-finalize gap and no adapter.
- [ ] Run focused+optional source audit,architecture preservation,ruff/format/mypy;commit.

### Task3: Result and complete verification

**Files:** docs/fork_copy_design_result.md;only necessary new-path attributes.
**Interfaces:** consumes Task1 Decision and Task2 validate;does not change them except tested defect fixes.

- [ ] Run full pytest,pure coverage,lint/format,mypy,old source/history/native/guest audits,build,fresh vanilla/research wheel,CRLF.
- [ ] Publish exact design-only result/retained blockers;commit and run exact-head verification.
- [ ] One fresh whole-branch review;regrade,one author C/I RED→GREEN pass/full rerun if needed;defer minor,no re-review.
- [ ] Push own branch/create Draft against PR38,attach PR,verify exact-head push+PR6jobs each,record preserved25PRs/main.
- [ ] Report Korean result,rulings/costs/deferred minors,next single task;recoverably archive only this plan's workspace.
