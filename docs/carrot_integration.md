# Future read-only Carrot integration

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
