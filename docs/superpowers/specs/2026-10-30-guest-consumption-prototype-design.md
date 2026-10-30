# Fixed harmless guest input-consumption producer prototype

Base `c5b824f4f37e05bcac81769f1d01a55a51c26e1d` (PR30). User approved the next
recommendation and delegated ordinary implementation decisions/continuation.
This is actual capture for new fixed harmless fixtures, not a Carrot build,
vehicle execution, qualified executor, immutable input seal or output promotion.

## Intent and author-selected approach

Produce actual stopped-task returned-buffer/file/image observations for a narrow
read/mmap/exec fixture profile, then map them to the unchanged PR30 neutral
receipt. Synthetic records and syscall pointer numbers alone are insufficient.

Alternatives: (1) post-hoc depfiles/hashes do not observe returned bytes;
(2) full kernel file/read/mmap/exec-loader observer remains preferred for future
full closure, but is a larger independently qualified backend; (3) selected
**static C ptrace stopped-buffer prototype plus strict Python consumer** supplies
real bounded fixture evidence now. It is explicitly narrower than (2), not a
replacement, and cannot clear its completeness/authenticity gates.

All choices here are the author's, not an invented user specification. The user
opted out of repeated design/plan approval menus. Inline implementation plus one
fresh independent whole-branch review, one C/I TDD fix pass and no re-review.

## Execution boundary

Reuse the exact prepared QEMU10.0.13 TCG q35/qemu64,1CPU/768MiB,
kernel6.12.113+deb13-cloud-amd64 VM recipe and frozen current-input verifier.
No KVM, NIC, disk, host filesystem share, QMP or hardware passthrough. Fresh
diskless guest per case, serial channel only, fixed180s outer resource timeout
(not a qualified watchdog). No host ptrace/proc/cgroup/BPF/security policy action.
Host uid1000 compiles only the new static C fixture/observer, never runs it.
Guest marker and exact kernel/machine checks prevent accidental host execution.
Actual guest tracing is opt-in, never normal pytest/CI or wheel import.

Use PR29 anchored/bounded `observe_fixed_inputs`/`load_checked_assets` and compare
the frozen snapshot before deriving an image. Do not import unsafe legacy runner
loaders or rely on an earlier observation without checking consumed asset bytes.
New binary/source/profile hashes are additional untrusted content identities.
Missing/drifted inputs fail closed with no download/install/rebuild fallback.
Old source, CI, packages, manifests, evidence, HF fixtures and PRs remain exact.

## C producer

One static ELF has fixed `--trace CPxx` and internal `--payload` modes; no arbitrary
executable/path/command interface. The independent parent observes an unprivileged
uid/gid65534 fixed payload (supplementary groups dropped, no_new_privs), starts
before its exec, uses TRACESYSGOOD/FORK/VFORK/CLONE/EXEC/EXIT/EXITKILL, and never
writes registers, arguments, target memory, results or seccomp state.

Task IDs are monotonic birth generations; exec generations start0 and advance
on actual exec events; fork children bind the exact parent event. Early child
stops are held, not guessed by PID/order. Actual `/proc/task/exe` at the stopped
exec event binds the image, not argv. Parent retains regular-file descriptors to
pin observed objects (dev/inode plus capture ordinal); inode alone is not durable
identity. Full content SHA256/stat is checked at binding, with fixed4MiB/object,
64-object,16-task and10,000-record resource bounds.

READ/pread entry binds the actual stopped-task FD/object and exact current or
explicit offset. On successful return, bounded PEEKDATA reads the returned user
buffer (max4,096 bytes), emits actual bytes as hex, and checks object/offset state.
Zero return emits empty bytes with actual offset, even beyond EOF; unavailable or
negative return never becomes zero. Oversize/unreadable/mutated input aborts the
profile without invented bytes. Read hashes are derived independently by Python
from observed bytes, not from expected fixture data. C full-object SHA256 is
cross-checked against known image/input content; no third-party executable bytes
are published. Post-return user-buffer observation is not a general kernel read
proof against shared-memory/asynchronous/hostile mutation.

