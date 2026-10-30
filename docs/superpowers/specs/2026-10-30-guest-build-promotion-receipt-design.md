# Guest-only build consumption / promotion receipt

2026-10-30 (Asia/Seoul). Base PR29:
`bbec08f84d0d08b17075663643ddeba6db46d977`.

## Intent, delegated continuation and limits

The user approved the next recommendation and explicitly allowed automatic
continuation. Continue ordinary repository design, pure implementation, tests,
independent review and own stacked Drafts without another approval menu. This
supersedes earlier stop-after-each-recommendation instructions, not prohibitions
on vehicle/Params/controller/application, host security changes or old PR merges.
There is no new perpetual background automation service.

This work first designs actual-consumption/output-promotion evidence, then
automatically implements the neutral validator and an execution-free preparation
planner. It stops at a genuine unavailable qualified producer/executor/sealing
boundary; automatic continuation cannot fabricate evidence or clear a gate.
No compiler/loader/guest/device/Carrot-native/model execution or new host policy.

PR29 proves current selected content and a static guest import profile, not past
build consumption or execution-time immutability. Its snapshot remains reference
evidence, never a sealed input receipt. Do not modify PR29 or old packages, src,
CI, native patch, current policy or evidence. All existing blockers remain.

## Approaches considered (author selection)

1. Post-hoc hashes/compiler depfiles: cheap but omit failed lookups, loader/linker
   scripts, mmap, generators, lineage and mutation windows. Not proof of closure.
2. **Neutral causal receipt plus independent guest producer architecture**:
   selected. Define exact evidence units and implement pure consistency checks
   now; no producer/immutable namespace/authenticity claim. Testable and isolated.
3. Immediate hermetic rebuild/launcher: would require qualified input/toolchain
   seal, capture/enforcement and output-promotion implementation first. Deferred,
   not replaced by chmod/read-only flags or compilation success.

## Preferred future capture and promotion architecture

Use an independent in-guest supervisor and kernel/file-object observer, outside
the unprivileged fixed harmless build domain. Inputs are prepared from a fully
reviewed source/compiler/header/sysroot/loader/config/environment closure into
an immutable namespace. The producer must start before the build and bind actual
task birth/exec/object generations and consumed read/mmap/exec objects, including
kernel exec-loader reads, dynamic loaders, link scripts and descendants. Ptrace
syscall presence/depfiles alone are not complete consumed-byte evidence.

Build outputs stay quarantined. All writer tasks, writable FDs/aliases and shared
mappings must quiesce before copying into a fresh protected diagnostic bundle.
Bind the final write, quiescence, seal, independent readback and namespace
promotion to one attempt/output generation. Prefer copy-out to a separate sealed
namespace, not in-place chmod. Both snapshots must identify exact bytes/objects;
hash equality does not establish quiescence or independent producer trust.
Promotion is **quarantine→sealed diagnostic bundle**, never install/execute/
application/merge. Produced code is not executed by this contract.

This architecture is a proposal, not an implemented or qualified kernel observer,
mount/cgroup policy, build runner, immutable store, signer or approval authority.
The original1CPU/768MiB software guest and its existing toolchain availability do
not automatically satisfy a hermetic compiler resource/input profile.

## Neutral contract (outside installed wheel)

New pure package `compatibility/guest_build_receipt/`, Python3.12 stdlib only.
Frozen/slotted defensive dataclasses and exact enums; no openpilot/cereal/Params/
application/old runtime imports, IO/network/process/thread/writer/singleton.

- `BuildIdentity`: non-identifying session/attempt IDs; exact source, toolchain,
  recipe, environment and observer digests (None if unavailable); explicit
  `GUEST_TRACER_OBSERVATION_MONOTONIC_NS`. Digest binds one attempt context,
  never wall clock, branch/PID or Python address.
- `BuildMaterial`: stable material ID/object generation, role SOURCE/TOOLCHAIN/
  CONFIG/GENERATED, logical relative path, size/SHA256 and cohort digest. Generated
  inputs require a future causal promotion DAG; v1 diagnoses them unsupported
  rather than silently accepting an opaque origin hash.
- `TaskImage`: task/exec generations, parent task generation, bound toolchain
  material/generation and observed interval. One rooted lineage, consecutive
  image generations starting0, no contradictory overlapping image intervals.
  Events carry exact image identity; clock alone never chooses a latest image.
