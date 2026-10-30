# FD-table/OFD lifetime observer qualification contract — design result

Base PR34 `3a831fdd423aa98638082eba126519db19f432d6`.
Branch `feat/fd-ofd-lifetime-observer-design`; own stacked Draft, append-only.

## Delivered, without a runtime observer

[Normative contract](fd_ofd_lifetime_observer_contract.md),
[backend alternatives/source constraints](fd_ofd_lifetime_backend_design.md),
[future qualification gates](fd_ofd_lifetime_qualification_plan.md), semantic
schema/source/counterexample manifests and a pure test-only SYNTHETIC oracle.
No src/compatibility/old evidence/fixture/CI changes; no actual VM/kernel/host
tracer/probe or observer executed/implemented. Existing passive compatibility
unit regressions are not a new producer or real source-build workload.

The contract distinguishes files_struct namespace lifetime, replaceable fdtable
storage, observer transaction epoch, FD binding incarnation, OFD lifetime,
task-local exec and reference pin lifetime. Same inode/hash/offset/FD/PID/current
kcmp relation does not establish persistent identity or allocation generation.
Actual backing-storage generation remains unavailable, not modeled as table key.

Shared tables, exact fork copies, conditional same/new unshare/exec, per-descriptor
CLOEXEC, precise close deltas, pin/terminal ordering, slot/table/task/OFD reuse,
context binding and per-CPU source/fence/loss claims are reasoned separately.
Snapshots/caller booleans/counter agreement do not prove continuous coverage.

## Main source findings / preferred future architecture

Source-pinned kernel-assisted lifecycle emission **with verified quiescence/cuts**
is preferred over snapshot-only reconstruction or a generic syscall stream.
This is a proposal, not an implemented/qualified kernel/eBPF observer.

Critical remaining evidence gaps:

- dup_fd can race with lockless fd_install even with file_lock held. A whole-copy
  cut cannot be assumed atomic; overlapping/unrepresentable cuts block.
- unshare/exec allocation depends on actual kernel references; current tracked
  task count or every exec call cannot assign a new table generation.
- task detach/reap, namespace terminal, delayed final fput and actual OFD free
  are different facts. Known reference count0 does not establish actual destruction.
- observer-held OFD/table references and ptrace/quiescence can change lifetime,
  copy behavior and scheduling. Read-only does not imply unperturbed execution.
- source-wide lossless delivery, scope closure, CPU/hotplug/fences and complete
  effect-class coverage/exclusion remain unqualified.

## Synthetic evidence and verification checkpoint

- Baseline2757 passed35.44s; pre-hardening full2866 passed34.59s.
- Pre-review full2868 passed34.97s before the two additional UInt32 CPU-ID
  regressions; final-head full-suite checkpoints follow in the PR handoff.
- Full2870 passed35.09s with those CPU-ID regressions; focused113 including
  architecture. Installed-source coverage checkpoint2868 passed100.43s, with
  no src changes; exact final-head CI/source coverage is recorded separately.
- Post-review author fix full2886 passed35.36s, focused129 including architecture.
- Pure oracle266/266 statements100%,72/72 branches100%, no exclusions.
  This is Python consistency coverage, not OS/C/kernel/VM coverage or correctness proof.
- Published51 **SYNTHETIC_ONLY** graphs:16 internally consistent,35 rejected.
  No new actual observations; PR34's actual9 captures are unchanged/replayed only.
- Four exact base Git blobs plus9 fresh authenticated Debian files,28 semantic
  ranges: complete size/SHA256/Git-blob/rangeSHA256 checked. Source archive/deb
  hashes match the preserved source cohort. Runtime source/BTF equivalence unqualified.
- Ruff/format green and strict mypy71 installed+3 new audit/model/example modules.
- Fresh vanilla/research wheel import/replay/Carrot-contract, knowledge/owner,
  science/friction/receipt smokes pass outside checkout. Wheel excludes tests/
  compatibility and NumPy before research extras.
- Existing H2..H7/history/observation-v2 and old guest evidence audits pass;
  passive native compatibility192 passed4.17s, no openpilot service/device execution.
- Exact final-head source aggregate, CRLF, independent review and push/PR CI
  checkpoints are recorded separately in the own PR handoff after observation.

TDD checkpoints:38 initial missing-API RED→GREEN;14 schema/catalog/source-audit
RED→GREEN;3 malformed source/profile RED→GREEN. Shared-table test exposed a tasks/
tables terminal-count order defect, fixed explicitly. Two pre-review resource
tests RED→GREEN cover oversized keys and repeated-value aggregate expansion.
The copy budget is100000 visited nodes,4MiB aggregate string characters and4MiB
canonical bytes in addition to depth/field/vector bounds; no safety threshold.
Two CPU-ID RED→GREEN regressions correct an unintended8-bit ID restriction to the
declared UInt32 domain; the8-CPU cohort size bound is separate from logical ID values.

## Independent review / single author fix pass

Reviewed exact64a5c8cbd051cc6bd1c2b171c8a760b727a90005: **C0/I1/M0**.
[Full review](fd_ofd_lifetime_design_review.md): allocating duplication methods
could replace occupied FD destinations. Four complete-graph reproductions were
RED. The author fix requires absent destination for DUP/F_DUPFD/F_DUPFD_CLOEXEC,
and DUP's lowest unused FD in this no-reservation profile; dup2/dup3 replacement
remains supported. Three positive allocation controls plus an empty-window
characterization are published, with two more exact kernel source ranges.
One author RED→GREEN/full-rerun pass; no second independent review or clean
fix-head C0/I0 claim. No new Minor findings, prior deferred4 unchanged.

Source ordinals, not timestamp monotonicity, define the graph's causal order;
time annotations provide no latency/alignment guarantee. Empty closed models are
consistent no-activity models, not workload/observer/consumer evidence. Actual
source/runtime/transport/concurrency/authenticity qualification stays unavailable.

## Status / permissions

FD_OFD_LIFETIME_OBSERVER_CONTRACT_DESIGN_READY.
FD_OFD_LIFETIME_SEMANTIC_SCHEMA_DESIGN_READY.
FD_OFD_LIFETIME_BACKEND_ARCHITECTURE_CONDITIONAL.
LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED.
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN.
COPY_CUT_PROOF_UNAVAILABLE.
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED.
OBSERVER_PERTURBATION_UNQUANTIFIED.
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED.
NO_PR30_QUALIFIED_BRIDGE.

Overall **BLOCKED**, all9 operational permissions fixedfalse; actual drop/global
prohibited-operation countsNone. Synthetic success is not observation authenticity,
freshness, executor qualification, complete source-build/namespace/consumption,
watchdog/vehicle fingerprint/bounds, estimator or application authorization.
All prior frozen-development/factor/vehicle/watchdog/executor/application blockers
remain; PR34 M1 and PR33 M1/M2/M3 deferred and unchanged.

No vehicle, Params/write/controller/cereal changes, real compiler workload,
candidate generation, estimator qualification, application/owner bridge,
longitudinal, external AI, upstream PR or old PR8/9/31/32/33/34 modification.

## Next single task

Source-pinned read-only kernel-hook/copy-cut/loss-accounting **feasibility design
spike**. Resolve whether actual lifecycle source points and quiescence can satisfy
the proposed evidence gates without invisible target-semantic changes. Do not
automatically promote this design into a production observer or PR30 adapter.
