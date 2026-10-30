# Fixed Guest Consumption Producer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce real bounded read/mmap/exec observations for seven harmless guest fixtures, map to unchanged PR30 receipts, never qualify actual builds/application.

**Architecture:** Static C ptrace observer/payload; pure strict Python frame consumer and receipt mapper; isolated opt-in fixed VM recipe. No installed-wheel/runtime bridge.

**Tech Stack:** Python3.12 stdlib, C17 static, existing pinned QEMU/kernel/toolchain.

**Spec:** [binding design](../specs/2026-10-30-guest-consumption-prototype-design.md).

## Global Constraints

- Basec5b824f4f37e05bcac81769f1d01a55a51c26e1d, new branchfeat/guest-consumption-prototype. Old source/CI/packages/evidence/HF/PRs unchanged; no merge.
- Only new fixed CP01–CP07 software-guest payloads. No host tracing/security policy, Carrot/native/model/service/vehicle, Params/controller/application, candidate/qualification or upstream PR.
- Frozen QEMU10.0.13 TCG q35/qemu64,1CPU/768MiB/kernel6.12.113+deb13-cloud-amd64; no KVM/NIC/disks/shares/QMP/passthrough. Resource timeout180s, no watchdog claim.
- Frozen input check + anchored byte reads, fixed recipe/binary/paths, no download/rebuild/install fallback. Guest marker/kernel guard; payload uid/gid65534/no_new_privs.
- Bounds4MiB/object,64objects,16tasks,10,000records,4,096returned read bytes; explicit incomplete/abort, never truncate into a valid claim.
- BLOCKED, all9 permissions false, global prohibited counts null, untrusted captures only. No full kernel-loader/read/page-touch/immutability/authenticity claim.
- Inline tasks, one fresh final reviewer on most capable model, one C/I RED→GREEN fix pass, minors deferred, no re-review. No repeated approval menus per user.

## Review Focus

1. Post-return buffer/read offset/file object confused with requested bytes, expected fixture bytes, mmap touches or a failed read; exact zero/None distinction.
2. PID/FD reuse, exec/fork arrival order or an inherited OFD mixes task/image/object generations or advances offsets incorrectly.
3. Payload output or adjacent/interleaved serial bytes forges capture records, completeness/counters or observer identity.
4. Unsafe legacy loader/current hash causes unverified asset execution, arbitrary binary/command/host tracing or old source/evidence mutation.
5. A successful narrow fixture, digest or declared window completeness clears build/full closure/qualification/authority gates.

### Task1: Strict frame consumer and neutral receipt producer

**Files:** Create `compatibility/guest_consumption/{__init__,contracts,wire,producer}.py`; `tests/fixtures/guest_consumption.py`; `tests/unit/test_guest_consumption_wire.py`, `test_guest_consumption_producer.py`.

**Interfaces:** frozen `CaptureEvent(seq,time_ns,kind,task,image,values)` and `ConsumptionCapture(events)`; `parse_capture(text:str)->ConsumptionCapture`; `capture_digest(capture)->str`; frozen `KnownMaterial(material_id,role,logical_path,size,sha256)` and `ConsumptionProfile(identity:BuildIdentity,materials:tuple[KnownMaterial,...])`; `produce_receipt(capture,profile)->ProducedObservation` with `receipt`, `trace_window_complete`, `profile_reasons`, fixed limitations/BLOCKED/false permissions/null counts.

- [ ] Write literal CP01-like frames and synthetic cross-generation/sequence/clock/lifecycle/range/hash/None/unknown/duplicate/forged-payload adversaries; missing API RED. Assert actual byte hashes, not expected bytes substituted by producer. All five Review Focus cases have consumer or Task2 boundaries.
- [ ] Implement bounded immutable models, strict per-kind JSON shapes, canonical content digest, pure causal/image/object/offset/known-content joins into unchanged PR30. Run focused+full GREEN. Commit `feat: consume fixed guest byte observations as neutral receipts`.

