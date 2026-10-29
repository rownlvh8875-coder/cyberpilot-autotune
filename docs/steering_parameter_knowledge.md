# Steering parameter source semantics

This is a descriptive catalog, not an application registry. Nine logical IDs are
recorded separately at each of three exact revisions: 27 descriptors, 78 claims,
39 source files. Six descriptions per revision pass `get_proven`; factor,
friction and offset remain diagnostic. Thus `STEERING_DESCRIPTOR_CATALOG_PARTIAL`
and `APPLICATION_POLICY_UNRESOLVED` are explicit outcomes.

## Provenance and preserved work

- Historical Hoya: ajouatom/openpilot
  `0e9c589c1b83027146f909a9cdc306c2c665ceaf` (explanation reference).
- Runtime source: rownlvh8875-coder/openpilot
  `c2130730239bcdb4cbde9361ab90c8d99aa4ff55` (future compatibility reference).
- Integration: `7a2f051b1f3847786318900444c88c2ba7a74a67`, tree-equal to runtime source.
- Current carrot-wip: ajouatom/openpilot
  `f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3`, unchanged at H2 start.
- PR #10 guarded merge/base: `dd1d4232f3d151fe9bbf0808c1fbe5131618b09a`,
  merged 2026-10-29T01:11:52Z; parents
  `b24ef18e4270af5ab4f731aca31cf95f4f4b0cce` and
  `8a3f6f5bfb35021e20dc5730f6650f12d53d571d`. Audit head is an ancestor;
  merge tree equals audit head tree. PR #10's 10 checks passed before merge,
  with no unresolved review threads or Critical/Important review finding.
- PR #8 remains preserved at `e4361678ed176cbd7c0bb6f838d3daa7174caf22`;
  PR #9 at `6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5`. Neither is changed/merged.
- Runtime fingerprint remains UNCONFIRMED; parked runtime qualification pending.

Original file/range identities, symbols and interpretation conditions are in
[source evidence](evidence/steering_parameter_knowledge_sources.json).
Full canonical metadata/digests are in
[catalog evidence](evidence/steering_parameter_catalog.json).
Claim prefixes `hoya:`, `runtime:` and `upstream:` select the respective revision;
the following table uses suffixes shared across those namespaces.

## Stored representation and primary consumer

All eight UI keys are native PERSISTENT **INT** settings encoded as integer text.
The settings service uses the native type to perform a typed write. The reference
controller often reads them with get_float; that does not change their native
storage type. These are observations of reference code, never calls by this package.

| ID | Classification / evidence | UI min..max; UI default / native default | Consumer conversion and software unit | Source claims |
|---|---|---|---|---|
| LateralTorqueAccelFactor | TUNING_CANDIDATE / CONDITIONAL | 1000..6000; 2500 / 2500 | custom raw ×0.001 → torque_params.latAccelFactor; global canonical unit unavailable | custom, linear, friction, live-tuple, controlsd-live, nn |
| LateralTorqueFriction | TUNING_CANDIDATE / CONDITIONAL | 0..1000; 100 / 100 | custom raw ×0.001 → torque_params.friction; global canonical unit unavailable | custom, linear, friction, live-tuple, controlsd-live, nn |
| LateralTorqueKpV | SAFETY_SENSITIVE / PROVEN | 0..200; 100 / 100 | raw ×0.01 → PID proportional software coefficient | custom, pid, nn |
| LateralTorqueKiV | SAFETY_SENSITIVE / PROVEN | 0..200; 10 / 10 | raw ×0.01 → PID integral software coefficient | custom, pid, nn |
| LateralTorqueKf | SAFETY_SENSITIVE / PROVEN | 0..200; 100 / 100 | raw ×0.01 → PID feedforward software coefficient | custom, pid, nn |
| LateralTorqueCustom | MODE_SELECTOR / PROVEN | 0..1; **1 / 0** | integer selector, no numerical tuning target | custom, live-tuple, nn |
| SteerRatioRate | DESCRIPTIVE_ONLY / PROVEN | 30..200; 100 / 100 | raw ×0.01 → dimensionless multiplier in source-specific resolver | ratio, vm |
| SteerActuatorDelay | DESCRIPTIVE_ONLY / PROVEN | 0..300; **30 / 0** | raw ×0.01 seconds; consumer-dependent selection/timing | delay, delay-model, delay-nn |
| liveTorqueParameters.latAccelOffset | COUPLED_PRESERVED_STATE / UNRESOLVED | none / none | Float32 latAccelOffsetFiltered copied unchanged (scale 1); canonical unit unavailable | offset-fit, offset-publish, wire, controlsd-live, live-tuple, linear |

