# History-preserving audit compatibility contract — design v1

## 1. Intent, scope and status

Design an **audit-only** contract for composing the pinned diagnostics PR58 and
friction-observation PR16, without rewriting their old evidence or weakening
fail-closed guards. Later stack adoption is a distinct profile, not inherited
permission. This task writes this design/preregistration specification only.
It does not implement a checker, modify a repository/PR, create a new Git
registration, resolve a merge, qualify an estimator or authorize execution.

The user delegated routine engineering choices; choices below are the author's
decisions, not evidence of user approval of every detail. Existing trust/custody
D01–D04 decisions remain OPEN. External documents are content-addressed design
artifacts, **not a committed Git preregistration or an authority grant**.

Pinned basis (branch names are labels only):
- M main:a5d3514f23797829eb58d08c638b22cf4dd30c8a.
- D diagnostics:75e00280a09323ad4a3fc82453383f220c92f6c6.
- O observation:5357d5d555d49b258affa237d83b8491b8a8c6ce.
- S later stack:eb305bfa373d92669217617bcdf667798118d0d8.
SOURCE_PINS.json records tree/parents,37 exact file anchors and five old
registration/manifests. The earlier read-only report proved R01–R05:
two textual conflicts, incompatible exact helpers, pinned H7 H6-hash mismatch,
closed later history scope, and attributes add/add/prefix ordering.

## 2. Approaches and selected architecture

| Approach | Decision / tradeoff |
|---|---|
| Broaden old helpers or rewrite old manifest hashes | Rejected: loses provenance and permits unrelated changes. |
| Pick one branch's validators or reverse merge order | Rejected: the other branch's edits/hash/scope remain rejected. |
| Explicit historical replay + exact current transition | Selected: more audit tooling, but independently proves old facts and current composition without calling them the same fact. |

The selected checker has two mandatory phases:
H = replay the original checks at exact immutable historical snapshots;
C = validate the complete current tree/index/worktree against separately frozen
exact compatibility metadata. Acceptance requires H AND C. Never replace a
current path with historical bytes and then label the old check as current.
Never call an old closed-scope verifier with a filtered changed-set to hide
current changes. A historical pass alone cannot admit the current tree.

## 3. Separate profiles

| Profile | Fixed inputs / scope | What it cannot imply |
|---|---|---|
| ENTRY_COMPOSITION_V1 | M,D,O; resolve R01–R03 and exact packaging; preserve D attributes | Does not admit S or the old29path/successor policy on a changed current tree. |
| STACK_ADOPTION_V1 | S plus an exact, successfully qualified ENTRY head and registration | Cannot be synthesized by promoting ENTRY, oldv1 records or standalone green CI. |

STACK needs a later registration with its concrete ENTRY subject SHA; that SHA
is UNAVAILABLE now and must not be guessed. This design specifies its obligations,
not its completed registration. Each profile has its own closed scope and source
anchors. Wrong profile/missing source pin/extra ancestry or tree delta rejects.
No branch name, clock, object address or current working manifest selects policy.

## 4. Two freezes and a non-circular Git binding

Future implementation uses separate semantic and exact-content freezes:

R = semantic preregistration commit (contract, acceptance inventory, source pins).
Q = exact-content preregistration commit, sole parent R, containing a closed
manifest and **inert** postimage blobs; no active implementation is changed in Q.
I = first implementation/integration commit, exact parents [Q,O] for ENTRY.
R's sole parent is D. R/Q/I are unavailable in this design-only task.

The new verifier may embed R's already-known identity, but must NOT embed Q's
identity in any file whose postimage is registered by Q. At I, Q is obtained from
I's first parent and must have sole parent R. No own-hash/own-commit fixed point
is attempted. Q's manifest does not contain its own digest; its metadata/inert
blobs are inherited exactly from Q's tree. The expected I tree is:
Q tree + explicitly enumerated incoming O content + registered active postimages.
Every other path must retain its selected pinned source image. Compare the
entire result, not just the allowlisted changed paths.

