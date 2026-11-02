# ENTRY read-only Git capture — design registration K1

## 1. Intent, scope and status

Specify how a future development-only adapter can observe exact local Git
objects and the actual current checkout without changing either. The existing
pure core compares supplied content; it cannot prove who captured it or whether
HEAD/index/worktree/attributes belonged to one atomic snapshot.

This task adds design/semantic/source/acceptance metadata only. No reader,
collector, historical executor, producer, CLI or qualification bridge exists as
a result. All runtime/application permissions remain false; final ENTRY remains
UNAVAILABLE/BLOCKED. The author makes routine engineering choices under the
user's delegation; these choices are not separate user approvals.

Pinned inputs:
- M:a5d3514f23797829eb58d08c638b22cf4dd30c8a.
- D:#58,75e00280a09323ad4a3fc82453383f220c92f6c6.
- O:#16,5357d5d555d49b258affa237d83b8491b8a8c6ce.
- W:exploratory pure core,2160085a1fed5999c4e25fbbb5480eea355e05c9.
- R0:prior pure-core semantic freeze,d3811778683b7e1659a8b3bb92dab5e01a59d61a.
- S:later stack,eb305bfa373d92669217617bcdf667798118d0d8;reference only.

K1 is a new design-registration commit whose sole parent is W. Its four literal
metadata additions are listed in semantics.json. It is NOT an ENTRY R or an
append-only R' repair:W is not I. No actual Q/I exists. R0's ten active paths and
semantics remain untouched. K1 cannot silently extend R0's closed ceiling.
A future definitive ENTRY R must start at D with an explicitly revised finite
scope,then Q and I=[Q,O]. Exploratory source can be registered by exact postimage;
it must not be relabeled as an already registered integration. K1's SHA is
recorded externally after commit,never embedded in its own metadata.

## 2. Approaches and author decision

| Approach | Assessment |
|---|---|
| Git status/diff or old helper's selected path set | Insufficient:ignored files,hidden index flags,ambient filters and whole-tree closure can be missed. |
| Provision and qualify an immutable filesystem/VM snapshot | Stronger possible provenance,but provider/executor qualification and snapshot creation are outside this task. |
| Explicit raw-object reader + closed whole-checkout inventory + safe reads + repeated capture | Selected:read-only diagnostic evidence,with stability separated from atomicity. |

Initial profile:C1_POSIX_RAW_BYTES_V1. No cleaning/filter execution. Raw worktree
bytes must equal the pinned Git blob. CRLF-to-LF equivalence is not implemented
in C1,even if an older historical helper accepts it. Windows/native safe-open
and normalized-text variants require separately specified and tested profiles;
they cannot fall back to ordinary open/resolve or strip CR silently.

## 3. Architecture and future literal path ceiling

The W architecture test inspects every module under tests/audit_compatibility
and allows only pure imports. Adding git_reader.py there would violate it.
Use the sibling audit-only namespace tests/audit_compatibility_capture instead.
Keep every existing pure-core source/test/guard byte unchanged in the first
reader slice. Nothing ships under src/ or the vanilla wheel.

Future implementation ceiling,not authorization or implemented files:
- tests/audit_compatibility_capture/__init__.py
- tests/audit_compatibility_capture/contracts.py
- tests/audit_compatibility_capture/git_reader.py
- tests/audit_compatibility_capture/worktree_reader.py
- tests/audit_compatibility_capture/capture.py
- tests/fixtures/audit_compatibility_capture.py
- tests/test_audit_compatibility_capture_values.py
- tests/test_audit_compatibility_capture_git.py
- tests/test_audit_compatibility_capture_worktree.py
- tests/test_audit_compatibility_capture_cohort.py
- tests/test_audit_compatibility_capture_architecture.py

Imports are inert. Explicit calls alone perform local reads and allowlisted Git
subprocesses. No network,thread,background job,timer callback,persistence,
checkout,installation,build,hook,filter,controller or estimator execution.
The caller may save a returned report outside the audited checkout;the adapter
does not write it. No root discovery from cwd or mutable branch-name policy.

## 4. Proposed interfaces and closed outcomes

