# Independent design review and author fix boundary

Exact base3a831fdd423aa98638082eba126519db19f432d6 →
head64a5c8cbd051cc6bd1c2b171c8a760b727a90005. One fresh read-only
gpt-6-astra/high reviewer, no checkout/index/branch/policy/remote changes or
host/guest/native target/tracer/probe execution.

## Findings: C0 / I1 / M0 at reviewed head

Strengths: separates files_struct/storage/slot/OFD/task-exec/pin lifetimes;
shared/copy semantics, explicit terminal witnesses, barriers/context/loss are
coherent; future runtime/source-cut/perturbation qualification remains blocked.

I1 — model.py296..303 permits allocating duplication methods to replace an
occupied FD. Changing the second DUP in additional('dup_replace') to DUP/F_DUPFD
still returns consistent; a complete F_DUPFD_CLOEXEC graph does likewise.
Linux dup/f_dupfd allocate unused slots; only dup2/dup3 replace occupied ones.
This admits an impossible binding/incarnation transition independently of false
operational permissions. Require an unused destination for allocating methods,
retain replacement for dup2/3, add all three negatives and positive controls,
and pin fs/file.c1389..1417 operation evidence.

Author regrading agrees: Important, not waived by SYNTHETIC/BLOCKED status.
One author RED→GREEN fix pass/full rerun follows; no second review or independent
clean fix-head C0/I0 claim. No new Minor finding; old PR34 M1/PR33 M1/M2/M3 unchanged.

## Independent verification

Full offline2870 passed35.67s; focused113 passed0.48s. Published43 graphs all match
their builder/expected verdicts:12 consistent/31 rejected.4 base Git+9 fresh Linux
files/26 ranges and authenticated archive/package hashes verified. git diff--check
green. Final HEAD64a5c8c, branch/index/worktree unchanged and clean.

## Declined to judge (exhaustive)

1. Actual observer/hook coverage/source-runtime equivalence/lossless delivery/
   perturbation bounds: explicitly future qualification work.
2. General concurrent copy/exec/teardown and raw terminal interleavings: outside
   admitted serialized semantic profile.
3. Mutually consistent fabricated or wholly omitted observations: consistency
   oracle explicitly provides no authenticity.
4. Runtime transport/duplicate-key handling: no runtime decoder delivered.
5. Cross-event timestamp monotonicity: source ordinals authoritative, no timestamp
   monotonicity validation rule in this profile.
6. Whether zero-allocation closed windows must reject: no explicit nonzero workload
   requirement in the contract.
7. Existing PR34 M1 and PR33 M1/M2/M3: protected, explicitly deferred prior work.

Verdict: with fixes; resolve I1 before considering the design oracle complete.

## Author verification (not a second independent review)

Four RED complete graphs: occupied destination for each allocating DUP/F_DUPFD/
F_DUPFD_CLOEXEC, and nonlowest unused destination for DUP. All GREEN after source-
backed guards; dup2/dup3 replacement retained. Three positive controls check actual
unused-allocation effects, and the empty closed-window policy is characterized.
The catalog now51 graphs/16 consistent/35 rejected;4 Git+9 Linux files/28 ranges.
Full2886 passed35.36s; pure266stmt/72branches100%, no exclusions. Final exact-head
wheel/source/CRLF/CI rerun checkpoints recorded in the PR handoff. Old minors
unchanged. No independent fix-head C0/I0 claim.
