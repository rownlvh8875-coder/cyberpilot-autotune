# Fixed guest FIRST_OBSERVED bootstrap prototype

Base PR41 `2d11becc2f5b3b71558db6c944de74ddf18354b3`; branch
`feat/guest-first-observed-bootstrap`. Implement the recommended bounded prototype,
not a qualified observer or inventory/estimator/application bridge. All old files,
PRs/main/source/build/binary/capture assets stay frozen; fresh source/asset prefix.

## Author's approach under standing autonomous inline delegation

Use a new CPBv1 wire/profile/path and origin-aware object-local tags in a fresh
Linux6.12.113 extract derived from the preserved PR40 standalone patch. Rejected:
always-on global boot tracing (wider coverage/overhead),or retrofitting old CPCv1
actual data (would invent pre-arm history). Separate capture/emission domain and
decoder; no actual→SYNTHETIC_ONLY conversion or use of PR41/PR35/PR30 admission.

Before first managed fork, fixed PID1 opens console/control/read descriptors and
two independent equal-data memfds5/6,plus alias40 of5. Parent/task and files_struct
receive FIRST_OBSERVED tags; each actually read pre-arm struct file receives one
immutable first-observation tag,shared by aliases. Preserve unavailable/no tag
separately from NULL. No pointer/PID/inode/path/content identity substitution.
No extra observer references. Source-local file_lock walk64slots records actual
pointer and raw open/CLOEXEC bits; it is NOT an all-mutator protected cut.

Reuse diagnostic cpl_cookie identity but keep parent managed cpl_scope_cookie0:
issuer epoch/provenance separate from managed-root membership. Add object-local
origin/epoch fields,clear inherited task diagnostic tags before fresh allocation
issuance;initialize files_struct fields before use and rely only on selected
admitted initialized file paths. New fork child/private destination get ALLOCATION
tags,never FIRST_OBSERVED. Current first-PID1-fork gate still sets the new child as
managed root. Allocation identity is not successful constructor/task commit.

All new tags have origin FIRST_OBSERVED/PRE_ARM_SEED or ALLOCATION/POST_INIT_ALLOC,
generation0,issuer_epoch1 within this one-boot frame. A kernel-generated128bit boot
nonce is an observed cohort annotation,not authenticated uniqueness/freshness;
never pool frames or infer equality across boots from IDs/nonce alone. Counter
exhaustion must not knowingly reissue a tag. Generic concurrency/wrap/reuse safety
remains unqualified. Existing/unrecognized tag state aborts rather than overwrites;
aliases issued during this walk reuse their existing immutable tag.

After seed walk,ARM then two fixed private forks. Root creates post-arm memfd7
and alias41; actual READ/ref-or-clear/STORE raw origin observed independently of
NODE issuance. Constructor/task failure stages remain separate. STOP disables
active callbacks and drains emitter RCU sections only. Old lifecycle shadow
instrumentation may remain in fresh source but is not a complete CPB/global domain.
No claim about its unexported counters,coverage or observer perturbation.

## Ten fixed fresh guests

NORMAL,SEED_LOSS,SMALL_BUFFER,SEED_FAIL,UNSEEDED_OFD,RESEED_REJECTED,
EARLY_ARM_REJECTED,CONSTRUCTOR_FAIL,TASK_FAIL,ALLOC_FAIL.

Normal:73bootstrap events(begin+7object tags+64slots+end),ARM,5post-arm tags,
392copy stages,STOP=472attempts. Normal copied PRESENT bindings18 (8root/10child),
REFERENCE18/CLEAR_OPEN110,READ128/STORE128. Source global IDs normally1parent,
2parentnamespace,3console,4control,5read,6memfd5/40,7independentmemfd6,
8root,9rootnamespace,10postarmOFD,11child,12childnamespace.

