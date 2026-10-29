# H3 steering writer audit plan

Goal: establish whether pinned Carrot can satisfy PR #9 SteeringTarget, without
implementing or invoking any writer. Execution is inline audit/test work, then a
fresh independent read-only whole-branch review. The owner's H3 specification is
the scope and authorization; implementation/vehicle work is excluded.

## Pins and merge ledger

- PR #11 guarded merge/base: 66f4b79036560a11e7020af9cc214118dcbd4fba,
  merged_at 2026-10-29T02:14:04Z.
- Parents: dd1d4232f3d151fe9bbf0808c1fbe5131618b09a and
  ea79157035e9c92076f3996cb5f4b65dbd8832a8. Head ancestor and tree equality
  checks passed. All 12 exact-head checks passed before merge, review C0/I0/M0,
  no unresolved threads, no existing runtime/control-file change.
- Main equals that merge; branch audit/carrot-steering-writer-ownership.
- PR #8 e4361678ed176cbd7c0bb6f838d3daa7174caf22 and PR #9
  6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5 stay unchanged Draft/Open.
- Runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55; integration
  7a2f051b1f3847786318900444c88c2ba7a74a67, identical tree.
- Current upstream rechecked: f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3;
  no move from the supplied last observation. Hoya historical comparison:
  0e9c589c1b83027146f909a9cdc306c2c665ceaf.

## File scope and decisions

Only new docs/evidence and tests/audit files are allowed. No src, existing tests,
CI workflow, reference tree or preserved PR is edited. Existing pytest CI discovers
the new offline audit tests. Optional full-Git source validation runs explicitly
against local reference repositories; source code is never imported/executed.
The existing CI source job remains scoped to H2; it is not misreported as a full
H3 Git-object audit.

Deliverables: writer graph, ownership audit, unit equivalence, conflict matrix,
five architecture alternatives and PR #9 requirement mapping, with two JSON
manifests. Hashes are identities, never evidence of vehicle approval. No source
body is copied. No bounds/rates or physical effect claims are introduced.

## Review focus

1. Message publication is not effective controller acknowledgement/readback.
2. A sequence of assignments or a schema/cache version is not CAS/atomicity.
3. Full NN, NN fallback, NN-lite and brand callbacks must not be conflated.
4. Fitted perpendicular friction spread is not automatically normalized torque.
5. A synchronous owner cannot recover a frozen control process by itself.

## Work items

- [x] Recheck and merge PR #11; preserve source/history/PR #8/#9 pins.
- [x] Read PR #9 ports/contracts/coordinator and both application documents;
  extract a complete acceptance matrix from actual code, not a design label.
- [x] Trace runtime/current torqued lifecycle, live fields, controller sampling,
  custom/NN/brand alternatives, schemas, model drift and Hoya comparison.
  Create independently worded exact-line/blob/range evidence.
- [x] Define field-by-field units, confidence and gaps. Separate numeric software
  forwarding, dimensional interpretation and qualified identification.
- [x] Compare conflicts/readback/CAS/rollback/watchdog alternatives; recommend
  exactly one architecture and map all PR #9 requirements without implementation.
- [x] RED/GREEN audit tests and source validator: pin/hash mutation, AST semantic
  witnesses, inventory/matrix completeness and unchanged production/goldens.
- [ ] Full regression, source validators, lint/format/type/build and fresh wheels.
  Push append-only commits, create Draft PR, fresh review and exact-head CI.

No next task is automatically started. Runtime fingerprint, vehicle application
bounds and scientific parameter-identification qualification remain unresolved.

## Local audit verification

- Post-merge H2 baseline: 843 tests passed before adding H3 evidence/tests.
- RED/GREEN: missing validator, coefficient transform witness and NN branch
  witness; mutation cases deny incorrect pins/hashes/units/authority/readback.
- H3 audit tests: 26 passed. Full base suite: 869 passed.
- Native optional schema regression: 1006 passed, 0 failed/skipped. Overall
  coverage 98.93%; knowledge 99.71% (branch-only 100%), safety/pure contract 100%.
- Explicit full source validator: 55 files / 93 claims / 3 fields / 16 PR9
  requirements. H2 39/78/27 source validator and H1 structural audit also pass.
- Ruff/format and strict mypy pass, with no production source change. Final
  build/fresh-wheel, independent review and remote CI outcomes are recorded
  in the Draft PR/final report after the audit commits.
