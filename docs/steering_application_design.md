# Shared bounded parameter application design

Status: Accepted for steering-only development on 2026-10-29; real activation policy remains unresolved.
Date: 2026-10-29.

## Authorized goal and preserved work

The owner approved the single-core design and explicitly restricted this increment to steering. Longitudinal behavior must remain unchanged. The owner wants development through real parameter application, rather than
stopping at SHADOW. They also require incorporating existing CyberPilot work
instead of building the same feature twice. This authorizes developing the shared steering application core; it does not supply vehicle-specific limits, a qualified
parameter-identification result or permission to install/run on a vehicle.

PR #8 remains immutable and Draft at e4361678ed176cbd7c0bb6f838d3daa7174caf22.
Its receive-only sidecar must not acquire engine, learner or write capabilities.
Current main is b24ef18e4270af5ab4f731aca31cf95f4f4b0cce. No changes to either
CyberPilot's active work or its historical audit baseline are made here.

## Source facts, not assumed integration readiness

- CyberPilot's original audit pin remains 588d6b21c21089065a7d9165d6e7a438e8aa6297.
- Observed feature/cyber-autotune still points to that commit remotely.
- Separately inspected public source: feature/f70ubm-source-boundary-metadata,
  02652a441c1c39b4a9c3bfaf1132217f0e57b384.
- The other active task's latest completed report concerns static technical
  evidence, with unresolved context fields; it is not a runtime application
  implementation or a qualified owner parameter registry. Its private inputs,
  fitting environment and in-progress artifacts must not be read or changed.
- CyberPilot contracts.py represents lat_accel_factor and friction only, and
  explicitly does not enable either. policy.py is an offline classification,
  not a permission registry. profiles.py fixes runtime_accepted=False.
- torque_identification.py fixes parameter_identification_qualified=False,
  candidate_generation_allowed=False and runtime_accepted=False. Its numerical
  diagnostic and heuristic residual spread must not become an authorized
  controller parameter merely because their names resemble one.
- Pinned Carrot source c2130730239bcdb4cbde9361ab90c8d99aa4ff55 already owns a
  liveTorqueParameters -> LatControlTorque.update_live_torque_params path in
  controlsd. Custom torque settings can suppress that update. A second writer
  would race the existing owner unless explicit single-owner arbitration exists.

## Approaches considered

1. One shared application core plus narrow owner adapters (recommended).
   CyberPilot retains identification/evidence production. cyberpilot-autotune
   owns one reviewed proposal admission and bounded application transaction.
   Consumers use the same versioned contract. This avoids duplicate algorithms,
   validators and independently evolving rollback rules.
2. Separate application implementations in both repositories (rejected).
   This duplicates safety logic and contradicts the owner's stated objective.
3. Copy the current research learner or offline policies directly into Carrot
   (rejected). Those are not qualified real-parameter conversions or authority.

## Recommended ownership

| Responsibility | Single owner / reuse decision |
|---|---|
| Empirical identification and scientific evidence | Existing CyberPilot work; do not refit/reimplement here |
| Canonical observation and baseline contracts | Existing cyberpilot-autotune contracts |
| OFF/SHADOW admission and residual research | Existing engine/gate/learner, unchanged |
| Versioned proposal/evidence compatibility | Explicit neutral bridge, retaining source/units/qualification blockers |
| Bounded application transaction and rollback state | New shared application core, implemented once |
| Runtime parameter ownership and actual update | Narrow, independently reviewed Carrot owner adapter |
| Source/fingerprint/parked qualification | Existing separate runtime evidence gate |

## New application boundary

Do not add a writer to integrations.carrot.sidecar. Add a separate application
package with immutable owner policy, proposal envelope, target snapshot,
transaction receipt and explicit fault state. Existing RuntimeMode OFF/SHADOW
and EngineResult baseline invariants remain intact. A separate application mode
may permit bounded application only when its complete policy and ownership gate
passes; it is not inferred from an eligible SHADOW decision.

Mandatory admission binds an exact policy revision, parameter family/units,
vehicle/context/software/source revision, baseline epoch, target revision,
evidence identity and one-time proposal identity. Require independently qualified
parameter evidence. A hash or asserted confidence is not review authority.

The target must provide a coherent snapshot, expected-revision update and
readback semantics in the controller owner's synchronous execution domain.
All coupled values must be committed coherently. Preserve unrelated parameters.
Reject stale baseline/revision, duplicates, context changes, nonfinite values,
expired evidence, driver override, saturation, unhealthy source and incomplete
policy. Bounds, delta/rate limits and deadlines are explicit caller-approved
policy, with no vehicle defaults and no automatic clipping.

An application receipt distinguishes proposed, host-committed, readback-verified,
rejected and rollback-failed states. None proves physical actuation. A failed or
uncertain write latches the application domain. Rollback failure must be reported
as failure, never described as a successful return to baseline. No automatic
rearming or persistence is introduced.

## Real Carrot owner integration

The first candidate family is the existing CyberPilot torque parameter family,
subject to approval; PID/gain/steering-ratio/longitudinal expansion is excluded
from this first change. Unit and signal-equivalence mappings remain unresolved
until traced, including friction's diagnostic coefficient versus live controller
semantics. No default conversion coefficient is invented.

Before activating a real owner adapter, resolve single ownership versus torqued,
custom-torque/NN branches, baseline freshness, coupled latAccelOffset preservation,
readback support, rollback timing and the exact source/context. A callable setter
alone is insufficient. Controller safety limits, engagement, override and panda
safety are not tuning parameters and must never be widened.

The current residual-statistics learner remains synthetic research. It must not
be treated as an identified torque/friction estimator. Existing CyberPilot
diagnostic output remains rejected while its qualification blockers remain.

## Proposed implementation sequence after design approval

1. Pin and hash the selected public source interfaces; freeze a compatibility
   matrix with explicit unresolved unit/qualification/ownership entries.
2. Implement neutral evidence/proposal bridging and test that unqualified
   CyberPilot diagnostics cannot create an application authorization.
3. TDD the shared bounded transaction/state machine against an in-memory target:
   valid commit, exact readback, baseline mismatch, coupled values, stale/duplicate
   proposal, rate/step/bounds, override/saturation, timer and target faults,
   uncertain commit, rollback success/failure, sticky fault and explicit reset.
4. Add an optional Carrot owner adapter only after exact owner/units/policy gates
   are resolved; verify native owner calls using synthetic/offline fixtures,
   unchanged unrelated controller outputs and failure readback. No vehicle run.
5. Full regression, architecture/property tests, wheel/build, exact-head CI and
   fresh independent review. Publish a separate Draft PR; keep PR #8 unchanged.

## Owner decisions required for real activation

- Ownership split and steering-only first family confirmed by the owner on 2026-10-29.
- Supply or approve the real parameter registry, units, hard/step/rate bounds,
  admission/evidence thresholds and rollback/watchdog acceptance criteria.
- Resolve the real runtime source/fingerprint and trusted context/baseline.
- Separately authorize installation, parked execution and any later closed-course
  test. None is included by inference in this development request.

No numeric vehicle policy is proposed in this document. Development of a
policy-driven transaction core can be tested with synthetic policies; real
activation remains fail-closed while the above evidence is absent.

No source code is copied. License/provenance decisions remain necessary before
distributing copied CyberPilot implementation; interface comparison alone does
not resolve ownership of its additions. No private dataset/model is accessed,
no message is sent to the other active task, and the reference source tree is not edited. Target implementation is recorded separately in steering_application_progress.md.