Every UI descriptor additionally references ui-ID, key-defaults, settings-type and
settings-write claims. Exact formulas/ranges are evidence, not vehicle bounds.
The UI's `unit`/increment metadata is not a canonical physical unit. Kf's English
and Chinese titles advertise ×0.001; the Korean title and **actual consumer use
×0.01**. We preserve that discrepancy instead of adopting a UI label as proof.

## Effects, modes, signs and availability

Torque coefficients are relevant to the selected torque controller, not universally
to angle/PID/MEB branches. Custom settings are sampled every ten controller
frames. A positive newly sampled custom value assigns factor/friction and PID
gains, including a captured CP offset; the previously cached mode gates live
updates. The source's reset branch checks previous mode >1, despite the UI's 0..1
range. This inconsistency is recorded without changing it. The source does not
establish exclusive ownership or an atomic live/custom transition.

The default linear conversion divides lateral acceleration by factor and adds
friction compensation; the friction helper interpolates signed compensation from
error with a deadzone when enabled. This supports a **scoped** factor interpretation
of m/s² per normalized torque and friction contribution in normalized torque.
Brand/NN alternatives and unqualified identification prevent promotion to a
universal canonical unit or PR #9 equivalence. Factor/friction are magnitudes or
coefficients, not left/right commands; the sign of the resulting correction is
consumer/error dependent. No global steering sign is assigned by this catalog.

PID gains multiply the callback-dependent error/feedforward domain. The ordinary
PID uses proportional error×Kp, integral increments error×Ki×dt, and feedforward×Kf,
with existing clipping/override semantics. Software coefficient units are proven
only at that level. They do not establish physical vehicle gain units, NN model
identification or beneficial numerical values. NN/NN-lite and brand callbacks are
recorded alternative consumers, not resolved application ownership.

For SteerRatioRate, a valid CustomSR override (raw ×0.1, finite and >1) takes
precedence; otherwise the helper handles invalid rate input/floors and applies
learned ratio×rate×0.01. Hoya MEB bypasses this transformation entirely; c213 and
current do not. A UI zero is not an available valid rate: source fallback rules
apply. Source-specific numeric guards are descriptive only.

Delay zero means liveDelay selection in the documented controlsd path, but not
in every consumer. Modeld selects positive custom delay or liveDelay and includes
dynamic smoothing. NN/NN-lite initialization caches raw×0.01 **plus 0.3s** for
desired lateral jerk timing, with no zero-to-live replacement in that expression.
Delay is software timing configuration, not a measured actuator delay. Controlsd
gating also differs by revision; see the compatibility matrix.

The offset logical ID is **not** a literal unfiltered wire field. Torqued publishes
latAccelOffsetRaw and latAccelOffsetFiltered alongside factor/friction/version/
useParams/validity. Controlsd passes the filtered value to the torque live setter
under source checks. Positive custom mode preserves the captured CP offset.
The default linear torque callback does not directly consume offset. Estimator
seed zero is not a known current value, default baseline or replacement for
missing evidence. The sign and canonical physical unit are deliberately unresolved.
PR #9 preserves offset in its coherent coupled tuple; it is not a tuning target,
and this package imports no PR #9 module.

## Descriptive ownership and exclusions

UI/settings writes, torqued/live publication, controlsd consumption, custom
override and NN alternatives are descriptions of competing paths. Every profile
retains OWNERSHIP_CONFLICT_UNRESOLVED. No exclusive owner, lease, CAS, readback,
rollback recovery or watchdog is inferred. Settings metadata defaults cannot
become trusted baselines. Current values are never read or stored here.

CarSelected3 is PLATFORM_SELECTOR / NOT_SUITABLE: get_car can force the platform
candidate. Its three exclusion range hashes are evidence only; it cannot enter
the steering registry. No longitudinal ID is admitted. SteerRatioRate and delay
remain separate descriptive families, not new members of PR #9's application tuple.

## Completion and next candidate

The contract is ready for descriptive consumers; the catalog is partial because
factor/friction canonical equivalence and offset units remain unresolved.
The single recommended next task is **PR #9 Carrot writer ownership/unit-resolution
audit**. It addresses the remaining application blocker without treating metadata
as authority; Episode Observer inputs and parked runtime qualification are also
still limited. That audit is not started by H2. No observer/supervisor, writer,
external AI, persistence, vehicle execution or longitudinal behavior is added.
