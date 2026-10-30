# Independent whole-branch review

Exact base74e3fdc67c2695a48035bf51758721f48bd5ae05 →
head058738163e90436045c617069d1795487d2be57f. Fresh gpt-6-astra/high read-only
reviewer, one review, no guest/native/host-ELF execution or remote writes.

## Strengths

Actual target fdinfo flags, actual proc exe/object binding, stopped target returned
buffer capture, empty vs unavailable inventory, pin release after actual reap,
HH04 entry gate, explicit HH05/06 fault injection, strict physical LF and shared
parser. Scope and permissions remain BLOCKED/all9false; old runtime untouched.

## Findings — C0 / I2 / M1 at reviewed head

I1: guest/probe.c146/153/265. HH02 compares against selected alternate and forces
mismatch by comparing the selected expected object to itself. HH02/03 deny by
case number, ignoring the observed snapshot result except errors. Published
witnesses really contain the violations, but live causation is not established.
Compare authorized primary/actual inventory and gate on actual violation. Show
that correcting those injections removes the corresponding live denial.

I2: model.py245/249/387/397. Comparison result/error and OFD_PIN validated
independently. Equality before any reference, equality after failed acquisition,
and KCMP_FILE999 for reusedFD0 are accepted. Validate per-FD pin lifecycle;
unattempted state before reference, propagate actual pin error if acquisition
failed, allow real kcmp/error after success, known result domain0/1/2 only.

M1 (deferred): guest/probe.c169/model.py421/contract84. DENY always reportsFD0;
HH03's extra descriptor isFD3. Correct reason/inventory and denial remain, but the
documented attempted/rejected FD field is wrong. No qualification escalation;
retained as a diagnostic metadata defect, not promoted to an Important to fix it.

## Reviewer verification

Full spec/plan/ledger/rulings and all15 changed files read. Focused70 pass;
actual original7 captures/138events/2scoped transports/5denials replayed. Source
8files/12ranges, authenticated package/archive hashes and all7 saved image/ELF/
init/scope/serial artifacts independently match. Four in-memory OFD contradiction
reproductions. Author full2748/coverage/ruff/mypy/wheel/native192 inspected, not
independently repeated. HEAD/index/tree remained unchanged and clean.

## Declined to judge (exhaustive)

1. Fresh guest execution reproducibility: execution excluded in read-only review;
   archived captures/images inspected and replayed.
2. Independent exact-head CI and CRLF: separate handoff gates.
3. Qualified FD-table/OFD observation, continuous closure, loss completeness,
   security-boundary enforcement, real-build/vehicle readiness: expressly not
   established by prototype.

Verdict: request changes for I1/I2. Author regrading agrees: both Important, M1
Minor/deferred. One author RED→GREEN fix pass and full rerun; no second review
and no independently clean fix-head C0/I0 claim.

## Author fix verification (not a second independent review)

I1: two additional fixed corrected-injection cases HH08/09, same original case2/3
branches. Actual pre-fix serial confirms authorized primary/onlyFD0 yet the old
gate denies; both RED. New gate compares authorized primary and observed inventory
mismatch; both actual cases reach exec/READY/full read after the fix. Original
HH02/03 violations still deny. No arbitrary command/profile entrypoint added.

I2: seven RED OFD regressions across positive/negative paths, GREEN after reference
lifecycle/error propagation and known KCMP_FILE0/1/2 domain checks. No generic OFD
identity/generation inference added.

Single author fix pass:9 actual captures,185events,4 scoped transports/5 expected
denials; full2757 passed34.50s; pure211/213stmt99.06%,58/58branch100%; no exclusions.
Final exact-head CRLF/CI and source aggregate/wheel/history rerun checkpoints are
recorded separately. M1 remains explicitly deferred, not silently fixed.
