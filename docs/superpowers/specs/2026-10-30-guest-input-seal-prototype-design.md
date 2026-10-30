# Guest-only input object seal prototype

Approved direction: next recommended task after PR31. Implementation is inline;
ordinary feature-branch commits and a stacked Draft PR are authorized. This is
not permission to merge old PRs, modify the vehicle or qualify an executor.

## Binding scope

Test Linux 6.12.113 memfd full object sealing in the already frozen diskless
QEMU 10.0.13 TCG guest. No host execution of the static probe. No host security
configuration, network, disks, shared folders, real build or Carrot workload.
The fixed trusted parent probe records libc return values/errno, fstat object
identity, F_GET_SEALS and actual pread bytes. These are local diagnostic claims,
not independently authenticated workload-consumption or a PR30 seal witness.

Use MFD_CLOEXEC | MFD_ALLOW_SEALING | MFD_NOEXEC_SEAL. Initially F_SEAL_EXEC=32;
full mask adds WRITE=8, GROW=4, SHRINK=2, SEAL=1, giving 47. F_SEAL_EXEC seals
execution mode bits; do not claim universal executable-mapping prevention.
Full seals cover the retained inode, not namespace aliases, private memory,
compiler/sysroot closure, host/hypervisor, outputs, or authority.

Fixed data: `0123456789ABCDEF\n` (17 bytes); deliberate mutation changes byte0
to X. Every read hashes actual returned bytes, never the expected fixture.
Device/inode is local identity only, pinned by an open FD for the capture.

## Fixed experiments

| case | required observation |
| --- | --- |
| IS01 | Full seal; original/dup/reopened writable FDs cannot write; shrink/grow and new shared writable mapping denied; original bytes read. |
| IS02 | Existing shared writable map makes full seal EBUSY, mask unchanged; map mutates backing; after explicit unmap/restore, distinct second attempt succeeds. |
| IS03 | FUTURE_WRITE/GROW/SHRINK/SEAL gives55, no WRITE; existing map still mutates backing; never full-sealed. |
| IS04 | Two identical fully sealed objects; FD0 reused for the wrong object; hashes and masks match but device/inode binding fails. |
| IS05 | chmod0444 does not revoke an existing writable descriptor; drop to uid/gid65534 with no_new_privs, record credentials, write succeeds; this guest's ordinary tmpfs file returns F_GET_SEALS=1, not a write seal. Unavailable/EINVAL is a separate synthetic contract case, never zero. |
| IS06 | Sealed object remains unchanged after pathname replacement; reading replacement is not a read of the expected sealed object. The separate ordinary tmpfs replacement has seal mask1. |
| IS07 | Private writable COW mapping can change private memory while backing sealed bytes remain unchanged. |
| IS08 | Read-only shared mapping from writable descriptor retains MAYWRITE and blocks full seal; unmap then distinct attempt succeeds. |

No silent retries or seal downgrades. Each scenario has a fixed ordered event
grammar; missing/duplicate/reordered/error events reject diagnostic recognition.
Receipt fields are immutable, finite exact integers, strict shaped and bounded.
Wire frames use physical LF, allow CRLF JSON whitespace, reject prefix repair,
duplicates, nonfinite, unknown fields and truncated completion. Canonical digest
is sorted JSON SHA256: content identity, never authenticity or authority.

All decisions remain BLOCKED with nine operational permissions fixed false,
prohibited-operation counts unavailable. Scoped behavior recognition is not
INPUT_SEAL_BACKEND_QUALIFIED. Preserve INPUT_SEAL_BACKEND_UNQUALIFIED,
EXECUTOR_UNQUALIFIED, OUTPUT_PROMOTION_UNQUALIFIED, APPLICATION_NOT_AUTHORIZED,
and all existing parked/runtime/scientific blockers. No PR30 witness bridge.

Python contracts/parser/evaluator are pure, outside the installed wheel.
Image/runner are separate opt-in operational code with fixed case selection,
source/binary/old-input hash checks, timeout and no arbitrary command interface.
Default CLI returns2 without loading guest assets or executing subprocesses.

## Acceptance

TDD pure contract/runner guards; eight actual guest captures committed compressed,
all independently checked against fixed literal expectations; exact kernel file,
blob and range hashes. Full existing suite, source/native regression, lint,
format, mypy, wheel/replay smoke and fresh CRLF clone. Report measured pure
coverage; do not imply C line coverage. One fresh independent whole-branch
review, one author RED/GREEN fix pass for C/I, minors deferred. Own stacked Draft
PR and exact-head push/PR CI; no merge or old-PR modification.
