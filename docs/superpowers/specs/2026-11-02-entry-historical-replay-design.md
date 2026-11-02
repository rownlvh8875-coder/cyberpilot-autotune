# ENTRY historical source-audit replay contract — H1 design

## 1. Intent and honest status

Define how future H can replay original source/history checks at exact O and D
cohorts without modifying their bytes,borrowing current imports,or relabelling an
old pass as current compatibility. This commit adds design/metadata/plan only.
It implements no executor,does not run H,and is NOT formal ENTRY R,Q,I or R'.
The user delegated routine engineering choices;the choices below are the
author's calls,not new application authority. No repeated permission handoff is
needed to finish this design. Actual execution/integration is a different task.

Base C1:16ccf73b9956d6f5c29e34b174133046c0d54fdb.
Profile:ENTRY_HISTORICAL_SOURCE_AUDIT_V1. Status BLOCKED;all9permissions false;
integrated_admission=false;source_capture_atomicity=NOT_ESTABLISHED.
HISTORICAL_REPLAY remains UNAVAILABLE. A design or structurally matching record
does not change that. D01–D04 and all existing project blockers stay open.

## 2. Approaches and size

| Approach | Result / cost |
|---|---|
| Substitute D's current helper or waive old checks | Rejected:loses O provenance and weakens original negatives. |
| Run all historical CI scripts unchanged | Rejected for this slice:install/build/network and broader execution effects exceed source-audit scope. Existing definitive integration gates are not waived. |
| Closed source-audit/test commands in separately prepared O/D snapshots | Selected:explicit cohorts,origins,scratch and reports;requires a later qualified execution boundary. |

This is a contract-sized project. The next buildable slice is a pure record and
policy consistency gate;an I/O runner is deliberately not part of its plan.
A fresh builder checks this design before handoff. It is not a code/safety review.

## 3. Source cohorts and exact identities

| Cohort | Revision | Tree | H6 audit SHA256 |
|---|---|---|---|
| O | 5357d5d555d49b258affa237d83b8491b8a8c6ce | 18e63fc8e03077684cd14c1ed33e2c7a8ceb89a5 | aa27d15517e693b0288ed37893deae4515a7c1f88388bb29e871c9fe0e68d032 |
| D | 75e00280a09323ad4a3fc82453383f220c92f6c6 | d0dd929f3bb46d1a33d8bb00f29e7638b48d9483 | eaddb6091b5054613ec8e7f0eb15cae9b64aa3d1d8f4e1205c688b89f1947efe |

sources.json fixes original parents,53 navigational file anchors with raw blob/
SHA256/length and the literal15O/16D pytest-file sets. The whole tree,not just
anchors,pins every helper,fixture,manifest,attribute and source file. No filtered
changed-set,patched ROOT,postimage substitution,alias module or current helper.
Full ancestry/raw object closure required by original history checks must be
prepared locally with its own exact HEAD/index;missing is not known absence.

O has no root .gitattributes;D uses exact raw SHA256
3da824d0f37be4082aecb38cef9b01c8f0b9e66ab67d574cfbe3b2e3553db908.
C1's fixed D-attribute profile deliberately rejects O. Do not edit C1,strip O
attributes,or call C1 stable for O. H needs its own separately registered source
snapshot policy preserving O's known absence and D's exact bytes.

S and P/P2/P3/P4/P5 STACK policies are excluded,not passed. Future STACK needs
its own full loader closure,effect classification and approval;no sentinel-only
substitute or inherited ENTRY grant. Original registration documents remain exact.

## 4. Case identity,not a convenient count

The D diagnostic tree currently contains499nodes:476original portable behavior
nodes,7coverage-gate negatives and16integration nodes. All499 remain mandatory.
case_inventory.json contains exact sorted nodes and raw canonical-array digests.
Only the two literal extra files test_coverage_gate.py and test_integration.py
are excluded to derive the ORIGINAL476 set;they are never excluded from D replay.
The56AR mapping rows are scenario labels,not the476case inventory.

These node identities came from CURRENT collection under Python3.12.14 after
proving all diagnostic/fixture files byte-identical to D. This is design input,
NOT collection or execution at historical D. It does not prove original command
outcomes. The full O inventory and D's four additional audit-file nodeids are
not collected here. Their expected exact node sets must be separately prepared,
reviewed and content-frozen before any real H execution. A runner may not learn
its expected set from the same run it is deciding to accept. null means unavailable.