- `InputUse`: consumption-stream sequence, attempt-context digest, exact task/
  image/material generations and observation time. READ_BYTES has actual offset,
  returned length and independently observed range hash; zero-length read is
  distinct from unavailable. MMAP_BOUND has mapping extent, not proof that bytes
  were read/touched; valid mapping can extend past EOF. EXEC_BOUND identifies
  the actual image object, not a requested argv/path. METADATA_ONLY proves no
  byte consumption. Separate counts; never derive one kind from another.
- `BuildOutput`: output/object generation, logical path, exact size/hash,
  last-write observation and writer task/image identity. No input/output object
  alias; no implicit reuse of an installed or approved executable.
- `BuildCompletion`: observed EXITED/SIGNALLED/None with distinct code/signal;
  complete-sequence/dropped-event claims and four optional witness digests:
  input seal, task trace, consumption trace, writer trace. None is unavailable,
  never zero/default. Caller-supplied claims and references are not trusted proof.
- `BuildReceipt`: identity, sorted material/image/output sets, ordered use stream,
  observed start/finish, completion and SYNTHETIC or OBSERVED_UNTRUSTED kind.
- `PromotionReceipt`: same context/build digest, exact output/generation and
  three agreeing output/staged/sealed byte hashes; distinct staging/destination
  namespace identities; quiesced/sealed/verified/promoted times and three optional
  witness references. Required ordering is last-write<=build-finish<=quiesce<=
  seal<=verify<=promote in the same declared observation clock. No invented delay.

Material cohort roles bind source/toolchain/environment appropriately. Uses bind
existing exact task/image/material generations, finite bounds and ordering. Full
file READ hash must agree with material hash; partial hashes cannot prove full
content by themselves. A metadata or mmap event cannot substitute for READ_BYTES.
External witnesses still need independently qualified capture/verification.

## Pure decisions, encoding and availability

`evaluate_receipts(build, promotions)` returns either
DIAGNOSTIC_CHAIN_CONSISTENT or REJECTED with all deterministic reasons. This is
internal consistency for a promotion candidate, **not promotion eligibility**.
Nonzero/signalled/unknown exit, missing scope/cohort/witness/trace, wrong identity,
unknown source, dropped records, malformed phase order, mutation or missing output
promotion reject. Missing required material fields reject structural construction;
partial receipts may retain None for unavailable context/times/completion/witness.

Every decision keeps overall BLOCKED, build_execution_allowed=false,
promotion_authorized=false, runtime_qualified=false, device_class_qualified=false,
policy_adopted=false, candidate_generation_allowed=false, application_authorized=
false, runtime_accepted=false, owner_proposal_allowed=false; global prohibited
handle/effect counts None. No QualifiedEvidence/AuthorizationGrant relationship.

Versions: guest-build-identity-v1, guest-build-consumption-v1,
guest-output-promotion-v1. Canonical sorted-key compact JSON, unknown explicit,
set-like arrays sorted and event order preserved; reject duplicate/unknown keys,
nonfinite/scalar coercions, traversal, overflow and unsupported enums. Digest is
content identity only. Wire proposal uses UInt64 for times/sequence/generations/
sizes, explicit enum/Bool/null and lowercase SHA256; no cereal tag allocation.

## Automatic next safe unit: execution-free preparation planner

After the receipt design/validator, implement a pure plan that binds the PR29
reference revision/snapshot and lists qualified executor, consumption producer,
input-seal and output-promotion registrations required next. The default CLI has
no IO and exits2; `--describe-plan` prints reference-only BLOCKED requirements,
not a current environment observation, runnable command or permission. Missing
registrations are None, not fabricated receipts. Supplying digest-shaped strings
cannot make execution ready. This automatically continues the recommended work
without crossing into an unqualified executor or security-sensitive operation.

## Verification and handoff

TDD literal synthetic conforming receipt and adversaries: stage substitution,
None/zero, mmap beyond EOF, context/task/object generation drift, clock mismatch,
parent/image gaps/cycles, sequence/drop errors, wrong full-read hash, failed exit,
write-after-finish, unquiesced/mutated/cross-attempt output, same namespace,
missing witness, duplicate records and fake observed-authority claims.
Pure statement>=98%, branch>=95%; target100/100. Full baseline2197 regressions,
ruff/format/strict mypy, build/fresh wheel/replay/source audits/native192, fresh
autocrlf checkout. One independent final review, one author C/I TDD fix pass,
minor deferral, own stacked Draft + exact-head push/PR CI. No old PR changes.
Then continue only if required real producer/immutable executor evidence exists;
otherwise report that concrete blocker, not another approval menu or fake success.
