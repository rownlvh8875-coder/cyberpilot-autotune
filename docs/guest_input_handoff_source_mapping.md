# Handoff design source mapping and admission gaps

All references pin repository `rownlvh8875-coder/cyberpilot-autotune` at exact
PR32 base `0652c87c5e1da83d2cf4a3336713b9839e929ae3`, not branch names.
`docs/evidence/guest_input_handoff_design_sources.json` records7 exact Git blobs
and11 semantic line ranges, with byte size/SHA256/Git-blob SHA1/range SHA256.
Audit reads those local immutable Git objects with lazy fetching disabled.
CRLF worktree text is never silently equated to runtime-consumed bytes; these
are source references, not an execution-time input receipt or authentication.

## Reuse classification

| Existing source / unit | Reusable meaning | Missing or wrong scope for this proposal |
| --- | --- | --- |
| PR30 BuildIdentity / BuildMaterial / TaskImage | neutral cohort, generation and stage concepts | no actual FD-table/FD/OFD/pin producer; logical path and hash do not establish identity |
| PR30 InputUse / evaluate_receipts | READ_BYTES vs MMAP_BOUND/EXEC_BOUND/METADATA_ONLY, full-read hash, missing witness rejection | no handoff seal/consumption bridge; opaque input_seal_digest is not trusted automatically |
| PR31 OBJECT + retained regular-file descriptor | local observed dev/ino/size/hash, pinned during its observation window | known-content caller metadata and local ordinals do not identify a PR32 memfd or transfer generation |
| PR31 BIRTH/EXEC task-image sequence | explicit actual image generation within that capture | not full FD-table/OFD lifecycle, controlled inherited-FD inventory or pre-consumption barrier |
| PR31 READ returned buffer | actual bounded returned bytes and range, not merely requested path | partial/stream reads do not automatically satisfy proposed full-file pread; no common sealed pin epoch |
| PR31 proc FD reopen / position | inspected object/position context | observer-side new description/flags are not actual target flags or a general OFD witness |
| PR32 snapshot / new_memfd / seal | actual isolated full seal47 and actual pread-byte hashes | same trusted parent driver, not independent target FD/permission/inventory observation |
| PR32 IS04 | FD0 reuse with identical bytes/mask but wrong pinned object rejects | no consumer-wide lifetime or descriptor-set proof |
| PR32 IS06 | actually bound initial symlink resolution, then changed object after replacement | not an immutable filesystem namespace, mount policy or search-path closure |
| PR32 strict serial execution envelope | exact unique terminated markers and order; no success substring repair | does not join distinct VM runs, clocks, consumer generations or producer authenticity |
| PR32 kernel source manifest | exact Linux6.12.113 seal/mapping reference cohort | no new inherited-FD/CLOEXEC/FD-table/OFD backend qualification from those old ranges |

None of these records is modified or passed into a new runtime adapter.
Design v2 explicitly distinguishes bootstrap and post-exec consumer cohorts,
with an observed predecessor/successor EXEC_TRANSITION. This fixes a proposal
ambiguity; it does not qualify actual kernel inheritance, FD-table changes or
slot/OFD preservation from existing PR31/32 evidence.
PR31/PR32 capture sessions were separate; common-looking CLOCK_MONOTONIC values
are not a shared session/context. No nearest-time/size-hash/path/FD join is allowed.
New proposal IDs and digest domains do not upgrade the old observations.

## Proposed future source qualification work, not performed here

Actual transport needs exact kernel/user-space source pins and harmless guest
evidence for read-only reopen versus dup access mode, FD_CLOEXEC changes through
controlled exec, copied/shared/unshared FD tables, actual target F_GETFD/F_GETFL
or equivalent independent inspection, pin lifetime/OFD equivalence, descriptor
close/reuse, full inventory, denied unsupported operations and observer loss.
Capturing a kernel pointer internally is not a stable exported ID; qualified
generation/pinning semantics must make opaque identities meaningful.

The future supervisor must observe the consumer **before** transfer and prevent
data reads until all post-exec bindings and independently enumerated capabilities
are verified. A READY string from the consumer, complete=true from a caller or a
hash computed over expected bindings does not meet this proof obligation.
Actual prevention/fail-stop is not proved by rejecting a retrospective trace.

## Non-goals retained

No C compilation/new guest run, Linux schema/controller/application edit, actual
namespace or FD transfer, compiler/sysroot closure, actual-consumption bridge,
cryptographic authenticity, execution authority or output promotion. No package
added to the wheel; oracle and read-only audit are test tooling only. Current
DATA_FD_ONLY v1 is not whole-build compatibility and must not be promoted as such.
