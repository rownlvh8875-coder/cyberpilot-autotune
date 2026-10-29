# Offline native friction source/schema registration

## Intent and boundary

Continue the single next task recommended by PR18: prepare and review the exact
native applied revision and its source/schema registration offline. This is an
offline content record, NOT an observation-policy allowlist entry, native fork
commit/push, device fingerprint, runtime qualification or deployment. User said
all next work approved and then proceed; do not repeat design questions.

CyberPilot base: 0d1d44c808050835aa5a52c3ddd76d51cb3300b0 (PR18).
Native base R: c2130730239bcdb4cbde9361ab90c8d99aa4ff55, root tree
ffb213d9fdc0f9618264822bd2a4e26263abfe74. Comparative C/carrot-wip remains
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3; no promotion/port/fingerprint.

## Approaches (implementer's choice)

1. File hashes only: cheap, but cannot identify the complete applied native tree.
2. **Selected:** reconstruct the seven-file patch in an ephemeral Git object
   overlay, retain all unchanged base entries and create a deterministic synthetic
   single-parent commit object. Verify parent, full tree and exact changed paths.
   No branch/ref/worktree/remote configuration or persistent native objects.
3. Commit/push in a native checkout: creates external native state and suggests
   deployment intent; outside this offline task.

Use existing Python/Git tooling, stdlib only, repository-only files. No change to
PR18 assets, installed src/, old tests/manifests, CI, controller math or schemas.

## Content record and semantics

Record native parent/base tree/applied tree/synthetic commit payload and SHA,
patch/helper/semantic-wire hashes, seven file modes/blob IDs/SHA-256 and all five
schema files in the transitive import closure. Preserve source_schema_digest's
existing meaning: SHA-256 of applied log.capnp bytes. Record a separate canonical
schema closure digest; do not silently redefine the receipt field. Canonical
encoding is sorted compact UTF-8 JSON with NaN/Inf rejected.

Commit identity/time are fixed synthetic recipe metadata, not the user's identity,
review time, signature or claim of origin. SHA/content digests confer no authority.
The complete tree references untouched base objects: this is not a standalone
Git bundle, all-blob availability test or deployable distribution.

Verify source and target hashes against frozen PR18 evidence, exact seven-path
diff, source git object format and R commit object, old/new schema compatibility
through existing mandatory native suite. Do not lazily fetch or write reference
objects/refs/config; use temporary object storage with read-only base alternates.
Wrong/missing source, schema drift, unexpected path/mode, altered record or true
permission must reject. CLI verifies committed evidence; it cannot enable a
producer or update H7's policy. No registration-to-receipt/estimator bridge.

## Acceptance and non-goals

Reproducible full native tree/commit identity, explicit schema digest semantics,
tamper rejection, reference unchanged, old H7 policy rejects the new revision,
all runtime/application/candidate/owner permissions false. Pure neutral wheel
remains unchanged. Full native/C++ build, hardware, real SubMaster/Params, timing,
transport, missing q, cohort completeness and empirical/application qualification
remain blocked. PR18's custom-selector/frame10 test gap remains deferred.

Author calls above are recorded as such, not attributed to the user. The user's
proceed instruction opts out of another questions/design approval round.
