# Bounded inherited-OFD identity and provenance contract

Design only, base PR40 `21a542eba9e889323b2cb1b7d7c75d9c9cab1025`.
No source patch, actual bootstrap receipt, new wire implementation or runtime
qualification. The executable model accepts **SYNTHETIC_ONLY** premises only.
All nine operational flags remain false and every result remains BLOCKED.

## Question and source facts

Can a future fixed guest identify the pre-arm parent/table/OFDs and follow their
actual copied bindings **without pretending it observed their allocations**?

PR40's actual first-copy parent/source are unavailable and PRESENT pre-arm files
have unavailable OFD cookies. Driver opens console, case and proc descriptors
before arm. `cpl_file_birth` returns unless both managed scope and active arm are
present; its selected alloc_empty_file hook follows successful initialization.
`cpl_task_alloc` clears copied tags, then selects first PID1 fork as managed root.
`cpc_attempt` reads the source namespace cookie; `cpc_read` uses the actual local
file pointer cookie. Seven exact patched files/thirteen ranges plus six existing
repository references bind these claims (whole file SHA256/Git blob/range SHA256).
Static inspection is not full hook coverage or actual bootstrap observation.

## Three approaches

| Approach | Benefit | Limitation / decision |
|---|---|---|
| Always-on early-boot allocation hooks | Could witness selected original allocation stages | Broader boot/hook/input closure,overhead and failure surface;not selected |
| Separate FIRST_OBSERVED bootstrap | Can propose continuity for existing objects without inventing births | Selected bounded future architecture;initialization/quiescence/identity retention still need implementation/proof |
| Keep all unknown forever | Honest and no new producer risk | Current PR40 behavior retained;does not design the requested continuity prerequisite |

The choice is the author's under standing delegation, not a claim that the user
approved actual producer execution. Source facts about missing births cannot be
repaired by hashes, FD numbers, inode/device/path equivalence, PID or later reads.

## Future capture architecture — not implemented

1. Fixed PID1 opens required stdio/control/read inputs; no new target references
   are acquired merely for observation. Before first managed fork, prepare a new
   **bootstrap issuer epoch**, separate from the managed-root scope.
2. A source-local bootstrap records the actual task/files_struct and selected
   local file values. Object-local immutable diagnostic tags distinguish
   FIRST_OBSERVED/PRE_ARM_SEED from ALLOCATION/POST_INIT_ALLOC. Do not overwrite
   existing allocation-issued tags or create a new tag per alias. Allocation
   history before the seed stays unavailable, including task/table lifetimes.
3. Record explicit seed handles and consumed-copy links with source/profile,
   boot/issuer cohort, object role, generation and origin. Actual READ, existing
   reference-or-clear and STORE must pair to the same consumed local value.
   Inherited aliases carry the same handle **and original provenance**. Copying
   does not promote a seed, change its generation or prove its earlier lifetime.
4. Keep constructor completion distinct from task commit/abort. Retain unknowns
   and lost seed records; never rebuild them from child slots or expected fixtures.
5. A new version/profile/availability-aware decoder must retain all raw bytes and
   reject mismatched domains/cohorts. Do not edit or silently upgrade CPS/CPCv1.

**Root-selection trap:** assigning PID1's old `cpl_scope_cookie` as a seed would
make PR40's `if(current->cpl_scope_cookie)` enroll children under the wrong root.
Use separate issuer/identity provenance fields and explicit first-root logic in a
future patch. A task identity is not a managed-root membership grant.

**Unresolved prerequisites:** prove valid initial tag state on every admitted
allocation route (selected zalloc path alone is not full coverage), no stale tag
on reuse, nonwrapping issuer or fail-closed epoch end, origin immutability, safe
publication under competing seeds/allocations/frees, and lifetime validity of each
borrowed local object. Exclude all relevant mutators/sharers/outstanding installs
before claiming a protected seed cut. file_lock alone explicitly does not exclude
lockless fd_install; one CPU, PID1, a stopped caller or emitter RCU drain do not
prove quiescence. On unmet premise emit unavailable/abort, not a trustworthy seed.
No new buffer capacity, timing/performance bound or empirical threshold is chosen.

No persistent pointer map, address/PID/inode wire identity, extra observer pins,
global observer effect lock, background collector, host tracing, device operation
or application capability is designed into this bounded proposal.

