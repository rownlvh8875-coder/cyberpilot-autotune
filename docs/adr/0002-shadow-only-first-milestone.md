# ADR 0002: OFF and SHADOW only

Status: accepted for Phase 0-4, following the supplied scope.

Only OFF and SHADOW are representable runtime modes. Eligibility means only
ACCEPTED_FOR_SHADOW. Every EngineResult enforces effective_parameters equals
baseline_parameters. No controller capability or apply method exists.

Unknown modes are rejected at construction. A trusted baseline is supplied
separately from observations so corrupted inputs cannot redefine fallback.
Insufficient elapsed history rejects nonzero candidate changes. NoOpLearner is
the only packaged learner; ScriptedLearner lives in tests only.

This provides software invariant evidence, not production safety certification,
vehicle bounds, improved driving performance or permission to deploy.
