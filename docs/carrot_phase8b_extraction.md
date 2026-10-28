# Phase 8B.1 read-only Carrot extraction boundary

## Authority, pins and implementation plan

This implements the owner's complete Phase 8B.1 specification inline with TDD
and fresh independent reviews. No Engine/learner execution, live SubMaster,
persistence, controller writes, real logs or vehicle work is authorized.

Target base/main is PR #6 merge **16e1695e7a9b41f4a6bc728a5bca781d38b26151**,
merged 2026-10-28T08:59:50Z. Parents are
03c3f2f36cbe47a9afec97ce7b9d411d3aa81ccb and
63f2829196272ebf7bed4fcba7c92a2286239baa. The old head is an ancestor, and merge
tree 18fc48d6264cca9fa226a0aabbcc6d0bd66cce06 equals the head tree. Fresh
read-only review: zero Critical/Important/Minor; 668 tests and exact-head CI pass.

Reference repository: https://github.com/rownlvh8875-coder/openpilot.

- Original clean source base: **604bc0a22733e648ec05b268da1ffaae7db52a69**.
- Observability code revision: **c2130730239bcdb4cbde9361ab90c8d99aa4ff55**.
- Fork integration merge: **7a2f051b1f3847786318900444c88c2ba7a74a67**,
  integration/carrot-wip-observability-c213073, merged 2026-10-28T09:02:12Z.
- Merge parents: clean source base and observability revision, above. Tree
  ffb213d9fdc0f9618264822bd2a4e26263abfe74 equals the observability source tree.
- PR #20 retarget preserved its 12 commits and 26 files. Fresh review found no
  Critical/Important/Minor issue and independently passed 378 offline tests,
  baseline-aware lint/type checks and four generated C++ schema syntax checks.
- base/carrot-wip-604bc0a remains at the clean source base; fork carrot-wip stays
  at 1ab3448148c936ea257389abaaf6e4ab26dd4af0. Source branch is not deleted.

The code revision remains c213073; the merge SHA is integration provenance,
not a different source implementation. No upstream branch or PR is changed.

Execution tasks and file ownership:

- [x] Verify/review/merge PR #6; preserve/retarget/review/merge PR #20 and prove
  parent, ancestor and tree equality before implementation.
- [ ] RED/GREEN extraction: integrations/carrot/errors.py, health.py,
  availability.py and extraction.py; explicit immutable decoded samples,
  field/union/enum checks, no retained reader, optional dependency boundary.
- [ ] RED/GREEN state: cache.py and adapter.py; exact bounded poisoned caches,
  transactional attempt consumption, sequence/high-water and explicit sessions.
- [ ] Run all 69 existing literal contracts through actual generated schema
  extraction plus exact caches/join. Keep adapter state-machine tests separate
  from deliberately corrupted caller-attempt metadata used in pure cases.
- [ ] Add compatibility tests/evidence and Linux-only pinned-schema CI; maintain
  all existing base jobs and no-dependency wheel smoke.
- [ ] Full regression, coverage, build/wheels, fresh final review, append-only
  commits, push and requested Draft PR; record exact-head CI before completion.

Review focus: a rejected frame repaired and resubmitted; stale health used from
a different sample; ambiguity forgotten on eviction; source/boot/receive time
mixing; old-session messages relabeled after reset. Tests must assert actual
failure behavior, not merely cache size or source text.

## Initial design decisions

The optional integration package imports only the standard library and existing
contracts at import time. Only its explicit dependency/compatibility entry point
locally imports pinned cereal/pycapnp. No arbitrary import path is accepted.
Actual construction without that dependency raises CarrotDependencyUnavailable.
Default wheel import remains independent of openpilot.

Decoded samples carry explicit non-identifying session generation/token, topic,
publication timestamp, Event.valid, immutable health and a transient reader.
Only immutable neutral evidence and health are retained. Actual Cap'n Proto
scalar False has no presence bit; it is known only with a qualified producer
capability, event/transport evidence and the exact source join.

