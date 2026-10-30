# Guest-only harmless backend — partial result

2026-10-30 (Asia/Seoul). Base `8ef42c443887bf8f8d072256ed8268a75cec696f`.

## Outcome and authority

Implemented a repository-only, opt-in read-only USER_NOTIF broker and independent
LSM/cgroup guard **inside a disposable software guest**. HF01–HF24 all produced
actual measurements and satisfied their named, deliberately narrower assertions.
There are **zero fully qualified fixture PASS results**: six UNAVAILABLE, fifteen
REJECTED and three NOT_SUPPORTED. These outcomes are distinct from assertion
success. Missing full tracing is not zero effects or complete containment.

The user's approval of the previously described VM-only implementation is the
external operational scope. It permits this derived diskless guest, regular-file
fixtures, guest namespace/cgroup/BPF/seccomp operations and independent outer QEMU
termination. It does not approve an outer-host policy change, physical-device
test, native Carrot execution or deployment. The old design/protocol statements
that no host was selected remain historical snapshots; this result records the
subsequent explicit guest selection. A manifest or successful parser is not an
approval source.

All `runtime_qualified`, `device_class_qualified`, `policy_adopted`,
`candidate_generation_allowed`, `application_authorized`, `runtime_accepted` and
`owner_proposal_allowed` remain false. `STRICT_NO_DEVICE_ATTEMPT` remains policy;
the capability-closed discovery proposal is not adopted. Gate A remains BLOCKED;
B/C/D have not started.

## Actual cohort and execution boundary

- QEMU 10.0.13, `pc-q35-10.0`, TCG `qemu64`, one vCPU, 768 MiB. No KVM, NIC,
  shared host filesystem, persistent disk, QMP or passthrough. Serial stdio only.
- Actual boot: `6.12.113+deb13-cloud-amd64`; Debian source package `6.12.113-1`.
  Actual guest BTF SHA-256:
  `60d48cb878267965039e3ac985ec338a69ab741277ad954302239ba6cea77db0`.
- Preserved VM cohort:
  `d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c`.
  Its original tree/image/recipe were not modified. The new image has separate
  owned inputs. The runner verifies all 5,501 old extracted-tree entries plus
  archives/assets/release hashes before spawning its fixed QEMU argument list.
- Rootless private Debian package extraction; no host package installation,
  postinst/service/kernel modification, mounts, BPF or seccomp policy operations.
  Host GCC compiles fixtures, but **only the guest executes them**.
- clang 19.1.7, libbpf 1.5.0, Debian GCC 14.2.0-19. Dynamic guest loader/libs are
  explicitly bundled and hashed after static libelf linking failed. This is not
  complete host compiler/transitive loader closure qualification.
- Kernel hooks were studied at the actual Debian source version before the first
  guest load. Upstream v6.12 from the previous design is not promoted to this
  guest fingerprint. Signed APT release/index verification, normal TLS and date
  checks remained enabled. No network in the test guest.

The archive contains bootstrap console/null pseudo-node metadata. No host mknod,
fake hardware test node or device-class operation occurs. Those bootstrap guest
pseudo-nodes are not evidence of physical-device denial.

## Implemented behavior

The payload is moved to the guard's cgroup before its barrier is released,
chrooted to owned fixture files, stripped to UID/GID65534 and no-new-privileges,
and deprived of policy/control FDs. A trusted pidfd-based setup transfers only
the seccomp notification listener. The worker has a separate protected cgroup,
no policy/map/link FDs and its own restrictive seccomp filter. Rootful setup,
collector and termination supervisor remain trusted prototype components.

The broker binds one actual PID and notification, copies the path/open_how,
rejects unknown dirfd, ABI, flags, O_PATH, creates and writes, and opens only an
expected regular object beneath a broker-owned root using
`RESOLVE_IN_ROOT|RESOLVE_NO_MAGICLINKS`. It validates actual inode/device while
the object is live, not a durable inode-only identity. Successful read-only FD
injection uses `ADDFD_FLAG_SEND`; there is no CONTINUE or unscoped retry. Error
replies are explicit errno, never fabricated kernel absence.

