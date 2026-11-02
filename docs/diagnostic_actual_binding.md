# Neutral actual-binding diagnostics

This package assesses only the internal **reported structure** of supplied bytes.
It does not collect evidence, attest a launch, inspect a kernel, qualify a device
or authorize any operation. It is unrelated to the controller friction receipt.

Canonical import: cyberpilot_autotune.diagnostics.actual_binding.
Public frozen/slots values: ActualDiagnosticBundle, PrelaunchExpectedReference,
CaptureFreezeExpectedReference, ActualBindingAssessment.
Pure evaluator: assess_actual_binding(bundle, *, expected_pre, expected_post).
Both references are required keyword arguments; explicit None makes the evidence
incomplete. No factory derives them from the candidate bundle.

The bundle is six canonical JSON documents (baseline, command, preflight, intent,
exit, snapshot) and seven opaque byte roles (telemetry, console, cli_stdout,
cli_stderr, record_json, initrd, exit_receipt). Opaque raw bytes are never parsed.
None is unavailable, unlike present empty bytes or numeric zero. Exact type,
shape, version, context, canonical encoding, hashes, chronology and reported
process-state consistency are checked without I/O, clock acquisition or execution.

Status precedence is REJECTED > INCOMPLETE >
REPORTED_TIME_ORDER_UNCOMPARABLE > REPORTED_BINDING_CONSISTENT.
Even the last outcome is status BLOCKED, content_status NOT_EVALUATED,
provenance BLOCKED_NO_INDEPENDENT_VERIFICATION, history UNAVAILABLE,
integrated_admission false and all nine permissions false. No application,
estimator, owner or runtime layer consumes this API.

## Integration and provenance

The nine runtime modules are byte-identical to the pinned portable release;
only their package path changed. No top-level alias, duplicate class, v1-to-v2
promotion, schema/wire version bump or authority was added. New .gitattributes
rules preserve their LF byte identities on Windows as well as Linux.
See evidence/actual_binding_integration_sources.json for original source hashes
and the HF commit/archive identity. A same-owner backup is not independent custody.

The complete 476-case portable suite is relocated, with extra integration tests.
The actual old SevenInputReference constructor is imported from an exact nine-file
historical ZIP closure, not a fake substitute or the old product checkout.
The ZIP intentionally preserves the original content.py I001 finding; it is
immutable test data, not active lint-clean project Python. The source fixture
README describes hash/inventory/origin checks and missing/corrupt negatives.
All active Python remains under repository-wide Ruff and strict typing gates.
The source distribution explicitly includes this test fixture; the wheel does not.

Three historical inventory tests now allow exactly ten hash-verified diagnostics
files (nine unchanged modules plus inert parent). Their original source/golden
hash assertions are unchanged. The H6 history validator accepts only those exact
test edits and the exact source-distribution fixture include, with no broad
path exemption. Any additional edit still fails. H6 estimator/candidate code and
all scientific policies/results remain untouched.

Existing CI is byte-unchanged. The additional workflow checks Linux/Windows and
Python 3.12.3/3.12, diagnostics statement >=98%, branch >=95%, source packaging
and a vanilla wheel outside checkout. Existing common CI still runs full
regression, lint, mypy, audits, replay goldens and optional-dependency smoke.
These are software checks, not runtime/kernel/vehicle qualification.

## Retained blockers and next boundary

D01, D02, D03, D04 remain OPEN: acquisition/trust/custody choices are not supplied
or solved by reported hashes. No authenticity, anti-replay, independent custody,
retention duration, native containment or compromised-tool guarantee is implied.
APPLICATION_NOT_AUTHORIZED, frozen-development artifact and factor-identification
blockers, vehicle bounds, runtime fingerprint, watchdog, external executor and
parameter-identification qualification blockers remain unresolved.
Previous technical debts outside this integration are not silently closed.

Existing #8/#9 and #16–#57 remain untouched. This independent main-based Draft PR
is not a Ready/merge approval and may need explicit inventory-patch reconciliation
when integrating the older stack. Do not automatically merge, deploy, run a
collector or start vehicle/runtime qualification after these tests.
