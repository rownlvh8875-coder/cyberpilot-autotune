# H1 Closed Synthetic Containment Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a development-only closed toy harness that observes FD/mount/descendant/supervision behavior without historical O/D execution or H admission.

**Architecture:** Inert immutable contracts plus a pure S-only seccomp encoder;one effectful runner creates a fresh owned toy tree and launches one dedicated supervisor. Only that helper becomes subreaper;all public results remain BLOCKED/all9false. No old code or record gate is connected.

**Tech Stack:** Python>=3.12.3,<3.13,stdlib,pytest,Ruff,strict mypy;Linux x86_64 effectful observations with exact registered Bubblewrap/setpriv/Python pins.

**Spec:** docs/superpowers/specs/2026-11-03-h1-executor-profile-design.md and docs/evidence/audit_compatibility/executor-profile-v1/{semantics,sources,acceptance}.json. This design commit does not start implementation.

## Global Constraints

- ADD ONLY the ten literal paths below;no existing source/test/config/CI/metadata edits.
- Status BLOCKED;all nine permissions false;integrated_admission=false;HISTORICAL_REPLAY remains UNAVAILABLE;source_capture_atomicity=NOT_ESTABLISHED.
- No actual H/O/D imports,collection,commands,source mounts,ENTRY/C1 bridge or application/owner/estimator/product dependency.
- No vehicle/Params/controller/cereal/schema/VM/guest,build/install/network publication,HF,push/PR/merge/rebase/force-push.
- No arbitrary argv,mount,filter,budget,FD or executable public parameter;only the eight SyntheticCase values from spec section7.
- Required controls fail closed with no --try,privileged/unconfined/alternate backend or numeric-PID fallback.
- Parent credentials/proxy guards untouched;children credential-free without bypassing provider guards;no credential values logged or hashed.
- S normal wall5seconds,timeout0.4seconds,cleanup2seconds,controller extra2seconds;CPU3,AS268435456,FSIZE1048576,NOFILE64,CORE0;output retained<=65536combined;read chunks4096.
- Fixture self-deadline3seconds,at most one descendant;no fork bomb or exhaustion attack. Limits are per-process,not aggregate/H/scientific qualification.
- Preserve all2279baseline tests and old90/95/98floors;new harness statement>=98%,branch>=95%,aim100/100.
- EP-001–030 remain planned in old registration;record actual execution mapping externally without rewriting this metadata.
- Local append-only isolated work;preserve every failed attempt and old evidence. Keep branch locally at finish.

## Review Focus

- An inherited RW file or connected socket bypasses readonly mounts:normal runner excludes it by identity,private unsafe control reproduces the failure (Task2).
- Direct child exits while a setsid descendant holds output pipes:deadline still fires and cleanup is not inferred from wrapper exit (Task3).
- PID reuse or supervisor crash turns cleanup into an unrelated kill:require retained pidfd/owned child handles;unknown cleanup stays UNCONFIRMED (Task3).
- Caller replaces run-root path or points at old evidence:reject nonexclusive/symlink roots and never clean/delete an old directory (Task2).
- Missing host enforcement gets disguised by mocks or green unit tests:separate actual observations from logic tests;no H readiness result exists (Tasks1,3).

## File map

1. tests/audit_compatibility_executor/__init__.py — inert public exports only.
2. tests/audit_compatibility_executor/contracts.py — exact frozen cases/request/result and fixed blocked properties.
3. tests/audit_compatibility_executor/seccomp.py — pure exact x86_64 S BPF bytes,not an H filter.
4. tests/audit_compatibility_executor/supervision.py — dedicated helper lifecycle,limits,streaming,pidfd,owned kill/reap.
5. tests/audit_compatibility_executor/runner.py — pin/precondition checks,new toy directories,mount/FD policy,closed dispatch.
6. tests/fixtures/h1_synthetic_payload.py — inert on import;closed script toy actions,one descendant,self-deadlines.
7. tests/test_h1_executor_values.py — exact types,immutability,missing/known-error precedence and BPF.
8. tests/test_h1_executor_launch.py — pin/path/argv/FD/environment/mount logic and bounded actual observations.
9. tests/test_h1_executor_supervision.py — output/deadline/error/abort/descendant cleanup logic and observations.
10. tests/test_h1_executor_architecture.py — inert imports,no bridges,ten-path/old-byte preservation.

No installed package,CLI,pytest config modification,third-party dependency or general-purpose executor API.
Private helper structure and local variable names are builder-owned. Public interfaces below are fixed.

