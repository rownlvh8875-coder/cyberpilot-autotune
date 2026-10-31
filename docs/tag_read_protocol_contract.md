# Owner-scoped tag read protocol — design contract

**OBJECT_LIFETIME_TAG_READ_PROTOCOL_DESIGN_READY** means a bounded hypothetical
protocol,not source/compiled/runtime proof or an implemented producer.
SYNTHETIC_ONLY/BLOCKED;all operational permissions remain false.

Project design base:PR43 `e01cdc127bbb17073aa47967b926b68088f57ded`.
Selected source catalog digest:
`4b0712a7d12069a74032f8f9f91861bf22397436927a278818968d9f647930af`.
This is a project/catalog reference,not a Linux revision,runtime fingerprint,
authenticated boot identity or application authority. The underlying unchanged
Debian archive/PR42 patch remain those pinned by PR43. No source/kernel/producer,
actual capture,controller,cereal or installed package changes occur here.

## Question and four independent requirements

When could a future producer copy a tag tuple from the **same live allocation**,
after its intended publication,and bind the result to unchanged membership?

1. **Lifetime:**the existing operation owns the object or already holds a valid
   source-bound reference before every target-dependent component read until the
   scalar envelope is saved. RCU/address equality/repeated reads alone do not
   prevent storage reuse. Do not add observer references or retain targets.
2. **Publication and writer closure:**the complete immutable identity tuple is
   initialized/frozen under an admitted writer protocol. Private capture is
   within an exclusive unpublished window;published capture needs a real existing
   release/acquire relationship. Numeric issuer serialization,record-buffer
   release,f_count initialization and relaxed reference increments are not that
   relationship. Coverage of every admitted writer is a separate unproved duty.
3. **Membership:**managed-root context and its generation have their own existing
   guard. Matching identity does not establish unchanged membership. Equal values
   before/after are not proof against ABA without the guard/generation contract.
4. **Save then emit:**complete target-dependent reads/context binding before the
   protection window ends. Later transport uses saved scalars only,not a retained
   target pointer or a pointer to an expired caller stack.

These requirements are independent even where one source ownership interval
supports several. None is currently qualified by a payload flag or source hash.

## Bounded modes

| Mode | Supported subject | Capture stage | Lifetime/publication premise |
|---|---|---|---|
| PRIVATE_OWNER | ALLOCATION TASK/NAMESPACE/OFD | PRIVATE_PRE_PUBLICATION | exclusive constructor owner;complete tag before first exposure |
| EXISTING_REFERENCE | ALLOCATION OFD only | POST_EXISTING_REFERENCE_PRE_STORE | operation's existing source-bound reference plus separate publication ordering |
| FIRST_OBSERVED | diagnostic only | unsupported by checker | exposed-object seed requires a separate admitted quiescent transaction |
| Other reference routes/stages | diagnostic only | no fallback | type-specific source proof missing |

The private owner window ends at its **first exposure/transfer/cleanup boundary**,
not just an arbitrary reference drop after publication. Ref-end similarly means
the first transfer/release point after which the observer cannot rely on the
operation's existing reference. These are conceptual source-witness definitions,
not observed facts from the model's graph.

FIRST_OBSERVED must not become ALLOCATION to satisfy this design. A future seed
transaction would need per-object lifetime protection,exclusion of all relevant
tag writers/mutators/outstanding installs,complete initialization/commit and
ordering to its first admitted reader. Partial seed aborts retain diagnostics,
not allocation history. PR42's local checks/file_lock/one CPU do not provide that
transaction. No seed-qualification Boolean or runtime adapter is added.

## Explicit assumed-HB graph

The checker evaluates **declared synthetic happens-before assumptions**,not a
kernel memory model. Node or edge vector position,CPB/CPL emission n,clock time,
one CPU or a matching digest cannot create an edge.

Reference-mode required relationships are illustrated below. Arrows are assumed
relations,not measured ordering. SAVE branches deliberately:EMIT may occur before
or after protection/context ends,provided it uses only saved scalars.

```text
tag_init → tag_freeze → publish_release → ref_begin → read_begin → read_end → save
context_begin → read_begin
save → {ref_end, context_end, emit(saved)}
```

Private mode replaces published/reference admission with owner_begin→tag_init
and save→owner_end. Both modes require tag_freeze→read_begin. Missing required
paths,cycles,foreign/duplicate anchors or edges reject. Transitive paths count;
list order never does. At most128edges is a finite parser resource bound,not an
empirical control/safety threshold. There is no timestamp alignment or actual
trace-to-HB reconstruction.

All component reads are *assumed* inside read_begin/read_end. The finite model
does not enumerate C loads/stores,tearing,concurrent executions,reclamation or
compiler transformations. Declared writer closure/write-once/private ownership
can be coherently fabricated;the checker cannot authenticate them.

## Identity,witness binding and availability

Identity:object_kind,cohort,cookie,epoch,generation,origin. Expected and observed
tuples must agree,as must the separate writer/publication and reader/lifetime
`witness_identity` tuples. Mere existence of some reference/publication does not
bind it to this subject. Matching synthetic labels are still not actual identity.

Membership is separate:cohort,root_before/root_after,generation_before/
generation_after and existing guard. Known roots/generations must match;guard
and bounds must be asserted. Cookie/epoch are positive UInt64,generation is
UInt64 with known0 allowed. None is unavailable;False is not integer0. Explicit
False,unknown None and numeric0 writer flags reject with different reasons.
Observer reference/lock counts must be exact integer0,not False or default0.

`evaluate` is the validated construction API. It returns an immutable defensive
snapshot on consistent premises or a reasoned rejection/no snapshot. Direct
unchecked dataclass construction and hostile in-process mutation are not a
security boundary. Positive output means only a self-consistent hypothetical
story;all source/runtime proof fields stay false,global counts stay None.

## Separation from real wire and qualification

`tag-read-protocol-design-v1` and the semantic schema manifest describe **synthetic
premise input**,not a production wire receipt. Actual producers must not populate
writer_set_closed or source-HB proof by asserting True. Future observations may
record a witness reference or UNAVAILABLE;independent qualification must establish
its meaning. This design supplies no such qualification,AuthorizationGrant,
QualifiedEvidence,estimator/app/owner bridge or permission transition.

Existing actual CPB/CPC/CPL records are unsupported input. They remain
OBSERVED_UNTRUSTED and are not relabeled into synthetic proofs. The offline audit
may hash-check their unchanged manifest bytes indirectly through static source
provenance;it does not parse/pass those records to this model. Prior PR41/35/30
admission paths are not invoked. All13PR43source obligations remain open.
