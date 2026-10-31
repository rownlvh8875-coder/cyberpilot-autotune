# Epoch Full Decoder Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the missing compiled-C-output→existing full-v2-decoder gate without changing frozen history.

**Architecture:** A bounded native test tool emits complete synthetic framing
around actual C payload snippets. A pure checker decodes unchanged bytes and
requires an independent literal cohort; separate architecture guards pin scope.

**Tech Stack:** Python3.12 stdlib/pytest, GNU C, existing immutable v2 decoder.

**Spec:** `docs/superpowers/specs/2026-10-31-epoch-decoder-bridge.md`

## Global Constraints

- Base4371dfe5e69878665abcb9133cc20d5e0451949d; preserve every prior blob/PR/asset.
- No merge, rebase, force/shared push, actual deployment, vehicle/guest/kernel execution.
- Synthetic C frame only; WIRE_BYTES_UNTRUSTED/BLOCKED, nine permissions/proofs false.
- Do not claim PR25/33/34/9 resolved or relax any history/acceptance rule.

## Review Focus

- Full C stdout must be decoded directly, not a regex-derived surrogate frame.
- Expected high-bit values must be independent of the source-under-test generator.
- Lossy masking/float outputs can parse but must fail the independent value gate.
- Correct values with wrong stage/context/availability must not pass.
- Passing a userspace integration test must never be presented as kernel/runtime qualification.

### Task 1: Full-output native bridge and checker

**Files:** Create `tests/epoch_decoder_bridge/{__init__,native,validation}.py`,
`tests/test_epoch_decoder_bridge.py`.

**Interfaces:** `probe_frame(owned: Path, mutation: str | None = None) -> bytes`;
`check_frame(raw: bytes) -> CaptureV2` using existing parse_serial unchanged.

- [x] Write tests for literal11values, direct full stdout, unknown/zero/context,
  by-value and nine mutations, strict input bytes and empty owned destination.
- [x] Run `.venv/bin/python -m pytest -q tests/test_epoch_decoder_bridge.py`.
  Expected: RED absent API.
- [x] Implement exact interfaces, hash-bound snippet loading, closed mutations,
  bounded compile/run, raw-byte direct decode, exact cohort/value comparisons.
- [x] Run focused then `.venv/bin/python -m pytest -q`. Expected: PASS.
  Commit `test: connect compiled epoch output to full v2 decoder`.

### Task 2: Scope guards and truthful handoff

**Files:** Create `tests/architecture/test_epoch_decoder_bridge_boundary.py`,
`docs/epoch_decoder_bridge_result.md`; add only new-prefix .gitattributes rule.

**Interfaces:** Consumes Task1 interfaces; no new runtime interface.

- [ ] Add old-blob and import/capability guards; execute them against actual tree.
- [ ] Run full/coverage/source/history/assets/lint/format/mypy/build/wheel/native/
  replay and CRLF checks. Expected: PASS, with skips/limits explicitly disclosed.
- [ ] Record PR18 offline-only scope and outstanding25/33/34/9 items; commit;
  one fresh whole-branch exact-head review, C/I one RED→GREEN fix pass if needed.
- [ ] Publish only a new own stacked Draft against feat/lossless-raw-epoch;
  attach; wait exact-head push+PR CI; preserve existing35PRs/main, archive own logs.
