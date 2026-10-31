# History-preserving strict-input corrections — design only

## Intent and boundary

Design explicit, repository-only strict validation entrypoints for the PR25
Unicode/digest inconsistency and PR33 float-equal limit metadata. This is a
design and two independently executable future plans, **not an implementation**,
legacy repair, caller migration, merge approval or runtime qualification.

Frozen source base: `1d3c7622603ad402e4f5d1ddb23a77f4d267a6b4` (PR49).
Main remains `a5d3514f23797829eb58d08c638b22cf4dd30c8a`.
PR25 head `3b1342f3e131642c6edbe3b18270a1fe1e7d216b`;
PR33 head `74e3fdc67c2695a48035bf51758721f48bd5ae05`.
This branch changes only new Markdown documents. All old tracked blobs,
source/hash manifests, fixtures, CI, runtime packages and PRs remain unchanged.

## Reproduced causes

PR25 `compatibility/native_containment/contracts.py`: `_text` checks exact str
and nonempty only (37–39); `parse_synthetic_case` can therefore return a case
whose label contains U+D800 or U+DFFF. `canonical_digest` uses sorted compact
JSON with `ensure_ascii=False`, then strict UTF8 (220–228), raising
`UnicodeEncodeError`. That is already a ValueError subclass and fail-closed;
this is inconsistent parse/digest admission, **not evidence of authority bypass**.

PR33 `tests/audit/validate_guest_input_handoff_design.py:176–179`: dictionary
equality accepts float values equal to the four integer constants. Actual
reproduction accepted4096.0/1024.0/2097152.0/16.0 individually. True/None/15/"16"
for members were already rejected. Do not change their existing rejection.

## Approaches and author-selected choice

| Approach | Benefit | Cost / decision |
| --- | --- | --- |
| Edit original validators and narrowly amend history guards | Repairs original calls | Changes frozen source/guards; outside this task's permission |
| Copy/relabel schemas as new evidence versions | Independent implementation | Duplicates semantics and risks v1/v2 evidence promotion; rejected |
| Add explicit test-only strict facades over unchanged validators | Preserves exact history and existing semantics | Selected; old callers stay legacy and findings cannot be called closed |

Important placement constraint: `test_guest_input_handoff_boundary.py` compares
whole `src`, `compatibility`, `.github`, `tests/fixtures` subtrees to PR32 base
`0652c87c5e1da83d2cf4a3336713b9839e929ae3`. Even **new** files under compatibility
violate that guard. Later guards freeze old test/evidence blobs too. Thus use
new `tests/strict_containment` and `tests/strict_handoff` prefixes, not a runtime
package, monkeypatch, replacement module, new fixture directory or guard exception.

## PR25 future contract

Create `tests/strict_containment/{__init__,validation}.py`, outside the wheel.
`VALIDATOR_PROFILE = "containment-scalar-utf8-strict-v1"` identifies the validator
only; input schema stays `synthetic-native-containment-case-v1` and evidence
stays SYNTHETIC. Return existing immutable types, not a newly qualified receipt.

Public signatures in validation.py:

- `parse_case_strict(raw: str) -> SyntheticContainmentCase`
- `digest_case_strict(case: SyntheticContainmentCase) -> str`
- `evaluate_case_strict(case: SyntheticContainmentCase, policy: SyntheticPolicyContext) -> SyntheticContainmentDecision`

`digest_case_strict` calls the unchanged `canonical_digest`; only
UnicodeEncodeError is normalized to exact `ValueError("INVALID_UNICODE_SCALAR")`
without echoing input. All other old errors propagate. `parse_case_strict` uses
unchanged `parse_synthetic_case`, then calls strict digest **before returning**.
`evaluate_case_strict` validates via strict digest before unchanged
`evaluate_synthetic`; a rejected strict input never falls back to legacy success.
Directly constructed/forged nested cases are revalidated by the existing digest.

