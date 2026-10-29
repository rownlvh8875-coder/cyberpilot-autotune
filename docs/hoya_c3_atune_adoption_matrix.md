# Hoya concept adoption decisions

Status: proposed design integration only, 2026-10-29. No runtime implementation.
Evidence IDs resolve in [the audit](hoya_c3_atune_audit.md#evidence-index), with raw
identities/ranges in [the source manifest](evidence/hoya_c3_atune_sources.json).
Machine-readable decisions and scoring rationales are in
[the feature manifest](evidence/hoya_c3_atune_features.json).

| Hoya concept | Source evidence | CyberPilot existing equivalent | Gap | Decision | Future layer |
|---|---|---|---|---|---|
| Telemetry idea | H:telemetry | Exact immutable observations, B:contract | Use canonical evidence, not another log loader | ADOPT_WITH_STRONGER_CONTRACT | Read-only evidence consumer |
| Latest-slot join | H:telemetry | Exact CC/CS receipt lookup, B:adapter | Missing source health/age/identity | REJECT | None |
| Episode taxonomy | H:episodes | Gate reasons and replay evidence exist; no Episode Observer | Versioned caller thresholds, duration, gap/coverage accounting | ADOPT_WITH_STRONGER_CONTRACT | Episode Observer |
| Driver intervention | H:episodes, A:prompt | Existing override veto and qualified steeringPressed | Observation versus cause, pre-event window | ADOPT_WITH_STRONGER_CONTRACT | Episode Observer |
| Automatic dissatisfaction label | A:prompt, A:rules | No such causal assertion | No independent motive evidence | REJECT | None |
| Parameter metadata | H:knowledge, P:clamp | ParameterSpec/policy separated, G:policy | Semantic consumer/units/ownership descriptor | ADOPT_WITH_STRONGER_CONTRACT | ParameterDescriptor |
| Source-code grounding | H:snippet, C:sources | Exact source manifests already exist | Structured conditional claims instead of copied/stale strings | ADOPT_WITH_STRONGER_CONTRACT | SourceKnowledgeDescriptor |
| Built-in heuristic recommender | A:rules, A:parse | Research learner is not identification authority | Fixed targets and fallback defaults unqualified | REFERENCE_ONLY | Symptom vocabulary only |
| External LLM recommender | A:network, A:prompt | No external AI capability | Privacy, consent, redaction, source grounding unqualified | DEFER | Future advisory backend only |
| Direct Apply endpoint | H:apply, P:write | PR #9 CAS/readback/authority core | Owner/revision/evidence/recovery gates absent | REJECT | None; APPLICATION_ARCHITECTURE_REJECTED |
| Rollback visibility | W:rollback, V:rollback | PR #9 verified recovery semantics | Honest UI outcome states | ADOPT | UX_CONCEPT_ONLY |
| AI provider configuration | A:providers, A:config | No provider or secret storage | No persistence/network authorization | REFERENCE_ONLY | Provider labels only |
| Longitudinal taxonomy | H:episodes, N:mpc | Current application is steering-only | Inputs/causality not qualified | DEFER | FUTURE_LONGITUDINAL_EPISODE only |
| Before/after explanation | V:results, V:rollback | Immutable proposals/receipts available conceptually | No presentation contract yet | ADOPT | Future advisory report |

Counts: **ADOPT 2; ADOPT_WITH_STRONGER_CONTRACT 5; REFERENCE_ONLY 2; REJECT 3;
DEFER 2.** These are concept decisions; no Hoya module is adopted as code.

## Ordinal subsystem assessment

Scores are architectural judgments, not measured safety or performance.
0–5: larger value/evidence/compatibility/reuse is better; larger coupling/risk
is worse. The rationale, not the score, determines adoption.

| Subsystem | Architectural value | Evidence quality | Safety compatibility | Reuse value | Implementation coupling | Risk | Evidence / rationale |
|---|---:|---:|---:|---:|---:|---:|---|
| Episode taxonomy | 4 | 2 | 3 | 4 | 2 | 2 | H:episodes/B:gate: useful categories, heuristic observations require exact inputs |
| Parameter knowledge | 5 | 2 | 3 | 5 | 2 | 2 | H:knowledge/K:settings/L:torque: valuable descriptors; unit/default discrepancies |
| AI explanation UX | 3 | 1 | 2 | 3 | 3 | 4 | A:prompt/A:parse: readable hypotheses, unjustified certainty/fallback targets |
| Rollback UX | 4 | 2 | 2 | 4 | 2 | 3 | V:rollback/W:rollback: clear intent, not verified recovery |
| Log extraction | 2 | 1 | 0 | 1 | 5 | 5 | H:telemetry: latest values, default coercion, route/log coupling |
| AI recommender | 2 | 1 | 0 | 1 | 3 | 5 | A:rules/A:network: numeric advice not qualified identification |
| Direct Apply | 1 | 1 | 0 | 0 | 5 | 5 | H:apply/G:ports: lacks independent owner transaction and authority |

## Future longitudinal vocabulary, with no implementation promotion

Departure sluggishness, catch-up surge, harsh deceleration, brake intervention,
gas intervention, lead-response anomaly and curve-speed mismatch are each
**FUTURE_LONGITUDINAL_EPISODE**, **UNRESOLVED_INPUT**, implementation **DEFERRED**.
They are candidate diagnostic questions, not confirmed failures, parameter
recommendations, safety bounds or an activated roadmap milestone. Longitudinal
runtime/application is unchanged.

## Application and runtime boundaries remain authoritative

PR #8 remains the unchanged Draft receive-only sidecar with actual parked
qualification pending. PR #9 remains the unchanged Draft steering core without
a real writer. UI metadata, recommendation selection, a hash, an episode count
or an LLM explanation cannot substitute for independent qualified evidence,
trusted registry, owner arbitration, application authority and vehicle-approved
bounds. No Hoya component resolves the runtime fingerprint or grants authority.
