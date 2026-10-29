# Passive Carrot friction observation producer — offline implementation result

## Outcome

PASSIVE_NATIVE_FRICTION_PATCH_BUNDLE_IMPLEMENTED_OFFLINE

This is implementation, not another schema proposal: the bundle changes seven
native paths at exact R, compiles the patched Cap'n Proto schema, executes pinned
baseline/patched Python controller bodies and applies the generated patch in an
empty sandbox. It is NOT deployed to a native fork/device, is not enabled at normal
startup and is not qualified for runtime/transport, empirical identification or
application. No upstream/fork-native PR, merge, Params access or vehicle action.

## Reproducible delivery

CyberPilot base: cd02d81b745565aa8ae41d4799fd1b1687f2a07e, unchanged design PR17.
Branch: feat/carrot-passive-friction-producer; stacked Draft PR against the design
branch, not main. First docs-only implementation freeze:2f137a2.

Native base R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55 in
rownlvh8875-coder/openpilot. Comparative C/carrot-wip re-read remains
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3. No C port or automatic promotion.
Neither source is proof of the user's device fingerprint.

Artifacts in native_patches/friction_observation/:

- instrumentation.patch: actual unified native patch; git apply --check and actual
  sandbox application both tested against exact pinned original files.
- friction_observation.py: stdlib-only bounded per-cycle collector, immutable
  finite-validated content envelope, encoder and post-seal Event construction.
- receipt.capnp: compiled wire implementation of the frozen134 fields/13 records/
  16 enums. Ten policy/eligibility/authority fields remain evaluator-local.
- edits.json: deterministic exact-source edit recipe, not a runtime dependency.

[Evidence manifest](evidence/carrot_passive_native_patch.json) binds all nine
source files, all seven target file hashes and the patch hash. The native applied
revision is deliberately null: no native Git commit/source registration exists.
Historical H7/design manifests remain frozen and describe their own old bases;
the current implementation evidence is this new manifest, not a rewritten claim.

Native tooling/assets are repository-only. The existing neutral Python wheel and
sdist are not native patch distributions; use the pinned Git checkout for this
tooling. No openpilot/cereal/pycapnp dependency is added to the installed package.

## Native implementation surface

| Path | Change |
|---|---|
| openpilot/cereal/custom.capnp | reserved3 renamed; retain typeID0xda96579883444c35 and file ID; add explicit optional wrappers/types |
| openpilot/cereal/log.capnp | Event member renamed to lateralTorqueIdentification, retain ordinal110 and type identity |
| openpilot/cereal/services.py | dedicated service100Hz nominal, should_log=False; all old service definitions identical |
| openpilot/common/pid.py | optional update friction_observer=None, actual gain operands and preclip/postclip taps; MultiplicativeUnwindPID unchanged |
| openpilot/selfdrive/controls/lib/latcontrol_torque.py | original FF invocation entry/return, exact executed family/function/site, installed context and limits; no extra callback evaluation |
| openpilot/selfdrive/controls/controlsd.py | optional constructor observer; cycle/source/local CC/applied VM/selected-delay capture; completion after original two sends |
| openpilot/selfdrive/controls/lib/friction_observation.py | new passive native helper only |

No helper/interface equation, torqued/liveTorqueParameters, CarController, safety,
longitudinal call site or application ownership change. Shared PID old-call numeric
compatibility is tested, not a claim that instruction timing is unchanged.

## What is captured, and what is not

- Raw desired/actual lateral acceleration, roll, roll compensation, a_cb and actual
  friction input/deadzone, raw callback return before k_f. LINEAR equations remain
  a=desired-roll*g, friction_input=desired-actual and the original interpolation.
- q_observed is absent, never term/C or a reconstructed helper value. Even after
  future source registration, an otherwise complete passive receipt is MISSING_Q.
- Actual PID gain reads, components, original preclip sum and postclip output.
  A skipped k_i remains unavailable; no extra interpolation/getter invocation.
  Existing Float32 pid_log.error readback is preserved, not replaced by raw double.
- Exact executed family/function/site, CUSTOM selector separate from family;
  unsupported equations do not become LINEAR. Module/name pairs are checked.
  FF invocation index is2 in the ordinary branch,2/3 in full NN depending on the
  actually executed extra error callback. Actual NN weights are not run here.
- Source Event time/receiver sequence/seen-valid-alive cohort at consumption;
  fresh local CC/fallback LP identities never use addresses or later publish time.
  Never-seen consumed readers drop the observation, not turn defaults into truth.
- R's torque callback sees fresh local CC. Later publish pose backfill cannot be
  substituted; livePose is explicitly unused for that callback. MODEL is consumed
  even on LINEAR. No model arrays/identifying fields are recorded.
- Actually applied VM wheelbase/front/ratio/stiffness/steer ratio and raw settings;
  source/applied generations split exact context changes. Unwitnessed individual
  effective modifiers remain unavailable, not reconstructed from requests.
- Only actually selected delay is captured, MANUAL or LIVE_DELAY, with raw
  alignment/correction_count0. Unselected delay is unavailable; no Params reread,
  CP/NN initializer fallback, arbitrary shift or double correction.
- Timer saturation, instantaneous controller limit, curvature/controls limits
  and steeringPressed remain distinct. Unwitnessed actuator/override/health flags
  remain unavailable. Requested/host/applied outputs are not backfilled as raw u.

consumption_manifest_complete stays false: this passive bundle does not claim
complete upstream/control-state provenance or full H7 eligibility. Missing q,
unregistered instrumented source, incomplete cohorts/context and runtime gates are
not hidden by the newly available raw callback output.

## Default-disabled and publication boundary