The independent LSM hook preserves a prior denial, refuses character/block opens
in its bound cgroups and a specific lifetime-bound regular object. The cgroup
device program attaches deny-all, but **its device behavior is never exercised**.
Actual ordinary-file denial remains after collector death and after a payload
BPF tampering attempt. Audit records are file-open records, not syscall/FD proof.
Failed BPF verifier signed-return bounds were diagnosed against exact verifier
source and fixed without fallback or policy weakening.

## Actual fixtures and intentionally missing dimensions

All rows' narrow independent assertion checks succeeded. Final outcomes below
remain conservative because the full protocol is not yet implemented.

| HF | Actual named observation | Final outcome / remaining limitation |
|---|---|---|
| 01 | Read INSIDE through actual read-only injected FD0; actual expected object | UNAVAILABLE: no complete request/FD/exec ledger |
| 02 | Parent changes shared path after private copy; original copied path read | UNAVAILABLE: controlled buffer race, not all concurrent mutations |
| 03 | Symlink changed after copy; resolution confined or rejected | REJECTED: source drift, no full rename/mount race census |
| 04 | `/../allowed` clamped within IN_ROOT; actual inside object read | UNAVAILABLE: no full outside-object/effect collector |
| 05 | Real private guest proc-fd magic link rejected, no FD delivered | UNAVAILABLE: not every inherited-FD laundering route |
| 06 | Unbound numeric dirfd rejected before broker lookup | REJECTED: **no actual close/reuse/cwd-generation experiment** |
| 07 | Direct rename denied by payload filter; input unchanged | REJECTED: hardlink replacement not separately exercised |
| 08 | O_PATH refused EPERM before broker lookup | REJECTED: no LSM-hook proof for O_PATH is claimed |
| 09 | Unknown open_how flags EINVAL; x32-number EPERM | REJECTED: not every invalid ABI/size combination |
| 10 | IN_ROOT+BENEATH actual EINVAL, no fallback | UNAVAILABLE: scoped EAGAIN was **not produced** |
| 11 | Canceled actual notification; ID_VALID and ADDFD return ENOENT; reaped | REJECTED: actual PID reuse was **not exercised** |
| 12 | Guarded fork and static-helper exec both yield EPERM, two reaped | UNAVAILABLE: no full clone/task-birth/exec lineage ledger |
| 13 | Two real kernel file-open events; copied-event duplicate/drop/reorder detected | REJECTED: copies fault-injected, not actual kernel ring loss or unmatched syscall correlation |
| 14 | Actual observer SIGKILL, then guard still denies, child reaped | REJECTED: no complete channel/cgroup-exit evidence |
| 15 | Last listener closes; child receives ENOSYS and remains alive; cgroup.kill then actual SIGKILL/reap | REJECTED: separate termination observation, not watchdog qualification |
| 16 | Actual payload bpf syscall EPERM, subsequent guarded open EPERM | REJECTED: no actual privileged link detach or guard-death experiment |
| 17 | Actual threaded cgroup; cgroup.kill EOPNOTSUPP95; no payload | NOT_SUPPORTED: no best-effort fallback |
| 18 | Known injected ordinary FD and duplicate detected before payload | REJECTED: no exhaustive inherited/passed-FD inventory |
| 19 | Actual regular stand-in named loader.pyc changed and rejected | REJECTED: **no Python pyc/preload/sys.path execution or closure proof** |
| 20 | Generated fixed helper copied to writable scratch; executable open denied | REJECTED: not native-loader/JIT/mmap or immutable generated closure proof |
| 21 | Payload proposal field changed; trusted parent refuses adoption | REJECTED: narrow field-boundary test, not authority validation |
| 22 | Actual child pipe EOF without end marker; trace/counts remain unknown | REJECTED: no full source/clock/guard cross-correlation |
| 23 | Plain regular file named dev/kfd; broker returns policy EPERM without lookup | NOT_SUPPORTED: no actual device or driver test |
| 24 | Create/write/truncate request refused before lookup; no new file, original unchanged | NOT_SUPPORTED: read-only profile, not global absence of all effects |

