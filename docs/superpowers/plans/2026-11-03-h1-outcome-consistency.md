# H1 Outcome Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans.

**Goal:** Reject already available outcome/collection contradictions even without policy witnesses.

**Architecture:** Add one invariant to the existing pure H1 observation checker.
Freeze prior range checks at a8b2bf1 and add a separate narrowly bounded successor.

**Tech Stack:** Existing Python 3.12,pytest,Git,Ruff,mypy;no new dependency.

**Spec:** `docs/superpowers/specs/2026-11-03-h1-outcome-consistency-design.md`

## Global Constraints

- Base `a8b2bf1e6f27a4157212298928a50c8e970babf5`;existing isolated feature worktree.
- No product,wire,workflow,collector,fixture,host-config or qualification change.
- Preserve D499,coverage floors,all old scope helpers and fixed historical ranges.
- All nine permissions false;all prior blockers and historical operational I1 retained.
- Local append-only commits only;no remote mutation,vehicle,Params or actual H.

## Review Focus

- Policy absent,command absent and expected inventory None must not hide a known contradiction.
- D additional audit nodes must be checked even when the D499 diagnostic subset is intact.
- None,empty sets,incomplete runs and reordered equal sets must remain distinguishable.
- Foreign outcomes must reject even before a successful exit is available.
- Successor guard must reject unknown/untracked/frozen/status-alias changes through the real consumer.

### Task 1: Fix the invariant and preserve fixed history

**Create:** this plan,its spec,`tests/test_h1_outcome_consistency.py`,
`docs/evidence/audit_compatibility/h1-outcome-consistency-v1/registration.json`.

**Modify:** `tests/audit_compatibility_history/validation.py`,
`tests/test_audit_compatibility_history_architecture.py`,
`tests/test_audit_compatibility_capture_portability.py`,
`tests/test_actions_preflight_registration.py`.

**Interfaces:** Existing `assess_record(record,policy)->HistoricalReplayDecision`
stays unchanged. `_observed(item,errors,missing)` adds only independent set
consistency. New `_h1_outcome_changes(rows)` validates literal successor paths
without granting authority from registration data.

- [x] Write real supplied-record regressions: empty/foreign outcomes;O and D-extra
  nodes;four policy states;foreign outcomes with exit unavailable;None/partial/
  empty/equal-reordered controls. Assert REJECTED versus UNAVAILABLE and nine false permissions.
- [x] Run the regression module and record the intended RED before implementation.
- [x] Add the minimal invariant;freeze old range endpoints and add the separate
  four-addition/four-modification successor guard. Keep old helper bodies unchanged.
- [x] Run targeted regressions and actual historical guard consumers to GREEN.
- [x] Run full pytest,unchanged coverage/floors,source/history audits,Ruff/format,
  mypy,replay goldens,build and fresh no-dependency wheel smoke.
- [ ] Commit append-only after verification;run a fresh exact-head independent
  review of this task's entire delta. Resolve any Important finding with RED/GREEN
  without weakening fixed ranges or criteria. Leave remote state untouched.

Expected: the six previously misclassified vectors reject;missing/in-progress
controls remain unavailable;all prior tests and scope/security checks remain green.

Checkmarks describe the precommit verification snapshot. Final exact-head review,
commit identity and postcommit verification are retained in the external task
archive rather than changing source after that review.
