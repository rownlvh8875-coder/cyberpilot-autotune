# H1 policy-independent outcome consistency repair

## Intent and scope

Fix cumulative-review Important-1 at exact base
`a8b2bf1e6f27a4157212298928a50c8e970babf5`. The user approved the
recommended bug-fix task and delegated implementation choices. This is a small
supplied-record consistency repair,not a historical executor or authority grant.

## Approaches

The implementer's choice is a minimal invariant inside existing `_observed`.
A new evaluator/adapter would duplicate validation;making policy mandatory would
hide already available contradictions. Neither alternative is selected. The
existing Python API,wire schema,source pins and observation meaning stay unchanged.

## Required behavior

When collected_nodeids and outcomes are both available,an outcome outside the
collection rejects,regardless of exit status or optional policy. A completed
exit=0 record must have equal available collection/outcome sets. An incomplete
subset without a successful exit stays unavailable,not a fabricated failure or
pass. None stays unavailable and is not an observed empty tuple. Set ordering is
irrelevant;existing duplicate checks remain. Keep D499 and expected-policy checks.

Use reason `OUTCOME_COLLECTION_MISMATCH` for the independent contradiction and
`CASE_OUTCOMES_INCOMPLETE` for an incomplete subset. Known errors continue to
outrank unavailable peers. These are diagnostic reasons,not application reasons.

## Frozen history and bounded successor

Freeze old portability/current-normalization checks at literal base a8b2bf1,
retaining their old exact inventories and helpers. Add a separate literal
successor guard for four additions (this spec,its plan,the new regression module,
the descriptive registration) and four modifications (H1 validation,history guard
consumer,portability guard consumers,preflight range assertion). Do not widen
earlier allowlists. The new regression checks exact scope,unknown/status/alias/
duplicate rejection and the actual consumer's frozen/untracked checks. Preserve
all old nonconsumer functions except those three portability range consumers and
the one preflight range assertion explicitly requiring the new endpoint.

## Constraints and evidence

No src,dependencies,workflows,collector,fixture setup,host configuration,Params,
controller,schema,application,vehicle or actual H changes. No skipped test or
coverage-floor relaxation. All nine permissions remain false and all project,
historical replay,source atomicity,ENTRY/stack/executor/inventory/application
blockers remain. The historical operational I1 and original host-config equality
UNCONFIRMED are retained. Hashes are content identity only.

Observe new regression RED before code,then focused/full pytest,unchanged
coverage/audits/Ruff/format/mypy/replay/build/isolated wheel checks and a fresh
exact-head review. Use existing isolated worktree,append-only local commit(s).
No push,PR modification,merge,rebase,force-push,dispatch or HF upload in this task.
