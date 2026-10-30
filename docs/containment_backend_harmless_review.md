# Guest harmless branch review and decision record

Independent reviewer: fresh-context `gpt-6-astra`, high reasoning, read-only.
Base `8ef42c443887bf8f8d072256ed8268a75cec696f`.
Reviewed head `a5b071558720924491a48e4dc6fce953d57a3bff`.
Verdict: **C0 / I1 / M0**, Draft publication with the Important fix; no merge or
expanded execution authority. Reviewer independently ran 134 focused tests and
verified 4,307 input hashes and the original VM cohort without launching a VM.

The Important finding was raw-byte JSON hash failure in ordinary autocrlf=true
checkouts. Both author and reviewer reproduced it. The append-only fix preserves
only the three new hash-bound JSON files using narrowly scoped Git attributes;
the original serial log already preserved exact bytes. Three regression tests
failed before the fix and pass after it. Full suite after fix: 1,855 passed.
Fresh autocrlf checkout publication tests are required before handoff. No C/BPF,
runner or receipt semantics changed after review. Under the inline execution
process this is one tested fix pass, **not** a fresh independent review of the
fix commit. Deferred minors: none in this review. Earlier PR25 minor is untouched.

## Execution rulings, in order

Each cost describes what is lost if the call is insufficient, not approval to
broaden the scope.

| # | Decision and reason | Cost / retained limitation |
|---|---|---|
| 1 | Reuse dedicated clean branch/checkout, matching existing preference | Less filesystem separation than a new worktree |
| 2 | Cloud skill helper unavailable: manual external ledger and test logs | Manual bookkeeping risk |
| 3 | Explicit latest approval selects software guest only; historical design snapshots unchanged | No physical/outer-host qualification |
| 4 | Static libelf link fails; explicitly hash and bundle dynamic guest loader/libs | Larger loader closure; full closure not qualified |
| 5 | File-open LSM audit is not complete syscall/FD evidence: keep unknowns | No full trace/lineage/global zero-count qualification |
| 6 | Publish all24 as narrower partial attempts, not complete HF protocol passes | EAGAIN/PIDreuse/FD/closure work still needed; zero qualified PASS |
| 7 | Fixed already-selected local VM/input paths, fail closed elsewhere | Explicit rebuild/rebinding required for another machine |
| 8 | Retain reusable signed inputs/build cache; remove only transient plan bookkeeping | Additional disk usage; no broad recursive cleanup |

## Rulings on all reviewer declined-to-judge items

Every item remains an explicit boundary, not a hidden positive finding. The
reviewer did not run these operations; the author does not convert source or
hash checks into their qualification.

| # | Behavior set aside / ruling | Cost / next proof needed |
|---|---|---|
| 1 | Fresh guest/kernel attachment review: keep committed author-run observations, no extra reviewer VM authority | Current attachment behavior not independently rerun |
| 2 | Physical devices/driver/ioctl/mmap/device-cgroup enforcement: excluded | No actual device-class qualification |
| 3 | Production containment/arbitrary adversarial payloads: fixed harmless scope only | No general hostile-payload guarantee |
| 4 | Hypervisor and hostile outer host: unqualified TCB/TOCTOU | No hypervisor/host-escape resistance claim |
| 5 | Compiler/loader/QEMU-module/transitive closure: hashes are not closure | Additional complete closure proof required |
| 6 | Upstream/package authenticity: signed acquisition author-recorded, not network-reverified by reviewer | No independent authenticity attestation |
| 7 | Complete syscall/task/exec/FD/collector/causal/global counts: unknown | Complete trusted collector still required |
| 8 | Real ring loss/unmatched capture/all observer channels: copied-event faults only | Actual loss/correlation experiments remain |
| 9 | Actual dirfd reuse/cwd generations: HF06 unbound numeric case only | Reuse/generation binding not qualified |
| 10 | Actual scoped EAGAIN: not produced | EAGAIN behavior remains unverified |
| 11 | Actual PID reuse/birth/exec generations: cancellation/stale-ID only | General task identity unqualified |
| 12 | Exhaustive argument/rename/hardlink/mount races: controlled cases only | No exhaustive race coverage |
| 13 | All invalid ABI/open_how/alternate acquisitions: tested subset only | Untested combinations remain unknown |
| 14 | Complete inherited/duplicate/passed/hardware FD inventory: HF18 narrow only | No exhaustive FD lineage |
| 15 | Actual Python pyc/preload/sys.path closure: regular stand-in only | No Python loader qualification |
| 16 | Generated native-loader/JIT/mmap/promotion: executable-open denial only | No generated-code immutable closure qualification |
| 17 | Privileged link detach/guard/supervisor death: denied payload BPF only | Failure-survival guarantees unqualified |
| 18 | General tree quiescence/watchdog timing: observed stop/reap only | No watchdog/timing qualification |
| 19 | Write/create/truncate/transactional cleanup: unsupported, refusal only | No write emulation/effect transaction guarantee |
| 20 | Carrot/model/controller/service/vehicle/science/application: excluded and blocked | No native/runtime/empirical/application readiness |
| 21 | Operational runner portability/provisioning: fixed paths only | Explicit new input/host binding needed elsewhere |
| 22 | Remote CI/wheel/history source reruns: author checks, not reviewer reruns | Independent review is not their attestation; report actual author/CI results separately |

No further task is authorized by this record. Gate A remains BLOCKED; B/C/D not
started. All permission fields false. Next single recommendation remains the
guest-only syscall/task/exec/FD collector, not hardware or Carrot execution.
