# Fixed harmless guest DATA-FD handoff prototype

This is an **OBSERVED_UNTRUSTED diagnostic experiment**, not the PR33 synthetic
v2 admission producer, a qualified FD/OFD lifetime observer, a compiler input
closure, a namespace security boundary or an executor qualification. It grants
none of the9 operational permissions. Installed wheel code is unchanged.

## Fixed transport and capture

Frozen diskless QEMU10.0.13 TCG / Linux6.12.113+deb13-cloud-amd64; one CPU768MiB,
no NIC/disks/shares/KVM/QMP/passthrough. Host compiles the harmless static C only;
the ELF is never host-executed. Source/ELF/legacy VM inputs are checked before
the public `capture_cases(tuple_of_fixed_HH_cases)` entrypoint boots anything.
There are no caller executable, command, VM-argument or arbitrary payload options.
The private transport helper is not an adversarial Python isolation boundary.

1. Guest supervisor holds primary sealed DATA memfd and separate RDONLY alias,
   program pin, and (HH02/06) a different equal-byte sealed DATA object/alias.
   Explicit MFD_NOEXEC_SEAL8, all required seals47, no executable-mode fallback.
2. Fixed trusted bootstrap forks, closes its inherited descriptor table, TRACEME
   stops. Supervisor observes actual empty `/proc/pid/fd` and single-thread root.
3. Bootstrap proc-reopens supervisor-held RDONLY aliases, installs FD0 (and fixed
   negative-caseFD3), sets actual target CLOEXEC flags, drops supplementary groups,
   UID/GID65534 and enables NoNewPrivs, then stops before one fixed self-exec.
4. Supervisor observes exact pre-exec object/FD inventory and credentials. It
   attempts pidfd_getfd of actual target FD, retaining the actual OFD where allowed.
   PTRACE_EVENT_EXEC binds the real `/proc/pid/exe` object/hash to the held program.
5. Payload restores CLOEXEC and stops. Actual post-exec snapshots precede local
   READY. A fixed pread syscall is inspected at entry and exit. Returned bytes
   come from the stopped target buffer, not from expected fixture/caller metadata.
6. Actual close, empty still-alive inventory (positive cases), wait/reap, then
   actual supervisor pin releases close the window. Missing END is unavailable.

Atomic here means fixed bootstrap/barrier-consistent snapshot, not a single
install syscall. Trusted root bootstrap/proc reopen, executable image mutability,
unobserved filesystem/metadata/mmap channels and generic task/alias closure remain
unqualified. Point FD snapshots do not prove continuous or whole-input closure.
Unexpected producer errors have probe exit2 or incomplete serial, never repaired.

## Actual identities and unavailable values

Observer-local task generation1 comes from the actual root fork. Exec0→1 comes
from the actual ptrace exec event; no argv, wall clock, Python address or branch
name identity. Raw PIDs and supervisor FD numbers are transient lookup arguments.
Held dev/ino/size/hash identify a pinned local object, not an OFD. Full stat is
compared by the guest; no global object identity or authenticity claim.

Target access/CLOEXEC flags come from **target fdinfo**, not F_GETFD on an observer
duplicate. `/proc/pid/fd/N` reopen witnesses object bytes/seals only. A successful
pidfd_getfd retains the actual target OFD. kcmp KCMP_FILE0 means local equivalence;
positive1/2 means distinct; syscall failure is `null` plus actual errno. No inode,
hash, offset or object-pin equality substitutes for OFD equivalence. ENODATA61
before the optional reference exists means no comparison was made.

FD0 and zero-byte successful read are actual zeros. FD-table generation is always
null; slot observation epoch0→1 is only observed close/dup2 reuse, not a qualified
kernel table/OFD generation. Global prohibited-operation counts and drop count
are null, not zero. Kernel/backend enforcement, log authenticity/loss completeness
and full consumption remain unqualified even when local kcmp succeeds.

## Closed physical wire

Version `guest-data-fd-handoff-observed-v1`, GUEST_MONOTONIC_NS. Exactly one
LF-terminated HFD_EXEC → BEGIN..END → HFD_PROBE_EXIT=0 → HFD_DONE window. CRLF
accepted without repairing other separators. Each `HFD [seq,time_ns,kind,...]`
is one bounded flat JSON array: contiguous seq, strictly increasing observation
timestamps, exact ints (not Bool/Float), explicit null, no NaN/Inf/nested values.
Snapshots describe stopped points, not source-operation timestamps. The frozen
parser/checker shares the runner and offline replay path; digests are content only.

| Event | Fields after generic seq/time_ns/kind |
|---|---|
| BEGIN | version, case, clock |
| OBJECT | label, dev, ino, size bytes, SHA256, seals or null, errno |
| BIRTH | observer-local actual root generation |
| FD | stage, exec generation, target FD, slot observation epoch, dev, ino, size, actual target flags, seals/null, errno, SHA256, kcmp result/null, errno |
| SNAP | stage, exec generation, actual FD count, thread count, UID, GID, NoNewPrivs, FD-table generation null |
| OFD_PIN | target FD, pidfd_getfd libc result/-1, errno; pin acquisition failure also -1/errno |
| EXEC | previous/actual exec generations, actual exe dev/ino/size/SHA256 |
| READY | actual exec generation; fixed local gate only |
| READ | exec generation, FD, slot epoch, offset, requested bytes, actual raw syscall result, actual returned hex |
| CLOSE | exec generation, FD, slot epoch, actual syscall result |
| DUP | exec generation, source FD, destination FD, new slot epoch, actual syscall result |
| DENY | fixed reason, exec generation, attempted/rejected FD |
| REAP | exec generation, EXITED/SIGNALLED, actual exit status/signal |
| RELEASE | parent pin label, actual libc close result |
| END | final exec generation, dropped-event count null |

Limits1024events/64FDs/17returned bytes/4MiB object hashing/1MiB serial are resource
bounds, not empirical/safety thresholds. Host timeout180s is bounded recovery,
not a qualified watchdog. Replays are not freshness/authenticity attestations.

## Seven fixed cases

| Case | Actual diagnostic expected; no qualification |
|---|---|
| HH01 | FD0 full17-byte pread; exact exec/flags/object; close/reap/release |
| HH02 | distinct sealed object with identical bytes/hash; pre-exec object rejection |
| HH03 | undeclared extra inheritedFD3; pre-exec inventory rejection |
| HH04 | read attempted before post-exec READY; deny at syscall entry, no returned READ |
| HH05 | **fault injection** deliberately leaves CLOEXEC before exec; actual FD loss, no READY/read. Normal policy would reject before exec |
| HH06 | **fault injection** two declared distinct objects, actual close0/dup2(3,0); new FD0 CLOEXEC cleared by dup2, slot epoch1, kcmp differs if available; next read denied before effect. Not supported generic alias/rebind behavior |
| HH07 | valid empty sealed object; requested17, actual result0/empty buffer; not missing |

HH02..06 recognized denials are not successful transport; no fabricated READ0.
HH01/07 scoped transport observations still return overall BLOCKED and9false.

## Separation and next boundary

No change to src/compatibility, existing sources/evidence/fixtures/CI, main or prior
PR8/9/31/32/33. No PR30 qualified seal/consumption bridge. PR33 M1/M2/M3 remain
deferred and unmodified. No vehicle, actual compiler/source build, Carrot/cereal,
Params/controller/application/owner proposal, external AI or upstream PR.

Next single task: design the missing **qualified FD-table/OFD lifetime observer**
and its evidence/admission boundary. Local same-OFD tests do not solve generation,
generic alias/task lifecycle, continuous inventory or trustworthy loss accounting.
