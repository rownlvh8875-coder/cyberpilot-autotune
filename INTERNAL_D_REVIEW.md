# Independent review
Reviewed9545d54..3f72de3, complete change and shared C/Python helpers.
One read-only independent review, no actual unit/native execution.
P2: identity/membership unknown could be rechecked and upgraded to confirmed D removal.
P2: readdir NULL/EIO could be accepted as complete worker FD enumeration.
P3: integer137 conflated normal exit137 with CLD_KILLED/SIGKILL.
Parent reproduced all3 with native test fixtures (3RED, SIGKILL positive controlPASS).
Repairs: terminal uncertain binding/membership; clean readdir EOF; exact siginfo kind.
Post-review source/test additions are author-self-verified, not independent C0/I0.
Atomic mkdir/open and hostile same-UID admission/name/FD races remain unqualified.
