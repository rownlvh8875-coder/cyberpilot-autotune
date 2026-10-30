# Guest Input Handoff Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an auditable DATA-only namespace/FD lifetime design and synthetic acceptance oracle, not a runtime handoff backend.

**Architecture:** Normative design plus test-only pure graph oracle; separate read-only manifest/Git-blob audit. No runtime package or bridge to existing receipts.

**Tech Stack:** Python >=3.12.3,<3.13 stdlib only; canonical JSON and read-only Git objects.

**Spec:** docs/superpowers/specs/2026-10-30-guest-input-handoff-design.md

## Global Constraints

- Base0652c87c5e1da83d2cf4a3336713b9839e929ae3; preserve all prior source/evidence/CI/PRs.
- DATA_FD_ONLY, SYNTHETIC-only, overall BLOCKED/all9 permissions false.
- No C/QEMU/guest/native target build, host policy, vehicle/Carrot/Params/application or PR30 bridge.
- New oracle/audit under tests, not src/compatibility/tests/fixtures or wheel.
- guest-input-handoff-design-v2 after reviewed cohort fix; observer clock GUEST_HANDOFF_OBSERVATION_MONOTONIC_NS.

## Review Focus

- Matching content with different pinned object or FD/OFD generation must reject.
- A complete caller manifest/inventory digest must not become runtime closure or authenticity.
- Transfer/binding subset, inherited extra FD, early consumption or premature pin release must reject.
- FD0/empty data are real zero; None, Bool-as-int, nonfinite and stale clock/context must reject.
- Successful synthetic full-file pread must not qualify partial read, mmap, exec or old PR31 consumption automatically.

### Task 1: Normative design and synthetic graph oracle

**Files:** Create docs/guest_input_namespace_handoff_contract.md; tests/audit/guest_input_handoff_model.py; tests/audit/guest_input_handoff_examples.py; tests/unit/test_guest_input_handoff_model.py.

**Interfaces:** evaluate(graph: Any) -> dict[str,Any], graph_digest(graph: dict[str,Any]) -> str; pure/test-only. complete() -> dict[str,Any], example(case: str) -> dict[str,Any] and literal CASES tuple(id,status,reason). Graph header/context/member/event fields exactly in spec. Events PIN,SEAL,STOPPED,TRANSFER,EXEC_TRANSITION,BIND,READY,PREAD_FULL,CLOSE,FINISH,RELEASE,END; strict arities/keys; END last. v2 adds explicit bootstrap/post-exec cohorts and the controlled transition after review I1.

- [x] Write independently derived fixtures/negative tests for every Review Focus line, exact false permissions, immutable inputs, canonical set ordering and literal expected reasons.
- [x] Run `.venv/bin/python -m pytest tests/unit/test_guest_input_handoff_model.py -q`; expect missing-module RED.
- [x] Implement minimum pure reference oracle and normative field/event tables; no OS observation. Restrict seal47/read-only/CLOEXEC, whole-set transfer, active exact FD/OFD references, complete inventory and barriers; reasoned failures, no inferred values.
- [x] Run focused and full pytest, expect green; commit `docs: define data-only namespace and FD handoff contract`.

### Task 2: Machine-readable acceptance and source mapping

**Files:** Create docs/evidence/guest_input_handoff_design_{schema,cases,sources}.json; docs/guest_input_handoff_source_mapping.md; tests/audit/validate_guest_input_handoff_design.py; tests/unit/test_guest_input_handoff_design_audit.py; tests/architecture/test_guest_input_handoff_boundary.py.

**Interfaces:** Consumes Task1 evaluate/example/CASES. Produces validate() -> dict[str,object]; default CLI reads only fixed repo manifests and pinned local Git blobs, no runtime execution. Source lookup exactbase/path/blob/range, never normalized worktree-as-consumed bytes.

- [x] Write failing published-audit/mutation/architecture tests; run RED for missing audit/evidence.
- [x] Implement semantic schema/counterexamples/proof obligations and exact Git source references; audit each literal example result and scope flags, unknown/duplicate fields and tampered bindings.
- [x] Run focused/full pytest and offline audit; expect all synthetic cases matched, permissions false, runtime unqualified. Commit `audit: pin handoff design sources and counterexamples`.

### Task 3: Verification, independent review and Draft handoff

**Files:** Create docs/guest_input_handoff_design_result.md; optional review record; update only own spec/plan checkpoint. No old implementation edits.

**Interfaces:** Consumes Task1/2; result statuses DESIGN_READY, RUNTIME_PRODUCER_NOT_IMPLEMENTED and all existing blockers.

- [x] Run full pytest/coverage, ruff/format/mypy/build/fresh vanilla+research wheel/replay/smokes, old source/native192/PR32 replay and fresh exact-head CRLF. Report actual oracle coverage, not OS/C coverage.
- [x] Commit checkpoint; one fresh most-capable reviewer on exact whole branch, with Review Focus verbatim and ledger rulings. C/I author RED→GREEN fix pass/full rerun; Minor deferred, no second review.
- [ ] Publish own stacked Draft `Design guest input namespace and descriptor handoff` on feat/guest-input-seal-prototype; verify final exact-head push+PR CI and preserve old refs. Attach PR via app tool; report acknowledgement honestly.
- [ ] Record final external results in PR handoff/owned ledger, preserve prepared old assets, recoverably archive only this plan workspace, Korean result with every ruling/cost and deferred minor. Recommend one next task, no real build/vehicle.
