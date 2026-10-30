# Fixed harmless guest consumption producer prototype

Base PR30: `c5b824f4f37e05bcac81769f1d01a55a51c26e1d`.
Branch: `feat/guest-consumption-prototype`. No prior PR edited or merged.

## Implemented, and what this is not

New static C observer plus seven fixed unprivileged payloads, strict immutable
Python capture consumer and mapping to unchanged PR30 receipts. This is actual
bounded software-guest capture, **not** a general/full-build producer, qualified
executor, kernel-read observer, immutable namespace or promotion backend. The
package is outside the wheel. No compiler/loader/controller/vehicle workload is
run as a target; the host compiles only this new harmless static program and never
executes it. Existing scientific/runtime/application gates remain unchanged.

Same prepared VM: QEMU10.0.13 TCG q35/qemu64,1CPU/768MiB,
kernel6.12.113+deb13-cloud-amd64, no KVM/NIC/disks/host shares/QMP/passthrough.
Fresh diskless guest per case. Fixed180s timeout is resource recovery, not a
qualified watchdog. Host uid1000; all ptrace/proc tracing is inside the guest.
Payload uid/gid65534, supplementary groups dropped and no_new_privs set.
No host security policy, native Carrot/model/service or device-class probe.

The C ELF is924,168 bytes, SHA256
`917f12753aaa7822916ff87691943a723731207af09226e4fb8d68bc192a5b63`.
Content identity is not authenticity or authority. Build/source manifest records
current inputs and the command; host compiler/header consumption is unqualified.
Prepared binary lives outside temporary review logs, at the manifest's fixed
asset path; normal CI does not need it or silently rebuild/download missing assets.

## Actual fixed observations

| Case | Records | Tasks | Execs | Read events | Expected result |
| --- | ---: | ---: | ---: | ---: | --- |
| CP01 | 15 | 1 | 1 | 5 | source `0123`,`4567`,`89A`,EOF at100; metadata1/map1 |
| CP02 | 13 | 2 | 1 | 3 | child image0 then parent image1; offsets0 and4 |
| CP03 | 12 | 1 | 2 | 3 | actual self re-exec; source read in image2 |
| CP04 | 11 | 1 | 1 | 2 | read EFAULT(-14), then actual source read; no fake EOF |
| CP05 | 9 | 1 | 1 | 1 | shared-VM clone aborted before execution, real SIGKILL reap |
| CP06 | 9 | 1 | 1 | 1 | returned-byte bound exceeded, incomplete/no fabricated bytes |
| CP07 | 9 | 1 | 1 | 1 | forged frame remains separately captured payload bytes |

All7 literal fixture checks matched,5 closed observation windows and2 explicitly
incomplete. Counts include successful reads of the fixed guest scope marker;
they are not just source samples, global handle/effect counts or kernel reads.
Actual serial bytes are retained losslessly as base64 inside deterministic gzip;
normal pytest replays them without executing guests. Capture failures retain full
raw bytes, including invalid UTF8/truncation, rather than a repaired success.

## Exact stage / provenance limits

READ is the successful stopped task's returned buffer, bounded PEEKDATA bytes and
current/explicit read offset. Python hashes observed bytes, never expected fixture
bytes. Zero is an actual zero return, including EOF beyond file size; failed calls
and unknown bytes do not become zero. MAP is only an actual file mapping extent,
not touched/read pages; META is only metadata; EXEC binds actual stopped `/proc/exe`
and a new image generation, never argv. Retained regular-file descriptors pin
objects across the window, preventing inode reuse, not privileged content writes.
Full content/stat checks are current observations, not an execution-time seal.

