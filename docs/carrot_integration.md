# Future read-only Carrot integration

## Phase 8A.2 exact observability-head re-audit

The [independent re-audit](carrot_observability_reaudit.md) pins fork observability
head 4d89f044fc74138b0938f309ff8ea88d90faddcd. Historical activity/saturation software
evidence gaps are resolved, but the overall result remains
**CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**: actual VM measurement provenance
is absent, and MEB final corrected request cannot replace the desired target.
No production contract module, actual adapter or Phase 8B implementation exists.
The earlier upstream-base findings below remain historical, not a new precheck
of the unchanged upstream source.

## Phase 8A contract resolution

The owner-selected audit target is carrot-wip at exact commit
604bc0a22733e648ec05b268da1ffaae7db52a69. Phase 8A status is
**CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**: published activity is a request,
not proof of final actuator authority, and saturation alerts are not a universal
instantaneous limiting signal. No mapper or actual adapter has been implemented.

The current normative evidence is [the signal contract](carrot_signal_contract.md),
[source provenance](carrot_provenance.md), [raw-blob manifest](carrot_source_manifest.json)
and [synthetic evidence specification](carrot_signal_evidence.md). Unknown mandatory
signals remain None and prevent Snapshot construction. Caller-supplied clock/health
limits and an immutable baseline are proposed policies, not approved vehicle defaults.
Phase 8B is NOT_STARTED; persistence, actual integration and Apply remain unauthorized.

## Historical Phase 0 reconnaissance

The observations below are preserved as historical context. Where they differ,
the exact-SHA Phase 8A contract above supersedes the provisional mapping and target
selection language. No historical row approves a runnable mapping.

Inspected on 2026-10-28 using actual git ls-remote --heads, fetch, ls-tree and show.
No upstream writes, PRs, branches or installation were performed.

| Remote branch | Exact observed SHA | Recent commit |
|---|---|---|
| carrot-wip | 604bc0a22733e648ec05b268da1ffaae7db52a69 | 2026-10-27: Isolate-forked-radar-replay-from-threaded-model-checks |
| carrot | 62d004320d5a8683b919379f16811a832a894cf5 | 2026-09-19: Keep source diffs readable in the prebuilt distribution |

Other actual refs included apilot-c2, c3-wip, hoya/c3-atune and developer forks
under happymaj11r, janpoo6427, jominki354, joongyu01 and thftgr namespaces.
There was no carrot-nav ref in the returned list. Branch names were not assumed.
carrot-wip is the provisional source candidate because it has newer source and
active checks; owner selection for integration is still unresolved.

Both inspected branches declare Python >=3.12.3,<3.13 in pyproject.toml.
carrot-wip .github/workflows/tests.yaml uses setup-python 3.12.

The table refers only to carrot-wip at the SHA above. Schema paths:
`openpilot/cereal/log.capnp` (ControlsState, Event),
`opendbc_repo/opendbc/car/car.capnp` (CarState).
Consumer/publisher: `openpilot/selfdrive/controls/controlsd.py`.

| Snapshot field | Actual source and type | Unit evidence | Freshness / uncertainty |
|---|---|---|---|
| control_active | No actual mapping implemented | Explicit Bool/None for actual evaluated-controller activity | Unknown must veto; cruise/UI enabled is not an acceptable substitute; mapping requires a separate reviewed change |
| speed_mps | CarState.vEgo Float32 | controlsd converts vEgo with MS_TO_KPH for display; canonical m/s | Require carState valid, alive and timestamp checks; speed magnitude/sign policy must be confirmed |
| desired_curvature_inv_m | ControlsState.desiredCurvature Float32, assigned from self.desired_curvature in publish | latcontrol_torque multiplies desired_curvature by vEgo squared for lateral acceleration; geometric inverse meters | Model/plan lag and actual sign convention need adapter-specific tests |
| measured_curvature_inv_m | ControlsState.curvature Float32; self.curvature = -VM.calc_curvature(...) | Vehicle-model path curvature; inverse meters from consumer equations | This is an estimate, not direct physical measurement; calibration validity needed |
| lateral_acceleration_mps2 | ControlsState lateralControlState torqueState.actualLateralAccel Float32 | latcontrol_torque computes actual_curvature * vEgo**2 | Available only in compatible torque-state branch; otherwise None |
| driver_override | CarState.steeringPressed Bool | Schema: user using steering wheel | Longitudinal overrides and full driver-priority contract unresolved; unavailable must veto |
| controller_saturated | ControlsState lateralControlState.*.saturated Bool | Unitless branch-specific controller state | Not universally meaningful: controlsd notes MEB angleState is dummy; unknown must veto |
| source_valid | Event.valid Bool, CarState.canValid Bool; SubMaster all_checks | Unitless; code notes circular dependency limits of controlsState.valid | Do not equate canValid alone with complete signal health |
| timestamp_s / source_age_s | Event.logMonoTime UInt64 nanoseconds; SubMaster.logMonoTime | Schema explicitly says nanoseconds, divide by 1e9 | Must prove same monotonic domain, arrival age and multi-topic alignment; no wall clock |
| sequence | Adapter-owned counter for admitted input events | Integer, no unit | SubMaster frame is not assumed to be a cross-process sequence |
| context_key | Adapter-produced, explicitly versioned context | Opaque text | No VIN, GPS, driver ID or guessed vehicle identity |
| baseline_parameters | Future owner-approved read-only extraction | Registry-specific | No approved registry or source mapping exists yet |

Candidate hook for a later RFC: consume copies of published carState and
controlsState outside the active controller path. Do not hook controller update
or Params writes. No hook or actual adapter has been implemented. Unit conversion,
clock-domain alignment, missing signals, saturation semantics, baseline extraction,
latency budget and selected target branch need mock/golden tests before Phase 8.
