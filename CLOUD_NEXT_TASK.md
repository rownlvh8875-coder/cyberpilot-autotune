# Next Cloud task — native dynamic manager owner/job binding

Implement and verify this research component end-to-end without asking for routine design/step approval.
Read CLOUD_HANDOFF.md, AGENTS.md, the latest PLAN/PROGRESS completion and referenced designs first.
Do not repeat the completed local host survey or add only another boolean/evidence model.

## Concrete gap

research/factory_manager/factory.c currently hardcodes manager owner :1.0, job ID1 and job path /job/1.
It is a closed private synthetic manager fixture, not a real shared-system-bus backend.
The persistent factory intent and actual local D lab do not solve dynamic manager creation correlation.

## Deliverable

A new isolated native component and test-only private sd-bus fixture supporting dynamic owner and job identities.
Reuse existing framing/request/lifecycle helpers after auditing them. Preserve every original135 snapshot file.
Add new source/tests/design/report files; append PLAN/PROGRESS. No product integration or actual system bus connection.

Default constructor remains unavailable/ENOSYS. No caller command/path/PID/FD/unit/receipt execution/recovery API.
Only factory-created live connection/endpoint/context can participate. Keep one attempt per process and consume
the Start attempt before an ambiguous send/call; timeout/cancel/disconnect never causes retry or retarget.
Keep synthetic M as E's original parent, F without E pidfd adoption, and unchanged explicit E shutdown/EOF.

## Binding requirements

- Bind original live bus/anchors, bus ID/generation, freshly obtained unique manager owner and fresh nonce unit.
- Subscribe to owner changes before the owner snapshot so the lookup/subscription gap cannot authorize a new owner.
  Drain/validate queued owner events at execution gates. Owner/generation loss taints the attempt.
- Use the owner from this current creation attempt, not a hardcoded name, caller claim or serialized receipt.
- Correlate the typed Start reply's bounded job path with actual JobRemoved ID/path/unit/result.
  Support valid non1 IDs and distinct unique owner names. Signals may arrive before the method reply.
- Callbacks only observe/copy bounded data; execution phases decide grant/ref release/terminal behavior.
- Unrelated correctly formed job events on a shared-bus-shaped fixture must not be mistaken for this attempt.
  Wrong sender/context for this fresh unit, duplicate/late/replayed matching events, invalid signatures,
  inconsistent ID/path, failed jobs or ambiguous replies must fail closed.
- Reference release uses only the original live owner/connection and generated current unit context.
  No reconnect-by-name or receipt-based cleanup after loss; unknown close/wait/ref results stay unknown.
- Preserve FD negotiation and retained-manager-endpoint semantics: E close alone is not EOF.
- Do not generalize the old private peer's final EOF requirement into a real shared-bus requirement.
- No original P/F1 or protected cross-UID qualification is inferred from bus strings or passing fixtures.

## TDD / verification

Write the reproducing failures first, then minimum implementation and full relevant regressions.
Cover multiple dynamic owners/job IDs; early matching signal; unrelated traffic; spoofed sender;
owner change during lookup/before Start/after reply/at ref release; bus generation change/disconnect;
duplicate/stale/extra/malformed events; cancel before/after submission; uncertain ref/FD/wait;
second attempt and receipt replay; unexpected ancillary FD and no foreign FD close.
Retain equivalent negative coverage rather than deleting the old known-hardcoded cases.

Use pure in-process typed message/encoding tests and compilation when native fixture prerequisites are unavailable.
Only run fixed child/private IPC fixtures when current nonroot Linux/native gates actually pass.
Do not create user units/cgroups, change credentials/security configuration or connect to PID1/system manager.
If Cloud starts as root, never work around that with sudo/su/setuid/user creation. Classify the native class
BLOCKED/UNAVAILABLE, keep pure implementation/testing moving, and report which acceptance cases remain unexecuted.
Do not turn unsupported classes into PASS, mix mocks with real kernel evidence or relax original checks.

Run lint/type/compiler/sanitizer/coverage appropriate to the new code. Record command/exit code and exclusions.
If independent review tools are available, obtain one fresh read-only whole-change review.
Reproduce material findings RED→GREEN, repair, revalidate and disclose final unre-reviewed scope.
Do not change frozen sources/tests/flags to make collection or qualification pass.

## Completion

Write CLOUD_MANAGER_BINDING_REPORT.md and sanitized new evidence; append the single PLAN.md/PROGRESS.md.
Report implemented API, source revision, actual commands/results, mock/native/OS distinctions,
cleanup/residue uncertainty, supported vs blocked cases and exactly one next engineering action.
Commit append-only on a separate research work branch. No push/PR/merge/main changes for this new implementation
unless a later user instruction explicitly authorizes publishing it.
Keep UNBOUND,16UNAVAILABLE,14false. Actual protected factory/F1/cross-UID deployment is out of scope.