### Task 1: Closed immutable values and exact synthetic filter

**Files:**Create paths1,2,3,7.

**Interfaces:**
- Consumes:spec section7 exact SyntheticCase,request/result fields and outcome semantics;semantics.json S filter numbers and hash.
- Produces:SyntheticCase,SyntheticRequest,SyntheticResult;seccomp_bytes()->bytes.
- Result exposes fixed status='BLOCKED',permissions=the nine literal false values,content_identity_only=True,historical_execution=False. No general H evaluator or serialized authority.

- [ ] Write lazy-import RED tests `test_closed_request_values`, `test_fixed_blocked_results`, `test_invalid_or_forged_values`, `test_seccomp_exact_bytes`. Assert only the eight named enum values;invalid types/relative owner path raise ValueError;tuples are defensive;known errors outrank unavailable;complete requires no errors/unavailable and cleanup CONFIRMED. Pin BPF hash12e1d308af4e6ed61ae5beccc2c3d2fc3f89506e13215ad31965e97c6fe66901 (EP-001–003,014,021,025).
- [ ] Run `python -m pytest -q tests/test_h1_executor_values.py`. Expected:missing-module/interface assertion failures,not a malformed fixture or unrelated baseline failure.
- [ ] Implement exact frozen/slotted DTOs with revalidation;use explicit struct endianness for x86_64 BPF,architecture/x32 checks,registered errno denylist and default ALLOW. Do not name it a complete network/security/H policy.
- [ ] Run values tests,Ruff/format and strict mypy on new modules. Expected:green. Commit only these new paths;no old metadata/test edits.

### Task 2: Owned fixture launch and FD/mount boundary

**Files:**Create paths5,6,8;extend only new paths1,2,3 as needed. Task3 supplies supervision before actual successful effectful runs.

**Interfaces:**
- Consumes:Task1 types and filter;the exact tool pins and Python home in sources.json.
- Produces:run_synthetic(request:SyntheticRequest)->SyntheticResult in runner.py. Invalid request raises ValueError before effects;unavailable controls/pins yield UNAVAILABLE before payload.
- Calls Task3's internal `supervise(case:SyntheticCase,run_root:str)->SyntheticResult` only after exclusive root creation and pin/control checks. This internal interface is not exported by __init__.
- Fixture's `main(argv:tuple[str,...])->int` accepts only fixed internal case/sub-action names and owned scalar control identities,no source path or shell. Guard `if __name__ == '__main__'`.

- [ ] Write RED tests `test_required_controls_fail_closed`, `test_fresh_owned_roots_only`, `test_exact_launch_policy`, `test_no_public_fd_or_argv_override`, `test_guarded_credential_free_environment`. Assert unknown platform/hash/missing seal/pidfd/control=>UNAVAILABLE,payload not invoked;reused/symlink run root rejected;no old directory removed;no --try/shell/fallback/ambient PATH;close_fds=True and only sealed filter FD passed (EP-004–006,013,015,022).
- [ ] Run `python -m pytest -q tests/test_h1_executor_launch.py`. Expected:fail because runner/fixture/launch behavior is absent. Do not launch an incomplete unconfined implementation to make a negative test pass.
- [ ] Implement preconditions,owned0700mkdtemp and no-follow directory-handle operations,closed mount/argv expansion and sealed memfd. Use actual exact paths,not PATH discovery. Preserve provider guards;incompatible credential-free execution is UNAVAILABLE. No supervisor effects occur at import.
- [ ] Add RED→GREEN mocked launch tests for second unrelated FD,socket FD,FD-number reuse,filter FD not reaching payload,private unsafe-control non-exportability,and protected directory create/write/rename/unlink/link attempts. The private unsafe helper is confined to the test's newly owned file and explicitly reports EXPECTED_UNSAFE_CONTROL (EP-008–013).
- [ ] Prepare closed fixture cases,including descendant socket/write and guarded loopback control. All writes are bounded/new-owned;all fixtures self-deadline3seconds. Unit tests can collect without bwrap;actual missing controls must report UNAVAILABLE explicitly,never skip-as-observed-success (EP-007–010,015,022).
- [ ] Until Task3 exists,run only pure/mocked tests whose asserted result is prelaunch unavailable/rejected or mocked policy behavior. Do not claim real kernel isolation. After Task3,run actual bounded cases and preserve per-node logs externally. Commit this independently inspectable launch boundary.