Reject any remaining U+D800–U+DFFF codepoint, including a Python string containing
two literal surrogate codepoints. Accept a JSON escaped valid surrogate pair
that JSON decoding combines to a non-BMP scalar. Valid ASCII, Hangul, non-BMP,
control characters and noncharacters keep old behavior; there is no new path or
label authorization policy. No Unicode normalization, ASCII conversion,
replacement/surrogatepass, integer coercion or alternate JSON digest encoding.
For every valid case, digest and decision equal the legacy result bit-for-bit;
NFC and NFD remain distinct content where they were distinct before.

All text-bearing fields are covered through canonicalization, not just actor_id.
Nested optional labels/flag strings and direct dataclass construction must be
tested. Legacy duplicate-key/nonfinite/unknown-key/UInt64/None/permission
rejections and deterministic reason order remain in force.

## PR33 future contract

Create `tests/strict_handoff/{__init__,validation}.py`, outside the wheel.
`VALIDATOR_PROFILE = "handoff-limit-exact-int-strict-v1"` does not change the
`guest-input-handoff-semantic-design-v2` input schema or synthetic graph version.

Public signature: `validate_schema_strict(data: Any) -> None`.
Require exact dict root and exact dict limits, exactly the four literal keys,
and `type(value) is int` with these exact values:

| key | value |
| --- | ---: |
| members | 16 |
| bytes_per_member | 4096 |
| events | 1024 |
| json_bytes | 2097152 |

Bad limit shape/type/value raises exact `ValueError("EXACT_INTEGER_LIMITS_REQUIRED")`.
Then call unchanged `validate_schema(data)` to enforce **all** other requirements.
Do not mutate/copy-repair data, coerce with int(), relax limits, accept dict/int
subclasses, or skip legacy validation. Changes outside limits retain old errors.
This is an object API, **not a raw-JSON decoder**: retain the existing published
`load("schema")` duplicate-key/nonfinite/size gates. Never claim this facade can
recover duplicate keys already lost by a permissive caller's JSON decoder.

## Test and adoption acceptance

Two separate plans own their code and RED→GREEN tests. Both require full existing
regressions, unchanged old-blob guards, pure/import boundaries and new test-module
coverage statement>=98%, branch>=95% (target100/100), without reducing existing
gates. Run Linux and Windows CI; no native/guest/vehicle test is needed to prove
these Python input semantics. A passing test is not runtime qualification.

Selected future callers must explicitly import strict functions and record the
validator profile at their test/audit invocation boundary. No implicit import
replacement, legacy name rebinding, global registration or fallback. Implementing
these facades alone does **not** fix original APIs, migrate old callers, qualify
old captures, authorize a merge or change old PR source. A later separately
reviewed adoption decision must inventory exact callers and address the history
constraint before claiming PR25/PR33 findings closed. No adoption implementation
or history-guard modification is authorized by these plans.

## Status / non-goals

`STRICT_INPUT_CORRECTION_DESIGN_READY` (subject to final design review)
`STRICT_CONTAINMENT_ENTRYPOINT_NOT_IMPLEMENTED`
`STRICT_HANDOFF_ENTRYPOINT_NOT_IMPLEMENTED`
`LEGACY_CALLERS_UNMIGRATED` / `PR25_PR33_FINDINGS_OPEN`

PR34 DENY-FD provenance and PR9 evidence-expiry policy remain unresolved. All
prior source/build-closure, lifetime/publication/concurrency/all-writer/copy-cut,
loss/perturbation, empirical, fingerprint, watchdog and external-executor blockers
remain. APPLICATION_NOT_AUTHORIZED; runtime_accepted, candidate_generation_allowed,
application_authorized and owner_proposal_allowed remain false. No Params,
controller/cereal/schema deployment, new kernel build/guest/driver/device/vehicle
execution, estimator/application/owner bridge, source/evidence promotion, upstream
PR, old PR edit/Ready/retarget/merge/rebase/force/shared push. Internal review
is not a GitHub approval or independent human authorization.
