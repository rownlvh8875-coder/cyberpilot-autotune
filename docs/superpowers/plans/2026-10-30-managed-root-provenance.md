# Managed-root provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record managed-root creation-time task/scope/namespace provenance in a fixed disposable guest.

**Architecture:** New test-only pure parser/diagnostic, complete Linux source patch,
fixed static driver and explicit frozen-asset runner. Preserve all PR37 artifacts.

**Tech Stack:** Python3.12, Linux6.12.113 C, GCC14.2, QEMU10.0.13 TCG.

**Spec:** `docs/superpowers/specs/2026-10-30-managed-root-provenance-design.md`

## Global Constraints

- Base `06e218ca9e17af9547fc7871df70d2b9415f2cb9`; branch `feat/guest-managed-root-provenance`.
- New package `tests/guest_root_scope`; no installed/runtime/old code or evidence changes.
- Exactly NORMAL, ROOT_BIRTH_LOSS, SMALL_BUFFER; one vCPU,512MiB,TCG; no network/device/arbitrary payload.
- All9 permissions false; global loss/prohibited counts unknown; no qualified observer/bridge/application.
- Inline implementation and one fresh final reviewer; append-only own stacked Draft only.

## Review Focus

1. Root armer PID/borrowed pointer or unknown old namespace mistaken for a birth.
2. Inherited task cookie or actor/subject conflation across copy_process/copy_files.
3. Allocation without successful commit, or missing record despite balanced counters.
4. Post-free identity/scope access and emission-order mistaken for effect order.
5. Captured diagnostic promoted to complete inventory/global losslessness/authority.

### Task 1: Pure creation provenance contract

**Files:** new `tests/guest_root_scope/{__init__,model}.py`, `tests/test_guest_root_scope.py`.
**Interfaces:** `parse_serial(raw: bytes) -> Capture`; `assess(capture: Capture) -> Diagnostic`.

- [ ] Write literal CPS frames; assert exact root task1/table2 link, actor/subject separation, immutable unknown values; malformed/stale/duplicate/stage rejection; missing/colliding allocation/namespace/commit reasons and no authority.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_guest_root_scope.py`; observe missing API/behavior RED.
- [ ] Implement strict bounded parser and pure evaluator; no IO/runtime imports.
- [ ] Run focused tests GREEN, then commit `feat: define managed-root creation provenance diagnostic`.

### Task 2: Source extension and actual guest

**Files:** new `tests/guest_root_scope/{image,runner}.py`, `guest/init.c`, `kernel.patch`, `kernel.config`; `tests/test_guest_root_scope_runner.py`.
**Interfaces:** `build_image(binary: bytes, case: str) -> bytes`; `capture(case: str) -> tuple[Capture, bytes, bytes]`.

- [ ] Test fixed case/recipe, deterministic newc image and asset-drift rejection; observe missing API RED.
- [ ] Build fixed driver; boot old PR37 kernel as actual missing-CPS-contract RED before new source patch.
- [ ] Implement source hooks from spec; build fresh prefix, pin source/kernel/driver/image inputs.
- [ ] Execute only three fixed guests; inspect all source frames and root creation sequence.
- [ ] Run focused tests; commit `feat: capture source-issued managed-root birth context in guest`.

### Task 3: Offline evidence, adversaries and result

**Files:** new `tests/guest_root_scope/audit.py`, `tests/test_guest_root_scope_audit.py`, architecture guard, new evidence `guest_root_scope_{build,actual,sources}.json`, docs contract/result.
**Interfaces:** `validate(pristine_root: Path | None = None, patched_root: Path | None = None, *, verify_assets: bool = False) -> dict[str, Any]`.

- [ ] Actual byte replay tests plus changed evidence/source/role/unknown/permission negative cases RED.
- [ ] Bind exact files/ranges/serial/build inputs; implement offline-only audit and architecture guard.
- [ ] Test source/archive/assets optional checks and previous code/PR invariance.
- [ ] Run focused/full regression,100/100 pure coverage where feasible,ruff/format,mypy,build,fresh wheel,CRLF,prior source/native audits.
- [ ] Commit result, dispatch one fresh exact-head reviewer, regrade findings, at most one TDD C/I fix pass; no second review.
- [ ] Push only own branch, create stacked Draft, verify both exact-head CI events; report evidence, all rulings/costs and retained blockers, archive only owned plan workspace.
