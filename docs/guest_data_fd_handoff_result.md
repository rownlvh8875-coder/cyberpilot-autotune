# Fixed harmless guest DATA-FD handoff result

Base PR33 `74e3fdc67c2695a48035bf51758721f48bd5ae05`.
Branch `feat/guest-data-fd-handoff-prototype`; own stacked Draft, no prior merge.

## Delivered scope

[Contract and full wire fields](guest_data_fd_handoff_contract.md), frozen pure
observed-untrusted parser/checker, fixed static harmless guest bootstrap/payload,
checked diskless QEMU runner, exact source/build manifests and original serial
capture replay. Everything new is test/experiment/audit documentation; wheel
code, prior compatibility/evidence/fixtures/CI remain untouched.

The prototype answers a bounded question: did this fixed consumer receive the
expected sealed DATA FD across its one actual exec, and what bytes did this fixed
pread return? It is not a v2 qualified producer, full FD-table/OFD lifetime
observer, namespace/input closure, real source build or authorized executor.

## Actual guest observations

Frozen QEMU10.0.13 TCG and Linux6.12.113+deb13-cloud-amd64. Nine fresh actual
guest cases, not synthetic traces. Original complete serial bytes are retained
base64/gzip with exact size/hash, bound to build manifest and image content hashes.
No target ELF ever executed on host; only static compilation occurred there.

| Case | Events | Scoped outcome |
|---|---:|---|
| HH01 |22| FD0, exec0→1, actual17-byte pread, close/empty inventory/reap/release |
| HH02 |16| equal-byte different sealed object rejected before exec |
| HH03 |14| undeclared inheritedFD3 rejected before exec |
| HH04 |16| pre-barrier read denied at syscall entry, no returned READ |
| HH05 |17| deliberate CLOEXEC-loss fault injection, actual missing FD after exec, no READY/read |
| HH06 |31| deliberate close/dup2 reuse fault injection; actual new slot epoch1 and different OFD; next read denied before effect |
| HH07 |22| actual empty-file read result0/empty bytes, not unavailable |
| HH08 |25| corrected HH02 injection, authorized primary, no case-selected denial, full read |
| HH09 |22| corrected HH03 injection, no extraFD, no case-selected denial, full read |

Total185 events. HH01/07/08/09 are4 scoped transport observations; HH02..06 are5 expected
denials, not successful handoffs. Actual pidfd_getfd succeeds in this guest;
KCMP_FILE is0 across the retained pre/post-exec OFD and nonzero for HH06 reusedFD0.
Unavailable optional comparison paths are separately synthetic-tested; no generic
OFD identity/generation is invented from that local success.

Both actual target access flags and CLOEXEC come from target fdinfo; observer
reopens witness only object/stat/hash/seals. Bootstrap actual empty FD table is
observed before installation; UID/GID65534, NoNewPrivs1 and one thread are observed
before and after actual exec. Program object/hash comes from actual proc exe,
not argv. Parent held pins release only after actual wait/reap. Physical FD-table
generation, global prohibited-operation counts and dropped-event count stay null.

DATA objects use explicit MFD_NOEXEC_SEAL8 + seals47, with no fallback. Initial
actual RED exposed executable-default seal63; fixed creation mode, kept required47.
Another actual RED exposed dup2 clearing CLOEXEC on newFD0; source-pinned and
fixed negative observation semantics, retained read denial. Original failed serial
stays separately in prepared assets, never relabeled success.

Static probe924280bytes, SHA256
`72eee6f3996a27afb9543403d6256410abd9f4c6914356aa6c6c8dfe62e951bb`.
The exact compiler command is recorded, not a claim of reproducible toolchain/full
compiler-input qualification. Existing prepared assets are preserved.

## Verification checkpoint

- Baseline2678 passed. New full2747 passed34.58s; after the offline portability
  regression full2748 passed34.26s (70 additional tests). Actual execution still
  requires anchored Linux input reads; offline replay has no execution authority.
- Post-review author fix full2757 passed34.50s (79 above baseline), focused79
  including architecture;9 actual guest captures/185events/4scoped transports/5denials.
