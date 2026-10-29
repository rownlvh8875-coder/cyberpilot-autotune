# Offline native friction source/schema registration result

## Outcome — content identity only

OFFLINE_NATIVE_SOURCE_SCHEMA_CONTENT_REGISTRATION_READY

The PR18 native patch now has a reproducible **complete applied tree and synthetic
commit identity**, plus explicit source/schema hashes. This is an offline content
record, NOT a qualified H7 source profile, native fork commit/push, deployment,
runtime fingerprint or permission. The normal producer remains disabled. No old
tracked file is changed: installed source, H6/H7, native patch assets, historical
evidence, CI and PR8/9/16/17/18 are preserved.

## Reproducible identities

| Identity | Exact value |
|---|---|
| CyberPilot patch/base (PR18) | `0d1d44c808050835aa5a52c3ddd76d51cb3300b0` |
| Native parent R | `c2130730239bcdb4cbde9361ab90c8d99aa4ff55` |
| R complete root tree | `ffb213d9fdc0f9618264822bd2a4e26263abfe74` |
| Applied complete root tree | `6185197d6f334f745a9c082519013b8fe0376f65` |
| Offline synthetic candidate commit | `9957868acc7459f515f1b79e9315cf93a878d933` |
| Patch SHA-256 | `8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac` |
| Comparative C/carrot-wip re-read | `f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3` |

The synthetic commit has exactly one parent, R. Its author/committer are fixed
`CyberPilot Offline Recipe <offline-recipe@example.invalid>` with recipe timestamp
`1793169536 +0000`, not a real author, signature, review/event time or device ID.
The complete raw commit payload is in the
[content record](evidence/carrot_passive_native_registration.json).

Only six native modifications and one addition are in the complete tree diff:
custom.capnp, log.capnp, services.py, PID, LatControlTorque, controlsd and the new
friction_observation helper. Their modes, before/after Git blob IDs and target
SHA-256 hashes are recorded. All unrelated tree entries are retained from R,
including unchanged symlinks and other modes, rather than omitted by a sparse
file manifest. Independent Git index reconstruction yields the same root tree.

Temporary Git objects are removed on completion; no persistent native ref, index,
config, checkout or remote is created/modified. This SHA cannot be fetched from a
native branch: no such branch/commit was published. Untouched promisor objects
may still be absent locally. The record is neither a standalone Git bundle nor
proof of complete source availability, full native build or deployable firmware.

## Schema registration semantics

`source_schema_digest` retains H7's original meaning: SHA-256 of exact applied
`openpilot/cereal/log.capnp` bytes:
`00ca3b61347659b2515d36efe26cedff57965ca9610e15fe6b2cafdeaefe3b77`.

`schema_closure_digest` is separate:
`7e80fb64b6163be664f3fe4bd96bcf5ff8634d708c7ec2e867aa165b416f394e`.
It hashes canonical records for all five schema files: applied log/custom plus
unchanged deprecated.capnp, include/c++.capnp and opendbc car.capnp. Each entry
binds path, Git blob ID and raw SHA-256. The semantic-wire map hash is also pinned
to PR18. These are content identities, not new wire fields or authority tokens.

Receipt version remains `friction-observation-v1`. The content-record format is
`passive-native-offline-registration-v1`, independent of receipt/source versions.
Its digest hashes all fields except itself, using sorted compact UTF-8 JSON,
explicit null/false and no NaN/Inf. Duplicate JSON keys reject. Verification
reconstructs expected content; recomputing a caller digest cannot approve changes.

H7's `SOURCE_SCHEMA_DIGESTS` and ObservationPolicy are unchanged. They reject this
new revision/schema pair. No producer constructor integration, decoder/adapter,
estimator bridge or runtime source-allowlist entry is introduced. Even a future
registered source remains blocked by absent independent q and incomplete cohort.

## Reproduce and verify offline

From this CyberPilot Git checkout, with the nine existing exact-R blobs and all
required R tree objects already warmed in a read-only Git input:

```bash
python -m compatibility.friction_native.registration \
  --reference-checkout /workspace/scratch/friction-native-reference
python -m compatibility.friction_native.registration \
  --reference-checkout /workspace/scratch/friction-native-reference --print-record
GIT_NO_LAZY_FETCH=1 python -m compatibility.friction_native.run \
  --reference-checkout /workspace/scratch/friction-native-reference --verify-history
```

The first verifies committed evidence; the second prints a fresh record but does
not save/change anything. The third executes the mandatory compiled-schema,
native-body, patch and registration suite. New test modules are discovered by
the existing source job automatically; CI itself is unchanged. Tools/assets remain
repository-only; no native source or dependency is added to the neutral wheel.

Git object/index/worktree/config-count overrides are removed from subprocess
environment; replacement objects are disabled. Global/system Git config is not
loaded. Network protocols and promisor lazy fetch are denied; missing inputs fail
closed. Only temporary object storage has write commands. Actual source/cache
files/refs/config/object metadata are unchanged before/after verification.

## Verification observed

- Baseline1481 core tests; final1494 pass. New registration tests21 pass.
- Mandatory exact-source native suite126 pass, no skips, including existing real
  Cap'n Proto compile/old-new reader interoperability and controller-body parity.
- New offline tool:119/125 statements95.20%,32/38 branches84.21%, combined92.64%.
  Defensive Git corruption/error paths are not all exercised; no100% claim.
- Real recursive-tree vs independent read-tree/update-index/write-tree oracle;
  exact single parent/seven paths, modes/hashes and reference unchanged.
- Wrong/missing source, SHA-256 object-format mismatch, mode/layout mismatch,
  duplicate JSON keys, altered parent/digest/authority and unknown/type fields
  reject; unchanged H7 policy rejects the new source.
- H2–H7 source/history audits, design audit, lint/format/mypy71 installed files,
  build/fresh vanilla wheel, replay11 tests/four fixture digests, knowledge/owner/
  science/research and optional-dependency smokes pass. Wheel imports70 modules
  without NumPy/cereal; H7/H6 source hashes unchanged.

Final exact-head independent review, hosted push/PR CI, rulings and any deferred
minor findings are recorded in the stacked Draft PR to avoid altering the reviewed
head. Local checks alone are not a claim that hosted CI completed.

## Retained qualification gates

INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
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

Every candidate/application/runtime/owner proposal permission remains false.
No real driving data, q reconstruction promoted to truth, actual Params access,
vehicle, device, real SubMaster, controller execution outside offline doubles,
full native/C++ build, transport activation, estimator qualification, application,
longitudinal behavior change, external AI integration or upstream/native-fork PR.
Timing/allocation/deadline/backpressure remain unqualified. PR18's M1 deferred
custom-selector/frame10 latch-reset parity gap remains, not silently closed here.

Recommended next SINGLE task: offline native custom-selector/frame10 parameter
latching/reset parity tests to close PR18's M1 before considering broader native
qualification. No automatic start, native deployment or vehicle permission.