Health valid is an explicit caller transport assessment, separate from copied
Event.valid. All seen/alive/valid/freq_ok/updated checks must pass. If a caller's
transport valid directly mirrors a False outer Event.valid, transport admission
rejects; the adapter never silently replaces that False with True. A separately
healthy transport assessment can carry a complete previous receipt even when
the current outer Event.valid is False.

Cache equality uses canonical neutral evidence plus frozen health, not unstable
wire layout or borrowed reader bytes. All capacities are explicit caller values.
Oldest publication timestamp is evicted deterministically; conflicting keys are
poisoned. Per-topic timestamp and apply/output high-water survive ordinary
rejection and consumed-ID eviction. Only explicit advancing session reset clears
caches/state. Every sample must carry the current receive-time session tag.

The existing pure contract should remain unchanged except for a demonstrated
boundary defect: actual inactive-v2 commands intentionally omit measurement and
thus cannot identify a source CS. A complete inactive receipt must still retain
its False activity diagnostic without constructing a Snapshot. Any required
minimal correction will be test-first, preserve all 69 expected projections,
and be recorded explicitly rather than manufacturing dummy source data.

## Implemented package boundary

`integrations.carrot` is optional. Its package import and all submodule imports
work without openpilot/pycapnp. The explicit `require_schema()` entry point makes
fixed local imports of capnp and openpilot.cereal.car/log only. It requires
pycapnp **2.1.0** and the pinned structural fingerprint
`ca3e63676b4deb03efbd7998c667a4fbcc74a4a1c47c9755869c62a76e7cf0a0`.
The fingerprint covers extracted fields' ordinal, type, node ID, union membership
and enum ordinals. Actual adapter construction without the optional dependency
raises `CarrotDependencyUnavailable`; incompatible schemas/import failures raise
`CarrotSchemaIncompatible`. Neither error message embeds backend input.

Only `availability.py` imports those schema dependencies. No messaging module,
SubMaster, CarInterface, Params or controller is imported. Core/safety/runtime/
replay cannot import this integration. The basic wheel has no new required
dependency. The separate optional test environment installs pycapnp and uses an
exact sparse reference checkout outside the package tree; it needs neither numpy
nor production SCons/native CAN code to generate these actual dynamic readers.

The API is synchronous, single-owner and **caller-serialized**: ingest, evaluate
and reset must not run concurrently. No worker, thread, lock service, process or
loop is created. Reader payload must be stable during its extraction call; after
return it may expire or mutate without changing retained evidence.

## Extraction and availability

`DecodedTopicSample` carries topic, Event.logMonoTime, Event.valid, explicit health,
a receive-time `SessionToken(generation, token)` and a transient reader. Topics
are limited to carControl, carState and carOutput. Only actual generated reader
class and matching topic schema node IDs pass the real binding. Builders must be
converted with as_reader by the caller. Unit doubles are never compatibility
evidence.

Extraction copies only named fields into frozen neutral contracts. A reader or
borrowed byte buffer is never cached. In particular CarState's unrelated GPS,
navigation and identifying fields are never traversed or retained.

| Wire evidence | Extraction rule |
|---|---|
| Receipt version | Actual field is `actuationReceipt.receiptVersion`; neutral field is version |
| Timestamp union | Explicit value plus known clock domain; missing/zero/unknown stays unavailable |
| Numeric union | Only value arm with finite numeric payload; genuine available 0.0 remains 0.0 |
| Enum | Explicit recognized names; unknown wire ordinal normalizes to unavailable/unknown |
| Actuator pointer | Require present pointer and all ten numeric fields finite; otherwise unavailable |
| Measurement | Copy complete version/mode/current health, all source timestamps and seven actual numbers |
| Desired target | Preserve Float64 pre-controller target independently of Float32 final request |
| CarState scalar Bool | Only known with qualified capability; unsupported producer yields None |