Task generations follow actual parent events, with early child stops held until
the parent binds them. BEGIN is observer setup; the receipt starts at the root's
first stopped observation, not pre-trace bootstrap or an invented birth time.
Initial inherited image history is excluded. Observed timestamps have the explicit
PR30 guest observer clock domain, not kernel-event time or vehicle alignment.
Selected syscall/file observations are not a complete all-syscall/FD ledger.
CP01 FD0 is checked by the pinned fixture; this is not independent general FD/OFD
lifetime/alias qualification. Shared buffers/FD-table clones/threads, generalized
concurrency, external writers, kernel-internal ELF loader reads, mmap page touches
and asynchronous IO remain outside this prototype's proven scope.

`trace_window_complete` concerns only the declared target observation profile;
even a fully observed nonzero exit stays a failed target, not a successful build.
Errors require exact task/image or explicit observer provenance. Missing exit,
wrong clock, loss, malformed framing, unknown object/image and counters reject or
remain explicitly incomplete. Payload stdout/stderr never become observer frames.
No interleaved serial record is repaired. Recovery is not a qualified watchdog.

## Neutral receipt and permissions

Receipts remain OBSERVED_UNTRUSTED, with no input seal, writer witness, outputs or
promotion. The unchanged PR30 evaluator therefore rejects full build/promotion
prerequisites. Actual fixed observations do not become application evidence,
an approved baseline, candidate parameters or an authorization grant.

Overall BLOCKED; all9 build/promotion/runtime/device/policy/candidate/application/
owner permissions false. Global successful prohibited handles/effects null.
Full compiler/native input closure, kernel-observer completeness and collector
authenticity remain unqualified. No H6 estimator bridge or deployed Carrot producer.

## Evidence and verification checkpoint

Kernel source7 files/11 ranges, full SHA256/Git-blob SHA1/range SHA256. Source tar
and authenticated Debian package hashes rechecked against the preserved prior
source receipt: linux-source-6.12 version6.12.113-1. Both source paths are read-only;
no package install, source download, kernel patch or privileged host action.

TDD:37 missing-consumer cases RED; missing runner/image cases RED; actual experiment
missing-producer RED; six author semantic/raw-evidence/start-boundary RED→GREEN
regressions;9 missing published evidence/audit cases RED. Seven actual final-source
guest checks and offline source/range/replay audit passed. Local/global regression,
coverage, wheel/CRLF, independent review and exact-head remote CI are recorded in
the final Draft handoff, not inferred from a producer bool.

Independent review: C0/I3/M1 at exact
`f57e203382ef233108132a6af37453772fdd1242`. Three protocol contradictions fixed
in one author pass: physical frame separators, exact fork image inheritance and
abort-phase observations.19 RED regressions→22 GREEN including positive controls.
No independent fix-head re-review/C0I0 claim. One manifest test-quality Minor is
deferred; see [full review/rulings](guest_consumption_prototype_review.md).

## Retained blockers / next boundary

FIXED_GUEST_CONSUMPTION_PROTOTYPE_IMPLEMENTED;
FIXED_GUEST_CONSUMPTION_CAPTURE_REPLAY_READY.
These do not clear:

FULL_BUILD_CONSUMPTION_PRODUCER_NOT_IMPLEMENTED;
BUILD_CONSUMPTION_CAPTURE_UNQUALIFIED;
INPUT_SEAL_BACKEND_UNQUALIFIED; OUTPUT_PROMOTION_BACKEND_UNQUALIFIED;
EXTERNAL_EXECUTOR_UNQUALIFIED; RECEIPT_AUTHENTICITY_UNQUALIFIED;
GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED; APPLICATION_NOT_AUTHORIZED.

Original Gate A BLOCKED; B/C/D and parked runtime qualification are not started.
Friction runtime producer deployment/qualification, empirical factor/friction
identification, missing frozen artifact, vehicle bounds/fingerprint, runtime
representation and watchdog blockers remain. No Params/controlsd/LatControlTorque/
torqued/cereal/application/writer/candidate/longitudinal/external-AI/upstream work.
Actual input sealing and independent executor/output qualification are still
required before any real build. Ordinary automatic continuation cannot fabricate
those witnesses or broaden host/vehicle execution authority.
