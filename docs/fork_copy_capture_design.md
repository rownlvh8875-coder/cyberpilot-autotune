# Future fork-copy capture architecture — not implemented

Read [contract](fork_copy_evidence_contract.md) first. Exact source symbols/ranges
resolve in [manifest](evidence/fork_copy_design_sources.json). No C/API edits,
kernel build,guest execution,probe attach,host trace or device work this phase.

## Alternatives and selected future capture point

| Option | Consumed slot read/ref/store | Actor/subject context | Cost / gap | Verdict |
|---|---|---|---|---|
| Post-copy copy_files summary | not recoverable | available | low coupling,but cannot recover historical reads/flags | insufficient |
| Explicit source-local copy context from copy_files into selected dup_fd walk | directly accessible | passed from actual creation call | source API/cookie/failure/buffer redesign and timing overhead | **preferred future architecture** |
| Later proc/trace/syscall/CPS join | wrong stage or missing | temporal guesses | loses exact reads,unknown object identity and copy order | insufficient |

Selection is the author's design call,not approval to implement or qualify it.
Do not add a global lock to manufacture a serialized PR35 history. No sidecar or
old consumer automatically supports the proposed records.

## Exact future placement and atomicity

1. In copy_files,select actual private-copy branch,carry scope/actor/child and old
   namespace cookie plus a newly issued copy-attempt ID. Child allocation is known
   before copy_files; unavailable armer/old namespace remains explicit for root.
2. On initialized newf allocation,issue a **constructor allocation cookie**,not a
   claim that the namespace constructor succeeded. Current PR38's cpl_task_files
   issues its cookie AFTER dup_fd; a future patch must link/retain the same cookie
   across constructor completion rather than simply moving TABLE_NEW early or
   allocating a second identity. Allocation failures may have no destination ID.
3. After the final reacquired old file_lock and computed range,record BEGIN and
   actual copied open/CLOEXEC bitmap values. Capture actual copy output,not a later
   reread presented as an input snapshot. Retry/resizing/punch-hole paths are outside
   the selected64profile and must reject,not silently choose another source.
4. Inside the actual ascending loop,record the local f from rcu_dereference_raw.
   For non-NULL,record completion of existing get_file;for NULL,record actual
   __clear_open_fd. Record the actual rcu_assign_pointer destination effect,linked
   to that read ordinal. Do not reread old_fds after advancement,probe a different
   fdt generation,derive object identity from an address,or hold observer references.
5. Record pointer tail clear and constructor return separately from task outcome.
   Current64/64tail length is0; it does not prove a larger range was visited.
6. At copy_process's last-failure boundary link commit,or preserve explicit failure
   on the relevant bad_fork cleanup path. alloc_fdtable errors/free of partially
   initialized newf require their own terminal allocation/attempt accounting;
   put_files_struct's successful-namespace free hook alone does not cover them.

No such capture context,cookie relocation,terminal failure hook or per-slot source
record is implemented. API/caller audit and failure injection belong to the next
implementation task. Current output uses only source review and synthetic premises.

The record envelope is one copy-attempt cohort,**not** an atomic source table.
Pairing local values avoids later topic joins but does not remove lockless installs.
A source can be `(0,0)→(1,0)→(1,1)` while the copy reads `(0,1)`. Parent file_lock,
one vCPU or successful task commit do not close hidden sharers or in-flight installs.
Per-slot evidence also does not close all external references or final destruction.

## Callback safety,precision and transport

Future hooks under spinlocks/RCU/task creation must not sleep,allocate,format text,
perform IO,retain target refs or recurse through the observed allocation paths.
Use preallocated bounded scalar records,source-local sequence/loss accounting and
post-stop formatting. Existing required get_file is a target operation,not an
observer intervention to hide. Instrumentation still changes instructions,layout,
buffer occupancy and scheduling; perturbation remains unquantified.

Bitmap bits are booleans with explicit unavailable state;raw bitsets may use
fixed UInt64 words for64slots in a future wire. IDs/ordinals preserve UInt64 width;
FDs/bounds UInt32. No Float32/Float64 conversion of identities or flags. No pointer,
PID,wallclock,VIN,GPS,route,driver identity or payload data belongs in the receipt.
Version changes on semantics/stage/cohort/unit changes; source content hashes are
separate provenance. Digests give content identity only,not approval/authenticity.

196normal proposal records exceed current128capacity. Derive a bounded transport
budget including both copies,existing lifecycle traffic,failure/stop metadata and
every pre-reservation attempt. Do not merely call overflow a missing sample or
raise capacity and claim completeness. Stop/drain/all-source arm/CPU/NMI/overflow
and omissions-before-attempt remain separate qualification obligations.

## Unchanged boundaries and acceptance for later work

Later implementation must first satisfy exact-source local slot/read/ref/store
tests,constructor/late-task failure tests,unknown-OFD/root contexts,actual transport
overflow tests and source/binary/input evidence in fresh harmless disposable guests.
No host tracing,policy changes,extra target references,global effect locks or
arbitrary payload expansion. This design recommends no vehicle execution.

Even future observed per-slot records do not themselves prove PR35's serialized
cut. A separate compatibility decision is needed,including actual owner/source/
loss/perturbation closure. PR30 evidence,consumer FD inventory,application authority,
qualified friction estimation and device/runtime readiness remain blocked.