## Synthetic semantic schema and checker

`inherited-ofd-provenance-design-v1`, proposed profile
`PR40_PRIVATE64_BOOTSTRAP_DESIGN`, domain `PROPOSED_LINEAGE_V1`.
This domain is a proposed program-record sequence, not kernel-effect linearization
and **not a merge of existing CPS/CPC ordinal or timestamp domains**. The checker
tests internally declared same-domain order/pairing only, not real causal truth.

Top-level closed fields schema,evidence_class,context,objects,copy. Context binds
exact PR40 base/selected-source manifest and non-identifying boot/issuer tokens.
Objects:max68,positive UInt64 cookies,distinct global issuer IDs,typed roles,
generation0 only,no within-profile reuse. Seeds must precede arm,declared initialized
allocations follow arm and precede copy begin. One origin per handle;duplicates,
wrong role/generation/cohort or stage promotion reject. Generation0 is a known
value; None is unavailable; cookie0 is never an identity in this semantic model.

Copy references parent/source (optional),child,destination (optional only failed
constructor),arm/begin/return/finalize anchors and exact terminal result/reason.
The new child and available private destination must reference ALLOCATION/
POST_INIT_ALLOC objects: a pre-arm seed cannot identify a newly allocated fork
subject. Existing parent/source/OFD objects may retain FIRST_OBSERVED provenance.
SUCCESS/COMMITTED require NONE; task abort after success has TASK_INJECTED/TASK_FAILED;
failed constructor has an explicit failure reason,aborted COPY_FAILED and no
binding links. Successful copy of an aborted child is diagnostic,not child inventory.

Bindings:max64,ascending unique fd0..63,typed pointer presence and source/destination
OFD references. Exact read→branch→store order and paired read ordinals required.
PRESENT needs REFERENCE,NULL needs CLEAR_OPEN and no OFDs. Known OFDs must match;
unknown on either side is retained without copying the known neighbor into it.
FD is only a binding locator. Distinct handles are not merged by equal attributes.
The vector may be partial and omits flags/bitmap/slot generation: **not** a full
copy receipt or lifetime inventory and cannot enter the PR35 oracle.

Output frozen origins preserve seed provenance; conditional synthetic links only
for known-parent/source,successful committed,equal-known-OFD rows. Missing values
are explicit diagnostics,not structural zero/false defaults. An empty vector may
be consistent but proves neither a workload nor coverage. `allocation_history_complete`
is fixed false even with all-allocation synthetic premises. There is no ingestion
state machine or cross-receipt anti-replay/origin retention proof. Coherently
fabricated source labels/claims remain undetectable. Canonical SHA256 is content
identity only,not authenticity,freshness,authority or application approval.

## Future wire proposal / mapping

Positive UInt64 handles/ordinals,UInt64generation,UInt32FD(logical0..63),typed role/
origin/stage/status enums,explicit availability union, bounded ordered vectors.
No cereal/Cap'n Proto tags assigned or changed. Version semantic/stage/unit/cohort
changes; source revision remains separate. Missing origin/issuer/seed record must
not default to ALLOCATION. Precision/timing is not inferred from record ordinals.

| Existing PR40 item | Meaning for new design |
|---|---|
| Source local pointer read/ref/store pairing | Reusable mechanical source semantics,not bootstrap provenance |
| Known post-arm OFD tag | Context for a future origin-aware record,not complete allocation history |
| Unknown parent/source/pre-arm OFD | MISSING;must remain unavailable in current actual captures |
| Scope/task/namespace cookies | Need explicit issuer/scope split,origin and new cohort/version |
| Balanced own-buffer counters | Local diagnostic only;not global seed/copy coverage |
| Actual CPCv1 captures | Unsupported by this SYNTHETIC_ONLY checker,no adapter/relabeling |

Required future tests: alias vs independently opened equal-data files;unknown and
missing seed emission;seed failure/buffer overflow;duplicate/competing issuance;
object reuse/wrap/stale origin;constructor/task failures;wrong paired consumed read;
cross-epoch/root selection;unproven mutator exclusion;no added refs;actual source
and full original-byte capture. These remain future producer obligations.

No VIN/dongle/route/GPS/driver/rawCAN/model/images. No estimator/application/owner
integration,vehicle assumptions or permission changes. Prior PRs/main stay frozen.
