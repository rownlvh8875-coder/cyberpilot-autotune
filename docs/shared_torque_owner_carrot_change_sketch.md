# H4 future Carrot source change sketch

**Sketch only: no patch, schema or runtime writer is included.** Source paths refer
to runtime `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`, as indexed by H3. Current
f5e4 geometry semantics cannot silently replace that qualified source selection.

| File / proposed boundary | Future change required | Proof needed before enabling |
|---|---|---|
| new owner module, exact native path to be agreed | sole immutable effective tuple/context/revision, bounded producer ingress, private target capability | all native transitions preserve protocol and have bounded execution |
| openpilot/selfdrive/locationd/torqued.py | retain estimator responsibility; deliver proposals/evidence rather than assuming published tuple is effective | origin/fit freshness, validity and generation; scientific units still separate |
| openpilot/selfdrive/controls/controlsd.py | sole serialized arbitration/owner/watchdog/consume scheduling; remove direct live competing install path | cycle ordering, actual context, source health and independent consumed-state readback |
| openpilot/selfdrive/controls/lib/latcontrol_torque.py | consume one installed immutable tuple; eliminate live/custom/reset direct coefficient assignments | same per-calculation tuple, offset preservation, unrelated gains/limits unchanged |
| custom Params refresh / UI ingress | coherent typed/versioned intent outside critical phase; enter owner as proposal or explicit mode request | no per-key mixed cohort or bypass write; explicit mode/epoch closure |
| opendbc_repo/opendbc/car/interfaces.py and actual selected callbacks | declare/attest callback and mode compatibility, without inventing coefficient conversion | base/NN/NN-lite/GM qualification and current context checked |
| openpilot/cereal/log.capnp, if IPC selected | possible TorqueParameterProposal and TorqueParameterState with identity/revision/time/digest/generation | versioned source/cohort/consume/Ack/readback semantics; schema alone is not CAS |
| openpilot/system/manager/process_config.py and independently accepted liveness path | assign monitor execution, generation/restart and fail-safe containment responsibilities | owner-death detection/containment proof, no concurrent backup writer |

The selected hybrid keeps the actual tuple in the controller process, so normal
commit/readback cannot be an asynchronous IPC round trip disguised as PR #9's
synchronous target. Producer messages may be asynchronous, but remain candidates
until the owner installs and the actual consumer binding is read back. No new
cereal/message type is required by the pure reference package.

## Migration sequence after separate authorization

1. Qualify units/evidence, selected runtime/context and encoding; obtain explicit
   authority for native integration work and its ordinary-mode behavior changes.
2. Inventory all construction/default/live/custom/reset/alias assignments for the
   selected exact source. Route every effective write through the owner. Leaving
   any bypass means EXCLUSIVE_OWNER_NOT_ESTABLISHED.
3. Bind the actual controller input cell and readback path; prove whole-tuple
   visibility, +1 Ack and exact encoding without a pending-value echo.
4. Integrate a separately reviewed PR #9 facade and source/authority context, with
   reservation from READY through verified close and no producer backlog takeover.
5. Prove native timing, recovery, mode transitions, shutdown/restart and external
   liveness/inhibition acceptance before any application authority is issued.
6. Separately qualify installed runtime/fingerprint, bounds/rates and parked
   execution under explicit vehicle-work authorization. No stage here authorizes it.

H4 specifies source responsibilities and dependencies, so its sketch can be
reviewed as CARROT_SOURCE_CHANGE_DESIGN_READY. That label means the proposed
change boundary is documented, not that source implementation or activation
gates have passed.

Recommended next single task after H4: **factor/friction scientific identification
qualification**. Distinguish the canonical coefficient from native residual
spread, align the signal/context/units and obtain independent qualification.
An owner model can demonstrate correct transactions without making those values
scientifically suitable. Native writer work must not bypass that distinction.