Frozen/slotted,defensively copied values:
- CaptureRequest:exact candidate_head,validation_head,declared_base or explicit
  None;source OIDs;explicit trusted RepoLayout;profile/version;resource budget.
- RepoLayout:worktree root,per-worktree gitdir,common gitdir and finite control
  file roots. These are access selectors,not content or authority identities.
- ObjectCapture:raw commits,complete path/mode/blob inventories and blob bytes;
  unavailable object IDs separately from known structural errors.
- IndexCapture:raw index SHA256/version,complete stage/mode/OID/name/flag rows.
- FileCapture:relative path,type,mode,raw-byte length/SHA256/Git blob identity;
  raw tracked bytes where required;read-only stat identity is diagnostic only.
- AttributeCapture:each actual path's complete effective attribute vector plus
  exact tracked attribute sources and relevant config/control-file identities.
- CapturePass:HEAD/index/control identities,complete tracked and untracked
  inventory,object/file/attribute observations and explicit unavailable reasons.
- CaptureReport:two passes,optional partial CompatibilityInputBundle,errors,
  unavailable facts,consistency status,atomicity NOT_ESTABLISHED and all9false.

Proposed calls:read_objects(request)->ObjectCapture;
capture_checkout(request)->CaptureReport;
assess_capture(report,policy)->CaptureConsistencyDecision. All are future APIs.
No public switch accepts caller-supplied historical_pass/atomic=true/qualified.

Known contradiction -> REJECTED,even with missing peers;otherwise incomplete or
unsupported -> UNAVAILABLE;only all C1 checks complete/equal -> OBSERVED_STABLE.
This last diagnostic is never full CONTENT_MATCH,admission or runtime approval.
Absent,empty,false and zero remain distinct. Do not turn ENOENT or parse failure
into an empty inventory/default. Pure assess_compatibility remains unchanged:
its four fixed IO_UNAVAILABLE reasons are not removed by this adapter.

## 5. Trust boundary and repository preflight

The toolchain/OS and explicitly prepared checkout are trusted to execute local
read-only plumbing;their authenticity,immutability and compromise resistance
are not qualified by content hashes. Arbitrary untrusted repositories are not
an executable input interface. Fail closed on unsupported configuration.

Validate explicit absolute roots and each ancestor without following symlinks;
support ordinary repositories and declared linked worktrees. A .git control
file may point only to the declared gitdir;do not reinterpret a tracked .git
path or arbitrary gitfile as a new root. Cross-check Git layout outputs against
these declared roots. Reject nested repositories/submodules and undeclared
control-file escapes. Do not change safe.directory or repository configuration.

Read known system/global/local/worktree config sources safely without following
includes. A small closed parser must reject unsupported syntax/includes rather
than approximate Git semantics. Before any plumbing,identify actual attribute,
filter,fsmonitor,external driver,sparse/split/partial/shallow/alternate/graft and
object-format influences. Values unrelated to that policy are not serialized;
especially omit remote URLs,credentials,user identity and config raw bytes.
Hash relevant control bytes in memory,report redacted reason codes only.

Config discovery starts from the launcher's declared finite system/global/XDG/
local/worktree config paths (including explicit absent files),not a repository
include search. Undeclared/unreadable scope is UNAVAILABLE. The C1 grammar may
support Git sections,quoted subsections,ordinary assignments and documented
escapes;anything it cannot parse exactly is UNAVAILABLE. The builder fixes its
finite grammar and inert-key table with Git parity tests before implementation
acceptance. All include/includeIf directives are unsupported and never followed.
Ordinary remote/user metadata may be parsed as inert data but is never reported.

Nonempty info/attributes,external core.attributesFile,filter/working-tree-
encoding/ident attributes,custom merge/diff drivers and fsmonitor helpers are
rejected. Unsupported config syntax,global include discovery,object format,
index feature or platform guarantee is UNAVAILABLE;known forbidden use remains
REJECTED. No command is used to make a rejected configuration acceptable.

## 6. Exact Git read protocol

