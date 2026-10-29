# H1 selective architecture audit plan

> Execution: inline read-only source audit and documentation, followed by one
> fresh independent full-diff reviewer. No product implementation is authorized.

**Goal:** Decide what Hoya concepts are useful without granting advisory output
application authority or changing current CyberPilot behavior.

**Spec:** The owner's H1 request, 2026-10-29. Deliverable paths and scope follow
that request. Architecture choices in the two design documents are proposals;
their completion does not authorize implementation.

**Architecture:** Pin Git objects outside this checkout, inspect actual producers
and consumers, record hashes/ranges and separate proven behavior from heuristics.
Offline audit validators check evidence consistency and source integrity; they
never import or execute the reference implementation.

**Tech stack:** English Markdown/JSON, standard-library Python audit tools, pytest.

## Constraints

- Base b24ef18e4270af5ab4f731aca31cf95f4f4b0cce; branch audit/hoya-c3-atune-adoption.
- Preserve PR #8 e4361678ed176cbd7c0bb6f838d3daa7174caf22 and PR #9
  6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5, Open/Draft/unmerged.
- No src, engine, learner, application, longitudinal, persistence or Params edits.
- No copied reference source bodies, real logs, vehicle execution or AI API calls.
- Draft audit PR only; no merge, upstream PR or automatic follow-up development.

## Review focus

- A source hash alone does not prove a claim: include symbol/range and confidence.
- Missing/default values and disjoint log segments must not become causal evidence.
- Driver intervention is observed; dissatisfaction is an unverified inference.
- UI ranges, snippets, numeric rules and LLM outputs confer no application authority.
- Deferred longitudinal concepts must not turn into runtime scope or readiness.

## Tasks

- [x] Verify base, preserved PR heads, clean isolated worktree and baseline tests.
- [x] Pin Hoya, original feature commit, current carrot-wip and divergence.
- [x] Audit extractor, eight episode predicates, all named recommendation keys,
  providers/privacy, actual consumer paths, snippet accuracy and Apply/rollback.
- [x] Write source/features manifests, adoption matrix and the two proposed designs.
- [x] RED/GREEN audit validation: malformed pins/ranges, dangling claims, unsafe
  authority decisions, unclassified keys, missing/default inventory and mutation.
- [x] Verify exact source blobs/ranges using a local reference only; run complete
  regression/lint/format/types/build and confirm old goldens/src unchanged.
- [ ] Append-only commits, fresh independent review, corrections if necessary,
  Draft PR/push CI and final Korean report. Stop without starting the next task.

Baseline: 738 tests passed, zero failed/skipped. Hoya stayed at 0e9c589; current
carrot-wip moved from bfc3ebb to f5e4f8b. Full evidence is recorded in the audit.

## Local verification checkpoint

- RED: 11 missing-validator/evidence tests failed before implementation. A further
  unsafe-adoption mutation failed before the validator rejected that promotion.
- Audit tests after source-range review corrections: 22 passed. Full Windows
  Python 3.12.14 suite: 760 passed.
- Linux Python 3.12.3 / actual pycapnp 2.1.0 combined suite: 897 passed.
  All runs have zero failures/skips. Native source branch-inclusive coverage:
  overall 98.82%, pure receipt contract and safety 100%.
- Ruff check/format, strict mypy (40 unchanged source files), wheel/sdist build
  and all four historical replay goldens passed.
- `python -m tests.audit.validate_hoya_c3_atune --reference-checkout <local-ref>`
  verified 40 raw Git blobs, 104 ranges, Python/JS exception inventory, all 35
  catalog-present named UI values and 19 snippet comparisons. No reference module,
  log or provider was executed.
- Wheel inspection excludes audit/tests and unmerged application/sidecar modules;
  both evidence JSON files in the sdist are byte-identical to the checkout.
- Frozen source/golden byte hashes match main. PR #8/#9 remain unchanged refs.

Final independent review and remote CI are recorded on the Draft audit PR after
the reviewed commit exists; this checkpoint does not predeclare those results.
The first review at ded12bd reported C0/I0/M1: per-key unit descriptions reused
alternatives. Each was resolved against its consumer. The append-only correction
also adds 35 individually hashed catalog ranges and RED/GREEN source-value checks.
