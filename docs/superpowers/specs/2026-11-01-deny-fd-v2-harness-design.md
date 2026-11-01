# DENY-FD v2 isolated collection harness — proposed design

Status: user-approved local implementation scope; no guest run or publication.
Date: 2026-11-01 (Asia/Seoul). Base: a97321f6bbf5c3e5d6e3205615e0a600b059b89a.
The user approved continuing the recommended harness task and delegated design
choices. The exact22-path history-policy delta was approved by the user on 2026-11-01.

## Intent and boundary

Implement a separate, test-only harness for preparing the six fixed DFD01–DFD06
guest diagnostics. Default operation must never launch anything. Implement and
test the future explicit opt-in capture path without invoking QEMU, the guest,
or the generated probe during this work. No actual-v2 acquisition is claimed.
The next guest execution remains a separate, explicitly approved task.

All nine permissions remain false: build_execution_allowed,
promotion_authorized, runtime_qualified, device_class_qualified, policy_adopted,
candidate_generation_allowed, application_authorized, runtime_accepted,
owner_proposal_allowed. A local diagnostic opt-in flag is not an authority grant.
Keep APPLICATION_NOT_AUTHORIZED and every inherited blocker. No vehicle, Params,
controller/cereal schema changes, estimator/application/owner bridge, network,
v1 promotion, previous-PR/main modification, publication, or merge.

## Grounding and alternatives

The current decoder accepts only one bounded, physically framed DFD2 window;
the producer source is M2=2481b84405beda95a394d1ca0248d7c9d632d28b. Existing v1
runners are coupled to old payloads and receipts and must not be repurposed.

1. Reuse/extend the v1 runner: rejected; changes historical evidence coupling.
2. General-purpose VM/payload runner: rejected; exceeds six fixed diagnostics.
3. New test-only fixed v2 harness: recommended engineering choice. It costs a
   separate image/launch boundary but preserves old bytes and default closure.

Use Python standard-library code in tests/deny_fd_v2_harness/. Reuse the existing
v2 decoder and pure inventory check read-only, never a v1 parser or old runtime
runner. Reuse bounded filesystem/archive/ELF readers where their exact semantics
fit; new image composition must not import or execute an old runner.

## Exact proposed repository scope: 2 modified + 20 new = 22 paths

Only these existing paths may change on a NEW descendant branch:

- tests/history_transition/deny_fd_v2_successor.py
- tests/architecture/test_deny_fd_v2_boundary.py

New paths:

1. docs/deny_fd_v2_harness_contract.md
2. docs/deny_fd_v2_harness_result.md
3. docs/evidence/deny_fd_v2_harness_history_v1.json
4. docs/evidence/deny_fd_v2_harness_assets_v1.json
5. docs/superpowers/specs/2026-11-01-deny-fd-v2-harness-design.md
6. docs/superpowers/plans/2026-11-01-deny-fd-v2-harness.md
7. tests/history_transition/deny_fd_v2_harness_successor.py
8. tests/deny_fd_v2_harness/__init__.py
9. tests/deny_fd_v2_harness/contracts.py
10. tests/deny_fd_v2_harness/assets.py
11. tests/deny_fd_v2_harness/image.py
12. tests/deny_fd_v2_harness/capture.py
13. tests/deny_fd_v2_harness/runner.py
14. tests/deny_fd_v2_harness/host_main.py
15. tests/test_deny_fd_v2_harness_assets.py
16. tests/test_deny_fd_v2_harness_image.py
17. tests/test_deny_fd_v2_harness_capture.py
18. tests/test_deny_fd_v2_harness_runner.py
19. tests/test_deny_fd_v2_harness_history.py
20. tests/architecture/test_deny_fd_v2_harness_boundary.py

No directory exceptions. Proposed cumulative scope is 78 literal paths, not a
new permission to modify all 78. The previous 58 paths are preserved except the
two explicit routing changes. The six M2 source files, v2 wire/source manifest,
all legacy sources/captures, P/P2/P3 records, original22 and original18 guards
remain byte-identical. PR55's branch itself must not move.

## History routing, not relaxed acceptance

Create P4 with sole parent equal to the base above. Its closed manifest records
56 preserved images and the exact pre/postimages of the two routing files,
20 new literal paths, content-identity-only meaning and nine false permissions.
Pin P4 from the subsequently added helper; do not put P4's own hash inside its
manifest. Require real Git objects/lineage, no replace objects/lazy fetch, raw
blobs/modes, and agreement across HEAD/index/worktree. Missing Git objects,
transport failures and unknown branches never grant a new scope.

The v2 successor retains all existing old-image checks and unions only a
successfully verified P4 scope. Historical cohorts receive no added paths.
The old architecture node's 19-path assertion is impossible on a legitimate
22-path successor. Route that ONE node on the new cohort to an isolated checkout
of the exact original base and run its ORIGINAL source/node/assertions, with an
owned basetemp and unchanged 60-second bound; no skip, xfail, altered expectation
or fabricated result. A new architecture guard checks the actual current 22-path
delta, P4 images and all prior protections. All other old tests stay unchanged.
This explicit test routing is why a fresh scope approval is necessary.

## Fixed assets and preparation