Child execution uses argv,shell=False,explicit cwd and vetted Git executable,
bounded subprocess output/time. Resource exhaustion is UNAVAILABLE with prior
known errors retained;budgets are capture limits,never scientific thresholds.
Prepare the child environment from an explicit non-secret contract. Reject
ambient repository redirections (GIT_DIR/WORK_TREE/INDEX_FILE/COMMON_DIR/
OBJECT_DIRECTORY/ALTERNATE_OBJECT_DIRECTORIES/NAMESPACE/CONFIG*/ATTR_SOURCE/
REPLACE_REF_BASE/GRAFT_FILE/SHALLOW_FILE) instead of trusting them. Preserve
host proxy/auth guard variables;never dump environment or secret files.

Always set GIT_NO_LAZY_FETCH=1,GIT_NO_REPLACE_OBJECTS=1,GIT_OPTIONAL_LOCKS=0,
GIT_TERMINAL_PROMPT=0,GIT_ALLOW_PROTOCOL=''. Use --no-pager and disable fsmonitor
and untracked-cache callbacks on every plumbing invocation. System/global
configuration is isolated only AFTER its actual influences were checked;
isolation must not conceal an effective override. No lazy fetch fallback.

Closed command families:rev-parse for layout/HEAD cross-check;ls-tree -rz
--full-tree <exact40OID>;cat-file --batch with exact hex OIDs;ls-files --stage
-z and --others -z with NO exclude rules;check-attr -z --all --stdin and an
explicit text/eol/filter/ident/working-tree-encoding/merge/diff vector,including
--cached variants for tracked-policy agreement. Parse NUL-framed paths and
length-framed object bytes exactly,not display quoting or line-splitting names.

Never invoke status,diff,textconv,cat-file --filters,hash-object --path,
checkout,read-tree,update-index,clean,reset,fetch,submodule,merge or any writer.
A raw hash-object --no-filters --stdin oracle is test-only,not needed at capture.
Get object type/length/raw bytes,recompute Git framing and compare requested OID;
never infer a commit's parents from rev-list/shallow/replace views. Parse literal
LF headers with the W boundary. Complete needed ancestry/tree closure or report
the exact missing IDs. No narrowed selected-path tree substitutes for full tree.
SHA256-format Git repos,alternates,nonempty graft/shallow/partial-clone metadata
and unsupported object types remain unavailable/forbidden as classified above.

Classification is closed in semantics.json:unsupported SHA256/alternates/
shallow/partial/index/platform features are UNAVAILABLE;nonempty grafts,
replacement refs,ambient repository redirects and custom execution/attribute
overrides are REJECTED. Inspect loose and packed replacement refs without
executing their rewrite. Plain detached HEAD is supported;symbolic HEAD/ref
bytes are control observations,not the source-policy selector.

## 7. Index,worktree and complete inventory

Initial index support:SHA1 Git index v2,valid checksum,regular100644 stage0,
no assume-unchanged/skip-worktree/intent-to-add/unmerged entries. The closed
parser validates all entry framing/padding/names/OIDs/flags and the optional
TREE cache extension's framing (not its authority). Unknown extensions,v3/v4,
split/sparse index are UNAVAILABLE,never rewritten. Duplicate/unsafe/case or
file-directory collisions and malformed checksum/flags reject. Cross-check
every parsed row with ls-files and the complete actual HEAD tree. Never trust
index stat cache to skip reading tracked files. W has321100644 files;this is an
observation,not a hard-coded future inventory size or grant for extra files.

For each tracked path,walk from a held root directory FD using no-follow
directory-relative opens (O_DIRECTORY/O_NOFOLLOW),then fstat a regular leaf FD,
read bytes,and fstat/revalidate path identity afterward. Reject symlinked
ancestors/leaves,mode changes,special files and path/case collisions. Never
resolve then reopen a string path. No equivalent guarantee -> UNAVAILABLE;
Windows must not silently fall back to POSIX assumptions.

