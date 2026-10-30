# Guest input namespace / descriptor handoff design

Next task approved after PR32. This is **design plus synthetic acceptance tests**,
not a runtime backend. Standing user preference: author executes inline without
approval menus, with one fresh whole-branch review. Own stacked Draft authorized;
no old PR merge or host/device execution authorization is inferred.

## Goal and scope

Specify how a future independent supervisor could bind an exact declared DATA
object set, sealed/pinned object generations, stopped consumer task/image/FD-table
cohort and active descriptor lifetimes before admitting any consumption.
PR31 returned bytes and PR32 memfd facts are separate observations: matching
hashes, FD numbers, timestamps or paths cannot join them into a qualified witness.

No new runtime package, C, QEMU run, syscall/FD operation, collector, signer,
namespace/mount/host policy, compiler/Carrot/vehicle/Params/application, PR30
adapter, owner proposal or qualification. Existing src/compatibility/tests/fixtures,
prior evidence and CI remain byte-identical. New audit/oracle lives under tests.

## Approaches and author selection

| Approach | Strength | Remaining cost |
| --- | --- | --- |
| Filesystem namespace with constrained pathname resolution | natural compiler/import compatibility | requires immutable complete search tree, negative lookups, mount/root/proc escape and alias qualification |
| Sealed DATA descriptor bundle with logical-name manifest | small explicit object/FD set; direct lifetime and FD0 checks | does not support ordinary compiler path opens, loader reads, arbitrary FD aliases or dynamic inputs |
| Hybrid filesystem plus descriptor broker | eventual path-based workload support with exact object handoff | combines both proof surfaces and requires a qualified broker/observer |

Author selects the second, **DATA_FD_ONLY**. Logical namespace is a name→object
set, not a Linux mount namespace or proof that all environmental inputs are closed.
Future transport: supervised inheritance through one controlled fixed bootstrap
exec, then actual stopped-image/FD inspection before READY. MFD_CLOEXEC must be
cleared only on the explicit transfer allowlist before that exec; after exec the
supervised bootstrap restores CLOEXEC, independently checked at BIND. dup does
not turn O_RDWR into O_RDONLY: supervisor must obtain/verify actual read-only
aliases of the pinned objects before transfer. No SCM_RIGHTS/socket implementation.
Parent control/serial FDs are not consumer FDs; v1 consumer has only declared
data descriptors, no inherited stdin/out/err/control capabilities. FD0 is valid.
Bootstrap executable/kernel loader bytes stay outside this DATA-only contract.

## Exact abstract interface

`tests.audit.guest_input_handoff_model.evaluate(graph: Any) -> dict[str, Any]`
is a stateless **SYNTHETIC-only reference oracle**, not an observed receipt API.
It returns SYNTHETIC_GRAPH_CONSISTENT or reasoned REJECTED, always overall BLOCKED,
all9 operational permissions false, prohibited-handle/effect counts None.
It never consumes actual PR30/31/32 objects or calls the OS. No boolean, digest
or well-shaped graph establishes underlying truth, collector authenticity or trust.

Graph version `guest-input-handoff-design-v1`; input-set digest domain
`guest-data-input-set-v1`; bundle `guest-data-fd-bundle-v1`; inventory
`guest-data-fd-inventory-v1`. Explicit evidence_kind SYNTHETIC only.

Header context: session_id, attempt_id, namespace_generation, source_revision,
vm_profile_digest, observer_profile_digest, consumer_image_digest,
consumer_task_generation, consumer_exec_generation, consumer_fd_table_generation,
clock_domain, manifest_digest. Each ordered event repeats context_digest.
Exact source SHA is separate from schema version. Object identity is supervisor
object_id + object_generation + pin_generation plus observed dev/ino in this
VM/session while the pin is held; never hash/path/PID/FD/address alone.
Each data binding also names fd, binding_generation, ofd_id + ofd_generation.

Manifest members: name, object_id, object_generation, pin_generation, dev, ino,
bytes, sha256. Names are lowercase ASCII relative logical keys, not host paths;
no traversal, empty/dot segments, backslashes, control/Unicode aliases. v1 rejects
duplicate names, duplicate object keys, same dev/ino aliases and duplicate OFDs.
Distinct objects may have identical content. Manifest is a set sorted by name;
stream events remain ordered. Canonical compact UTF8 JSON sorted keys, explicit
None; NaN/Inf/scalar coercions rejected. Digest means content identity only.

