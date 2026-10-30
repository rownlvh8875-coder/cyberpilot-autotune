# Guest DATA namespace / descriptor handoff contract — design only

Version `guest-input-handoff-design-v1`. Base PR32
`0652c87c5e1da83d2cf4a3336713b9839e929ae3`. This proposes a future wire/evidence
contract, not a Linux namespace implementation, collector, FD transfer, executable
receipt API, trusted input seal witness or qualified executor. Nothing in this
branch opens/transfers/seals a target FD, builds C, starts QEMU or runs a vehicle.
The executable reference model lives only in `tests/audit`, outside the wheel.

## Selected architecture

**DATA_FD_ONLY**: supervisor retains sealed-object pins, supervises one fixed
bootstrap exec with an exact inherited data-FD allowlist, binds the stopped
consumer's actual image/FD table, verifies an independently enumerated inventory,
then releases a pre-consumption barrier. Only full-file pread and close are in
v1. The logical namespace is a closed declared name→object set, **not** a mount
namespace, pathname-resolution sandbox, whole-environment or compiler closure.

Alternatives: immutable filesystem view suits compiler search paths but requires
qualified mount/root/proc/negative-lookup/alias rules; hybrid broker eventually
supports those paths but adds both proof surfaces. FD-only is the next bounded
design because PR32 established an isolated memfd primitive, not either backend.
Normal path-opening compilers/ELF loader reads/generated headers remain unsupported.

Future supervisor must obtain actual RDONLY aliases of pinned objects: dup of
an O_RDWR FD does not change its access mode. A `/proc/<pid>/fd/N` reopen creates
an observer-side description and **does not establish the target's access mode,
CLOEXEC or OFD identity**. Those need independently qualified actual-target
inspection. Numeric FD/inode/position equality is not a general OFD witness.

MFD_CLOEXEC data FDs cannot survive exec unchanged by accident. The future
bootstrap protocol explicitly clears CLOEXEC only on the selected inherited
data slots before its single controlled exec and restores it before READY.
Actual observed post-exec image, task/FD-table generations and descriptor flags
must agree. The trusted fixed bootstrap is source-bound and observed from before
transfer; any data consumption before READY rejects. Loader/bootstrap internal
reads are not relabeled DATA consumption or complete compiler-input coverage.
No SCM_RIGHTS implementation or arbitrary socket/command/root interface exists.

Consumer v1 has only these data FDs: inherited stdin/out/err/control capabilities
are not silently exempted. Parent logging/tracing channels belong to a different
task and are outside the consumer inventory. A data object may occupy FD0.
Future implementation must demonstrate this actual closure rather than compute
an empty extras count from its own manifest. Runtime closure is still unqualified.

## Identity domains

| Domain | Proposed exact identity | Not an equivalent |
| --- | --- | --- |
| context | session/attempt + namespace generation + source/VM/observer/image digests + consumer task/exec/FD-table generations + clock + manifest digest | branch, wallclock, PID or latest record |
| manifest member | logical name + opaque object_id/object_generation/pin_generation + actual local dev/ino + byte size/hash | hash or pathname alone |
| pinned object | member identity + supervisor-held reference throughout transfer/use/finish | current snapshot or caller registration |
| transfer | context digest + transfer_generation + whole ordered-canonical object-reference set | argv or a subset with matching hashes |
| target FD binding | consumer cohort + fd + binding_generation + actual object/pin + opaque OFD id/generation + flags | FD number or inspector's reopened FD |
| consumption | exact active target binding + full pread returned bytes/length at offset0 | open/mmap/metadata/exec presence |

IDs are non-identifying opaque tokens minted by the future supervisor/observer,
not Python/kernel memory addresses. An opaque label alone proves nothing.
Dev/ino comparisons are VM/session-local while pins are continuously held;
reuse after release requires a new object/pin/namespace attempt, not pooling.
No VIN/dongle/route/GPS/raw CAN/driver identity/model output/images.

## Proposed fields and precision

