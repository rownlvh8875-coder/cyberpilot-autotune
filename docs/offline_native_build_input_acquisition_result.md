# Offline native-build input acquisition / static-audit result

GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED
NATIVE_SOURCE_INPUT_CLOSURE_VERIFIED
LOCKED_PYTHON_AND_VCS_PAYLOADS_ACQUIRED
FULL_NATIVE_BUILD_INPUT_CLOSURE_INCOMPLETE
STATIC_BUILD_ACTION_AUDIT_INCOMPLETE
NATIVE_BUILD_EXECUTION_NOT_STARTED

## Outcome and scope

Gate A made material acquisition progress, but **did not pass**. Exact-R source,
selected locked Python distributions, VCS sources, SDK release assets and candidate
build-backend wheels are now acquired and hash checked. Static inspection found a
reachable device-probing boundary incompatible with claiming this build is already
CPU-only/device-free. No native code or probe was run to investigate it.

This is Task1 only of the
[approved plan](superpowers/plans/2026-10-29-offline-native-build-verification.md).
Its full acquisition/audit completion checkbox stays unchecked. Image preparation,
offline environment installation, native configuration/build and schema execution
(B/C/D) were neither authorized nor started. A green CyberPilot regression/CI run
does not override this BLOCKED verdict.

Base PR22: `16ee9373d8c790255591d2e887f75471f099f47b`.
Branch: `audit/offline-native-build-inputs`, stacked Draft against PR22's
`design/offline-native-build-verification`. New evidence/report files only; no
installed code, native source/patch, old evidence/test/CI/lock or policy changes.

## Inputs actually acquired

| Category | Observed result |
|---|---|
| Native R | Complete6286 blobs, raw bytes/modes and seven symlinks verified against Git; strict fsck passes |
| Native archive |436920320 bytes; SHA-256 `4a6a423095f60395ad1de1579dbbbd1b794610686fa0689b07f3cbaf031d9ae6` |
| Registry |103 target distributions:102 wheels + spidev3.8 sdist; every lock hash/size matches |
| VCS |16 exact tips/source archives:14 dependency shims, MetaDrive, pytest-xdist; strict fsck passes |
| SDK assets |14 GitHub release wheels, explicit release/asset IDs and SHA-256; no shim install hooks executed |
| Additional backend candidates |hatchling1.27.0, setuptools-scm9.2.2, wheel0.48.0, editables0.3, trove-classifiers2026.9.21.13; PyPI hash/size checked, not installed |
| Offline artifact checks |139 files,844649663 bytes; size/SHA-256 pass; wheel ZIP CRC checks12509 members; no extraction/execution |
| Negative manifest cases |Missing SConstruct source member, ffmpeg VCS build asset, driving-model entry each rejected |

R remains `c2130730239bcdb4cbde9361ab90c8d99aa4ff55`, tree
`ffb213d9fdc0f9618264822bd2a4e26263abfe74`. The unchanged passive patch remains
SHA-256 `8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac`;
existing offline registration reconstructs the same applied tree
`6185197d6f334f745a9c082519013b8fe0376f65` and unpublished synthetic recipe commit
`9957868acc7459f515f1b79e9315cf93a878d933`. No native ref was published.

Designated `ajouatom/openpilot:carrot-wip` was re-read as unchanged C
`f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3`. No source promotion or vehicle inference.
Complete source at R is not complete ancestry, deployed software or the unavailable
frozen development-fit point artifact.

The two required ONNX inputs now have verified raw hashes, not just metadata:

- dmonitoring_model.onnx:7844499 bytes,
  `dee5a294e8afaacc9295ac5d100e00733ecac278e79264b96331e40a3ede1b04`.
- driving_supercombo.onnx:60792584 bytes,
  `f73a9e535523d5e9acb9e642c64e33d631825dc8ba74123757d107cedd047bb5`.

No model import, pickle loading, inference or empirical data use occurred.

## Blocking static finding: enumeration is execution

The exact source/range hashes and call-path evidence are in
[static audit](evidence/offline_native_build_static_audit.json),22 claims.

`SConstruct → modeld/SConscript → probe_devices() → child Python →
Device.get_available_devices() → backend constructor`.

`get_available_devices()` iterates ALL_DEVICES and suppresses exceptions. It is
not a passive list of names. AMD and NV constructors select actual interfaces;
KFD/NV interfaces attempt O_RDWR opens of `/dev/kfd`, `/dev/nvidiactl` and UVM
nodes. QCOM's constructor attempts `/dev/kgsl-3d0`. `FileIOInterface` uses os.open.
The conditional PCI path can attempt sysfs enable/driver-unbind when matching
hardware, exposed paths and sufficient privileges exist.

This is a **source-level reachability finding**, not an observation of a device
open, host mutation or successful hardware initialization. Missing modules/devices
or denied permissions can make an attempt fail; that does not prove the source is
a CPU-only query. DEV=CPU does not filter this enumeration: DEV.target for another
backend falls back to that backend's default Target. No actual device availability
was queried, and no claim is made about this host's GPU/device state.

The plan's no-device/denied-action boundary needs an explicit containment decision
before configuration. Do not resolve this by running the probe, spoofing hardware,
skipping model targets, exposing devices, adding privileges or silently editing R.
The transitive audit stops **rejected**, not complete: this record is not a full
allowlist of all remaining imports/build actions.

## Other dependencies exposed by acquisition

