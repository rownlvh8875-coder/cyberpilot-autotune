# H3 Carrot steering writer ownership audit

**Decision: CARROT_WRITER_ARCHITECTURE_BLOCKED_UNIT_EQUIVALENCE_AND_OWNER_PROTOCOL_ABSENT.**
The audit is complete; an actual writer is not implemented or authorized. Source
identity and a selected architecture do not close units, owner protocol, vehicle
policy, scientific identification or watchdog acceptance gates.

## Exact basis

| Role | Exact revision |
|---|---|
| H3 target main/base, PR #11 merge | 66f4b79036560a11e7020af9cc214118dcbd4fba |
| Runtime source | c2130730239bcdb4cbde9361ab90c8d99aa4ff55 |
| Integration, same runtime tree | 7a2f051b1f3847786318900444c88c2ba7a74a67 |
| Current upstream carrot-wip | f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 |
| Historical Hoya comparison only | 0e9c589c1b83027146f909a9cdc306c2c665ceaf |
| Preserved PR #9 application contract | 6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5 |
| Preserved PR #8 sidecar | e4361678ed176cbd7c0bb6f838d3daa7174caf22 |

Current upstream was rechecked and had not moved from the supplied last observed
f5e4 pin. No runtime compatibility pin is upgraded. The source manifest independently
binds 55 files and 93 source ranges/claims with Git blob and SHA-256 identities.
The two PR #9 documents, ports, contracts, coordinator and research guard were
read at the exact PR #9 head; they are not installed/imported into main.

PR #11 was OPEN/Draft/mergeable at expected ea79157 with all 12 checks successful,
no unresolved threads and independent C0/I0/M0. Only knowledge production files
were added; previous runtime/control files were unchanged. It was made Ready and
merged using merge method with the exact-head guard, at 2026-10-29T02:14:04Z.
Parents are dd1d4232f3d151fe9bbf0808c1fbe5131618b09a and
ea79157035e9c92076f3996cb5f4b65dbd8832a8. Ancestor and merge/head tree equality
checks passed. No force push, squash, rebase or admin bypass was used.

## Ownership questions, answered for runtime and current source

| Question | Finding | Source evidence suffixes |
|---|---|---|
| Q1 factor authoritative writer? | No exclusive application owner. CP seeds; torqued proposes; controlsd live setter and custom sampler assign effective builder state under conditions | cp-seed, estimator-init, controlsd-frame, live-setter, controller-compute |
| Q2 friction writer? | Same competing paths; its estimator and callback meanings also need separate unit proof | fit, friction, live-setter, controller-compute |
| Q3 filtered offset producer? | TorqueEstimator filter updated from TLS intercept, initialized from CP-related seed or matching cache; message publishes latAccelOffsetFiltered | estimator-init, fit, filter-update, publish |
| Q4 custom behavior? | Cached positive selector suppresses setter; newly sampled positive selector writes manual coefficients/CP offset. torqued stays running/publishing under its independent lifecycle | live-setter, controller-compute, estimator-main, processes |
| Q5 NN effect? | Full NN good-model path bypasses factor division; optional friction override still uses callback. NN fallback, NN-lite and GM neural/siglin differ. Generic writer activation is unsupported in these unqualified modes | callback-init, controller-compute, gm-select, gm-neural, gm-siglin |
| Q6 effective truth? | Consumer builder plus actual mode/callback determines calculation. Latest estimator message or Params storage alone does not prove consumed state | controller-init, controlsd-frame, controller-compute |
| Q7 sample/use order? | Every control call attempts live update before LaC.update; its ten-frame custom sampling precedes active calculation | controlsd-loop, controlsd-frame, controller-compute |
| Q8 mixed updates? | Live fields come from one message and same setter call. Manual keys are read separately and can reflect different storage updates; no multi-key transaction/owner revision | live-setter, settings-write, params-put, controller-compute |
| Q9 tuple coherence? | Normal live source order is known, but atomic owner-visible replacement/ack/readback is not established. Custom resets offset independently of live estimator state | live-setter, controller-compute, schema |
| Q10 exclusive owner? | No PR #9-compatible exclusive owner protocol exists in the inspected graph | live-setter, schema, params-put, pr9:ports |

R and C agree on those ownership gaps. C changes VM context, not the live setter,
custom arbitration or torqued calculation formula. See [the graph](carrot_steering_writer_graph.md).

## torqued lifecycle and health limitations

Manager starts torqued only onroad. It constructs an estimator from CarParams;
useParams depends on allowed brand and torque tuning. It does not inspect custom
or NN mode to stop publication. A user selecting custom is not an ownership
handoff recognized by the estimator.

Ordinary fit admission requires source activity history, no override, velocity/
torque/acceleration gates and adequate point buckets. The normal minimum sample
count is 4000, with distinct decimated settings and bucket requirements. These
are **existing diagnostic estimator heuristics**, not newly approved learning or
vehicle application policy. TLS produces slope/intercept and perpendicular
spread. Source sanity clipping affects factor/friction; offset is filtered without
the corresponding clip in this path.

At nominal 4 Hz get_msg emits filtered values even when no new valid fit updates
them. liveValid is separate from Event.valid and controlsd only checks the latter
through all_checks plus useParams. A reset recreates histories/buckets/decay but
does not recreate existing filtered parameter objects. Thus publication freshness
is not the age of the estimate or proof of live fit validity. Source NaN/None
screening is not a complete finite-value/qualification contract.

