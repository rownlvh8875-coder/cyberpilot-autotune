# Disposable guest post-reference tag diagnostic

## Intent and boundaries

Implement the single follow-up recommended by PR44, based on exact
`eba2e74759cefa65a941ebce09ce2a4cfa33ec21`. Observe what raw OFD tag scalars a
bounded copy operation reads after its existing get_file(f), before destination
ownership transfer. This is not lifetime/publication qualification. Every result
is OBSERVED_UNTRUSTED/BLOCKED; all nine operational permissions remain false.

Use a fresh source/assets prefix and new CPRv1/profile, never upgrade old CPB
records/codecs. Preserve every existing tracked blob except narrow new-path
.gitattributes additions. No installed package, controller, cereal, Params,
vehicle/device/host policy probes, shared-branch write or merge. Software-only
1vCPU/512MiB TCG guests have no network, KVM, shared filesystem or passthrough.

## Approaches — author choice under standing autonomous execution

1. New observer reference/lock: changes target lifetime; rejected.
2. Reinterpret old pre-reference READ/STORE: wrong stage; rejected.
3. Fresh delta on the frozen PR42 patch, split pointer markers from tag loads,
   save raw scalars under the existing operation reference, emit saved values
   after STORE: selected. Costs inherited source gaps and no general safety claim.

Inline execution and a fresh whole-branch final review follow the standing
workflow. Routine question/design approval gates are opted out by the user's
autonomous execution instruction; these implementation choices are the author's.

## Capture and wire

New tests/guest_tag_snapshot package and /proc/cptagread endpoint. Apply the
unchanged tests/guest_bootstrap/kernel.patch, then the new delta to fresh exact
Debian 6.12.113 archive bytes. New release 6.12.113-cptagread-v1.

POINTER_READ exports presence and consumed ordinal only, with no OFD tag load.
REFERENCE is an operation marker, not a witness. A local snapshot copies raw
cookie, scope, epoch and origin after get_file and before rcu_assign_pointer.
STORE exports presence/read link only. TAG_SNAPSHOT emits those saved scalars
after STORE; no target pointer is dereferenced by its emitter. Source stage and
emission stage are distinct. No observer reference or lock is added.

Raw integer zero is observed data, not missing data or valid logical identity.
No object generation is measured. Lifetime, publication, membership and generation
witnesses remain UNAVAILABLE/None. Existing context IDs are unqualified context,
not verified subject protection. No adapter to PR44's synthetic evaluator or
PR35/PR30 is implemented. Seed and other inherited readers are not repaired or
qualified by this narrow copy-loop change.

Seven fixed cases: NORMAL, SEED_LOSS, SMALL_BUFFER, UNSEEDED_OFD,
CONSTRUCTOR_FAIL, SNAPSHOT_LOSS and POINTER_LOSS. New losses are real buffer
rejections of selected records. Missing pointer or reference/store records never
become recovered receipts from an ordinal or matching fixture. Partial captures
remain diagnostic; contradictions in available context/order are rejected.

Closed bounded decoder rejects old versions, unknown fields/enums, duplicate
fields, noncanonical/out-of-range integers, wrong release/profile and incomplete
frames. Pure assessment reports observed snapshots and available source links,
not qualified history/cuts/HB. Local count balance is distinct from global drops.
All global drop/prohibited counts stay None.

## Verification and handoff

Tests precede decoder, diagnostics, native scalar helper and audit APIs. Literal
synthetic wire expectations are independent of actual captures; actual original
bytes and semantic signatures are frozen separately. Boot the unchanged PR42
kernel with the new driver as the actual missing-interface negative baseline.
Build fresh kernel/static init and run all seven fixed guests, retaining original
serial/images and source/build provenance. Ordinary pytest/import/audit never
builds or boots; runner is explicit opt-in and hash-bound.

Audit repository inputs, both source profiles/ranges, build tools, images and
actual serial bytes. Replay all old audits/regressions, native/replay goldens,
lint/format/type/build/fresh wheel and CRLF checks. Review exact final head and
publish only own stacked Draft with exact-head push/PR CI. Retain all inherited
blockers/minors. Recommend only one next task and do not treat capture success as
protocol/runtime or vehicle readiness.