Each future case records exact nodeid plus setup/call/teardown outcomes. Missing,
extra,duplicate,renamed,deselected,skipped,xfail and xpass mandatory nodes cannot
be converted into a pass. A collection-only result has no executed outcomes.
No new test-count,excitation,scientific or timing safety threshold is invented.

## 5. Closed command registry

semantics.json is the authoritative six-command argv registry. Parameters such
as <RUN_OUTPUT> are typed bound paths,not shell expansions or caller fragments.
One fresh child per command;no shared interpreter/sys.modules,even within a cohort.

| ID | Entrypoint | Required work |
|---|---|---|
| O-PYTEST | pytest.main | All15literal O files,friction+observability branch coverage |
| O-H6 | tests.audit.validate_friction_model | Original source bytes,results,history and98/95coverage gate |
| O-H7 | tests.audit.validate_friction_receipt | Original H7 manifests/imports/history,source references,20synthetic cases,98/95gate |
| D-PYTEST | pytest.main | All16literal D files,including499diagnostic nodes;friction+diagnostic coverage |
| D-H6 | tests.audit.validate_friction_model | D's original helper,source/results/history and98/95gate |
| D-COVERAGE | tests.audit.validate_actual_binding_coverage | Exactly9diagnostic modules,independent98/95floors |

All pytest arguments/file lists are mandatory;no -k/-m slicing,no lastfailed,
ignore,xfail,monkeypatched pass or modified acceptance fixture. Pytest's cache
provider is disabled. Explicit plugins are pytest_cov.plugin and
_hypothesis_pytestplugin;ambient plugin autoload is disabled. Each command's
entrypoint,argv,cwd subject,toolchain and dependency inventory are bound before
launch. Resolve placeholders by typed registry ID and containment checks only.

The H6/H7 source reference argument denotes separately prepared complete local
Carrot Git objects at the original manifest pins,including R=c2130730239bcdb4cbde9361ab90c8d99aa4ff55
and C=f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3. These are read as raw source;
no openpilot/cereal/controller imports or native producer execution. All required
autotune history objects come from the private cohort repository,not mutable main.
No auto-fetch,installation,build or network recovery in H. Missing prerequisites
yield unavailable,not rerun with reduced arguments.

## 6. Preparation,read-only subjects and permitted scratch

Preparation is outside H:explicit new private snapshots,complete Git objects,
trusted interpreter/dependencies,registration/bootstrap,and exclusive output/
scratch roots. Never run git checkout/reset/worktree/clean/install against old
branches to prepare H. A copied working directory or git archive without the
original graph/index cannot satisfy original history checks.

"Read-only" describes audited O/D/reference subjects and existing repositories,
not every operation in the original tests. test_friction_audit creates a temporary
Git graph using init,hash-object,commit-tree;diagnostic negatives create corrupted
ZIPs/files and fresh Python children. Preserve these tests. Permit their known
test-only effects solely in new owned scratch,never in source/objects/index/HEAD,
existing evidence,original repositories,Params or a device. All descendant
effects must obey the same boundary;Python audit hooks alone are not confinement.

Future real H requires a separately prepared,observed enforcement profile that
denies audited-subject writes and network for descendants. Its mechanism and
trust evidence are NOT supplied or qualified here. Caller booleans,mode bits,
GIT_ALLOW_PROTOCOL,rereads,mount labels or content digests are not that evidence.
Without the profile a real-H request remains unavailable. Do not add an
unconfined fallback. The next pure-gate build requires no enforcement backend.

Scratch/basetemp/output paths must be absolute,non-symlink,contained in a new
exclusive owned run root,and never preexisting. Pytest may remove an existing
basetemp:therefore reject reuse before launch;do not clean old runs. Hypothesis
storage,TMPDIR,TEMP,TMP,COVERAGE_FILE and coverage JSON point only to this root.
Counters cap input/output bytes,entries,process-tree count and execution time;
exact positive integer limits belong to a later content-frozen resource profile,
not caller defaults or scientific thresholds. Missing limits are unavailable.
Bound stdout AND stderr while streaming;timeout/flood kills and reaps the entire
run process group,retaining known failures observed first. Enforcement is a
prerequisite,not a capability this documentation or a digest confers.

## 7. Python,Git and consumed-source provenance

