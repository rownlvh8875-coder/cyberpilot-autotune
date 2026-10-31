# PR25 opt-in strict containment input gate

STRICT_CONTAINMENT_ENTRYPOINT_IMPLEMENTED
STRICT_CONTAINMENT_SYNTHETIC_VALIDATION_READY
LEGACY_CALLERS_UNMIGRATED
PR25_FINDING_OPEN

Approved design: `docs/superpowers/specs/2026-10-31-history-preserving-strict-input-design.md`.
Executed plan: `docs/superpowers/plans/2026-10-31-strict-containment-input.md`.
Actual branch base0095e64fbe8cf9815e14226f527bf654315a12dc (PR50);
branch `feat/strict-containment-input`. Every pre-existing tracked blob is
preserved, including the historical unchecked design-plan snapshot. Execution
evidence lives in this new result and the own Draft handoff, not an old PR edit.

## Implemented boundary

`tests/strict_containment/validation.py` exposes only:

- `parse_case_strict(raw)`: unchanged legacy parse, then strict digest before return.
- `digest_case_strict(case)`: unchanged canonical digest; only UnicodeEncodeError
  becomes exact ValueError("INVALID_UNICODE_SCALAR") with suppressed exception
  display context and no input in the error message. This is not a hostile-host
  sandbox or erasure of objects accessible to the caller.
- `evaluate_case_strict(case, policy)`: strict digest, then unchanged synthetic
  evaluator. Invalid scalar input cannot fall back to legacy evaluation success.

`VALIDATOR_PROFILE="containment-scalar-utf8-strict-v1"` identifies validation,
not a new evidence schema, authority or source qualification. Returned objects
are existing immutable synthetic types. Input remains
`synthetic-native-containment-case-v1`; no v1→v2 upgrade or capture relabeling.

Nested actor/optional endpoint/errno/each flag and directly replaced/forged
synthetic cases are checked. Lone high/low surrogates and literal Python
surrogate-pair content reject; a valid JSON escaped pair decoded into U+1F600
passes. ASCII/Hangul/non-BMP/scalar boundaries/control/noncharacter labels keep
legacy behavior, not filesystem authorization. No normalization, replacement,
surrogatepass, ASCII digest rewrite, coercion, new threshold or weakened check.
Five literal digest goldens include distinct NFC/NFD content, and equal parsed
content preserves digests across JSON key order and escape spelling.

Duplicate-key/nonfinite/unknown/missing-key/UInt64 type and permission rejections
propagate unchanged. Valid decisions are compared in full across both policy
modes, each false/unknown modeled proof, real zero versus unknown counts,
nonzero counts and unavailable backend. All four permissions and runtime
qualification remain false. There is no collector, I/O, process, network,
thread, application/owner dependency, global registration or new runtime API.

## Verification

- Before implementation: baseline3944PASS38.15s; original nested surrogate
  parse-accept/digest-reject behavior independently reproduced.
- RED: missing tests.strict_containment module/API, before implementation;
  GREEN:122focusedPASS0.32s (120behavior +2architecture).
- Full existing/new regressions:4066PASS38.51s.
- Isolated new-facade coverage:15/15statements,100%; coverage.py reports zero
  branch arcs (N/A, not a fabricated branch100/100). Normal and exception paths
  are both exercised by actual tests. No artificial branches added for metrics.
- Original containment unit/adversarial/architecture224PASS0.36s; there is no
  separate containment-audit CLI. Existing handoff audit remains66syntheticcases,
  6consistent,7pinnedfiles/11ranges, overallBLOCKED, runtime/permissions false.
- ruff/format644files/mypy71sourcefiles/buildPASS; new wheel has no tests package
  and all72installed package files exactly match the base Git bytes. Fresh
  exclusive vanilla wheel imports all modules without tests or NumPy. Exact-head
  full rerun, internal review and platform CI are
  recorded in the own Draft handoff after actual execution.

Guards preserve all baseline blobs and restrict the new facade to the two exact
neutral legacy imports and pure calls. Existing history/acceptance gates are
unchanged. Python coverage and structural guards are not kernel/runtime evidence
or a proof against an adversarial interpreter/host. Internal fresh-context AI
review is not registered GitHub approval or independent human authorization.

## Retained limitations

The old parse still accepts unencodable surrogate labels and old digest/evaluate
still reject with UnicodeEncodeError; this is explicitly characterized, not
patched or hidden. Only explicit new imports use the strict facade. Existing
callers are unmigrated and the original PR25 finding stays OPEN pending separately
reviewed adoption and the history constraint. PR33 strict handoff remains
NOT_IMPLEMENTED; PR33/34/9 findings and all previous source/build-closure,
lifetime/publication/concurrency/all-writer/copy-cut/loss/perturbation/empirical/
fingerprint/watchdog/executor/application blockers remain. APPLICATION_NOT_AUTHORIZED.

No src/compatibility/fixtures/CI/evidence/old test or document changes; no original
PR edit/Ready/retarget/merge/rebase/force/shared push. No new kernel build,
guest/driver/device/vehicle/Params/controller/schema deployment, estimator,
candidate/application/owner bridge or upstream PR. Existing native regression
units are not reclassified as new runtime qualification.

Next single recommendation: implement the already-designed PR33 strict-handoff
limits facade. Not started by this task; caller adoption remains separate.