The fourteen pinned Git shims run custom build_py hooks that fetch a release wheel
without source-pinned checksum validation. A Git pin alone was not their complete
artifact identity. Each acquired wheel now has an asset ID and raw hash, but the
future preparation stage still needs an audited offline cache/reinstall strategy.
No package hook was run and no source lock was rewritten.

The ffmpeg SDK actually contains x264/z/VA/DRM static libraries required by R's
loggerd link list; CasADi and t_renderer are bundled in the acados distribution.
These are archive-content observations, **not link/ABI compatibility or execution
proof**. No missing-library blocker was inferred solely from a package name.

pytest-xdist needs SCM metadata for its locked local version. The initial shallow
tip had no tags;64 additional ancestry levels and exact annotated v3.7.0 tag
`6d65210cfb5e69ec8b9e526a8f0fc935c721b32a` were acquired. Git describes the tip as
`v3.7.0-24-g2b4372b`; the locked Python version is
`3.7.1.dev24+g2b4372bd6`. No backend was executed to assert those produce equal
installed metadata; no pretend-version override was introduced.

spidev has no selected compatible wheel, so its exact locked sdist was acquired
directly, not installed. Its build backend needs setuptools>=61; shim backends
need setuptools/wheel, xdist setuptools-scm, root hatchling. Additional backend
candidate pins are acquisition choices outside the native uv.lock, not proof of
the original environment or a successful offline build. Dynamic editable/backend
requirements and exact installed versions still need the separate preparation gate.

The model metadata generator uses pickle.loads for output_slices. Those exact model
hashes are known, but their pickle semantics were not executed/approved. Synthetic
JIT warm-up/validation inside compilation and all other native actions also remain
unexecuted; do not confuse them with observed safe runtime behavior.

Host Ubuntu image/config digest, managed Python artifact, compiler/binutils/LLVM
and signed system-package snapshot remain null/unacquired. No complete build
closure, image seal, offline uv sync, resource sufficiency or native-build pass.

## Artifact locator, verification and replay limits

Acquired bytes are quarantined outside Git at
`/workspace/scratch/offline-native-inputs.8VplmB`, observed about1.17GB total versus
an8GiB acquisition envelope. This is ephemeral workspace storage, not a published
artifact repository or full-build capacity estimate. Git contains manifests only.
No acquired binary/source archive/key material is uploaded in this PR.

[Input manifest](evidence/offline_native_build_inputs.json) is
`offline-native-build-inputs-v1`, `seal_status=UNSEALED`, gate_a_status=BLOCKED.
It records all139 payloads, origins/hashes, source/tree/modes, models, backend
candidates, local Git stores and explicit unknowns. Archive files are not Git
history bundles or a prepopulated uv cache. Existing local Git stores retain
acquired commit/tag context; do not assume source tars alone satisfy a future
Git/SCM install. If the workspace disappears, reacquire by pinned origin/hash and
revalidate; do not claim the local locator is durable or fetch synthetic995….

Its content digest hashes sorted compact UTF-8 JSON excluding only content_digest,
rejecting NaN/Inf. The local locator is receipt context, so another acquisition
location creates a different acquisition receipt; the original path-independent
native registration/source identities are unchanged. Neither digest is authenticity,
safety approval, qualification or application authority.

Read-only reproduction on these acquired inputs, from the CyberPilot checkout:

```bash
GIT_NO_LAZY_FETCH=1 GIT_ALLOW_PROTOCOL='' git -C /workspace/scratch/offline-native-inputs.8VplmB/source.git fsck --full --strict
GIT_NO_LAZY_FETCH=1 python -m compatibility.friction_native.registration --reference-checkout /workspace/scratch/offline-native-inputs.8VplmB/source.git
```

Temporary operational scripts in the evidence store parse/hash archives, select
locked wheel tags or inspect AST text; none imports acquired code. Their generated
source-verification/static-audit/artifact-verification records support the report.
Three negative checks remove entries from temporary **manifest views**, not
physical source objects or SDK files; this is not an end-to-end uv/cache test.

uv export initially hit the read-only default cache and only-managed interpreter
requirement. The retry used task-specific UV_CACHE_DIR and the existing interpreter
only as an offline lock parser with --no-managed-python. No native environment was
installed or copied from CyberPilot. A binary-only pip download stopped at spidev;
direct immutable lock URLs then acquired all103 payloads with independent hashes.

Fresh regression/CI and independent exact-head review are recorded in the Draft PR
after they finish, not preclaimed here. Source acquisition success and green
regressions must not relabel gate A as eligible.

## Workflow ruling

Cloud skill script resources task-start/sdd-workspace were unavailable. A fresh
external task ledger and direct operational checks replace their bookkeeping;
cost: no helper automation, so explicit commands/status remain necessary. The
ledger is preserved with the acquired inputs because Task1 remains blocked.

## Retained gates and next SINGLE task

All candidate_generation_allowed, application_authorized, runtime_accepted and
owner_proposal_allowed remain false. q_observed remains null; no H7 source-policy
change, empirical bridge or runtime/schema producer qualification.

FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
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

No native source/Params/SubMaster/runtime/controller mutation, SCons invocation,
device/vehicle, native install/build, image/container, empirical qualification,
candidate/application/owner bridge, longitudinal behavior change, external AI
integration, deployment, upstream/native-fork PR, merge/rebase/force push or prior
PR modification.

Recommended next SINGLE task: design a CPU-only, no-device-capability containment
contract for the exact-R build preflight, explicitly resolving how constructor
probe attempts and denied accesses are handled without pretending that CPU
selection filters them. This safety boundary must be settled before image/build
execution or approval of the remaining transitive actions. No native patch or
next stage starts automatically.