Launch the exact prepared interpreter with -I -B -S and an exact pinned bootstrap
outside source subjects. Bootstrap adds only bound cohort root/src and the
prepared dependency roots;no editable .pth,user site,sitecustomize,PYTHONPATH or
ambient cwd discovery. Disable bytecode. Preserve required runtime proxy/auth
guards;never dump,hash or publish credential values. Reject undeclared Git
influences,trace/output controls,replace/graft/shallow/alternate/promisor
redirections. Git is exact prepared local plumbing with --no-pager,
GIT_NO_LAZY_FETCH=1,GIT_NO_REPLACE_OBJECTS=1,GIT_OPTIONAL_LOCKS=0,
GIT_TERMINAL_PROMPT=0,GIT_ALLOW_PROTOCOL=''. No fetch/helper/filter/hook execution.

Nested original test children are allowed only when statically reviewed against
the pinned full source closure and contained by the prepared supervisor. Record
their actual image/argv and expected role;unknown process or toolchain yields
rejection/unavailable,not an expanding allowlist. Existing legacy Python -c
probe belongs to exact pinned source,not arbitrary caller-provided code.

Verify actual imported module origins before collection and record consumed
origins through execution,then verify final origins/source identities again.
Bind module name,cohort revision/tree,relative source path and raw SHA256;ZIP
imports bind exact archive and member. D's legacy ZIP has9source files/11members,
SHA256 a53ddbac195f273843af05e79235985823ecc954f50018d28e5e329297de14c7.
The original helper must reject foreign exact types;top-level tests/contracts
aliases from another checkout cannot satisfy it. Path strings and __file__
assertions alone do not authenticate a compromised loader/toolchain. Instrumented
bootstrap and enforcement are separate trusted prerequisites,not self-proof.

Source/reference tree,index,HEAD and file/control identities are checked before
and after;any observed change rejects even if tests pass. Unobserved ABA,
authenticity,independent custody and forensic no-atime guarantees remain absent.
Do not call before/after equality an immutable snapshot qualification.

## 8. Neutral records and separate pure consistency evaluator

Future test-only pure sibling:tests/audit_compatibility_history/. All DTOs frozen,
slotted,exact-type revalidated,finite and defensively tuple-owned. It imports no
process,filesystem,network,clock,application,owner or estimator capability.
Use only these record concepts (builder may split private helpers,not semantics):

- SourcePin(revision:str,tree:str):exact40lowercase hex object IDs.
- OriginPin(module:str,path:str,sha256:str,archive_member:str|None):literal safe
  relative file/member paths;no prefix grants. Module source hash is independent
  of its wrapper archive hash;the complete expected origins are content-frozen.
- CoverageCounts(path:str,statements:int,covered:int,branches:int,covered_branches:int):
  exact nonnegative integers,covered<=total;bool is not int. Expected module set
  exact. Aggregate totals must be positive;covered*100>=total*98 and branch
  covered*100>=branch total*95. Zero-branch individual modules are not coerced.
- CaseOutcome(nodeid:str,setup:str,call:str,teardown:str):phases PASSED,FAILED,
  SKIPPED,XFAIL,XPASS,NOT_RUN or UNAVAILABLE;only all three PASSED completes a case.
- HistoricalCommandPolicy(command_id:str,cohort_id:str,kind:str,entrypoint:str,
  argv:tuple[str,...],expected_nodeids:tuple[str,...]|None,
  origins:tuple[OriginPin,...]|None,
  coverage_groups:tuple[tuple[str,tuple[str,...]],...]|None):kind PYTEST or
  AUDIT;AUDIT has explicit empty node set,not missing. PYTEST expected set nonempty.
- HistoricalCommandRecord(command_id:str,cohort_id:str,run_id:str,subject:SourcePin|None,
  entrypoint:str|None,argv:tuple[str,...]|None,exit_code:int|None,
  collected_nodeids:tuple[str,...]|None,outcomes:tuple[CaseOutcome,...]|None,
  origins:tuple[OriginPin,...]|None,coverage:tuple[CoverageCounts,...]|None,
  coverage_artifact_sha256:str|None,coverage_producer_command_id:str|None,
  errors:tuple[str,...],unavailable:tuple[str,...]). Explicit missing stays missing.
- HistoricalReplayPolicy(profile_id:str,cohorts:tuple[tuple[str,SourcePin],...],
  commands:tuple[HistoricalCommandPolicy,...],executor_revision:str|None,
  toolchain_digest:str|None,case_inventory_digest:str|None,
  control_profile_digest:str|None,budget_profile_digest:str|None).
- HistoricalReplayRecord(profile_id:str,run_id:str,policy_digest:str|None,
  commands:tuple[HistoricalCommandRecord,...],errors:tuple[str,...],
  unavailable:tuple[str,...]). It has no writable authority or historical_pass field.
