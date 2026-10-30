# Guest Build/Promotion Receipt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design actual build-consumption/promotion evidence, implement its pure diagnostic validator, then automatically continue to an execution-free preparation planner.

**Architecture:** Immutable neutral receipt objects and canonical encoding; pure causal/identity/phase evaluator; reference-only preparation plan. No executor or trust authority; all operational permissions false.

**Tech Stack:** Python3.12 stdlib and pytest, outside installed wheel.

**Spec:** [binding design](../specs/2026-10-30-guest-build-promotion-receipt-design.md).

## Global Constraints

- Basebbec08f84d0d08b17075663643ddeba6db46d977; old source/packages/evidence/CI/PRs unchanged, no merge.
- User explicitly allows automatic ordinary repository continuation. No vehicle/Params/controller/application, host security, compiler/VM/device/Carrot-native payload execution. No perpetual service.
- Pure dataclasses/functions only; SYNTHETIC/OBSERVED_UNTRUSTED, overall BLOCKED; all execution/promotion/runtime/device/policy/candidate/application/owner permissions false, global counts None.
- Exact integer nanoseconds/generations, explicit observer clock; no wallclock/PID-only identity, floats, unavailable-as-zero, hash-as-authority or mmap-as-read.
- Inline implementation; one fresh independent final reviewer, one C/I RED→GREEN fix pass, no repeated reviewer.

## Review Focus

1. A structurally consistent synthetic/observed claim or opaque witness digest becomes execution/promotion authority: no positive permission path exists.
2. Reused material/task/image/output generation or cross-attempt digest silently joins unrelated evidence: exact cohort, generation and parent binding required.
3. Read/mmap/exec/metadata substitution or unavailable/zero confusion invents consumed-byte evidence: separate kind semantics/counts and source-byte bounds.
4. Writer activity, failed build, wrong namespace or reordered seal/verify/promotion stage qualifies output: complete matching chain required, real sealing still unqualified.
5. Reference-only planning/source hash is mistaken for current observed/qualified executor evidence or automatic continuation crosses old restrictions: explicit reference status and fixed-false operational decisions.

### Task1: Immutable contracts and strict canonical codec

**Files:** Create `compatibility/guest_build_receipt/{__init__,models,codec}.py`; `tests/fixtures/guest_build_receipt.py`; `tests/unit/test_guest_build_models.py`, `test_guest_build_codec.py`.

**Interfaces:** Frozen BuildIdentity(session_id,attempt_id,source_digest,toolchain_digest,recipe_digest,environment_digest,observer_digest,clock_domain); BuildMaterial(material_id,generation,role,logical_path,size,sha256,cohort_digest,origin_digest=None); TaskImage(task_generation,exec_generation,parent_generation,image_id,image_generation,start_ns,finish_ns); InputUse(sequence,context_digest,task_generation,exec_generation,material_id,material_generation,kind,time_ns,offset,length,range_digest); BuildOutput(output_id,generation,logical_path,size,sha256,last_write_ns,writer_task_generation,writer_exec_generation); BuildCompletion(exit_kind,exit_code,term_signal,sequence_complete,dropped_events,input_seal_digest,task_trace_digest,input_trace_digest,writer_trace_digest); BuildReceipt(identity,materials,images,uses,outputs,start_ns,finish_ns,completion,evidence_kind); PromotionReceipt fields per spec. `receipt_digest(value) -> str`; `encode_receipt(value) -> str`; `parse_build(raw) -> BuildReceipt`; `parse_promotion(raw) -> PromotionReceipt`.

- [x] Write conforming literal receipt fixture and strict finite/enum/path/immutability/duplicate/canonical/version/None-versus-zero tests. RED missing APIs; implement only defined shapes/codecs, GREEN focused+full.
- [x] Commit `feat: define immutable guest build and promotion receipts`.

### Task2: Pure causal consistency evaluator

**Files:** Create `compatibility/guest_build_receipt/evaluation.py`; `tests/unit/test_guest_build_evaluation.py`.

**Interfaces:** `evaluate_receipts(build: BuildReceipt, promotions: tuple[PromotionReceipt,...]) -> ReceiptDecision`; decision contains diagnostic status/reasons/read/map/exec/metadata/promotion counts, fixed-false permissions and fixed blockers. No operational imports or mutable global state.

- [x] Write all five Review Focus adversaries: missing/cross-cohort/unknown generation, parent cycle/image gap/clock/time/sequence errors, read/hash/mmap semantics, missing witnesses/drop/exit, alias/mutated/cross-build/output-generation/phase-order/namespace promotion. Expected literal reasons and false permissions, not mirror assertions.
- [x] Run RED; implement identity/lineage/range/phase joins with deterministic all-reason output, GREEN focused+full; coverage statement>=98%,branch>=95%.
- [x] Commit `feat: validate diagnostic build consumption and promotion chains`.

### Task3: Automatically continue to reference-only preparation plan and handoff

**Files:** Create `compatibility/guest_build_receipt/{planning,host_main}.py`; `docs/guest_hermetic_build_receipt_contract.md`, `docs/guest_hermetic_build_capture_design.md`, `docs/guest_build_promotion_result.md`; `docs/evidence/guest_build_promotion_contract.json`; `tests/unit/test_guest_build_planning.py`, `test_guest_build_published.py`; `tests/architecture/test_guest_build_boundary.py`; new-specific attributes only if source hashes need exact bytes.

**Interfaces:** Frozen PreparationInputs with PR29 revision/snapshot reference and optional executor/producer/input-seal/promotion registrations; `assess_preparation(inputs) -> PreparationDecision` always reference-only/BLOCKED/no authority; `current_reference_plan() -> PreparationDecision`; `host_main.main(argv) -> int`, default2/no IO, only `--describe-plan` prints pure requirements then2. No arbitrary command/path or actual producer.

- [x] Before code write tests for missing registrations, digest-shaped fake registrations, reference-versus-observation, no IO/process/authority and preserved old packages; RED then implement pure planner. This is the automatically started safe next unit, not a request for another approval menu.
- [x] Publish semantic wire/capture architecture + synthetic evidence/known blockers, no actual producer/seal claim. Full pytest/coverage/ruff/format/mypy/build/fresh wheel/replay/source audits/native192 and fresh autocrlf, compare old protected bytes.
- [x] Commit result, dispatch one fresh exact-head independent reviewer with Review Focus/rulings; C/I one RED→GREEN pass/full rerun, minor defer.
- [ ] Own stacked Draft basefeat/guest-input-closure-verifier, title `Define guest build consumption and output promotion receipts`; attach, exact-head push+PR CI success. Continue automatically only within authority/evidence; actual missing qualified producer/executor/seal is a blocker, never a fabricated next run.

Self-review: Task1 exact shapes feed Task2 and Task3; current reference cannot
masquerade as observed build identity. Task2 digest links never trust witnesses;
Task3 cannot execute even with all strings present. All five Review Focus classes
have explicit tests. Current narrower generated-input DAG is unsupported, not
silently qualified. No original native-build/device gate is reinterpreted.

Source completion:58dd8ceb797958c10568fbb60cbefb038b6dbaf0; local final2342,
CRLF2342, focused145, pure100/100. Independent C0/I1/M0 atfe2cc6e; I1 fixed
one author pass, no fix-head independent re-review. Final forge checkbox is
recorded by the exact-head CI/Draft handoff rather than a CI-triggering docs loop.