- Post-fix pure checker211/213 statements99.06%;58/58 branches100%, no exclusions.
  Two syntax-error exception lines remain uncovered. No C/kernel/VM coverage claim.
- Focused model/audit/VM/architecture69 passed before the portability regression.
  Missing API, negative cases,
  witness ordering, actual dup2 flags, process/timeout evidence preservation and
  kernel byte/range mutations have recorded RED→GREEN gates.
- Eight exact authenticated Debian source files/twelve semantic ranges: complete
  bytes, Git blobSHA1, SHA256 and numbered rangeSHA256. Source equivalence with the
  running kernel remains unqualified. Source archive and authenticated package
  identities preserved from PR32 and independently checked locally.
- Post-fix Ruff/format461, strict mypy71 installed+4 experiment modules green.
- Fresh vanilla/research installed wheel imports/replay/Carrot-contract,
  knowledge/owner/science/friction/receipt smokes green, outside checkout with-I.
  Wheel excludes tests/compatibility and NumPy before optional research extras.
- Existing H2..H7 source/history audits, observation-v2, previous actual capture
  replays and192 passive native patch tests green. Not vehicle/Carrot execution.
- Final exact-head source aggregate coverage, CRLF full replay, independent review
  and push/PR CI checkpoints are recorded in the own PR handoff after observation.

## Independent review and one author fix pass

Exact reviewed058738163e90436045c617069d1795487d2be57f: **C0/I2/M1**. See
[complete review and limitations](guest_data_fd_handoff_review.md). I1 live denial
was case-selected rather than observation-caused; I2 allowed impossible OFD
comparisons. Seven OFD counterexamples plus two corrected-injection cases were
RED. Both corrected inputs also failed in actual guest before the gate fix, with
authorized primary/onlyFD0 still spuriously denied. The single author fix compares
authorized primary/actual inventory and enforces per-FD reference lifecycle.
HH08/09 are additional fixed actual counterfactuals, not qualified admissions.
Full post-fix/coverage/CRLF/CI checkpoints are recorded in the handoff after fresh
observation. No second reviewer and no independent fix-head C0/I0 claim.

M1 is deferred: HH03's EXTRA_FD reason and inventory are correct, but DENY's
rejected-FD field reports0 instead of3. This remains a known diagnostic metadata
defect; no qualification/application capability is available from any receipt.

## Limits retained

Overall **BLOCKED**, all9 operational permissions false. Local READY is only the
fixed-case gate, not a production safety/enforcement boundary. The parent output
channel is not a cryptographic attestation. Point snapshots, optional KCMP_FILE
equivalence, program pin/hash and host180s timeout establish no continuous closure,
lossless observer, FD-table generation or qualified watchdog.

GUEST_DATA_FD_HANDOFF_FIXED_PROTOTYPE_OBSERVED.
GUEST_INPUT_HANDOFF_V2_QUALIFIED_PRODUCER_NOT_IMPLEMENTED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED.
INPUT_SEAL_BACKEND_UNQUALIFIED.
NO_PR30_QUALIFIED_SEAL_OR_CONSUMPTION_BRIDGE.
WATCHDOG_EXECUTION_MODEL_UNRESOLVED.
EXTERNAL_EXECUTOR_UNQUALIFIED.
RUNTIME_FINGERPRINT_UNCONFIRMED.
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED.
APPLICATION_NOT_AUTHORIZED.
Frozen development artifact/identification qualification blockers are unchanged.

PR33 deferred minorsM1/M2/M3 remain deferred; no old fix folded into this work.
No vehicle, actual compiler/source build, Params/write/controller mutation,
estimator qualification, candidate generation, application/owner bridge,
longitudinal, external AI, upstream PR or prior PR8/9/31/32/33 modification.

## Next single task

Design a qualified FD-table/OFD lifetime observer and its evidence/admission
boundary. It must address generations, generic alias/task lifecycle, continuous
inventory and trustworthy loss accounting before any qualified v2/PR30 bridge.
Do not infer actual-build or vehicle readiness from these nine harmless cases.
