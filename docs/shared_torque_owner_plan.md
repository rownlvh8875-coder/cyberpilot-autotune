# H4 execution plan and ledger

Spec: user Phase H4 master prompt, supplied 2026-10-29. H4 authorizes a pure
vehicle-independent reference protocol, not a Carrot writer or application.

PR #12 was verified Open/Draft/MERGEABLE at 040b6500aeef47d486cf11895c1bca1b1b8e2282,
with successful push and PR CI, no review threads and fresh independent C0/I0/M0.
Ready + guarded merge-commit completed at 2026-10-29T04:54:31Z.
H4 base/main: b0de6b4032d587c818f3d47389ae1afc37f2009c.
Parents: 66f4b79036560a11e7020af9cc214118dcbd4fba and
040b6500aeef47d486cf11895c1bca1b1b8e2282. H3 ancestor and merge/head tree equality verified.
Current carrot-wip remains f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3.
PR #8/#9 remain unchanged; #8 conflict is future maintenance, not an H4 blocker.

## Tasks

- [x] Specify immutable contracts and failing owner/CAS/replay tests.
- [x] Implement pure contracts, in-memory port and deterministic reference owner.
- [x] Exercise independent readback, uncertain commits, recovery, mode/lease,
  process shutdown and property/architecture/PR9 compatibility invariants.
- [x] Complete six design documents and contract evidence, retaining all H3 gates.
- [x] Run full regression, source validators, coverage, build, fresh wheel/goldens.
- [ ] Fresh final-head independent review; fix C/I with RED regression and re-review.
- [ ] Publish append-only commits and Draft PR; verify final exact-head CI.

## Design rulings

- The earlier design-only sketch was preserved outside the checkout under /tmp.
  H4 explicitly supersedes it: reference model implementation is now authorized.
- Logical tuples retain finite Python float representations exactly, including
  signed-zero identity. No Float32 encoding policy or scientific conversion is
  adopted; REPRESENTATION_ENCODING_UNRESOLVED remains a native-adapter gate.
- One-shot proposal IDs encode a producer sequence. Bounded per-producer high-water
  state prevents replay without an unbounded ID cache or duplicate PR9 algorithm.
  This is a local reference admission boundary; future adapter mapping must bind
  PR9's session sequence rather than invent an independent replay lane.

Results and remaining decisions are appended as work completes. No next task
starts automatically after H4.

Reference RED/GREEN observations include missing package, cross-producer lease
replacement, repeated lease recovery, post-install clock fault, mode/Ack state,
expiry during mode authorization, final timing checks and explicit restart.
All were reproduced before correction. No Float32 encoding or parameter equation
was introduced. Current owner-only suite passes with combined coverage >98%.

H1/H2/H3 architecture tests are narrowly extended to permit owner_protocol as a
new isolated namespace while preserving every original production/replay hash.
Existing runtime, integration, application and knowledge source bytes stay frozen.
CI adds an explicit owner_protocol >=98% coverage report to existing coverage runs.

## Local verification before final review

- Full regression: 993 passed; overall coverage 97.55%. Owner protocol coverage
  99.04% combined statements/branches; all seven lifecycle states exercised.
- Targeted protocol/property/architecture/evidence suites include RED/GREEN
  regressions for identity collisions, context-loss recovery bypass and active
  proposal-age expiry in addition to the timing/mode/lease failures above.
- H2 exact source verification 39 files / 78 claims / 27 descriptors, H3 55 files /
  95 claims, and the existing metadata validators pass. H3 manifests are unchanged.
- Ruff/format and strict mypy pass; build produces wheel/sdist. Fresh isolated
  wheel exercises actual owner CAS/readback/rollback/stop, knowledge profiles,
  optional dependency failure and four unchanged replay goldens.
- No missing local links across the seven H4 documents. Production preservation
  checks retain all pre-H4 source bytes outside the new owner_protocol namespace.

Final exact-head CI, independent review findings/fixes and PR URL are recorded in
the Draft PR and final report after the immutable implementation/design commits.

## Independent review correction

Initial independent review of 8559ed68b94f036226ef7529647121a74e1ba999:
Critical 0 / Important 2 / Minor 0. RED regressions reproduced both findings:
old lease expiry crossed at the final pre/post-CAS/final-return clocks could be
masked by a new lease, and mode's last clock omitted the transaction duration.

Correction checks the old lease at every forward install/return boundary while
allowing explicit baseline recovery after expiry; it retains the expiry fault
even when pre-install rejection is followed by direct recovery. Mode's final
clock checks both duration and grant expiry. Four adversarial timing cases plus
the sticky-recovery assertion passed after their observed failures. Full-suite
and fresh final-head review results are reported after the correction commit.
