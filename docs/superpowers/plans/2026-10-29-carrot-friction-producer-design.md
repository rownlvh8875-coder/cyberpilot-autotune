# Carrot Friction Producer Patch Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline for this design/audit plan. No native implementation. Steps use checkboxes; a fresh builder check and one final whole-branch review are the only delegated work.

**Goal:** Produce source-pinned native patch design, field mapping and an offline
audit, preserving every H7 production/contract/test/evidence file.
**Architecture:** Approved H7 capture A, passive legacy-preserving diagnostic
producer blueprint; independent q remains unavailable, no C*q rewrite.
**Tech Stack:** existing Python3.12/dev/research tools, Git object reads, JSON/AST;
no dependencies or native runtime imported.
**Spec:** docs/superpowers/specs/2026-10-29-carrot-friction-producer-design.md.

## Global Constraints

- Design base 5357d5d555d49b258affa237d83b8491b8a8c6ce; H7 PR16 unmerged/unchanged.
- R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55 primary blueprint, C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 comparative, not device fingerprint.
- No src/, native schema/controller/Params/producer, H6 estimator or PR8/9 edits.
- No vehicle/real data/application/longitudinal/external AI/upstream PR.
- Preserve all H7 tracked bytes except exact additive CI hooks; no old test relaxation.
- q_observed None; all authority absent/fixed false; runtime/empirical blockers kept.

## Review Focus

1. Parallel/reconstructed q mislabeled operational HELPER_OBSERVED.
2. Numeric parity confused with timing/transport/vehicle noninterference.
3. Post-publish CC or latest SubMaster state substituted for consumed state.
4. Wire absence/default/unknown silently decoded as zero, false or LINEAR.
5. Instrumented source given old R/C SHA to bypass source-profile registration.

## Task 1 — freeze design and builder check

Files: this plan and the spec. Interfaces: fixed H7 base/R/C pins and passive-q
decision feed all later design/audit artifacts.
- [x] Inspect H7/source/environment, baseline1416 passed, PR16 exact12CI success.
- [x] Explain passive vs C*q vs diagnostic-laundering alternatives and scope.
- [x] Commit these two documents before audit implementation; fresh builder check.
Expected: first design commit only these docs; no native/source changes.

## Task 2 — reproducible source and wire/proof manifests

Create tests/audit/test_carrot_friction_patch_design.py (RED first), then
tests/audit/validate_carrot_friction_patch_design.py; evidence files
docs/evidence/carrot_friction_patch_{sources,wire,math}.json.
Interfaces: build_sources(reference: Path)->dict, build_wire()->dict,
build_math(reference: Path)->dict, validate_sources(data,reference=None)->None,
validate_wire(data)->None, validate_math(data,reference=None)->None,
verify_history()->dict; CLI --reference-checkout/--verify-history.
- [x] RED tests for absent artifacts, authority/q-laundering/source/schema mutation.
- [x] Build source file/blob/symbol/range hashes for R/C helper/PID/controller/
  controlsd/schema/services/messaging and H7 acceptance basis; no native imports.
- [x] Map all144 semantic fields:134 wire fields/10 evaluator-local fields;
  proposed reserved slot/type IDs, explicit optional wrappers and unknown enums.
- [x] Pin40 synthetic helper cases/profile; count bit and numeric mismatches
  separately, no empirical/vehicle relevance claim; source extraction only.
- [x] Test preservation of all base files and exact additive CI hooks; run GREEN.
Expected: source/wire/proof reproducible; full baseline regressions remain green.

## Task 3 — builder-ready future native plan and result

Create docs/carrot_friction_producer_implementation_plan.md and
docs/carrot_friction_producer_design_result.md. Future native plan specifies file/
symbol interfaces and test-first tasks but is explicitly NOT executed this turn.
- [x] Cover source/local/cycle capture, raw/PID taps, mode/geometry/delay partials,
  model dependency, CC mutation, schema presence/evolution, source registration,
  disabled/failure parity, synchronous transport gate and all retained blockers.
- [x] Resolve builder questions from source or ledgered conservative design choices.
Expected: no hidden authority/implementation claim; one next task only, not started.

## Task 4 — verify, review and publish design-only Draft PR

Modify .github/workflows/ci.yml by additive design-audit/source-warm hooks only.
- [x] Full pytest, lint/format/mypy, all H2-H7 audits/goldens, coverage/build/wheel.
- [ ] Commit final result; fresh whole-branch review on exact head.
- [ ] Publish stacked Draft PR against feat/friction-observability-receipt;
  attach PR, verify exact-head push/PR CI; do not merge PR16 or the new PR.
Expected: clean tree, all tests/CI green; scoped design review, not runtime approval.

## Ledger / rulings

Pre-flight: Task1's pins/passive scope constrain Task2 manifests; Task2 schema/proof
inventory constrains Task3 native plan; Task4 checks all artifacts without native code.

Ruling: user's all-approval delegates details of the already recommended design
task, not native implementation or merges — preserves explicit task boundary — cost:
an additional approval remains necessary to implement/activate any producer.
Ruling: keep H7 Draft PR unchanged and stack design work on its exact head — no
inferred merge authority — cost: PR dependency until H7 is separately merged.
Ruling: select passive q=None, reject bit-changing C*q as read-only — source proof
shows rounding differences — cost: full friction observability remains blocked.
Ruling: existing dedicated checkout and tracked ledger substitute for unavailable
remote skill shell scripts — no extra worktree or invented executable paths — cost:
manual bookkeeping, mitigated by commits and preservation checks.

Progress: Task1 freeze115fd98534eed0f39e4017e0d72fafbb662fc71d precedes code;
fresh read-only builder check: nothing important left, no questions/findings.
Task2 initial RED17failed/1passed (existing passive-q rejection characterization);
GREEN19passed including a separate record-name/primitive-substring regression.
Source audit:32 files,144 semantics,292 H7 base files preserved except exact
additive CI hooks; synthetic40/profile,19bit/16numeric differences each. This is
an offline design audit, not native producer or timing qualification.
Existing setup needs no new config/dependencies/services. Task3 complete as an
explicitly unexecuted native implementation plan and design result. Full1435pass,
coverage98.52%, H7 843statements/276branches100%/100%, lint/format/mypy/build/wheel
and all pinned source/golden audits pass. Final review/publication/CI gates are
recorded in the Draft PR's final-verification section after the final commit, so
they do not cause a self-referential SHA or post-review code change in this ledger.
