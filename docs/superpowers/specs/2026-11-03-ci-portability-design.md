# CI portability repair

## Intent and constraints

Repair the exact-head push CI failures at `ce138c503ff320a2a6956ceff3d8735418b72bcc` without weakening capture admission or frozen-byte checks. The user delegated implementation choices and approved this next repair. This is test infrastructure, not runtime qualification.

Keep product code, `tests/audit_compatibility*` implementation packages, all existing workflow bytes, collector bytes, K1 source bytes and all qualification permissions unchanged. Do not skip additional tests, normalize bytes before comparison, accept helpers, alter host configuration, change HOME, or relax any coverage floor. No main merge, force-push, PR #8/#9 change, manual dispatch, vehicle, Params, controller, schema or application work.

## Approaches

The implementer's choice is a test-only synthetic configuration scope, plus one narrow LF checkout rule. Permitting runner helpers in the actual reader would violate fail-closed semantics. A privileged mount/container fixture is disproportionate and adds an execution dependency. Host-wide config removal would mutate the runner and conceal a real influence. Neither is selected.

## Design

- Existing native capture fixtures use three empty private files representing system, user and XDG configuration. Five native capture test modules explicitly import this pytest fixture; no global plugin or shared conftest change. The real reader still parses every declared file and rejects helper, include, attribute and cohort faults.
- A context manager in `tests/fixtures/audit_compatibility_capture.py` temporarily substitutes only configuration-source discovery; it restores discovery on success and exception. The request builder consumes that discovery. No reader implementation changes.
- Synthetic repository setup Git commands ignore ambient system/global configuration in their child environment only. They retain inherited proxy, CA, authentication and guard variables; no process-global HOME/config or real repository configuration is changed.
- The fresh-child read-only architecture test explicitly adopts the same synthetic scope before its existing audit guard. It remains a synthetic native fixture and cannot establish actual system configuration provenance.
- Append `tests/audit_compatibility/*.py text eol=lf` to `.gitattributes`. Preserve K1 bytes and direct raw byte equality. Exercise a fresh checkout with `core.autocrlf=true`; do not equate this local simulation to actual Windows CI.
- Freeze the old registration range at exact `ce138c5`. Preserve its literal inventory and previous history guards. Add a separate literal inventory for this repair. The evidence manifest describes scope; it cannot authorize extra files or execution.

## Acceptance and handoff

Observe regression RED before implementation, then full pytest, unchanged security/canary cases, Ruff/format, mypy, source audits, coverage and wheel checks. Use a fresh independent reviewer at the committed head. A normal fast-forward update of this feature branch and its automatic push CI may verify actual hosted Linux/Windows only after review; no manual dispatch or merge. If publication requires new authority or remote drift appears, stop and report it. Retain evidence externally; all existing blockers and nine false permissions remain.

## Development incident and publication hold

An expanded RED test initially omitted private-path validation before writing a canary configuration. It attempted actual host paths: the system path denied access, the XDG parent was absent, and the user path received synthetic helper bytes. A subsequent setup Git invocation created the helper's zero-byte test marker inside the verification archive. The known synthetic user file was content/type/owner checked and moved recoverably into that archive. Pre-test user-config contents were not captured, so exact restoration is not established. Do not claim host-config preservation. The regression now verifies resolved private paths before every canary write, and setup Git is child-config-isolated. Local verification/review may proceed; publication is held pending environment recovery/verification. No credential contents are exposed or guessed for recovery.

## Follow-up: source checkout normalization

Base: `3fc532d5c2634e716401701278cb45b49dbea3ac`. Its hosted Windows run exposed two false scope failures: synthetic setup Git neutralizes the system/global EOL configuration that was used to materialize the actual source checkout. Applying that helper to source metadata makes CRLF checkout bytes appear modified.

The delegated implementation choice is a separate module-local `source_git(*args) -> bytes` for the existing trusted source-metadata call sites. It inherits the checkout configuration and authentication/proxy/CA environment, adding only no-lazy-fetch/no-optional-lock guards. It is not a general hostile-command sandbox or runtime capture interface. Synthetic repository setup continues using the unchanged neutral helper. Rewriting all files or attributes, ignoring reported modifications, and weakening raw K1 equality are rejected alternatives.

Only the portability test module and this existing spec/plan may change relative to this base. The original 4-addition/8-modification ceiling and every older frozen range remain intact. A stricter follow-up inventory pins the three modified paths. Regressions must exercise a fresh LF-index/CRLF-worktree with controlled temporary configuration, detect actual content changes and untracked files, and prove real consumers do not route source metadata through synthetic setup. All fixture writes stay under pytest-owned paths; no host configuration/HOME writes.

The earlier publication hold remains historical evidence. The user subsequently adopted the verified current Git configuration as a new forward-working baseline and authorized publication of `3fc532d`; its hosted CI passed diagnostic/source/schema checks but failed the two scope tests. Original host-config equality is still unconfirmed. This follow-up retains that record and all project blockers/false permissions, requires fresh exact-head review, and verifies only automatic push CI on the same feature branch. No main merge, PR creation, manual dispatch or force-push.