Root keys: `schema`, `evidence_kind`, `context`, `manifest`, `events`.
The current reference oracle only accepts `evidence_kind=SYNTHETIC`; it is not a
decoder for runtime evidence. A future observed schema/producer must be separately
versioned and qualified. A well-shaped synthetic graph cannot become authority.

Context fields: `session_id`, `attempt_id`, `namespace_generation`,
`source_revision`, `vm_profile_digest`, `observer_profile_digest`,
`consumer_image_digest`, `consumer_task_generation`, `consumer_exec_generation`,
`consumer_fd_table_generation`, `clock_domain`, `manifest_digest`.

Member fields: `name`, `object_id`, `object_generation`, `pin_generation`,
`dev`, `ino`, `bytes`, `sha256`. All members have role DATA by this v1 profile.
The whole declared DATA set is frozen before transfer. A member can remain
declared-but-unread; its existence does not imply consumption.

Event fields: `seq`, `time_ns`, `context_digest`, `kind`, `data`. Sequence starts0,
is contiguous and determines order when timestamps coincide. Time domain is
`GUEST_HANDOFF_OBSERVATION_MONOTONIC_NS`: observer time, not kernel event time,
wallclock, vehicle time or automatically compatible with another VM/capture.

UInt64 exact ints (not Bool/Float) for times, ordinals, sizes, offsets and
generations; Bool exact for coverage/CLOEXEC; lowercase SHA256, exact40-hex source
revision; bounded opaque ASCII IDs. Byte payload is exact lowercase hex in the
synthetic proposal. A future actual encoding may use bytes, but needs its own
version and precision/availability equivalence. No cereal tags/patch are assigned.
There are no floating point signals or tolerances to invent here.

All fields are required structurally. None is explicit unknown and cannot satisfy
a required fact. Empty bytes/size0/FD0/drop0 are real values, never substitutes for
unknown. Partial graphs remain rejected diagnostic material; there is no repair,
latest-value join or synthetic fill of missing evidence.

## Stage semantics

Let K = object_id/object_generation/pin_generation/dev/ino and F =
fd/binding_generation/ofd_id/ofd_generation.

| Event | Exact `data` fields | Required meaning |
| --- | --- | --- |
| PIN | K | supervisor retains exact member, no duplicate/released pin |
| SEAL | K,seal_mask,bytes,sha256 | actual same-object snapshot47 plus exact bytes/hash while pinned |
| STOPPED | inventory_digest,complete,extra_fd_count | stopped consumer before transfer; independent complete empty FD set |
| TRANSFER | transfer_generation,bundle_digest,members | atomic whole object-reference set, no subset/duplicates/extras |
| BIND | K,F,transfer_generation,access_mode,cloexec,seal_mask,bytes,sha256 | actual target RDONLY/CLOEXEC=true; exact transferred object/epoch, no FD/OFD alias |
| READY | transfer_generation,bundle_digest,inventory_digest,complete,extra_fd_count | all BINDs plus independent whole actual consumer inventory, same transfer |
| PREAD_FULL | F,transfer_generation,offset,returned_len,returned_bytes_hex | active exact binding; offset0, full size; hash actual returned bytes |
| CLOSE | F | closes that exact active descriptor generation |
| FINISH | exit_kind,exit_code,complete,drop_count | all data FDs closed; EXITED/0 with coverage true/drop0 |
| RELEASE | object_id,object_generation,pin_generation | only after FINISH, once per held pin |
| END | empty object | last record, every declared pin released |

```
PIN/SEAL all → STOPPED → TRANSFER all → BIND all → READY
  → (PREAD_FULL / CLOSE)* → FINISH → RELEASE all → END
```

The phases are **contract obligations**, not a new runtime state machine.
Atomicity means a barrier-consistent whole-set snapshot, not one Linux syscall:
target FD installation can be sequential only while consumer data consumption
is stopped; intermediate reads cannot become a successful atomic handoff.
Unsupported operations or loss must make a future supervisor stop/abort before
claiming consistency; a retrospective graph rejection is not a proof that their
side effects were prevented. Enforcement/executor/watchdog qualification remains
separate. v1 rejects dup, fork/clone/CLONE_FILES, exec, open/reopen and rebind after
READY. CLOSE followed by stale read rejects; FD reuse requires a future extension,
not a guessed latest binding. Multiple distinct objects can have identical hashes.