### Task 3: Bounded supervision,observed effects and final handoff

**Files:**Create paths4,9,10;extend only other new paths as needed.

**Interfaces:**
- Consumes:Task1 types and Task2 owned root/closed fixture/tool pins.
- Produces:`supervise(case:SyntheticCase,run_root:str)->SyntheticResult` in supervision.py. Run root is the exclusively created validated directory,not caller source input.
- Dedicated helper may launch its own script path under exact Python -I -B -S,adding only this new sibling's trusted directory for imports. Freeze/check helper and fixture bytes before launch;no .pth/PYTHONPATH/site initialization. Internal helper protocol is versioned closed JSON with exact keys/types/byte limits;unknown/duplicate/nonfinite fields reject. Parent-supplied messages cannot contain argv,mounts or filters.

- [ ] Write RED tests `test_combined_output_cap`, `test_deadline_with_open_descendant_pipe`, `test_owned_pidfd_only_cleanup`, `test_abort_and_cleanup_failure`, `test_first_failure_survives_cleanup`. Assert combined65536byte retention,first excess triggers failure,wall checks independent of EOF,missing pidfd=>UNAVAILABLE,no arbitrary kill,and earlier nonzero error retained with CLEANUP_UNCONFIRMED (EP-016–021,023).
- [ ] Run `python -m pytest -q tests/test_h1_executor_supervision.py`. Expected:absent/unimplemented lifecycle failures with no unsafe workload started.
- [ ] Implement dedicated non-threaded subreaper helper,retained pidfds/owned unreaped process handles,monotonic selector loop,exact per-process rlimits and child launch. On error enforce owned group checks,kill/reap under2second cleanup deadline;controller wall+cleanup+2seconds bounds helper. Namespace parent-death handles setsid descendants;unobserved cleanup never becomes confirmed. No outer worker prctl/rlimit/seccomp/namespace mutation.
- [ ] RED→GREEN bounded tests for timeout setsid heartbeat,early child exit with pipe holder,65537byte stdout/stderr flood,nonzero exit plus later timeout,supervisor abort and mocked pidfd/reap failure. Actual helper-abort cleanup remains UNCONFIRMED unless independently observed. No long waits or fork bomb (EP-016–023).
- [ ] Write architecture RED→GREEN tests for inert first import,no product/application/owner/H1/C1 bridge,no CLI,ten literal new paths,unchanged old source/ZIP/config bytes,and no historical command code path. Assert all result paths BLOCKED/all9false (EP-002,024–026).
- [ ] Run `python -m pytest -q`;then `python -m pytest --cov=tests.audit_compatibility_executor --cov-branch --cov-report=json:<NEW_EXTERNAL>/coverage.json tests/test_h1_executor_values.py tests/test_h1_executor_launch.py tests/test_h1_executor_supervision.py tests/test_h1_executor_architecture.py`. Expected:all2279baseline plus new tests green;new statements>=98%,branches>=95%;missing actual controls explicitly listed,not counted as passed host observations (EP-027–028).
- [ ] Run `python -m ruff check .`, `python -m ruff format --check .`, `python -m mypy`, and strict mypy for new sibling. Map all30EP IDs to actual nodes/outcomes externally;distinguish mocks/current regression/host observations. Preserve old controls/floors and raw failed attempts;do not update registration cases to hide omissions.
- [ ] Verify outer security state,prior refs/worktrees/evidence and source byte equality. Fresh exact-head independent review targets inherited FD bypass,pidfd/group races,output floods,misreported cleanup,secrets and H qualification overclaim. Fix Important/Critical findings with RED→GREEN evidence and full rerun;report final-review exact head honestly (EP-029–030).
- [ ] Keep local branch/worktree/evidence;no push/PR/merge or real H follow-on. Report synthetic observations only,all9false and every real-H prerequisite still unavailable. Do not reuse this as a historical runner.

## Self-review

Spec1–3/8→Task3architecture/report and retained blockers;spec4–5→Task2;
spec6→Task3;spec7→Task1public contract and Tasks2–3closed effects.
All ten paths and shared signatures agree. Every Review Focus has named tests.
Full H syscall policy,aggregate resource provider,historical preparation/closure,
trust/custody and ENTRY adoption are deliberately not implemented by this plan.
No test success or this plan's existence resolves them. Native execution is the
recommended later method because the three tasks share strict local interfaces;
this design handoff itself does not begin that execution.