Normal Controls() still has friction_observer=None. Existing PubMaster/SubMaster
arguments, Params getter calls and original send calls are unchanged. No new
subscription, socket, thread, timer, file writer or global collector is started.

Explicit offline construction requires enabled=True plus source/schema/context/
session content IDs; old R/C pins and branch names cannot label instrumented code.
IDs are content identity only and do NOT register a qualified source or grant any
authority. Tests use clearly synthetic IDs. Session/context inputs must be
non-identifying. The real applied native SHA/schema must be registered separately.

At state_control entry the observer begins before local allocations. At original
publish completion it seals the final identity using real controlsState and later
carControl timestamps. An optional on_receipt callback gets the sealed immutable
record only after both original sends; it may use encode/to_event with a supplied
compiled schema. It does not create a transport. Callback errors affect only
observation. No observer exception catches an original controller exception.

Source/context IDs and all JSON/content hashing are deferred until completion,
after the original command send. Pre-command epoch comparison uses only fixed-size
scalar tuples, preserving signed zero without packing/serialization. A dedicated
RED→GREEN guard forbids content hashing in capture/PID/callback paths.

Synchronous publication may delay the next cycle. Allocation/hash/encoding/queue/
deadline behavior is NOT qualified. No on-device activation or autonomous publisher
is installed; explicit production transport construction must await separate exact
target qualification. No numerical tolerance is called vehicle-safe.

## Verification observed in this task

| Check | Result |
|---|---|
| Core baseline |1435 passed |
| Core final full pytest |1481 passed |
| Required source-backed native suite |105 passed, no skips |
| Native helper coverage |288/288 statements,114/114 branches,100%/100% |
| Preserved core coverage |98.52% combined; H7 remains100% statements/branches |
| Ruff / format / mypy | pass;71 installed source files typed |
| Old/new actual schema readers | compile, reserved ID/ordinal, old-empty unknown/presence and old reader round-trip pass |
| Raw Float64 / None vs0/False | actual encoded message round-trip pass; no q pointer |
| Native PID | normal/freeze/override/clip/reset/nonfinite/error, output/state bits and gain-read sequence preserved |
| Native lateral/controlsd bodies | synthetic enabled/disabled/mode/pose/delay branches; original callback/Params/send behavior preserved |
| Patch application | exact target hashes after sandbox git apply; nonempty build target rejected |
| Existing H2–H7 source/history audits | pass, including exact source blobs/ranges and unchanged science/geometry semantics |
| Replay |11 focused/golden tests pass; four wheel replay fixture digests unchanged |
| Core build / fresh wheel | pass;70 modules import outside checkout without NumPy/cereal; H7/H6 six source hashes each |
| Wheel knowledge/owner/science | pass; optional-dependency and research smokes pass |

Ordinary CI matrices without optional pycapnp skip the two schema-dependent unit
checks. The new mandatory isolated source job installs exact pycapnp2.1.0 and runs
the entire native suite with no skips. Old CI gates are retained. The historical
design audit recognizes only the exact additional install/warm/audit lines.

Tests execute actual pinned AST function/class bodies with explicit offline
dependency/IO doubles; controlsd tests use actual generated car/log readers.
They do not execute real SubMaster, Params, model weights, a full native process,
the full openpilot hardware suite or a native C++ binary build. Those are NOT
reported as passed/skipped into qualification. Python3.12.14/NumPy2.5.4 locally.

The new history check separately compares committed Git blobs exactly and labels
working-tree CRLF normalization. Base has301 files; only CI and the exact old
design-validator recognition extension may differ. CyberPilot production source,
H6/H7 contracts/tests/evidence and PR8/9/16/17 heads remain unchanged.

Final exact-head independent review, any findings/rulings/deferred minors and
hosted push/PR CI belong to the new Draft PR's final record. Local verification
is not itself hosted CI success; publication does not merge or enable the patch.

## Cloud setup and decisions

The actual setup script was run successfully: dev/research environment,
pycapnp2.1.0 and nine warmed exact-R blobs in the read-only bare dependency cache
/workspace/scratch/friction-native-reference. No services are required. The
onboarding skill saved complete install_script/start_skill in an environment
configuration DRAFT; review/save and Publish in environment settings are still
needed. Current-instance validation is not proof of a future restored snapshot.

Ruling: deliver a native patch bundle in the requested repository rather than
write a different fork/device — preserves publication/deployment boundary — cost:
native application/source registration/deployment still need a separate decision.
Ruling: reuse dedicated cloud checkout and tracked manual ledger — no unsolicited
worktree/remote skill scripts — cost: manual bookkeeping.
Ruling: execute the approved passive plan inline — no repeated design round —
cost: one final independent review, not per-task implementer/reviewer agents.
Ruling: keep native assets repository-only — preserve the dependency-free neutral
wheel/sdist scope — cost: use a Git checkout for native tooling/patch distribution.
Ruling: keep unavailable full-native/model/hardware/transport tests unqualified —
synthetic body/schema validation cannot prove them — cost: no runtime-readiness claim.

## Retained blockers and next single task

FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
INSTRUMENTED_NATIVE_SOURCE_REGISTRATION_REQUIRED
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
NO_EMPIRICAL_ESTIMATOR_BRIDGE
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED

All candidate/application/runtime/owner proposal permissions remain false/absent.
No actual vehicle, Params read/write, real runtime producer execution, estimator
qualification, candidate generation, application bridge, longitudinal behavior
change, external AI integration, preserved-PR modification or upstream PR.

Recommended next SINGLE task: prepare/review an exact native applied revision and
its source/schema registration from this patch, offline, before any runtime or
transport qualification. Not started automatically; it does not solve missing q
or authorize a device/vehicle experiment.
