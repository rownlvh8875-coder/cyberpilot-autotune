# Guest Input Closure Verifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify fixed guest current source/toolchain inventories and static ELF loader dependencies without claiming historical consumption or immutable execution.

**Architecture:** Frozen logical inventories + strict byte parsers + pure fail-closed report. A separate fixed-path read-only adapter reconstructs images, never executes them. Existing packages/evidence are immutable inputs.

**Tech Stack:** Python3.12 standard library, pytest, existing pinned fixed guest assets.

**Spec:** [binding design](../specs/2026-10-30-guest-input-closure-design.md).

## Global Constraints

- Base `9aeb4aeda3297d25b0df7d5dbb909265847f597a`; previous packages/evidence, src, CI, PR8/9/25/26/27/28 unchanged.
- No compiler/VM/device/Carrot-native execution, subprocess/network/host security changes or broad filesystem discovery. Fixed cached trees and selected source/host tool paths only.
- Content equality and guest static imports are narrow facts, never historical consumed input, authenticity, immutable execution or authority. Overall BLOCKED; seven permissions false and global effect/handle counts None.
- Default CLI exit2/no IO. `--verify-current` read-only fixed paths only. No blessing command or arbitrary roots/commands.
- Implement inline as already delegated; one fresh independent final reviewer only.

## Review Focus

1. Current snapshot/rebuilt image mistaken for historical build/executed input or immutable execution: report always retains those blockers.
2. Symlink/parent substitution, unreadable files and short reads: reject ordinary instability; never follow untrusted host links or promise hostile-host TOCTOU protection.
3. Malformed ELF virtual address/string table or hidden search/audit/filter dependency: bounded byte parser rejects instead of inventing a closed graph.
4. CPIO duplicate/traversal/hardlink/special entry or archive symlink cycle: virtual namespace only, no extraction or target execution.
5. A matching selected inventory mistaken for exact-tree/whole compiler/Python/QEMU closure: scope labels and mandatory blockers cannot be bypassed by report data.

### Task1: Immutable inventories and ELF metadata

**Files:** Create `compatibility/guest_input_closure/{__init__,contracts,inventory,elf}.py`; `tests/fixtures/guest_closure.py`; `tests/unit/test_guest_closure_inventory.py`, `test_guest_closure_elf.py`.

**Interfaces:** `InputEntry(root,path,kind,mode,size,sha256,target)`, `InputSnapshot(entries)`; `parse_snapshot(raw: str) -> InputSnapshot`, `snapshot_digest(snapshot) -> str`, `compare_snapshots(expected,actual) -> tuple[str,...]`; `inspect_elf(data: bytes) -> ElfInfo`. Frozen types; exact integer/bytes/path rules; canonical sorted entries.

- [ ] Write tests: hand-authored byte/mode/link deltas produce literal reasons; duplicate/traversal/unknown keys/None-as-zero reject, field order preserves digest. ELF literals pin interpreter/needed/SONAME, reject truncated/bad/multiple/overlapping header/string bounds, unsupported ABI/search extensions. Expected missing package RED.
- [ ] Run focused tests RED, implement the exact pure interfaces with bounded parsing, run focused+full pytest GREEN.
- [ ] Commit `feat: define immutable input inventories and bounded ELF inspection`.

### Task2: Archive namespace and fail-closed closure report

**Files:** Create `compatibility/guest_input_closure/{archive,evaluation}.py`; `tests/unit/test_guest_closure_archive.py`, `test_guest_closure_evaluation.py`.

**Interfaces:** `parse_image(data: bytes) -> tuple[ImageMember,...]`; `guest_dependencies(members) -> tuple[tuple[str,str,str],...]` raises ValueError on unsupported/missing graph; `evaluate_closure(expected,actual,images:tuple[bytes,...]) -> ClosureReport`. Report derives narrow flags, always retains historical/host-toolchain/host-Python/QEMU-dynamic/immutability/authenticity blockers, permissions false, global counts None.

- [ ] Write literal synthetic images and adversaries for duplicate/traversal/link cycle/escape/hardlinks/truncation/gzip concatenation, missing dependency/interpreter/wrong architecture, RPATH/RUNPATH/audit/filter/unknown executables. Root graph includes busybox/helper/fixture/collector and separate BPF object; init interpreter is explicit.
- [ ] Run RED for missing APIs; implement strict no-extraction parser and fixed virtual resolver; tests GREEN and full suite GREEN. Test matching image still cannot qualify execution/historical inputs; frozen/caller mutation cannot change permissions.
- [ ] Commit `feat: reconcile guest loader graph without granting execution authority`.

### Task3: Fixed read-only adapter, actual current evidence and Draft

**Files:** Create `compatibility/guest_input_closure/{filesystem,fixed,host_main}.py`, new `evidence/current-snapshot.json.gz`; `docs/evidence/guest_input_closure_result.json`, `docs/guest_input_closure_result.md`; `tests/unit/test_guest_closure_fixed.py`, `test_guest_closure_published.py`; `tests/architecture/test_guest_closure_boundary.py`; append only new-specific `.gitattributes` entries.

**Interfaces:** `scan_tree(root_id: str,root: Path) -> tuple[InputEntry,...]`, no-follow bounded stable regular-file reads; fixed selected-file observer separately scoped. `observe_fixed_inputs() -> tuple[InputSnapshot,tuple[bytes,...]]`; `host_main.main(argv) -> int`, default2/no IO, explicit read-only verification prints report and exit2 while overall BLOCKED.

- [ ] Write real tmpdir file/mode/link/add/remove tests, default CLI no-IO test, architecture guards and missing evidence RED. Implement no subprocess/network/write adapter and fixed asset reconstruction only.
- [ ] Observe actual fixed trees/selected inputs and independently parse all24 reconstructed images. Publish exact current hashes/graph/snapshot and precise unavailable dimensions; no historical receipt change or VM boot.
- [ ] Run full pytest/coverage/lint/format/strict mypy/build/fresh wheel/replay, historical audits/native192, fresh persistent-autocrlf tests. Pure statement>=95%, branch>=90%; disclose adapter separately. Verify old references and bytes unchanged.
- [ ] Commit evidence, dispatch one final exact-head read-only reviewer with Review Focus + rulings. C/I -> one TDD fix pass/full rerun; minors deferred.
- [ ] Own stacked Draft base `feat/guest-syscall-fd-collector`, title `Verify guest-only input closure without execution authority`; attach it, require exact-head push/PR CI success, clean tree. No merge/old PR edit. Stop after one next recommendation.

Self-review: Task1 types feed Task2 evaluator and Task3 scanner without operational
imports. Task2 parses actual image bytes, not a producer success flag. Task3
records current snapshot only; missing historical/immutable proof cannot become
a boolean success. All five Review Focus failures have explicit tests above.
