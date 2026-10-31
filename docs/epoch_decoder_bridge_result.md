# PR48 C stdout → full decoder integration supplement

PR48_C_OUTPUT_FULL_DECODER_INTEGRATION_TEST_READY
PR18_OFFLINE_PATCH_SCOPE_CONFIRMED

Base4371dfe5e69878665abcb9133cc20d5e0451949d; new branch
`test/epoch-full-decoder-bridge`, own stacked Draft base
`feat/lossless-raw-epoch`. No old PR was edited or merged. All prior tracked
blobs, source/hash manifests, acceptance/history guards, v1/v2 code and actual
assets are preserved; only new files and a narrow attribute rule are added.

## What changed

PR48 checked actual C payloads by regex-extracted numbers, while full decoder
tests used separate literal frames. The new test-only native tool consumes the
unchanged hash-bound actual OBJECT_FIELDS/HELPER/BUFFER/EMITTER/FORMAT snippets
and emits a complete CPR2 frame. Full original stdout bytes are passed directly
to the existing v2 `parse_serial`; no regex extraction, integer conversion or
raw_epoch reserialization occurs between C and the decoder.

The C value table and Python literal expectations are authored independently
at0,1,2^32−1,2^32,2^32+1,2^53−1,2^53+1,2^63−1,2^63,2^64−2,2^64−1.
The checker also pins the complete event/frame context, row order/counts,
stage labels and observed availability. Unknown cannot stand in for observed
zero. Original-object and saved-object mutation preserve by-value semantics.
Each loop emits its actual C formatted payload, not a Python surrogate record.

Four type/format mutations fail compilation. Masking, float transit and
post-mutation reread emit syntactically valid numbers but fail the independent
decoded cohort. The float mutation is bounded to avoid out-of-range float→u64
undefined behavior at U64_MAX. Bad status and legacy marker mutations fail
decoding. Source-bundle drift and nonempty output directories fail before writes.

## Evidence boundary

The wrapper, metadata, source IDs and context are deliberately **synthetic**.
The object-layout aliases, step and seq_printf shims are a userspace test
stand-in, not the full kernel/guest producer. In particular the capture-stage
label is a synthetic premise, not an observed VFS-reference witness. This closes
the scoped source-snippet C-output→full-decoder integration gap, not complete
kernel emitter/runtime/source-binding qualification. GCC or Clang in GNU C mode is required; the
native gate is not silently skipped if the compiler is unavailable.

Decoder results remain WIRE_BYTES_UNTRUSTED/BLOCKED, all nine permissions and
runtime/source/lossless-runtime proofs false, actual epoch/global loss None.
No new kernel build or guest/driver/device/vehicle execution, deployed schema,
controller/Params write, estimator/candidate/application/owner bridge, v1
record promotion, external AI or upstream PR. Existing regressions may run
their unchanged native units; that is not a new runtime qualification.

## Confirmed scope and remaining merge preparation

The user confirmed PR18 **offline schema/controller patch storage/testing only**.
That settles the scope question from the read-only chain review; it is not a
merge approval, deployment permission or independent GitHub review. Actual
deployment, vehicle operation, Params writes and steering application stay barred.

The following are **not resolved** by this supplement:

- PR25: lone-surrogate input may parse before canonical UTF-8 rejects it.
- PR33: float-equal integer limit metadata requires an exact-type correction.
- PR34: legacy HH03 DENY records FD0 instead of actual extra FD3; old captures
  must never be rewritten to manufacture missing provenance.
- PR9: admission-only versus commit-time evidence expiry semantics and its
  regression test remain to be agreed; no proven runtime exploit is claimed.
- PR8/9 remain separate Draft/dirty tracks; existing independent-review claims
  are not GitHub approvals. No old PR Ready transition or retarget occurred.

Directly changing frozen source would violate current exact-history guards.
Separate scoped/versioned corrections or explicitly reviewed narrow history
extensions are needed. Do not weaken tests or silently whitelist changes to
make a history check pass. Prior thirteen source obligations and all application,
fingerprint, build-closure, watchdog, executor, lifetime/publication, all-writer,
copy-cut, loss/perturbation and empirical-identification blockers remain.

## Verification

Baseline3907PASS38.11s. Missing bridge API RED→GREEN; focused33PASS,
new51statements28branches100/100; task1full3940PASS38.44s.
Final focused37PASS including old-blob/import and required-compiler guards;
full3944PASS106.42s, installed package coverage98.52%.
New58statements30branches100/100. Old source/
history/originalasset audits, native192/replay4, lint/format635files,
mypy71sourcefiles, build and fresh vanilla/researchwheel PASS. CRLF, exact-head
internal review and CI are recorded in the own Draft handoff after their actual
runs. Internal fresh-context AI review is not a registered GitHub approval or
independent human authorization. Python coverage is not C/LKMM/vehicle proof.

Compiler discovery/fail-before-write tests also ran RED→GREEN. The native
gate uses GCC or Clang with identical GNU C/Wall/Wextra/Werror semantics; it
does not add a skip when a compiler is missing. Historical native-test skips
are preserved, not counted as new integration execution. Local execution used
GCC; platform CI remains the check for its actual available frontend.

```
.venv/bin/python -m pytest -q tests/test_epoch_decoder_bridge.py tests/architecture/test_epoch_decoder_bridge_boundary.py
```

Next single task: scope a history-preserving PR25/PR33 strict-input correction,
with no relaxation of original acceptance criteria. Not started by this supplement.
