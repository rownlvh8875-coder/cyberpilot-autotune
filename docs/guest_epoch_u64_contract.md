# Bounded offline UInt64 epoch producer correction

RAW_EPOCH_PRODUCER_PATCH_IMPLEMENTED_OFFLINE
RAW_EPOCH_ACTUAL_DECLARATION_GUARDS_COMPILED_OFFLINE
RAW_EPOCH_V2_DECODER_IMPLEMENTED_UNTRUSTED

Base PR47 `1d9207723ac63c90d8a2173bd401e3115abe2edf`; branch
`feat/lossless-raw-epoch`, stacked Draft base `design/lossless-raw-epoch`.
These statuses are not runtime qualification. No v2 guest execution/capture,
vehicle/device execution, estimator or application bridge exists in this task.

## Source correction and actual compile boundary

The unchanged Debian6.12.113-1 archive SHA-256 is
`ded797683f4161cfb8839b281b97f5be3fec02dc517ecea999798815ebeece33`.
Apply unchanged PR42 `tests/guest_bootstrap/kernel.patch`, unchanged PR45
`tests/guest_tag_snapshot/kernel.patch`, then the new
`tests/guest_epoch_u64/kernel.patch` (SHA-256
`c2e5fad7f6e968b66a92d395153afb173a050fd9cc492bf4c556b0f939c764fa`).
The third delta changes only include/linux/cptagread.h and fs/proc/cpcopy.c.
It was independently replayed with zero fuzz and compared byte-for-byte.

| Layer | v1 (preserved) | New selected v2 source |
| --- | --- | --- |
| actual file.cpb_epoch | u64 | unchanged u64 |
| cpt_snapshot.epoch | unsigned int | u64 |
| cpb_record.raw_epoch | unsigned int | u64 |
| raw_epoch formatting | `%u` | `%llu`, matching unsigned-long-long argument |
| decoder numeric domain | UInt64 despite narrow source | exact UInt64 |
| origin | u8 source / unsigned int saved+buffer | unchanged |

Static type-equality assertions reference the **actual** struct file,
cpt_snapshot and cpb_record members in kernel translation units, plus unsigned
64-bit type and printf width checks. The selected x86_64 kernel was freshly
built with `KCFLAGS=-Werror=format` using the new config/release and guards.
The new static driver was compiled with `-Wall -Wextra -Werror`. Neither binary
was executed. Actual config, selected object files, kernel/driver, build log
and recipe hashes are frozen; recorded compiler/cc1/assembler/linker/make
paths/hashes describe observations, not complete authenticated input closure.

Capture remains after the existing reference and before destination store;
emission receives saved values after store. fs/file.c and other selected
context sources remain byte-identical. No new writer, additional target
reference, guard, lock, object reread or membership/publication witness is added.
This corrects selected source representation, not the runtime binding proof.

## Native tests and limits

`native_inputs.json` embeds exact source/range bytes for actual object fields,
helper, buffer declaration, saved emitter and format call. Full-file Git blob
and SHA-256 plus range hashes bind them to the new source catalog. The opt-in
native probe rejects bundle drift and nonempty output directories before
compilation. It uses those exact snippets in a **userspace stand-in** with
faithful selected scalar aliases; this supplement is not actual-kernel/LKMM
execution or a layout/lifetime proof. Actual declaration assertions were also
compiled separately in the real kernel build; the stand-in does not replace them.

Independent literal decimals exercise0,1,2^32−1,2^32,2^32+1,2^53−1,2^53+1,
2^63−1,2^63,2^64−2,2^64−1 through source→saved→actual saved-emitter snippet→
buffer→actual printf snippet. The original test object and then saved object
are changed before output to check by-value preservation. Missing/not-captured
is a separate UNAVAILABLE result, never a fabricated observed zero. Production
still emits TAG_SNAPSHOT only for captured scalars.

Old source failed `saved_u64` and `buffer_u64` assertions before correction.
Six closed native mutations (saved32,buffer32,signed,format32,mask32,float)
must fail compile or independent value checks. They are test-local mutations,
not live source writers, and do not measure loss in any retained capture.

