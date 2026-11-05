# ADMIN REVIEW BUNDLE — INDEPENDENT REVIEW

Base8c0058ee8b24e7acd1de8bec248563d623ff60e4.
One fresh independent reviewer: admin_bundle_review.
Result: REQUEST_CHANGES — Important1 / Minor1. No actual system bus/unit/credential/cgroup/native lab.

## Important: unsupported whitespace could hide a security directive

ConfigParser strips NBSP/Unicode and VT/FF whitespace differently from pinned systemd255.
NoNewPrivileges<NBSP>=yes, <VT> or <FF> produced _inspect==[] while systemd would ignore that key.
Account strip/splitlines had the same normalization issue.
Primary source: systemd v255 conf-parser.c + basic/string-util.h (ASCII WHITESPACE).

Author reproduced five syntax/account false PASS cases RED; a global-impact declaration test also RED.
Both proposed files now accept printable ASCII plus TAB/LF/CR only before normalization.
Focused73 and full402 tests pass after repair. This is content lint, not a host/parser security certificate.

## Minor: global sysusers backup/cache footprint omitted

Pinned v255 sysusers.c backs up/replaces /etc/{passwd,group,shadow,gshadow}- and can flush nscd caches.
The earlier transaction mentioned auth DB changes but did not enumerate these existing-backup effects.
Author verified source and added account_tool_effects to manifest/checker, future-impact/rollback paragraphs,
conditional cache scope, distribution-specific unknown effects and NOT_GRANTED authorization.
No local auth DB/backup contents were read. No account tool invoked.
A mandatory declaration and omission tests cover the review record; apply remains BLOCKED.

## Independent commands and limits

Reviewer command:
~~~text
.venv/bin/python -I -B -m pytest -q tests/test_admin_review.py -p no:cacheprovider --basetemp=/tmp/admin-source-review-o73bsnht
~~~
64PASS, exit0 on earlier snapshot; temporary review fixture was subsequently removed by reviewer.
Checker also exited0 with PASS/APPLY_BLOCKED. These earlier checks are NOT added to final PASS total.
No old source/evidence removed. Author final fixtures/logs are retained in a separate private diagnostics tree.

Reproduction snapshot hashes:
~~~text
e794ad691d2bb017ed1765515f6f7777d01387c539622df0c9dea0186f5ed5de  check_bundle.py
9a07f83e48aa2500cb1bb403216302984ba70120adc55227eaf00173b5faa34f  test_admin_review.py
f8ac2ed595ae5ba5db26788a99774dcc079abaa12bc22e70665ff77c46147f0d  ADMIN_CHANGE_TRANSACTION.md
~~~

The reviewer found FD typeh/duplication/AddRef, PID1→E vs E→W ownership, shutdown caveat and
remaining blockers coherent at source/design level. No other Important/Critical finding reported.
Final author repairs were not independently re-reviewed. No final-tree independent C0/I0 certification.

Rulings: user forbids actual privilege/config/host/vehicle work; preserve prior evidence and unknown state.
Root-owner metadata, source hashes, tests, checker PASS never become provider registration or live authority.
