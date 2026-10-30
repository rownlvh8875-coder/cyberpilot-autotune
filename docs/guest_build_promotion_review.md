# Guest build receipt independent review and author fix pass

Independent read-only review: **C0 / I1 / M0**, exact
`fe2cc6ea769d77f03e42ad1589b48dd4c3e9acf1` versus base
`bbec08f84d0d08b17075663643ddeba6db46d977`. Reviewer read complete spec/plan,
package/tests/docs/evidence, ran focused140 and reproduced I1; checkout remained
clean and HEAD unchanged. One reviewer, not a cascade of review seats.

I1 accepted as Important: repeated partial READ_BYTES claims for one immutable
material/generation/offset/length could disagree on hashes yet return consistent.
This is an internal contradiction, independent of real producer authenticity;
overall BLOCKED is not an excuse to ignore it. Two rejection regressions failed
RED (same and different task), then GREEN after a per-range hash consistency map.
Three positive regressions preserve agreeing repeated reads and independent
ranges. Test: `tests/unit/test_guest_build_review_fixes.py`. Hashes of overlapping
but nonidentical ranges cannot be compared without bytes; no false proof claimed.

One author fix pass, followed by full regression/static/source/build/wheel/CRLF
verification. **No independent re-review of the fix head and no independent
C0/I0 verdict claimed at that head.** Deferred minors: none.

## Exhaustive rulings, in order

1. Automatically continue design→validator→reference planner: user delegated
   ordinary same-repo continuation. Cost: author-selected boundary; real gates
   still stop execution and cannot be cleared by an approval string.
2. Reuse dedicated checkout/new branch: established workflow. Cost: less
   filesystem isolation than another worktree.
3. Manual external ledger: cloud workspace helper unavailable. Cost: manual
   bookkeeping risk.
4. Keep actual producer/executor/seal absent, implement pure consistency only:
   no qualified evidence exists. Cost: actual build/promotion remains BLOCKED.
5. GENERATED input DAG unsupported v1 rather than accept opaque origin hashes:
   causal proof absent. Cost: no full code-generating native build support.
6. Reviewer declined empirical producer authenticity: absent producer and
   untrusted receipts stay explicit. Cost: coherent forgery not excluded.
7. Reviewer declined executor containment: no executor/run implemented; original
   gates unchanged. Cost: no execution containment qualification.
8. Reviewer declined actual capture completeness: only supplied trace claims
   checked; actual observer absent. Cost: missing reads/descendants not ruled out.
9. Reviewer declined actual input/output sealing: no seal/promotion backend;
   digest references never authority. Cost: no real immutability/quiescence proof.

Items6–9 cover all declined behavior; nothing was silently counted as passing.
No finding waived and no deferred minors. Final exact-head CI/PR identities are
in the Draft handoff; docs-only handoff commits do not imply new source review.
