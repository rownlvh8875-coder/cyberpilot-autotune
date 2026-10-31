# Fixed guest FIRST_OBSERVED bootstrap observations

Base PR41 `2d11becc2f5b3b71558db6c944de74ddf18354b3`. This is a bounded
disposable-guest source prototype,not a qualified lifetime producer or inventory/
estimator/application bridge. Existing actual captures and all prior decoders are
unchanged. Actual CPB data stays **OBSERVED_UNTRUSTED**,never fed/reclassified into
the PR41 SYNTHETIC_ONLY premise checker or PR35/PR30 admission paths.

## Captured question and source architecture

Which actual pre-arm objects were first observed,which copied local file values
carried those tags,and which new objects received allocation-stage tags?
The ten-file standalone patch targets exact Debian Linux6.12.113 in a new source
extract. New CPBv1 release/path/wire,not a silent CPS/CPCv1 extension.

Fixed PID1 opens console/control/read,two independent memfds5/6 containing the same
literal bytes,and alias40 of5,before seeding. A source-local64-slot walk records
actual local pointer presence,object tag/origin,and raw open/CLOEXEC bits. Each
distinct actually encountered object gets one FIRST_OBSERVED/PRE_ARM_SEED tag;
aliases reuse its object-local tag. No observer-held reference or pointer map.
Equal bytes/names/FD numbers do not establish OFD equality. Source/read tags are
recorded independently from NODE issuance witnesses;missing NODE is never rebuilt.

Parent task/files_struct identity tags do NOT set managed cpl_scope fields. The
existing first-private-PID1-fork gate selects the newly allocated child as root.
Inherited task diagnostic identity is explicitly cleared before fresh issuance.
New child and private constructor namespace get ALLOCATION/POST_INIT_ALLOC tags;
constructor allocation is not completed namespace birth or committed child.
Selected file allocation hooks assign allocation origin only after initialization
and only within active managed scope. Seed origins never become allocation origin
through copying. Unexpected pre-existing tag state aborts without overwriting it.

Root creates post-arm memfd7/alias41 and a nested child. Actual local READ,existing
reference-or-clear,and destination STORE preserve consumed-value pairing and raw
origin. COPY_RETURN,partial allocator free and TASK_FINALIZE are distinct stages.
Failure injections deliberately change fork results;driver checks ENOMEM/EAGAIN.
They are not natural failure frequencies or passive transparency measurements.

**Mutation/perturbation boundary:** read-only describes the evidence envelope,
not zero observer effect. This source writes diagnostic kernel fields and changes
structure layout/instructions/scheduling;the fixed workload writes its own memfds.
No controller/Params/application data is read or changed. No observer references
are added,but all-mutator exclusion and perturbation bounds remain unproved.

## Source interval,issuer and availability

One-shot seed,then ARM,then fixed forks,then STOP. Reseed and early ARM receive
actual EBUSY/EINVAL rejections. Injected partial seed failure keeps assigned tags,
never rolls them back/reissues them,and does not arm/fork. Stop disables new CPB
emitters,drains emitter RCU sections,then attempts a terminal STOP reservation.
This is not a target/global/all-source quiescence proof. A full buffer can lose
the STOP record despite a completed transport frame.

Issuer cookies use an exhaustion-guarded monotonic counter;generation0 is fixed
for this no-reuse profile. Kernel boot nonce is an observed128bit annotation and
epoch1 is local to this frame. Neither authenticates boot uniqueness,freshness,
anti-replay or source truth. Never pool handles or infer cross-boot equality from
matching cookies,nonces,release or source hashes. Generic concurrent issuance,
wrap/reuse/publication/tag-initialization safety is not runtime-qualified.

Local seed checks:PID1,single thread,files count1,no resize,64-slot storage,
unpopulated admitted tags and unmanaged parent scope. These checks do NOT exclude
every external mutator/sharer/outstanding fd_install. Holding file_lock or one CPU
is insufficient for a protected seed cut,as the pinned copy-source warning states.
Only selected initialization/allocation routes are pinned;full hook closure remains
a blocker. Missing/unsupported context must not become default trusted history.

Cookie0 decodes None,not an actual identity. FIRST_OBSERVED != ALLOCATION !=
UNAVAILABLE. PRESENT with no tag is distinct from NULL. Raw zero/false bitmap bits
are observed values;NULL effective binding CLOEXEC is None even if a raw stale
bit is true. Known raw tag but missing NODE is a different gap from unknown tag:
the former appears in missing_origin_witness_ids,the latter in raw None/UNAVAILABLE
and unknown_present_count. Neither field alone is a completeness verdict.

## CPBv1 contract