Registration rows store active path/mode plus preimages from each applicable
input and an exact postimage blob/SHA256; the inert blob must really exist in Q.
Raw source bytes are not silently formatted or normalized before identity checks.
Inert new source is not exempt from lint/type/test: activated source gets every
existing gate. Exploratory TDD before Q is labeled exploratory; R fixes semantics
before implementation, Q fixes content before definitive I acceptance/CI/review.

Repairs are append-only: new semantic R' sole-parent old I, Q' sole-parent R',
and I' sole-parent Q' (O is already an ancestor). R' names the prior I/Q and
supersedes that content registration. Never mutate old R/Q/I or force-push.
No ordinary post-I tracked edits are implicitly allowed; results/logs stay
outside the checkout. Any tracked code/docs change needs a new registered
revision and exact-head review/CI. Old failed attempts are retained as failures.

Candidate source head and validation checkout head are separate fields.
For push they normally equal I/I'. For a GitHub PR virtual merge, require exact
declared base and source parents, source-head identity and tree-equivalence to
the registered candidate. An unregistered main drift/tree delta fails and
requires new registration, never a permissive fallback. Pin R separately in
the reviewed bootstrap/CI; graph/content consistency is not self-authentication.

## 5. Proposed pure core and explicit development-only I/O

Future test/audit-only namespace:tests/audit_compatibility/. Nothing is added to
src/, application/, observability/, runtime/, or the neutral diagnostics API.

- contracts.py:frozen/slotted tuples for GitImage,SourceAnchor,TransitionRow,
  CompatibilityInputBundle,PinnedCompatibilityManifest,AuditCompatibilityDecision.
- validation.py:pure assess_compatibility(bundle,manifest) -> decision.
- git_reader.py:explicit local Git/blob/index/worktree snapshot adapter.
- historical_replay.py:explicit prepared child interpreter in private snapshots.
- cli.py:orchestrates H+C and reports both subjects/results independently.

The implementer may split these files further, but may not broaden capabilities.
The pure core receives bytes and explicit unavailable values; no Git/file/network/
clock/process imports. Missing manifest/postimage/source is UNAVAILABLE, not an
empty value,zero,false or a skipped mandatory check.

Decision precedence:REJECTED > UNAVAILABLE > CONTENT_MATCH. CONTENT_MATCH requires
all mandatory H/C checks and complete inventory. Result names must not contain
runtime-qualified,friction-identifiable,approved or application-authority claims.
Fixed fields:status BLOCKED,content_identity_only true,integrated_admission false,
all9domain permissions false,scientific/runtime/device qualification false.
This decision is not QualifiedEvidence,AuthorizationGrant,owner proposal or
controller receipt. No estimator/application bridge consumes it.

## 6. Historical phase H

Replay original H6/H7 audits at O with original manifests,H6 helper,original
source imports and original graph. Preserve H7's recorded H6 hash
aa27d15517e693b0288ed37893deae4515a7c1f88388bb29e871c9fe0e68d032.
Replay diagnostics original source/476 acceptance identities at D as relevant.
The current diagnostic H6 hash eaddb6091b5054613ec8e7f0eb15cae9b64aa3d1d8f4e1205c688b89f1947efe
is a different source identity, never substituted into the old manifest.

For STACK, separately replay old P/P2/P3/P4/P5 policies at their pinned original
source cohorts and the final S source view. Their complete loader closure and
manifests remain unmodified; all old raw-object,parent,mode,index/worktree and
negative mutation checks are retained, not replaced by the prior audit's sentinel.

Use a fresh child per historical cohort/current cohort; no shared sys.modules or
top-level aliases. Verify the tree and imported audit/test/runtime module origins
before executing only the closed, registered source-audit/test entrypoints.
Use private snapshots with their own HEAD/index rooted at the declared revision,
never the original repository HEAD or a mutable caller cwd. No fake ROOT/path
proxy can satisfy final acceptance. Missing objects fail without fetch.

H reports historical revision,tree,commands,test identities and outcomes;
current C reports actual current sources. Reporting H as validation of current
H6 bytes or relabeling old source evidence is forbidden.

