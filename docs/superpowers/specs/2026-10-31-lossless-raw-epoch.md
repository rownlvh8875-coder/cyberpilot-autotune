# Lossless raw-epoch representation design

This is a design-only successor to PR46 at
`72362dcf235f91cbce30501aeeb72b66ee6c124c`, not a producer correction.

The selected source declares `struct file.cpb_epoch` as u64 but saves it in
unsigned int, buffers unsigned int and prints `%u`. A UInt64 decoder cannot
restore bits already discarded. Existing 0/1 observations neither demonstrate
actual loss nor prove an exhaustive writer range invariant.

## Contract

Preserve UInt64 from source through saved scalar, buffer, decimal wire and
decoded integer. Reject booleans, floats, signed/out-of-range integers and
noncanonical decimal. Unknown is an explicit UNAVAILABLE state, never zero.
Store large boundary fixture values as decimal strings, not JSON numbers.

Provide a pure, frozen test-only scalar and a small executable design codec
with prefix `EPOCH_U64_DESIGN_V2`. It is deliberately not a CPR producer,
receipt parser, adapter or runtime proof. Its fixed source-catalog digest is
an audit reference, not the identity of a future built producer. Reject
legacy/mixed frames and wrong stage, schema or reference cohort. Compare
independently supplied source/saved/buffer/wire/decoded synthetic values.
Every decision is SYNTHETIC_ONLY/BLOCKED, with permissions and proofs false,
actual loss/global counts unknown and no future producer revision.

Propose a separately versioned future full CPRv2 profile; never reinterpret
CPRv1 as lossless. Document exact actual-declaration type checks, UInt64
formatting and boundary/mutation tests required of a future implementation.
Python tests cannot establish C ABI, compiled type fidelity, reference
binding, publication, tuple atomicity, membership or runtime qualification.

## Deliverables and boundaries

`tests/epoch_encoding_design/model.py` owns immutable scalar, fixture codec,
content identity and synthetic pipeline comparison. A separate read-only
audit verifies literal fixtures and the existing frozen source catalog.
Architecture tests keep these out of installed packages and preserve all
prior tracked source/tests/evidence/workflows byte-for-byte.

Human docs describe migration and future acceptance gates. No actual kernel,
producer, schema, vehicle, Params, controller, estimator or application
changes. No prior record promotion, source rebuilding or new guest run.
All previous blockers remain. Publish only a new stacked Draft PR, with no
merge or edits to other PRs. Inline execution and routine design/integration
menus are waived by the user's standing instruction to proceed autonomously.
