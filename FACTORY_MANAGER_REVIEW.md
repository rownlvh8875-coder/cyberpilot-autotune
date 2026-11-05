# FACTORY / PRIVATE MANAGER INDEPENDENT REVIEW

Base4595279c63052c5d24a43916600fb423cdc1e674.
Fresh reviewer factory_manager_review: source/design only, no native tests or OS/manager operations.
Verdict REQUEST_CHANGES: Important1/P2 and Minor generation-test gap.

## Important/P2: constructor partial ownership

Original private constructor created F socket+anchor+M before sd_bus_new/set_fd.
If new failed, l.busNULL cleanup skipped fd/anchor.
If set_fd failed, nonnull empty bus was mistaken for owner and l.fd discarded without close.
Two own-/proc/self/fd-count regressions RED, then GREEN after explicit bus_owns_fd provenance.
Socket/anchor metadata is retained before library creation; ownership changes only on successful set_fd.
Native pre-transfer failures close original known refs, mapping uncertainty remains UNKNOWN.
Constructor helper also propagates local close uncertainty instead of continuing a successful link.

Minor: second sd_bus_get_bus_id comparison lacked direct changed-ID mutation.
Added generation_changed and event_wrong_sender fixtures. Final46PASS/448research/UBSan/GCOV.
Repairs/additions after original review are author-verified, not final-tree independent C0/I0 certification.

## Original reviewed hashes

~~~text
ad0af469dd1813cc803c4656b10c3170cfe8dbc72e1030d24632af12040b6a03  factory.c
e680838919a161f3b7badf01f4dbced2d387d410a701a73aa4d36d2e143c6cf4  request.c
e30ef0705acc772ed3a02a176acffc8d834bf8c904a1a2045de4d6ee609c9d2c  fake_manager.c
783d9f910d755e78b463e8ed0e660947efa2a8028d39dbad7ed3a128940df345  driver.c
fca54b29d7c3b0abede979ede9fc6a1be5ce5a3e04849bb74cf830b073e496fd  test_factory_manager.py
2988001e293e9094963cfdcf844d2d1959304ef7234729baba4b6d77f2e6894f  FACTORY_MANAGER_DESIGN.md
~~~

No other material source/design issue identified by reviewer.
Review confirmed defaultENOSYS/private-only topology, M ownership of E, consumed attempts,
late-event drain and explicit library-close UNAVAILABLE align with stated limits.
It did not certify actual PID1, system bus, protected origin, UID/fence/P/D/W or qualification.

Ruling: preserve old source/evidence/unknowns; no actual OS apply or remote publication.
All14false/UNBOUND/16UNAVAILABLE retained; protocol completion is separate from global cleanup proof.
