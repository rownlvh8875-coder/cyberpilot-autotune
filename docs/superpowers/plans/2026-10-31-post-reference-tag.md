# Post-reference Tag Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax for tracking.

**Goal:** Add a bounded disposable-guest diagnostic that observes saved raw OFD tags after an existing reference, without qualification.

**Architecture:** Fresh CPRv1 decoder/diagnostic, delta on frozen PR42 source,
static driver and explicit frozen TCG runner. Separate original-byte/source audit;
no actual-to-synthetic or installed runtime bridge.

**Tech Stack:** Python 3.12, pytest, C, exact Linux 6.12.113, static GCC, QEMU TCG.

**Spec:** docs/superpowers/specs/2026-10-31-post-reference-tag-design.md

## Global Constraints

- Base eba2e74759cefa65a941ebce09ce2a4cfa33ec21; preserve all old blobs/assets/PRs/main.
- OBSERVED_UNTRUSTED/BLOCKED; all nine permissions false; global counts None.
- Software-only 1vCPU/512MiB TCG, no network/KVM/sharedFS/passthrough/device/vehicle.
- No added observer reference/lock, no synthetic oracle or PR35/PR30 bridge.
- New files only in guest_tag_snapshot namespace/evidence/docs; narrow attributes.
- Seven cases and release/profile exactly as spec; no automatic build/boot in tests.

## Review Focus

- A saved tuple may be mistaken for lifetime/publication evidence: assert fixed unavailable witnesses and false proof flags.
- A lost consumed-source record may be reconstructed: test absent and contradictory pointer/reference/store links separately.
- Cookie zero may impersonate unavailable raw data or a valid ID: test raw zero with separate logical None.
- Wrong-stage/old CPB bytes may be admitted: test exact closed wire/stage/profile rejection.
- Emission after transfer may re-read file memory: native helper mutation test plus exact source-range audit and actual source review.

---

### Task 1: Closed CPR diagnostic contract

**Files:** tests/guest_tag_snapshot/{__init__,contracts,wire,model,fixtures}.py;
tests/test_guest_tag_snapshot.py.

**Interfaces:** parse_serial(raw: bytes) -> Capture; assess(capture: Capture) -> Decision.
Capture has immutable raw events and exact profile/count/context. Decision has
saved snapshot tuples, available links/reasons and fixed false authority fields.

- [x] Write independent literal wire fixture and failing tests for seven-case framing, raw zero, stages, malformed values, losses and context/order mismatches.
- [x] Run `python -m pytest tests/test_guest_tag_snapshot.py -q`; expect missing API RED.
- [x] Implement decoder and pure diagnostic, never importing old/synthetic estimators.
- [x] Run focused tests and full `python -m pytest -q`; expect all PASS.
- [x] Commit `feat: define unqualified post-reference snapshot diagnostics`.

### Task 2: Fresh source delta and bounded guest captures

**Files:** tests/guest_tag_snapshot/{kernel.patch,kernel.config,image.py,runner.py,guest/init.c};
tests/test_guest_tag_snapshot_runner.py; tests/guest_tag_snapshot/native_probe.py.

**Interfaces:** build_image(binary: bytes, case: str) -> bytes;
arguments(image: Path) -> list[str]; capture(case: str) -> tuple[Capture, bytes, bytes].
Consumes Task1 parse_serial/assess. Native helper test consumes exact new source
helper and verifies scalar copy/zero/by-value behavior under a controlled layout.

- [x] Write runner/image boundary and native-helper behavioral tests; run for missing API/source RED.
- [x] Add delta implementing pointer-only READ/STORE and local raw capture after get_file before STORE, saved-scalar emission after STORE.
- [x] Add static seven-case driver and opt-in fixed runner; fresh source/build under its own assets prefix only.
- [x] Run old-kernel/new-driver negative baseline; expect missing /proc/cptagread and decoder rejection.
- [x] Build fresh exact kernel/static driver and capture all seven cases, preserving original serial/images. Compare outcomes with independent literal expectations, not the PR44 oracle.
- [x] Freeze runner input hashes; rerun focused/full tests; expect PASS. Commit `feat: capture raw tags after existing copy references in fixed guests`.

### Task 3: Frozen provenance audit, architecture and result

**Files:** tests/guest_tag_snapshot/audit.py; tests/test_guest_tag_snapshot_audit.py;
tests/architecture/test_guest_tag_snapshot_boundary.py;
docs/evidence/guest_tag_snapshot_{build,sources,actual}.json;
docs/guest_tag_snapshot_{contract,result}.md; .gitattributes narrow new rules.

**Interfaces:** validate(*, source_root: Path | None = None, verify_assets: bool = False) -> dict.
Consumes frozen Task2 byte hashes/paths and Task1 actual parser/diagnostic only.
No build/boot/output writes in audit or ordinary tests.

- [x] Write failing audit tests for input/serial/source/image drift and no-authority; run missing API RED.
- [x] Implement offline auditor, source/file/range provenance and original-byte manifests; test mutated actual records without upgrading them.
- [x] Add preservation/import guards; verify all old source/test/evidence/CI blobs unchanged.
- [ ] Run full suite, source/native/replay audits, ruff/format/mypy, build/fresh wheel, focused CRLF clone and coverage. Expect PASS; report limitations honestly.
- [ ] Write result/next-single-task; commit `audit: freeze unqualified post-reference guest evidence`.
- [ ] Fresh whole-branch reviewer; one RED→GREEN fix pass for C/I only if needed; ledger all declined judgments/minors.
- [ ] Publish own stacked Draft, attach it, verify exact-head push/PR CI and old remote snapshots. Recoverably archive only this plan workspace; no merge or further task start.

## Self-review

Spec paths, seven cases, release/stages and interfaces agree. Task1 feeds Task2
runner and Task3 auditor; Task2 hashes/captures feed Task3 freeze. The native test
is a scalar-behavior check, not a C/LKMM/runtime safety proof. No unresolved scope
choice requires user input under standing autonomous execution.
