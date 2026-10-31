# UInt64 Producer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the selected producer's epoch width without upgrading runtime evidence.

**Architecture:** New kernel delta and compiled type guards, separate raw v2
wire decoder, frozen source/build audit. All code stays in test-only tooling.

**Tech Stack:** Python3.12 stdlib/pytest; GNU C; selected Debian6.12.113 source.

**Spec:** `docs/superpowers/specs/2026-10-31-epoch-u64-producer.md`

## Global Constraints

- Base1d9207723ac63c90d8a2173bd401e3115abe2edf; preserve prior blobs/assets/PRs.
- No new guest/vehicle execution, v1 migration, qualification or application bridge.
- CPR2_ markers; profile POST_REFERENCE_RAW_EPOCH_U64_V2; encoding UINT64_DECIMAL_V1.
- Release6.12.113-cptagread-u64-v2; exact UInt64 decimal, unknown distinct from0.
- All permissions/proofs false; actual loss/global counts unknown.

## Review Focus

- Actual declarations, saved/buffer types and variadic format must agree, not merely a fake struct.
- Values above 2^32,2^53,2^63 and UInt64 max must remain exact across all layers.
- Mixed v1/v2 frames and stale profile/source markers must fail closed.
- Unknown must not become zero; raw observed zero must not become missing.
- Compiled/offline/source evidence must never become an actual capture or runtime permission.

### Task 1: Corrected producer and high-bit compile tests

**Files:** Create `tests/guest_epoch_u64/kernel.patch`, `kernel.config`,
`guest/init.c`, `native_probe.py`, `tests/test_guest_epoch_u64_native.py`.

**Interfaces:** Produce `probe(owned: Path, mutation: str | None = None) -> tuple[str,...]`
using frozen actual declaration/helper excerpts; mutation closed to saved32,
buffer32,signed,format32,mask32,float. Actual kernel type guards also compile.

- [x] Write native high-bit/mutation tests using literal decimal expectations.
- [x] Run `.venv/bin/python -m pytest -q tests/test_guest_epoch_u64_native.py`.
  Expected: RED absent API; additionally compile native against old narrow types
  and observe rejection before correcting source.
- [x] Implement kernel delta and native test tool; prepare separate exact source,
  apply patches, compile actual type guards/kernel with format warnings errors
  and new driver. Record hashes; do not execute kernel/driver.
- [x] Run focused tests and `.venv/bin/python -m pytest -q`.
  Expected: all PASS. Commit `fix: preserve raw epoch width in versioned producer`.

### Task 2: Separate v2 wire contract

**Files:** Create `tests/guest_epoch_u64/{contracts,wire,fixtures}.py`,
`tests/test_guest_epoch_u64_wire.py`.

**Interfaces:** Produce `parse_serial(raw: bytes) -> CaptureV2`, separate frozen
v2 types, fixed WIRE_BYTES_UNTRUSTED/BLOCKED and permissions false. Purely reuse
unchanged v1 event field vocabulary, never its parser/decision/converter.

- [x] Write literal v2 fixtures, UInt64/unknown, framing, field/cohort/resource,
  stage, count, duplicate and v1/mixed-version rejection tests.
- [x] Run `.venv/bin/python -m pytest -q tests/test_guest_epoch_u64_wire.py`.
  Expected: RED absent v2 API.
- [x] Implement bounded canonical ASCII parser; explicit epoch status/payload
  pairing; strict one-frame marker set, no legacy upgrade.
- [x] Run focused and full pytest. Expected: all PASS.
  Commit `feat: decode distinct untrusted UInt64 producer frames`.

### Task 3: Freeze source/build evidence and integration boundaries

**Files:** Create `tests/guest_epoch_u64/{audit,cohort}.py`, source/build manifests
under `docs/evidence/guest_epoch_u64_*.json`, `tests/test_guest_epoch_u64_audit.py`,
`tests/architecture/test_guest_epoch_u64_boundary.py`, contract/result docs.
Add only new-prefix `.gitattributes` rules.

**Interfaces:** Consume tasks1/2 and produce readonly `validate(source_root:
Path | None = None, assets_root: Path | None = None) -> dict` CLI. Default audit
is portable; explicit roots verify actual source/build bytes, never runtime.

- [x] Write frozen-source/build mutation and old-blob/import architecture guards.
- [x] Run focused audit tests. Expected: RED missing audit API.
- [x] Implement read-only source/build validation, exact hashes and evidence limits.
- [ ] Run full pytest/coverage, source/history/assets, lint/format/mypy/build,
  native192/replay4, fresh wheel, CRLF and new CLI/native/source-root checks.
  Expected: PASS; new pure decoder target98statement/95branch or explain gap.
- [ ] Commit; fresh whole-branch review at exact head; C/I one RED→GREEN fix pass,
  minors deferred. Publish authorized new stacked Draft, attach and await both CI.