- HistoricalReplayDecision(errors:tuple[str,...],unavailable:tuple[str,...]):
  derived consistency REJECTED > UNAVAILABLE > STRUCTURAL_RECORD_MATCH;fixed
  status BLOCKED,content_identity_only=true,integrated_admission=false,all9false.

Interfaces:assess_record(record:HistoricalReplayRecord,
policy:HistoricalReplayPolicy|None)->HistoricalReplayDecision;
canonical_record(record:HistoricalReplayRecord)->bytes;
decode_record(raw:bytes)->HistoricalReplayRecord. Canonical sorted UTF8 JSON,
explicit null,duplicate/unknown keys/nonfinite numbers rejected;schema version
historical-replay-record-v1. Digests SHA256 over canonical bytes,content only.
All nested exact types revalidated at assessment and serialization. No caller
type duck typing. Invalid wire/DTO construction raises ValueError;available
record-vs-policy contradictions become reasons. Reject known duplicates,wrong
origins,nonzero exit,failed/missing promised nodes and bad coverage even if
another required command/policy field is unavailable. Missing not-yet-observed
outcomes are unavailable;an observed completed run omitting mandatory nodes is
rejected. Exit0 or a printed H6/H7 success marker alone is not a complete record.

run_id is32lowercase hex,assigned to one prepared run,not a source identity or
authority. All six records bind the same run_id. PYTEST coverage identifies its
own command as producer;the two cohort audits must bind that cohort's PYTEST ID
and the identical raw coverage-artifact SHA256. Cross-cohort,old-run or duplicate
producer substitution rejects. The raw artifact remains private external data.
Coverage groups are exact nonoverlapping module path tuples:friction_model plus
observability for O,friction_model plus diagnostics.actual_binding for D. All
records of a cohort carry the same complete counts and group inventory;each
group independently meets98/95. Do not combine good coverage in one group to hide
bad coverage in another. Missing group inventories are unavailable,not empty.
Policy profile,cohorts and six command IDs must match this registered registry;
future materialized argv/origin/module/limit values require a separate freeze.

H1's pure gate can match supplied synthetic claims;it cannot prove a process ran,
authenticate a supervisor,or clear HISTORICAL_REPLAY. A policy digest is not
authorization. Its records remain separate from C1 and the old pure core's
IO_UNAVAILABLE. No conversion into QualifiedEvidence/AuthorizationGrant or owner
proposal. H alone cannot accept bad current C,or unregistered R/Q/I/STACK.

## 9. Acceptance,versioning and content freeze

acceptance.json contains40PLANNED_NOT_EXECUTED cases. HR-001–026 are preparatory
pure-contract cases;HR-027–040 require a separately scoped I/O runner. None was
executed as an H test here. Existing HC obligations are referenced,not replaced.
Pure preparation targets>=98%statement and>=95%branch coverage independently;
all old90/95/98floors and scientific criteria remain exact. Synthetic tests do
not count as kernel/VM/device/runtime or real historical execution proof.

This six-new-document commit is H1 design only. It cannot expand the original
ten-active-path ENTRY ceiling or C1's eleven-path implementation ceiling. Future
pure preparation may ADD ONLY the eight literal paths in semantics.json. It
must preserve all existing files and is exploratory,not actual R/Q/I. Any I/O
runner or ENTRY adoption requires a new separately scoped semantic/content
registration before its code/execution. Never edit old metadata or choose latest
by branch/glob/clock. Freeze executor source/toolchain/command expansion/case
inventories/origin closure/budgets in a later externally pinned content record,
not a record containing its own digest or guessed future SHA. Results stay out
of audited subjects. Ordinary post-freeze code changes require a new revision.

Change semantic version for cohort/stage/origin/timing/outcome/precision meaning;
source revision and observed run identity are separate. Retain failed attempts.
No broad read-only/file-mode claim,source hash,green synthetic test or old review
may be promoted into runtime/vehicle/application readiness.

## 10. Handoff and non-goals

Next single buildable task:implement the eight-path pure H1 record/policy gate
using the companion TDD plan,without an I/O runner or real O/D execution.
It is NOT started by this design task. Remaining execution prerequisites include
complete O/D audit node inventories,exact executor/content review and prepared
enforcement/toolchain/resource evidence. Preserve existing C1 implementation and
all old PRs/main;no push,PR,merge,rebase,force-push or external publication.

No real vehicle,Params,controller/cereal/schema edits,estimator qualification,
candidate/application/owner bridge,longitudinal,external AI,upstream PR,VM/QEMU/
guest execution or HF publication. No test skip or floor waiver to claim H pass.
