# ENTRY compatibility pure-core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement the pure supplied-object ENTRY checker and mutation tests,with semantic R and an explicitly incomplete Q preparation packet.

**Architecture:** Audit-only frozen values and exact Git-object/tree/registration checks. No Git reader or historical executor is implemented in this slice,so even a structural match remains UNAVAILABLE/BLOCKED. Exploratory local implementation commits are not registered integration I commits.

**Tech Stack:** Python3.12.3–3.12.x,stdlib only core,pytest,Ruff,strict mypy.

**Spec:** docs/superpowers/specs/2026-11-02-audit-compatibility-design.md.

## Global Constraints

- Base D=75e00280a09323ad4a3fc82453383f220c92f6c6,branch feat/audit-compatibility-entry-core.
- R is the first commit and only adds the five declared semantic metadata files.
- Existing src/,tests,manifests,CI,goldens,PR8/9/16–58 and main are unchanged.
- Pure audit namespace tests/audit_compatibility/,no application/estimator/observer bridge.
- All9permissionsfalse;no historical replay or current index/worktree/attribute capture is fabricated.
- No push,PR creation,actual O merge,Q/I qualification or STACK adoption in this task.
- Q draft is incomplete postimage preparation only;actual Q must later be a sibling of exploratory commits with sole parent R. No force-push/rebase is needed.
- Existing coverage floors unchanged;new core statement>=98%,branch>=95%.

## Review Focus

- A matching supplied tree must not imply historical execution or current worktree observation.
- A well-formed Q with an extra active file must fail whole registration delta validation.
- Nested tree ordering/file-directory collisions must agree with Git,not a JSON-only digest.
- A known contradiction must survive another unavailable source.
- Prototype commits or draft postimages must not qualify as actual Q/I or authority.

### Task 1: Immutable object boundaries

Files:tests/audit_compatibility/{__init__,contracts,git_objects}.py;
tests/test_audit_compatibility_objects.py.
Interfaces:GitImage(mode,data);TreeSnapshot(entries);CommitObject(raw);
PinnedCompatibilityManifest(r,m,d,o,semantic_path,semantic_paths,active_paths,manifest_path,inert_root);
CompatibilityInputBundle(commits,trees,candidate_head,validation_head,declared_base).

- [ ] Write missing-module RED and literal Git object/tree,immutability/path/type cases.
- [ ] Implement immutable values,raw SHA1 object framing,nested tree SHA1,raw commit parsing.
- [ ] Compare with actual Git hash-object/mktree in a temporary test-only repository.
- [ ] Run targeted and full pytest;expected pass,then commit.

### Task 2: Pure ENTRY content checks

Files:tests/audit_compatibility/{schema,validation}.py;
tests/fixtures/audit_compatibility_core.py;tests/test_audit_compatibility_validation.py.
Interfaces:assess_compatibility(bundle,manifest)->AuditCompatibilityDecision;
decision REJECTED if known invalid,otherwise UNAVAILABLE;
structural_content_status separate from final decision;all false facets fixed.

- [ ] Write complete synthetic R/Q/I object fixture;RED missing assessor.
- [ ] Check source ancestry,raw commit/tree identities,R/Q closed deltas,canonical schemas,rows/preimages/inert blobs,three-way selection/full current tree and virtual merge identity.
- [ ] Test invalid known fields plus missing peers,no permission flags can be supplied.
- [ ] Run full pytest,lint/type and commit exploratory implementation;not I.

### Task 3: Adversarial coverage and Q preparation

Files:tests/test_audit_compatibility_adversarial.py;
tests/test_audit_compatibility_architecture.py;external Q draft/evidence.
Consumes Task1 objects and Task2 assessor.

- [ ] Add missing/extra/mutated/path/case/order/foreign-type/canonical JSON negative tests and prepared first-call effect checks.
- [ ] Run whole-project suite,new branch+statement coverage,existing source/history auditors,replay,build and fresh wheel.
- [ ] Prepare only actual implemented audit/test postimage hashes,mark omitted integration rows/IO components UNAVAILABLE;do not create actual Q or I.
- [ ] Commit final local code,freeze exact head and request fresh whole-branch independent review. Preserve worktree/evidence and report one next task. No remote publication.
