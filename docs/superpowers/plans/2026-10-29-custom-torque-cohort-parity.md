# Custom Torque Cohort Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close PR18-M1 with source-backed positive-selector/frame10 latch-reset
parity and exact receipt cohort tests, without changing the native patch.

**Architecture:** Extend existing offline AST harness with actual R callback/helper
and31-cycle scripted settings. Compare baseline/patched states and independent
literal expectations; inject test-only in-memory mutants to prove sensitivity.

**Tech Stack:** Python3.12, NumPy, pycapnp2.1.0, pytest, existing Git object cache.

**Spec:** docs/superpowers/specs/2026-10-29-custom-torque-cohort-parity-design.md

## Global Constraints

- Base f0fc6cdcab10447c2b855c9c65e7acafe7e3c2a9; native R=c213, comparative C=f5e4.
- New files only; old code/assets/CI/source registration/prior PRs unchanged.
- No actual Params/SubMaster/runtime/vehicle, native fork PR/merge or authority.
- Legacy selector1->0 vs2->0 difference retained; no gain reset invented.
- NR-M1 and all empirical/runtime/application gates remain unresolved.

## Review Focus

1. Baseline/patched equality masking a shared faulty or unexecuted custom branch.
2. Requested settings mistaken for latched installed values or exact gains.
3. Comment-based1->0 reset/gain assumptions overriding actual pinned source.
4. Fake callback or receipt backfill replacing actual FF/PID/cohort observations.
5. Test-only source mutation or setup touching old assets/runtime/deployment.

## Task1 — continuous custom cohort harness and tests

Create compatibility/friction_native/custom_cohort.py and test_custom_cohort.py.
Consume existing load_pid/load_lateral/lateral and exact Git source input. Produce
load_callback(reference), run(source, callback, selector, family, observer_kind,
inactive=()), assert_parity(before,after), assert_cohorts(result,selector,family).
Returns scalar snapshots/callback-read traces/immutable receipts, not estimator
observations. Hand-derived expected table lives in source-backed tests.

- [x] Write missing-harness tests; run and observe CUSTOM_COHORT_HARNESS_MISSING.
- [x] Implement exact hash-validated callback/helper AST load,31-cycle fixture;
  inspect actual baseline/patched state/bit/reader traces and literal assertions.
- [x] Add latch cadence, reset condition, live bypass and wrong capture mutants;
  demonstrate actual failing assertions in subprocesses/in-memory sources only.
- [x] Run focused/native/full core tests and lint; commit GREEN harness/tests.

## Task2 — evidence, regressions and final delivery

Create docs/evidence/carrot_custom_torque_cohort_parity.json and
docs/carrot_custom_torque_cohort_parity_result.md. Add no old CI/test changes.

- [x] Pin source file/blob/range hashes, scenario/coverage/mutation observations
  and unchanged patch/tree identities; test evidence against observed scenarios.
- [x] Full core/native/source/history/coverage, lint/format/mypy/build/fresh wheel,
  replay and knowledge/owner/science/research smokes. No native/full NN claim.
- [x] Test reusable setup with eleven warmed R blobs; save necessary environment
  draft fields for user review/Publish, not runtime activation.
- [ ] Commit final candidate; one independent exact-head review; C/I RED→GREEN
  fixes only, minors deferred. Record final review externally to preserve head.
- [ ] Publish stacked Draft PR; attach and verify exact-head push/PR CI, clean
  worktree and preserved main/PR8/9/16/17/18/19. Stop; no auto-next task.

## Ledger

Pre-flight: Task1's snapshots and exact source claims feed Task2 evidence, while
the existing runner discovers new source tests automatically. Extra R callback/
helper blobs are setup inputs already warmed by CI's old science/source audit.

Ruling: approved next task continues inline in the existing dedicated checkout
with tracked ledger — avoids repeated approval/worktree creation — cost: manual
bookkeeping and one final independent review rather than per-task reviews.
Ruling: load exact R callback/helper and use explicit settings/IO doubles — tests
need real math without runtime imports — cost: constructor/full process/NN weights,
timing and vehicle behavior remain unqualified; no universal equivalence claim.

Baseline1494 core pass, clean tree. PR19 OPEN/Draft/f0fc6cd and12 successful checks;
carrot-wip unchanged at f5e4. Two already hash-pinned source blobs copied into the
bare dependency cache from the existing read-only exact-R source cache during
setup; no source tree or native ref modified. New tests remain network-free.

Task1: complete — dedicated body test RED CUSTOM_COHORT_HARNESS_MISSING then
GREEN53 scenarios/checks. Evidence assertion RED CUSTOM_COHORT_EVIDENCE_MISSING
then GREEN58; six in-memory mutants all killed by actual parity/literal cohort
assertions. New harness124 statements/22 branches100%/100%, NOT whole-controller
coverage. Mandatory native184 pass/no skips; core1494 pass; lint/format/mypy pass.
Actual Cap'n Proto tuning/log fields are used, including original Float32 error
readback, not a Python replacement for the native callback equation.

Ruling: include evidence in the harness commit — source tests consume the frozen
checkpoint record — cost: regenerate it if the scoped scenario semantics change.
Setup tested successfully with eleven exact-R blobs, core1494/native184; only
install_script/start_skill drafts updated for review/Publish. No network/secrets,
repository ref selection or actual runtime behavior changed by the setup draft.

Task2 local gates complete: fresh184 native/no skips and1494 core pass; installed
coverage98.52%, H7 unchanged843 statements/276 branches100%/100%. All H2–H7/design
source/history/coverage audits, source registration, lint/format/mypy71, build/
fresh wheel70 imports, replay11/four digests, knowledge/owner/science/research and
optional-dependency smokes pass. Exact callback count/consumed cohorts and actual
PID f multiplication are also asserted; all six mutants remain caught. Native
patch/applied tree/candidate and all old tracked files remain unchanged. Final
review/publication/CI results belong to the new PR's external completion record.