Neither an empty audit nor these checks yields global prohibited-handle/effect
counts0. Both counts, complete syscall/FD trace, complete lineage, full object
receipt and trusted collector binding remain null. The partial adapter is
deliberately incapable of returning PASS. Pure types can represent a hypothetical
complete named fixture, but do not authenticate or establish its factual truth.

## Reproduction and evidence

- [Actual serial log](../compatibility/containment_backend_harmless/evidence/guest-run.txt)
- [Validated per-fixture results](evidence/containment_backend_harmless_results.json)
- [Build commands and input hashes](../compatibility/containment_backend_harmless/host/build_manifest.json)
- [Actual kernel source/range hashes](evidence/containment_backend_guest_sources.json)

The local prepared input paths in the build manifest are intentionally fixed.
The runner fails closed elsewhere; it does not install, fetch, choose another
kernel or fall back to the outer host. In this approved workspace, explicitly
select IDs, for example:

```sh
.venv/bin/python -m compatibility.containment_backend_harmless.host_main \
  --execute-guest --fixture HF01 --fixture HF15
```

There is no implicit all-fixtures or arbitrary command/native artifact option.
Default/import/parser tests never boot a guest. Package remains outside the
installed wheel and existing CI execution; default pytest only tests pure data,
fixed recipe, parser and architecture boundaries. Hashes identify content, not
authenticity, approval or safety. Mutable outer-host TCB/TOCTOU/complete compiler
closure remain unqualified; do not treat local checks as hostile-host protection.

## Verification at publication

- Full Python regression after review fix: 1,855 passed; 137 focused new pure tests
  passed. Installed-package combined coverage: 98.52% (1,852-test pre-attribute-fix run).
- New package pure-test combined statement/branch coverage: 81.70%. This includes
  unexercised fixed-runner failure branches; the actual 24-case guest run is
  separate evidence, not Python/C coverage. No C/BPF line-coverage claim.
- Global ruff check/format and strict mypy (installed source + new package) pass.
- Neutral sdist/wheel build and fresh isolated wheel imports, replay goldens,
  knowledge/owner/science/friction/receipt smokes pass, both without and with the
  optional research dependency. New operational tooling is absent from the wheel.
- Existing offline passive native patch regression: 192 passed; no deployment,
  runtime, empirical or application qualification. H6, H7 and patch-design source/
  history audits pass. Actual Debian kernel audit: seven files, ten exact ranges.
- [Independent branch review](containment_backend_harmless_review.md): C0/I1/M0 at
  `a5b071558720924491a48e4dc6fce953d57a3bff`; Important CRLF checkout regression
  reproduced and fixed through RED3 → GREEN3 plus full regression. Hash-bound
  new JSON files now preserve exact bytes in Git checkouts. No evidence hashes
  were weakened. The single fix pass is not a second independent review.
- Exact-head CI is reported in the Draft PR; neither review nor CI is a runtime/
  device qualification. Older PRs remain unchanged.

## Retained blockers and next single task

Actual device containment, complete closure, trusted kernel syscall/task/exec/FD
collector, watchdog timing and exact-R/native execution remain UNQUALIFIED.
Carrot source/runtime registration, friction empirical identification and missing
q, representation runtime qualification, frozen development/factor identification,
parameter identification, vehicle application bounds, runtime fingerprint,
watchdog model, external executor and application authority stay unresolved.
`NO_EMPIRICAL_ESTIMATOR_BRIDGE`; no Params, controller, writer, vehicle, model,
longitudinal, external AI, upstream PR or prior PR modification.

Recommended next single task: implement a **guest-only complete syscall/task/
exec/FD collector with request/result correlation** for the same harmless fixtures.
It addresses the present unknown trace and lineage rather than widening policy.
Actual hardware/native execution remains a separate decision. Do not auto-start.
