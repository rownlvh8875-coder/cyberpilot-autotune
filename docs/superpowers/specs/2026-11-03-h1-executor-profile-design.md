# H1 executor isolation / FD / supervision profile — preregistration

## 1. Scope and status

2026-11-03 KST. Base:61245f6bbf3fdbc3d14ce8c93ff7349234da46f7.
This is a five-new-document semantic preregistration,not an implemented executor,
an executable content freeze,or formal ENTRY R/Q/I/R'. Status BLOCKED;all nine
permissions in semantics.json remain false;integrated_admission=false;
source_capture_atomicity=NOT_ESTABLISHED;HISTORICAL_REPLAY remains UNAVAILABLE.
The user delegated routine choices;decisions here are the author's calls,not
user-granted application authority. No real historical O/D commands run here.

Keep two distinct profiles:

- H1_EXECUTOR_ISOLATION_DESIGN_V1:requirements for a future historical executor.
  This document registers semantics only. Missing content/prerequisites forbid H.
- H1_SYNTHETIC_CONTAINMENT_V1:the next buildable development-only slice,limited
  to repository-owned toy cases in new private directories. Its strongest result
  is SYNTHETIC_OBSERVATION_COMPLETE,never H admission or runtime qualification.

No product source,old metadata,CI,guards,PRs,main or earlier worktrees change.
No vehicle,Params,controller,cereal/schema,VM/guest,application/owner/estimator,
longitudinal,external AI,network publication,HF,push,merge,rebase or force-push.
Domain build_execution_allowed=false does not prohibit ordinary development
regression tests;it cannot authorize a vehicle/native-build/application workflow.

## 2. Approaches and evidence boundary

| Approach | Decision / tradeoff |
|---|---|
| Adopt throwaway probe as H runner | Rejected:FD leak demonstrated;filter/resources/closure are incomplete. |
| Privileged Docker/host fallback | Rejected:broader authority;daemon never tested;no fallback permission. |
| Strict Bubblewrap candidate,first a closed synthetic harness | Selected:observed unprivileged primitives,small inspectable surface;H stays blocked. |

External references and raw hashes are in sources.json. They are local observations
on one Linux6.18.57 x86_64 worker,not authenticity,independent custody,or universal
kernel proof. Bubblewrap0.12.0 is a candidate,not a qualified security boundary.
The23assertions in the old archive were bounded observations,not this profile's
30planned acceptance cases. None of EP-001–030 is executed by this design task.

Observed:readonly toy file write EROFS;main/descendant socket EPERM;NNP1,
CapEff0,Seccomp2;distinct namespaces;missing required mount prevented payload;
one setsid heartbeat stopped and owned helper reaped descendants after timeout.
Counterexample retained:explicit O_RDWR pass_fds wrote24bytes into its own toy
control file despite readonly mounts. Hardened pass_fds excluded it:EBADF.
This was a launcher policy error,not a Bubblewrap vulnerability verdict.

## 3. Trust model and unresolved real-H prerequisites

S trusts the small pinned fixture,launcher,Python/tool binaries and worker kernel.
It tests particular effects;it does not execute arbitrary caller code or promise
hostile-native-code containment. /usr and Python remain broad readonly runtime
inputs;their full transitive closure was not frozen by the old probe. Parent
credentials/proxy guards remain untouched;never dump/hash credential values.
Children receive no credential values. If a provider requires a child guard that
cannot coexist with a credential-free environment,return UNAVAILABLE;do not
remove or bypass that guard or attempt direct egress.

H additionally requires every item in semantics.json's real_H_prerequisites.
Unresolved values remain null/UNAVAILABLE,not permissive defaults. In particular:

- Freeze/review complete executor/bootstrap/filter/toolchain/dependency bytes,
  materialized six argv/origin/module sets,full O and additional D case inventories,
  private complete HEAD/index/Git graph/reference objects. Do not edit old H1/C1.
- Specify and independently review a complete syscall/enforcement policy and
  trust model. The toy default-ALLOW denylist is NOT an H policy;alternative
  syscall paths,io_uring,native/kernel attacks remain unqualified. Do not invent
  an allowlist by guessing syscall names. Missing policy means no H launch.
- Supply an enforceable aggregate process/memory/scratch/output resource boundary
  with exact positive budgets. Current cgroup root is not delegated to UID1000;
  no other delegation has been established. RLIMIT_AS/CPU/FSIZE/NOFILE are
  per-process,not aggregate containment. No NPROC or cgroup claim is made.
- Establish observed directory/tree/FD/descendant protection and cleanup under
  the frozen workload,then separate actual scope authorization and ENTRY adoption.
  Hashes,booleans,H1 STRUCTURAL_RECORD_MATCH and green current tests cannot do so.

