# NR-M1 offline registration Unicode reference-path result

NR_M1_UNICODE_REFERENCE_PATH_FIXED

The offline registration tool now preserves Unicode when passing a C-quoted
alternate object path to Git. The only existing-code change is
`json.dumps(original_objects, ensure_ascii=False)`. No native source, patch,
schema, installed package, old tests, CI, registry policy or evidence is changed.

Base PR20: feac824124966940d6ec2c541127f466b0c5221b.
Branch: fix/native-registration-unicode-paths, stacked Draft PR against PR20.

## Reproduction and root cause

Before the fix, Python JSON's default ASCII encoding replaced Korean, accented,
CJK and emoji characters with `\u` escapes. Git expects C-quoted alternate paths,
not JSON Unicode escape syntax, and reports "unable to normalize alternate object
path". This happens at the actual Git object-lookup boundary, before tree rebuild.
CLI consequently returned1; ASCII-space input already worked.

Eight actual-Git regression cases observed RED7/ASCII1 pass -> GREEN8:

- ASCII space, Korean space, accented Latin, CJK, emoji/space, combining accents.
- Two CLI cases with both non-ASCII reference and Unicode temporary-overlay parent.

References are physical temporary bare Git directories, not symlinks that
Path.resolve could collapse to ASCII. An alternates FILE points to the existing
read-only warmed native object cache; the code under test must consume the new
Unicode objects directory through its ENV path. No mock encoder or duplicate
registration implementation substitutes for prepare/main. Reference and backing
file size/mtime snapshots remain unchanged. Temporary overlay objects are cleaned
up. No copy of the native tree, native branch, service or device is created.

Existing quote/ASCII whitespace handling is retained; this is not a filename
normalization feature or a universal claim about every platform/filesystem/path.
Source-backed Unicode cases ran on Linux (also the mandatory hosted source job).
Normal Windows CI does not constitute full Windows-native path qualification.

## Identity and authority preserved

Every Unicode case produces the EXACT complete committed record, not only equal
tree/hash fields. Input location is not added to content identity or provenance.
No normalization, digest/schema/version change or source allowlist extension.

- Native R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55.
- C/carrot-wip re-read unchanged: f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
- Patch SHA-256:8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac.
- Applied tree:6185197d6f334f745a9c082519013b8fe0376f65.
- Offline synthetic revision:9957868acc7459f515f1b79e9315cf93a878d933.
- source_schema_digest remains exact applied log.capnp SHA-256; separate schema
  closure digest and every other record field stay unchanged.

q_observed remains null, all candidate/application/runtime/owner flags false,
runtime/empirical qualification and native publication/deployment false. H7 still
rejects the instrumented revision/schema pair. This portability fix grants no
source/device/runtime/estimator/application authority.

## Verification

New regression8 pass; mandatory native192 pass/no skips; core1494 pass. Existing
source/schema/patch/registration/history gates, H2–H7/design audits, lint/format/
mypy71 files, build/fresh wheel70 neutral imports, H7/H6 source hashes, replay11/
four fixture digests and knowledge/owner/science/research smokes pass. Installed
source coverage remains98.52%, H7 remains100% statements/branches. No new package,
dependency, setup or environment-configuration change is needed.

Final exact-head independent review and hosted push/PR CI are recorded in the new
Draft PR rather than by rewriting the reviewed head. Existing PR8/9/16/17/18/19/20
and main are preserved; no merge/rebase/force push or upstream/native-fork PR.

## Retained gates and next single task

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

No vehicle, real Params/SubMaster, runtime producer activation, empirical data,
candidate generation, application/owner bridge, longitudinal or external AI.

Recommended next SINGLE task: prepare an offline full-native-build verification
plan for exact R plus the preserved patch. Unlike schema/body-level tests, a full
native build has not been demonstrated; first identify target/toolchain/dependency
and reproducibility gates without assuming a device fingerprint or deploying.
This recommends planning only, not starting a build/runtime/vehicle task. No
automatic next task is started.
