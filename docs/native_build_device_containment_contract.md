# Native-build device containment receipt contract (proposal v1)

`native-build-device-containment-v1` is a neutral semantic proposal, not an active
kernel profile, runner, installed Python type, telemetry producer or authority
token. [Design](superpowers/specs/2026-10-30-cpu-device-containment-design.md).

## Policy modes and decisions

| Mode | Meaning | Current adoption |
|---|---|---|
| STRICT_NO_DEVICE_ATTEMPT | Any hardware attempt rejects, including denied opens | Retained current rule |
| CAPABILITY_CLOSED_DISCOVERY_PROPOSAL | Only narrowly proven, no-capability discovery failures may be diagnostic | Not approved/adopted |

Proposed pure evaluator decisions:

- `REJECTED`: one or more typed reasons; no positive inference from missing data.
- `DIAGNOSTIC_EXPECTED_DENIAL_ONLY`: individual event classification, never a
  run-level permission or evidence that the whole trace is complete.
- `CONTAINMENT_RECORD_REVIEWABLE_NOT_AUTHORIZATION`: complete conformant record
  under a separately approved/qualified policy; not execution or Gate A approval.

Synthetic records can exercise decision logic but must retain evidence_kind=
SYNTHETIC and runtime_qualified=false. A caller writing evidence_kind=OBSERVED or
guard_active=true is not trust establishment. A trusted verifier must bind those
claims to the qualified external collector/control plane; no such implementation
exists now. Receipt digest is content identity only, not collector authenticity.

The first proposed implementation is deliberately narrower: the manifest's
`synthetic_case_v1` defines exact `synthetic-native-containment-case-v1` fields for
one modeled discovery child/security-event list. It can return only REJECTED or
synthetic diagnostic classification, never the third run-reviewable state. Its
modeled proof flags are claims in a test, not actual kernel/collector evidence.

## Required envelope and availability

Fields are semantic requirements for a future implementation. Every unavailable
value is null/UNAVAILABLE, not0/false/default. Numeric inputs reject nonfinite,
wrong scalar types (including bool-as-int), invalid ranges and ambiguous units.

| Group | Required content |
|---|---|
| Identity |schema_version, evidence_kind, non-identifying run_id, policy mode/version/digest, collector/verifier implementation digests |
| Source cohort |exact R or preserved applied tree, patch digest, acquisition manifest digest, complete input/loader/generated-code provenance |
| Execution cohort |image/config/Python ABI/toolchain digests, CPU feature exposure/backend, exact command/env allowlist, source/output/cache layout digests |
| Enforcement |observed kernel/runtime/MAC/device/seccomp/namespace state; zero capabilities, no_new_privs, mount/FD inventories, immutable-source proof |
| Trace coverage |capture start before payload, all descendants/exec generations, explicit sequence/clock domain, complete exit/quiescence, lost-event status |
| Resource outcomes |inherited/transferred/opened handles, operation results/effects, exact pseudo-device class, prohibited-capability/write/ioctl/mmap counts |
| Verdict context |independent adoption/qualification references, known missing checks and reason list; no application/estimator permission |

Monotonic time is an integer nanosecond value with an explicit clock domain. Do
not join host/guest clocks using wall time or unproved offsets. Process identity
binds run/namespace generation + PID/TID + observed start/exec generation; PID alone
is not stable and Python object addresses are not identities. No VIN/dongle/route/
GPS/driver/raw-CAN/images, host identity or secret/signing material in receipts.

All current observations in the semantic manifest are unavailable, not actual
zero measurements. Zero successful prohibited handles/effects is a future
structural security requirement, not an observation made by this design.

## Operation receipt

Each operation record separates:

1. Trusted process/stage/lineage/exec identity and sequence/time domain.
2. Requested operation/flags/arguments, explicitly untrusted until bound.
3. Resolved resource kind/object or a kernel-bound private-namespace absence proof;
   resolution provenance and namespace/mount generation.
4. Actual result: completion, errno, FD created/imported, side effect observed,
   independent capture/guard linkage and availability for each.

No string-prefix path approval. Resolved device identity includes type and
major/minor when an object exists; an absent object has no invented inode/device
number and instead requires qualified lookup/namespace binding. A physical node
inside the supposedly private device view rejects preflight. Regular-file or
pseudo-device aliases must still resolve to the same permitted object class.

Unknown final syscall result, FD lineage, resolution, clock, enforcement or event
origin rejects. The observer must protect result provenance and event storage
against payload writes; a post-hoc log hash alone cannot prove completeness.

## Narrow diagnostic proposal

Initial candidate endpoint requests are only exact `/dev/kfd`, `/dev/nvidiactl`,
`/dev/nvidia-uvm`, `/dev/kgsl-3d0`. This is a proposed request-class list, **not an
allowlist granting access** or proof these are all R's possible requests.

