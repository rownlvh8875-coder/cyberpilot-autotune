# Fixed-profile object-lifetime / tag publication read protocol design

## Purpose and scope

Continue PR43 exact `e01cdc127bbb17073aa47967b926b68088f57ded` and its selected
source catalog digest `4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af`.
Design when a future scalar tag capture could have internally consistent
lifetime,publication and membership premises. Do not implement a kernel/runtime
producer or qualify any actual capture. All13PR43obligations remain open.

The user approved this next design and delegated inline execution without
routine approval menus. Choices here are the author's,not user-provided details.
No source/kernel/producer/old capture/controller/schema changes,new references,
new observer locks,VM/device/vehicle execution or qualification are authorized.

## Alternatives and selected architecture

1. Observer-acquired references plus identity revalidation: can protect a target
   but changes lifetime/perturbation and exceeds the no-added-reference profile.
2. READ_ONCE/barriers/seqlock alone: may constrain scalar accesses but cannot
   keep freed/reused storage alive;not sufficient,not selected.
3. Existing-operation lifetime-scoped capture plus write-once identity and
   explicit publication/membership premises: selected bounded future design.
   It costs unsupported routes where those premises cannot be demonstrated.

Preferred future OFD point:after the copy operation's **existing** get_file(f),
before destination STORE,using the actual caller-local f and consumed-read link.
This is a new POST_EXISTING_REFERENCE_PRE_STORE tag-snapshot stage,not a silent
reinterpretation of PR42's pre-reference READ. The existing reference must itself
have a justified source binding;its relaxed increment alone is not a publication
acquire. No observer get_file/put_file is added. A new future receipt/profile is
needed;current actual captures and codecs remain unchanged.

Private constructor-owned TASK/NAMESPACE/OFD snapshots are separately modeled
before first object publication. They are not equivalent to published borrowed
reads. Existing-reference mode is OFD-only in this design;other referenced object
routes remain unsupported pending type-specific source proof.

FIRST_OBSERVED seed tags were written into already existing objects. They cannot
be retroactively treated as pre-publication ALLOCATION tags. Quiescent seed
initialization needs a separate admitted all-mutator/lifetime transaction,which
does not exist. The bounded checker rejects FIRST_OBSERVED with
SEED_PROTOCOL_UNQUALIFIED;the document records its future prerequisites without
inventing a Boolean seed-proof grant. No origin promotion or source-gap closure.

## Independent premises

- Lifetime:the existing operation owns the object or already holds a valid
  source-bound reference across **every** component read and scalar save.
- Publication:the complete identity tuple was initialized and frozen once;
  private ownership orders a private capture,or an actual existing release/
  acquire relationship orders published reads. Record-buffer/issuer ordering
  and f_count initialization alone are not this relationship.
- Writer closure:all identity writers on the admitted route are covered and
  cannot change the tuple during/after freeze. This is only an explicitly
  assumed synthetic premise here,not inferred from absent trace events.
- Membership:managed root and membership generation are separate from immutable
  identity,and protected by an existing operation guard across capture. Identity
  equality alone cannot pool changing membership cohorts.
- Save before protection ends;emit later from saved scalars only. Emission does
  not authorize a fresh target dereference or prove global effect order.

Identity fields:object_kind(TASK/NAMESPACE/OFD),cohort,cookie,epoch,generation,
origin. Cookie/epoch positive UInt64;generation known UInt64 including0,None is
unavailable. Matching values are conditional labels,not authenticated identity.
Reader mode,stage,lifetime witness and publication witness must agree exactly.
Observer reference/lock counts are exact integer0,not False/None/default0.

## Executable design artifact,not runtime proof

New test-only `tests/tag_read_protocol/model.py` exposes
`evaluate(payload:Any)->ReadProtocolDecision`. Input closed schema
`tag-read-protocol-design-v1`,evidence_class SYNTHETIC_ONLY,exact source base/
catalog,identity and observed_identity,writer,reader,membership,graph.

