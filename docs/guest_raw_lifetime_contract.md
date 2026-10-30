# Disposable guest raw FD lifecycle prototype

Base PR36 `57b2c942d38f26343bb73fa8cf0f813c58f920a5`. Experimental source patch,
fixed static PID1 driver, tiny Linux6.12.113 image and explicit opt-in QEMU TCG
runner only. Not a production observer, PR35 semantic assembler, PR30 evidence,
scientific estimator, consumer sandbox or vehicle/application authorization.

## Fixed scope / interventions

Three fresh disposable guests: NORMAL, FORCED_LOSS, SMALL_BUFFER. One vCPU,512MiB,
no KVM, network, shared filesystem, host device, monitor or arbitrary payload.
Only fixed memfd_create, dup3, F_SETFD, fork, close/wait operations. Static PID1
opens both experimental proc-control handles before arm. An actual missing control
interface on the pristine kernel is the negative integration case.

The patch adds diagnostic cookie fields and source callbacks. It does not retain
table/file references, change operation results or add locks around target effects.
It necessarily changes structure layout, allocation size, instructions and scheduling.
Read-only evidence collection is **not** unperturbed or naturally timed execution.
Root scope recognition borrows the fixed living PID1's unchanged files_struct
pointer internally; it is not transmitted, not a lifetime ID and not a safe generic
scope registry. This experiment must not be reused with arbitrary root exit,
unshare/exec, sharers or workloads. PID1 is only a fixed control-interface gate,
never persistent task identity. Task lifetime identity is unavailable.

Successful initialized alloc_empty_file and successful new dup_fd namespace birth
receive source-issued opaque increasing cookies. Other constructors/failure paths,
boot/static objects and pre-arm objects remain uninstrumented/unknown. Field0 is
the explicit **UNAVAILABLE cookie encoding**, not an actual zero identity; Python
maps it toNone. Unknown root namespace is never relabeled a birth. Cookies are
bounded experiment-local content, not authenticated allocation issuers. Address
reuse cannot stand in for cookies. Cookie wrap/whole-path behavior is unqualified.

Binding callbacks distinguish INSTALL/CLOSE/FLAGS/REPLACE. Fork copy emits only a
TABLE_NEW result, not per-slot reads or an atomic inventory. No complete geometry,
copy/exec cut, reserved-slot quiescence or source-wide closure is supplied.
REPLACE names the do_dup2/dup3 write path, including writes into unused slots;
it does not assert that the destination was occupied. Old-cookie0 is unavailable,
not evidence of absence (an existing uninstrumented object also has unknown cookie).

FILE_FREE and TABLE_FREE are callbacks **after the selected allocator free returns**,
using only a cookie saved before release. Never dereference a released object.
They do not establish complete reference history or natural destruction time;
later/out-of-window cleanup, other constructors and unobserved sources stay unknown.
Pointer reuse and callback emission may interleave; emission order is not effect
linearization. Monotonic timestamps annotate hooks, not an alignment proof.

## Raw wire and accounting

Fixed textual version1 source frames with exact key sets; metadata identifies case,
release, one-CPU profile and buffer capacity. Events carry emission ordinal, kind,
optional namespace/OFD/old cookie, optional FD, flags and kernel monotonic ns.
`fd=-1` means unavailable, FD0 remains actual0. Zero flags remain actual0.
Frames reject malformed/duplicate fields, unknown stage/version/case/release/CPU,
out-of-range numbers, duplicate/reordered source sequence, truncation and oversize.
Original serial, image, source, configuration, patch, compiler/kernel/driver/QEMU
bytes are bound separately; parser acceptance does not authenticate their origin.

Diagnostic buffer is preallocated128slots. Attempt ordinal is incremented before
fallible reservation. FORCED_LOSS deliberately rejects ordinal2. SMALL_BUFFER uses
capacity2 and observes overflow rejections. Each successful reservation has its
own slot; commit publishes valid with release ordering. No target-effect lock.
These are own-buffer counters, **not BPF ring-buffer counters or NMI-loss proof**.
NMI callbacks are outside this process/task-work experiment and not counted as0.

Local equations: `attempted = reserved + failed`,
`reserved = committed + discarded + pending`, `received = committed`.
Stop disables subsequent emissions and waits existing RCU read-side emitter
sections before reading slots/counters. This is not target quiescence, all-source
arm/drain, hotplug proof or closure of later deferred cleanup. The source can omit
an effect before attempted++, and coherent fabricated histories remain undetectable.
Single-CPU membership follows the built config/QEMU recipe, not a general CPU protocol.

The pure evaluator reports **local accounting balance** separately from **reported
local reservation failures**. A balanced FORCED_LOSS stream is still visibly lossy.
Empty errors or zero own-buffer failures never mean complete/qualified observation.
All9 operational permissions remain false, status BLOCKED, actual **global/overall**
loss and prohibited-operation counts unavailable. Experimental scoped counters
may be observed numbers; never substitute them for global zero.

## Build / execution boundary

Use exact preserved Debian source archive, explicitly recorded available compiler,
owned-prefix build dependencies, actual generated .config, patch and binary hashes.
The build is diagnostic, not qualified input/toolchain/reproducibility closure.
The runner accepts only a fixed case, verifies frozen source/asset bytes before
starting QEMU, and has no arbitrary path, command, source, VM or compiler interface.
No guest ELF executes on the host. Ordinary pytest/offline audit never boots a VM.
Timeout preserves failure evidence and is not a qualified watchdog.

Existing src/compatibility/CI/old evidence/audits/fixtures/experiments and previous
PRs remain unchanged. No H6 estimator/application/owner runtime bridge. Previous
factor/frozen-artifact/vehicle-bounds/fingerprint/watchdog/executor/application
blockers and prior deferred minors remain. No vehicle/Params/controller/cereal/
longitudinal/external AI/upstream PR work.
