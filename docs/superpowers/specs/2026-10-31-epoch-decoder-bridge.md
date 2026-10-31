# Close the PR48 offline C-output/full-decoder acceptance gap

Base4371dfe5e69878665abcb9133cc20d5e0451949d; original PR48 and all previous
blobs/assets remain unchanged. The user approved PR18's scope as offline
schema/controller patch storage/testing only, not deployment, Params writes,
vehicle execution or steering application. No merge or old PR edit is authorized
by this work. Routine menus are waived by standing inline execution preference.

## Selected approach

Add a repository-only userspace C integration probe and a pure checker in
`tests/epoch_decoder_bridge/`. Consume PR48's unchanged, hash-bound actual
OBJECT_FIELDS/HELPER/BUFFER/EMITTER/FORMAT snippets. The C harness emits a full
CPR2 frame: envelope/context are explicitly synthetic; TAG_SNAPSHOT payloads
come verbatim from the selected C formatter. Return original stdout bytes,
never regex-extract or reserialize raw_epoch before the existing exact v2
decoder. The checker calls that decoder directly and compares decoded values
against an independently literal expected UInt64 sequence.

The 11 values are0,1,4294967295,4294967296,4294967297,9007199254740991,
9007199254740993,9223372036854775807,9223372036854775808,
18446744073709551614,18446744073709551615. Original object and then saved
object are mutated after capture/emission to pin by-value behavior. Raw zero
is observed, not unknown. Unexpected unknown, altered context, missing/extra/
reordered rows and wrong stages must not pass this complete-case checker.

Closed test-local mutations: saved32,buffer32,signed,format32,mask32,float,
reread,unknown_status,legacy_marker. Width/type/format mutations fail compilation;
lossy-but-syntactically-valid output must reach the decoder and fail independent
expected values. Unknown-status and mixed-marker mutations fail decoding.

Do not modify legacy native_probe, old decoder, native input catalog, C kernel
delta, old evidence, workflow, installed src or any old test/acceptance rule.
Only new files and narrowly additive .gitattributes rules. This is an integration
test supplement, not a new producer/version/router or empirical adapter.

## Evidence and unresolved scope

The C process is a userspace faithful scalar stand-in containing actual-source
snippets, not an executing kernel/guest/device or a lifetime/publication proof.
The full frame is generated synthetic evidence. Existing decoder output is
WIRE_BYTES_UNTRUSTED/BLOCKED; all permissions/proofs remain false and actual
epoch/global loss unknown. No new kernel build, guest run or v1 record promotion.
The native gate requires a GNU-compatible C compiler (GCC or Clang) and preserves
gnu11/Wall/Wextra/Werror for both. Missing both fails before writing inputs;
there is no native-gate skip path. Compiler discovery is not ABI qualification.

Do not claim PR25 surrogate handling, PR33 exact-integer metadata, PR34 denied-FD
diagnostics or PR9 evidence-age policy resolved. Frozen historical files cannot
be edited without breaking existing history guards. New versioned corrections
or explicitly reviewed narrow history extensions need separate scoped work;
loosening guards to hide changes is excluded. This turn closes only the PR48
integration gap and records the approved PR18 boundary.

Alternative rejected: changing the old probe to return full bytes would alter
frozen sources/manifests and historical checks. Separate C/decoder unit tests
alone are the missing connection, not a substitute for it.
