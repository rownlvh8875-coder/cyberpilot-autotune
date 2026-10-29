# Steering source compatibility

Sources remain distinct; a row describes the named conversion/path scope only.
SEMANTICALLY_EQUIVALENT never asserts vehicle behavior, runtime applicability or
application qualification. No PR #8/#9 source pin is upgraded.

| Role | Exact revision | Repository |
|---|---|---|
| Hoya historical | 0e9c589c1b83027146f909a9cdc306c2c665ceaf | ajouatom/openpilot |
| Runtime | c2130730239bcdb4cbde9361ab90c8d99aa4ff55 | rownlvh8875-coder/openpilot |
| Current carrot-wip | f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 | ajouatom/openpilot |

Runtime integration `7a2f051b1f3847786318900444c88c2ba7a74a67` has the same tree
as c213. Current upstream was rechecked at H2 start and had not moved from f5e4.
There is no branch-only trust or automatic latest-source selection.

| Parameter | Hoya 0e9 | Runtime c213 | Current carrot-wip f5e4 | Verdict |
|---|---|---|---|---|
| LateralTorqueAccelFactor | custom raw ×.001; live/custom/NN paths | same scoped conversion | same scoped conversion | CONDITIONAL: universal unit/brand/NN equivalence unresolved |
| LateralTorqueFriction | custom raw ×.001; callback-specific friction | same scoped conversion | same scoped conversion | CONDITIONAL: global friction equivalence unresolved |
| LateralTorqueKpV | custom raw ×.01 → PID proportional coefficient | same assignment | same assignment | SEMANTICALLY_EQUIVALENT for coefficient assignment |
| LateralTorqueKiV | custom raw ×.01 → PID integral coefficient | same assignment | same assignment | SEMANTICALLY_EQUIVALENT for coefficient assignment |
| LateralTorqueKf | custom raw ×.01; English/Chinese UI label ×.001 | same discrepancy | same discrepancy | SEMANTICALLY_EQUIVALENT for assignment, UI gap retained |
| LateralTorqueCustom | positive sampled value selects custom; cached live gate | same mode semantics | same mode semantics | SEMANTICALLY_EQUIVALENT for selector, ownership unresolved |
| SteerRatioRate | MEB early return bypasses manual/rate; others resolve | no MEB bypass; all platforms resolve | same helper, additional VM geometry update in controlsd | DRIFTED |
| SteerActuatorDelay | controlsd read each state_control | lane-plan/active conditional read | lane-plan/active conditional read | DRIFTED; model/NN consumers remain separately scoped |
| liveTorqueParameters.latAccelOffset | filtered wire/live setter; CP default custom | same named wire/tuple path | same named wire/tuple path | UNRESOLVED global units/qualified identification |

UI min/max/default and native INT declarations/defaults match across the three
pins. Those matching defaults still disagree between UI/native registries for
Custom (1/0) and Delay (30/0). Matching metadata is not matching whole software.

The resolver claim is about its actual source-specific implementation. Current
controlsd additionally calls VM.update_geometry(centerToFrontRatio); c213 does
not. Therefore even a matching rate multiplier cannot prove equivalent VM or
physical response. Similarly, matching torque gain assignment does not establish
equivalent NN/brand callback outputs or independent parameter identification.

All supporting claims carry their own repository/revision/blob/range hashes in
[the source manifest](evidence/steering_parameter_knowledge_sources.json). Catalog
entries have separate identities even when conversions match. On any new source
revision, add independently reviewed claims/profile; an unknown revision query
returns None. Do not relabel these profiles or silently reuse old evidence.
