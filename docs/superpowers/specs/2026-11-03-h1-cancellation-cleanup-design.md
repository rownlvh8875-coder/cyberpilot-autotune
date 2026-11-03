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

## Post-assignment ownership repair (Task 2)

The fresh cumulative review of actualmain0dd/head701 reported C0/I1/M0:lines
559-562 had an assigned helper outside the try boundary. Task1's original and
nested interruption symptoms are addressed,not the entire ownership obligation.
After the user requested this next repair,the environment temporarily went offline;
resume at701 without recreating completed Task1 or changing environment settings.

Choose bookkeeping initialization before ownership acquisition and acquire the
helper inside the existing protected lifetime. A successfully assigned helper is
covered at its very first subsequent Python line. A factory/argument failure
before assignment owns no helper and must not close or signal an unrelated one.
Keep the existing public signature,normal results,secondary-failure handling,
no-pidfd EOF/bounded wait and all original bounds/permissions unchanged.

Reject merely relocating the outer try after Popen or adding a destructor:neither
proves an immediately assigned handle's explicit lifetime. Numeric PID fallback,
signal masking,new threads and native cancellation experiments remain out of scope.

Add real-function fake-edge line tracing that discovers every executed line after
helper assignment and before the first pidfd operation,not hardcoded line numbers.
Inject the same primary exception independently at each boundary;assert EOF,one
bounded wait,all stream closes,no request/signal/fd release,and fixed uncertainty.
Include incomplete acquisition and secondary-cleanup controls. Trace selection
locates the boundary;literal observable cleanup requirements determine expectations.
Restore any prior tracer. These tests prove Python control flow,not uninstrumented
SIGINT timing,CPython bytecode atomicity or native process-tree cleanup efficacy.

The live-line regression also exposes the nested try header's traceable NOP
outside Python3.12's exception table. Keep the owner body flat:private
_helper_pidfd(helper)->int|None catches the same OSError in its own call frame;
its call site is protected by the owner. None retains the existing unavailable
branch;zero remains an actual returned descriptor. No new fallback or API.

Only four already-registered paths change in Task2:supervision.py,the cancellation
test,this spec and its plan. Current4A5M scope,old freezes/manifests/workflow remain
unchanged. Local append-only commit,full regression/static/source/replay/build/
freshwheel verification and a fresh independent repair review;no push/Ready/merge.
