# H1 cancellation cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair owned-helper cancellation cleanup without changing execution authority.

**Architecture:** One post-Popen ownership boundary encloses pidfd acquisition and
protocol evaluation. Best-effort cancellation cleanup preserves the original
exception; a separate literal successor preserves all old history checks.

**Tech Stack:** Python >=3.12.3,<3.13,stdlib,pytest,Ruff,mypy,existing build/replay tools.

**Spec:** docs/superpowers/specs/2026-11-03-h1-cancellation-cleanup-design.md.

## Global Constraints

- Start exact209edaa83b398e6204af1097fda4b651807cc815; same named isolated branch.
- Append-only local commits; no Ready/merge,remote publication or PR8/9/other edits.
- No numeric PID fallback,new dependency,budget,workflow or product delta.
- Existing normal wall5s,timeout0.4s,cleanup2s and original thresholds stay fixed.
- All9domainpermissionsfalse;H/Q/I/ENTRY/STACK/application/vehicle remain blocked.
- Spec/plan record a precommit checkpoint; definitive results/reviews stay external.

## Review Focus

- Cancellation before pidfd availability: EOF/wait without numeric signaling.
- Cancellation at input write/close: helper cannot remain awaiting owned open input.
- Secondary cancellation/OSError in cleanup: original exception identity survives.
- Already reaped helper/uncertain descriptor close: no stale-descriptor retry.
- Registered successor versus historical scopes: unknown or frozen mutations reject.

### Task 1: Repair and guard the owned-helper lifetime

**Files:**
- Create: this plan,the named spec,tests/test_h1_cancellation_cleanup.py,
  docs/evidence/audit_compatibility/h1-cancellation-cleanup-v1/registration.json.
- Modify: tests/audit_compatibility_executor/supervision.py,
  tests/audit_compatibility_executor/runner.py,
  tests/test_audit_compatibility_history_architecture.py,
  tests/test_h1_outcome_consistency.py,tests/test_actions_preflight_registration.py.

**Interfaces:** Preserve supervise(case:SyntheticCase,run_root:str)->SyntheticResult;
private ownership helpers may factor protocol evaluation and cleanup. Preserve
the old _h1_outcome_changes ceiling; add _h1_cancellation_changes(rows) with the
literal four-add/five-mod inventory. No other public interface changes.

- [ ] Write fake-boundary cancellation tests against actual supervise: same
  KeyboardInterrupt/SystemExit at acquisition/write/close/collect/wait propagates,
  input/output handles close,retained pidfd signals before bounded wait/close;
  no pidfd means no signal. Add cleanup-error and normal/known-error controls.
- [ ] Run the new behavior tests before implementation.
  Expected: failures showing absent close/kill/wait,not fixture/import errors.
- [ ] Implement the smallest post-Popen ownership cleanup satisfying the spec.
  Expected: behavior tests pass; fixed uncertainty notes,not fabricated success.
- [ ] Add exact new successor and freeze previous outcome range at209. Add scope
  rejection/consumer/history tests first,observe RED,then implement literal guards.
  Expected: exact9path inventory passes;unknown/status/alias/untracked changes fail.
- [ ] Run the whole project pytest command with external temp/cache outputs.
  Expected: all regressions green,old cases retained;report unsupported native
  observations as UNAVAILABLE,not kernel passes. Run lint/format/type/source/history,
  coverage,replay,build and fresh installed-wheel smoke without changing floors.
- [ ] Commit the complete verified repair locally,then verify exact committed
  head and run the named task suite again. Expected: clean append-only commit.
- [ ] Obtain one fresh independent review of the whole repair and rule every
  declined item. Any new Critical/Important gets one RED->GREEN fix pass plus full
  suite;do not change old freezes or claim a new-head hosted CI that did not run.

Self-review: one coupled task,no inter-task interfaces;the five Review Focus items
are covered by behavior/scope regressions. Full native efficacy remains outside
software-control-flow qualification. User delegated execution-method decisions;
implement inline,then independent review. Preserve worktree/branch and external
evidence;publication is the next separately authorized action.

Review-fix pass at98626b9:C0/I1/M0,primary cancellation masked by inner cleanup.
The spec's adjustment narrowly adds runner.py to the current successor only and
allows _collect/_read_owned plus runner's directory/write helpers to preserve
primary exceptions. Add real imported nested cleanup fake regressions first,
observe RED,fix once,full rerun and append-only commit. No second independent
review;the final report must distinguish reviewed98626b9 from parent-verified fix.
