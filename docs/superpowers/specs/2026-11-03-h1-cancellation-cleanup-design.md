# H1 owned-helper cancellation cleanup — narrow repair design

## Intent and basis

Repair the whole-branch review's Important cancellation finding at source head
`209edaa83b398e6204af1097fda4b651807cc815`. This is development-only tooling,
not actual H, executor qualification, ENTRY/STACK admission or application authority.
Executor design section 6 and EP-020 already require bounded controller-exception
cleanup. The helper can await EOF before any payload deadline starts.

The user delegated routine engineering choices and requested this repair.
Implementation details below are the author's choices, not individually approved
policy or execution grants. Prior operational I1/original-host equality remains
UNCONFIRMED and is not inspected or repaired by this work.

## Approaches

- Merely broaden one exception tuple: rejected; it misses pidfd acquisition and
  can replace cancellation with a result or mask it with a cleanup exception.
- One explicit post-Popen ownership boundary: selected; keep protocol/result
  evaluation separate from resource ownership, stop through a retained pidfd only,
  attempt bounded reap and preserve the primary exception.
- Numeric PID fallback or a new execution profile: prohibited and unnecessary.

Keep Python >=3.12.3,<3.13 and stdlib only. No new runtime/public API, dependencies,
worker signal policy, workload, environment authority or timing threshold.

## Required behavior

1. Once Popen returns, cancellation at pidfd acquisition, request write/close,
   collection, wait, or subsequent controller I/O must attempt cleanup and re-raise
   the same primary BaseException. Do not return success or swallow cancellation.
2. Close protocol input so a short request can reach EOF. When a retained pidfd
   exists, use only pidfd_send_signal(SIGKILL), never numeric PID/group fallback.
   Without a pidfd, send no request after failed acquisition: EOF plus the existing
   bounded wait is the available safe cleanup. Do not invent stronger authority.
3. Attempt helper.wait with the existing 2-second cleanup bound independently of
   close/signal failures. Attempt every owned stream close and final pidfd close.
   Keep pidfd ownership through reap; do not retry a released/uncertain descriptor.
4. Secondary cleanup exceptions cannot replace the primary exception. Attach only
   a fixed CLEANUP_UNCONFIRMED note; never arbitrary exception text or host data.
   Cancelling does not prove descendant cleanup or native effectiveness.
5. Preserve existing protocol validation, first known command errors, output,
   unavailable values and nine false permissions. A normal result whose controller
   handle cleanup fails must remain/revert UNCONFIRMED, not claim a clean result.
6. Original normal/timeout/output-limit/supervisor-failure behavior and all existing
   test cases remain. No budget changes: normal wall5s,timeout0.4s,cleanup2s and
   existing stream/resource bounds remain unchanged.

## Verification and exact scope

Use real controller code with fake process/stream/pidfd operations for interruption
tests; no real helper is needed to reproduce the finding. Pin interruption at
acquisition, write, close, collection and wait; include cleanup faults, original
exception identity, no numeric fallback, EOF-before-reap and normal regressions.
These tests establish control flow, not a kernel/process-tree qualification.

Freeze the old outcome repair at literal209. Add a separate current successor
consumer with exactly four additions and five modifications, enumerated in the
descriptive registration and literal code/test inventories. Old history-helper
bodies,pins,ranges,thresholds and manifests remain unchanged. A current manifest cannot
grant another path. Reject unknown/status/alias/duplicate/untracked/frozen changes.

No src/, application, controller, Params, schema, workflow, collector, historical
executor, vehicle or HF changes. D01-D04 and every inherited blocker/permission
remain. Verify full software regressions, source/history validators, lint/format,
type checks, package/wheel/replay smoke and a fresh independent repair review.
New-head hosted CI remains a separate publication prerequisite; no Ready/merge here.

## Independent-review fix-pass adjustment

Review of exact98626b9 found that inner collector/selector/artifact cleanup could
mask primary cancellation before the new outer boundary received it. Extend only
this current successor by runner.py (one exact path,no directory grant),for a
private primary-preserving cleanup context and the two existing directory/write
helpers. Update _collect,_read_owned and controller artifact cleanup to use it.
Do not widen any historical ceiling or change workloads,bounds or permissions.
Directory traversal transfers ownership to the newly opened handle before closing
the previous one;never retry an uncertain close. Add real imported helper/collector
fake-edge regressions,not only mocks at their entry points. This is the one planned
review-fix pass;final repaired head will be parent-verified,not independently
re-reviewed. The original C0/I1/M0 review stays bound to98626b9 without relabeling.