Successful file mmap binds extent/object only, never touched/read bytes or a read
hash. Successful fstat is metadata only. Failed operations retain signed negative
results without consumption claims. Shared/untraced/VM/thread clone flags are
unsupported and abort before execution, not silently modified or retried.
Selected fixed fork cases do not have concurrent shared-buffer writers; this is
not a general multithreaded capture guarantee. Kernel exec-loader internal reads,
mmap page touches, asynchronous IO and external writers remain UNAVAILABLE.

Only the observer writes capture frames. Payload stdout/stderr go to a separate
pipe, encoded as payload bytes and never reparsed as records. Fatal errors kill/
reap actual tracees and produce an explicitly incomplete window, or a truncated
capture rejects. No fabricated exit, complete flag or loss count.

## Strict wire and unchanged receipt mapping

Prefix `CONSUMPTION `, JSON `{seq,time_ns,kind,task,image,values}`; explicit BEGIN
version `guest-consumption-prototype-v1`, case ID and PR30 observation clock.
OBJECT records carry capture ordinal/dev/inode/size/full SHA256; BIRTH/EXEC/EXIT
bind task/image lifetimes; READ carries object/offset/returned length/hex; MAP
extent only; META object only; FAILED signed syscall result; ERROR exact reason;
PAYLOAD hex only; END carries declared window completeness and exact counters.
All record shapes/types/counts/sequence/time/clock/lifecycle references validated;
unknown/duplicate keys, nonfinite/coerced scalars, truncation, trailing/interleaved
frames, wrong case/context and unsupported fields reject. Adjacent kernel console
diagnostics are not repaired into records; original bytes are preserved.

Pure `parse_capture(text) -> ConsumptionCapture`; immutable bounded typed events.
`produce_receipt(capture, profile) -> ProducedObservation` maps known full-content
materials to PR30 roles/cohorts and exact task/image lifetimes/use identities.
Profile is untrusted context with BuildIdentity and fixed known material bindings.
No result/authority/estimator/application bridge. `EvidenceKind.OBSERVED_UNTRUSTED`;
input seal/writer witness/outputs/promotions absent. Neutral evaluator remains
REJECTED for missing build/promotion prerequisites even for a matching fixture.

`trace_window_complete` refers only to this declared ptrace window, not full input
closure. Every assessment has overall BLOCKED and all execution/promotion/runtime/
device/policy/candidate/application/owner permissions false; global prohibited
success counts null. Content digest is not authenticity or approval.

## Fixed fixtures and independent checks

- CP01: FD0 reuse; read4 at0, read4 at4, pread3 at8; EOF beyond size; fstat;
  file mmap4,096 beyond EOF without fabricated read evidence.
- CP02: fork/parent-wait then parent read, inherited object/OFD offset and exact
  child task generation. No shared VM/FD-table clone.
- CP03: successful fixed self re-exec then read; actual image generation changes.
- CP04: EFAULT read then actual read; failed call is not empty byte consumption.
- CP05: unsupported CLONE_VM attempt, abort before execution and incomplete window.
- CP06: returned buffer above4,096 bound, explicit incomplete/no invented bytes.
- CP07: payload attempts to print forged capture frames; bytes cannot spoof frames.

Normal CI replays committed **actual** captures and synthetic adversaries, never
starts guests or runs compiled payloads. Actual7 opt-in runs checked against
literal offsets/bytes/identities/exits and unchanged receipt rejection/permissions.
Pure statement>=98%, branch>=95%, target100/100. Full regressions, ruff/format,
strict mypy, C -Werror/static build, source/range hashes, build/fresh wheel/replay,
history/source audits/native192, fresh CRLF, one independent review, own stacked
Draft + exact-head push/PR CI. No full-native/empirical/device readiness claims.
