# Passive Carrot Friction Producer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans inline, TDD, one fresh whole-branch review. This implements the existing approved design, not a new controller model.

**Goal:** Build an exact-R native schema/producer patch bundle and offline native
synthetic harness in CyberPilot; do not publish/apply it to a fork or device.
**Architecture:** existing cycle-local passive capture, optional PID taps, final
immutable snapshot after original command send. q stays unavailable. Native files
are materialized into disposable test directories from pinned Git objects and
patched; CyberPilot production modules/H6/H7 and PR8/9/16/17 are unchanged.
**Tech Stack:** Python3.12, NumPy, pycapnp2.1.0, Cap'n Proto, exact Git objects.
**Spec:** docs/superpowers/specs/2026-10-29-carrot-friction-producer-design.md;
docs/carrot_friction_producer_implementation_plan.md. User's next-step request
approves executing that previously unexecuted plan; activation remains excluded.

## Global Constraints

- CyberPilot base cd02d81b745565aa8ae41d4799fd1b1687f2a07e; primary native R
  c2130730239bcdb4cbde9361ab90c8d99aa4ff55. C is comparative only, no C port.
- Native changes only custom/log/service, controlsd/LatControlTorque/optional PID
  and new observation helper. Helpers/interfaces/torqued/longitudinal untouched.
- No Params access by observation helper, extra Params reads, real SubMaster
  execution, socket use, vehicle, persistence, estimator/candidate/application.
- Default observer absent; source/schema/context registration required for explicit
  offline construction. No old R/C SHA reused as instrumented producer revision.
- q=None; full friction identification remains blocked. No native execution or
  transport/performance qualification inferred from synthetic bit parity.
- Append-only branch; stacked Draft PR on design branch; no automatic merge.

## Review Focus

1. Observer errors alter native callback/PID exceptions, return bits or gain reads.
2. Setpoint/measurement callback mistaken for actual feedforward invocation.
3. Consumed local CC/retained pose provenance backfilled from publish/latest reader.
4. Default wire fields, unknown mode or Float32 telemetry become exact observations.
5. Disabled producer opens transport, wrong source SHA gets registered or q is derived.

## Task1 — exact source fixture and schema (RED→GREEN)

Files: compatibility/friction_native/{__init__,bundle}.py,
native_patches/friction_observation/{receipt.capnp,instrumentation.patch},
tests/native_friction/test_bundle.py.
Interfaces: bundle.build(reference:Path,destination:Path)->dict of source bytes;
bundle.verify(reference)->None. Reject unknown pin/changed source bytes; never
modify the reference checkout. Build into a newly allocated empty test directory.
- [ ] Test absent bundle; exact slot110/typeID, required presence and 134 wire fields.
- [ ] Generate static schema from frozen map; reject authority/unavailable defaults.
- [ ] Preserve all old union/type IDs and validate old/new readers in separate
  schema parsers/processes (avoid duplicate global schema registration).
- [ ] Commit after focused tests pass.

## Task2 — bounded collector and actual PID tap (RED→GREEN)

Files: native_patches/friction_observation/friction_observation.py;
instrumentation.patch; tests/native_friction/test_capture.py and test_pid.py.
Interfaces: PassiveFrictionObserver(enabled=False, *, source_revision,
source_schema_digest,vehicle_context_digest,session_id); begin_cycle(cycle);
callback/pid/context/limits capture; seal(control_time,command_time)->immutable
native receipt mapping; encode(schema)->wire. Native module imports stdlib only.
- [ ] Write failing tests for disabled/invalid origin, immutable sealing, finite
  validation, duplicate/future/wrong-clock input, context generation and q absence.
- [ ] Test exact native PID base/patched parity: return/state bits and getter counts,
  normal/freeze/override/clip/reset/error cases; observer exceptions stay observer-only.
- [ ] Implement bounded per-cycle scalars; no IO, mutable external references or
  callback/gain re-evaluation; missing reads remain unavailable.
- [ ] Commit after targeted and whole suite pass.

## Task3 — native callback/caller wiring (RED→GREEN)

Files: instrumentation.patch; tests/native_friction/test_controller.py;
compatibility/friction_native/harness.py. Native helper supplies begin/context/
callback/PID/limit/finalization entry points consumed only by the optional taps.
- [ ] Write source-backed baseline/patched actual-method tests (not substitute
  controller equations), including LINEAR/NN_LITE/NN/custom/GM and inactive paths.
- [ ] Wire original FF invocation and raw ff/PID operands; preserve readback,
  sanitizer, callback invocation count and original command sends.
- [ ] Wire cycle start/local sources/installed/applied context and separate
  t_ctl/t_cmd/final completion; no post-publish CC mutation or latest-reader join.
- [ ] Test observer failures and controller exceptions independently; no timer or
  threshold invented, no unselected delay or skipped k_i filled with a default.
- [ ] Commit after parity and full tests pass.

## Task4 — schema round-trip / CI / review / publication

Files: compatibility/friction_native/run.py; tests for actual compiled schema;
docs/carrot_passive_friction_producer_result.md; source/payload evidence manifest.
CI adds pinned pycapnp install and isolated runner to existing source-audit job;
old design-history audit gets only exact recognition of these additive CI lines.
- [ ] Round-trip actual native wire; old empty payload/version/default/NaN/Inf/
  unknown enums/None vs0/False; callback raw cannot be applied or reconstructed q.
- [ ] Full CyberPilot regressions, source audits, coverage, lint/type/build/wheel;
  runnable native synthetic baseline and patched harness. Full hardware/native
  build/vehicle/transport tests are explicitly unrun, not skipped into a pass.
- [ ] Fresh final independent review; one C/I RED→GREEN fix pass, minors deferred.
- [ ] Publish stacked Draft PR, attach and verify exact-head CI; no fork PR/merge.

## Ledger

Pre-flight: Task1 schema/source fixture feeds Task2 encoder and Task3 native
method loading. Task2's optional sink is consumed by Task3 without changing the
default update calls. Task4 compiles exact schema and exercises all earlier work.
No producer-to-estimator/adapter interface is introduced.

Ruling: deliver native patch bundle in the requested CyberPilot repository, not
write another repository or device — previous scope excludes upstream/fork PR —
cost: deployment still needs a separate apply/review/qualification decision.
Ruling: use existing isolated checkout and tracked ledger, no extra Git worktree or
unavailable remote skill scripts — managed onboarding guidance — cost: manual ledger.
Ruling: execute the already approved passive plan inline — user asks next step,
not another design — cost: one final independent review rather than per-task agents.

Baseline:1435 tests pass, tree clean. pycapnp2.1.0 needed for real schema tests;
no controller runtime/services or hardware dependencies will be started.

Progress: schema/pin guards RED3→GREEN3; collector/codec/absence/immutability
RED→GREEN16. Native PID tap RED19 PID_TAP_MISSING→GREEN19; actual lateral update
FF-site RED5 capture missing→GREEN10 active/inactive mode cases. NN input preparation
and Float32 error logging use explicit offline dependency doubles; these do not
qualify actual NN models, transport or hardware. Full runnable native/hardware
baseline is not available; CyberPilot baseline and extracted pinned method
baselines are distinguished, never reported as a full openpilot native build.