Cache restore uses fingerprint/tuning/offline factor/friction/estimator VERSION;
VERSION=1 is cache compatibility, not a monotonically increasing owner revision.
Existing upstream writes LiveTorqueParameters cache periodically and removes
failed cached data. **This is audited reference behavior, not persistence added
or executed by H3.** No device Params are accessed. Its restore key is not a PR #9
trusted baseline/epoch, and it does not bind all custom/NN/live-geometry context.

With an ungated additional setter, the current controlsd path can replace its
values on the next control call using the same still-healthy latest message,
without waiting for a new torqued publication. Manual custom sampling provides
another replacement path. A direct Python setter therefore cannot be wrapped
as an exclusive SteeringTarget.

## Readback, CAS and atomicity

| Candidate | Why it does not satisfy current verified readback |
|---|---|
| Params | Stored per-key intent, not scaled/consumed tuple; no effective offset/revision |
| latest liveTorqueParameters | Estimator proposal can be ignored or old; no owner ack/revision |
| controller internal builder | Closest numeric state, private/mutable, no public coherent owner snapshot/revision/lease |
| new owner-managed state | Selected future mechanism; currently absent; must read consumed state rather than echo request |
| CarControl / CarOutput receipt | Command/actuation cohort evidence, not parameter tuple/revision evidence |

**NO_EXISTING_VERIFIED_READBACK; NO_EXISTING_CAS; ATOMIC_TUPLE_NOT_PROVEN.**
The existing setter accepts three values, not expected_revision; it returns no
revision+1 acknowledgement. Params has single-file lock/rename/fsync behavior,
but no controller tuple CAS, effective readback or owner epoch. No claim is made
that every unrelated subsystem lacks revisions: these findings concern the
inspected torque parameter ownership graph.

PR #9 accepts exact numeric selected-tuple readback. CP/message fields are
Float32: a future owner must explicitly qualify representation/round-trip
semantics before authorization. Silently rounding a Float64 proposal after its
grant, or returning an unconsumed higher-precision echo, would not meet that port.
No threshold/rounding policy or converter is implemented here.

## Rollback and watchdog ownership

Rollback source must be the independently trusted original baseline, bound to a
coherent effective owner snapshot/epoch at admission. It is not UI default, CP
startup seed, estimator cache or unrelated latest live message. Recovery must
prove the still-owned revision (including an exact uncertain-commit cohort), CAS
restore and independently verify, preserving offset and unrelated state. A
foreign/unknown revision must not be overwritten to manufacture recovery.

The recommended owner executes ordinary hold/veto checks at its serialized
consumption boundary. PR #9 watchdog remains caller-driven and cannot preempt a
blocked callback or frozen control process. There is **no approved independent
execution owner for stalled-process recovery** in current source. A detailed
design must assign liveness monitoring, restart/session invalidation and recovery
ownership, explicitly stating when actual restoration cannot be proven. Another
process's control/transport liveness gate is not parameter rollback verification.
No watchdog guarantee is inferred, and no process/reboot/control change is made.

## Source drift and Hoya comparison

Current C adds live center-to-front geometry/axle-stiffness updates in VM and
paramsd. This changes VM-derived curvature/acceleration/error and potentially
closed-loop data context: **SOURCE_DRIFT_AFFECTS_IDENTIFICATION**. The torqued file
and its yaw/speed/roll-based input formula are byte-identical between R/C and do
not directly call VehicleModel. This is potential context drift, not a measured
change in fitted parameter accuracy or proof of an altered torque unit.

Hoya api_autotune_apply_params at exact 0e9 reads prior storage values, loops per
key, clamps using UI metadata, calls set_param_value and records engaged=False.
It returns the prior storage snapshot; it has no effective controller tuple CAS,
exclusive owner, verified recovery or watchdog. It remains
**APPLICATION_ARCHITECTURE_REJECTED**, a comparison only (hoya:apply).

## Decisions, evidence and verification scope

See [units](carrot_torque_unit_equivalence.md),
[conflicts](steering_writer_conflict_matrix.md),
[options](carrot_writer_architecture_options.md),
[PR #9 mapping](carrot_writer_pr9_mapping.md) and
[machine-readable matrix](evidence/carrot_writer_unit_matrix.json).
H2 descriptors are a proof index only; none becomes QualifiedEvidence, bounds,
baseline, writer lease or authorization. H2 source/catalog identities stay intact.

The audit validator checks pins, identities, references, decision completeness and
negative promotion cases. Explicit local-Git mode verifies all source bytes and
inclusive LF line ranges and inspects selected structural AST/schema witnesses;
no reference imports, tests or models are executed. Semantic interpretation still
requires human/independent review; hashes alone do not prove an absence claim.

```text
python -m tests.audit.validate_carrot_writer
python -m tests.audit.validate_carrot_writer --reference-checkout <local-openpilot-git>
python -m pytest tests/audit/test_carrot_writer_ownership.py -q
```

Existing pytest CI discovers the new audit tests. Its existing source-fetch job
continues to verify H2 only; **full H3 Git-byte validation is separately run locally**.
No CI workflow changes are made because H3 permits only docs/evidence/audit files.
All tracked production and replay fixture bytes are frozen to the merge basis;
checkout CRLF normalization is allowed only in that preservation check, never
when hashing raw upstream file/range evidence.

No source bodies are copied; evidence and descriptions are independently written.
No LICENSE choice is made. No writer/application/learner, Params read/write,
persistence, external AI, real logs, vehicle execution, longitudinal behavior or
upstream PR is introduced. PR #8/#9 remain unchanged and unmerged.
