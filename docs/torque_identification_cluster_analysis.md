# H5 frozen development and route-cluster analysis

Policy was committed before development evidence inspection:
da2f9a082018285dd706e49aad61d3783233a29d. Its canonical SHA256 is
5ee040a5ad7af8bcf8c56422da3ae8ed7794c5b77f52ddd380e5aa24df95b94b.
The first commit contains only policy and estimands. No threshold was fitted to
real outcomes. There were no actual development outcomes to inspect or compute.

## Evidence inventory: reported is not recomputed

The exact CyberPilot pin's aggregation document reports the following. The
underlying point/epoch/route/selection artifacts were not supplied or located.

| Quantity | Historical document reports | Independently recomputed in H5 |
|---|---:|---|
|route clusters|not specified|UNAVAILABLE|
|epochs|19|UNAVAILABLE|
|nonempty epochs|15|UNAVAILABLE|
|points|31,595|UNAVAILABLE|
|valid full-rate native epochs|not established|UNAVAILABLE|
|bucket counts|104,608,2709,11591,10588,4443,1194,358|UNAVAILABLE|
|duplicates / timestamp ordering|reported0 errors|UNAVAILABLE|
|source revisions / boundary reasons / delay provenance|artifact bindings not present|UNAVAILABLE|

The published point-manifest SHA256 is
27ed097453beeb075b133cc492b8462d5b5c2de7bf36e2f1d94e145f95b846d8.
A hash and an aggregate summary cannot reconstruct the missing observations or
authenticate their scientific selection. Do not turn the reported counts into
newly verified dataset counts. Canonical report counts are null, not0 or31,595.

## Authorized retrieval attempts

[Search evidence](evidence/torque_identification_artifact_search.json) records the
local filename inventory, exact and relevant current Git trees (untruncated),
GitHub releases,90 Actions artifact names, exact-hash indexed search including
forks, HF project/author searches and273 configured LFS tree entries. No matching
frozen artifact was located. This does not prove private/global nonexistence.

HF commaai/commaSteeringControl exists, but its metadata does not bind it to this
frozen selection/role/provenance. No zip was downloaded, no new raw extraction was
performed, and no holdout/evaluation payload was opened. Substitution would need
separate authorization and a new pre-analysis data contract; it cannot silently
change this preregistration's development corpus.

## Implemented admission and epoch validity

Only development_fit, exact signal/source/mode/unit declarations and one delay
application are admitted. All route/epoch/sample identities are hashes. Duplicate
route records, globally duplicate sample IDs, duplicate epochs, overlapping
segments and incompatible boundary reasons reject. Within-epoch times must
already be strictly increasing; permutation is rejected rather than guessed.
Epoch/route ordering is canonicalized. Different epochs can restart their clocks.

Each supplied epoch is separately classified VALID, INSUFFICIENT_COVERAGE or
INVALID_SOURCE_CONTRACT. Missing epoch payloads are UNAVAILABLE at the inventory
boundary, not fabricated empty epochs. Full-rate native validity requires all
eight minima100,300,500,500,500,500,300,100, total>=4000, per-bucket cap1500,
x in[-.5,.5),|x|>.02,|y|<=1. Qlog/pooled thresholds never substitute for per-epoch
validity. Empty supplied epochs are insufficient coverage, not independent samples.

## Chosen uncertainty method

Use exhaustive leave-one-route-out (LOO) and delete-one-route jackknife descriptive
standard error, not a point bootstrap. For G nonempty routes and omission
estimates theta_(-r),

    mean_LOO = sum(theta_(-r))/G
    SE_jack = sqrt((G-1)/G * sum((theta_(-r)-mean_LOO)^2)).

At least3 nonempty routes are required operationally, so each omission retains
at least2 routes. This is not a scientifically calibrated minimum N. Every
omission must have a numerical fit; a failed omission makes SE unavailable rather
than removing an unfavorable route. Empty route omissions are still listed but
do not inflate G. Same-route epochs never count as independent route samples.

The method assumes meaningful independent route clusters and a smooth common
estimand. Convenience sampling, shared source/model errors, heterogeneous modes,
small G, correlated routes or unstable fits can invalidate inferential use.
No95% interval is issued: independent sampling/calibration is unproved. A
descriptive scientific SE would not be an application bound even if available.

## Influence, secondary diagnostics and current outcome

The implementation reports every route and epoch fit, all-route/all-epoch LOO,
factor absolute/relative deltas, offset/native-spread deltas and maximum route
influence. Epoch omissions diagnose reset/segment/boundary sensitivity only.
Side fits, residual-command covariance, variance, skew, left/right residual means
and OLS comparison are secondary diagnostics, never alternative physical targets.

Without the actual artifact, all real full/route/epoch/side/residual fits, LOO,
influential-cluster identities and jackknife SE are UNAVAILABLE. The tested
synthetic fixtures exercise the code but are not substitutes for development data.
THRESHOLD_NOT_JUSTIFIED and SCIENTIFIC_CLUSTER_STRUCTURE_UNAVAILABLE remain.