preflight() returns an immutable AssetBundle containing verified source/build/
VM identities and retained probe/busybox bytes. Select only the fixed cached
assets; missing/mismatched content is unavailable, not a download or fallback.
Verify the complete VM tree and cohort metadata, including libraries, loader,
BIOS, modules, package/archive metadata and kernel, not only qemu's executable.
Keep toolchain/header/library build-closure qualification false.

- VM cohort: d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c
- VM root: /workspace/scratch/qemu-vm.Hkx9tc/sysroot
- Kernel: 6.12.113+deb13-cloud-amd64; QEMU cohort: 10.0.13/pc-q35-10.0, TCG only.
- Probe: 915376 bytes, SHA256 0eb1891fe5c25a04e5447c637f81fb86a80404efbf8602b1ea31bf4d6a342f41
- Source manifest: 1255f050f56240afe14d4fa7479692ed07b00bf59a6396fa6919354d07ace166
- Current retained probe/record directory:
  /workspace/verification-archive/deny-fd-v2-source.LbkXkT/compile-M2481b84

Retain the original compile command and record as historical provenance even
though its old scratch path moved. Relocation is not recompilation, build-input
closure, reproducibility, authentication, or a new source revision.

build_image(assets, case) creates deterministic gzip/newc bytes in memory. Its
closed minimal contents are the pinned static busybox, unchanged static probe,
required directories/console/null nodes, and new v2-only init/scope bytes. No old
fixture/BPF/collector binaries, host extraction, disk/share/network or arbitrary
payload. Scope bytes: deny-fd-v2: fixed pre-exec inventory probe only followed
by LF. Init emits exactly DFD2_EXEC, calls /deny-fd-v2-probe --probe <fixed case>,
then emits the actual DFD2_PROBE_EXIT=<status> and DFD2_DONE. Setup failures must
not manufacture a complete success window. Guest boot claims remain untrusted.

## Future runner and evidence

capture_cases(cases, destination, *, run_prepared_guest=False) rejects by
default before filesystem setup or process creation. A true flag expresses
diagnostic intent, not application/runtime authority. Linux-only future launch
uses fixed argv, a newly owned destination outside checkout, explicit minimal
environment, -no-user-config/-nodefaults, TCG single thread, qemu64, 1 CPU,
768M, no NIC/disk/share/KVM/passthrough/monitor. Caller cannot provide commands,
payloads, QEMU flags, kernel, binary or alternate versions.

Use Popen without shell, a new process session/group, bounded nonblocking pipe
collection and a monotonic 180-second deadline. At deadline/output error/limit,
terminate the owned group, wait a 2-second grace, escalate to kill and reap.
These are resource controls, NOT a qualified watchdog or scientific thresholds.
Bound serial collection to the existing 1MiB profile; over-limit evidence is an
explicit retained prefix, never a complete capture. Preserve completed previous
cases and the failed attempt's raw bytes/exit/error/cleanup outcome. On persistence
failure, propagate the available bytes and a failed record; never claim success.

Use a separate immutable AcquisitionRecord: fixed case, host attempt identity,
source revision/manifest, build/probe identity, VM/kernel identity, init/image
digests, exact argv, raw-byte digest/size/completeness, process exit/termination
reason, explicit clock domains, and fixed false permissions. Content identity
does not authenticate collection. The normal future path decodes the retained
bytes, cross-checks BEGIN source/manifest/case, and calls check_inventory; any
consistent diagnostic remains BLOCKED. No receipt/application adapter.
Also bind POLICY/EXPECT to the requested fixed source profile. Never derive
the observed FD set, CAUSE rows or denial outcome from the case label.

host_main defaults to BLOCKED/NOT_STARTED and exit2. It exposes only the fixed
case selection plus explicit guest opt-in and new output destination. Import,
default CLI, pytest, CI and wheel installation must not start QEMU or a probe.

## Verification and completion

RED/GREEN tests cover raw asset drift, unsafe links/extra VM entries, retained
bytes vs rereads, deterministic minimal images, wrong source/case/ELF/window,
duplicate cases, default-denied launch, stdout flood/partial timeout/nonzero
exit/cleanup or write failure, and preservation of earlier successful cases.
Use subprocess test doubles for QEMU; harmless Python worker tests may verify
the Linux host process-group lifecycle, never guest or target-ELF execution.
Platform-specific new host tests must be explicitly distinguished from existing
skips; no old skip/gate/assertion/deadline may be loosened.

Run the complete existing suite, all unchanged coverage/audit/history/build/
wheel/replay gates and new-package coverage (target100/100; floor98% statements,
95% branches). Keep installed product bytes base-identical and the harness out
of wheels. Use private temp roots; no cleanup of archived/rejected old sessions.
Perform a fresh final whole-branch independent source review. Do not infer guest
correctness from mocks, host-worker tests, coverage or source review.

Completion may say HARNESS_IMPLEMENTED_NOT_EXECUTED, never observed-v2 available.
Retain DENY_FD_V2_RUNTIME_PRODUCER_UNEXECUTED, OBSERVED_V2_CAPTURE_UNAVAILABLE,
LEGACY_PR34_M1_OPEN, FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED, EXTERNAL_EXECUTOR_UNQUALIFIED and all other
runtime/vehicle/empirical/application blockers. No automatic execution/publication.
