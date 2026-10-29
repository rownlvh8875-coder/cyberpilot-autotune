# Offline Native Source/Schema Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce the full patched native tree and synthetic revision in an
offline content registration without approving or deploying that source.

**Architecture:** Temporary Git object overlay with read-only base alternates;
seven-file reconstruction from unchanged PR18 assets. Repository-only CLI verifies
a new content record; installed H7 policy and native producer stay unchanged.

**Tech Stack:** Python3.12 stdlib, Git SHA-1 objects, existing pycapnp2.1.0 suite.

**Spec:** docs/superpowers/specs/2026-10-29-native-friction-registration-design.md

## Global Constraints

- Base 0d1d44c808050835aa5a52c3ddd76d51cb3300b0; native R=c213; C=f5e4 unchanged.
- No old tracked file modifications, native refs/push, device, Params or services.
- Source/schema/content registration only; no H7 allowlist/estimator bridge.
- Missing q and every runtime/empirical/application/owner gate remain blocked.
- Temporary Git objects are not a complete source archive or deployment.

## Review Focus

1. A partial file manifest mistaken for a complete applied native tree.
2. Root log schema digest confused with transitive closure or authorization.
3. Reference writes/lazy fetch through Git environment/config/replace objects.
4. Synthetic identity/missing objects mistaken for real native commit/deployment.
5. Altered manifest, true permissions or unsupported new source silently accepted.

## Task 1: reproducible native tree and source record

Files: create compatibility/friction_native/registration.py,
tests/native_friction/test_registration.py,
compatibility/friction_native/test_registration.py.

Interfaces: prepare(reference:Path)->dict; verify(record, reference)->None;
canonical(value)->bytes; main(argv=None)->int. Verification reconstructs content,
not a shape-only or caller-supplied digest check. CLI --reference-checkout required;
--print-record optional, otherwise compare committed evidence and fail on drift.

- [x] Write tests: missing module fails with OFFLINE_REGISTRATION_MISSING;
  deterministic full tree/single-parent commit, seven-path diff and unchanged
  reference; schema digest/closure; old source rejection; altered record denial.
- [x] Run tests, observe expected RED. Native cases require exact warmed R cache.
- [x] Implement isolated object overlay, deterministic metadata, frozen PR18
  source/target/patch validation, separate root/closure digests and CLI verification.
- [x] GREEN: core tests and mandatory source-backed native tests; record exact count.
- [x] Commit implementation after passing focused/full tests.

## Task 2: evidence, result and regression/publication

Files: create docs/evidence/carrot_passive_native_registration.json,
docs/carrot_passive_native_registration_result.md. No old evidence rewritten.

Interfaces: evidence is exactly prepare(reference), verified by CLI and mandatory
source tests discovered by the existing runner/CI; no CI edits needed.

- [x] Generate record using --print-record and add via apply_patch.
- [ ] CLI verify, source suite/no skips, coverage, all old audits, pytest, lint,
  format, mypy, build/fresh wheel, replay and knowledge/owner/science smokes.
- [ ] Document provenance/limits, synthetic identity and all retained blockers.
- [ ] Commit final result, one fresh exact-head review; C/I RED→GREEN fix pass only.
- [ ] Publish a stacked Draft PR against PR18; exact-head push/PR CI; preserve
  PR8/9/16/17/18 and main; attach PR URL. No merge or automatic next task.

## Ledger

Pre-flight: Task1 prepare/verify returns the exact record consumed by Task2
evidence and CLI. Existing source runner discovers both new test modules without
CI edits. No runtime interface shared; the old source registry is deliberately
not extended.

Ruling: user opted out of another questions round with all-work approval/proceed;
execute scoped offline preparation inline — previous recommendation is explicit —
cost: no new design approval round or per-task independent review.
Ruling: reuse the clean dedicated cloud checkout on a new feature branch, not
create an unsolicited worktree or unavailable skill-script workspace — preserve
managed environment and use this tracked ledger — cost: manual bookkeeping.
Ruling: use an ephemeral synthetic Git commit object, not a native branch or
signed/published commit — identifies the whole tree without external mutation —
cost: source deployment/registration qualification still require separate work.

Baseline:1481 core tests pass; PR18 exact head0d1d44c OPEN/Draft with12 successful
CI checks. carrot-wip re-read unchanged at f5e4. All prior heads remain preserved.

Task1 RED14: absent implementation fails OFFLINE_REGISTRATION_MISSING. Initial
GREEN run13/14: independent write-tree attempted a missing untouched promisor
blob, while network guard correctly denied lazy fetch. Git documents --missing-ok;
the index oracle uses it to compare complete trees without claiming blob closure.
Ruling: untouched blobs may remain promisor references — this task proves complete
tree identity, not full-source availability — cost: no standalone/deployable Git
archive, full build or device distribution is produced.

Ruling: include the generated evidence with Task1 rather than defer it to Task2 —
Task1's record-verification tests need their committed input — cost: regenerate the
record if implementation semantics change before the final freeze.
Task 1: complete — RED14 missing implementation → GREEN14; duplicate-key parser
test RED missing read_record → GREEN. Added real Git mode/layout, wrong object
format, tamper/CLI and additive-history cases. Final focused21/21, native126/126
without skips, core1494/1494; lint/format/mypy pass. New offline tool coverage
119/125 statements (95.20%),32/38 branches (84.21%), combined92.64%; defensive
Git corruption/error guards remain unexercised, not claimed100%. Old H7 unchanged.
