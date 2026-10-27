# Shadow core implementation plan

> Agent workflow: execute inline with test-driven-development and verification-before-completion.

Goal: complete Phase 0-4 software, retaining baseline in every mode and failure.
Architecture: docs/architecture.md and ADRs 0001/0002. The user's master prompt
defines scope. Implementation decisions below are maintainer-reviewable choices.

## Constraints and review focus

- Python >=3.12.3,<3.13; runtime standard library only; English source/docs.
- No application modes, real tuning constants, vehicle hooks, persistence or logs.
- Read-only source repositories live outside this target checkout.
- Review forged dataclasses, malformed learner collections and duplicate IDs.
- Review first-frame rate budget, repeated timestamps and clock regression.
- Review aliasing of baseline/registry and exceptions after partial evaluation.
- Review absent signal flags: unknown must not silently become False or zero.
- Review zero-proposal paths: invalid input must still produce a diagnostic.

## Tasks

1. Phase 0: inspect remote refs, audit pinned object and separately HEAD; record
   provenance, branch SHAs, real signal sources, Python evidence, ADRs and blockers.
   Commit only documentation after whitespace checks; Python checks are not yet
   applicable before a package/test toolchain exists.
2. Phase 1: write import smoke test and see it fail because package is absent.
   Add pyproject, src package, CI, contribution/security docs and PR template.
   Install dev tools, run smoke, ruff, format, mypy and pytest; commit.
3. Phase 2: tests/unit/test_contracts.py first: valid/invalid numeric construction,
   missing signals, frozen objects, defensive mapping copies, unsupported modes.
   Implement contracts/{validation,observation,parameter,proposal,decision,result},
   runtime/mode and safety/reasons. Constructor failures are ValidationError.
   Verify RED then GREEN, run full checks and commit.
4. Phase 3: tests/unit/test_gate.py first: ordered vetoes, freshness, sequence,
   proposal binding, numeric corruption, bounds/step/rate and health. Implement
   sanitizer, bounds, rate_limiter and gate. SafetyGate.evaluate accepts an
   observation and proposal plus explicit now/history/baseline/health arguments;
   validate_observation also protects empty proposal streams. No state in gate.
   Add Hypothesis eligibility properties, run regression and checks; commit.
5. Phase 4: tests/integration/test_runtime.py and property tests first: trusted
   fallback, no learner call in OFF or invalid frames, all exception boundaries,
   immutable results, deterministic streams, rate and ordering. Implement Clock,
   Learner, NoOpLearner, read-only ObservationAdapter and AutoTuneEngine.step.
   step accepts object, always returns EngineResult for processing exceptions.
   Add synthetic NoOp example; run regression and checks; commit.
6. Architecture tests: isolated import with file/network/thread guards and AST
   dependency/capability checks. Whole-branch independent review; fix substantive
   findings with RED/GREEN regression tests. Complete safety/replay/roadmap docs.
7. Clean-clone venv install, lint, format, mypy, pytest, coverage, sdist/wheel and
   isolated wheel import. Commit progress evidence, push feature branch, create
   target-only Draft PR and inspect CI if authentication permits. Never merge.

Each implementation commit runs git diff --check, ruff check, ruff format --check,
mypy and the complete pytest suite. Progress records phase evidence and blockers.
