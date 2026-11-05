# Real cgroup adapter independent source review

Reviewer:/root/real_cgroup_review; source-only, no test/experiment/write actions.
Initial verdict REQUEST_CHANGES: Important3, Minor1.
Initial source hashes are in private logs/review-source-hashes.json.
Final docs/evidence are author-verified; no post-fix independent C0/I0 assertion.

## Important1 — compile/source pin generation mismatch
The manifest first hashed source after compilation.
RED: last real compiler return then mutate factory.c in a NEW source-copy fixture; stale ELF was accepted.
Fix: capture source bytes, compile actual private snapshot, compare original/snapshot bytes before attesting.
The old launcher remains uncalled and old source unchanged.

## Important2 — unknown communicate-close retry
RED: fake communicate invoked stdout.close(), its first close raised OSError,
then finally invoked the same close again (count2).
Fix: communicate exclusively owns closure after entry; retain original job/unknown streams.
Before communicate, explicit close ownership is consumed before one attempt.
No receipt/numeric handle recovery.

## Important3 — GO had no EOF/additional-message guard
RED: valid first36bytes plus trailing byte/duplicate GO reached asset opening.
Fix: single absolute8s deadline, bounded read1, require exact token and clean EOF.
Empty/partial/additional/live-timeout/unsupported-reader cases reject before exec.

## Minor — FIFO type can delay gate
RED: newly created manifest/worker FIFO blocked on open until test-only1s alarm.
Routine authorized follow-through fixed it with O_NONBLOCK plus regular-file metadata before reads.
No actual unit was created during these tests.

All reported findings reproduced before their code changes. Fixes were authored in one review pass.
Additional positive/negative tests covered loaded identity, reordered frames, duplicate JSON keys,
initial lookup race, manager/root controller gates, source/type/mode/compile failures and cancellation.
New package typechecking uses proper module search roots, no missing-import or type-error ignores.
Fresh full/focused results recorded separately; repeated tests are not added to unique PASS count.

Reviewed distinctions retained:
manager-created P vs E-created D; synthetic M/credential boundary vs real kernel cgroup;
actual kernel lab vs protected origin/F1/crossUID/readonly/namespace/16 qualification evidence.
