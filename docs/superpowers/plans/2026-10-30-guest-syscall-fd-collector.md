# Guest Syscall/FD Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and actually exercise a kernel-stop-based guest syscall/task/exec/FD collector for the fixed harmless fixtures.

**Architecture:** Independent ptrace supervisor before fixed fixture exec; retain the unchanged LSM guard and broker. Pure immutable event parsing/evaluation independently checks capture closure and FD/request provenance; unsupported evidence rejects.

**Tech Stack:** Python3.12 standard library/pytest; C17 native x86_64 Linux ptrace/procfs; already pinned guest/kernel/toolchain; no new dependency or host policy.

**Spec:** [binding design](../specs/2026-10-30-guest-syscall-fd-collector-design.md).

## Global Constraints

- Base `1b2ff21ac83a8ea9d7c04850c8e2f7e92d06425d`; prior package, tests, evidence, installed source, CI and older PR heads unchanged.
- Same approved QEMU TCG/6.12.113 guest only. Only fixed harmless C helpers execute; no outer-host tracing/policy, devices, network, Carrot-native/model/controller/Params/vehicle or arbitrary commands.
- Version `guest-syscall-fd-v1`; UNTRUSTED_CAPTURE_REPORT; observation clock `GUEST_TRACER_OBSERVATION_MONOTONIC_NS`.
- STRICT_NO_DEVICE_ATTEMPT; Gate A BLOCKED; B/C/D not started. All permissions false; global handle/effect counts unknown.
- No register/result/argument/seccomp mutation, CONTINUE, unscoped fallback or guessed task/FD generation.
- Author implements inline as delegated; one fresh independent whole-branch final reviewer. No implementation subagents.

## Review Focus

1. Seccomp ERRNO call missing from entry trace, or kill/exit mistaken for normal return: reject unexplained pairing.
2. PID/FD reuse, cloned file-table sharing or nonleader exec: never silently alias generations or claim supported completeness.
3. USER_NOTIF source/target/request pairing: never infer successful delivery from inode similarity or failed/stale ADDFD.
4. Collector truncation/loss/counter mismatch or clock drift: fail closed; never zero prohibited counts or invent termination.
5. Operational argument/asset drift and publication line endings: fixed guest recipe and exact-byte hashes, no host or arbitrary payload fallback.

### Task1: Immutable capture and independent evaluator

**Files:** Create `compatibility/containment_guest_collector/{__init__,contracts,validation,evaluation}.py`; `tests/fixtures/guest_collector.py`; `tests/unit/test_guest_collector_contracts.py`, `test_guest_collector_evaluation.py`.

**Interfaces:** Frozen `TraceEvent(kind,seq,mono_ns,task,tid,image,values)` and `Capture(fixture_id,events,end_values)`; `parse_capture(raw: str) -> Capture`; `capture_digest(capture: Capture) -> str`; frozen `CaptureAssessment(capture_complete,fd_profile_complete,task_count,call_pairs,aborted_calls,exec_count,fd_transitions,notifications,donations,reasons)` with fixed-false permissions. `evaluate_capture(capture: Capture) -> CaptureAssessment`. No IO or operational imports.

- [ ] Write literal synthetic seed/fork/exec/FD/notification examples and tests for all five Review Focus failures, None/zero distinctions, immutable tuples and exact JSON keys. Expected literal counts independent of evaluator.
- [ ] Run focused pytest; Expected: RED missing APIs, not import typo.
- [ ] Implement strict finite/range/kind validation and a per-task pending-call/exec/FD/request ledger. Explicit seed/birth completions and signal aborts; no unpaired success.
- [ ] Run focused + full pytest; Expected: GREEN, all prior1855 tests unchanged.
- [ ] Commit `feat: define immutable guest capture and fail-closed reconciliation`.

### Task2: Actual fixed guest collector and runner

**Files:** Create `compatibility/containment_guest_collector/guest/{collector.c,fd_snapshot.c,collector.h,build_manifest.json}`, `{image,host_main,vm_runner}.py`; `tests/unit/test_guest_collector_runner.py`; `tests/architecture/test_guest_collector_boundary.py`; new source manifest `docs/evidence/guest_collector_sources.json`.

**Interfaces:** Guest executable accepts exactly one HF01–HF24 ID and always execs `/harmless-fixtures`; no payload path. `int snapshot_fds(pid_t tid, struct fd_record *records, size_t capacity)` observes only stopped traced tasks; `host_main.main(argv) -> int`, default2/no IO. `build_collector_image(...) -> bytes` fixed asset names. New runner verifies old frozen manifest/cohort and new collector hashes, fixed TCG arguments and explicit selected IDs only.

- [ ] Read/pin actual kernel ptrace/seccomp/fork/exec/procfs source and ranges before any guest execution; source archive hash must match the authenticated bound Debian package component.
- [ ] Write closed-default/asset drift/image bootstrap override tests; run RED before runner implementation.
- [ ] Build an actual guest missing-collector RED image; independent parser must reject missing capture, not accept old HF raw output.
- [ ] Implement C supervisor: initial stop/before-exec tracing; TRACEFORK/VFORK/CLONE/EXEC/EXIT, TRACESYSGOOD, EXITKILL; GET_SYSCALL_INFO; actual task generations; numeric FD snapshots and typed ioctl records. All output counters from actual collection.
- [ ] Implement fixed runner/image, rootless compile only, no default CI guest execution. Run focused tests + actual HF01/HF09/HF11/HF12/HF15/HF22, then explicit all24; Expected: original narrow checks still pass, complete captures or precise rejected unsupported reasons. Fix actual causes, never widen filters or bypass fixture timeouts.
- [ ] Run full pytest, ruff/format/mypy; Expected GREEN; commit `feat: collect actual guest syscalls lifecycle and fd receipts`.

### Task3: Evidence, regression and Draft handoff

**Files:** Create `docs/guest_syscall_fd_collector_result.md`, `docs/evidence/guest_collector_results.json`, new lossless raw artifact under new package `evidence/`, `tests/unit/test_guest_collector_published.py`; narrowly scoped new evidence Git attributes if required.

**Interfaces:** Actual logs -> Task1 Capture/Assessment/digest; Task2's unchanged HF assertions separately checked. Publish every selected result/reason and immutable source/build/log hashes; no promotion of old reports or automatic trusted authenticity.

- [ ] Write published artifact/digest/unknown-count and fresh-autocrlf behavior tests; run RED for missing evidence.
- [ ] Publish actual24 per-fixture summaries and raw bytes, explicit completeness scope/missing proof, full inherited blockers. Expected: no device/native/application claim, no fabricated zero.
- [ ] Run full pytest, lint/format/mypy, build/fresh wheel/replay/smokes, historical source audits and passive native192; verify old frozen package/evidence byte equality and original VM cohort.
- [ ] Commit evidence/result, dispatch one fresh exact-head read-only independent reviewer, all five Review Focus inputs and rulings supplied. C/I -> one RED/GREEN fix pass + full rerun; minors deferred, no repeated reviewer.
- [ ] Create own stacked Draft against `feat/guest-harmless-backend-harness`, attach it and require exact-head push/PR CI success; no earlier PR edit or merge. Stop, recommend exactly one next task without starting it.

Self-review: Task1 owns identities/reconciliation, Task2 actual capture and fixed
scope, Task3 evidence honesty/handoff. Counters are derived only from raw events;
no producer bool is sufficient to establish completeness or authority.
