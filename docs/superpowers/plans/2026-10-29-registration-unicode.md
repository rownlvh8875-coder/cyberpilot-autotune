# Offline Registration Unicode Path Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close NR-M1 without changing the native patch or registered content.

**Architecture:** Preserve Unicode in the existing Git alternate-path literal.
Exercise real Git/prepare/CLI via isolated temporary bare input aliases that share
only read-only object access with the existing pinned source cache.

**Tech Stack:** Python3.12 stdlib, Git, existing mandatory native/source suite.

**Spec:** docs/superpowers/specs/2026-10-29-registration-unicode-design.md

## Global Constraints

- Base feac824124966940d6ec2c541127f466b0c5221b; branch stacked on PR20.
- One encoding-line change; no normalization or content/policy/native changes.
- Original references/read-only backing cache unchanged, no lazy fetch/network.
- All runtime/empirical/application/fingerprint/q blockers remain.

## Review Focus

1. Symlink resolution hiding the actual non-ASCII Git alternate object path.
2. Mocking an encoder instead of exercising actual Git/prepare/CLI behavior.
3. Path content leaking into digests, identity, registry permissions or schema.
4. New temporary aliases writing original objects/refs/config or fetching inputs.
5. Unsupported cross-platform/full-native claims from Linux-only source tests.

## Task1 — reproduce then minimally fix encoding

Create compatibility/friction_native/test_registration_unicode.py. Consume actual
FRICTION_NATIVE_REFERENCE and the existing committed content record; temporary
bare references have physical Unicode directories and objects/info/alternates.
No symlink-to-reference that Path.resolve would collapse back to ASCII.

- [ ] Add six path cases and two CLI/Unicode-temp cases. Assert actual complete
  record equality, unchanged source/backing metadata and cleanup; no source mocks.
- [ ] Run against old code: observe Git path parsing failures, ASCII case passes.
- [ ] Change only json.dumps(original_objects) to preserve Unicode.
- [ ] GREEN focused/native/core suites, lint; commit the fix and regression tests.

## Task2 — final proof and delivery

Create docs/native_registration_unicode_result.md. Existing evidence stays frozen.

- [ ] Reverify source/patch/schema/digests; full source/history/coverage, core/native,
  lint/format/mypy/build/fresh wheel/replay and knowledge/owner/science smokes.
- [ ] Commit result; final exact-head independent review, C/I RED→GREEN fixes
  only/minors deferred; record review externally, not by changing reviewed head.
- [ ] Stacked Draft PR, attach, verify exact-head push/PR CI and preserved prior
  heads/main. No merge, source/runtime promotion or automatic next task.

## Ledger

Pre-flight: Task1's complete-record/path equality and fixture assertions are the
behavioral evidence Task2 reports; no new production interface or dependency.
Ruling: continue approved minimal fix inline in existing managed checkout with
tracked ledger — preserve environment/no unsolicited worktree — cost: manual
bookkeeping and one final independent review, not per-task review.
