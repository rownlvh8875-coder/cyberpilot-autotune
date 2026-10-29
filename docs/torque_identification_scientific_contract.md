# H5 scientific contract and design

The user-supplied H5 specification fixes the workflow: source/model derivation
(A), independent known-truth synthetic experiments (B), statistical policy freeze
commit (C), existing frozen development evidence (D), separate verdicts (E).
The estimands document is written before running any fit, including synthetic.

## Approaches and decision

1. Import the complete native/research runtime: rejected because its dependencies
   and startup paths are unnecessary and can cross the no-runtime/no-data boundary.
2. Implement an isolated research-only package, with an independent source-equation
   generator and exact-source mathematical-function parity checks: selected here.
   This preserves the existing runtime and allows explicit data admission.
3. Treat frozen numerical parity as qualification: rejected by the specification;
   it cannot identify the physical estimand or justify point independence.

This is the implementer's choice within the prescribed pipeline, not a change to
its scope. No new interactive design decision is needed to execute the supplied
specification. Work proceeds inline; fresh independent review is required at the
final exact head, and again after every Critical/Important correction.

## Boundaries

New research/torque_identification modules depend on pure standard library plus
an optional NumPy analysis extra, imported only when fitting. Existing core,
runtime, application, owner, knowledge, replay, integration and sidecar source
bytes remain unchanged. No scientific report feeds an application/owner API.
Only audit/reproduction tooling performs explicit local file/Git reads.

Contracts bind exact source, source-native selection/alignment, development role,
hashed route/epoch/sample IDs, ordered sample times and provenance hashes. These
declarations/digests are bindings, not independent authentication. Missing point
artifacts or selection provenance are evidence gaps, never permission to extract
new raw logs, pool unknown sources or invent timestamps/clusters.

## Statistical design

Route is the minimum correlation cluster; epochs are nested diagnostics only.
Use exhaustive leave-one-route-out plus delete-one-route jackknife descriptive
standard error. No point bootstrap or confidence interval is inferred from small
convenience samples or unproved independent routes. No defensible real-data
stability acceptance threshold currently exists: freeze that gap explicitly
instead of selecting a favorable percentage after observing outcomes.

Native full-rate per-epoch coverage is evaluated independently; pooled coverage
never makes an epoch valid. Raw unfiltered, unclipped estimates are analyzed.
All prespecified sensitivities are reported, including adverse results. A
diagnostic estimate is not an approved parameter or safe application range.

## Determinism and failure

Canonical sorting fixes allowed point permutation and route/epoch ordering;
duplicate identities or within-epoch nonincreasing times reject. Results bind
input, policy, source and analysis implementation. Byte determinism applies to
the same numerical stack; floating-point cross-BLAS bit identity is not claimed.
The original sine-trajectory float64 inputs are stored exactly as hexadecimal
values so platform libm rounding does not silently redefine a frozen experiment.
The existing scenario digests and result artifact remain unchanged.
Unavailable evidence returns null metrics with exact blockers, not fake zeros.
Reports are frozen and cannot be dataclass-replaced into application authority.

## Merge basis

PR #13 merged at 2026-10-29T06:17:49Z with exact-head protection.
H5 base/main: 3ded3dec7011f24b7f1195f0c73bbed290891ff3.
Parents: b0de6b4032d587c818f3d47389ae1afc37f2009c and
a6a149305f2a5d831cd99e6e914aa4dcd8be2896. H4 ancestry and merge/head tree
equality verified. carrot-wip was re-read as f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
PR #8/#9 remain outside the mutation scope. The initial automatic merge rejection
was resolved by verifying the current uploaded request's explicit Section 2
authorization; no merge protection or network rule was bypassed.