Cap'n Proto scalar Bool cannot encode None or distinguish an explicit False from
its wire default. Therefore availability is a separate caller/producer fact.
The synthetic unknown_override case retains this fact in extraction capability,
not by interpreting a default False as known. Supported False is proven only by
qualified producer context, topic/event/health evidence and exact CS join; it is
not inferred from bytes alone.

No canonical wire-byte equality is claimed. Layout/allocation and default pointer
representations can differ without changing these semantics. Cache equality is
frozen neutral evidence plus health. Nonfinite numbers and unknown enums normalize
to unavailable; semantically identical unavailable entries remain unusable.

## Cache and consumption lifecycle

All three capacities are positive explicit caller-supplied integers, without
defaults. Separate CC/CS caches use positive UInt64 publication keys. Lookup is
exact, with no latest fallback or interpolation. Same key plus same neutral
evidence/health is idempotent. Different evidence or health, or a structurally
malformed source at that key, poisons it. Poison remains until deterministic
oldest-publication eviction. Per-topic high-water prevents an evicted old key
from being reintroduced as a newly trusted source in that same stream.

Every evaluate call allocates a new attempt sequence, including rejected calls.
For a correct topic/current session the transaction is:

1. Observe publication ordering, retaining any sample-clock failure for later.
2. Extract a readable receipt, register its known cohort ID, and advance the
   structurally present monotonic apply high-water before downstream rejection.
   Consumed IDs evict oldest-first by attempt insertion order at their capacity.
3. Report retained clock/sample errors only after this consumption. Invalid
   evaluation time, unhealthy transport, missing cache, bad policy or pure-gate
   rejection never rolls consumption/sequence/high-water back.
4. Require `host apply <= carOutput publication <= evaluation time`; join exact
   CC and its exact measurement CS. Only cached source entries whose own frozen
   transport health passed can supply evidence. Current good health cannot
   repair old unhealthy source metadata.
5. Pass the **pre-attempt** consumed/high-water values to pure evaluate, so the
   current first attempt is not mistaken for its own duplicate. Return its
   MappingDecision only. Duplicate publication/cohort or old apply rejects.

Malformed receipt data whose cohort cannot safely be extracted requires explicit
new-session reset. This prevents repairing it under a new publication timestamp.
Known malformed clocks/causal order or a known controller/context mismatch also
require a new session. An initial well-typed unavailable/version-0 receipt is
simply rejected: absent time is not invented clock-regression evidence.
An incomplete version-1 cohort identity instead invalidates the session, even
when individual field extraction succeeds. Known controller/version/domain and
same-domain causal faults are checked immediately after consumption, independently
of later cache, health or evaluation-clock failures. A missing exact source must
never mask source command after apply, nor may an invalid evaluation argument
hide a known changed controller. Source measurement clock ordering is checked
without requiring the missing source CS first. No cross-domain subtraction occurs.
Structurally present but later-invalid apply time can conservatively advance the
high-water before rejection; explicit reset is required after an actual clock
fault. This characterizes a fail-closed availability tradeoff, not optimal live
timing or availability. No physical effect or per-CAN approval is implied.

The inactive boundary defect was reproduced before correction. The pure module's
missing-CS check now follows its complete inactive-receipt diagnostic branch.
No Snapshot or dummy CS is constructed; all 69 old projections remain unchanged.
No other pure-contract algorithm, gate, engine, learner or replay fixture changes.

## Session and caller attestations

ProducerAttestation requires the exact source/integration/schema revisions,
static-context digest, baseline epoch, session generation/32-hex lifecycle token,
permitted controller kinds and optional qualified steeringPressed capability.
AdapterConfig validates these against its frozen StaticVehicleContext and policy
and defensively copies the trusted baseline. Epoch/context cannot mutate in place.