### Task2: Static C observer and fixed opt-in VM recipe

**Files:** Create `compatibility/guest_consumption/guest/{probe.c,sha256.h,build_manifest.json}`; `{image,vm_runner,host_main}.py`; `tests/unit/test_guest_consumption_runner.py`; `tests/experiments/run_guest_consumption.py`; new-specific `.gitattributes`.

**Interfaces:** C emits Task1 protocol. `build_image(files:dict[str,tuple[int,bytes]],binary:bytes,case:str)->bytes`; `capture_case(case:str)->tuple[ProducedObservation,str]` preserves raw serial output; host `main(argv)->int` default2/no IO, only `--capture CPxx` invokes fixed runner and prints BLOCKED report then2. No arbitrary command/path/options. `check_case(observation,case)->tuple[str,...]` independent literal fixture checks, used by opt-in experiment.

- [ ] Runner/image/CLI boundary tests RED: unknown/empty cases no IO, new/old asset drift, image contains exact binary/input/scope and no arbitrary init, QEMU argv fixed. Experiment RED asserts missing real C/runner before implementation.
- [ ] Implement SHA256 self-checks, guest-only marker/kernel guard, unprivileged fixed payloads, independent read-buffer/object/exec/fork observation, stdout pipe separation and explicit incomplete aborts. Build C17/static -Wall/-Wextra/-Werror into this plan's own scratch path only.
- [ ] Use anchored PR29 verified assets, derive image without old modifications, run each of CP01–CP07 in fresh fixed guest. Assert CP01 literal `0123`,`4567`,`89A`,EOF at100; CP02 exact child/offset; CP03 image change; CP04 failed negative distinct; CP05/06 incomplete; CP07 cannot forge. Diagnose RED source semantics, no unscoped retries or host fallback. Save original raw bytes, no repair. Commit source/runner after focused+full GREEN.

### Task3: Evidence, source audit, review and Draft handoff

**Files:** Create new actual capture gzip under `compatibility/guest_consumption/evidence/`; `docs/guest_consumption_prototype_result.md`, `docs/guest_consumption_prototype_review.md`; `docs/evidence/guest_consumption_{sources,results}.json`; `tests/unit/test_guest_consumption_published.py`; `tests/architecture/test_guest_consumption_boundary.py`; `tests/audit/validate_guest_consumption.py`.

**Interfaces:** committed capture replay regenerates literal checks and reports; independent source/blob/range SHA256 audit; fixed build inputs manifest, no seal/authenticity. Normal pytest/CI never guest executes.

- [ ] Publish actual capture evidence and precise coverage/unsupported gaps; synthetic malformed/causal/authority adversaries RED→GREEN. Pure>=98statement/95branch; fullpytest, lint/format, strictmypy, staticCbuild, source audits/native192, build/fresh wheel/replay/smokes, fresh CRLF, protected-byte check.
- [ ] Commit exact review checkpoint; one fresh whole-branch reviewer with complete spec/plan/Review Focus/rulings. Reproduce C/I RED, one author fix pass/full rerun; minors deferred and every declined behavior ruled with cost. No re-review or false fix-head C0I0 claim.
- [ ] Own stacked Draft basefeat/guest-build-promotion-receipts, title `Prototype fixed guest input consumption observations`; attach artifact, final exact-head push+PR CI. Record all results/head/rulings/limitations. Ordinary automatic continuation does not authorize actual full Carrot build or fabricate seal/executor evidence.

Self-review: Task1 shapes bind Task2 wire exactly; immutable PR30 types reused,
not modified. Task2 new binary and Task3 hashes mutually excluded from self-hash
cycles. Task3 checks actual capture+literal fixtures, not synthetic-only success.
All five Review Focus boundaries are explicitly tested; no host security action
or general executable interface exists. No seal/runtime/application gate changes.