SEED_LOSS loses actual NODE6 reservation after attempted accounting:472attempted,
471received/1failed;copy tags do not reconstruct missing issuance. SMALL_BUFFER
limits unified own buffer128:472attempted/128received/344failed. SEED_FAIL injects
abort after slot0:7events includingSTOP,noARM/fork;partial tags retained,never
rolled back/reissued. UNSEEDED_OFD intentionally skips fd6 tag and records PRESENT
with unavailable identity/origin:471events,root IDs shift,unknown never repaired.
RESEED_REJECTED and EARLY_ARM_REJECTED each record one real rejected command:
473events,driver requires EBUSY/EINVAL and then continues only allowed protocol.
CONSTRUCTOR_FAIL uses real partial free+ENOMEM cleanup:280events/200copy stages.
TASK_FAIL uses EAGAIN after copy_files and actual cleanup:472events/aborted child.
ALLOC_FAIL injects before allocator call:277events/198copy stages,no child namespace.
Faults deliberately change telemetry/operation results,not natural error frequencies.
Expected counts must be checked against actual unmodified original serial.

## Wire and pure observed diagnostic

New `/proc/cpbootstrap`,release6.12.113-cpbootstrap-v1,prefixCPB/version1.
Closed metadata:case/release/CPU1/capacity512(or128)/copies0or2/root/boot_nonce/
epoch1/seed_walk(COMPLETE/ABORTED). Driverok/forked result and transportEND/EXIT
are distinct from a lost buffered STOP or semantic completeness. UTF8/2MiB bound,
at most512records,exact unsigned widths/positive ordinals,field order irrelevant.

Each event n/epoch/kind. NODE object/role/origin/stage/generation;SEED_BEGIN;
SEED_SLOT task/source/fd/presence/ofd/origin/open/cloexec;SEED_END parent/source/
result;SEED_ABORT/SEED_REJECT/ARM_REJECT reason;ARM status;STOP result. Copy kinds
and paired local ordinals retain PR40 mechanical meanings,with copy/local/scope/
actor/task/source/dest plus payload. READ/STORE add actually observed origin.
Bitmap rawUInt64words are not pointer/identity witnesses. NULL binding CLOEXECNone
while raw stale bit remains observed. Cookie0→None,originUNAVAILABLE distinct
from a tag. Unknown context/stage/cohort/role/width/result/reason rejects/diagnoses,
never linear/default fallback. Unified CPB emission ordinal is NOT effect order.

Pure test-only tests/guest_bootstrap:contracts.py(frozen dataclasses),wire.py
parse_serial(raw:bytes)->Capture,model.py assess(Capture)->Decision,image.py
build_image(binary:bytes,case:str)->bytes,runner.py capture(case:str)->
tuple[Capture,bytes,bytes],audit.py validate(pristine_root:Path|None=None,
patched_root:Path|None=None,*,verify_assets:bool=False)->dict.

Decision reports local equations/gaps,recorded seed walk,object origins,unknown
PRESENT/issuance gaps,complete committed mechanical copies and conditional
seed→first-copy links. Missing NODE never rebuilt from tag values. New subject/
destination must have allocation origin;seed origins never promoted. No state
machine/collector/actual-to-synthetic adapter. Fixed evidence_classOBSERVED_UNTRUSTED,
statusBLOCKED,allocation_history_complete/atomic_cut_proven/runtime_qualifiedfalse,
globaldrops/prohibitedNone,all9permissionsfalse. No operational or lifetime admission.

## Verification / non-goals

TDD literal wire fixtures before source;old PR40 kernel+newdriver actual missing
interface RED;fresh source/build/static driver with recorded existing tools/deps;
10actual1vCPU512MiBTCG guests,no network/KVM/sharedFS/passthrough/arbitrarypayload.
Preserve complete original serial/images/source/kernel/init/config/tool hashes,
selected file/blob/ranges and independent pre-hook raw-token goldens. No host ELF
driver execution/kernel/security/package changes. Normaltests/audit never boot/build.
Pure statement98/branch95minimum,aim100;fullregressions/oldaudit/native192/replay/
ruff/format/mypy/build/freshwheel/CRLF;one fresh final review onexplicithead,one
authorC/I TDDfixpass/fullrerun,no re-review;own stacked Draft+exactheadpush/PR CI.
User requests continuous execution:complete this approved workflow without routine
approval pauses;do not turn that into vehicle/shared-branch/merge authority.
No vehicle/Params/controller/cereal/H6 estimator/candidate/application/owner/PR8·9/
longitudinal/externalAI/upstream changes. All prior scientific/runtime/hookcoverage/
birthhistory/copycut/loss/perturbation/consumer/artifact/factor/vehicle/watchdog/
executor/application blockers and4deferredminors retained.
