# Guest-only build-consumption / promotion receipt contract

Version: `guest-build-consumption-v1`; identity: `guest-build-identity-v1`;
promotion: `guest-output-promotion-v1`. This is a neutral **diagnostic contract**,
not a hermetic build implementation, seal, signature or runtime qualification.
The package lives under `compatibility/guest_build_receipt`, outside the wheel.

## Causal units and encoding

| Unit | Exact binding | Availability / interpretation |
| --- | --- | --- |
| BuildIdentity | session + attempt; source/toolchain/recipe/environment/observer SHA256; observation clock | missing digests are null, never defaults |
| BuildMaterial | stable object ID + generation, role, logical relative path, byte size/hash and cohort | paths do not prove object identity; GENERATED is unsupported in v1 |
| TaskImage | task + exec generation, parent task, bound toolchain object, interval | not PID/argv/time-only inference; one root, consecutive images from zero |
| InputUse | contiguous sequence; context digest; exact task/image/material; time | READ_BYTES, MMAP_BOUND, EXEC_BOUND and METADATA_ONLY never substitute |
| BuildOutput | object + generation; path, size/hash, writer task/image, final-write observation | quarantine, not an approved artifact |
| Completion | exit kind/code/signal, trace completeness/drop count, seal/task/input/writer witness references | null != zero/false; opaque witness digest is unverified |
| Promotion | context + build + output generation; output/staged/sealed hashes; distinct namespaces; phase times and witnesses | diagnostic copy-out only, never install/execute/application |

Unsigned64 integers represent nanoseconds, generations, sequence, byte offset,
length and size. Exact int types exclude Bool/Float. Strings carry explicit
clock and enum semantics, lowercase SHA256 and non-identifying opaque IDs.
The clock is `GUEST_TRACER_OBSERVATION_MONOTONIC_NS`; it denotes observer times,
not kernel event time or proven wallclock equivalence. All phase times inherit
the bound build context. No clock conversion or tolerance is invented.

Canonical JSON is compact UTF8 with sorted keys and explicit null. Material,
image and output sets are defensively copied/sorted with duplicate identity
rejection; use streams retain order. Unknown/missing/duplicate fields, scalar
coercions, overflow, traversal, nonfinite values and future enums fail closed.
Arrays are capped at50,000 entries; encoded/parsed envelopes at64MiB. These are
resource bounds, not empirical safety/qualification thresholds. Digest is content
identity only. Semantic/stage/timing/unit changes require a version change; a new
source SHA alone does not. No cereal fields/tags or compatibility claim.

## Consumption-stage semantics

READ_BYTES records observed returned bytes: exact offset, returned length and
range hash. A full-file read must match the bound full hash. A partial read hash
is only a supplied claim; the pure evaluator cannot verify absent bytes. Supplied
observations of the same material/generation/offset/length must agree on the
range hash across all tasks/images; a contradiction rejects as
`CONFLICTING_READ_HASHES`. Different ranges are not compared without their bytes.
Actual zero-length EOF can occur beyond file size and requires the empty byte hash.
Null offset/length/hash is unavailable, not EOF. MMAP_BOUND records an extent,
which can extend past EOF; it is not page-touch/read evidence and cannot carry a
read hash. EXEC_BOUND records the actual image object, not an argv request, and
cannot claim read bytes. Metadata does not prove bytes consumed. Separate counts
remain separate. Exact execution-generation IDs disambiguate shared interval
endpoints; timestamps never select a latest image for a use.

Each use must bind a known material and task/image inside its declared interval,
the same attempt context, contiguous stream order and nondecreasing time. Source,
toolchain and config bind their respective source/toolchain/environment cohorts.
A generated origin hash alone does not establish the required producer DAG;
`GENERATED_INPUT_CHAIN_UNSUPPORTED` rejects such graphs in v1.

## Promotion and pure decision

Required phase order:

`last write <= build finish <= quiesce <= seal <= independent readback <= promote`

All outputs need one exact promotion receipt, matching generations/hashes and
distinct quarantine/destination namespaces. Missing witnesses/times, mutation,
aliasing input identity, failed/unknown exit, dropped/incomplete trace and
cross-context joins reject. The preferred real architecture separately proves
all writers/aliases/mappings quiesced before copy-out; the pure evaluator only
checks supplied claims. Equality of hashes or ordered times does not prove this.

`evaluate_receipts` returns `DIAGNOSTIC_CHAIN_CONSISTENT` or deterministic
reasoned `REJECTED`. Both SYNTHETIC and OBSERVED_UNTRUSTED remain untrusted.
All decisions have overall `BLOCKED`; build execution, promotion, runtime,
device, policy, candidate, application and owner permissions are fixed false.
Global successful prohibited handle/effect counts remain null. No application
QualifiedEvidence, AuthorizationGrant, installed baseline or executor relationship.

## Automatic next unit already implemented

`planning.current_reference_plan()` returns reference-only preparation
requirements for PR29 revision `bbec08f84d0d08b17075663643ddeba6db46d977` and its
`6f854b3c1e6bb1f216092c87f983c553a7ff5419897415f56a007d74e06b5eb7`
snapshot. It performs no new observation. Four registrations are absent:
executor, consumption producer, input seal and output promotion. Even supplying
all four well-shaped digests yields unverified references and BLOCKED, not trust.
Default CLI performs no IO and exits2. `--describe-plan` prints only this plan
and exits2; arbitrary commands/paths/options do not run. No daemon or auto-runner.
