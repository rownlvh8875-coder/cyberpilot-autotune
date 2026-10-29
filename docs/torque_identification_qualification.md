# H5 scientific qualification decision

This work delivers a reproducible research procedure and a scientifically negative
friction result, not qualified application evidence. H4's opaque owner transaction
correctness remains independent and unchanged.

## Execution order and pins

A source/model derivation and B known-truth tests preceded C policy commit
da2f9a082018285dd706e49aad61d3783233a29d. D development inventory occurred only
after that commit; actual development fits could not execute because the frozen
artifact and its route/epoch/selection bindings were unavailable. E therefore
retains explicit fail-closed verdicts rather than inventing results.

Runtime c2130730239bcdb4cbde9361ab90c8d99aa4ff55, integration
7a2f051b1f3847786318900444c88c2ba7a74a67, observed current carrot-wip
f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3 and CyberPilot scientific interface
02652a441c1c39b4a9c3bfaf1132217f0e57b384 remain separate exact pins.
The current branch was re-read, not silently substituted for the runtime pin.
24 exact files /50 ranges were byte/hash verified;66 pre-H5 production, owner,
owner-test, replay and source-evidence files are checked against the H5 Git base.

## Synthetic primary results

Fixed seed17; all values are mathematical diagnostic examples, not vehicle bounds
or recommended parameter values. Numeric JSON is canonical; table values are
rounded.28 prespecified sensitivity cases additionally cover the policy's axes.

|Case|True F|True C|x/y noise std|Raw fitted factor|Native residual coefficient|Interpretation|
|---|---:|---:|---|---:|---:|---|
|ideal factor|2|0|0/0|2.000000|~0|ideal recovery|
|factor + offset .125|2|0|0/0|2.000000|~0|offset .125 recovered|
|symmetric friction|2|.1|0/0|2.162440|.130007|biased, not identity|
|another friction magnitude|2|.05|0/0|2.040158|.066550|mapping depends on model|
|x noise|2|0|.02/0|1.987827|.031154|noise enters spread|
|y noise|2|0|0/.02|1.997656|.012520|noise enters spread|
|x+y noise|2|0|.02/.02|1.985806|.035008|positive spread at C=0|
|unbalanced sides|2|.1|0/0|2.422181|.124120|excitation sensitivity|
|lag mismatch|2|0|0/0|2.098840|.150133|alignment contamination|
|constant roll bias .01 rad|2|0|0/0|2.000000|~0|offset -.098098|
|inside deadzone|2|.1|0/0|2.000000|~0|nonzero C invisible|
|threshold transition|2|.1|0/0|2.004446|.022341|occupancy dependence|
|low excitation, no noise|2|0|0/0|2.000000|~0|algebra only, no confidence|
|degenerate|2|0|0/0|unavailable|unavailable|correctly rejected|
|mild nonlinearity|2|0|0/0|2.027237|.002015|nonlinear contamination|

Ideal affine and restricted analytic/synthetic comparisons pass the frozen2e-12
numerical allowance. Noisy/friction cases are sensitivity results, not a relaxed
recovery test. Lag axes are +/-1 synthetic sample and correct alignment, not
vehicle deadlines; actual development cadence/delay bindings are unavailable.
The generator has no dependency on the estimator or analytic prediction helper.

## Separate scientific decisions

- Factor: ideal conditional affine mapping is proven; real selection, mode,
  noise, epoch validity and cluster inference are not established.
  FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE.
- Friction: analytic and independent synthetic counterexamples reject the native
  spread coefficient as a universal direct controller-C estimator.
  FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION.
- Joint: NONIDENTIFIABLE in the unrestricted observed-x/y model with latent
  friction state, unknown noise and nuisance intercept. This does not deny ideal
  conditional factor identification or a future better-instrumented model.

For joint nonidentifiability, observations y can be represented by multiple
(F,C,b) choices whenever latent q=(F*u+b-y)/(F*C) remains in[-1,1]; an appropriate
unobserved error trajectory can realize that q. Constant q confounds C with b,
and spread alone also confounds C with noise. Those variables are not available
in the frozen numerical diagnostic's x/y records.

## Numerical parity is necessary, not scientific success

Exact pinned TorqueEstimator.estimate_params and CyberPilot identify_torque were
executed as isolated mathematical AST definitions on identical frozen rows.
Two affine/noisy cases have maximum absolute difference0 locally; the actual
imported friction helper has18 enabled/disabled boundary checks. The native
constructor, Params, cache, native randomized bucket sampling and runtime module
imports are not executed. Native full-process/selection parity is not claimed.
NATIVE_NUMERICAL_PARITY_PASS is explicitly not IDENTIFICATION_PASS.

## Authority and retained gates

ScientificQualificationReport is frozen and binds sources, policy/freeze commit,
synthetic execution and optional supplied development evidence. Candidate
generation, application, runtime acceptance and identification qualification
fields are init=False false; dataclass replacement into authority rejects.
There is no PR #9 QualifiedEvidence bridge and no connection to the H4 owner.

```text
TORQUE_IDENTIFICATION_BLOCKED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_ESTIMAND_DEFINED
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FRICTION_ESTIMAND_DEFINED
FRICTION_NATIVE_ESTIMATOR_NOT_DIRECT_IDENTIFICATION
NONIDENTIFIABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
FACTOR_UNIT_EQUIVALENCE_UNRESOLVED
FRICTION_UNIT_EQUIVALENCE_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
REPRESENTATION_ENCODING_UNRESOLVED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_INHIBITION_EXECUTOR_ACCEPTANCE_UNRESOLVED
APPLICATION_NOT_AUTHORIZED
```

## Verification and reproduction

Install the optional analysis dependency with `python -m pip install -e ".[dev,research]"`.
Run `python -m pytest`, Ruff, strict MyPy and the existing H2/H3/golden checks.
`python -m tests.audit.validate_torque_science --verify-history` validates metadata,
recomputes synthetic results with the frozen numerical allowance, protects old
source bytes and proves policy commit ancestry/result introduction ordering.
Git history proves file order, not an unauditable claim about a person's thoughts.

For exact external bytes/native math parity, add explicit `--carrot-checkout` and
`--research-checkout` object stores. CI prepares the pinned objects outside the
package, then verifies hashes/parity with networking disabled. The installed-wheel
smoke runs outside the checkout, checks the missing optional dependency first,
then exercises actual float64 fitting and the authority-free scientific report.

Local verification before final review:1157 tests passed; research statement
coverage100%, branch coverage100%; overall combined97.92%. Final exact-head CI,
fresh independent review and wheel verification are completion gates recorded
in the Draft PR/final report, not inferred from these local counts.

Recommended next single task: **A — friction estimator redesign / identifiable
friction model**. Do not begin it automatically and do not recommend a combined
factor+friction writer from the current evidence.
