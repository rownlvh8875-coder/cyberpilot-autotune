# Existing writer/source conflicts

Runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55 and current
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 have the following conflicts **if an
additional ungated CyberPilot writer were introduced**. No such writer exists
in this PR. DEFINITE describes the stated source path/condition, not a claim
that an actual vehicle conflict occurred. See runtime/current-prefixed evidence
in [the manifest](evidence/carrot_writer_ownership_sources.json).

| Writer/source | Factor | Friction | Offset | Active condition | Can overwrite/invalidate proposed ownership? |
|---|---|---|---|---|---|
| torqued → controlsd live setter | Filtered candidate | Filtered candidate | Filtered candidate | all_checks/useParams and cached custom <=0 | DEFINITE: controlsd reassigns on each eligible frame, even with no new publication |
| Manual/custom torque | Params ×.001 | Params ×.001 | Captured CP default | Fresh selector >0 at ten-frame sampler | DEFINITE: overrides earlier live assignment in that call |
| Full NN / NN-lite / brand callbacks | Bypassed or conditional | Bypassed, special override or shaped helper | No direct scalar use in inspected equations | Actual cached flags, model_good and callback | CONDITIONAL: computation-mode conflict, not a coefficient writer |
| Default CarParams | Table seed | Table seed | Seed/captured default | Construction or source-specific reset | CONDITIONAL: startup/session or reset replaces numeric state |
| controlsd initialization | New builder | New builder | New builder | Process/controller construction | DEFINITE: invalidates any prior instance/session claim |
| Params/UI refresh | Per-key intent | Per-key intent | No tuple offset UI key | Reads follow external stored updates | CONDITIONAL: partial storage epoch/mode changes; no controller tuple transaction |
| CyberPilot proposed writer | Not implemented | Not implemented | Must preserve | No real owner capability yet | UNRESOLVED: must not be added as a second direct setter |

## Mode arbitration requirements

- Continuous custom >0 prevents live assignment but does not stop torqued fit or
  publication. Message freshness cannot prove effective consumer ownership.
- 0→positive and 1→0/>1→0 transitions depend on cached selector and source call
  order. A mode change invalidates a future owned context; no silent handoff.
- Full NN good-model response, fallback to callback, NN-lite and GM neural/siglin
  must be distinct capabilities. Proposed initial activation is **linear torque
  only**, with exact callback and NN/custom context separately attested. Merely
  declaring a Hyundai brand or torque tuning kind is insufficient.
- `WRITER_MODE_UNSUPPORTED_NN` and `WRITER_MODE_CONTEXT_CHANGED` are design
  rejection candidates, not implemented runtime statuses or permission grants.
- Any future owner must route every effective coefficient assignment, including
  defaults and mode resets, through the same owner domain. All proposal sources
  need explicit priority/lease rejection rules and no hidden retry.

Live publication contains three fields in one message; the consumer currently
assigns them in one serialized source call. We do not assert spontaneous
interleaving in that ordinary path. The missing guarantee is an owner-visible
immutable tuple transaction/revision/ack/readback protocol for external updates.
Manual storage reads can span independently written keys; a single-file Params
lock is not a multi-key controller transaction.

Evidence: estimator-main, controlsd-frame, live-setter, controller-init,
controller-compute, callback-init, gm-select, cp-seed, settings-write, params-put;
PR #9 ports and coordinator define the stronger required ownership contract.
