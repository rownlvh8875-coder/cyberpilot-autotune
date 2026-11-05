# Cohort integration independent review

Reviewer: fresh /root/cohort_integration_review, source-only, no tests/OS experiments or writes.
Base:4643a9e7be574c6d3f9db114ebff7ce518777b5d.
Initial source hashes are included in the private review-source-hashes.json delivery log.
Files: new coordinator, fixed peer, synthetic manager, failure driver and Python tests; included old helpers.
Initial verdict: REQUEST_CHANGES — Important P2 one, Minor one; no Critical reported.

## Important P2: unavailable clock encoded as successful context generation
cohort.c initial lines31–32 called now_ms once to encode and separately again to check.
A one-shot failure in the first call encoded UINT64_MAX, while the next valid read allowed success.
The test-only mkdirat/clock boundary arms after new P creation and fails exactly that first read.
RED: test_single_unavailable_context_clock_rejects_before_worker failed:
PRIVATE_COHORT_PROTOCOL_COMPLETE, actual synthetic W birth/exec1.
Fix: read one int64_t generation, reject negative before encoding, never substitute false/zero.
GREEN: targeted failure + normal positive2PASS. Final whole suite/instrumented results in final report.
This is the only new production-code change after the source review.

## Minor: preliminary plan's P creation order
The initial Task1 said P before M creation; actual source creates P after job acceptance.
The later appended ruling is authoritative: M/E must not inherit F's P.
The design/report describes actual order. Historical plan text/evidence was not rewritten.

## Explicit limits / rulings
- Original M/E/W wait hierarchy and P removal checks reviewed.
- Forced M/E termination at upper bound does not certify descendant drain.
  UNKNOWN is preserved, so no additional finding was assigned.
- SDK internal close remains UNAVAILABLE; full cleanup is never claimed.
- No actual manager/unit/cgroup/crossUID/protected-origin/F1 qualification claimed.
- Existing92 files remain unchanged. No user manager/global permissions changed.
- No post-fix independent rereview was performed; final-tree independent C0/I0 is not claimed.
- Author performed RED→GREEN correction and final full verification.
