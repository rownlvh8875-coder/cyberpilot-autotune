# Parked read-only sidecar: Phase 8B.2A

## Approved scope and pins

The owner authorized implementation, synthetic validation and a new Draft PR;
no vehicle/runtime execution or merge is authorized. Base/main is
b24ef18e4270af5ab4f731aca31cf95f4f4b0cce. The initial worktree is clean and its
adapter/goldens equal that base. New branch: feat/carrot-live-readonly-sidecar.

Reference integration is 7a2f051b1f3847786318900444c88c2ba7a74a67, tree-equal
to observability source c2130730239bcdb4cbde9361ab90c8d99aa4ff55; original base
604bc0a22733e648ec05b268da1ffaae7db52a69. Schema revision is
observation-v2-measurement-v1. All remote pins were rechecked before changes.
[Runtime evidence](evidence/carrot_phase8b2a_runtime_contract.json) records source
hashes and the explicit config/health/exit contracts without source bodies.

## Design decisions and plan

The approved data flow is SubMaster -> immediate immutable extraction -> existing
exact caches/join -> existing pure evaluator -> MappingDecision and sanitized
terminal diagnostics. No engine/learner/controller is reachable.

Ruling: retain the existing normal admission/cache algorithm. Add frozen read-only
cache metrics and cumulative per-session poison/eviction counters because these
cannot be truthfully reconstructed outside the cache. An explicit unavailable
output-envelope rejection also increments the existing attempt counter and latches
the session, without fabricating a timestamp or False validity. No source evidence
or mutable cache entry is exposed. The cost is these small tested observer/closed
rejection extensions; the established receipt evaluator path is unchanged.

Ruling: configuration uses explicit CLI pins/platform/budgets plus a bounded JSON
object on stdin; no config file, Params or CarParams reader. All context, baseline,
age/skew, capacity, capability and session values are caller supplied. There are
no vehicle defaults. The stdin software size bound is 64 KiB, not a vehicle limit.

Ruling: CLI is a bounded qualify command with caller-supplied positive update
budget and poll timeout. Interrupt exits normally; failures are sticky and
sanitized. Explicit API new-session requires a fresh source instance and advancing
caller token/generation. CLI recovery requires process restart; no reset command,
generation inference or automatic reconnect is implemented.

- [x] Recheck base, source tree, unchanged adapter/goldens and clean worktree.
- [x] TDD immutable config/platform/pin gates, source health/update handling,
  typed dependencies and frozen cache metric semantics.
- [x] Implement source callback bridge, runner/session handling and sanitized
  diagnostics; validate no reader survives a callback outside SubMaster itself.
- [x] TDD qualify-only CLI, stdin validation, stable exit codes and shutdown.
- [x] Actual schema simulated streams: Hyundai, MEB, delayed/missing/conflicting
  sources, rejected receipt consumption, unavailable fields and fault precedence.
- [x] Full local regression/coverage, installed wheels and unchanged goldens;
  define pinned network-isolated CI and wheel checks.
- [ ] Confirm remote CI and fresh independent whole-diff review at exact head.
- [ ] Append-only push and new Draft PR; record review/check results externally.

## Pinned SubMaster semantics

The inspected messaging/__init__.py SubMaster constructs conflated receive sockets,
stores current readers in data, and exposes them via __getitem__. update resets
updated, then update_msgs copies Event.logMonoTime and Event.valid into its maps.
seen, alive and freq_ok are distinct evidence. The three services are each 100 Hz
in this source; their rates are not copied into a new acceptance threshold.

The live factory subscribes only to carControl, carState and carOutput, with all
three in poll. It supplies no ignore lists, frequency override or remote address.
Simulation and any health-ignore shortcuts are rejected on every poll. Native
SubMaster/msgq internals own their IPC; the sidecar creates no additional socket,
publisher, process or background thread. The pinned API has no SubMaster.close;
our close drops its owned reference, letting native socket destructors release
resources. No current reader is accessed after close.
The dependency entry point returns a frozen binding containing only the receive
constructor; it does not return the messaging module or expose its publishers.

Only updated=True topics are consumed, in CC/CS/CO order per synchronous update.
Each callback copies immediately through the existing adapter. No batch of borrowed
readers, previous reader or SubMaster object enters cache/MappingAttempt. Conflation
can lose commands: an unobserved exact source is rejected, never reconstructed.

SubMaster.valid is the actual outer Event.valid. All five existing health flags
must pass. In particular an outer-invalid carOutput has unhealthy transport here,
even if its previous receipt looks complete. The sidecar does not force it True,
nor claim it describes the previous receipt. Producer measurement health remains
separate. Health-failed but structurally readable outputs still reach transactional
adapter rejection; missing envelope metadata is a sticky runtime fault with no
retry or partial Snapshot.

A structurally unparseable updated carOutput still consumes an explicit closed
adapter attempt through reject_output_envelope. It produces INVALID_INPUT with no
cohort or Snapshot and requires a new session. Available output envelopes always
use the original evaluate_car_output transaction, including unhealthy health.

## Runtime gates and lifecycle

Exact pins, existing context digest/baseline epoch and qualified platform metadata
are checked before dependency loading or subscription. CLI supports the qualified
Hyundai platform allowlist only; MEB source/runner regression uses injected test
sources and explicit caller context, not a fabricated Hyundai vehicle identity.
Missing runtime platform is RUNTIME_PLATFORM_UNCONFIRMED; different values are
RUNTIME_PLATFORM_MISMATCH; unsupported values are UNSUPPORTED_PLATFORM.

Source identity, static CP and runtime platform remain trusted caller attestations,
not wire fields. This PR does not read CP.carFingerprint. Project status remains
**RUNTIME_FINGERPRINT_UNCONFIRMED** even when synthetic supplied strings match.

