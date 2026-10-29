# Steering knowledge contract v1

H2 adds immutable descriptive metadata for future explanation. It does not add a
recommendation, current-value reader, baseline, observer, supervisor or writer.
`STEERING_KNOWLEDGE_CONTRACT_READY` describes this knowledge boundary;
`APPLICATION_POLICY_UNRESOLVED` continues to apply to steering application.

## Authority and module boundary

| Knowledge item | Independent contract it cannot satisfy |
|---|---|
| ParameterDescriptor | PR #9 SteeringPolicy/ParameterSpec |
| SourceKnowledgeDescriptor | QualifiedEvidence / independent parameter identification |
| Descriptor digest | AuthorizationGrant or proposal identity |
| ui_catalog_min / ui_catalog_max | Approved application bounds, step or rate |
| ui_default / storage_registry_default | Trusted baseline or current vehicle value |
| Descriptive owner role | Exclusive writer lease/arbitration |
| Source semantic proof | Vehicle approval or evidence that a value improves control |

PR #9 is inspected at `6a5ccc6732c8cd0b0fd123c23c98e4407c7213c5` only.
Its torqued/custom/NN ownership, CAS/revision/readback, friction equivalence,
qualified identification, vehicle bounds/rates and rollback/watchdog gates remain
unresolved. This package neither imports application types nor converts to them.
All pre-existing production files remain byte-identical to the H1 preserved-file
manifest; no existing core, safety, runtime, replay or integration imports knowledge.

## API

`knowledge.contracts` provides frozen, slotted, version-1 dataclasses and typed
enums. Nested sequences are copied into immutable tuples, duplicate descriptive
set members normalized, and registries sorted by stable IDs. Mutable dictionaries,
reader objects, source bodies and arbitrary payload fields are not descriptor
fields. Numeric metadata rejects Bool, NaN and infinities. Unavailable values stay
`None`; numeric zero is a distinct available description.

`knowledge.steering.get_registry(exact_revision)` requires an explicit exact SHA.
There is no branch/latest/default-source fallback. Each of three immutable
registries has nine descriptors and 26 source claims. `get_any(parameter_id)` is
diagnostic, including conditional and unresolved entries. `get_proven` returns
only source-PROVEN descriptions, **not proof of current controller applicability,
safe values or application authorization**. PROVEN requires known scale, software
unit, consumer unit, explicit mode conditions and PROVEN supporting claims.
It may still have UI-label, ownership or branch-drift gaps outside that narrow
descriptive proof. See the per-parameter scope in the catalog document.

Only nine steering IDs are admitted by KnowledgeRegistry. CarSelected3 and all
longitudinal keys are excluded. LateralTorqueCustom must be MODE_SELECTOR;
the logical offset ID must be COUPLED_PRESERVED_STATE with no storage key.
An unproven alias, duplicate ID/storage key, unrelated/missing claim or claim
from another source revision rejects construction. This is validation of
metadata consistency, not an attestation of a running producer.

## Units, defaults and conditions

Storage scale means the documented primary consumer conversion, not a callable
conversion API or universal physical calibration. Factor/friction have known
custom-path scaling but unavailable global canonical units. Software PID
coefficient names deliberately make no physical-dimension or optimality claim.
Offset's scale 1 explicitly describes unchanged filtered-wire copying, not a
known physical unit. Delay has several consumers; its scale does not erase
zero/live-delay selection or NN constructor timing. Unknown mode conditions stay
`None`; an empty condition list cannot mean unconditional use.

UI min/max/default are copied only as `ui_catalog_*` / `ui_default`. Native key
defaults are separately `storage_registry_default`. Different defaults and UI
language labels remain visible; no discrepancy is repaired by choosing a new
value. There is no current_value field, Params access, CarParams reader or
baseline factory. The descriptor package never reads a vehicle's settings.

## Exact source and identity

Each SourceKnowledgeDescriptor binds repository, exact revision, path, symbol,
inclusive 1-based line range, Git blob SHA, range SHA-256, structured semantic
claim, conditions and confidence. `schema_revision=steering-source-knowledge-v1`
versions the interpretation contract; it is not a claim that Hoya/current upstream
implements observation-v2. Historical Hoya, integration runtime and current
upstream claims have separate IDs/registries. Current upstream cannot upgrade
PR #8/#9 pins. No source bodies are stored in descriptors or manifests.

Canonical identity is SHA-256 of sorted-key, compact ASCII JSON over all
descriptor fields. Enum values and immutable sequences have stable projections;
integer 1 differs from Float 1.0; signed float zero is preserved. Any source,
unit, UI range, condition or classification change changes identity. These hashes
are **not signatures, authenticity proof, QualifiedEvidence or authorization**.
`matches_source` compares three explicitly supplied identities without IO.

The audit validator separately checks JSON projections against compiled metadata,
then optionally reads exact Git objects to recompute file/blob/range hashes and
verify UI ranges/native INT defaults. LF-inclusive range bytes are hashed without
decoding/normalizing them. Hash success establishes source identity, not semantic
truth: semantic interpretation still requires independent review. Reference code
is parsed/read only and is never imported/executed. CI performs source reads
without network after its explicit dependency/object setup.

```text
python -m tests.audit.validate_steering_knowledge
python -m tests.audit.validate_steering_knowledge --reference-checkout <local-git-repository>
```

## Future consumers and limits

A future read-only Episode Observer can reference stable IDs for context/unit
labels, without deriving thresholds from these descriptions. A future advisory
Supervisor can explain source semantics and evidence gaps. Neither connection is
implemented. No numerical write target, SteeringRequest or AuthorizationGrant
can be emitted here. External AI, prompts, provider SDKs and network requests
are absent; there is no IO, clock, thread/process creation or persistence in
the knowledge package. Import succeeds without openpilot.

Provenance is independently written metadata derived from pinned source reading;
no upstream source body is copied. H1 license/provenance evidence remains
historical reference, not a license grant. No target LICENSE is added or chosen;
owner license selection remains necessary before an upstream contribution.