All old H1 prerequisites,HR/HC obligations,D01–D04,project/application blockers,
ACTUAL_Q_I,EXACT_I_CI,ENTRY_GUARD_INTEGRATION and STACK_ADOPTION remain open.
This registration neither changes their meaning nor fills their missing evidence.

## 4. Mount and execution contract

Required child shape:setpriv --no-new-privs followed by pinned /usr/bin/bwrap;
unshare user,pid,net,ipc,uts;uid/gid1000;cap-drop ALL;disable-userns;
assert-userns-disabled;die-with-parent;new-session. No --try,root/sudo,daemon,
host-network/repository/socket bind,ambient PATH,shell command or retry fallback.
Fresh mount namespace is mandatory. Internal /proc is for the new PID namespace;
minimal /dev and private /tmp are not host device/temporary-directory grants.

S mounts only /usr readonly,its /bin,/lib,/lib64 symlink aliases,the pinned Python
home readonly,the closed fixture readonly,a NEW owned protected directory tree
readonly and a different NEW owned scratch directory writable. Fixture leaves
hold SYNTHETIC_ONLY_PROTECTED_V1\n. No old repository/evidence enters the sandbox.
Directory write/rename/unlink/link and descendant attempts require new tests;
the old EBUSY file-mountpoint observation does not satisfy this requirement.

The future H mount list is unavailable until content freeze. It must keep audited
O/D/reference trees,objects,index,HEAD readonly while preserving their complete
graph and original tests' scratch effects. Preparation is separate from H;
no auto-fetch/install/build,patched ROOT,current helper or reduced test set.
Never infer O compatibility from C1's D-only attribute profile.

Only owned exclusive run roots,created0700 with no preexisting/symlink component
under a supplied existing owner directory,are writable. Do not delete/reuse
basetemp,clean old runs,or follow caller paths into old subjects. Directory-handle
relative operations/no-follow checks prevent accidental symlink substitution;
they are not an authenticity or same-UID adversary/ABA proof. Record that limit.

## 5. FD contract:mounts are not enough

At each trusted exec boundary close_fds=True. stdin is freshly opened /dev/null;
stdout/stderr are fresh bounded pipes,never inherited terminal/files/sockets.
For the supervisor→bwrap launch,the ONLY pass_fds entry is a sealed seccomp
memfd holding exactly the registered S bytes. Use memfd_create(ALLOW_SEALING),
write,rewind,apply WRITE/GROW/SHRINK/SEAL seals and verify;otherwise UNAVAILABLE.
The old unsealed memfd is reference-only. No status FD is required in S-v1.
The helper's outward result uses its own stdout pipe;control pipe is not passed
to the payload. Verify the filter FD is consumed/closed before payload execution.

Do not pass source/scratch/directory/O_PATH/RW-file/socket/namespace/pidfd/secret
FDs. Internal pidfds stay in supervisor. FDs0–2 are the declared pipe/null roles;
numeric values alone are not identities. At the trusted launch boundary record
role,type,access mode,dev/inode and sealing state for controls,without content or
private target paths. Validate fresh owned handles,not a caller's role label.
Payload's own newly opened descriptors are not inherited leaks.

The closed S FD-negative case intentionally violates this rule ONLY through a
private test helper using one newly created control file. It must reproduce the
write and then show normal launch cannot access that object. Its result is
EXPECTED_UNSAFE_CONTROL,never a successful safe launch. No public pass_fds knob,
environment switch or alternate profile may enable that exception in the runner.
FD reuse must compare object identity;EBADF at a once-used number alone is not a
complete FD inventory proof. Include a second nonallowlisted FD and a socket case.

## 6. Process supervision and output

One fresh,non-threaded supervisor process per S case. Only this helper becomes a
subreaper;the main worker is not changed. The controller retains its Popen handle
and pidfd. The helper owns the bwrap Popen handle,pidfd and a new process group;
it waits/reaps only its own children. No global process scans or arbitrary kill.
Require pidfd_open support;missing means UNAVAILABLE,not numeric-PID fallback.
Pidfds and parent handles stay open through reap,preventing PID reuse ambiguity.

Use monotonic deadlines and nonblocking concurrent stdout/stderr reads in4096byte
chunks. Retain at most65536combined bytes;the first excess byte triggers
OUTPUT_LIMIT. Count bytes,not decoded characters;preserve stream labels and
truncation,without pretending to know unconsumed bytes. Never wait for EOF before
checking deadlines:descendants can hold pipes open after the direct child exits.

On timeout,output excess,nonzero exit or controller exception,preserve that first
error,request stop,then SIGKILL only the owned child/group after checking pid>1,
matching pidfd/open handle and getpgid(pid)==pid. The unreaped leader cannot be
reused. Use --die-with-parent and PID namespace teardown for setsid descendants;
group kill ALONE is not sufficient. Reap adopted children under a2second cleanup
deadline. Cleanup failure adds CLEANUP_UNCONFIRMED;it cannot replace an earlier
error or be silently reported complete. Stop the batch;retain partial evidence.

