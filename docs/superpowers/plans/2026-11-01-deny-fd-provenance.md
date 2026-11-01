# Denial-FD Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax; one fresh whole-branch reviewer at the end.

**Goal:** Implement the approved synthetic point-provenance contract without
rewriting v1 evidence or granting operational authority.

**Architecture:** Pure immutable test-only contract/evaluator; separately pinned
Git successor loader preserves27old paths and freezes two updated policy paths.
No runtime producer/adapter, installed-package or old C/source mutation.

**Tech Stack:** Python3.12.3..<3.13 standard library, pytest, Git, existing quality tools.

**Spec:** `docs/superpowers/specs/2026-11-01-deny-fd-provenance-design.md`.

## Global Constraints

- Exact base1c4fb3d26db913645cb2292f362396076e47adcb; branch feat/deny-fd-provenance-contract.
- Exactly two existing+11new paths; cumulative40, no other tracked edits.
- v1 source/model/captures, original P and22postimages unchanged; legacy M1 OPEN.
- Synthetic consistency only; all9permissions false; no operational imports/IO in pure package.
- No producer/C/schema/Params/kernel/guest/vehicle/runtime/empirical/application execution.
- No prior PR/main/ref edits, publication/merge/rebase/force push.

## Review Focus

- FD0 must remain valid while missing values never become0 or empty inventories.
- Cause refs must bind each FD's exact snapshot/slot context, not just a number.
- A valid synthetic envelope cannot be promoted to an observed runtime receipt.
- Changing working manifest cannot supply policy; strengthened preservation must still reject it.
- P2 must freeze updated old paths without its loader hashing/referencing itself.

### Task 1: Neutral contract and synthetic evaluator

**Files:** create tests/deny_fd_provenance/{__init__,contracts,validation}.py,
tests/test_deny_fd_provenance.py, tests/architecture/test_deny_fd_provenance_boundary.py,
docs/evidence/deny_fd_provenance_schema.json.

**Interfaces:** spec's CaptureContext/PointRef/FdWitness/InventoryWitness/
InventoryPolicyContext/DenialReceipt; evaluate, canonical_digest, policy_digest.

- [x] Write tests for missing API, synthetic HH03 consistency, wrong cause/context,
  None/0/empty, real FD0/multiple extras, unsupported missing/mixed/other stages,
  future/duplicate references, exact types, mutation, digests and all false permissions.
- [x] Run `.venv/bin/python -m pytest tests/test_deny_fd_provenance.py -q`.
  Expected: RED because contract API is absent, not a typo.
- [x] Implement only the pure API; add semantic-schema/source-cohort/purity tests.
- [x] Rerun behavior and architecture. Expected: GREEN; no loader/producer dependency.
- [x] Commit exact additions (whole old architecture freeze remains intentionally
  RED until the approved successor policy is enabled; do not publish intermediate tips).

### Task 2: Preregister and enforce successor history

**Files:** modify only tests/history_transition/policy.py and
tests/test_history_transition_policy.py; create tests/history_transition/deny_fd_successor.py
and docs/evidence/deny_fd_history_successor_v1.json.

**Interfaces:** successor `PREREGISTRATION`, `validate_successor(root) -> frozenset[str]`.
Old policy invokes it without embedding P2; test clone fixture uses successor P2.

- [x] Add real-Git missing-successor,27preserved/two-postimage layer mutations,
  unlisted-path, historical acceptance/current rejection and CRLF tests; observe RED.
- [x] Update only two approved old files; retain old P/_load/guard criteria and node IDs.
- [x] Freeze manifest and finalized two modified postimages in append-only P2.
  Expected: P2 ancestor of final HEAD, base1c4 ancestor P2, no self-hash.
- [x] Add loader pin after P2; exact immutable manifest, all29old states and cumulative
  scope checks fail without fetch/fallback. No mutable manifest authority.
- [x] Run `.venv/bin/python -m pytest tests/test_history_transition_policy.py tests/architecture -q`.
  Expected: GREEN, original v1 node also executes in fixed historical clone.
- [x] Commit enabling loader; full suite now must be GREEN.

### Task 3: Verify and local handoff

**Files:** create docs/deny_fd_provenance_result.md; update only new spec/plan/schema
if bookkeeping needs it, never frozen two postimages after P2.

- [x] Run full pytest, isolated new-package coverage, all old audits/history validators,
  ruff/format/mypy, build/fresh wheel, replay/knowledge/owner/science smoke.
  Expected: all pass; wheel installed-source bytes unchanged; no test criteria weakened.
- [x] Check exact13delta/40cumulative paths and byte-exact v1/P/22postimages/27preserved.
- [ ] Commit pre-review result. Fresh exact-head reviewer inspects whole branch and
  all ledger rulings; any material finding gets RED→GREEN and full rerun.
- [ ] Final exact-head rerun and clean status; report local branch/head and review.
  Leave publication/CI/merge/runtime qualification for separately authorized work.
