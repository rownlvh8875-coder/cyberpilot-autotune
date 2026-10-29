# Offline custom selector / frame10 cohort parity

Approved single task: close PR18-M1, the untested positive custom-selector and
tenth-frame parameter-latching/reset branches. Base PR19 exact head
f0fc6cdcab10447c2b855c9c65e7acafe7e3c2a9. Native R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55;
C/carrot-wip re-read remains f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.

## Selected approach and boundary

Use existing source-backed AST loading plus actual pinned LINEAR callback and
legacy friction helper, rather than a duplicate controller model or full native
process. Only settings/vehicle/model/IO are explicit offline doubles. Run actual
baseline and unchanged PR18 patched controller/PID bodies over continuous frames.
This choice extends existing tests without starting Params, SubMaster or services.
No production source, native asset/schema, old evidence/CI/test or prior PR edit.
NR-M1 (non-ASCII registration reference path) remains deferred, outside this task.

## Required observations

Run31 consecutive cycles. Request selector1/2/3 at frame9; latch at10. Change
custom F/C/gains after10; refresh at20. Request0 at29; exit at30; allow new live
F/C/offset at31. Observe frames9/10/11/19/20/21/29/30/31, all settings read
names/order/count, live-update bypass, callback invocations, raw return, PID
components/state and installed/gain generation snapshots. Compare baseline with
patched observer absent/disabled/enabled/failing. Include LINEAR and NN_LITE
executed branches, inactive latch cycles and original settings failure propagation.

Pin actual source, not misleading comment: selector1->0 retains custom F/C/offset
until a subsequent live update; selector>=2->0 restores default F/C/offset. Neither
exit resets custom PID gains. Do not fix or reinterpret these native semantics.
Inactive control still latches settings before the active branch; no callback
receipt is invented for that cycle. q remains absent, not reconstructed or term/C.

Use hand-derived expected settings/context tables as an oracle separate from
baseline/patched parity. Demonstrate that in-memory mutations of latch cadence,
reset condition, live bypass and capture cohort are detected; never write mutants
into the native bundle. Float64 bit parity is a finite synthetic check, not a
vehicle-safe tolerance or universal proof. No actual NN weights/full NN coverage.

## Delivery and qualification

Add repository-only test harness, source-backed tests, evidence/result documents;
existing mandatory native runner discovers them without CI changes. Evidence
binds exact source/blob/ranges and unchanged patch/applied-tree registration.
Independent review at final exact head, full regression/source/schema/build/wheel
gates and push/PR CI. Stacked Draft PR against PR19; preserve all prior heads.
No merge/native fork/device publication. Only claim the PR18-M1 offline branch
test gap closed if actual tests and mutation sensitivity pass. All runtime,
empirical, q/cohort, fingerprint and application blockers/false permissions remain.