Writer fields:components_initialized,writer_set_closed,identity_write_once
(True/False/None distinguished),publication,witness_identity.
Reader fields:mode,stage,lifetime,observer_refs,observer_locks,
all_component_reads_bounded,emission,witness_identity. Both witness identities
must bind the full expected/observed subject tuple,not merely assert a reference
or publication exists. These are still synthetic claims,not actual attestation.
Modes PRIVATE_OWNER/EXISTING_REFERENCE;
stages PRIVATE_PRE_PUBLICATION/POST_EXISTING_REFERENCE_PRE_STORE;
lifetime witnesses PRIVATE_OWNER/EXISTING_OPERATION_REFERENCE_WITH_SOURCE_BINDING;
publication OWNER_PRIVATE_ORDERED/EXISTING_RELEASE_ACQUIRE;
emission SAVED_SCALARS_ONLY. Unsupported values never fall back.
Membership fields:cohort,root_before,root_after,generation_before,generation_after,
guard(EXISTING_OPERATION_GUARD). Root/generation must be known and unchanged.

The graph is an explicit **assumed happens-before DAG**,not event-list order,
timestamps or a join of real CPB/CPL domains. Nodes/edges are arbitrary-order
vectors with exact mode-specific anchor names,unique pairs,at most128edges.
Common anchors:tag_init,tag_freeze,read_begin,read_end,save,emit,context_begin,
context_end. Private adds owner_begin,owner_end;reference adds publish_release,
ref_begin,ref_end. Missing paths or any cycle reject. Closure means finite
logical consistency only,not LKMM/C/compiler verification.

Required paths:tag_init→tag_freeze→read_begin→read_end→save→emit;
context_begin→read_begin and save→context_end. Private additionally
owner_begin→tag_init and save→owner_end. Reference additionally
tag_freeze→publish_release→ref_begin→read_begin and save→ref_end.
No ordering of protection-end vs emit is required:the copy was saved already.
All component reads are explicitly assumed inside read_begin/read_end;this
abstract checker does not model instructions,tearing or all C writes.

Output frozen defensive-copy SyntheticTagSnapshot only on consistent premises;
otherwise reasoned rejection/no snapshot. Always SYNTHETIC_ONLY/BLOCKED;
runtime_producer_implemented,target_lifetime_proven,tag_publication_qualified,
source_happens_before_proven,allocation_history_complete,atomic_cut_proven,
runtime_qualified and all9permissions false;global counts None. Consistently
fabricated premises remain undetectable and never authorize application.

New offline audit freezes semantic schema,independent synthetic cases and source
references. It checks existing PR43 source catalog/byte-bound repository files,
not actual C execution or external source roots. Existing PR43 explicit source
audit is run separately;its source checks never become a runtime witness.

## Deliverables and verification

New model/audit/tests/architecture guards;docs/tag_read_protocol_contract.md,
docs/tag_read_protocol_capture_design.md,docs/tag_read_protocol_result.md;
docs/evidence/tag_read_protocol_{schema,sources,cases}.json. Only new files and
two narrow new .gitattributes rules. No installed src or dependency changes.

Independent literal tests precede code. Cover private/reference positives,
post-release saved-scalar emission,nonordered/missing/cyclic DAGs,mixed identity/
cohort/member generation,None/zero/False,partial initialization,unsupported
stages/RCU/barrier-only lifetime,added refs/locks,seed nonpromotion,actual-input
rejection,and immutable output. Pure model minimum98%statement/95%branch,aim100.
Full regression,old source/history audits,native192/replay4,ruff/format/mypy,
build/fresh vanilla-research wheel,CRLF and exact-head push/PR CI. One fresh final
whole-branch review;one author C/I TDD fix pass,minors deferred,no re-review.

Own branch design/owner-scoped-tag-read-protocol,stacked Draft against
audit/bootstrap-tag-initialization. Preserve30existing Open/Draft PRs and
maina5d3514f. No merge/shared branch write. Recoverably archive only this plan's
workspace;existing producer/source/assets/other plans untouched.

Non-goals:no kernel/producer/schema/controller patch,no actual guest execution,
no Params/vehicle/device/host probe,no estimator qualification,candidate,
application/owner bridge,PR8/9 edit,longitudinal,external AI or upstream PR.