## v2 full frame and separation

Distinct markers are CPR2_DRIVER,CPR2_META,CPR2_COUNT,CPR2_EVENT,CPR2_END and
CPR2_EXIT. Metadata requires version2, profile POST_REFERENCE_RAW_EPOCH_U64_V2,
encoding UINT64_DECIMAL_V1 and release6.12.113-cptagread-u64-v2, alongside
the existing fixed case/capacity/CPU/epoch/source identifiers. These markers
are parsed profile claims, **not source/binary attestation**. Exact build and
source digests live in the separate frozen catalogs; no runtime attestation
of their execution is claimed. A forged matching frame remains untrusted.

TAG_SNAPSHOT adds raw_epoch_status. OBSERVED requires a canonical unsigned
decimal integer0…18446744073709551615. UNAVAILABLE requires literal UNAVAILABLE
and decodes to None. Zero is never missing. This producer emits only OBSERVED
when captured; accepting an explicit diagnostic unknown does not claim the
selected producer emitted it. Generation/lifetime/publication/membership remain
UNAVAILABLE. No installed C is repurposed, no physical estimator is connected.

The memory-only parser permits at most2MiB of ASCII serial and517 v2 lines
(512events plus5framing lines), one completed frame, exact field sets/enums,
monotonic source record IDs and coherent **local** reservation/commit counts.
LF and CRLF console transports are accepted; original-byte identity is separate
from this semantic parsing and no normalized capture artifact is substituted.
Boot noise is not evidence. Non-ASCII/control bytes, old marker prefixes,
unknown v2 records, mixed/duplicate/truncated frames, noncanonical numbers,
wrong modes/stages and unavailable/zero contradictions fail closed.

`CaptureV2`/`EventV2` are frozen tuple-valued decoder outputs, separate from v1
types; direct constructors are not an authenticity boundary. The v1 event-field
vocabulary is reused read-only, but its parser and lifecycle decision model are
never called. No actual-to-qualified adapter or v1→v2 conversion exists.
Every decoded frame is WIRE_BYTES_UNTRUSTED/BLOCKED, with all nine permissions
and runtime/source/lossless-runtime proof flags false and actual/global loss
unknown. Parser acceptance does not prove a complete source join or copy cut.

## Frozen manifests and reproduction

- Source catalog canonical digest:
  `985eb40287ab4cc2dda823a56eb3421b97b63038cdc1544e83bb22a5bb3e64f8`.
- Build catalog canonical digest:
  `624b45c9ec475ff2bb630d8efa4c2fd5e2e97be2e3d0a5b2d64513ada5b74cc7`.
- New kernel SHA-256:
  `7a6325da177fb9532db892a4f019c4fddc279ac048b284b7a8e3faa4cf84b2b5`.
- New static driver SHA-256:
  `1bf34b6686f88ca85877173633f0e020572c7ec07464b9ff4a5f5475b264c819`.

Permanent assets (not another plan's workspace):
`/workspace/scratch/epoch-u64-producer.ykWOCe`, corrected source at its
`linux-source-6.12` child. No prior source/build/assets were modified.

```
.venv/bin/python -m pytest -q tests/test_guest_epoch_u64_native.py tests/test_guest_epoch_u64_wire.py tests/test_guest_epoch_u64_audit.py tests/architecture/test_guest_epoch_u64_boundary.py
.venv/bin/python -m tests.guest_epoch_u64.audit
.venv/bin/python -m tests.guest_epoch_u64.audit --source-root /workspace/scratch/epoch-u64-producer.ykWOCe/linux-source-6.12 --assets-root /workspace/scratch/epoch-u64-producer.ykWOCe
```

Default audit verifies frozen catalog/embedded/repository bytes only. Explicit
roots also verify selected source/retained build asset bytes; neither reruns a
build or establishes runtime source binding. Toolchain binaries are recorded,
not independently reverified by this audit; input closure remains unqualified.
The copied prior patched tree is a build input with selected byte verification,
not an exhaustive authenticated source tree reconstruction.
