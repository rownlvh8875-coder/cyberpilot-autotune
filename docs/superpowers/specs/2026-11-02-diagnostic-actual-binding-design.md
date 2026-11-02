# Neutral actual-binding integration

## Intent and approved scope

Integrate the previously portable offline **reported-structure** checker into a
separate main-based Draft PR. Base: `a5d3514f23797829eb58d08c638b22cf4dd30c8a`.
This is not a friction receipt producer, evidence collector or admission bridge.
The user delegated routine design choices and approved continuing the integration.

## Architecture and approaches (implementer decisions)

Use one canonical namespace:
`cyberpilot_autotune.diagnostics.actual_binding`. Preserve all nine runtime source
files byte-for-byte: their imports are already relative. Add only an inert parent
namespace. No top-level compatibility alias or duplicate value class.

A main-based branch isolates this pure checker from the 42 unmerged stacked PRs;
stacking after #57 or editing it would unnecessarily couple their review histories.
Do not modify #8, #9, #16–#57 or their branches, main, or merged history.

Preserve the nine exact historical legacy sources as a test-only ZIP, with original
SOURCES.json and SHA256SUMS. This avoids rewriting the frozen content.py I001 import
block or changing global Ruff rules. A derived sorted copy would have a new byte
identity and is unnecessary here. The ZIP is an explicitly documented historical
source fixture, not active project Python and not a lint-clean original. Validate
its complete inventory and bytes before executing its actual old constructor in
an isolated `-I -S -B` child. No extraction, checkout-root sys.path, old worktree
fallback or fake old type. A prepared uniquely named vector module supplies only
synthetic test values. Keep the entire 476-case portable behavior suite.

Add a dedicated diagnostics CI workflow; do not edit the shared existing workflow
or relax its thresholds. Test namespace/shadow behavior, original-byte provenance,
full main regression, strict typing, lint, coverage, build and an installed wheel
outside checkout. Linux and Windows must run the new checks on 3.12.3 and 3.12.
Three historical source-inventory guards on main reject any new namespace.
Extend only their inventory accounting with the exact ten hash-verified new
diagnostics files; retain every existing source/golden hash and reject extra,
missing or modified diagnostics files. Never exclude the whole namespace blindly.

## Exact contract

Export ActualDiagnosticBundle, PrelaunchExpectedReference,
CaptureFreezeExpectedReference, ActualBindingAssessment and
assess_actual_binding(bundle, *, expected_pre, expected_post).
Frozen/slots value types, exact type checks, immutable tuples, stdlib only.
Six supplied canonical documents plus seven opaque raw roles; mandatory keyword
references with explicit None allowed but INCOMPLETE. No self-derived references.
Precedence: REJECTED > INCOMPLETE > REPORTED_TIME_ORDER_UNCOMPARABLE >
REPORTED_BINDING_CONSISTENT. Keep existing v1 domains and content identities.

Every result remains status BLOCKED, content NOT_EVALUATED, provenance
BLOCKED_NO_INDEPENDENT_VERIFICATION, history UNAVAILABLE, integrated_admission
false, and all nine permissions false. Consistency is not authenticity or safety.

## Non-goals and blockers

No runtime I/O, files, network, clock, process/thread, producer, VM/QEMU/guest/vehicle
execution, Params/controller/schema change, estimator, candidate, application/owner
bridge, longitudinal or upstream PR. Tests may prepare files and child interpreters;
this is not runtime capability. Do not promote v1 evidence or relabel old failures.
D01–D04 acquisition/trust/custody policies remain OPEN; same-owner HF storage is
not independent custody. APPLICATION_NOT_AUTHORIZED and all inherited scientific,
runtime, bounds, fingerprint, watchdog and external-executor blockers remain.

## Completion boundary

Fresh exact-head independent review, push only this new branch, create a Draft PR,
verify exact-head push and PR CI, preserve existing PR heads/base/draft states.
Do not Ready or merge. Retain local verification artifacts for audit.