## Required sequence and lifetime rules

`PIN_ALL/SEAL_ALL → STOPPED → TRANSFER_ALL → BIND_ALL → READY → PREAD_FULL/CLOSE → FINISH → RELEASE_ALL → END`

Event: seq, time_ns, context_digest, kind, data. seq starts0 and is contiguous;
single explicit observer MONOTONIC domain, nondecreasing timestamps; equal times
use sequence, never infer cross-clock alignment. Missing fields/None are not0 or
false. Unknown kinds reject; 16 members/4096 bytes per object/1024 events/2MiB JSON are resource bounds,
not empirical safety thresholds. Protocol barrier is a future supervisor obligation,
not a runtime state machine introduced here.

- PIN: exact member object/generation/pin/dev/ino, kept through FINISH and all
  consumer closes. SEAL: same identity plus actual full seal snapshot47, exact
  bytes/hash. FUTURE_WRITE55, chmod1, unavailable, or post-hoc hash equality reject.
- STOPPED: independent pre-transfer consumer inventory must be complete/empty,
  zero unexpected descriptors and a matching inventory content reference.
- TRANSFER: one transfer_generation, canonical bundle digest and the exact whole
  manifest object-reference set. Partial/duplicate/extra transfer rejects.
- BIND: actual post-exec consumer FD snapshot of exact transferred member and
  pin cohort, actual dev/ino, RDONLY, CLOEXEC true, seal47, bytes/hash and full
  FD/OFD identity. No lookup of the latest path/FD/time or inference from argv.
- READY: exact complete BIND set and independently obtained actual FD inventory
  digest, complete coverage/zero extras, same bundle generation/digest; before
  any target consumption. Caller flags/digests only simulate these prerequisites.
- PREAD_FULL: v1 only full-file pread at offset0 with actual returned byte hex
  and length; hash bytes independently against the active bound object. Empty
  file/zero returned bytes is actual zero, not unknown. Partial/stream reads,
  mmap presence/page touches, metadata and exec never substitute. Declared but
  unread objects may close; that is not observed consumption.
- CLOSE: closes that exact active fd/binding/OFD generation. Reads after close,
  stale generations and reused FD references reject. No BIND after READY; v1
  dup/fork/exec/CLONE_FILES/path reopen are unsupported and abort the graph.
- FINISH: active FDs empty, successful exit0, coverage true/drop0; failure/null/
  loss cannot be completed. RELEASE only after FINISH; END only after all pins
  released and as the last event. Missing completion/unknown operation rejects;
  raw partial diagnostics can be retained separately, never repaired as consistent.

## Scientific and runtime boundary

Complete declared DATA set ≠ complete build/system input closure. Exact observer
task/image/FD-table generations and inventories, FD/OFD lifetime observation,
pin ownership, actual permission snapshots, execution barrier and fail-stop
coverage all require future qualified producers. PID reuse, proc reopen, exec
inheritance, clone/unshare and alias behavior require separately pinned source
and actual fixed guest counterexamples before an implementation can qualify.
This task only pins what PR30/31/32 currently establish or lack, not new Linux
transport semantics as empirically proven. No automatic old receipt bridge.

Retain INPUT_SEAL_BACKEND_UNQUALIFIED, GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED,
BUILD_CONSUMPTION_CAPTURE_UNQUALIFIED, RECEIPT_AUTHENTICITY_UNQUALIFIED,
EXTERNAL_EXECUTOR_UNQUALIFIED, OUTPUT_PROMOTION_BACKEND_UNQUALIFIED,
APPLICATION_NOT_AUTHORIZED and all prior empirical/device/runtime blockers.

## Deliverables and acceptance

Normative contract/capture+mapping docs, semantic schema and counterexample
matrix, exact repository Git-blob/source-range references at PR32 base. Pure
synthetic oracle and literal positive/negative examples under tests, strict
offline design audit (audit exit0 is not runtime permission), architecture guards.
Full pytest, lint/format/mypy/build/fresh wheel/CRLF and existing source/native
regressions; no new guest or target execution. One fresh independent whole-branch
review, one author RED→GREEN C/I fix pass, minors deferred; own stacked Draft and
exact-head push/PR CI. Next recommendation is one fixed harmless guest handoff
prototype only, never a real build or qualified PR30 bridge automatically.