## 7. Current phase C and complete file accounting

1. Parse canonical JSON with duplicate/unknown keys rejected; nonfinite numbers
   rejected; booleans not integers;None explicit. Digests are content only.
2. Verify R/Q/I graph,source anchors and actual local object availability.
3. Verify every inert postimage in Q against its Git blob,raw SHA256,mode and
   exact active destination. Reject duplicate/escaping/case-conflicting paths.
4. Materialize expected tree in memory/private Git objects, never mutate the
   original repository. A conflict marker/tree is not an accepted implementation.
5. Compare every tracked path/type/mode/blob against the full expected tree;
   extras/deletions/unknown changes fail, even outside requested changed subset.
6. HEAD/index agree; stage0 only,no unresolved entries. Worktree regular-file
   identity agrees;no symlink escape or unexpected executable-mode change.
7. Explicit source/worktree normalization policy only:registered LF files exact;
   CRLF equivalence only where original policy permits and actual Git-clean
   result agrees. Reject custom filters and .git/info/attributes overrides.
   Never execute arbitrary filter/merge/hook commands to make bytes match.
8. Effective attributes must equal registered tracked policy. STACK preserves
   the S attribute bytes as prefix then appends diagnostics LF/ZIP binary rules.
   ENTRY retains D attributes byte-for-byte. Check actual CRLF/Windows behavior.
9. Index/worktree/untracked sets are closed over exact registered paths,not a
   directory-prefix grant. Logs,caches,results and snapshot tools stay outside
   the audited checkout. Capture HEAD/index before+after;changes reject.
10. Old production source/goldens/manifests and neutral package bytes stay exact.
    Current audit routing/test edits require explicit pre/post rows and
    H+C checks;unknown edits never inherit permission from an ancestor profile.

The reader uses argv arrays,no shell interpolation,local exact revisions,
GIT_NO_LAZY_FETCH=1,GIT_NO_REPLACE_OBJECTS=1,GIT_OPTIONAL_LOCKS=0.
Network,installation,build and test prerequisites are prepared separately,
not silently invoked to recover an unavailable source. Compromised Git/Python/
compiler/CI tooling is not qualified by content hashes.

## 8. Closed scope ceilings versus actual registrations

ENTRY existing-path ceiling (not permission to modify all):
- tests/architecture/test_knowledge_boundary.py
- tests/audit/test_carrot_writer_ownership.py
- tests/audit/test_hoya_c3_atune_evidence.py
- tests/audit/validate_friction_model.py
- tests/audit/validate_friction_receipt.py
- tests/audit/test_h7_namespace_preservation.py
- tests/audit/test_friction_receipt_sources.py
- tests/audit/test_friction_audit.py
- tests/diagnostics/actual_binding/test_integration.py
- MANIFEST.in
- .github/workflows/ci.yml

ENTRY inherited .gitattributes,all src/ modules,old evidence/manifests,remaining
test cases and replay goldens are preservation-only. New audit files/tests,
CI and metadata have exact literal path lists in Q; no wildcard admission.
Any discovered need outside this ceiling requires a revised semantic R before
new content registration. Do not improvise an exception in implementation.

STACK additionally needs its own explicit ceiling/materialization for the five
history_transition loaders and affected closed-history call sites,attributes,
and any compatibility routing. Exact paths and incoming ENTRY head must be
fixed in its R,not inferred from directory or accepted by ENTRY. Old P..P5
manifests stay preservation-only. This design leaves STACK actual postimages
unavailable,not silently approved.

## 9. Existing tests/CI must keep their jobs

Keep original test nodeids/scenarios and all negative inputs in a traceable
historical/current mapping. A current test that previously called a frozen
helper must explicitly assert both original replay and current exact compatibility;
do not skip it,xfail it,monkeypatch its result or delete the old rejection.
Invalid current manifests/changed bytes must reach C and reject even when H passes.

