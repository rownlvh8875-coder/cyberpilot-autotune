# Guest Input Seal Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Observe full memfd object seals and their failure boundaries in a fixed harmless guest.

**Architecture:** Pure immutable framed capture contract and fixed-case diagnostic evaluator. Separate static C parent probe, derived diskless image and opt-in fixed runner. No workload/PR30 witness bridge.

**Tech Stack:** Python >=3.12.3,<3.13, Linux6.12.113, static C17, QEMU10.0.13 TCG.

**Spec:** docs/superpowers/specs/2026-10-30-guest-input-seal-prototype-design.md

## Global Constraints

- Fixed IS01..IS08 only; guest-input-seal-v1; 17-byte fixed data.
- No host probe execution, real build, Carrot, vehicle, Params or old PR changes.
- Pure package outside wheel; all nine permissions false and overall BLOCKED.
- Local object seal observations are not full namespace/input closure qualification.
- Preserve unavailable versus zero, FD0, actual returned read bytes and pinned object identity.

## Review Focus

- Same bytes/seals on a different inode must not satisfy expected object binding.
- Failed EBUSY attempt must not inherit a later successful seal epoch.
- FUTURE_WRITE-only and chmod must never be recognized as full seals.
- Prefix/control-separator repair and incomplete captures must not become complete evidence.
- Private COW mutation must not be confused with backing-object mutation or immutable process memory.

### Task 1: Pure capture and scoped decision

**Files:** Create compatibility/guest_input_seal/{__init__,contracts,wire,evaluation}.py; tests/unit/test_guest_input_seal_contract.py.

**Interfaces:** Produces parse_capture(text: str) -> SealCapture, capture_digest(capture: SealCapture) -> str, evaluate(capture: SealCapture) -> SealDecision. Records have seq/time_ns/kind/label/values; SNAP stores dev,ino,size,sha256,seal-mask-or-None,seal-errno,mode; OP stores signed libc result and errno; BIND stores expected dev/ino and actual dev/ino/fd; LOCAL stores private byte value. Capture stores tuple events. Decision stores case, scenario_recognized, object_seal_observed, reasons, overall BLOCKED and fixed-false permissions.

- [x] Write tests for immutable defensive copies, FD0/None, strict types, complete ordering, duplicate JSON, separators, content digests and each Review Focus adversary. Literal synthetic event fixtures, not producer-generated expectations.
- [x] Run `.venv/bin/python -m pytest tests/unit/test_guest_input_seal_contract.py -q`; expect missing-module RED.
- [x] Implement strict structural shapes and exact per-case grammar in contracts/wire/evaluation.
- [x] Run focused tests and full pytest; expect all pass. Commit `feat: define scoped guest input seal evidence`.

### Task 2: Fixed guest probe and execution boundary

**Files:** Create compatibility/guest_input_seal/{image,vm_runner,host_main}.py, guest/probe.c, guest/build_manifest.json; tests/experiments/run_guest_input_seal.py; tests/unit/test_guest_input_seal_runner.py.

**Interfaces:** Consumes Task1 parser/evaluator. Produces capture_cases(cases: tuple[str,...]) -> tuple[tuple[SealCapture,bytes],...], build_image(files,binary,case) -> bytes, main(argv: list[str] | None=None) -> int. Only CLI --run-prepared-guest --case ISxx or --all-cases, no command/path override.

- [x] Test fixed image selection, default CLI2/no I/O, argument rejection, no disk/network/share/KVM QEMU arguments, source/binary binding validation and opt-in boundary. Run focused tests; expect missing implementation RED.
- [x] Implement eight fixed C scenarios, exact phase events, guest marker/kernel guard, retained descriptors and actual bytes read. Compile -std=c17 -O2 -Wall -Wextra -Werror -static to new prepared asset directory; never run it on host.
- [x] Implement hash-bound manifest, checked legacy input loader, fixed derived image and bounded runner.
- [x] Run runner tests/full suite. Execute eight actual guest cases, compare literal decisions; preserve original raw serial bytes. Commit `feat: probe full input object seals in fixed guest`.

### Task 3: Source evidence, audit and handoff

**Files:** Create docs/guest_input_seal_prototype_result.md, docs/evidence/guest_input_seal_sources.json, compatibility/guest_input_seal/evidence/actual-captures.json.gz, tests/audit/validate_guest_input_seal.py, tests/architecture/test_guest_input_seal_boundary.py; append own .gitattributes entries.

**Interfaces:** Consumes Task1/2; audit validate(kernel_source: Path | None=None) -> dict[str,object]. No qualified build/seal/consumption bridge.

- [x] Test committed source/capture audit tamper rejection and architecture boundaries; run RED, then implement audit/manifests. Replay all eight captures and source ranges; expect eight recognized diagnostics, four scoped object-seal positives, all BLOCKED.
- [ ] Run full pytest/coverage, ruff/format/mypy/build, vanilla wheel/replay and knowledge/owner/science/friction smokes, historical source/native192, fresh exact-head CRLF clone; expect green, report actual coverage.
- [ ] Commit evidence/results, dispatch one fresh independent whole-branch review at exact head. C/I: author RED/GREEN fix pass and rerun full suite; minors deferred.
- [ ] Publish own stacked Draft PR against feat/guest-consumption-prototype, wait exact-head push and PR matrix, record actual results without claiming qualified executor or old-PR merge. Commit append-only; handoff in Korean with all rulings/deferred minors.
