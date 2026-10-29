# PR #9 SteeringTarget acceptance mapping

Inspected exact PR #9 head: 6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5.
Read documents steering_application_contract.md / steering_application_design.md
and actual application/ports.py, contracts.py, coordinator.py and cyberpilot.py.
H3 changes none of those files and imports/executes no application capability.
Evidence: pr9:ports, pr9:contracts, pr9:coordinator, pr9:contract-doc, pr9:design-doc,
pr9:research and pr9:parameter-spec in the source manifest.

PROVEN means an existing source fact only. DESIGNABLE is a proposed obligation;
SOURCE_CHANGE_REQUIRED is absent in current Carrot; BLOCKED needs unresolved
acceptance/qualification. None of these labels authorizes a writer.

| PR #9 requirement | Proposed Carrot owner mechanism | Status |
|---|---|---|
| snapshot() coherent selected tuple | Immutable actual-consumed factor/friction/offset sampled at owner boundary | SOURCE_CHANGE_REQUIRED |
| owner identity | Non-identifying owner instance/session identity, not a metadata owner label | SOURCE_CHANGE_REQUIRED |
| scope | Independently reviewed steering-only application scope | DESIGNABLE |
| context identity | Exact source, controller/callback, NN/custom, VM context; mode changes invalidate | SOURCE_CHANGE_REQUIRED |
| baseline epoch | Bind independently trusted baseline/session; no default/cache substitution | SOURCE_CHANGE_REQUIRED |
| monotonic sample timestamp | Owner consume/sample time in one monotonic domain, not publication time | SOURCE_CHANGE_REQUIRED |
| revision | Monotonic effective tuple/mode transition counter | SOURCE_CHANGE_REQUIRED |
| commit(expected_revision, values) | Compare expected revision and replace tuple in one serialized owner operation | SOURCE_CHANGE_REQUIRED |
| atomic selected tuple | Consume one immutable tuple per controller calculation, preserve offset | SOURCE_CHANGE_REQUIRED |
| revision +1 acknowledgement | Ack exact committed next revision only after completed operation | SOURCE_CHANGE_REQUIRED |
| independent readback | New owner snapshot after ack must observe consumed tuple and revision | SOURCE_CHANGE_REQUIRED |
| unrelated state preservation | Preserve offset/untuned keys and all gains/limits/engagement/controller state | DESIGNABLE |
| exclusive ownership | Route all live/custom/default transitions through one effective owner | SOURCE_CHANGE_REQUIRED |
| rollback capability | CAS trusted original tuple only at provably owned revision; verify readback | SOURCE_CHANGE_REQUIRED |
| deterministic failure semantics | Explicit reject/unknown/foreign/partial/deadline fault; no retry/rearm | DESIGNABLE |
| watchdog execution ownership | Owner-loop checks plus separately approved stalled-process/liveness/recovery responsibility | BLOCKED |

TargetSnapshot permits a selected subset in its general type, while the initial
Carrot owner design here must expose the complete coupled triple. Tuning selectors
remain only lat_accel_factor and friction; offset is preserved state. An offset
missing from the effective snapshot must reject; it is not seeded with zero.

The coordinator validates owner/context/epoch/scope, shape, age and expected
revision, asks independent authorization, rereads, CAS commits, then independently
reads the whole tuple. Unknown effective values remain None. Recovery must match
the previously verified or exact pending revision/tuple and refuses foreign state.
The port's synchronous shape is not satisfied by publishing an unacknowledged
proposal or reading back stored intent. Callback overrun is detected after return;
this source does not provide a preemptive external watchdog.

## Twelve real-writer gates

| Gate | H3 result |
|---|---|
| Factor equivalence | BLOCKED: scoped base/fit role proven, global qualified CyberPilot mapping absent |
| Friction equivalence | BLOCKED: fitted spread versus additive callback coefficient unresolved |
| Offset preservation semantics | PROVEN source role; effective coherent readback still absent |
| Single owner selected | DESIGNABLE: C shared owner, not implemented/approved detail |
| Existing conflicts mapped | PROVEN for inspected graph/conditions |
| CAS/revision design approved | BLOCKED; SOURCE_CHANGE_REQUIRED |
| Effective readback design approved | BLOCKED; SOURCE_CHANGE_REQUIRED |
| Rollback source identified | DESIGNABLE: independently trusted original effective tuple/epoch |
| Custom/NN handled | DESIGNABLE: context faults and unsupported-mode admission; no implementation |
| Runtime source selected and qualified | BLOCKED: integration reference exists; actual installed runtime unknown |
| Vehicle fingerprint/context | BLOCKED: RUNTIME_FINGERPRINT_UNCONFIRMED |
| Vehicle bounds/rates | BLOCKED: no approved values supplied or invented |

Scientific proposal validity is separate: even a future unit-compatible owner
cannot promote residual diagnostics or H2 descriptor metadata to independently
qualified identification, AuthorizationGrant or SteeringRequest. Actual baseline,
vehicle bounds/rates/deadlines, rollback/watchdog owner acceptance and parked
runtime qualification are not supplied by H3.

Final distinct statuses:

```text
CARROT_WRITER_ARCHITECTURE_BLOCKED_UNIT_EQUIVALENCE_AND_OWNER_PROTOCOL_ABSENT
FACTOR_UNIT_EQUIVALENCE_UNRESOLVED
FRICTION_UNIT_EQUIVALENCE_UNRESOLVED
OFFSET_SEMANTICS_PROVEN
OWNERSHIP_MODEL_SELECTED
CAS_SOURCE_CHANGE_REQUIRED
READBACK_SOURCE_CHANGE_REQUIRED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
```

OFFSET_SEMANTICS_PROVEN is scoped fit/filter/preserved-state interpretation, not
physical bias calibration or a current owner snapshot. No actual writer, units
converter, bounds policy, application activation, vehicle execution or next task
is implemented by this audit.