Existing H6/H7 source/policy/scientific/geometry/schema semantics are unchanged.
Keep all coverage floors:global90%,existing95/98% subgates,H6/H7 and diagnostics
statement>=98%,branch>=95%;no numerical/scientific threshold is invented.
New pure compatibility core also statement>=98%,branch>=95%,target100/100.
Current full suite plus historical tests,source/history audits,replay4goldens,
Ruff E/F/I/UP/B,format,strict mypy,build,fresh vanilla wheel and optional research/
schema smoke run on exact I/I';Linux/Windows ×3.12.3/3.12, push and PR events.
Wheel must ship both neutral namespaces unchanged,not audit tooling/frozen data;
sdist must retain the original legacy ZIP. Verify old exact-type and shadow
negatives and the original476diagnostics case identities.

No full STACK execution is assumed safe from old green CI. Before running its
tests,classify effects read-only. Required VM/QEMU/guest/vehicle/Params/controller/
producer execution is not authorized by this contract. If an existing mandatory
test requires it,do not silently skip/waive it:STACK remains blocked pending a
separate scope decision. ENTRY and source-only historical audit replay have no
such permission. This task executes none of those tests.

## 10. Admission/test contract and remaining unavailable facts

ACCEPTANCE_MATRIX.json defines mandatory success and mutation cases,all
PLANNED_NOT_EXECUTED. Every R01–R05 obligation has explicit test ownership.
The exact implementing API postimages,source code,registration IDs,R/Q/I SHA,
combined test totals and CI/review outcomes do not yet exist. A future Q must
materialize every required field;null/template data can never admit anything.

The external frozen specification records expectations before implementation;
it is not an actual source-policy preregistration or proof the design works.
Builder review checks unanswered planning questions,not C0/I0/M0 code review or
runtime safety. Future exact-head review/CI and separate merge approval remain.
No current PR/main/branch changes are part of this design task.

Registration itself has a closed delta:initial R may only ADD its literal
semantic design,source-pin and acceptance metadata paths,never change D's
active files. Q may only ADD its one content manifest and exactly referenced
inert .blob files under the declared data root;no active .py/CI/source change.
Validate these full R/Q deltas before inheriting Q's tree,so arbitrary additions
cannot be laundered through the registration tree. New active audit/test paths
must already be literal entries in R's finite ceiling. Any extension needs
new semantic registration,not arbitrary Q.new_paths.
Suggested initial metadata paths:
docs/evidence/audit_compatibility/entry-v1-r1/{semantics,source_pins,acceptance}.json
and docs/evidence/audit_compatibility/entry-v1-r1/content.json.
These braces are notation only;the actual manifest lists four literal paths.
Inert paths are exact SHA256-named .blob files declared by Q,not directory grants.
Repair registrations use a new literal revision path and preserve all old
metadata files in both history and current tree. Never select latest by glob,
branch,wall-clock or mutable working manifest.

Expected-tree algorithm is a literal three-way image selection using M as base,
Q as left and O as incoming (STACK uses its registered predecessor/input bases).
Absence is a distinct image. Equal sides retain that image;one side equal to
base selects the other;only genuinely divergent paths require an exact
registered resolution. Then apply exact registered active postimages. Unknown
resolution/deletion/mode changes fail. No textual merge or prefix fallback
determines admission. This preserves D's MANIFEST include when O equals M there.
Q does not store its own SHA,an I commit SHA or a final I-tree SHA:those would
be circular. Derive the complete expected tree from Q's actual pinned tree and
its rows after Q exists;compare I/current validation tree to that derivation.

## 11. Non-goals and single next boundary

No vehicle/VM/QEMU/guest execution,Params/controller/cereal changes,estimator/
candidate qualification,application or owner bridge,longitudinal,external AI
service or upstream PR. Same-owner HF backup is not independent custody.
Keep D01–D04 OPEN,all9permissions false,APPLICATION_NOT_AUTHORIZED and all prior
artifact/factor/bounds/fingerprint/watchdog/executor/qualification blockers.

After this design task,the single recommended implementation task is:
implement ENTRY_COMPOSITION_V1's pure checker plus bounded mutation tests and
R/Q preregistration machinery in a new isolated branch,without altering the old
PR heads or merging. That follow-up is not started or authorized by this file.
