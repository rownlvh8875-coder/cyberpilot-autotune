# Bounded UInt64 producer correction

Implement the next single recommendation of PR47, base
`1d9207723ac63c90d8a2173bd401e3115abe2edf`. Keep all previous tracked blobs,
assets and PRs unchanged. Work inline in a new branch, publish only a new
stacked Draft; no merge or shared-branch updates. The user has waived routine
design/integration menus and asked to proceed autonomously.

## Chosen approach

Add a third, separately versioned kernel delta on the unchanged PR42+PR45
patch chain. Preserve actual u64 cpb_epoch through u64 saved/buffer fields and
correct unsigned-long-long formatting. Compile static type/signedness guards
against the actual kernel declarations; keep origin unchanged. Preserve the
existing post-reference/pre-store capture and saved-only post-store emission.
No new tag writer, extra object reference, collection thread or capture point.

Use distinct CPR2_ markers throughout a new v2 driver/frame, profile
POST_REFERENCE_RAW_EPOCH_U64_V2, encoding UINT64_DECIMAL_V1, release
6.12.113-cptagread-u64-v2. This prevents mixed-version end/event markers from
being silently accepted. Keep v1 files/parsers/records unchanged; no converter.
Add raw_epoch_status=OBSERVED to emitted snapshots. A v2 structural decoder
may represent explicit UNAVAILABLE/None, never replace it with zero; this
producer emits snapshots only when captured. Parsing does not establish origin,
binary provenance or actual execution: all decoded frames are WIRE_BYTES_UNTRUSTED,
BLOCKED with all nine permissions/proofs false and global loss unknown.

Alternatives rejected: decoder-only tightening cannot recover bits; imposing
a 0/1 writer bound lacks a proof; editing v1 would destroy historical identity.
These are author choices, not new safety approvals.

## Verification boundary

Compile the actual corrected kernel/driver offline in a new permanent asset
directory, never modify prior source/build trees. Record exact source/patch,
config, compiler and binary hashes. Real kernel type guards are distinct from
a supplementary faithful-layout native scalar test. That native test must
consume frozen actual source excerpts and verify independently literal decimal
values at 0,1,2^32−1,2^32,2^32+1,2^53−1,2^53+1,2^63−1,2^63,2^64−2,2^64−1;
unknown and original-object mutation after capture are separate tests.
Narrow saved/buffer, signed type, bad format, low32 masking and float-transit
mutations must fail. Test-only stand-ins do not prove C ABI/runtime binding.

Add portable source/patch audits and v2 decoding/adversarial tests. Preserve
all installed source/schema/controllers/Params, estimator/application/owner
types and existing workflow files. No vehicle/device/host probes or new guest
execution. No actual v2 captures, old-record promotion or qualification adapter.
All runtime, lifetime/publication, all-writer/range, source-hook, perturbation,
empirical-estimator and application blockers remain unresolved.

New source bytes and offline build may show the selected narrowing corrected;
they do not close LOSSLESS_SOURCE_EPOCH_REPRESENTATION_UNQUALIFIED at runtime.
Next separate task is a bounded software-guest v2 capture/verification cohort,
not a vehicle attempt. Do not start that task in this work item.
