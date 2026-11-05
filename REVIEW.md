# Independent review
Reviewed SHA: 200b4f900a5512de9ff6d30fbd9704fe551955c1, all tracked code/tests/docs.
One fresh read-only independent reviewer, pure control reproductions only.
No child/unit/network or project qualification executed by reviewer.
Three P2 findings:
1. lab.py pipe close masked primary cancellation and skipped later pipes.
2. handles.py BaseException close left finalizer able to retry uncertain numeric FD.
3. gate.py reported worker execution when clone3 had not created a worker.
Parent reproduced all three as RED in logs/red-independent-review.txt, then repaired.
Repairs are author/parent verified, NOT another independent review or C0/I0.
The reviewer correctly found metadata-only directory OFD identity insufficient.
Parent additionally reproduced same-directory independent reopen closing a replacement,
then added retained creation-time OFD anchors and Linux x86_64 same-process kcmp.
No permission/availability fallback to fstat equality. Distinct OFD reuse now rejects,
but this extra repair is parent-only verified. In-process hostile FD-table races/aliases,
atomic directory custody and general security isolation remain unproven.
Missing internal D/containment/read-only mount/drain are disclosed, not qualified.
