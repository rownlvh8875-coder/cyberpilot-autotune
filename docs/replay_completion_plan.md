# Replay completion implementation plan

> Execute inline with test-driven-development and verification-before-completion.
> User explicitly authorized PR #2 merge, PR #3 retarget and only this replay scope.

## Dependency evidence

PR #2 exact head 26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0 had 8 successful CI
checks, no reviews/threads, mergeable=true and main base. Ready transition preserved
head. Merged at 2026-10-28T00:52:04Z with merge_method=merge, no bypass/auto-merge.
Merge/main SHA: fd8c60c111a6e25443f26093f424b8be0a605940. Parents:
05b016237afec7c53195cb802bef2c3ae8138a8c and
26e83f9a5af23b2c9cb93aeb3ddae8f1189c0df0. Ancestor command exited 0.
Branch retained. PR #3 retargeted from feat/shadow-residual-statistics to main,
OPEN/Draft, exact unchanged head 950019643bab050f3cbafeddd1c926913ea1840a.
Mergeability briefly pending then true. Retarget diff: 25 files, 6 commits,
2278 additions/49 deletions; no Phase 5/admission implementation duplicated.
The retained file list is in replay_progress.md and the original six commits remain.

## Constraints and design

- Append only on feat/deterministic-replay; never merge/ready PR #3. No new branch,
  rebase, amend, force push, engine/gate/learner algorithm edits or reference edits.
- Python >=3.12.3,<3.13; standard-library runtime. Persistence NOT_AUTHORIZED.
  No real logs, adapters, controller writes, Apply, vehicle values or live tests.
- Schema validates shape/numbers/units/domain and monotonic evaluation clocks;
  repeated/regressed observation sequence/capture times reach engine admission.
- Independent replay checker maintains sequence and clock-safe timestamp maxima,
  including rejected frames, and checks eligible ordering against previous maxima.
- Preserve aggregate fixture bytes and result digest. ReplayReport deterministic
  v1 bytes stay unchanged. Add scenario/config/result SHA-256 properties; digest
  aliases result_sha256. No self-reference or timer in hashed projections.
- Capture learner sample counts as a separate characterization sidecar from the
  same run, using the existing statistics property. Do not change ReplayReport's
  historical deterministic projection. CLI expected checks cover sidecar directly.
- CLI is the sole package file-IO boundary; bounded read only, no golden updates.
  run emits canonical UTF-8 JSON plus LF, no latency. verify compares exact legacy
  or full expected semantic projections, including metrics/reasons and focused
  event sample counts. verify-all sorts *_v1.json and excludes *.expected.json.
- Exit codes 0 success; 2 invalid input/schema; 3 expected mismatch; 4 invariant/
  internal replay failure; 5 typed unsupported configuration. No raw error/input
  or file paths in errors. Library constructors retain typed visible errors.

## Review focus

Lossy clocks remain rejected; lower sequence/high safe timestamp must advance only
the time maximum; future capture must not poison time; hashes must bind policy and
outputs while retaining aggregate compatibility; CLI must validate expected field
sets and types so altered/unknown expectations cannot silently pass; CLI import is
inert and file writes/network/threads remain unavailable.

## Tasks

- [x] Schema/order: RED admit duplicate/regressed sequences/times, engine rejection,
  corrected-frame replay and high-water effects. Implement schema relaxation and
  independent maxima only. Existing invalid/clock-domain tests stay green. Full
  regression before atomic commit. Files: replay/schema.py, runner.py, replay tests.
- [x] Digest/characterization: RED formatting/input/policy/output/timer/self-exclusion
  and per-event learner sample counts. Add three properties and characterize_replay
  returning (ReplayReport, immutable sample-count tuple) from one shared executor.
  Keep aggregate digest. Full regression and commit.
- [x] CLI: RED run/verify/verify-all, exits 0/2/3/4/5, strict expected matching,
  stable redacted errors, sorted discovery and canonical bytes. Implement cli.py
  and typed unsupported schema errors; no IO in core. Full regression and commit.
- [x] Focused goldens: hand-derive constant, admission/reset and ordering stream
  metrics/event sample counts; verify before pinning new hashes. Keep historical
  aggregate bytes. Two fresh processes/hash seeds per fixture; full regression.
- [x] CI/docs: preserve matrix, overall coverage >=90%, package floors >=95%, CLI
  verify-all, installed-wheel CLI and fresh-process comparisons. Update schema,
  acceptance/high-water docs and evidence, build and isolated wheel validation.
- [x] One independent read-only review; reproduce and fix concrete findings.
- [x] Append commits/push, keep PR #3 Draft; verify final push/PR CI, clean tree,
  unchanged engine/gate/learner and historical aggregate. Stop after report.