Enumerate the full worktree namespace,not just a diff list or registered paths.
Exclude only the verified Git control plane itself. Compare independent safe
filesystem and Git untracked inventories;include ignored files/hidden names.
Any unregistered untracked/ignored path rejects WITHOUT opening its contents;
report its path digest,not secret filename/content. Empty extra directories
are diagnostic only;they are not Git content. Do not traverse unknown symlink
directories or nested repositories. Registered untracked allowance is empty in
C1;no .venv/cache/log directory-prefix exception. Run future acceptance capture
on a separately prepared clean checkout;preparation is not a reader action.

RAW_BYTES_ONLY:binary ZIPs and all tracked text are compared byte-for-byte with
Git blobs. A CRLF difference rejects;never replace CRLF then claim exact raw
identity. Effective attributes must agree with pinned tracked policy for every
path;ENTRY inherits D's .gitattributes exactly,O's absence is known absence,
not an empty file. Capture both cached/current attribute sources and all unknown
attributes;unexpected extra attributes also reject. Do not run a clean filter
to establish equivalence. A later normalized profile must prove actual built-in
Git-clean equivalence without enabling arbitrary helpers/races.

For this fixed D policy,the expected applied vector is {text:set,eol:lf} for
src/cyberpilot_autotune/diagnostics/**;{binary:set,diff:unset,merge:unset,text:unset}
for tests/fixtures/actual_binding/*.zip;empty applied vector elsewhere. Explicit
queries for absent attributes return unspecified,not false. These rules are
valid only with the exact pinned root attribute bytes and no other tracked
attribute files/macros/overrides;any expansion requires new policy registration.
The check-attr observations must equal these independently fixed vectors,not a
second query against the same mutable attribute file labeled expected.

## 8. Cohort stability is not atomicity

Pass A:read HEAD/index/config/ref/attribute controls,full object+path inventories,
and safely read all required tracked bytes. Pass B repeats every relevant
identity/inventory/content read,not just size/mtime/HEAD. Controls are rechecked
after each pass. Compare complete normalized records,not wall clock order.
Any observed difference,including disappeared/added ignored paths or restored
metadata with changed bytes,rejects;IO failures add unavailable facts.

Equality means only OBSERVED_STABLE. Between-read ABA and concurrent changes
that restore every observed byte cannot be ruled out by rereads/fstat/hashes.
Read-only bind mounts,caller booleans or a digest are not immutable provenance.
SOURCE_CAPTURE_ATOMICITY remains UNAVAILABLE even after a stable capture.
Provider-qualified snapshot/custody evidence needs a separate contract and
qualification task;this design defines no way to clear that blocker.
HISTORICAL_REPLAY also remains UNAVAILABLE. Do not link this report to estimator,
application,owner proposal or the PR8 runtime sidecar.

## 9. Acceptance,versioning and non-goals

acceptance.json contains finite PLANNED_NOT_EXECUTED cases and literal owners;
none is represented as a passing implementation test. Include actual temporary
Git repositories for raw object/index/attribute oracles,negative helper canaries,
independent filesystem drift injection,missing+invalid combinations and
Linux/Windows explicit supported-or-unavailable outcomes. No live network,
vehicle,VM/QEMU/guest,Params/controller/schema execution is needed or allowed.
Keep existing1931test cases,old floors and all W source bytes;future new reader
statement>=98%,branch>=95%,target100/100. Build/fresh wheel/source/history/replay
and original pure import guards remain mandatory at implementation,not claimed
completed by this design. All output artifacts stay outside audited checkout.

Capture schema,normalization,stage/cohort/availability/units or supported index
semantics changes require new semantic registration/version. Source SHA changes
are separate exact source identity,never automatic policy promotion. Digests
identify content only,not authenticity,independent custody or approval.
No VIN/route/GPS/driver identity/raw CAN/images/model data is captured. No HF or
cloud publication,PR8/9/16–58 edit,force-push,merge,upstream PR or external AI.
D01–D04 and all artifact/factor/bounds/fingerprint/watchdog/executor/parameter
qualification blockers remain. APPLICATION_NOT_AUTHORIZED is unchanged.

The next single task after K1 is a separately scoped TDD implementation of the
C1 reader in the sibling namespace,using these exact semantics and planned
cases. It does not include historical execution,full ENTRY acceptance or any
original guard/main/PR modification. It is not started in this design task.
