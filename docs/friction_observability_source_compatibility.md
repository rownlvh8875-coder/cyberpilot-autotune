# R/C source compatibility for H7

R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55.
C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
carrot-wip was re-read at H7 start and still equals C; no branch movement or
automatic promotion. H7 primary profiles remain the H6 pins.

evidence/friction_observability_receipt_sources.json pins 41 files, 34 semantic
claims, file/blob/range hashes and H6 acceptance-basis content. Its canonical
digest is c2bc6a566ec0a9906e9ce407fce6ec803d1c8f0dc72edd696b6dd2f46c36a747.
Explicit source audit runs isolated exact helper/callback/PID/VM math only:
44 helper/callback/PID cases plus H6 geometry parity, no native imports or Params.
Exact source archives are audit inputs outside the installed package.

| Field / semantic | c213 | f5e4 | Receipt impact |
|---|---|---|---|
| LINEAR a | desired accel minus roll*g | same | exact callback input, not achieved acceleration |
| LINEAR friction input | desired minus actual accel | same | local error, not PID/log error |
| feedforward flag | compensation=True, gravity_adjusted=True | same | false flag is preserved diagnostic, not eligible pinned FF call |
| q helper | strict interior deadzone; interpolate [-T,T] to [-C,C] | same | normalized q conceptual; not exposed; no h/C inference |
| threshold | 0.3 from interfaces | same | exact source constant, not a new empirical cutoff |
| raw callback | a/float(F)+friction | same | before k_f, no offset regressor |
| offset | stored via live update/custom defaults | same | context optional; LINEAR return does not read offset |
| NN_LITE | accel error + lookahead jerk; branch-dependent gains | same | separate executed family, diagnostic only |
| NN | NN inputs/history/roll/jerk, optional override in PID error | same | not additive LINEAR ff; diagnostic only |
| custom latching | periodic installed F/C/gains reads, live-update bypass | same | selector plus actual family/values/generation, never defaults inferred |
| PID | speed latch then effective gains, p/f/d, i clamp, sum/output clip | same | gain capture after current speed latch; scaled f not raw ff |
| PID error precision | pid_log.error Float32 before PID use | same | distinct from local friction-driving error |
| return sign | -internal output | same | requested actuator sign is separate from raw callback |
| published torqueState | Float32 p/i/d/f/output/desired/actual/error | same | not raw local precision |
| CP tuning precision | Float32 F/C/offset/gains | same | Float64 receipt preserves consumed decoded value, not lost intent |
| geometry | static CP axle baseline; VM live stiffness/SR updates | dynamic coherent geometry path too | R static baseline vs C actually applied VM; no backport assumption |
| CenterToFrontRatio zero | no dynamic key/live path | vehicle-default intent; LP is candidate until applied | never physical ratio zero |
| effective SR | live/rate/CustomSR resolver | same, plus geometry update | separate SR context from CG and delay |
| delay | SAD/liveDelay branches and NN initialization/lookahead | same | source/branch/effective value and pair metadata explicit |
| source timestamps | Event times but no atomic callback receipt | same | consumed IDs/capture receipt still missing |
| consumed object origin | wire CS, fresh local CC; LP can be local fallback | same | role/origin pinned; consumed local objects bind current cycle; no cross-cycle local-ID reuse |
| cycle start / serial entry | state_control entry before local allocations; serial run loop | same | explicit caller-entry timestamp, local creation interval and next-cycle publication boundary |

## Source details not inferred from comments

Custom branch reset is guarded by the previous selector being >1. The comment
mentions 1->0 reset, but that is not what the condition implements. H7 does not
fix it or assume selector 0 means all coefficients reverted to CP defaults.
Only actually latched installed values and generations describe the cycle.

The callback reads F and friction; latAccelOffset is stored but not referenced
in the LINEAR return. Existing filtered/raw offset fields are not automatically
an effective LINEAR regressor or a qualified bias estimate.

Gain getters interpolate using PID self.speed. That speed is assigned at the
start of PID.update, after ff callback evaluation. A pre-callback gain getter
can therefore return previous-cycle speed's gain. H7 gives GainSnapshot a
separate actual-use cycle/time binding.

Existing helper has no direct independent q to capture. A real producer needs a
reviewed helper-state interface and source-profile update. A declaration of
HELPER_OBSERVED in a synthetic receipt is not proof such a runtime exists.

## Compatibility boundary

H7 does not change any native source, cereal/custom schema, CP tuning, Params,
controller output or liveTorqueParameters publisher. A future patch produces
new source/schema identities and requires explicit compatibility review.
A hash binds content only; it does not confirm a device runtime fingerprint.
RUNTIME_FINGERPRINT_UNCONFIRMED and representation/runtime/empirical/application
blockers remain.
