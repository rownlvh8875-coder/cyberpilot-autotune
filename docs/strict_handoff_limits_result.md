# PR33 opt-in strict handoff limits gate

STRICT_HANDOFF_ENTRYPOINT_IMPLEMENTED
STRICT_HANDOFF_SYNTHETIC_VALIDATION_READY
LEGACY_CALLERS_UNMIGRATED
PR33_FINDING_OPEN

Approved spec: `docs/superpowers/specs/2026-10-31-history-preserving-strict-input-design.md`.
Executed plan: `docs/superpowers/plans/2026-10-31-strict-handoff-limits.md`.
Actual branch basec477cfc1b30578165405b6cbb3af26b7334064e5 (PR51);
branch `feat/strict-handoff-limits`. Only five new files are added; every prior
tracked blob, fixture, source/evidence manifest, guard, CI file and historical
document/plan remains unchanged. Completion is recorded here and in the own
Draft handoff, not by editing old unchecked design-plan snapshots or old PRs.

## Explicit object-validation boundary

`tests/strict_handoff/validation.py` exposes
`validate_schema_strict(data: Any) -> None` and
`VALIDATOR_PROFILE="handoff-limit-exact-int-strict-v1"`.
This profile identifies validation, not evidence version, runtime acceptance,
an authorization grant or a new source/schema/producer qualification.

Require exact built-in dict root/limits, exactly the four literal string keys,
and exact built-in int values: members16, bytes_per_member4096, events1024,
json_bytes2097152. Reject float including equal decimal/exponent values, Bool,
None, str, subclasses, equality-spoof mappings/values/keys, wrong integer and
missing/extra/renamed keys. Non-string/str-subclass keys inside an exact dict
are rejected before any equality comparison against literal keys is needed.
Invalid limit envelopes/types/values raise exact
ValueError("EXACT_INTEGER_LIMITS_REQUIRED"). Constants are an immutable tuple;
there is no coercion, default, input repair, mutation, fallback or registration.

After limit checks, call **the complete unchanged** legacy validate_schema.
All other schema/scope/clock/encoding/transport, type/unit/stage/proof and each
permission check remains effective, with original errors propagated. Valid
input returns None; that is structural consistency only, not a qualified graph.
The existing semantic schema remains guest-input-handoff-semantic-design-v2
and SYNTHETIC; there is no v1/v2 promotion, capture relabeling or runtime decoder.

This is **not raw JSON parsing**. Existing load("schema") keeps its duplicate-key,
nonfinite and2MiB gates. Tests exercise the actual frozen loader using exclusively
owned synthetic pytest files and a temporary ROOT substitution restored by the
fixture. The new facade never calls load/validate/main/source-inspection or file,
process, thread or network functions. Importing the frozen audit module does not
turn its existing CLI capabilities into newly implemented pure-runtime tooling.
A permissive decoder can lose duplicate keys before this object API sees them:
the resulting otherwise-valid dict can pass. That limitation is explicitly tested,
not represented as raw-input authenticity or complete lexical validation.

## Verification observed before final handoff

- Baseline4066PASS38.68s; all four old float-equal admissions directly reproduced.
- Test-first RED: absent tests.strict_handoff API; minimal implementation GREEN:
  129focusedPASS0.30s (127behavior +2architecture), no skip-based success.
- Full existing/new regressions4195PASS38.25s.
- New facade19/19statements and12/12branches,100/100, no missing paths.
- Old handoff audit66syntheticcases/6consistent/7sourcefiles/11ranges, overallBLOCKED;
  runtime_producer_implemented/runtime_qualified and all permissions remain false.
- ruff/format, installed-source71mypy +newfacade1mypy, build PASS. Fresh wheel
  excludes tests and its72package files exactly match base Git bytes. Fresh
  exclusive vanilla wheel imports all modules with no tests or NumPy dependency.
- History/import/call guards cover every prior tracked blob and restrict the new
  facade to typing plus the exact legacy validate_schema entrypoint. Tests check
  both successful/rejected inputs remain unchanged, including float/None/False/0
  representation and limits-object identity; dictionary equality alone is not
  treated as proof of type preservation.
- Final exact-head rerun, fresh-context internal review and Linux/Windows push/PR
  CI results are recorded in the own Draft after actual execution. Internal AI
  review is not registered GitHub approval or independent human authorization.

These Python tests do not establish runtime, kernel, executor, containment,
adversarial-host, concurrency, resource-exhaustion or real-device guarantees.
Existing native regression units are not reclassified as new runtime qualification.

## Unchanged limitations and next decision

Original validate_schema still accepts float-equal metadata; the regression
explicitly characterizes it. Existing callers are not migrated/rebound and the
original PR33 finding remains OPEN until separately reviewed adoption and history
constraints are resolved. PR25's strict facade is preserved, not newly adopted;
PR25/34/9 and all inherited findings remain open/unresolved as previously recorded.

All source/build-closure, lifetime/publication/concurrency/all-writer/copy-cut,
loss/perturbation, empirical, fingerprint, watchdog, executor and application
blockers remain. APPLICATION_NOT_AUTHORIZED; runtime_accepted,
candidate_generation_allowed, application_authorized and owner_proposal_allowed
remain false. No Params/controller/cereal/schema deployment, new kernel build,
guest/driver/device/vehicle execution, estimator/candidate/application/owner bridge,
old PR edit/Ready/retarget/merge/rebase/force/shared push or upstream PR.

Next single recommendation: read-only inventory of PR25/PR33 callers and review
the exact adoption/history-guard boundary. No caller transition or guard exception
is started or authorized by this implementation.
