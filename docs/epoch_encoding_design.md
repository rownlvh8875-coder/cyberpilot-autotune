# Lossless raw-epoch representation and version migration design

RAW_EPOCH_LOSSLESS_REPRESENTATION_DESIGN_READY
RAW_EPOCH_WIRE_MIGRATION_DESIGN_READY

Design readiness only. **No producer correction is implemented.** The test-only
Python package cannot establish C types, compiled ABI, runtime source binding,
lifetime, publication, membership, stable identity or atomic tag tuples.

## Basis and selected representation

Base PR46 `72362dcf235f91cbce30501aeeb72b66ee6c124c`. Its frozen source catalog
`docs/evidence/copy_reference_publication_sources.json`, canonical SHA-256
`11b7d1e538851ee4d93ceb5477a57a805833217c0c2824e711a0796de1c22044`,
is reused unchanged, including exact blobs, embedded excerpts and range hashes.
The source is Debian linux6.12.113-1, archive SHA-256
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`,
with the unchanged PR42 and PR45 patches identified in that catalog. It is an
audit reference, **not** a future corrected producer/binary identity.

| Layer | Selected source today | Future proposed contract |
| --- | --- | --- |
| Object `file.cpb_epoch` | u64 | u64, full unsigned 64-bit domain |
| Saved `cpt_snapshot.epoch` | unsigned int | u64, no narrowing |
| Buffer `cpb_record.raw_epoch` | unsigned int | u64, no narrowing |
| Wire `raw_epoch` | `%u` | canonical unsigned decimal, full UInt64 |
| Decoder | UInt64 bound, wider than current emitter | exact integer 0…18446744073709551615 |
| Old fake file probe | unsigned int epoch | not sufficient as an actual-source type test |

Exact source claims in the catalog:

| Claim | Path and inclusive range | Meaning |
| --- | --- | --- |
| OFD_TAG_LAYOUT | include/linux/fs.h:1075–1082 | Actual u64 epoch declaration |
| SNAPSHOT_RAW_HELPER | include/linux/cptagread.h:1–20 | Source-to-saved narrowing |
| BUFFER_TAG_TYPES | fs/proc/cpcopy.c:18–29 | Narrow saved record field |
| WIRE_OUTPUT | fs/proc/cpcopy.c:325–382 | Current v1 profile and `%u` output |
| PR45_DECODER_EPOCH | tests/guest_tag_snapshot/wire.py:149–169 | UInt64 decoder, not lost-bit recovery |
| PR45_STANDIN_EPOCH | tests/guest_tag_snapshot/native_probe.py:18–39 | Fake declaration already narrow |

The frozen catalog owns full-file Git blob SHA-1, SHA-256 and each range
SHA-256/base64; duplicating those bytes into a second manifest would introduce
another drift surface. The audit verifies all catalog excerpts/repository
files; `--source-root` additionally checks the preserved external source bytes.
Neither mode interprets C or proves a runtime witness. The broader copy-reference
argument, including its deferred caller/initial-lock citation minor, is unchanged.

The x86_64 unsigned-int boundary example 4294967296→0 demonstrates what a
narrowing conversion *can* do. It does not establish that any retained capture
lost bits. Current selected writes/observations 0/1 do not prove an exhaustive
all-writer invariant. `actual_epoch_loss` stays unknown. A decoder-only bound
fix cannot restore discarded source bits. Choosing a 0/1 schema would require
a separate exhaustive invariant proof; it is not assumed here.

## Scalar semantics and executable specification

Observed epoch: exact built-in integer in [0,18446744073709551615]. No bool,
float, signed-domain reinterpretation, masking or implicit string coercion.
`EpochScalar(None)` is UNAVAILABLE; `EpochScalar(0)` is observed zero. Frozen
values contain only immutable data. No mutable input collection is retained.

`tests/epoch_encoding_design/model.py` is a **synthetic-only executable design**.
It is not a CPRv2 decoder, receipt producer, actual-record adapter or installed
package. `encode_design` and `decode_design` recognize only the fixed ASCII
prefix `EPOCH_U64_DESIGN_V2`, schema `raw-epoch-u64-design-v2`, evidence
SYNTHETIC_ONLY, the fixed reference-catalog digest and these fixed stage labels:
`POST_EXISTING_REFERENCE_PRE_STORE` / `SAVED_SCALARS_AFTER_STORE`.

The remaining canonical suffix is exactly one of:

```
availability=OBSERVED raw_epoch=<canonical UInt64 decimal>\n
availability=UNAVAILABLE raw_epoch=UNAVAILABLE\n
```

Each `\n` denotes one LF byte, not two literal characters. Frames are bytes,
at most 512 bytes, one line, no CRLF, no leading zero except `0`, no sign,
whitespace variation, extra/duplicate/missing fields, alternate stage/profile,
non-ASCII or mixed records. This strict miniature grammar is a fixture contract,
not a proposed implementation of the full CPR framing. CPRv1 **and CPRv2** real
frames are rejected. No legacy upgrade function exists.

Content digest is SHA-256 of canonical fixture bytes. Same content gives the
same identity; unknown differs from observed zero. It is never authenticity,
source/binary attestation, safety approval or an AuthorizationGrant.

`assess_pipeline(source,saved,buffered,wire,decoded)` compares independently
supplied synthetic values across adjacent layers. It returns all mismatch
reasons in stage order; malformed wire raises ValueError. `consistent` only
means scalar equality, `available` means every scalar was supplied; neither
is eligibility, correctness of a C implementation or runtime qualification.
Every result remains SYNTHETIC_ONLY/BLOCKED, all nine permissions and both
qualification flags false, actual epoch loss/global drops unknown, future
producer revision unknown. Even a fabricated consistent fixture cannot
acquire authority. This is not an epoch/generation or lifecycle state machine.

## Proposed future full-wire migration

The following are **proposals, not published or reserved runtime identifiers**:
`CPR_META version=2 profile=POST_REFERENCE_RAW_EPOCH_U64_V2` and a distinct
release such as `6.12.113-cptagread-u64-v2`. A future implementation must define
and freeze the complete frame/cohort contract before acceptance; this miniature
codec is not its implementation and no cereal tags are allocated.

1. Keep CPRv1 bytes, fixtures, parser, kernel patches and source/binary hashes
   unchanged. Preserve old records' existing classification, never promote or
   rewrite their low bits as a proven full-width source value.
2. A future corrected producer must publish a new exact source+patch/build
   identity, release, wire version and profile together. A version string or
   source digest alone does not attest the executing binary.
3. Future full decoder selects exactly one known version/profile/source cohort
   per frame; rejects mixed metadata/events/end markers, duplicate metadata,
   missing/unknown fields and silent fallback. V1 readers must reject V2,
   V2-only readers must reject V1. Any later multi-version router keeps decoded
   types/evidence profiles separate rather than coercing to a common qualified
   receipt. There is no such router in this task.
4. Canonical unsigned decimal exactly represents all 64 bits. JSON evidence
   interchange uses decimal **strings**, not JSON numbers or JavaScript Number.
   Python uses exact int; future non-Python consumers need an exact UInt64 or
   BigInt domain, never Float32/Float64 or a signed-only intermediary.
5. Observed raw zero is valid. Missing/not-captured epoch needs an explicit
   availability state and no numeric payload, not zero filling. A captured
   scalar need not be a valid stable identity, generation or namespace member.
6. No migration recovers unrecorded high bits. Retained loss/global counts stay
   unknown. A future bounded source invariant is a different proof obligation.

## Future implementation acceptance gates (not executed here)

Exactly one preferred correction path: retain the current scalar capture point
after the existing reference and before destination store, keep emission of
saved scalars after store, and correct **every** epoch representation layer.
Do not add object reads at POINTER_READ/STORE or change controller behavior.

- Inspect actual `struct file.cpb_epoch`, `cpt_snapshot.epoch` and
  `cpb_record.raw_epoch` declarations in the exact patched source. Require
  unsigned 64-bit type equality to u64, not only equal size or a fake struct
  with a convenient narrower member. Exact source pins/blob/range hashes
  must change for the corrected source; the PR46 reference remains historical.
- Compile actual-declaration static type/signedness checks under the exact
  target toolchain/architecture/configuration. Keep origin's separate u8/enum
  semantics; do not widen/change unrelated fields implicitly. A faithful
  stand-in may supplement tests but never replace actual-declaration checks.
- Preserve u64 assignments through the saved-value emitter argument and buffer.
  `%llu` must receive a matching unsigned-long-long argument, with an explicit
  lossless cast from u64 if the target typedef requires it. Assert the target
  representation width; do not blindly replace the format while keeping `%u`
  storage or pass a mismatched variadic type. Compiler format warnings are errors.
- Independently inject test-local values 0,1,2^32−1,2^32,2^32+1,2^53−1,
  2^53+1,2^63−1,2^63,2^64−2,2^64−1 through source→saved→buffer→formatted wire→
  exact decoder. Never modify a live host/device or infer a new production
  writer policy. Test the unavailable path separately from raw zero.
- Mutations to each layer (UInt32 saved/buffer, `%u`, signed storage, float
  transit, low32 masking, wrong profile, mixed cohort, unavailable→zero) must
  fail independent expected-byte/type tests. A self-roundtrip codec is not
  enough. Include capture-by-value tests that change the original object after
  capture without rereading it at emission.
- Build/source/config/toolchain/binary/original-capture digests and provenance
  need independent verification in a separately approved bounded implementation
  and guest validation task. No source type probe, producer build or new guest
  run has been performed in this design task.

Passing these future numeric gates still does not close reference binding,
publication ordering, tuple atomicity, identity/membership/generation, all-writer
coverage, loss accounting, perturbation, estimator or application obligations.

## Reproduction and retained boundaries

```
.venv/bin/python -m pytest -q tests/test_epoch_encoding_design.py tests/test_epoch_encoding_audit.py tests/architecture/test_epoch_encoding_design_boundary.py
.venv/bin/python -m tests.epoch_encoding_design.audit
.venv/bin/python -m tests.epoch_encoding_design.audit --source-root <preserved-exact-source-root>
```

`docs/evidence/epoch_encoding_design_cases.json` freezes 12 boundary cases
(including unknown) and six adjacent-layer loss/availability mismatches.
Its canonical digest is
`e177e7c7d95fb083e2f5ec10f63fffd89cdbbd60bd8128732b8e48ede5250e53`.
Further adversarial tests reject noncanonical encodings, alternate source/stages,
legacy/mixed prefixes and untyped values. Python coverage measures this
executable specification, not C/LKMM, kernel layout or vehicle behavior.

All blockers in `docs/copy_reference_publication_result.md` remain, notably
LOSSLESS_SOURCE_EPOCH_REPRESENTATION_UNQUALIFIED, EPOCH_RANGE_INVARIANT_UNPROVEN,
COPY_REFERENCE_RUNTIME_BINDING_UNQUALIFIED and TAG_PUBLICATION_RUNTIME_UNQUALIFIED.
No old source/test/evidence/workflow blobs or PR8/9/45/46 are modified.
No runtime producer, real-data adapter, estimator/candidate/application/owner
bridge, Params/controller/schema mutation, vehicle/device execution or upstream PR.
