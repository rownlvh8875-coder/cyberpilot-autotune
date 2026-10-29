# H6 preregistered estimands

Frozen before comparisons at the first H6 commit (history audit must prove this).
Base: `43ca6761749e71ec575906f099b02386bc76d994`. H5 PR14 head
`d705622e256b47506752e3e2beb131765c8a0136` merged 2026-10-29T08:01:48Z;
parents are `3ded3dec7011f24b7f1195f0c73bbed290891ff3` and that H5 head.
Merge/head trees equal. PR8 and PR9 remain untouched.

The estimand is the coefficient C in a **conditional controller-domain**
response `u_cb=a_cb/F+C*q+b0`, where a_cb is the actual callback input,
not achieved physical acceleration. F has acceleration/normalized-torque
units; C and b0 have normalized-torque units; q is dimensionless.
Installed C is context, never independent ground truth. Reconstructing
`h=C_installed*q` establishes implementation consistency, not optimal
physical steering friction. No empirical qualification is possible with
the missing frozen development artifact.

H5 K=1.5 std(perpendicular residual) remains a diagnostic statistic.
It is not C, will not be rescaled to C, and is not a calibration target.
Known-F tests use synthetic truth only. Unknown F requires joint rank;
uncertain F requires a declared external interval with sensitivity propagation.

## Frozen decision rule

The JSON policy is authoritative and immutable after this commit. First
check current signal stage, independent response/state, mode and complete
applied geometry/delay/cohort binding. If any mandatory item is missing,
select exactly `NO_IDENTIFIABLE_MODEL_WITH_CURRENT_SIGNALS` regardless of
synthetic accuracy. Otherwise compare structural recovery, noise behavior,
factor dependence, complexity and source feasibility in the recorded order.
A synthetic recovery is conditional, never empirical or application permission.

Do not invent real-vehicle low-error, low-jerk or condition-number cutoffs:
`SELECTION_THRESHOLD_UNJUSTIFIED`. Numerical rank uses SVD tolerance only.
Single-sign and all-deadzone state windows must fail closed.

## Execution plan and durable ledger

1. Freeze this policy, all four candidate families, selection rules, all
   synthetic scenarios, observation requirements and geometry policy.
2. Tests first: independent generator, four candidates, rank/excitation,
   factor interval, PID stages and immutable context/epoch boundaries.
3. Implement pure offline prototypes; compare preregistered synthetic cases.
4. Publish exact-source/range/hash evidence, gap matrix and all seven documents.
5. Run existing H2/H3/H4/H5 audits, full suite/coverage, build and fresh wheel.
6. Fresh independent final-head review, fix C/I via RED→GREEN and full rerun
   plus a new review, append-only push and Draft PR, exact-head CI.

Pre-flight interfaces: generator -> scalar observations -> candidate fit;
geometry context -> admission/epoch gate -> every fit. No shared regression
or q-generation helper. Existing H5 package/tests/evidence are read-only.

Ruling: use this already dedicated cloud checkout and requested research
branch, not an extra worktree — no user authorization for extra worktrees.
Remote skill scripts are not executable paths here; this tracked plan is
the durable execution ledger. User's explicit H6 requirements govern merge,
Draft PR publication and fresh re-review after fixes.

Task 1: preregistration complete when this document and policy are committed;
no H6 candidate code or comparison results exist at that point.
