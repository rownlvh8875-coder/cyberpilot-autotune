# Guest-only input closure verifier

2026-10-30 (Asia/Seoul). Base PR28:
`9aeb4aeda3297d25b0df7d5dbb909265847f597a`.

## Intent and authority

The user approved the previous single next recommendation: an immutable
source/toolchain/loader closure verifier for the fixed harmless software guest.
This is read-only offline verification, not permission to build or execute
Carrot/native/model code, run a vehicle/device, alter host security, merge or
refresh older PRs, or qualify friction/application. Ordinary design/inline work
was delegated; choices below are the author's, not a new user-selected design.

The previous collector closes a bounded observed task/FD ledger, not its whole
build/loader trust chain. Existing manifests hash many files but omit some modes,
symlink identities, dependency edges and actual build-consumption receipts.
Reconstructing today's image cannot prove what a historical compiler or loader
consumed. Snapshot equality cannot establish execution-time immutability.

## Approaches considered (author selection)

1. Extend old hash manifests in place: smaller diff, but mutates frozen evidence
   and would obscure the distinction between current and historical evidence.
2. **Separate offline verifier (selected):** immutable neutral inventory, strict
   content/mode/link comparison and byte-parsed guest ELF dependency graph. New
   current-state evidence; precise BLOCKED dimensions stay explicit. No target
   execution, ldd, compiler probing, mounts or installed/runtime dependency.
3. Hermetic rebuild/immutable execution launcher: could collect new consumption
   evidence, but requires a separately reviewed execution/promotion boundary and
   does not retroactively qualify old runs. Not implemented in this task.

## Deliverable and meanings

New `compatibility/guest_input_closure/`, outside the installed wheel:

- Frozen defensive `InputEntry`, `InputSnapshot`, `ElfInfo`, `ImageMember` and
  `ClosureReport`; exact scalar types, ranges, finite data and stable canonical
  content digest. Unknown is not zero or permission.
- Inventory records bind logical root/path, kind, complete permission mode,
  regular-file length/hash or literal symlink target. Relative paths are
  normalized; duplicates, traversal, unknown keys and special host files reject.
  Exact-tree snapshots detect additions as well as removals. Selected-file
  inventories are explicitly not complete directory/search coverage.
- Filesystem adapter uses lstat/no-follow reads, before/after identity checks and
  bounded traversal. No target symlink execution or host path resolution through
  supplied link targets. It detects ordinary changes, not a malicious host/TOCTOU
  attack against writable ancestors or a compromised interpreter.
- Strict bounded gzip/newc archive parser independently observes the derived
  guest image. No extraction, host mknod or subprocess. Reject duplicate names,
  traversal, hardlink ambiguity, malformed/truncated/concatenated archives and
  unknown executable forms. Console/null pseudo-nodes remain metadata only.
- ELF64 little-endian parser observes actual program headers, PT_INTERP,
  DT_NEEDED, SONAME and RPATH/RUNPATH. Native x86_64 executable/shared objects and
  the named BPF relocatable object are separate. No section-name heuristic, ldd,
  loader invocation or target execution.
- Resolve guest interpreter/library dependencies only in the declared virtual
  archive namespace and fixed `/lib/x86_64-linux-gnu` profile. Symlink cycles,
  namespace escape, missing/wrong architecture, unsupported dynamic search/audit/
  filter directives and unknown executable members reject. Closure means static
  ELF import dependencies only, never arbitrary dlopen/NSS/plugin completeness.
- `declared_inputs_match` and `guest_elf_dependencies_closed` are narrow derived
  facts. Overall closure/execution qualification remains **BLOCKED**: historical
  build consumption, complete host GCC/Python/QEMU dynamic inputs, execution-time
  immutability and collector authenticity are not established by this task.
  The graph cannot automatically clear any prior runtime/science/application gate.

## Fixed current-state adapter and evidence

Default CLI exits2 without filesystem IO. Explicit `--verify-current` reads only
fixed repository/cache/selected host-tool paths and the new committed snapshot.
No manifest blessing command, arbitrary command/root, network, subprocess,
thread, timer, subscriber, persistent collector or application import.

Inventory exact cached toolchain and VM sysroot trees. Separately label selected
source/build/host GCC tool files; do not claim full host filesystem closure.
Preserve old4,307-input manifest,5,501-entry VM tree,13-input collector manifest,
old raw captures and their byte hashes. Use the old fixed pure image builder and
verified assets to reconstruct HF01–HF24 images, without booting them. Publish
new snapshot, graph/image hashes and independently recomputed result. These are
CURRENT_RECONSTRUCTION, not historical executed-image or consumed-build receipts.
Published hashes are content identities, not authenticity or authorization.

The operational verifier may return exit2 with precise BLOCKED reasons even
when every current byte and guest static import graph matches. This is success
of fail-closed verification, not a claim that the missing evidence was supplied.

## Constraints and non-goals

Use Python3.12 standard library only; default CI is pure/synthetic and committed
evidence replay, with no workspace-specific input requirement. Native code,
runtime/source packages, old fixtures/evidence/PRs/CI are unchanged. No compiler
or VM run is needed for this read-only task. No host tracing/security/package
installation. No VIN/route/GPS/driver/raw CAN. No estimator bridge, writer, Params,
device, candidate, owner proposal or application authority. Seven permissions
remain fixed false; global prohibited-handle/effect counts remain None.

All retained Gate A/runtime/frozen-development/representation/watchdog/executor/
vehicle/application blockers remain. No historical receipt is upgraded to PASS.

## Verification and handoff

TDD each unit; real malformed bytes and real temporary filesystem changes, not
mock-only assertions. Full baseline2004 and all old regressions, global ruff/
format, strict mypy, build/fresh vanilla+research wheel/replay smokes, source
audits and passive offline native192. Target new pure verifier coverage>=95%
statements and>=90% branches; disclose actual adapter coverage separately.
Fresh persistent-autocrlf checkout. One final independent read-only whole-branch
review, C/I RED→GREEN in one author fix pass; no repeat reviewer. Own stacked
Draft against PR28, append-only commits, exact-head push+PR CI success. No merge.
Stop after handoff and recommend exactly one next task without starting it.