Controller also bounds supervisor progress at wall+cleanup+2seconds. On helper
failure it terminates only that owned helper via pidfd,and records cleanup as
UNCONFIRMED unless independently observed. Never assert all descendants gone
because a wrapper returned. Parent-death,early-exit,pipe-holder and error-race
cases are required;the old heartbeat covers only one bounded pattern.

S budgets (engineering bounds,not scientific thresholds):normal wall5seconds;
timeout-control wall0.4seconds;cleanup2seconds;process CPU3seconds,AS268435456,
FSIZE1048576,NOFILE64,CORE0;retained output65536bytes. Fixture programs use a
3second self-deadline and at most one descendant;no fork bomb/resource exhaustion.
These are not H workload budgets,aggregate process limits or stress qualification.

## 7. Closed future synthetic interface

The ten literal ADD-ONLY paths are in semantics.json. No existing file changes,
CLI,entrypoint,product dependency,H1/C1 bridge or arbitrary argv/mount API.
Python>=3.12.3,<3.13;stdlib only;Linux x86_64 pins from sources.json required.

- SyntheticCase enum:FD_CLOSED,DIRECTORY_READ_ONLY,DESCENDANT_NETWORK,
  TIMEOUT_SETSID,OUTPUT_FLOOD,MISSING_MOUNT,NONZERO_EXIT,SUPERVISOR_ABORT.
- SyntheticRequest(case:SyntheticCase,owner_directory:str):frozen exact-type
  request;absolute path denotes ONLY the existing parent for a new mkdtemp run.
  No request can name an audited source,executable,argv,filter,FD or budget.
- SyntheticResult(case:SyntheticCase,outcome:str,errors:tuple[str,...],
  unavailable:tuple[str,...],cleanup:str,stdout:bytes,stderr:bytes,
  run_directory:str|None):frozen defensive tuple-owned result. Outcomes
  REJECTED > UNAVAILABLE > SYNTHETIC_OBSERVATION_COMPLETE;cleanup CONFIRMED or
  UNCONFIRMED. Fixed BLOCKED,all9false,content_identity_only=true,
  historical_execution=false. Known errors outrank missing facts;process return0
  alone is not completion. Construction/assessment rejects forged nested types.
- run_synthetic(request:SyntheticRequest)->SyntheticResult:the sole effectful
  public function;no effects at import. Unsupported host/pins/controls return
  unavailable before payload;invalid request raises ValueError before effects.
- seccomp_bytes()->bytes:pure x86_64 S-only BPF. Match the old filter SHA256
  12e1d308af4e6ed61ae5beccc2c3d2fc3f89506e13215ad31965e97c6fe66901.
  Filter numbers/architecture/default-ALLOW limitation are in semantics.json.
  This is exact compatibility for trusted toys,not an H security-policy decision.

Case dispatch is a fixed internal table. FD_CLOSED's normal runner excludes all
victim FDs;the unsafe negative control is test-private. MISSING_MOUNT removes
only a newly owned required fixture to provoke failure,not arbitrary host paths.
SUPERVISOR_ABORT deliberately exits its owned helper,never the main worker.
OUTPUT_FLOOD writes65537bytes across both streams,with its3second deadline.
No case opens external network;optional listener control binds only owned loopback.
New source files must be independently content-frozen/reviewed before any H
use;being on this ten-path list is not such a freeze or authority.

## 8. Acceptance,versioning and handoff

acceptance.json defines30PLANNED_NOT_EXECUTED cases. The next S implementation
must record actual pytest nodes/raw logs,positive and negative controls,actual
host pins,exit/cleanup results and partial failures outside audited subjects.
Mocked launch tests prove argument/error logic only,not observed kernel effects.
Unsupported hosts yield explicit unavailable for effectful checks,never a skip
counted as kernel success. Unit tests must remain runnable without bwrap.

Preserve all2279baseline tests and old90/95/98floors;new test-only harness targets
statement>=98%,branch>=95%,aim100/100. No weakening/xfail/skip to obtain admission.
This docs-only task checks JSON/source hashes,existing regressions and preservation;
it does not rerun toys or measure new implementation coverage.

Change semantic version for FD/mount/control/trust/cleanup/outcome meaning. Tool,
code and run identities are separate. Content digest uses canonical sorted UTF8
JSON,explicit null,no duplicate/unknown keys/NaN/Inf,and means content identity
only. Later executable freeze is external and must not contain its own hash;
retain prior failed attempts. Source changes do not rewrite old receipts.

Next single task:implement H1_SYNTHETIC_CONTAINMENT_V1's ten-path closed harness
using the companion TDD plan. Do not execute it as part of this design task.
Actual H O/D execution,full syscall/resource design,prepared historical closure,
trust/custody decisions and ENTRY adoption remain separate blocked work.
