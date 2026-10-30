# Kernel lifetime source feasibility — result

Base PR35 `a982d1bec759916013981f9cbc76ced6679c71ea`.
Branch `feat/kernel-lifetime-feasibility`; own stacked Draft, append-only commits.

## Delivered

[Source feasibility review](kernel_lifetime_feasibility.md),
[implementation gates](kernel_lifetime_implementation_gates.md), exact source and
9-obligation decision manifests, pure test-only copy/loss counterexamples and an
offline source auditor. No source producer, hook attachment, kernel patch/build,
guest/probe run or real compiler workload. Building the unchanged Python package
and running passive compatibility unit tests are not kernel instrumentation.

## Decisions and limits

- **NO_GO_CURRENT_PROFILE**: present source/diagnostic evidence cannot qualify
  PR35's serialized source-complete profile. Not a universal impossibility result.
- **CONDITIONAL_DESIGN_ONLY**: explicit instrumentation in a source-pinned disposable
  guest is the selected future architecture; actual sites, safety, closure, cuts,
  accounting, exact binary identity and perturbation remain unqualified.
- Two pre-reserved slots and lockless fd_install can produce a copy with no single
  source-state cut. A file_lock, event number or successful fork event does not fix
  this. PR35's no-inflight-reservations premise must be proven, not assumed.
- BPF ring reservation may fail including an NMI try-lock failure with free space.
  Discard/busy records and reservation order do not establish effect completeness
  or order. Proposed count equations are not built-in ring byte counters.
- Source unregister synchronization, source arm, target quiescence, transport drain
  and CPU/hotplug cohort closure are different evidence obligations.
- Identity references/stopping/instrumentation can change copies, final release
  and scheduling. No transparent/unperturbed observation claim.
- Whole-source omissions/coherent fabrication remain invisible to synthetic count
  agreement. Actual loss/global prohibited-operation counts remainNone, not0.

## Verification checkpoint

- Baseline2886 passed36.32s. New64 focused tests, full2950 passed35.37s.
- Task1 missing-module RED→39 GREEN; Task2 missing-audit RED→22 GREEN;
  wrong existing source-claim substitution separately RED→GREEN. The final23 audit
  tests prevent source drift, false qualification and irrelevant claim substitution.
- All6 reader/writer order merges evaluated;1 lacks a matching source presence
  state. Synthetic schedules only, not actual captures or probabilities.
- Pure witness67/67 statements,32/32 branches,100/100%, no exclusions.
-10 fresh Linux source files/26 ranges verified against whole-file/range/blob
  hashes; preserved package and inner archive rehashed. No running-kernel match or
  fresh distribution-signature verification claimed.
- Ruff/check/format, mypy71 installed modules and2 new audit modules pass.
- Existing H2..H7/history/observation-v2/guest/PR35 evidence audits pass; old kernel
  manifests without their optional source root report kernel verificationfalse.
- Passive native compatibility192 passed3.94s, no service/target execution.
- Python sdist/wheel build passes. Fresh wheel, final independent exact-head review,
  CRLF and remote push/PR CI outcomes are recorded in the PR handoff after execution.

No changes to src, compatibility, CI, old audits/evidence/fixtures/experiments or
earlier PRs. Only the new evidence JSON receives a new -text attributes rule.
Prior PR34M1 and PR33M1/M2/M3 remain deferred; no silent fixes to prior evidence.

## Status

KERNEL_LIFETIME_SOURCE_FEASIBILITY_REVIEW_COMPLETE.
KERNEL_LIFETIME_CURRENT_SERIALIZED_PROFILE_NO_GO.
KERNEL_LIFETIME_INSTRUMENTED_DESIGN_CONDITIONAL.

Retain LIFETIME_RUNTIME_PRODUCER_NOT_IMPLEMENTED;
LIFETIME_SOURCE_HOOK_COVERAGE_UNPROVEN; COPY_CUT_PROOF_UNAVAILABLE;
LIFETIME_LOSS_ACCOUNTING_UNQUALIFIED; OBSERVER_PERTURBATION_UNQUANTIFIED;
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED; CONSUMER_FD_INVENTORY_BACKEND_UNQUALIFIED;
NO_PR30_QUALIFIED_BRIDGE. All frozen-development/factor/vehicle-bounds/runtime-
fingerprint/watchdog/external-executor/application blockers remain.

All9 operational permissions false; no estimator qualification, candidate generation,
owner proposal, trusted baseline, application bridge or vehicle-readiness claim.
No Params/controller/cereal/longitudinal/external AI/upstream PR changes.

## Next single task

**Disposable-guest raw FD lifecycle source prototype**: instrument a deliberately
small fixed harmless operation set in the exact source cohort; retain raw effects,
actual failure counters and interventions, without PR35/PR30 qualification bridge.
It must follow G1..G9's evidence boundaries and stop on unavailable prerequisites.
This result does not automatically start it or authorize broader runtime work.
