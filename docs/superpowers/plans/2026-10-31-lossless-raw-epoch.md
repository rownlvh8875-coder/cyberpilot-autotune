# Lossless Raw Epoch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a lossless UInt64 representation design without changing the producer.

**Architecture:** Test-only immutable values and a synthetic fixture codec,
then a read-only source/fixture audit and human future acceptance contract.

**Tech Stack:** Python 3.12 stdlib, pytest, existing source catalog verifier.

**Spec:** `docs/superpowers/specs/2026-10-31-lossless-raw-epoch.md`

## Global Constraints

- Base `72362dcf235f91cbce30501aeeb72b66ee6c124c`; preserve all prior blobs.
- SYNTHETIC_ONLY/BLOCKED; all permissions/proofs false; actual counts unknown.
- No actual producer correction, record adapter, guest run or installed code.
- Large JSON fixture numbers are canonical decimal strings.
- Own stacked Draft publication only; no merge/shared branch/other PR changes.

## Review Focus

- UInt64 max and values above 2^53 must not traverse float or signed domains.
- Unknown and observed zero must remain distinct through encoding and digest.
- A consistent synthetic chain must not become runtime/source qualification.
- Legacy or mixed CPR frames must not be upgraded or accepted as this fixture.
- Frozen audit-source identity must not be claimed as a future binary identity.

### Task 1: Synthetic scalar and representation specification

**Files:** Create `tests/epoch_encoding_design/{__init__,model}.py`,
`tests/test_epoch_encoding_design.py`.

**Interfaces:** Produces `EpochScalar(value: int | None)`,
`encode_design(epoch: EpochScalar) -> bytes`, `decode_design(raw: bytes) -> EpochScalar`,
`content_digest(epoch: EpochScalar) -> str`,
`assess_pipeline(source, saved, buffered, wire, decoded) -> PipelineDecision`.
All scalar arguments are EpochScalar; wire is bytes.

- [x] Write literal-boundary roundtrip, invalid input, immutable value,
  unavailable/zero digest, schema/stage/cohort/legacy rejection and loss tests.
  Pin `4294967296`, `9007199254740993`, `18446744073709551615` exactly;
  a source 4294967296 / saved 0 must report SOURCE_SAVED_MISMATCH.
- [x] Run `.venv/bin/python -m pytest -q tests/test_epoch_encoding_design.py`.
  Expected: RED because the design API is absent.
- [x] Implement the exact interfaces in the pure test-only model.
- [x] Run the focused tests then `.venv/bin/python -m pytest -q`.
  Expected: all PASS. Commit `test: specify lossless raw epoch scalar pipeline`.

### Task 2: Frozen audit and future migration gates

**Files:** Create `tests/epoch_encoding_design/audit.py`,
`tests/test_epoch_encoding_audit.py`,
`tests/architecture/test_epoch_encoding_design_boundary.py`,
`docs/evidence/epoch_encoding_design_cases.json`,
`docs/epoch_encoding_design.md`, `docs/epoch_encoding_design_result.md`.
Modify only new-prefix rules in `.gitattributes`.

**Interfaces:** Consumes Task 1 APIs. Produces read-only `validate(source_root:
Path | None = None) -> dict` and `python -m tests.epoch_encoding_design.audit`.
Uses PR46's existing frozen catalog verifier, not an actual record parser.

- [ ] Write tests that execute literal fixtures, reject fixture mutation and
  assert source-byte checking cannot promote synthetic decisions; add guards
  for old blob preservation and prohibited imports/capabilities.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_epoch_encoding_audit.py`.
  Expected: RED because the audit API is absent.
- [ ] Implement audit and literal fixture catalog; document UInt64 fullchain,
  proposed CPRv2 version migration and actual C/ABI/mutation acceptance gates.
- [ ] Run full pytest, source validators, lint/format/mypy/build, fresh wheel
  smoke, native compatibility/replay and CRLF regression. Expected: all PASS.
- [ ] Record honest verification/status, commit, obtain one fresh whole-branch
  exact-head review; C/I fixes require RED→GREEN and full rerun, minors deferred.
- [ ] Publish own stacked Draft; attach; wait exact-head push and PR CI;
  compare preserved main/PR snapshot and archive only this plan's scratch.
