# H2 steering knowledge implementation plan and ledger

Execution: inline TDD, then one fresh independent whole-branch review. Scope is
the owner's H2 specification, 2026-10-29: steering-only descriptive knowledge.
No observer, supervisor, recommendation, application or vehicle execution.

## Pinned basis

- PR #10 guarded merge: dd1d4232f3d151fe9bbf0808c1fbe5131618b09a,
  merged_at 2026-10-29T01:11:52Z.
- Parents: b24ef18e4270af5ab4f731aca31cf95f4f4b0cce and
  8a3f6f5bfb35021e20dc5730f6650f12d53d571d; two parents, ancestor exit 0,
  merge/head tree diff exit 0. Main equals the merge SHA.
- Branch: feat/steering-parameter-knowledge, created at that merge.
- Historical Hoya: 0e9c589c1b83027146f909a9cdc306c2c665ceaf.
- Runtime source: c2130730239bcdb4cbde9361ab90c8d99aa4ff55;
  integration 7a2f051b1f3847786318900444c88c2ba7a74a67.
- Current upstream: f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3, unchanged at start.
- PR #8/#9 remain frozen at e4361678ed176cbd7c0bb6f838d3daa7174caf22 /
  6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5. No reference branch is edited.

## Architecture and rulings

- `knowledge/contracts.py`: frozen versioned parameter/source descriptors, strict
  enums and immutable registry. No application types or dependencies.
- `knowledge/canonical.py`: finite canonical JSON identity, with exact integer/
  float representation preserved. Hashes are identities, never signatures.
- `knowledge/steering.py`: explicit exact-revision selection, no latest/default
  source fallback. `get_any` is diagnostic; `get_proven` excludes unresolved data.
- A static data module holds independently described source claims/catalogs;
  import reads no JSON/file/network and imports no openpilot component.
- Ruling: one nine-entry catalog per exact revision, not a blended catalog.
  Each registry binds its descriptors to source claims from that same revision.
- Ruling: software gain coefficients are described as software coefficients,
  without inventing physical dimensions or universal controller effect.
  Factor/friction global unit equivalence and offset canonical unit remain
  explicitly unresolved where not proven; known storage scaling is still recorded.
- Ruling: `liveTorqueParameters.latAccelOffset` is a logical catalog ID. Actual
  consumed wire field is `latAccelOffsetFiltered`; never invent an unfiltered
  wire member or use the producer's seed zero as an available/default baseline.
- Ruling: Hoya's MEB ratio bypass differs from c213/current upstream. New upstream
  VM geometry also prevents broad physical-effect equivalence claims.
- Ruling: preserve H1's frozen original-file hashes and original manifest; its
  whole-source assertion will permit only this expressly authorized new knowledge
  namespace, with separate H2 boundary tests. No historical source pin is rewritten.

## Tasks and verification

- [x] Recheck PR #10 metadata, all 10 checks, empty review threads/reviews and
  runtime diff; Ready and guarded merge, verify provenance. Baseline tests follow.
- [x] Trace nine parameters at all three source revisions: catalog/key definitions,
  typed settings writer, torque/NN/custom/live paths, VM/delay and estimator/schema.
  Record hashes/ranges, descriptive defaults and exclusions; no source bodies copied.
- [x] RED/GREEN canonical and frozen contracts: unknown scale/mode, numeric zero,
  nonfinite values, bad confidence, missing proof fields, mutable input and digest.
- [x] RED/GREEN exact-revision immutable catalogs: duplicate IDs/storage keys,
  cross-revision/dangling claims, source drift and proven-versus-diagnostic queries.
- [x] Property/adversarial/architecture/source-validation tests. Preserve all old
  source/goldens, no authority conversion, IO/network/time/threads/processes.
- [x] Docs and evidence matrices, including PR #9 policy/evidence/owner separation.
- [x] Full regression, >=90% source coverage, >=95% knowledge branch coverage,
  lint/format/mypy/build/fresh wheel and exact-source audit checks.
- [ ] Append-only commits/push, Draft PR, fresh independent review, corrections
  as needed and exact-head CI. No merge of this development PR or next task.

Review focus: stale source pin, invented unit equivalence, UI/default authority,
misleading offset alias/default, and controller-mode/ownership overclaims.

## Local verification ledger

- RED/GREEN: 48 missing-contract tests, UI-unit separation, source manifest
  validator, mode live-gate linkage, offset linear non-use and CP-constructor
  provenance linkage. Each failed before the corresponding implementation/data.
- Windows Python 3.12.14: 841 passed; overall branch-inclusive coverage 97.21%.
- Linux Python 3.12.3 / actual pycapnp 2.1.0: 978 passed, 0 failed/skipped;
  overall 98.93%; knowledge 99.71% (branch-only 100%), pure receipt/safety 100%.
- Separate coverage files are required when Windows/Linux checks share a checkout.
  A first concurrent local report mixed path names; a fresh isolated native
  coverage run removed the reporting warnings and confirmed these percentages.
- Ruff/format, strict mypy (45 source files), wheel/sdist build passed.
- Fresh base wheel: 44 importable submodules, three knowledge profiles,
  typed missing-openpilot error and four unchanged replay goldens.
- Fresh optional wheel: actual-schema mapping and four Hyundai False/True
  extraction cases; no runtime service/hardware/real log used.
- Offline source validator: 39 files / 78 source claims / 27 descriptors,
  all source bytes/blob/range hashes plus UI/native defaults verified.
- Exact-head review and remote CI results are recorded in the Draft PR/final
  report after these commits; no development PR Ready/merge is authorized.