No session is generated. Known adapter clock/controller/version faults, receive
boundary failures, explicit producer-restarted notification and local monotonic
regression stop the qualification session. No old cache is automatically reused.
The adapter continues to own receipt attempt consumption/high-water and exact
join semantics; a rejection cannot be repaired into a later Snapshot.

## Diagnostics and parked procedure

Only an allowlisted frozen summary is emitted: session uptime/state, topic and
healthy counts, attempts/acceptance/rejection counts, duplicate/poison/eviction
counts, faults and latest cohort/tri-state/Snapshot availability. No baseline,
actuator map, raw exception, reader, context, token, VIN, GPS, route, device or
driver data is serialized. Counters and uptime are per explicit session. No file
logging, network telemetry, database or persistent state exists.

This PR never runs the live factory against a vehicle. A later separately approved
parked qualification must first verify the actual runtime fingerprint read-only,
use a safely parked stationary vehicle, confirm no write/controller/learner path,
and supply all policy/context/baseline/session values. This process does not kill
or control the vehicle based on speed and never declares a vehicle qualification
pass. A successful synthetic CLI exit is not parked-vehicle evidence.

## Limitations and review focus

No native IPC/service, hardware, live timing, real log or vehicle test is performed.
Actual-schema tests use generated readers with a scripted SubMaster-shaped source;
they establish bridge semantics, not native socket compatibility or delivery rate.
The fixed native factory/API is source-audited and tested without launching it.

Review focus: health fields missing versus False; skipped updates; source buffers
mutating after callback; unhealthy outputs still consumed; sticky fault precedence;
new-session old-source reuse; CLI raw-input leakage; counters falsely inferred
outside cache; accidental engine/learner/Params/publisher or hidden IO capability.

Phase 8B.2B is NOT_STARTED. Persistence and Apply are NOT_AUTHORIZED. No upstream PR.

## Implementation checkpoint

Final local regression: 830 base tests and 999 combined actual-schema/audit tests
passed, with zero failures/skips. All 69 existing literal cases and four replay
goldens remain unchanged. Overall branch-inclusive coverage is 98.75%; sidecar
coverage is 98.36%, all Carrot integration coverage is 98.65%, and pure receipt
contract/safety coverage is 100%. The focused sidecar suite passes 123 tests.
Ruff/format and strict mypy pass (46 source modules).
The new frozen cache metrics do not change admission, eviction order or equality.

Observed RED/GREEN cases include absent runtime modules/APIs, cache transitions,
unknown updated flag silently skipped, unexpected new-session clock exception,
initial clock exception leakage, metadata-error receive counting, stdin error
exit classification, native signed-int timeout representability, unavailable
envelope consumption, evaluation-clock failure consumption, schema/controller
fault latching and receive-only dependency exposure. Each has a behavioral
regression test; the subsequent complete suite passes.

Actual reader tests cover 27 literal runner streams, one MEB bridge-only
regression and four envelope/version/controller fault cases (32 new actual-schema
tests). The MEB case does not bypass the CLI's Hyundai platform gate or
authorize a new platform. Raw schema readers are generated from the pinned tree;
the SubMaster receive loop is scripted, so no native service is launched.

Validation commands: `python -m ruff check .`, `python -m ruff format --check .`,
`python -m mypy src/cyberpilot_autotune`, `python -m pytest -q`,
`python -m compatibility.carrot.run --reference-checkout <pinned-checkout>`,
the same compatibility command with `--sidecar-only`, scope-specific coverage
reports, `python -m build`, and `python -m cyberpilot_autotune.replay.cli verify-all
tests/fixtures/replay`. Actual-schema runs use Linux Python 3.12.3 and pycapnp 2.1.0;
the base run uses Windows Python 3.12.14.

Fresh wheel environments confirm all 45 discoverable submodules import without
openpilot, optional dependencies fail with the typed error, two Hyundai sidecar
streams and the four existing Hyundai extraction cases preserve their baselines,
and all four replay goldens verify. Both wheel and sdist build successfully.
Exact-head independent review and remote push/PR CI are recorded in the Draft PR
after this checkpoint; no vehicle or native IPC qualification is implied.

## CLI input and stable exits

Only `qualify` exists. It requires the four exact revision flags, expected/runtime
platform flags, positive `--maximum-updates` and `--poll-timeout-ms`. The poll timeout
must fit the pinned Cython Poller's signed C int; this is a software representation
bound, not a vehicle freshness value. Launch pins are checked before stdin or IPC.

Stdin is one JSON object with exactly these keys:

| Key | Caller-owned value |
|---|---|
| static_context | All fields of existing StaticVehicleContext, without extra fields |
| static_context_digest | The existing context.digest; no alternative hashing |
| baseline_parameters | Explicit finite parameter mapping, defensively copied |
| baseline_epoch | Same epoch as snapshot_policy and producer attestation |
| session | Explicit generation and non-identifying 32-hex token |
| cache_policy | Three positive existing CachePolicy capacities |
| snapshot_policy | All existing age/skew/version/kind/context/epoch fields |
| steering_pressed_capability | Exact audited producer path, symbol and revision |
| allowed_controller_kinds | Same list as snapshot_policy |

No default input file or policy is created. Duplicate JSON keys, nonfinite JSON,
unknown/missing fields and over-64-KiB input reject without echoing input. Argparse
errors are likewise sanitized. Terminal output is canonical JSON per summary line.

Exit codes: 0 bounded normal exit or interrupt; 2 invalid config/input; 3 optional
dependency/schema unavailable; 4 source/platform/session mismatch; 5 runtime
invariant/envelope fault; 6 unsupported environment. Code 0 never means that a
vehicle, live timing, physical actuation or parked procedure has been qualified.
