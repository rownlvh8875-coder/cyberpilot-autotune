# Guest input namespace / FD handoff design result

Base PR32 `0652c87c5e1da83d2cf4a3336713b9839e929ae3`.
Branch `feat/guest-input-handoff-design`; own stacked Draft, no old PR merge.

## Delivered — design, not runtime implementation

Normative [DATA-only handoff contract](guest_input_namespace_handoff_contract.md),
[source/admission mapping](guest_input_handoff_source_mapping.md), semantic schema,
counterexample matrix, exact source references and a **test-only SYNTHETIC oracle**.
No package under src/compatibility; no C/QEMU/guest/FD transfer, runtime producer,
host policy, compiler target, vehicle/Carrot/Params/application or PR30 adapter.
Prepared old binary assets and all prior code/evidence/CI/fixtures remain intact.

Preferred future architecture: sealed read-only descriptor bundle with logical
name→object manifest, controlled fixed bootstrap inheritance and actual post-exec
image/FD-table inspection before a supervisor-owned consumption barrier. This is
not a mount namespace or whole compiler/sysroot closure. An actual implementation
must independently establish flags, OFD identities, complete actual inventory,
loss accounting and enforcement before it can claim those facts.

## Bound identities and order

Context binds session/attempt/namespace generation, exact source revision,
VM/observer/consumer-image digests, consumer task/exec/FD-table generations,
clock and whole manifest. Each event carries the context content digest.
Member binds logical name, object/pin generations, local held dev/ino and exact
bytes/hash. Target binding additionally carries FD/binding generation, OFD
id/generation and actual RDONLY/CLOEXEC/full-seal context. FD0 is an actual value.

`PIN/SEAL_ALL → STOPPED → TRANSFER_ALL → BIND_ALL → READY → PREAD_FULL/CLOSE → FINISH → RELEASE_ALL → END`.

Atomic means barrier-consistent whole-set handoff, not a single syscall. Partial
transfer, early reads, unexpected descriptors, wrong object with identical bytes,
stale FD/OFD/transfer generations and premature release reject. v1 excludes dynamic
dup/fork/exec/reopen/rebind, mmap/metadata-as-read and partial/stream consumption.
Empty-file zero is valid; None/Bool/Float cannot impersonate kernel integers.
Declared-but-unread is not consumed. Standalone digests give no freshness/authenticity.

MFD_CLOEXEC bootstrap inheritance must be deliberate and source-bound; dup does
not convert O_RDWR into RDONLY. Reopening the consumer's proc FD on the observer
side does not establish actual-target flags or OFD identity. Caller inventory
hashes/coverage bools are simulated claims, never proof of complete real FD closure.

## Evidence and current verification checkpoint

- 57 published synthetic cases:5 internally consistent,52 expected rejections.
 These are not actual guest handoffs or empirical qualification.
- 7 exact Git blobs/11 source ranges at the base, byte size/SHA256/blob/range SHA.
 Worktree CRLF text is not treated as consumed source; no lazy fetch/substitute.
- Baseline2548; full2653 passed34.28s and coverage run2653 passed100.31s.
- Focused105 including architecture and schema/source/counterexample mutations.
- Pure oracle175/175 statements100%;47/48 branches97.92%. One closed-enum
 defensive branch remains unexecuted, not excluded. No OS/C/native coverage claim.
- Existing installed src aggregate98.52% (4350 statements/1192 branches).
- Fresh core.autocrlf=true clone exact `ca33788442dc9cbdd48120739cbd62986a3d1fb9`:
 full2653 passed36.89s.
- Ruff/format447; strict mypy71 installed+3 new audit/model/example modules green.
- Build/fresh isolated vanilla+research wheel/import/replay/Carrot-contract,
 knowledge/owner/science/friction/receipt smokes green. Wheel excludes tests,
 compatibility and, before research extras, NumPy.
- Existing H2..H7 source/history/observation-v2 audits, PR31/32 capture replays and
 192 passive native patch tests green. No new guest/target execution.

TDD evidence: missing model/audit RED;9 kernel-identity numeric-coercion RED→GREEN;
4 exact wire-field type/unit audit RED→GREEN. Published source range bounds were
checked against numbered exact source before manifest publication. No old source
or receipt was patched to make this design fit.

Fresh independent review and final exact-head CRLF/push+PR matrix are recorded
in the append-only review/handoff checkpoint once observed, not presumed here.

## Status

GUEST_INPUT_NAMESPACE_HANDOFF_DESIGN_READY, subject to final review/CI checkpoint.
GUEST_INPUT_HANDOFF_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
CONSUMER_FD_INVENTORY_PRODUCER_NOT_IMPLEMENTED.
HANDOFF_BARRIER_PRODUCER_NOT_IMPLEMENTED.
NO_PR30_QUALIFIED_SEAL_OR_CONSUMPTION_BRIDGE.

Overall BLOCKED; all9 operational permissions false, global prohibited-operation
counts unavailable. Preserve INPUT_SEAL_BACKEND_UNQUALIFIED,
GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED, BUILD_CONSUMPTION_CAPTURE_UNQUALIFIED,
RECEIPT_AUTHENTICITY_UNQUALIFIED, EXTERNAL_EXECUTOR_UNQUALIFIED,
OUTPUT_PROMOTION_BACKEND_UNQUALIFIED, APPLICATION_NOT_AUTHORIZED and all prior
frozen-development-artifact/factor/friction/vehicle-bounds/fingerprint/runtime
representation/watchdog/parked-runtime blockers. No ready vehicle or real build.

## Next single task

Implement one **fixed harmless guest DATA-FD handoff prototype**, separately
scoped/reviewed, to test actual controlled bootstrap inheritance, target flags,
pre/post inventory, barrier, object/pin binding and close/reuse counterexamples.
It must expose unavailable OFD/coverage/enforcement facts honestly and remain
unqualified; it cannot infer a PR30 witness or start a real build/vehicle.
