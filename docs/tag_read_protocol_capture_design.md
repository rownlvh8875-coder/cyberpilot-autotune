# Future tag capture architecture — not implemented

## Alternatives and selected point

| Architecture | Benefit | Why not sufficient / decision |
|---|---|---|
| Observer-acquired reference/revalidation | Can establish a lifetime interval | extra target lifetime/perturbation exceeds selected no-added-reference profile |
| READ_ONCE/barrier/seqlock-only lookup | Can constrain some tuple accesses | cannot keep reused/freed object storage alive;not selected |
| Existing-operation owner/ref-scoped scalar capture | uses existing operation lifetime and a separately qualified publication route | selected bounded future architecture;unproved routes stay unavailable |

Exactly one preferred future OFD site:inside `copy_fd_for_context`,after its
existing get_file(f),before destination pointer STORE/ownership transfer. Use the
actual consumed caller-local f and read link. Do not acquire/release an observer
reference or introduce a new lock. The operation's relaxed get_file increment
alone does not prove publication ordering or validate an arbitrary borrowed pointer.
Its source binding/ordering must be independently justified for an admitted route.

PR43 claim NS_CONSTRUCTOR pins `fs/file.c:315-445`;OFD_RCU_REVALIDATE pins
`:888-928` as an example of a different validated reference reader. The latter
is **not** automatically the copy loop's acquisition protocol. OFD_INIT/
OFD_NORMAL_ALLOC pin source initialization/tag order;ORIGIN_READ/COPY_RAW_READ
pin current scalar accesses. TASK_RESET_GATE identifies the separate private
constructor route. All are selected source observations,not runtime proofs.

## Critical legacy-reader limitation

Current PR42 cpc_read reads tag fields **before** get_file. Its later STORE also
reads tags. Merely adding a safe-looking new post-reference snapshot does not
remove or qualify those legacy accesses. A future producer intended to meet this
protocol must audit every target dereference,split pointer-consumption/ordinal
capture from tag-field reads,and place target reads within admitted protection.
Until then the producer remains unqualified. No existing code/record is changed
or made safe by this design document.

Conceptual future flow,not implemented code:

```text
consume caller-local pointer / presence / operation link (no OFD-tag dereference)
  → existing copy operation gets its existing reference
  → copy observed tag + context into a local scalar envelope
  → existing destination STORE / operation ownership transfer
  → optional later by-value record emission from that saved envelope
```

Missing reference/source-binding/publication/context witness means UNAVAILABLE
qualification context,not an invented successful witness. A diagnostic prototype
may observe raw scalars while retaining OBSERVED_UNTRUSTED;it must not use the
synthetic model as an actual admission engine.

## Existing observation mapping

| Existing item | Future mapping |
|---|---|
| caller-local f and consumed read ordinal | possible source link,not an exported pointer or standalone lifetime proof |
| PR42 pre-reference READ tag tuple | WRONG_STAGE for post-reference snapshot;preserve original meaning |
| REFERENCE marker | operation marker,not a full identity tuple;current cpc_step argument is NULL |
| STORE tag tuple | different stage;not a substitute for protected pre-transfer capture |
| NODE ALLOCATION | origin/allocation context,not completed constructor,publication or commit |
| FIRST_OBSERVED seed NODE | diagnostic seed origin;no ALLOCATION/private-unpublished promotion |
| legacy post-free saved cookie/scope | partial saved-scalar context,not complete identity/membership tuple or a live read |
| balanced buffer counts / emission n | local transport diagnostics,not target HB/cut/lifetime closure |

If the source READ record is lost,a numeric read ordinal is not a recovered
receipt. Do not reconstruct missing origin/read witnesses from later values or
expected fixtures. A new producer/profile and explicit adapter would be required;
no codec,PR42capture or PR8sidecar is silently upgraded here.

## Future neutral observation envelope

This is a wire *proposal*,not cereal/Cap'n Proto schema or an implemented codec.
Keep its version separate from synthetic-premise version. No real tags assigned.

| Field group | Proposed type / meaning |
|---|---|
| capture/session/cohort/source | bounded non-identifying tokens,source revision/archive+patch/build context;not authentication |
| operation/consumed-source link | optional UInt64 IDs with explicit domain,source receipt availability and stage |
| raw cookie/epoch/origin | availability-tagged observed UInt64/enums;observed raw0 remains a raw value,not valid identity |
| logical identity/generation | separate typed context;positive cookie and known generation only with explicit provenance |
| root/membership generation | optional UInt64,independent source/guard context;never fill unknown generation with0 |
| lifetime/publication/writer witness | source-bound witness reference or UNAVAILABLE,not self-certified True |
| timing | optional capture and emit monotonic UInt64ns with distinct clock/domain meanings |
| snapshot/emit stage | explicit PRIVATE_PRE_PUBLICATION / POST_EXISTING_REFERENCE_PRE_STORE / SAVED_SCALARS_ONLY or unsupported |

Current CPB generation0 is a source-profile convention,not a new measured
object-local generation counter. Current missing membership-generation/witness
fields remain unavailable. Raw0 differs from unread None;logical cookie0 is
reserved/unavailable. Preserve integer precision;Float32/Float64 is not a lossless
UInt64 identity encoding. NaN/Inf/Bool cannot impersonate IDs. Capture time is not
emission time and neither supplies an assumed HB edge.

Capture all target-dependent values and metadata before protection ends. A local
saved envelope must remain live until synchronous by-value buffer copy completes;
never queue its stack address. Transport loss stays explicit and cannot elevate
a partial envelope to a qualified observation. No timing/throughput/overhead
bound is measured or invented. No-added-reference/lock does not mean zero observer
effect or complete hook coverage.

## Seed/private scope and implementation prerequisites

Private constructor snapshots concern the tag tuple,not full object construction
success,task commit or child inventory. First exposure/cleanup ends that private
window even if some reference survives. Shared/unshare/fallback namespace routes
and referenced TASK/NAMESPACE remain unsupported by the bounded model.

Exposed seed objects require a distinct quiescent writer/lifetime transaction
before they could support stable FIRST_OBSERVED reads. Existing local checks,
file_lock,one CPU,RCU or emitter drain do not supply it. Aborts retain partial
diagnostics,not historical allocations. This design does not close those duties.

Before any actual qualification:identify the exact existing lifetime/source-binding
and publication guards,cover every admitted tag writer/reader/reuse route,bind
membership without ABA,prove layout/type/compiled ordering,account for losses,
measure perturbation,and validate actual captures independently. No real kernel
patch,producer,VM/vehicle run,application or estimator is authorized by a source
hash,a proposed wire field,or a passing synthetic case.