Qualified override producers currently are the pinned Tesla CarState.update and
VW MEB CarState.update_meb, checked against the caller context's brand/controller
and exact source path/symbol/revision. Other ports yield unavailable override
until separately audited; controller-family synthetic tests do not qualify a
physical vehicle. Capabilities, static CP and live producer source identity are
caller attestations, not nonexistent receipt fields or constants filled as True.
Actual transport health is calculated from all five supplied flags on every use.
The caller must obtain these facts from its qualified receive/launch boundary;
this module does not authenticate a remote publisher or read CarParams itself.

Session tags are assigned at receive time, never relabeled after reset. Timestamp
regression, explicit producer_restarted notification, known changed controller
context or a broken clock/cohort requires a new session. Reset is explicit, with
strictly advancing generation and a different non-identifying token; it clears
caches, poison, counters and consumed IDs together. Old-tag samples reject before
they can contaminate new state. Ordinary admission rejection never resets state.
An adapter process restart likewise needs a fresh receive session; no persistent
history or automatic restart inference exists. Token must be software lifecycle
metadata, never a VIN/route/device/driver identifier.

## Executable evidence and qualification

[Compatibility evidence](evidence/carrot_phase8b_schema_compatibility.json)
records all three source pins, six raw schema/loader hashes, the actual generated
field/union/enum layout, reader version and 69 independent expected result hashes.
No source bodies or real logs are copied. Source attribution/license selection
for any future reuse remains an owner decision; no LICENSE is introduced.

The optional suite uses real pycapnp builders/readers. All 69 old cases traverse
actual extraction plus exact caches/join and compare unchanged expected
projections. Deliberately invalid caller-only context/epoch/counter metadata is
retained outside wire fields. Public adapter tests separately exercise actual
state-machine ingestion/evaluation across all four controller kinds, delayed
publication, MEB target/request separation, inactive/safety/limit states, missing
sources, conflicts and legacy defaults. No fake binding is used for compatibility.

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy src/cyberpilot_autotune
python -m pytest -q
python -m pytest --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90
python -m compatibility.carrot.run --reference-checkout <exact-integration-checkout>
python -m coverage report --include="*/integrations/carrot/*" --fail-under=95
python -m build
```

The compatibility runner first verifies exact checkout/parents/tree equality and
schema bytes, then denies network socket operations during tests. CI additionally
runs tests and optional wheel mapping in a separate Linux network namespace,
dropping back to the normal runner UID. Dependencies, sparse checkout, build and
wheel installation finish during setup before isolation. CI never updates evidence.

The existing 8 push/PR matrix jobs remain; an extra Linux-only compatibility job
per event pins integration 7a2f051 directly. Basic wheel smoke proves import and
typed optional-construction failure without openpilot. Optional wheel smoke
proves actual generated-schema mapping against installed site-packages outside
the checkout, without editable-source substitution.

Full production SCons, native CAN extension, device Params/IPC, hardware, live
timing and real logs remain unverified. No live SubMaster, Engine/learner connection,
persistence, Apply/controller write, vehicle installation/test or upstream PR is
implemented. Final review/exact-head results are recorded after verification.

## Independent review correction record

The fresh whole-branch review of implementation 8b2ad8ae331f5a379ddbe09f12bb41f67ce0edde
found zero Critical, two Important and zero Minor issues. Both Important findings
were lifecycle failures: an incomplete version-1 receipt could be repaired under
a later publication; known clock/controller faults could be masked by an earlier
missing-source or invalid-evaluation-time rejection. They were reproduced with
actual generated readers before correction (six failing scenarios), then fixed
by independent attestation checks immediately after transactional consumption.
Three further actual-wire cases pin unsupported receipt/observation/measurement
version changes. All nine cases now reject and require explicit new-session
reset; default version-0 startup recovery remains tested. No second independent
review of this correction is claimed.

Post-correction local checks: 731 base tests and 834 combined native Linux tests
(including 103 actual-schema checks), zero failures/skips. All 69 existing literal
projections remain unchanged. The network-audited minimal environment uses Python
3.12.3 and pycapnp 2.1.0; no production source dependency beyond schemas is loaded.
Final clean-clone, wheel and remote CI results are recorded at publication.