An event is diagnostic-only under the proposed mode only if ALL hold:

- Separate policy adoption/qualified backend references verified outside payload.
- Exact immutable source/input/interpreter/argv/env cohort and trusted lineage bind
  it to the reviewed discovery child/stage, not an arbitrary Python process.
- Actual attempted open has only the preregistered O_RDWR or O_RDWR|O_CLOEXEC
  flags; no create/truncate/append/O_PATH, device FD import/reopen or effect.
- Resource/absence binding is authoritative for the sealed private namespace.
- Resolution kind is PRIVATE_NAMESPACE_ABSENCE, or POLICY_DENIED_NO_OBJECT with
  qualified broker proof that no object lookup/operation was continued. The latter
  is an explicit policy refusal, not a fabricated kernel ENOENT/absence claim.
  An exposed PROHIBITED_HARDWARE object contradicts the private-view requirement
  and rejects with ENFORCEMENT_UNQUALIFIED even if its eventual open was denied.
- Enforcement was independently observed active before the attempt and remained
  active; result is proven ENOENT, EACCES or EPERM, FD-created=false, effects=false.
- Complete trace/descendant coverage, no dropped or unmatched records, and no
  successful prohibited capability anywhere in the run.

The errno set alone is never sufficient. A library import failure is a different
event, not a denied device open. A private empty-directory/stat lookup is also a
different operation class, permitted only against the private sanitized view;
never infer that host hardware was absent.

Any new endpoint/flag/operation requires a separately reviewed policy revision.
Do not auto-expand to /dev/dri/*, /dev/nvidia*, USB/VFIO or arbitrary unknown
paths. Under strict mode, even a fully proven candidate denial still rejects.

## Fatal operations and lifecycle rules

These reject even when denied: sysfs enable/unbind/driver_override/drivers_probe,
VFIO/KVM/raw-block access, ioctl/mmap on hardware, GPU render/data nodes outside
the exact proposal, CAN/GPIO/camera/USB control, network/FD passing, privilege/
namespace/MAC/device-rule changes, observer tampering and unmediated async I/O.
All successful prohibited opens/FD imports/effects reject regardless of stage.

After any violation or unknown/lost coverage, trusted supervisor stops the entire
process tree; no retry with broader mounts/capabilities, fallback networking,
source patches, synthetic GPU success or "continue because CPU was selected".
Do not use audit events as an application state machine or runtime supervisor in
the neutral package. No such executable controller exists in this design task.

Required future tests include alias/proc-fd/dirfd/relative-path races, inherited
and passed FDs, PID reuse, thread/clone/exec gaps, observer loss, source/pyc/preload
shadowing, tampered scope/digests and unsupported kernel/MAC/device controls.

## Reason taxonomy (separate from application rejection)

`POLICY_NOT_ADOPTED`, `ENFORCEMENT_UNQUALIFIED`, `SOURCE_COHORT_MISMATCH`,
`INPUT_CLOSURE_INCOMPLETE`, `MUTABLE_LOADER_INPUT`, `PROCESS_PROVENANCE_UNKNOWN`,
`CLOCK_DOMAIN_UNBOUND`, `TRACE_INCOMPLETE`, `TRACE_SEQUENCE_INVALID`,
`RESOURCE_RESOLUTION_UNKNOWN`, `RESULT_UNKNOWN`, `DEVICE_ATTEMPT_STRICT`,
`UNEXPECTED_DISCOVERY_OPERATION`, `PROHIBITED_CAPABILITY_ACQUIRED`,
`CONTROL_OPERATION_ATTEMPTED`, `NETWORK_OR_FD_PASS_ATTEMPTED`,
`OBSERVER_OR_POLICY_TAMPERED`, `CPU_BACKEND_UNCONFIRMED`.

Return every applicable reason in deterministic enum order; an exception label
must never erase a fatal reason. An empty/partial trace cannot be positive.

## Separation and current verdict

The contract does not change H7 receipt/friction estimand, observe independent q,
qualify source/schema/runtime, authorize application, import native/application
code or grant owner proposal capability. All existing false permissions remain.

Proposal encoding: UInt64-like integer ns/sequence/generations, explicit enums,
booleans/null and lowercase SHA-256; sorted compact UTF-8 canonical JSON rejects
duplicate keys and NaN/Inf. Version changes for policy meaning, provenance,
scope/clock/resource semantics or allowed diagnostic classes. Source SHA changes
are separately bound, never automatically compatible. No cereal tags allocated.

No evaluator/collector/guard is implemented. Actual image/host compiler/LLVM/system
closure, model-pickle semantics, remaining transitive audit and runtime containment
are unresolved. Current verdict stays `GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED`.