Seal47 is the exact PR32 cohort: WRITE/GROW/SHRINK/SEAL plus initial EXEC mode seal.
55 lacks WRITE;1 is only SEAL; neither is full. Other masks, even a kernel-valid
full63, are outside this profile, not automatically unsafe or silently equivalent.
SEAL before PIN, changed generation, early RELEASE or later seal success cannot
retroactively prove an earlier interval. Existing shared-writer mappings need
kernel seal rejection/qualified lifetime handling, not chmod or post-hoc hashes.
Private COW memory is not sealed backing-object immutability or vice versa.

## Canonical content identity and resource limits

All JSON object keys sorted, compact UTF8, explicit unknown, NaN/Inf rejected.
Member set sorted by logical name; transfer refs sorted by object_id/generation;
inventory rows sorted by FD. Event order is never sorted away. Logical keys are
case-sensitive lowercase ASCII relative segments `[a-z0-9][a-z0-9_.-]*`, no empty,
dot/dotdot/backslash/absolute/Unicode alias. Duplicate names/object/dev-ino aliases
reject; no invented filesystem normalization.

- manifest_digest = SHA256 canonical `{schema:guest-data-input-set-v1,members}`.
- event context_digest = SHA256 canonical context including manifest_digest.
- bundle_digest = SHA256 canonical `{schema:guest-data-fd-bundle-v1,context_digest,transfer_generation,members}`.
- inventory_digest = SHA256 canonical `{schema:guest-data-fd-inventory-v1,context_digest,bindings}`.
- graph digest = canonical whole graph with member-set sorting only.

These are content references, never authenticity, access control or authorization.
Each graph is standalone; it provides no global registry, freshness or anti-replay
guarantee. A future trusted producer must mint/bind new attempt generations.
Actual independent FD inventory **cannot be generated solely from the expected
BIND set**. The oracle can only compare simulated references; even all matching
digests/complete flags do not prove that no other real FD existed.

Bounds16 members,4096 bytes/member,1024 events,2MiB JSON,255-character logical
names,96-character opaque IDs are parser/profile resource limits, not vehicle,
scientific, excitation or safety thresholds. Semantic/unit/timing/cohort changes
require schema version change; source revision alone is independently carried.

## Proof obligations and disposition

| Obligation | Current material | Verdict |
| --- | --- | --- |
| complete declared DATA manifest | frozen synthetic set/digest | design only, not complete build input closure |
| continuously held object pins/full seals | PR32 isolated trusted-driver checks | separate captures, no consumer witness |
| actual target image/task/FD-table/OFD generations | partial PR31 process/object observations | general FD/OFD backend unqualified |
| stopped pre-consumption barrier and inherited FD audit | no producer | NOT_IMPLEMENTED |
| independent complete actual FD inventory/coverage | no producer | NOT_IMPLEMENTED, caller flags not proof |
| full returned-byte observation in exact same lifetime | PR31 narrower separate capture | no automatic old receipt join |
| authentication/executor/watchdog/output promotion | absent qualification | BLOCKED |

Synthetic oracle status SYNTHETIC_GRAPH_CONSISTENT means only internal consistency
of the proposal, never eligibility or runtime readiness. REJECTED is diagnostic.
Both retain overall BLOCKED and all9 permissions false, prohibited counts None.
No PR30 input_seal_digest is populated and no old type is changed.

Next implementation must first demonstrate fixed harmless guest cases for the
new transport, initial/post-exec inventories, actual flags/OFD lifetime, close/
reuse, early-read denial, mismatch/loss/abort and pin release. No kernel transport
claim is empirically qualified by this design branch, and no real build/vehicle
should start from it. Existing parked/empirical/vehicle/application blockers remain.
