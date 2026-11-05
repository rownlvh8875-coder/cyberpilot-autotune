# Domain cohort independent review

Fresh reviewer: /root/domain_cohort_review. Source-only, no tests/experiments/writes.
Base:d70b425bb061c710fd0aabe2fdd396c765d16770.
Initial hashes: private logs/review-source-hashes.json.
Initial verdict: REQUEST_CHANGES, Important P2 two; Critical0/Minor0.
Final report/evidence were not yet written and were outside this source review.

## P2: unchecked W generation clock
peer.c initial line39 encoded now_ms directly as uint64_t.
The native fixture arms at original-worker-alive check, fails exactly the following clock query.
RED: full protocol/D removal succeeded with invalid generation.
Fix: one checked int64_t generation, encode only nonnegative value.
GREEN: no successful protocol/reclaim/kill write after the injected failure.

## P2: partial-parent same-inode foreign OFD close
policy.c initial87–90 closed unanchored parent by dev/ino only.
The fixture replaces that FD number with a separately opened same-inode P and fails the fs gate.
RED: foreign_close_attempts=1 despite final UNKNOWN.
Fix: without established OFD anchor do not close/recover numeric FD; retain process-bound UNKNOWN.
GREEN: foreign_close_attempts=0, D/worker birth requests0.

Both issues were reproduced before changes and fixed by the author in one pass.
Targeted normal + two corrected failure cases3PASS.
Final whole-suite/UBSan/GCOV results are in the report.
No post-fix independent rereview; no final-tree independent C0/I0 certification.

## Confirmed boundaries / rulings
Original F→M→E→W wait ownership, monotonic birth, one-shot stop/write/wait,
name/OFD rejection, exact SIGKILL vs normal exit137, library-close UNAVAILABLE,
D-removal fact vs late unknown result, simulated vs actual cgroup scope were reviewed.
Private hidden live-P interface is fixed E internal wiring, not a public adoption API.
No actual containment/F1/admin factory/crossUID qualification was inferred.
Ruling: retain unanchored FD until process exit rather than risk a foreign close; full cleanup remains unproved.
No unrelated feature/minor cleanup or original evidence rewrite.
