# Copy Reference/Publication Source Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax for tracking.

**Goal:** Freeze replayable conditional source arguments and remaining gaps for PR45's copy-local reference and raw tag publication.

**Architecture:** Immutable closed static catalog plus source-byte verifier;new
source/result manifests and human argument maps. No actual record admission or
producer mutation. Existing source assets are read-only.

**Tech Stack:** Python3.12,pytest,JSON/SHA256,read-only exact Linux source.

**Spec:** docs/superpowers/specs/2026-10-31-copy-reference-publication-design.md

## Global Constraints

- Base5581049957088b348498eb5ef0b1061f76d19b7c;preserve all old blobs/assets/PRs/main.
- STATIC_SOURCE_AUDIT_ONLY/BLOCKED;all9permissionsfalse,proofsfalse,globalcountsNone.
- No source/producer/decoder/minor fix,no new kernel/producer build or guest/device/vehicle/host/compiler-based type probe;ordinary unchanged regression/native-unit/Python-wheel tooling remains in scope.
- No actual-record parser/runner/synthetic-estimator/application adapter dependency.
- Six dimensions and four type flows exactly as spec;no automatic proof/admission.
- Only new namespace/evidence/docs and two narrow attribute additions.

## Review Focus

- get_file relaxed increment mistaken for valid-pointer/acquire proof: test immutable false source-binding/publication flags.
- RCU publication confused with later seed writes or another namespace lock: freeze separate conditional arguments and missing writer/alias closure obligations.
- Object u64 epoch conflated with unsigned-int saved/probe/wire domain: reject altered type-flow records;document narrowing without claiming actual corruption.
- Embedded excerpt byte checks mistaken for external source or semantic proof: test optional-root flags,source drift and fixed false semantic-proof flag.
- Passing source audit mistaken for actual/synthetic/application evidence: test no-authority and preserved old blobs/import boundaries.

---

### Task1: Closed source catalog,verifier and type-flow result

**Files:** tests/copy_reference_audit/{__init__,model,audit}.py;
tests/test_copy_reference_publication_audit.py;
tests/architecture/test_copy_reference_publication_boundary.py;
docs/evidence/copy_reference_publication_{sources,result}.json;.gitattributes.

**Interfaces:** assess(rows:Any,flows:Any,available_claims:frozenset[str])->ReferenceAudit;
validate_sources(data:Any,source_root:Path|None=None)->frozenset[str];
validate_result(data:Any,claims:frozenset[str])->ReferenceAudit;
validate(source_root:Path|None=None)->dict[str,Any].

- [x] Write failing tests with independent literal dimension/type-flow expectations,malformed catalogs,source drift,immutable defensive copies and false authority.
- [x] Run `.venv/bin/python -m pytest tests/test_copy_reference_publication_audit.py -q`;expect missingAPI RED.
- [x] Freeze exact selected source excerpts and repository refs,then implement pure closed result and read-only byte audit.
- [x] Add old-blob/import guards;run focused tests,explicit source-root audit,full pytest,ruff/format/mypy;expect PASS with source_interpretations_machine_proven=false.
- [x] Commit `audit: freeze copy reference and tag publication source boundaries`.

### Task2: Argument maps,representation finding and verified handoff

**Files:** docs/copy_reference_publication_audit.md;
docs/copy_reference_publication_result.md;plan progress.

**Interfaces:** Consumes Task1 validated citation IDs,source digest,dimensions,
type flows,conditional arguments and obligations. No new runtime interface.

- [x] Write caller/slot/ref/transfer and pre-install/seed/lock argument maps with exact claim references and explicit conditional premises.
- [x] Write object→saved→buffer→printf→decoder type table and stand-in probe limitation;retain actual bytes and prior minor status unchanged.
- [x] Run full suite,old source/history/original-byte audits,native192/replay4,lint/format/type/build/fresh wheel and pure-module coverage;expect PASS,not semantic qualification.
- [ ] Commit `docs: publish conditional copy reference and publication audit`.
- [ ] Verify final exact-head/full and fresh persistent CRLF clone;expect clean/PASS. Fresh whole-branch read-only reviewer;one author RED→GREEN C/I fix pass if needed,minors defer,no re-review.
- [ ] Publish own stacked Draft against PR45 branch,attach it,verify exact-head push/PR CI and old32PR/main preservation. Recoverably archive only this plan;recommend one next task without starting it.

## Self-review

Task1 identifiers/result feed Task2 docs;source/catalog hashes are byte identity
only. All five review-focus cases belong to Task1 tests or Task2 source argument
review. No runtime patch or data bridge is hidden in the plan. Source interpretation
is explicitly human-reviewed,not proven by Python hashes or catalog validation.
