# Denial-FD point provenance: approved design

Approved in conversation before implementation. Base
`1c4fb3d26db913645cb2292f362396076e47adcb`, new local branch
`feat/deny-fd-provenance-contract`. Approval is for the exact 13-path local
implementation, not publication, merge, runtime or application authority.

## Intent and alternatives

Legacy PR34 (`3a831fdd423aa98638082eba126519db19f432d6`) HH03 records
PRE_EXEC descriptors0/3, snapshot count2 and DENY(EXTRA_FD,exec0,fd0).
Producer and checker both hardcode0. Preserve the complete original v1 cohort.
A derived overlay could explain extraFD3 but cannot claim the producer emitted3.
Rewriting old captures or a case-number0→3 remap is excluded. Author's recommended
choice, approved by the user: a separate immutable neutral contract, synthetic
validator and future wire/capture proposal; no legacy-to-new adapter.

## Scope and non-goals

Only UNEXPECTED_FD at PRE_EXEC_INVENTORY is supported for synthetic diagnostic
consistency. Missing/mixed inventory, binding, early-read and rebound reasons
are explicitly unsupported, never silently mapped to this model. Evidence kinds
may be represented structurally, but observed input is rejected as
PRODUCER_NOT_IMPLEMENTED. No actual producer, decoder, C patch, compiler, kernel,
guest, device, vehicle, Params, application/owner or empirical bridge.
No installed `src`, compatibility, CI, legacy fixtures/captures/source/validator,
original P/manifest, old18guard or prior PR/main changes. All nine operational
permissions remain false; legacy M1 and all qualification blockers remain open.

## Neutral API and semantics

`tests/deny_fd_provenance/contracts.py` defines frozen, slots dataclasses and
exact enums, with defensive tuple copies and structural validation:

- CaptureContext: capture_id, source_revision, source_manifest_digest,
  evidence_kind, clock_domain, root_birth_ordinal, exec_ordinal,
  optional fd_table_generation/ofd_generation. These are caller-authored context;
  local ordinals/slot epochs are not qualified kernel lifetimes.
- PointRef: context, snapshot_id, stage, seq, time_ns, optional
  slot_observation_epoch. Identity is capture_id+seq; clock/source/cohort explicit.
- FdWitness: ref and fd; InventoryWitness: ref, optional observed_fds and complete
  fd_witnesses. Snapshot group/context/stage must match, not a latest-seen join.
- InventoryPolicyContext: optional expected_fds, optional configured_subject_fd;
  context-only policy identity is a canonical digest of its fields.
- DenialReceipt: ref, reason, policy, optional snapshot, optional operation_fd,
  optional cause_fds and cause_refs; semantic schema
  `deny-fd-provenance-receipt-v1`.

UInt64 times/sequences/ordinals, Linux int FD domain0..2**31-1, exact built-in
integers (not Bool/Float); scalar strings and hashes checked. None differs from0
and empty tuple. FD sets sorted unique, at most the existing64FD resource bound,
not a safety threshold. No invented empirical thresholds or Unicode normalization.
Nested objects are revalidated at evaluator/digest boundaries.

`validation.py` exports `evaluate(receipt) -> DenialDecision`,
`canonical_digest(receipt)` and `policy_digest(policy)`. Structural invalidity
raises ValueError; semantically unsupported/incomplete data gives reasoned
REJECTED. Only SYNTHETIC evidence with SYNTHETIC_MONOTONIC_NS can yield
SYNTHETIC_DIAGNOSTIC_CONSISTENT, never runtime admission. Receipt has no authority
fields; decision's status is BLOCKED and permissions are fixed false.

For supported inventory checks, operation_fd must be None (no syscall target).
Configured subject0 is context only. Expected set must be a subset of observed;
observed-minus-expected must be nonempty and exactly cause_fds. Every observed FD
has exactly one witness. FD refs precede snapshot, which precedes denial, in both
seq/time; context/snapshot/stage match. Cause refs pair with sorted cause_fds and
must equal their actual inventory FD refs, including optional slot epoch. Reject
duplicates, future/missing/wrong-clock/cross-capture/exec/root references and stale
cause references. A known empty set is not unavailable. Synthetic HH03 uses
expected(0,), observed(0,3), cause(3,), operationNone, configured_subject0.

Digests use compact sorted JSON, explicit unknowns, reject nonfinite values,
content identity only. Optional final raw-capture digest is an outer post-close
envelope proposal, not required or self-referenced by the in-cycle event.

## Future wire and capture proposal (not implemented)

Proposed future wire `guest-data-fd-denial-observed-v2` is distinct from both this
neutral semantic version and PR33's qualified-v2 admission. While the target is
stopped, retain inventory/policy comparison and individual FD source refs before
reducing the result to an enum. Emit explicit configured subject/actual operation/
causal FD roles with source snapshot/capture identity. Monotonic timestamps are
observation times, not kernel linearization proof. Missing identities stay unknown.
No old v1 record is promoted/reconstructed into observed-v2 evidence.

## Exact successor policy

Only existing `tests/history_transition/policy.py` and
`tests/test_history_transition_policy.py` may change. Exactly11new paths are
listed by the successor manifest (package3, behavior/architecture tests2,
successor loader1, spec/plan/result3, schema/policy manifests2). Delta13paths;
cumulative old29+new11=40. No wildcard/path auto-expansion.

Keep original P127f485 and its22postimages, BASEs, old protected queries/scopes,
original seven NEW_PATHS and `_load` meaning intact. New immutable preregistration
P2 records source base1c4, prior P link,27preserved old-phase preimages and two
updated pre/postimages/modes. P2 descends from1c4 and precedes enabling the new
loader. Existing policy imports loader but does not contain P2's SHA. After P2,
new deny_fd_successor.py pins P2, reads its Git manifest, checks lineage and all29
old-phase states in HEAD/index/worktree, then returns only the11exact additions.
Missing P2 fails without fetch/fallback. New helper/files rely on final exact-head
review, not self-authentication. Per-command Git-clean CRLF equality follows the
original policy, never arbitrary normalization or a lowered hash criterion.

Current policy-test clone fixture uses P2, not by replacing original P. Keep all
old node IDs. The mutable working-manifest test first proves immutable `_load`
still ignores that file, then expects current preservation rejection. A separate
fixed local Git clone at1c4 runs the original acceptance node in an isolated
Python interpreter, preserving historical behavior without recursion or an
arbitrary revision/command API. Original five frozen characterization nodes remain.

## Verification and completion meaning

Test-first adversarial contracts, source/cohort/time/type/digest/unknown/multiple-FD
cases; pure architecture/no legacy bridge; immutable v1 source/capture checks;
actual Git mutations in HEAD/index/worktree, missing P2, preserved-file changes,
unlisted additions, modes and CRLF. Full pytest/audits/ruff/format/mypy/build,
fresh wheel/replay and one fresh whole-branch internal review. No weakening,
skip/xfail or automatic scope expansion. Local completion is CONTRACT_READY and
SUCCESSOR_POLICY_READY only. PRODUCER_NOT_IMPLEMENTED, LEGACY_PR34_M1_OPEN,
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED and APPLICATION_NOT_AUTHORIZED remain.
