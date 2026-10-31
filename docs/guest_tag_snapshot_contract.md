# Fixed guest post-reference raw tag diagnostic contract

## Scope and source cohort

This test-only prototype implements PR44's single next recommendation. Base
`eba2e74759cefa65a941ebce09ce2a4cfa33ec21`, branch
`feat/guest-post-reference-tag-snapshot`, stacked against
`design/owner-scoped-tag-read-protocol`. No prior source/test/evidence/CI blob is
edited. The two .gitattributes additions affect only the new package/evidence.

Fresh Debian linux-source-6.12_6.12.113-1 archive SHA256
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33` receives the
unchanged PR42 patch SHA256
`3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848`, then
tests/guest_tag_snapshot/kernel.patch SHA256
`78bada7bb59500a6c25d9d5e691867eccb27a3e7e5f10b9e958d8e2a308777f2`.
New release `6.12.113-cptagread-v1`, endpoint `/proc/cptagread`, wire CPRv1,
profile POST_REFERENCE_RAW_V1. Old CPB decoders/captures keep their old meaning.

## Capture versus emission

| Stage | Available observation | Not established |
|---|---|---|
| POINTER_READ | actual copy-local pointer presence and read ordinal, no OFD tag load | tag identity, lifetime, publication |
| existing get_file(f) | unchanged copy operation's existing reference acquisition | source-binding or acquire-publication proof |
| POST_EXISTING_REFERENCE_PRE_STORE | sequential READ_ONCE of cookie/scope/epoch/origin into local scalars | atomic tuple, stable identity or all-writer closure |
| REFERENCE | operation marker with fd/read link | identity tuple or verified witness |
| STORE | destination pointer store marker and presence, no OFD tag load | post-store tag value or completed task commit |
| SAVED_SCALARS_AFTER_STORE | by-value emission of the saved local scalars | target re-read, timestamp/HB/lifetime proof |

`fs/file.c:414-433` captures after the original get_file, before destination
rcu_assign_pointer; emission is after STORE. The native unit probe uses the actual
patch's scalar helper under a controlled stand-in layout and mutates the original
after capture. It does not check actual Linux layout, compiled ordering, LKMM,
tearing, reclamation or concurrency. READ_ONCE is not a lifetime/publication proof.

No new observer reference, lock or pointer registry is introduced. This only
splits the selected copy-loop's old pre-reference/STORE tag reads. Inherited seed,
binding/free/constructor readers/writers and unsupported routes are not repaired,
qualified or generally safe by implication. Successful disposable guests do not
resolve those source obligations. No saved stack or target pointer is queued.

## Availability and source links

TAG_SNAPSHOT contains UInt64 raw_cookie/raw_scope and zero-extended native
unsigned-int raw_epoch/raw_origin, exact fd/read/copy local context, explicit
capture/emit stages. Raw zero is an observed number; absent receipt is not zero.
Logical cookie is context-only and None unless positive with epoch1/origin1or2.
This is not a trusted baseline, birth/destruction history or globally unique ID.

generation/lifetime/publication/membership are literal UNAVAILABLE on wire and
None in Snapshot. NODE generation0 is only the inherited profile convention,
not a newly observed OFD-local generation. Nonce and hashes identify a content
cohort, not authenticity, freshness or authority. No addresses/VIN/driver/GPS/
route/CAN/images are exported.

Known deferred minor:the decoder currently applies a UInt64 bound to raw_epoch,
not the producer's native UInt32 bound. An impossible >UInt32 diagnostic epoch
can therefore parse and retain a source join,although logical_cookie is None
unless epoch1. Frozen actual epochs are within range;no authority is granted.

A complete available source join requires observed POINTER_READ, REFERENCE and
STORE of the exact same copy/context/fd/read ordinal in observed mechanical order
before the snapshot's emission. It is not a source lifetime/publication witness.
Missing records remain unavailable, even if an ordinal or later tuple matches.
Contradictory available stage/context/presence links are rejected. The diagnostic
does not infer a capture timestamp, target linearization or an assumed HB DAG
from emission n/local counters. Local count balance is not global completeness.

Available branch consistency is checked even without a surviving snapshot:
CLEAR_OPEN cannot coexist with present/reference/snapshot evidence;pointer/store
presence must agree. Consumed ordinals must precede each consuming local marker,
agree within a copy/fd,and cannot visibly belong to another fd in that copy.
Equal local ordinals in different copies are not interchangeable source receipts.

The decoder is closed/bounded and rejects wrong release/profile/stages, old
reserved record prefixes, unknown or duplicate fields, bad integers and frames.
Direct dataclass construction or hostile in-process mutation is not a security
boundary. Pure diagnostics accept decoded records, not arbitrary authenticated
claims. There is no actual-to-PR44-synthetic-oracle, PR35 or PR30 adapter.

## Execution and replay

Seven fixed cases only: NORMAL, SEED_LOSS, SMALL_BUFFER, UNSEEDED_OFD,
CONSTRUCTOR_FAIL, SNAPSHOT_LOSS, POINTER_LOSS. Two new loss cases reject the actual
selected copy1/fd5 record in the producer buffer. Capacity128 case loses its tail;
losses are never filled from fixture expectations. SEED_LOSS retains the inherited
missing origin NODE; raw snapshots do not recreate that origin witness.

Explicit opt-in only: `python -m tests.guest_tag_snapshot.runner --execute-fixed NORMAL`
or another fixed case, using matching prepared assets. Ordinary import/tests/
audit do not build or boot. Runner verifies frozen source, kernel, static ELF,
image and VM inputs before starting a process; no arbitrary command/host probe.
All guests:1vCPU512MiB TCG, no KVM/network/sharedFS/passthrough/device/vehicle.
The 120s process timeout is not a qualified watchdog or complete resource bound.

`python -m tests.guest_tag_snapshot.audit` replays original embedded bytes only.
Optional `--source-root /exact/new/patched/tree --verify-assets` checks source
files/ranges and prepared tools/archive/kernel/init/config plus retained original
serial/images; default false flags explicitly mean those external bytes were not
checked. Neither mode boots or upgrades evidence. Manifests are frozen finite
cohorts, not a generic portable capture admission protocol.

All nine operational permissions remain false. Task-authorized offline builds/
fixed guest tests are not authority granted by the resulting artifact. All
runtime/HB/lifetime/publication/history/cut proof fields stay false; global drops
and prohibited-operation counts stay None. No installed runtime, Params, controller,
schema, estimator qualification, candidate/application/owner or vehicle bridge.