`/proc/cpbootstrap`,release `6.12.113-cpbootstrap-v1`,version1,prefixCPB.
Frame:DRIVER(ok/forked),META,COUNT,EVENT rows,END,EXIT. Metadata binds case,release,
one CPU,capacity512(or128),copies0or2,root,boot_nonce,epoch1,seed walk status.
COMPLETE describes a seed walk,not identity/protected-cut/history qualification.
Transport completion is distinct from semantic record completeness.

Every buffered event has positive emission n,epoch1,kind and a closed payload:

| Kind | Payload/stage |
|---|---|
| NODE | object,role,origin,stage,generation0;issuance record,not lifetime completion |
| SEED_BEGIN / SEED_SLOT | begin marker;task/source/fd/presence/ofd/origin/rawopen/rawcloexec |
| SEED_END / SEED_ABORT | parent/source/completion;explicit abort reason |
| SEED_REJECT / ARM_REJECT | explicit rejected-command reason,not a state transition grant |
| ARM / STOP | ACTIVE;DRAINED_EMITTERS_ONLY,not global closure |
| BEGIN / BITMAPS | copy context;actual scan/capacity and copied rawUInt64words |
| READ / REFERENCE / CLEAR_OPEN / STORE | actual consumed local value,paired local ordinal,raw origin |
| COPY_RETURN / ALLOC_FREE / TASK_FINALIZE | constructor result/tail/reason;saved scalar post-free;task commit/abort |

Copy context is copy/local/scope/actor/task/source/dest. Actor,subject,source and
private destination identities cannot collide. Scope equals observed managed root,
not seeded parent. Source namespace must match recorded committed creator context.
New subject/destination require witnessed allocation origin. Missing context NODE
cannot be recovered from later tag values into seed→first-copy links. Unknown
copy IDs,cohorts,roles,stages,epochs,generations or malformed values reject/diagnose.
SUCCESS/COMMITTED require NONE;task abort/failure reasons remain distinct.

Observed one-shot controls must agree:SEED_BEGIN precedes observed seed records
and terminal marker;SEED_END precedes ARM and copy stages follow ARM. Observed
abort cannot coexist with completion/ARM/copy;duplicate controls and contradictory
reject-command order are rejected. Missing markers stay unavailable,not inferred
transitions or automatically contradictory order. No control check proves a cut.

Wire limits:UTF8,2MiB original serial,at most512buffered records,UInt64 source
values,FD0..63,exact enums,closed keys,field-order independence. NaN/Inf/Float/Bool
cannot impersonate numeric strings. This is a proc text experiment,not cereal or
Cap'n Proto;no tags/schema/controller fork changes. A semantic/unit/stage/cohort
change needs a new wire version/profile;source revision is separately pinned.
Unified CPB emission ordinal is not effect linearization and not a merge of old
CPS/CPC domains. Legacy lifecycle shadow instrumentation remains in this fresh
source but its counters are not exported or asserted as CPB/global completeness.

## Decoder,diagnostic and evidence

Test-only contracts/wire/model/image are pure frozen memory operations. `parse_serial`
creates finite typed immutable Capture/Event values;`assess` consumes parsed values
only,not arbitrary unchecked dataclass constructions. It reports local equations,
recorded seed walk,raw bindings/origins,complete committed mechanical copy sequences,
unknown reads/missing issuance and conditional seed→first-copy links. Severe
identity/stage/cohort contradictions clear those links. Partial/aborted copies
stay diagnostic. An empty reason tuple is never admission or completeness.

Always OBSERVED_UNTRUSTED/BLOCKED;allocation_history_complete,atomic_cut_proven,
runtime_qualified and all9permissions false;actual_global_drops/prohibited None.
No collector/thread/timer/persistence/global service in the pure path,no estimator,
application/owner dependency or proposal capability. Default audit never builds,
boots or networks. Only an explicit fixed enum runner request executes a guest.

Local equations:attempted=reserved+failed;reserved=committed+discarded+pending.
Attempt ordinal is taken before fallible reservation. Balance does not erase a
gap or prove zero global drops;NMI/out-of-profile sources remain unqualified.

Evidence freezes full original serialB64/size/SHA,images,build/kernel/init/config/
source/tools/dependency metadata and selected file/blob/range hashes. Independent
literal raw-token goldens were written before hooks;no decoder computes expected
truth. Frozen actual manifest digest additionally binds nonce/boot annotations.
These hashes are content identity,never authenticity or authority. Existing package
authentication is inherited preparation,not newly proven freshness/reproducibility/
complete build-input closure. Optional source/assets verification checks bytes,
not actual execution or global hook coverage.

No vehicle/host tracing/Params/controller/cereal/estimator qualification/candidate/
application bridge/owner proposal/PR8·9 edits/longitudinal/external AI/upstream PR.
